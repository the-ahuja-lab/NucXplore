# Pipeline Parameters

Current parameter reference for `nucxplore-pipeline/nextflow.config`.

## Stage Control

| Parameter | Default | Notes |
|---|---|---|
| `from_stage` | `crop` | One of `crop`, `segmentation`, `features`, `prediction`. |
| `to_stage` | `prediction` | One of `crop`, `segmentation`, `features`, `prediction`. |

## Entry Inputs

| Parameter | Default | Required when |
|---|---|---|
| `slide_root` | `null` | `from_stage=crop`. |
| `crop_root` | `null` | `from_stage=segmentation`. |
| `features_root` | `null` | `from_stage=prediction`. |
| `input_mode` | `roots` | Feature-stage entry mode: `roots` or `samplesheet`. |
| `image_root` | `null` | `from_stage=features` and `input_mode=roots`. |
| `mat_root` | `null` | `from_stage=features` and `input_mode=roots`. |
| `samplesheet` | `null` | `from_stage=features` and `input_mode=samplesheet`. |

## Crop And Filtering

| Parameter | Default | Notes |
|---|---|---|
| `slide_exts` | `.ndpi,.svs,.tif,.tiff` | Whole-slide extensions. |
| `tile_size` | `1250` | Crop tile size in pixels. |
| `mean_threshold` | `220` | Bright-tile mean threshold. |
| `std_threshold` | `15` | Bright-tile standard deviation threshold. |
| `drop_partial_tiles` | `true` | Drop partial edge tiles. |
| `crop_recursive` | `false` | Recursively scan `slide_root`. |

## Segmentation

| Parameter | Default | Notes |
|---|---|---|
| `seg_batch_size` | `8` | HEIP inference batch size. |
| `seg_patch_size` | `256` | Inference patch size. |
| `seg_stride` | `80` | Sliding-window stride. |
| `seg_padding` | `120` | Sliding-window padding. |
| `seg_device` | `cuda` | `cuda` or `cpu`; CUDA falls back to CPU inside the CLI if unavailable. |
| `seg_n_devices` | `1` | Number of segmentation devices requested. |
| `seg_checkpoint` | `/opt/heip/models/last.ckpt` | In-container checkpoint path. |

## Containers

| Parameter | Default |
|---|---|
| `crop_filter_container` | `ahujalab/nucxplore-crop-filter:latest` |
| `seg_container` | `ahujalab/nucxplore-rgci-seg:latest` |
| `container` | `ahujalab/nucxplore-cell-type-prediction:latest` |

The Docker profile runs containers as the host UID/GID. CUDA segmentation uses NVIDIA runtime options from `conf/docker.config`.

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
| `workers` | `4` | Worker count for feature and prediction tasks. |
| `max_images` | `null` | Optional cap on image pairs. |
| `skip_existing` | `false` | Skip existing feature CSV outputs. |
| `mat_key` | `null` | Optional MAT instance-map key. |
| `inst_type_key` | `inst_type` | Optional nucleus type key. |
| `padding` | `10` | Crop padding in pixels. |
| `use_gpu` | `false` | Use NucXplore WGPU extraction. |
| `save_crops` | `true` | Save feature-stage nucleus crops. |
| `save_pre_normalized_crops` | `true` | Save pre-normalized crops. |
| `save_post_normalized_crops` | `true` | Save post-normalized crops. |
| `stain_normalization_features` | `true` | Enable post-normalized feature groups. |

## Prediction

| Parameter | Default | Notes |
|---|---|---|
| `model_path` | `/opt/nucxplore/models/Final_XGB_Model_FullData.pkl` | In-container XGBoost model path. |
| `encoder_path` | `/opt/nucxplore/models/final_label_encoder.pkl` | In-container label encoder path. |
| `fail_on_missing_model_features` | `true` | Must remain true for supported prediction runs. |

## Params File

```bash
nextflow run ./nucxplore-pipeline -profile docker -params-file nucxplore-pipeline/params.example.yaml
```

Copy `params.example.yaml` for production runs and edit paths, stage range, and resource options.
