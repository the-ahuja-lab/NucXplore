# nucxplore-pipeline Developer Guide

This guide is for contributors maintaining the Nextflow pipeline. User setup, run examples, parameters, outputs, and troubleshooting are in [`user-guide.md`](user-guide.md).

## Repository Boundary

This pipeline lives in the `nucxplore-pipeline/` subdirectory of the [NucXplore](https://github.com/<org>/<repo>) repository. The `nucxplore` Python package is built and published separately from `nucxplore/`. Pipeline runtime images should consume released package wheels from PyPI, not an unpublished source-tree checkout.

## Source Layout

| Path | Purpose |
|---|---|
| `main.nf` | Four-stage Nextflow workflow. |
| `nextflow.config` | Parameter defaults and profile includes. |
| `conf/docker.config` | Docker profile and per-stage container binding. |
| `bin/crop_and_filter.py` | WSI crop/filter CLI. |
| `bin/rgci_seg_to_mat.py` | RGCI/HEIP segmentation to MAT CLI. |
| `bin/samplesheet_to_pairs.py` | Samplesheet validation and pair expansion. |
| `bin/cell_type_predict.py` | XGBoost cell-type prediction CLI. |
| `Dockerfile.crop-filter` | Crop/filter image definition. |
| `Dockerfile.rgci-seg` | CUDA segmentation image definition. |
| `Dockerfile` | Features and prediction image definition. |
| `params.example.yaml` | User-editable parameter contract example. |
| `tests/` | Stub contract and Python unit tests. |
| `docs/` | User and developer documentation. |

## Stage Contract

| Stage | Process | Required image parameter | Entry input |
|---|---|---|---|
| `crop` | `CROP_AND_FILTER` | `crop_filter_container` | `slide_root` |
| `segmentation` | `RGCI_SEG` | `seg_container` | `crop_root` or crop output channel |
| `features` | feature extraction process | `container` | `image_root`/`mat_root`, samplesheet, or segmentation output channel |
| `prediction` | prediction process | `container` | `features_root` or feature output channel |

Keep stage ranges contiguous and preserve the allowed stage names: `crop`, `segmentation`, `features`, `prediction`.

## Local Development Setup

Activate the `nextflow` micromamba environment, then run commands from `nucxplore-pipeline/`:

```bash
micromamba activate nextflow
```

Useful validation commands:

```bash
bash tests/run_stub_pipeline_checks.sh
python -m pytest tests/test_pipeline_contract.py tests/test_cell_type_predict.py
```

Use `XDG_CACHE_HOME=/tmp/xdg-cache` if local Nextflow or sandbox lock behavior requires a writable cache location.

From the repository root, the pipeline can also be invoked as:

```bash
micromamba activate nextflow
nextflow run ./nucxplore-pipeline -stub-run --from_stage features --to_stage prediction
```

## Docker Image Contract

Runtime images are expected to be hosted on Docker Hub. Use real names during release, such as:

```text
docker.io/<owner>/nucxplore-crop-filter:<tag>
docker.io/<owner>/nucxplore-rgci-seg:<tag>
docker.io/<owner>/nucxplore-cell-type-prediction:<tag>
```

Do not leave placeholders in production params files or published run examples tied to a release tag.

Image responsibilities:

| Image | Dockerfile | Must contain |
|---|---|---|
| Crop/filter | `Dockerfile.crop-filter` | `tiffslide`, OpenSlide runtime, Pillow, OpenCV, `bin/crop_and_filter.py`. |
| Segmentation | `Dockerfile.rgci-seg` | CUDA PyTorch stack, HEIP/RGCI code, `cellseg-models-pytorch`, `last.ckpt` baked at `/opt/heip/models/last.ckpt`. |
| Features/prediction | `Dockerfile` | NucXplore package (from PyPI for production, or local source for development), pandas, XGBoost, trained model and label encoder under `/opt/nucxplore/models/`. |

### Features/prediction Image: Dual Install Mode

The feature/prediction Dockerfile supports two build targets:

- **`runtime-source`** (default): Builds `nucxplore` from the local `nucxplore/` checkout using Rust/maturin. Use for development and CI.
- **`runtime-pypi`**: Installs a released `nucxplore` wheel from PyPI via `NUCXPLORE_VERSION` build arg. Use for production releases.

```bash
# Development (local source)
docker build -f nucxplore-pipeline/Dockerfile --target runtime-source \
  -t docker.io/<owner>/nucxplore-cell-type-prediction:<tag> .

# Production (PyPI)
docker build -f nucxplore-pipeline/Dockerfile --target runtime-pypi \
  --build-arg NUCXPLORE_VERSION=0.2.0 \
  -t docker.io/<owner>/nucxplore-cell-type-prediction:<tag> .
```

The segmentation Docker profile adds `--gpus all` only when `params.seg_device == 'cuda'`.

## Build And Publish Checklist

Build image commands should be run from the repository root and tagged with the release version:

```bash
docker build -f nucxplore-pipeline/Dockerfile.crop-filter -t docker.io/<owner>/nucxplore-crop-filter:<tag> .
docker build -f nucxplore-pipeline/Dockerfile.rgci-seg -t docker.io/<owner>/nucxplore-rgci-seg:<tag> .
# Production (installs nucxplore from PyPI)
docker build -f nucxplore-pipeline/Dockerfile --target runtime-pypi \
  --build-arg NUCXPLORE_VERSION=<version> \
  -t docker.io/<owner>/nucxplore-cell-type-prediction:<tag> .
```

Omit `--target` (defaults to `runtime-source`) to build `nucxplore` from the local checkout instead.

After validation, publish with normal Docker Hub credentials:

```bash
docker push docker.io/<owner>/nucxplore-crop-filter:<tag>
docker push docker.io/<owner>/nucxplore-rgci-seg:<tag>
docker push docker.io/<owner>/nucxplore-cell-type-prediction:<tag>
```

Before pushing release tags, confirm the feature/prediction image uses the intended released NucXplore package version and contains the expected model artifacts.

## Parameter Maintenance

When adding or changing a parameter, update all relevant files in the same change:

| File | Required update |
|---|---|
| `nextflow.config` | Default value and grouping. |
| `params.example.yaml` | Example value and comment. |
| `docs/user-guide.md` | Parameter reference and run examples if user-visible. |
| `README.md` | Only if quickstart behavior changes. |
| `tests/` | Contract coverage for validation or branching behavior. |

Keep placeholder container validation strict for active stages. Users should fail early when an active stage still points at an unconfigured placeholder image.

## Testing Guidance

| Change type | Minimum validation |
|---|---|
| Documentation only | Manual link/parameter consistency check. |
| Nextflow stage wiring | `bash tests/run_stub_pipeline_checks.sh`. |
| Prediction code | `python -m pytest tests/test_cell_type_predict.py`. |
| Contract validation | `python -m pytest tests/test_pipeline_contract.py`. |
| Dockerfile change | Build affected image and run at least the relevant stub or smoke command. |
| Segmentation runtime change | Run a CUDA smoke test with the intended `last.ckpt` image when hardware is available. |

## CI Scope

GitHub Actions in this repository are scoped to the `nucxplore` Python package only (see `.github/workflows/package-ci.yml` and `.github/workflows/publish-pypi.yml` in the repo root). There is no pipeline CI workflow; pipeline validation is local unless a future task adds one. Pipeline Docker images are published manually.

## Release Checklist

| Step | Check |
|---|---|
| Version | Update `manifest.version` in `nextflow.config` if releasing a new pipeline version. |
| Images | Build and push DockerHub tags for active images. |
| Params | Replace placeholders in release params examples or release notes with final tags. |
| Docs | Ensure README and user guide use final release image tags where appropriate. |
| Validation | Run stub contract checks and any changed Python tests. |
| Changelog | Add a top entry describing user-visible changes and image impacts. |

Note: the `nucxplore` PyPI package is released independently from the pipeline code in `nucxplore/`. Pipeline releases do not trigger package publishing, and package releases do not trigger pipeline Docker builds.

## Development Notes

The crop/filter stage replaces notebook hard-coded paths with configurable CLI parameters. The segmentation stage wraps the HEIP/RGCI model and should keep patch input root, MAT output root, checkpoint path, device, patch size, stride, padding, and batch size configurable through Nextflow params.

The current segmentation contract writes MAT masks compatible with NucXplore. Do not add GeoJSON-only behavior to the default pipeline unless the feature stage contract is updated at the same time.
