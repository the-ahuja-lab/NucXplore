#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass
class FileResult:
    status: str
    input_csv: str
    output_csv: str | None
    rows: int
    error: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Annotate NucXplore feature CSVs with predicted cell type labels "
            "and confidence scores using a baked XGBoost model."
        )
    )
    parser.add_argument("--input-features", type=Path, required=True, help="Root directory containing feature CSVs")
    parser.add_argument("--output-dir", type=Path, required=True, help="Root directory for annotated CSV outputs")
    parser.add_argument("--model", type=Path, required=True, help="Path to XGBoost model pickle")
    parser.add_argument("--encoder", type=Path, required=True, help="Path to label encoder pickle")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 1) - 1), help="CPU workers/threads hint")
    parser.add_argument("--manifest-json", type=Path, default=None, help="Optional manifest JSON output path")
    parser.add_argument("--manifest-csv", type=Path, default=None, help="Optional manifest CSV output path")
    parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True, help="Recursively scan input-features for CSVs")
    return parser.parse_args()


def iter_csv_files(root: Path, recursive: bool) -> list[Path]:
    walker: Iterable[Path] = root.rglob("*.csv") if recursive else root.glob("*.csv")
    paths = [p for p in walker if p.is_file()]
    paths.sort()
    return paths


def set_thread_limits(workers: int) -> None:
    import threadpoolctl

    safe_workers = max(1, int(workers))
    threadpoolctl.threadpool_limits(limits=safe_workers)
    try:
        os.sched_setaffinity(0, set(range(safe_workers)))
    except (AttributeError, OSError, ValueError):
        pass


def load_artifacts(model_path: Path, encoder_path: Path) -> tuple[Any, Any, list[str]]:
    import joblib

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not encoder_path.exists():
        raise FileNotFoundError(f"Encoder not found: {encoder_path}")

    model = joblib.load(model_path)
    encoder = joblib.load(encoder_path)

    try:
        feature_names = list(model.get_booster().feature_names)
    except Exception as exc:
        raise RuntimeError("Failed to read model feature names from booster") from exc

    if not feature_names:
        raise RuntimeError("Model booster has no feature names")

    return model, encoder, feature_names


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def process_csv(
    input_csv: Path,
    output_csv: Path,
    model: Any,
    encoder: Any,
    feature_names: list[str],
) -> FileResult:
    import numpy as np
    import pandas as pd

    df = pd.read_csv(input_csv)

    if df.empty:
        return FileResult(
            status="skipped_empty",
            input_csv=str(input_csv),
            output_csv=None,
            rows=0,
            error=None,
        )

    missing = [name for name in feature_names if name not in df.columns]
    if missing:
        missing_preview = ", ".join(missing[:20])
        suffix = "" if len(missing) <= 20 else f" ... (+{len(missing) - 20} more)"
        return FileResult(
            status="failed_missing_features",
            input_csv=str(input_csv),
            output_csv=None,
            rows=len(df),
            error=(
                f"Missing {len(missing)} model feature columns in {input_csv}: "
                f"{missing_preview}{suffix}"
            ),
        )

    x_new = df[feature_names]

    pred_indices = model.predict(x_new)
    pred_labels = encoder.inverse_transform(pred_indices)

    probs = model.predict_proba(x_new)
    confidence_scores = np.max(probs, axis=1)

    df_out = df.copy()
    df_out["Predicted_Label"] = pred_labels
    df_out["Confidence_Score"] = confidence_scores

    ensure_parent(output_csv)
    df_out.to_csv(output_csv, index=False)

    return FileResult(
        status="ok",
        input_csv=str(input_csv),
        output_csv=str(output_csv),
        rows=len(df_out),
        error=None,
    )


def write_manifest_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_manifest_csv(path: Path, results: list[FileResult]) -> None:
    ensure_parent(path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["status", "input_csv", "output_csv", "rows", "error"])
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def default_manifest_paths(output_dir: Path) -> tuple[Path, Path]:
    return output_dir / "manifest.json", output_dir / "manifest.csv"


def main() -> int:
    args = parse_args()
    set_thread_limits(args.workers)

    input_root = args.input_features.expanduser().resolve()
    output_root = args.output_dir.expanduser().resolve()
    model_path = args.model.expanduser().resolve()
    encoder_path = args.encoder.expanduser().resolve()

    output_root.mkdir(parents=True, exist_ok=True)

    try:
        model, encoder, feature_names = load_artifacts(model_path, encoder_path)
    except Exception as exc:
        print(f"ERROR failed to load model artifacts: {exc}")
        return 1

    csv_paths = iter_csv_files(input_root, args.recursive)
    if not csv_paths:
        print(f"ERROR no CSV files found in {input_root}")
        return 1

    results: list[FileResult] = []
    had_failure = False

    for input_csv in csv_paths:
        rel = input_csv.relative_to(input_root)
        output_csv = (output_root / rel).with_suffix(".csv")

        try:
            result = process_csv(input_csv, output_csv, model, encoder, feature_names)
        except Exception as exc:
            result = FileResult(
                status="failed_exception",
                input_csv=str(input_csv),
                output_csv=None,
                rows=0,
                error=f"Unhandled exception for {input_csv}: {exc}",
            )

        results.append(result)

        if result.status == "ok":
            print(f"OK    {result.input_csv} -> {result.output_csv} rows={result.rows}")
        elif result.status == "skipped_empty":
            print(f"SKIP  empty CSV: {result.input_csv}")
        else:
            had_failure = True
            print(f"ERROR {result.error}")

    ok_count = sum(1 for r in results if r.status == "ok")
    skipped_count = sum(1 for r in results if r.status == "skipped_empty")
    failed_count = len(results) - ok_count - skipped_count

    manifest_json, manifest_csv = default_manifest_paths(output_root)
    if args.manifest_json is not None:
        manifest_json = args.manifest_json.expanduser().resolve()
    if args.manifest_csv is not None:
        manifest_csv = args.manifest_csv.expanduser().resolve()

    summary = {
        "input_root": str(input_root),
        "output_root": str(output_root),
        "model_path": str(model_path),
        "encoder_path": str(encoder_path),
        "workers": max(1, int(args.workers)),
        "feature_count": len(feature_names),
        "discovered_csv_files": len(csv_paths),
        "ok_files": ok_count,
        "skipped_empty_files": skipped_count,
        "failed_files": failed_count,
        "results": [asdict(r) for r in results],
    }

    write_manifest_json(manifest_json, summary)
    write_manifest_csv(manifest_csv, results)

    print("")
    print(f"Summary: discovered={len(csv_paths)} ok={ok_count} skipped_empty={skipped_count} failed={failed_count}")
    print(f"Manifest JSON: {manifest_json}")
    print(f"Manifest CSV: {manifest_csv}")

    if had_failure:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
