#!/usr/bin/env python3
"""Compare generated NucXplore CSVs with Sample_For_Adnan-style references.

Feature mismatches affect the exit status. Prediction label/confidence drift is
reported only because replacing the classifier is expected to change outputs.

Algorithmic complexity is O(R * C) time and space for R matched nuclei and C
numeric feature columns; the in-memory merge makes exact nucleus alignment
explicit before correlations are calculated.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


NON_FEATURE_COLUMNS = {
    "nucleus_id",
    "Tissue",
    "Sex",
    "Age Bracket",
    "Hardy Scale",
    "Pathology Categories",
    "nucleus_type",
    "Predicted_Label",
    "Confidence_Score",
    "tile_name",
}


def load_csvs(root: Path) -> pd.DataFrame:
    paths = sorted(path for path in root.glob("*.csv") if path.name != "manifest.csv")
    if not paths:
        raise ValueError(f"No CSV files found in {root}")
    frames: list[pd.DataFrame] = []
    for path in paths:
        frame = pd.read_csv(path)
        if "nucleus_id" not in frame.columns:
            raise ValueError(f"Missing nucleus_id in {path}")
        frame["tile_name"] = path.stem
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def assert_unique_keys(frame: pd.DataFrame, label: str) -> None:
    duplicate = frame.duplicated(["tile_name", "nucleus_id"], keep=False)
    if duplicate.any():
        raise ValueError(f"{label} contains {int(duplicate.sum())} duplicate nucleus keys")


def paired_schema_equal(frame: pd.DataFrame) -> tuple[bool, list[str]]:
    failures: list[str] = []
    for pre_name in sorted(c for c in frame.columns if c.startswith("pre_norm_")):
        post_name = "post_norm_" + pre_name.removeprefix("pre_norm_")
        if post_name not in frame.columns:
            failures.append(f"missing {post_name}")
            continue
        pre = pd.to_numeric(frame[pre_name], errors="coerce").to_numpy()
        post = pd.to_numeric(frame[post_name], errors="coerce").to_numpy()
        if not np.array_equal(pre, post, equal_nan=True):
            failures.append(pre_name)
    return not failures, failures


def feature_correlations(
    merged: pd.DataFrame,
    generated_columns: set[str],
    reference_columns: set[str],
) -> tuple[dict[str, float | None], list[str]]:
    common = sorted((generated_columns & reference_columns) - NON_FEATURE_COLUMNS)
    correlations: dict[str, float | None] = {}
    unequal_constants: list[str] = []
    for name in common:
        left = pd.to_numeric(merged[f"{name}_generated"], errors="coerce").to_numpy(float)
        right = pd.to_numeric(merged[f"{name}_reference"], errors="coerce").to_numpy(float)
        finite = np.isfinite(left) & np.isfinite(right)
        left = left[finite]
        right = right[finite]
        if not len(left):
            correlations[name] = None
            continue
        if np.std(left) == 0.0 or np.std(right) == 0.0:
            equal = np.array_equal(left, right)
            correlations[name] = 1.0 if equal else None
            if not equal:
                unequal_constants.append(name)
            continue
        correlations[name] = float(np.corrcoef(left, right)[0, 1])
    return correlations, unequal_constants


def prediction_report(generated: pd.DataFrame, reference: pd.DataFrame) -> dict[str, Any]:
    required = {"Predicted_Label", "Confidence_Score"}
    if not required.issubset(generated.columns) or not required.issubset(reference.columns):
        return {"available": False}
    merged = generated.merge(
        reference,
        on=["tile_name", "nucleus_id"],
        suffixes=("_generated", "_reference"),
        validate="one_to_one",
    )
    label_equal = (
        merged["Predicted_Label_generated"].astype(str)
        == merged["Predicted_Label_reference"].astype(str)
    )
    left = pd.to_numeric(merged["Confidence_Score_generated"], errors="coerce")
    right = pd.to_numeric(merged["Confidence_Score_reference"], errors="coerce")
    return {
        "available": True,
        "matched_nuclei": len(merged),
        "label_agreement": float(label_equal.mean()),
        "confidence_correlation": float(left.corr(right)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-features", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--generated-predictions", type=Path)
    parser.add_argument(
        "--min-correlation",
        type=float,
        default=0.99,
        help="Minimum aggregate Pearson correlation per non-constant feature",
    )
    parser.add_argument("--report-json", type=Path)
    args = parser.parse_args()

    generated = load_csvs(args.generated_features)
    reference = load_csvs(args.reference)
    assert_unique_keys(generated, "generated features")
    assert_unique_keys(reference, "reference")

    merged = generated.merge(
        reference,
        on=["tile_name", "nucleus_id"],
        suffixes=("_generated", "_reference"),
        validate="one_to_one",
    )
    generated_pairs_equal, pair_failures = paired_schema_equal(generated)
    correlations, unequal_constants = feature_correlations(
        merged, set(generated.columns), set(reference.columns)
    )
    finite_correlations = {k: v for k, v in correlations.items() if v is not None}
    below_threshold = {
        key: value
        for key, value in finite_correlations.items()
        if value < args.min_correlation
    }

    predictions = {"available": False}
    if args.generated_predictions is not None:
        predictions = prediction_report(load_csvs(args.generated_predictions), reference)

    report: dict[str, Any] = {
        "generated_files": int(generated["tile_name"].nunique()),
        "reference_files": int(reference["tile_name"].nunique()),
        "generated_nuclei": len(generated),
        "reference_nuclei": len(reference),
        "matched_nuclei": len(merged),
        "pre_post_exact": generated_pairs_equal,
        "pre_post_failures": pair_failures,
        "feature_count": len(correlations),
        "minimum_finite_correlation": min(finite_correlations.values()),
        "below_threshold": below_threshold,
        "unequal_constant_features": unequal_constants,
        "predictions_report_only": predictions,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.report_json is not None:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    feature_ok = (
        len(generated) == len(reference) == len(merged)
        and generated_pairs_equal
        and not below_threshold
        and not unequal_constants
    )
    return 0 if feature_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
