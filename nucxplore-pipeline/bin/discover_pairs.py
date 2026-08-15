#!/usr/bin/env python3
"""Discover (image, mat) file pairs from matching crop and segmentation roots.

Walks *crop_root* for PNG tiles and *mat_root* for MAT segmentations, matches
files by stem name (e.g. ``patch_x-1000_y-2000``), and writes a CSV with one
row per matched pair.

Output columns: ``tile_name,image_path,mat_path``
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover image/MAT pairs by tile name."
    )
    parser.add_argument("--crop-root", required=True)
    parser.add_argument("--mat-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--image-exts", default=".png,.jpg,.jpeg,.tif,.tiff,.bmp")
    parser.add_argument("--mat-exts", default=".mat")
    args = parser.parse_args()

    crop_root = Path(args.crop_root).expanduser().resolve()
    mat_root = Path(args.mat_root).expanduser().resolve()
    image_exts = tuple(e.strip().lower() for e in args.image_exts.split(",") if e.strip())
    mat_exts = tuple(e.strip().lower() for e in args.mat_exts.split(",") if e.strip())

    if not crop_root.is_dir():
        raise SystemExit(f"crop root not found: {crop_root}")
    if not mat_root.is_dir():
        raise SystemExit(f"mat root not found: {mat_root}")

    # Index images by stem
    images_by_stem: dict[str, Path] = {}
    for path in crop_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in image_exts:
            images_by_stem[path.stem] = path

    # Index mats by stem
    mats_by_stem: dict[str, Path] = {}
    for path in mat_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in mat_exts:
            mats_by_stem[path.stem] = path

    # Find common stems
    common = sorted(images_by_stem.keys() & mats_by_stem.keys())

    if not common:
        print(f"WARN no matching pairs found between {crop_root} and {mat_root}")
        # Still write an empty CSV with headers
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["tile_name", "image_path", "mat_path"])
        raise SystemExit(0)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["tile_name", "image_path", "mat_path"])
        for stem in common:
            writer.writerow([stem, str(images_by_stem[stem]), str(mats_by_stem[stem])])

    print(f"OK discovered {len(common)} pairs | output={args.output}")


if __name__ == "__main__":
    main()
