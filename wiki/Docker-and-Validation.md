# Docker And Validation

This page describes the Docker image contract and validation assets used by the NucXplore pipeline.

## Runtime Images

| Stage | Parameter | Default tag | Expected contents |
|---|---|---|---|
| Crop/filter | `crop_filter_container` | `ahujalab/nucxplore-crop-filter:latest` | `tiffslide`, OpenSlide runtime, Pillow, OpenCV, `crop_and_filter.py`. |
| Segmentation | `seg_container` | `ahujalab/nucxplore-rgci-seg:latest` | CUDA PyTorch, HEIP/RGCI code, `cellseg-models-pytorch`, `last.ckpt`. |
| Features/prediction | `container` | `ahujalab/nucxplore-cell-type-prediction:latest` | NucXplore wheel, pandas, XGBoost, model and encoder artifacts. |

Docker uses a local image with the requested tag when present; otherwise it attempts to pull the same tag.

## Local Build

From the repository root:

```bash
bash nucxplore-pipeline/scripts/build_docker_images.sh
```

Manual equivalent:

```bash
docker build -f nucxplore-pipeline/Dockerfile.crop-filter -t ahujalab/nucxplore-crop-filter:latest .
docker build -f nucxplore-pipeline/Dockerfile.rgci-seg -t ahujalab/nucxplore-rgci-seg:latest .
docker build -f nucxplore-pipeline/Dockerfile -t ahujalab/nucxplore-cell-type-prediction:latest .
```

The features/prediction image builds the local `nucxplore/` wheel with `maturin`, so local image tests do not require a published PyPI release.

## Local SVS Smoke Run

```bash
bash nucxplore-pipeline/scripts/run_local_svs_pipeline.sh /path/to/GTEX-1117F-0126.svs
```

The helper copies the pipeline and SVS into a writable home-directory run folder before launching Nextflow. This avoids Docker bind-mount write issues on hosts where Docker cannot write to non-home storage mounts.

## NVIDIA Runtime

For `seg_device=cuda`, `conf/docker.config` configures segmentation with:

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

Historical Conda-generated CSVs may drift from Docker outputs because CCSM features are sensitive to floating-point reassociation. Use Docker-generated references for CI-like checks.
