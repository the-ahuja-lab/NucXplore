#!/usr/bin/env python3
"""RGCI/HEIP segmentation — produce NucXplore-compatible MAT masks from crop tiles.

Replaces the RGCI_Seg_HEIP.ipynb cells with a deterministic CLI.  Uses the
HEIP SlidingWindowInferer without save_format so it writes ``inst_map`` and
``inst_type`` to .mat files that NucXplore can consume directly.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("rgci_seg")


def discover_crop_folders(crop_root: Path) -> List[Path]:
    """Return sorted list of subdirectories under *crop_root*."""
    dirs: List[Path] = []
    for entry in sorted(crop_root.iterdir()):
        if entry.is_dir():
            dirs.append(entry)
    return dirs


def load_heip_model(checkpoint_path: str):
    """Load the HEIP model from a pytorch_lightning checkpoint."""
    import torch
    from src.unet import get_seg_model, convert_state_dict, MODEL_PARTS

    logger.info("Loading HEIP model from %s …", checkpoint_path)
    model = get_seg_model()
    ckpt = torch.load(
        checkpoint_path,
        map_location=lambda storage, loc: storage,
        weights_only=False,
    )
    new_state_dict = convert_state_dict(
        MODEL_PARTS, model.state_dict(), ckpt["state_dict"]
    )
    model.load_state_dict(new_state_dict, strict=True)
    model.eval()
    logger.info("Model loaded successfully.")
    return model


def resolve_device(preferred: str) -> str:
    """Return *preferred* if available, else fall back to CPU."""
    import torch

    if preferred == "cuda" and not torch.cuda.is_available():
        logger.warning(
            "CUDA requested but not available — falling back to CPU"
        )
        return "cpu"
    return preferred


def run_inference(
    crop_root: Path,
    output_root: Path,
    checkpoint_path: str,
    device: str,
    n_devices: int,
    batch_size: int,
    patch_size: int,
    stride: int,
    padding: int,
) -> Dict[str, Any]:
    """Iterate crop subdirectories, run HEIP inference, save MAT masks.

    Returns a manifest dict.
    """
    crop_folders = discover_crop_folders(crop_root)
    output_root.mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, Any] = {
        "tool": "rgci_seg",
        "args": {
            "crop_root": str(crop_root),
            "output_root": str(output_root),
            "checkpoint": checkpoint_path,
            "device": device,
            "n_devices": n_devices,
            "batch_size": batch_size,
            "patch_size": patch_size,
            "stride": stride,
            "padding": padding,
        },
        "samples": [],
        "summary": {
            "total_samples": len(crop_folders),
            "successful": 0,
            "skipped": 0,
            "failed": 0,
        },
    }

    if not crop_folders:
        logger.error("No crop subdirectories found in %s", crop_root)
        manifest["summary"]["failed"] = 1
        return manifest

    from cellseg_models_pytorch.inference import SlidingWindowInferer

    model = load_heip_model(checkpoint_path)
    device = resolve_device(device)

    for sample_dir in crop_folders:
        sample_name = sample_dir.name
        save_dir = output_root / sample_name
        if save_dir.exists():
            logger.info("Skipping %s (already processed)", sample_name)
            sample_entry = {"sample": sample_name, "status": "skipped"}
            manifest["samples"].append(sample_entry)
            manifest["summary"]["skipped"] += 1
            continue

        save_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Processing %s → %s", sample_name, save_dir)

        try:
            t0 = time.monotonic()
            inferer = SlidingWindowInferer(
                model=model,
                input_folder=str(sample_dir),
                out_activations={
                    "inst": "softmax",
                    "type": "softmax",
                    "omnipose": None,
                },
                out_boundary_weights={
                    "inst": False,
                    "type": False,
                    "omnipose": True,
                },
                patch_size=(patch_size, patch_size),
                stride=stride,
                padding=padding,
                instance_postproc="omnipose",
                batch_size=batch_size,
                save_dir=str(save_dir),
                device=device,
                n_devices=n_devices,
            )
            inferer.infer()
            elapsed = time.monotonic() - t0
            logger.info(
                "Finished %s in %.1fs", sample_name, elapsed
            )

            sample_entry = {
                "sample": sample_name,
                "status": "ok",
                "elapsed_sec": round(elapsed, 1),
            }
            manifest["samples"].append(sample_entry)
            manifest["summary"]["successful"] += 1

        except Exception:
            logger.exception("Failed to process %s", sample_name)
            sample_entry = {"sample": sample_name, "status": "failed"}
            manifest["samples"].append(sample_entry)
            manifest["summary"]["failed"] += 1

    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="RGCI/HEIP segmentation — produce NucXplore-compatible MAT masks from crop tiles."
    )
    parser.add_argument(
        "--crop-root",
        required=True,
        help="Root containing subdirectories of cropped PNG tiles (one per slide)",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Output root for mirrored structure of MAT masks",
    )
    parser.add_argument(
        "--checkpoint",
        default="/opt/heip/models/last.ckpt",
        help="Path to HEIP pytorch_lightning checkpoint (default: /opt/heip/models/last.ckpt)",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device to run inference on (default: cuda, falls back to cpu if unavailable)",
    )
    parser.add_argument(
        "--n-devices",
        type=int,
        default=1,
        help="Number of devices for model forward (default: 1)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Batch size (default: 8)",
    )
    parser.add_argument(
        "--patch-size",
        type=int,
        default=256,
        help="Patch size in pixels (default: 256)",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=80,
        help="Sliding window stride in pixels (default: 80)",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=120,
        help="Padding in pixels (default: 120)",
    )
    parser.add_argument(
        "--heip-root",
        default="/opt/heip",
        help="HEIP source root directory (so `from src.unet import ...` works; default: /opt/heip)",
    )
    parser.add_argument(
        "--output-manifest",
        default="segmentation_manifest.json",
        help="Path for the output manifest JSON (default: segmentation_manifest.json)",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Optional path for structured log output",
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

    # Ensure HEIP source is importable.
    if args.heip_root not in sys.path:
        sys.path.insert(0, args.heip_root)

    manifest = run_inference(
        crop_root=Path(args.crop_root),
        output_root=Path(args.output_root),
        checkpoint_path=args.checkpoint,
        device=args.device,
        n_devices=args.n_devices,
        batch_size=args.batch_size,
        patch_size=args.patch_size,
        stride=args.stride,
        padding=args.padding,
    )

    manifest_path = Path(args.output_manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info("Manifest written to %s", manifest_path)

    failures = manifest["summary"]["failed"]
    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
