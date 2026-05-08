# Repository Guidelines

## Project Structure & Module Organization

This combined repository contains two NucXplore subprojects:

- `nucxplore/` — Rust + PyO3 Python package for histopathology nucleus feature extraction. Rust source lives in `nucxplore/src/`: `features/` contains CPU feature implementations, `gpu/` contains WGPU backends and WGSL shaders, `io/` handles image and MATLAB input, and `stain_norm/` contains stain normalization. Python wrappers, type stubs, and compatibility packages live in `nucxplore/python/`. Integration tests are in `nucxplore/tests/`, benchmarks in `nucxplore/benches/`, examples in `nucxplore/examples/`, and developer notes in `nucxplore/docs/`.

- `nucxplore-pipeline/` — Nextflow workflow covering WSI crop/filtering, RGCI/HEIP segmentation, NucXplore feature extraction, and XGBoost cell-type prediction. The pipeline is run via `nextflow run <org>/<repo> -r <tag>` for hosted use or `nextflow run .` / `nextflow run ./nucxplore-pipeline` from a local checkout.

Upstream slide cropping/filtering and RGCI/HEIP segmentation planning should reference `CropAndFiltering.ipynb`, `RGCI_Seg_HEIP.ipynb`, `HEIP/HEIP/src/scripts/infer_wsi.py`, `HEIP/HEIP/src/unet.py`, and `HEIP/HEIP/last.ckpt`. The crop/filter notebook uses hard-coded source and output paths; any production script, Docker image, or Nextflow process must replace those with configurable parameters. The segmentation notebook uses `HEIP/HEIP` code plus `cellseg-models-pytorch` and must likewise expose patch input root, segmentation MAT output root, checkpoint path, device, patch size, stride, padding, and batch size through CLI or Nextflow params. Use a CUDA segmentation container with `last.ckpt` baked into the image unless a later plan explicitly changes that.

Pipeline planning notes live in `plans/`. The upstream crop/segmentation integration draft is `plans/upstream-crop-segmentation-nextflow.md`.

## Build, Test, and Development Commands

### Package (rustenv)

Run commands from `nucxplore/`:

- `python -m pip install -r requirements.txt`: install development dependencies.
- `maturin build --release --out dist --interpreter python`: build a release wheel.
- `python -m pip install --force-reinstall --no-deps dist/nucxplore-*.whl`: install the local wheel.
- `cargo fmt --all`: format Rust code.
- `cargo test --tests`: run Rust integration tests.
- `cargo bench --bench benchmark_suite`: run Criterion benchmarks.
- `python -m py_compile python/nucxplore/batch.py scripts/batch_extract_and_crop.py`: quick Python syntax check.

If using `PYTHONPATH=python`, rebuild after Rust changes so `python/nucxplore/_core.abi3.so` is current.

### Pipeline (nextflow)

Run commands from `nucxplore-pipeline/`:

- `nextflow run . -stub-run`: run the pipeline in stub mode.
- `bash tests/run_stub_pipeline_checks.sh`: run stub contract checks.
- `python -m pytest tests/test_pipeline_contract.py tests/test_cell_type_predict.py`: run Python tests.

From the repo root, use `nextflow run ./nucxplore-pipeline` or depend on the root `nextflow.config` facade for `nextflow run .`.

## Release Workflow

- PyPI wheels are built from `nucxplore/` on tags matching `nucxplore-v*`.
- Pipeline Docker images are published manually to Docker Hub (not part of package CI).
- Pipeline validation is local unless a future task adds a separate CI workflow.

## Coding Style & Naming Conventions

Use Rust 2021 idioms and keep code `cargo fmt` clean. Name Rust modules and functions in `snake_case`, public types in `PascalCase`, and constants in `SCREAMING_SNAKE_CASE`. Keep Python package code typed where practical; maintain `.pyi` stubs and `py.typed` markers when API signatures change. Avoid broad refactors during feature or bug work.

## Testing Guidelines

Add Rust integration tests under `nucxplore/tests/` using descriptive names such as `test_crop_export.rs`. Add Python API checks as `test_*.py` for wrapper or batch behavior. Prefer narrow tests first, then run `cargo test --tests` before submitting. For performance changes, capture baseline benchmark numbers before editing and compare with `cargo bench --bench benchmark_suite`. For pipeline changes, run `bash tests/run_stub_pipeline_checks.sh` from `nucxplore-pipeline/`.

## Commit & Pull Request Guidelines

Use concise Conventional Commit messages, for example `fix(io): validate mat instance map shape` or `feat(batch): export normalized crops`. Pull requests should include a problem statement, implementation summary, validation commands, linked issues when applicable, and screenshots or sample outputs for notebook, crop, or visualization changes.

## Security & Configuration Tips

Do not commit secrets, `.env` files, private keys, generated wheels, or large derived artifacts. Keep optional GPU behavior guarded and provide CPU fallbacks. Use `NUQR_ENABLE_STAIN_NORMALIZATION` only for runs that intentionally require Vahadane post-normalization.
