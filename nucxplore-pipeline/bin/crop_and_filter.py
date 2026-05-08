#!/usr/bin/env python3
"""Crop whole-slide images into PNG tiles with blank/partial-tile filtering.

Replaces the three notebook cells in CropAndFiltering.ipynb with a single
deterministic CLI that tiles, filters, and emits a manifest.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger("crop_and_filter")

TILE_NAME_PATTERN = "patch_x-{x}_y-{y}.png"


def discover_slides(slide_root: Path, exts: List[str], recursive: bool = False) -> List[Path]:
    """Return sorted list of WSI paths matching any of *exts* (case-insensitive)."""
    slides: List[Path] = []
    lower_exts = tuple(e.lower() for e in exts)
    entries = slide_root.rglob("*") if recursive else slide_root.iterdir()
    for entry in sorted(entries):
        if entry.is_file() and entry.name.lower().endswith(lower_exts):
            slides.append(entry)
    return slides


def tile_slide(
    slide_path: Path,
    output_dir: Path,
    tile_size: int,
    mean_threshold: float,
    std_threshold: float,
    drop_partial: bool,
) -> Tuple[int, int, int]:
    """Tile *slide_path* into *output_dir*, returning (total, kept, filtered).

    Tiles are named ``patch_x-{x}_y-{y}.png``.  Blank and partial tiles are
    silently skipped.
    """
    total = 0
    kept = 0
    filtered = 0

    with _open_slide(slide_path) as slide:
        level = 0
        dims = slide.level_dimensions[level]
        width, height = dims

        for x in range(0, width, tile_size):
            for y in range(0, height, tile_size):
                total += 1
                x_end = min(x + tile_size, width)
                y_end = min(y + tile_size, height)
                read_w = x_end - x
                read_h = y_end - y

                try:
                    region = slide.read_region(
                        (x, y), level, (read_w, read_h)
                    )
                except Exception:
                    filtered += 1
                    logger.warning(
                        "Failed to read region x=%d y=%d from %s — skipping",
                        x,
                        y,
                        slide_path.name,
                    )
                    continue

                tile = region.convert("RGB")

                if drop_partial and (read_w < tile_size or read_h < tile_size):
                    filtered += 1
                    continue

                arr = np.asarray(tile, dtype=np.float32)
                gray = arr.mean(axis=2)
                mu = float(gray.mean())
                sigma = float(gray.std())

                if mu > mean_threshold and sigma < std_threshold:
                    filtered += 1
                    continue

                tile_name = TILE_NAME_PATTERN.format(x=x, y=y)
                tile.save(str(output_dir / tile_name))
                kept += 1

    return total, kept, filtered


def _open_slide(slide_path: Path):
    """Open a WSI with tiffslide (lazy import to keep CLI responsive)."""
    import tiffslide  # noqa: D205 (lazy)
    return tiffslide.open_slide(str(slide_path))


def process_slides(args: argparse.Namespace) -> Dict:
    """Main workhorse.  Returns the manifest dict for JSON output."""
    output_root = Path(args.output_root)
    slide_root = Path(args.slide_root)

    if not slide_root.exists():
        logger.error("Slide root does not exist: %s", slide_root)
        sys.exit(1)

    exts = [e.strip() for e in args.slide_exts.split(",") if e.strip()]
    if not exts:
        logger.error("No slide extensions configured")
        sys.exit(1)

    slides = discover_slides(slide_root, exts, recursive=args.recursive)
    logger.info("Discovered %d slide(s) in %s", len(slides), slide_root)

    output_root.mkdir(parents=True, exist_ok=True)

    manifest: Dict = {
        "tool": "crop_and_filter",
        "args": {
            "slide_root": str(slide_root),
            "output_root": str(output_root),
            "tile_size": args.tile_size,
            "mean_threshold": args.mean_threshold,
            "std_threshold": args.std_threshold,
            "drop_partial_tiles": args.drop_partial_tiles,
            "slide_exts": args.slide_exts,
            "recursive": args.recursive,
        },
        "slides": [],
        "summary": {
            "total_slides": len(slides),
            "successful_slides": 0,
            "failed_slides": 0,
            "total_tiles": 0,
            "kept_tiles": 0,
            "filtered_tiles": 0,
        },
    }

    t0 = time.monotonic()

    for slide_path in slides:
        slide_name = slide_path.stem
        slide_out = output_root / slide_name
        slide_out.mkdir(parents=True, exist_ok=True)

        slide_entry: Dict = {
            "slide": slide_path.name,
            "slide_path": str(slide_path),
            "output_dir": str(slide_out),
            "tiles_total": 0,
            "tiles_kept": 0,
            "tiles_filtered": 0,
        }

        try:
            total, kept, filtered = tile_slide(
                slide_path,
                slide_out,
                args.tile_size,
                args.mean_threshold,
                args.std_threshold,
                args.drop_partial_tiles,
            )
        except Exception:
            logger.exception("Failed to process slide %s", slide_path.name)
            slide_entry.update(
                {"status": "failed", "tiles_total": 0, "tiles_kept": 0, "tiles_filtered": 0}
            )
            manifest["summary"]["failed_slides"] += 1
            manifest["slides"].append(slide_entry)
            continue

        slide_entry.update(
            {
                "status": "ok",
                "tiles_total": total,
                "tiles_kept": kept,
                "tiles_filtered": filtered,
            }
        )
        manifest["summary"]["successful_slides"] += 1
        manifest["summary"]["total_tiles"] += total
        manifest["summary"]["kept_tiles"] += kept
        manifest["summary"]["filtered_tiles"] += filtered
        manifest["slides"].append(slide_entry)

    elapsed = time.monotonic() - t0
    manifest["summary"]["elapsed_sec"] = round(elapsed, 1)

    if kept := manifest["summary"]["kept_tiles"]:
        logger.info(
            "Done: %d/%d tiles kept, %d filtered, %.1fs",
            kept,
            manifest["summary"]["total_tiles"],
            manifest["summary"]["filtered_tiles"],
            elapsed,
        )
    else:
        logger.warning("No tiles kept after filtering. Check thresholds and slide content.")

    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Crop WSI slides into HEIP-compatible PNG tiles with blank/partial filtering."
    )
    parser.add_argument("--slide-root", required=True, help="Directory containing WSI files")
    parser.add_argument("--output-root", required=True, help="Output root for cropped tiles")
    parser.add_argument(
        "--tile-size", type=int, default=1250, help="Tile width and height in pixels (default: 1250)"
    )
    parser.add_argument(
        "--mean-threshold",
        type=float,
        default=220,
        help="Grayscale mean threshold for blank detection (default: 220)",
    )
    parser.add_argument(
        "--std-threshold",
        type=float,
        default=15,
        help="Grayscale std threshold for blank detection (default: 15)",
    )
    parser.add_argument(
        "--no-drop-partial-tiles",
        dest="drop_partial_tiles",
        action="store_false",
        help="Keep partial edge tiles instead of dropping them",
    )
    parser.set_defaults(drop_partial_tiles=True)
    parser.add_argument(
        "--slide-exts",
        default=".ndpi,.svs,.tif,.tiff",
        help="Comma-separated list of slide extensions (default: .ndpi,.svs,.tif,.tiff)",
    )
    parser.add_argument(
        "--output-manifest",
        default="crop_manifest.json",
        help="Path for the output manifest JSON (default: crop_manifest.json)",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Optional path for structured log output",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=False,
        help="Recursively search for slides under slide-root (disabled by default for WSI scans)",
    )

    args = parser.parse_args(argv)

    log_handlers: list = [logging.StreamHandler(sys.stderr)]
    if args.log_file:
        Path(args.log_file).parent.mkdir(parents=True, exist_ok=True)
        log_handlers.append(logging.FileHandler(args.log_file))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=log_handlers,
    )

    manifest = process_slides(args)
    manifest_path = Path(args.output_manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info("Manifest written to %s", manifest_path)

    failures = manifest["summary"]["failed_slides"]
    if manifest["summary"]["total_slides"] == 0:
        logger.error("No slides discovered in %s with extensions %s", args.slide_root, args.slide_exts)
        return 1
    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
