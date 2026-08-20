# Pipeline Parameters

Current parameter reference for `nucxplore-pipeline/nextflow.config`.

## Stage Control

| Parameter | Default | Notes |
|---|---|---|
| `stage` | `null` | Single-stage shorthand: `crop`, `segmentation`, `features`, or `prediction`. Overrides `from_stage`/`to_stage`. |
| `from_stage` | `crop` | Range start. One of `crop`, `segmentation`, `features`, `prediction`. Use `--stage` for single-stage runs. |
| `to_stage` | `prediction` | Range end. One of `crop`, `segmentation`, `features`, `prediction`. Use `--stage` for single-stage runs. |

Usage:
- **Full pipeline**: default (no stage params)
- **Single stage**: `--stage features`
- **Custom range**: `--from_stage crop --to_stage features`

## Entry Inputs

| Parameter | Default | Required when |
|---|---|---|
| `slide_root` | `null` | Starting at `crop`. |
| `crop_root` | `null` | Starting at `segmentation`. |
| `features_root` | `null` | Starting at `prediction`. |
| `input_mode` | `roots` | Feature-stage entry mode: `roots` or `samplesheet`. |
| `image_root` | `null` | Starting at `features` and `input_mode=roots`. |
| `mat_root` | `null` | Starting at `features` and `input_mode=roots`. |
| `samplesheet` | `null` | Starting at `features` and `input_mode=samplesheet`. |

## Conda Environment

Crop/filter, samplesheet prep, and featurizer run locally via the `nucxplore-local` conda environment.
Create it once before running the pipeline:

```bash
micromamba env create -f nucxplore-pipeline/environment.yml
```

## Crop And Filtering

| Parameter | Default | Notes |
|---|---|---|
| `slide_exts` | `.ndpi,.svs,.tif,.tiff` | Whole-slide extensions. Per-slide parallel execution. |
| `tile_size` | `1250` | Crop tile size in pixels. |
| `mean_threshold` | `220` | Bright-tile mean threshold. |
| `std_threshold` | `15` | Bright-tile standard deviation threshold. |
| `drop_partial_tiles` | `true` | Drop partial edge tiles. |
| `crop_recursive` | `false` | Recursively scan `slide_root`. |

## Segmentation

| Parameter | Default | Notes |
|---|---|---|
| `seg_batch_size` | `8` | HEIP inference batch size. Sequential execution (one slide at a time). |
| `seg_patch_size` | `256` | Inference patch size. |
| `seg_stride` | `80` | Sliding-window stride. |
| `seg_padding` | `120` | Sliding-window padding. |
| `seg_device` | `cuda` | `cuda` or `cpu`; CUDA falls back to CPU inside the CLI if unavailable. |
| `seg_n_devices` | `1` | Number of segmentation devices requested. |
| `seg_checkpoint` | `/opt/heip/models/last.ckpt` | In-container checkpoint path. |

## Containers & Profiles

Only segmentation and prediction run in containers. Crop/filter and featurizer use the local conda environment.

| Parameter | Default | Used by |
|---|---|---|
| `seg_container` | `ahujalab/nucxplore-seg:latest` | Segmentation stage (container). |
| `container` | `ahujalab/nucxplore-cell-type-prediction:latest` | Prediction stage (container). |

The container engine is selected via profile:

| Profile | Engine | Usage |
|---|---|---|
| default (no profile) | Docker | Default engine for containerized stages. |
| `-profile apptainer` | Apptainer | Use Apptainer instead of Docker. |
| `-profile singularity` | Singularity | Use Singularity instead of Docker. |

## Intermediate Publishing

| Parameter | Default | Notes |
|---|---|---|
| `publish_crops` | `false` | Publish `crops/` under `outdir`. |
| `publish_segmentation` | `false` | Publish `segmentation_mats/` under `outdir`. |

## Feature Extraction

| Parameter | Default | Notes |
|---|---|---|
| `outdir` | `results/celltype` | Published output root. |
| `recursive` | `true` | Recursive image scan in features roots mode. |
| `image_exts` | `.png,.jpg,.jpeg,.tif,.tiff,.bmp` | Feature-stage image extensions. |
| `workers` | `4` | Worker count for prediction task (featurizer parallelism is per-tile at Nextflow level). |
| `max_images` | `null` | Optional cap on image pairs. |
| `skip_existing` | `false` | Skip existing feature CSV outputs. |
| `mat_key` | `null` | Optional MAT instance-map key. |
| `inst_type_key` | `inst_type` | Optional nucleus type key. |
| `padding` | `10` | Crop padding in pixels. |
| `use_gpu` | `false` | Use NucXplore WGPU extraction. |
| `save_crops` | `true` | Save feature-stage nucleus crops. |

Vahadane normalization is unconditional and therefore is not exposed as a
parameter. Pipeline output includes the normalized measurements required by
the prediction model.

## Prediction

| Parameter | Default | Notes |
|---|---|---|
| `model_path` | `/opt/nucxplore/models/xgboost_best_model.pkl` | In-container XGBoost model path. Sequential execution (one features dir at a time). |
| `encoder_path` | `/opt/nucxplore/models/label_encoder.pkl` | In-container label encoder path. |
| `fail_on_missing_model_features` | `true` | Must remain true for supported prediction runs. |

The bundled reference model artifacts require 129 named inputs. Their hashes,
eight labels, and serialization versions are recorded in
`nucxplore-pipeline/models/model_manifest.json` and validated at load time.

## Params File

```bash
nextflow run ./nucxplore-pipeline --seg_container <img> --container <img> -params-file nucxplore-pipeline/params.example.yaml
```

Segmentation and prediction use the Docker engine by default (no profile flag needed).
Add `-profile apptainer` or `-profile singularity` to switch container runtimes.

Copy `params.example.yaml` for production runs and edit paths, stage range, and resource options.
