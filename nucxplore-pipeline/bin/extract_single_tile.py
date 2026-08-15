#!/usr/bin/env python3
"""Extract features from a single image/MAT pair and write one feature CSV.

Supports optional nucleus crop export. Mirrors process_single_task from batch.py.
"""
from __future__ import annotations

import argparse
import csv
import json
import traceback
from pathlib import Path
from typing import Any

import numpy as np


def _unwrap_mat_scalar(value: Any) -> Any:
    current = value
    while isinstance(current, np.ndarray):
        if current.size == 0:
            return ""
        if current.ndim == 0:
            current = current.item()
            continue
        if current.size == 1:
            current = current.reshape(-1)[0]
            continue
        break
    if isinstance(current, bytes):
        return current.decode("utf-8", errors="ignore")
    if hasattr(current, "item") and not isinstance(current, str):
        try:
            return current.item()
        except Exception:
            return current
    return current


def load_instance_types(mat_path: Path, inst_type_key: str) -> dict[int, str]:
    try:
        from scipy.io import loadmat
    except ImportError:
        return {}
    mat_data = loadmat(mat_path)
    raw = mat_data.get(inst_type_key)
    if raw is None:
        return {}
    flat = np.asarray(raw, dtype=object).reshape(-1)
    result: dict[int, str] = {}
    for index, value in enumerate(flat, start=1):
        parsed = _unwrap_mat_scalar(value)
        result[index] = str(parsed).strip()
    return result


def crop_masked_patch(
    image: np.ndarray, nucleus_mask: np.ndarray, padding: int
) -> np.ndarray | None:
    coords = np.argwhere(nucleus_mask)
    if coords.size == 0:
        return None
    min_row, min_col = coords.min(axis=0)
    max_row, max_col = coords.max(axis=0)
    h, w = image.shape[:2]
    min_row = max(0, int(min_row) - padding)
    min_col = max(0, int(min_col) - padding)
    max_row = min(h - 1, int(max_row) + padding)
    max_col = min(w - 1, int(max_col) + padding)
    cropped = image[min_row : max_row + 1, min_col : max_col + 1].copy()
    mask = nucleus_mask[min_row : max_row + 1, min_col : max_col + 1]
    return cropped * mask[..., np.newaxis].astype(cropped.dtype)


def save_rgb_patch(path: Path, patch: np.ndarray) -> None:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.asarray(patch, dtype=np.uint8), mode="RGB").save(path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract features from a single image/MAT pair."
    )
    parser.add_argument("--image-path", required=True)
    parser.add_argument("--mat-path", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--mat-key", default=None)
    parser.add_argument("--inst-type-key", default="inst_type")
    parser.add_argument("--padding", type=int, default=10)
    parser.add_argument("--save-crops", action="store_true")
    parser.add_argument("--crop-output-dir", default=None)
    parser.add_argument("--use-gpu", action="store_true")
    parser.add_argument("--feature-schema", choices=("legacy", "dual", "v2"), default="legacy")
    args = parser.parse_args()

    from nucxplore._core import extract_features
    from nucxplore.io import load_instance_map, load_rgb_image
    from nucxplore.batch import V2_FEATURE_COLUMNS, legacy_fieldnames

    image_path = Path(args.image_path)
    mat_path = Path(args.mat_path)

    try:
        image = load_rgb_image(image_path)
        instance_map, _detected_key = load_instance_map(mat_path, preferred_key=args.mat_key)
        features = extract_features(
            image,
            instance_map.astype(np.uint32, copy=False),
            use_gpu=args.use_gpu,
            feature_schema=args.feature_schema,
        )
    except Exception as exc:
        print(f"ERROR failed to extract features: {exc}")
        raise SystemExit(1) from exc

    # Load instance types
    instance_types = load_instance_types(mat_path, args.inst_type_key)

    # Build CSV rows
    rows: list[dict[str, Any]] = []
    for feature_row in features:
        nucleus_id = int(round(float(feature_row.get("nucleus_id", 0))))
        row: dict[str, Any] = {"nucleus_id": nucleus_id}
        row["nucleus_type"] = instance_types.get(nucleus_id, "Unknown")
        for key, value in feature_row.items():
            if key == "nucleus_id":
                continue
            row[key] = value
        rows.append(row)

    schema_metadata = {"feature_schema": args.feature_schema,
                       "schema_version": 2 if args.feature_schema in ("dual", "v2") else 1,
                       "algorithm_revision": "v3.0",
                       "feature_count": {"legacy": 129, "dual": 218, "v2": 89}[args.feature_schema],
                       "stain_normalization": True, "padding": args.padding}
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{args.output_csv}.schema.json").write_text(
        json.dumps(schema_metadata, indent=2) + "\n", encoding="utf-8"
    )

    if not rows:
        Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_csv).write_text("nucleus_id,nucleus_type\n")
        return

    # Write CSV with deterministic column order
    if args.feature_schema == "v2":
        ordered = ["nucleus_id", "nucleus_type", *V2_FEATURE_COLUMNS]
    else:
        ordered = legacy_fieldnames((), rows)

    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ordered, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # Save crops if requested
    if args.save_crops and args.crop_output_dir:
        crop_root = Path(args.crop_output_dir)
        labels = sorted(int(l) for l in np.unique(instance_map) if int(l) != 0)
        for label in labels:
            mask = instance_map == label
            if not mask.any():
                continue
            patch = crop_masked_patch(image, mask, args.padding)
            if patch is not None:
                save_rgb_patch(crop_root / "nuclei" / f"nucleus_{label:04d}.png", patch)

    print(f"OK  {image_path.name} | nuclei={len(rows)} | csv={args.output_csv}")


if __name__ == "__main__":
    main()
