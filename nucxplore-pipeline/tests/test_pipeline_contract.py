from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def test_stub_pipeline_contract(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    if shutil.which("nextflow") is None:
        pytest.skip("Nextflow is not available on PATH")

    test_dir = tmp_path / "nf_contract_test"
    shutil.copytree(
        repo,
        test_dir,
        ignore=shutil.ignore_patterns("work", ".nextflow*", "dist", "__pycache__"),
    )
    local_script = test_dir / "tests" / "run_stub_pipeline_checks.sh"
    env = dict(os.environ)
    env.setdefault("NXF_ANSI_LOG", "false")
    args = ["bash", str(local_script)]
    proc = subprocess.run(args, cwd=test_dir, capture_output=True, text=True, env=env)
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


def test_nucxplore_seg_empty_input_returns_nonzero(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    script = str(repo / "bin" / "nucxplore_seg_to_mat.py")
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


def test_nucxplore_seg_empty_input_does_not_load_model(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    script = str(repo / "bin" / "nucxplore_seg_to_mat.py")
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


def test_nucxplore_seg_nextflow_gpu_and_cleanup_contract() -> None:
    repo = Path(__file__).resolve().parents[1]
    main_nf = (repo / "main.nf").read_text()

    assert "process NUCXPLORE_SEG" in main_nf
    assert "accelerator request:" in main_nf
    assert "params.seg_device == 'cuda'" in main_nf
    assert "exec nucxplore_seg_to_mat.py" in main_nf


def test_nextflow_cli_boolean_flags_are_parsed_explicitly() -> None:
    repo = Path(__file__).resolve().parents[1]
    main_nf = (repo / "main.nf").read_text()

    assert "def boolParam(value)" in main_nf
    assert "value.toString().trim().toLowerCase() in ['true', '1', 'yes', 'y', 'on']" in main_nf
    assert "as Boolean" not in main_nf


def test_raw_feature_and_replacement_artifact_contract() -> None:
    repo = Path(__file__).resolve().parents[1]
    active_files = [
        repo / "main.nf",
        repo / "nextflow.config",
        repo / "params.example.yaml",
        repo / "bin" / "extract_single_tile.py",
    ]
    active_text = "\n".join(path.read_text(encoding="utf-8") for path in active_files)

    assert "normalize_staining" not in active_text
    assert "save_pre_normalized_crops" not in active_text
    assert "save_post_normalized_crops" not in active_text
    assert "/opt/nucxplore/models/xgboost_best_model.pkl" in active_text
    assert "/opt/nucxplore/models/label_encoder.pkl" in active_text
    assert (repo / "models" / "xgboost_best_model.pkl").is_file()
    assert (repo / "models" / "label_encoder.pkl").is_file()


def test_demo_launcher_contract() -> None:
    repo = Path(__file__).resolve().parents[1]
    demo = repo / "examples" / "demo"
    launcher = demo / "run_demo.sh"
    launcher_text = launcher.read_text(encoding="utf-8")

    syntax = subprocess.run(
        ["bash", "-n", str(launcher)], capture_output=True, text=True
    )
    assert syntax.returncode == 0, syntax.stderr

    help_result = subprocess.run(
        ["bash", str(launcher), "full", "--help"], capture_output=True, text=True
    )
    assert help_result.returncode == 0, help_result.stderr
    assert "run_demo.sh intermediate" in help_result.stdout

    invalid = subprocess.run(
        ["bash", str(launcher), "unknown"], capture_output=True, text=True
    )
    assert invalid.returncode != 0
    assert "expected full or intermediate" in invalid.stderr

    assert "releases/download/demo-data-v1" in launcher_text
    assert "d15569bc5c725a7635692376df34733bbd7fa2288db7e8a271d70b177e80cd93" in launcher_text
    assert "b571e9eaecf57a11db4f84ab7f0becaaf48b571e25c36ccc00ba9279c8a6987a" in launcher_text
    assert "Expected 8 PNG inputs" in launcher_text
    assert "Expected 8 MAT inputs" in launcher_text
    assert '-profile docker' not in launcher_text
    assert 'm.version("nucxplore") == "0.3.0"' in launcher_text


def test_demo_parameter_stage_contracts() -> None:
    repo = Path(__file__).resolve().parents[1]
    demo = repo / "examples" / "demo"
    full_params = (demo / "full.params.yaml").read_text(encoding="utf-8")
    intermediate_params = (demo / "intermediate.params.yaml").read_text(
        encoding="utf-8"
    )

    assert "from_stage: crop" in full_params
    assert "to_stage: prediction" in full_params
    assert "seg_device: cpu" in full_params
    assert "publish_crops: true" in full_params
    assert "publish_segmentation: true" in full_params

    assert "from_stage: features" in intermediate_params
    assert "to_stage: prediction" in intermediate_params
    assert "input_mode: roots" in intermediate_params
    assert "feature_schema: legacy" in intermediate_params


def test_prediction_batches_collected_features_as_one_directory() -> None:
    repo = Path(__file__).resolve().parents[1]
    main_nf = (repo / "main.nf").read_text(encoding="utf-8")

    assert "path feature_inputs, stageAs: 'feature_inputs/*'" in main_nf
    assert "--input-features feature_inputs" in main_nf
    assert "--input-features ${features_dir}" not in main_nf
