from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_stub_pipeline_contract() -> None:
    repo = Path(__file__).resolve().parents[1]
    script = repo / "tests" / "run_stub_pipeline_checks.sh"
    env = dict(os.environ)
    env.setdefault("NXF_ANSI_LOG", "false")
    args = ["micromamba", "run", "-n", "nextflow", "bash", str(script)]
    proc = subprocess.run(args, cwd=repo, capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    assert "OK milestone5 stub checks passed" in proc.stdout


def test_crop_slide_discovery_honors_recursive_flag(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo / "bin"))

    from crop_and_filter import discover_slides

    root_slide = tmp_path / "root.svs"
    nested_dir = tmp_path / "nested"
    nested_slide = nested_dir / "nested.SVS"
    nested_dir.mkdir()
    root_slide.write_text("")
    nested_slide.write_text("")

    assert discover_slides(tmp_path, [".svs"]) == [root_slide]
    assert discover_slides(tmp_path, [".svs"], recursive=True) == [nested_slide, root_slide]


def test_crop_and_filter_empty_input_returns_nonzero(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    script = str(repo / "bin" / "crop_and_filter.py")
    empty_dir = tmp_path / "no_slides"
    empty_dir.mkdir()
    out_dir = tmp_path / "crop_out"
    manifest = tmp_path / "manifest.json"

    proc = subprocess.run(
        ["python3", script,
         "--slide-root", str(empty_dir),
         "--output-root", str(out_dir),
         "--output-manifest", str(manifest)],
        capture_output=True, text=True,
    )
    assert proc.returncode != 0, f"Expected nonzero exit, got {proc.returncode}"
    assert out_dir.exists()


def test_rgci_seg_empty_input_returns_nonzero(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    script = str(repo / "bin" / "rgci_seg_to_mat.py")
    empty_crop = tmp_path / "no_crops"
    empty_crop.mkdir()
    out_dir = tmp_path / "seg_out"
    manifest = tmp_path / "manifest.json"

    proc = subprocess.run(
        ["python3", script,
         "--crop-root", str(empty_crop),
         "--output-root", str(out_dir),
         "--output-manifest", str(manifest),
         "--heip-root", str(repo.parent / "HEIP" / "HEIP" / "src")],
        capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": ""},
    )
    assert proc.returncode != 0, f"Expected nonzero exit, got {proc.returncode}"
    assert out_dir.exists()


def test_rgci_seg_empty_input_does_not_load_model(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    script = str(repo / "bin" / "rgci_seg_to_mat.py")
    empty_crop = tmp_path / "no_crops2"
    empty_crop.mkdir()
    out_dir = tmp_path / "seg_out2"
    manifest = tmp_path / "manifest2.json"

    # Use a nonexistent checkpoint to prove model is never loaded for empty input
    proc = subprocess.run(
        ["python3", script,
         "--crop-root", str(empty_crop),
         "--output-root", str(out_dir),
         "--output-manifest", str(manifest),
         "--checkpoint", "/nonexistent/checkpoint.ckpt",
         "--heip-root", str(repo.parent / "HEIP" / "HEIP" / "src")],
        capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": ""},
    )
    # Should fail because of empty input, not because of missing checkpoint
    assert proc.returncode != 0, f"Expected nonzero exit, got {proc.returncode}"
    assert "No crop subdirectories found" in (proc.stdout + proc.stderr)
    assert out_dir.exists()
