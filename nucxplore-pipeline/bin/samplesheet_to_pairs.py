#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path


REQUIRED_COLUMNS = ("sample_id", "image_path", "mat_path")


@dataclass
class RowRecord:
    sample_id: str
    image_path: str
    mat_path: str
    staged_image: str
    staged_mat: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a samplesheet and stage mirrored image/MAT roots via symlinks"
    )
    parser.add_argument("--samplesheet", type=Path, required=True)
    parser.add_argument("--images-out", type=Path, required=True)
    parser.add_argument("--mats-out", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    return parser.parse_args()


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def safe_name(sample_id: str) -> str:
    clean = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in sample_id)
    return clean.strip("_") or "sample"


def _resolve_input_path(raw_path: str, samplesheet_dir: Path) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (samplesheet_dir / candidate).resolve()


def stage_samplesheet(samplesheet: Path, images_out: Path, mats_out: Path, manifest: Path) -> None:
    if not samplesheet.exists():
        raise FileNotFoundError(f"Samplesheet not found: {samplesheet}")

    clean_dir(images_out)
    clean_dir(mats_out)

    records: list[RowRecord] = []
    used_names: set[str] = set()

    samplesheet_dir = samplesheet.parent

    with samplesheet.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Samplesheet is empty or missing header")

        missing_cols = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing_cols:
            raise ValueError(
                f"Samplesheet missing required columns: {', '.join(missing_cols)}"
            )

        for idx, row in enumerate(reader, start=2):
            sample_id = (row.get("sample_id") or "").strip()
            image_path_raw = (row.get("image_path") or "").strip()
            mat_path_raw = (row.get("mat_path") or "").strip()

            if not sample_id:
                raise ValueError(f"Line {idx}: sample_id is empty")
            if not image_path_raw:
                raise ValueError(f"Line {idx}: image_path is empty")
            if not mat_path_raw:
                raise ValueError(f"Line {idx}: mat_path is empty")

            image_path = _resolve_input_path(image_path_raw, samplesheet_dir)
            mat_path = _resolve_input_path(mat_path_raw, samplesheet_dir)

            if not image_path.exists():
                raise FileNotFoundError(f"Line {idx}: image file not found: {image_path}")
            if not mat_path.exists():
                raise FileNotFoundError(f"Line {idx}: MAT file not found: {mat_path}")

            sample_key = safe_name(sample_id)
            if sample_key in used_names:
                raise ValueError(
                    f"Duplicate sample_id after sanitization: {sample_id} -> {sample_key}"
                )
            used_names.add(sample_key)

            image_ext = image_path.suffix or ".png"
            staged_image = images_out / sample_key / f"tile{image_ext}"
            staged_mat = mats_out / sample_key / "tile.mat"

            staged_image.parent.mkdir(parents=True, exist_ok=True)
            staged_mat.parent.mkdir(parents=True, exist_ok=True)

            if staged_image.exists() or staged_image.is_symlink():
                staged_image.unlink()
            if staged_mat.exists() or staged_mat.is_symlink():
                staged_mat.unlink()

            os.symlink(str(image_path), str(staged_image))
            os.symlink(str(mat_path), str(staged_mat))

            records.append(
                RowRecord(
                    sample_id=sample_id,
                    image_path=str(image_path),
                    mat_path=str(mat_path),
                    staged_image=str(staged_image),
                    staged_mat=str(staged_mat),
                )
            )

    if not records:
        raise ValueError("Samplesheet contains no rows")

    manifest.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "samplesheet": str(samplesheet),
        "staged_images_root": str(images_out),
        "staged_mats_root": str(mats_out),
        "sample_count": len(records),
        "records": [asdict(r) for r in records],
    }
    manifest.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    try:
        stage_samplesheet(
            samplesheet=args.samplesheet.expanduser().resolve(),
            images_out=args.images_out,
            mats_out=args.mats_out,
            manifest=args.manifest,
        )
    except Exception as exc:
        print(f"ERROR {exc}")
        return 1

    print(f"OK staged samplesheet: {args.samplesheet}")
    print(f"OK images root: {args.images_out}")
    print(f"OK mats root: {args.mats_out}")
    print(f"OK manifest: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
