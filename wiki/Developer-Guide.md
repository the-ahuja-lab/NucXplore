# Developer Guide

This page collects detailed maintenance guidance for the package and pipeline. Public user docs stay in each component README and `docs/user-guide.md`.

## Repository Layout

| Path | Purpose |
|---|---|
| `nucxplore/` | Rust + PyO3 Python package. |
| `nucxplore-pipeline/` | Nextflow workflow and Docker runtime definitions. |
| `plans/` | Active and historical implementation plans. |
| `wiki/` | GitHub-wiki-ready detailed documentation pages. |

## Package Development

Run from `nucxplore/`:

```bash
python -m pip install -r requirements.txt
maturin build --release --out dist --interpreter python
python -m pip install --force-reinstall --no-deps dist/nucxplore-*.whl
cargo fmt --all
cargo test --tests
python -m py_compile python/nucxplore/batch.py scripts/batch_extract_and_crop.py
```

Source map:

| Path | Purpose |
|---|---|
| `src/lib.rs` | PyO3 module entrypoint. |
| `src/features/` | CPU feature implementations. |
| `src/gpu/` | WGPU backends and WGSL shaders. |
| `src/io/` | Rust image and MATLAB v5 readers. |
| `src/stain_norm/` | Vahadane stain normalization. |
| `python/nucxplore/` | Python wrappers, type stubs, and `py.typed`. |
| `tests/` | Rust integration tests and Python API checks. |
| `benches/` | Criterion benchmark suite. |

Preserve these API contracts:

| API | Contract |
|---|---|
| `extract_features` | Accepts `(H, W, 3)` `uint8` image and instance map or boolean masks. |
| `extract_features_from_files` | Loads image and MAT in Rust; auto-detects MAT key when safe. |
| `save_cropped_nuclei_from_files` | Writes selected crop directories and returns crop records. |
| `batch_extract_and_crop` | Writes per-image CSVs and optional crop PNGs. |
| `BatchExtractor` | Reusable class API for batch extraction workflows. |

Update `python/nucxplore/_core.pyi`, `python/nucxplore/batch.pyi`, and docs whenever public signatures change.

## Pipeline Development

Run from `nucxplore-pipeline/`:

```bash
bash tests/run_stub_pipeline_checks.sh
python -m pytest tests/test_pipeline_contract.py tests/test_cell_type_predict.py
```

Stage contract:

| Stage | Process | Required active image parameter | Entry input |
|---|---|---|---|
| `crop` | `CROP_AND_FILTER` | `crop_filter_container` | `slide_root` |
| `segmentation` | `RGCI_SEG` | `seg_container` | `crop_root` or crop output channel |
| `features` | `EXTRACT_FEATURES` | `container` | image/MAT roots, samplesheet, or segmentation output |
| `prediction` | `PREDICT_CELL_TYPES` | `container` | `features_root` or feature output channel |

Keep stage names stable: `crop`, `segmentation`, `features`, `prediction`.

## Parameter Maintenance

When changing a user-visible parameter, update:

| File | Required update |
|---|---|
| `nucxplore-pipeline/nextflow.config` | Default value and grouping. |
| `nucxplore-pipeline/params.example.yaml` | Example value and comment. |
| `nucxplore-pipeline/docs/user-guide.md` | Concise mention if users need it. |
| `wiki/Pipeline-Parameters.md` | Full reference. |
| `nucxplore-pipeline/tests/` | Contract coverage. |

## Release Boundaries

| Component | Release path |
|---|---|
| Package | GitHub Actions build/publish PyPI wheels on `nucxplore-v*` tags. |
| Pipeline | Docker images are built and pushed manually. |
| Pipeline validation | Local unless a future CI workflow is added. |

## Docker Publishing Checklist

```bash
bash nucxplore-pipeline/scripts/build_docker_images.sh
bash nucxplore-pipeline/scripts/run_local_svs_pipeline.sh /path/to/slide.svs
docker push ahujalab/nucxplore-crop-filter:latest
docker push ahujalab/nucxplore-rgci-seg:latest
docker push ahujalab/nucxplore-cell-type-prediction:latest
```

Before pushing, confirm the feature/prediction image was built from the intended local `nucxplore/` checkout and contains the expected model artifacts.

## Documentation Policy

- Keep root and component READMEs concise.
- Keep `docs/user-guide.md` short and user-oriented.
- Keep detailed operational content in `wiki/*.md`.
- Add changelog entries for user-visible behavior, public APIs, and durable documentation changes.
