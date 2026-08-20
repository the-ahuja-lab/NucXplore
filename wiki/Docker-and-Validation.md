# Docker And Validation

This page describes the container image contract and validation assets used by the NucXplore pipeline.

## Runtime Images

| Stage | Parameter | Default tag | Execution |
|---|---|---|---|
| Crop/filter | — | — | Conda environment `nucxplore-local` (no container). |
| Segmentation | `seg_container` | `ahujalab/nucxplore-seg:latest` | Container (Docker/Apptainer/Singularity). Contains CUDA PyTorch, NucXplore code, `cellseg-models-pytorch`, `last.ckpt`. |
| Features | — | — | Conda environment `nucxplore-local` (no container). |
| Prediction | `container` | `ahujalab/nucxplore-cell-type-prediction:latest` | Container. Contains NucXplore wheel, pandas, XGBoost, model and encoder artifacts. |

Docker uses a local image with the requested tag when present; otherwise it attempts to pull the same tag.

## Local Build

From the repository root:

```bash
bash nucxplore-pipeline/scripts/build_docker_images.sh
```

Manual equivalent:

```bash
docker build -f nucxplore-pipeline/Dockerfile.nucxplore-seg -t ahujalab/nucxplore-seg:latest .
docker build -f nucxplore-pipeline/Dockerfile -t ahujalab/nucxplore-cell-type-prediction:latest .
```

The prediction image builds the local `nucxplore/` wheel with `maturin`, so
local image tests do not require a published package release. It also installs
XGBoost 3.1.3 and scikit-learn 1.8.0, then verifies the adjacent model manifest
when loading the artifacts. The segmentation image is GPU-heavy and is not
needed for CPU-only testing.

## Local SVS Smoke Run

```bash
bash nucxplore-pipeline/scripts/run_local_svs_pipeline.sh /path/to/GTEX-1117F-0126.svs
```

The helper copies the pipeline and SVS into a writable home-directory run folder before launching Nextflow. This avoids Docker bind-mount write issues on hosts where Docker cannot write to non-home storage mounts.

## NVIDIA Runtime

For `seg_device=cuda`, `conf/containers.config` configures segmentation with:

```text
--runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=all -e NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

Set `--seg_device cpu` for CPU segmentation testing or hosts without a working NVIDIA runtime.

## Stub Validation

```bash
cd nucxplore-pipeline
bash tests/run_stub_pipeline_checks.sh
python -m pytest tests/test_pipeline_contract.py tests/test_cell_type_predict.py
```

Stub checks validate stage contracts without production Docker images or full WSI input data.

GitHub Actions runs these contracts with Nextflow 25.04.7 in addition to strict
Rust linting/tests and Python 3.10/3.12 wheel tests.

## Docker Reference CSVs

When present, `Docker_References/GTEX-1F75B-0126/` contains verified reference outputs from a Docker pipeline run:

| Path | Contents |
|---|---|
| `features/` | 248 feature CSVs. |
| `predictions/` | 248 prediction CSVs with `Predicted_Label` and `Confidence_Score`. |

Validation script:

```bash
python nucxplore-pipeline/scripts/validate_against_reference.py \
  --new-features /path/to/new/run/features \
  --new-predictions /path/to/new/run/predictions \
  --ref-features Docker_References/GTEX-1F75B-0126/features \
  --ref-predictions Docker_References/GTEX-1F75B-0126/predictions
```

Validation rules:

| Component | Rule |
|---|---|
| Non-CCSM features | Exact equality. |
| CCSM features | Tolerance check with `rtol=1e-12`, `atol=1e-12`. |
| `Predicted_Label` | Exact equality for same-build comparisons. |
| `Confidence_Score` | Exact equality. |

Reference predictions are valid only when their model and encoder hashes match
the active `model_manifest.json`. The reference model artifacts were replaced
on 2026-08-14, so prediction CSVs produced by older artifacts are historical
baselines rather than expected current output.
