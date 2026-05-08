# nucxplore-pipeline User Guide

This guide is for users running the Nextflow pipeline. Contributor setup, tests, Docker image builds, and release workflow are in [`developer-guide.md`](developer-guide.md).

## Repository Boundary

This pipeline lives in the `nucxplore-pipeline/` subdirectory of the [NucXplore](https://github.com/<org>/<repo>) repository. The `nucxplore` Python package is published independently to PyPI (`pip install nucxplore`) and is consumed by pipeline runtime Docker images. The package release and pipeline release processes are independent.

## What The Pipeline Does

The workflow runs four stages:

| Stage | `from_stage` / `to_stage` value | Purpose |
|---|---|---|
| Crop/filter | `crop` | Tile whole-slide images and remove blank or partial tiles. |
| RGCI/HEIP segmentation | `segmentation` | Segment nuclei from crop tiles and write MAT masks. |
| NucXplore features | `features` | Extract nucleus-level features and optional nucleus crops. |
| Cell-type prediction | `prediction` | Apply the bundled XGBoost model and label encoder. |

The default run is the full `crop` to `prediction` workflow. Partial runs are supported when you provide the correct entry-stage inputs.

## Requirements

| Requirement | Notes |
|---|---|
| Nextflow | Installed on the host. |
| Docker | Required for `-profile docker`. |
| CUDA runtime | Required only when segmentation runs with `--seg_device cuda`. |
| DockerHub images | Replace all `docker.io/<owner>/...:<tag>` placeholders with published images. |
| Input data | Whole-slide images, crop tiles, image/MAT pairs, or feature CSVs depending on entry stage. |

## DockerHub Images

Each stage uses a stage-specific image:

| Stage | Parameter | Expected image contents |
|---|---|---|
| Crop/filter | `--crop_filter_container` | `tiffslide`, OpenSlide runtime, Pillow, OpenCV, crop CLI. |
| Segmentation | `--seg_container` | CUDA-capable PyTorch, HEIP/RGCI code, `last.ckpt` at `/opt/heip/models/last.ckpt`. |
| Features + prediction | `--container` | NucXplore package, pandas, XGBoost, model artifacts under `/opt/nucxplore/models/`. |

Final DockerHub owner and tags are release decisions. Until then, examples intentionally use placeholders such as `docker.io/<owner>/nucxplore-cell-type-prediction:<tag>`.

## Full Pipeline

Run the pipeline from the hosted GitHub repository:

```bash
nextflow run <org>/<repo> -r <tag> -profile docker \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag> \
  --slide_root /data/slides \
  --outdir /data/results
```

From a local checkout (repo root):

```bash
nextflow run . -profile docker \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag> \
  --slide_root /data/slides \
  --outdir /data/results
```

A root `nextflow.config` facade delegates to the pipeline subdirectory. To invoke the subdirectory explicitly:

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag> \
  --slide_root /data/slides \
  --outdir /data/results
```

From inside the pipeline directory:

```bash
cd nucxplore-pipeline && nextflow run . -profile docker \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag> \
  --slide_root /data/slides \
  --outdir /data/results
```

`--slide_root` must contain whole-slide images with extensions from `--slide_exts`.

## Partial Pipeline Examples

### Crop Only

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage crop --to_stage crop \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --slide_root /data/slides \
  --publish_crops true \
  --outdir /data/results
```

### Segmentation Only

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage segmentation --to_stage segmentation \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --crop_root /data/crops \
  --publish_segmentation true \
  --outdir /data/results
```

### Features Only

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage features --to_stage features \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag> \
  --input_mode roots \
  --image_root /data/images \
  --mat_root /data/mats \
  --outdir /data/results
```

### Features To Prediction

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage features --to_stage prediction \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag> \
  --input_mode roots \
  --image_root /data/images \
  --mat_root /data/mats \
  --outdir /data/results
```

### Prediction Only

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage prediction --to_stage prediction \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag> \
  --features_root /data/features \
  --outdir /data/results
```

## Input Modes

### Full Mode

Required when starting at `crop`:

| Parameter | Description |
|---|---|
| `--slide_root` | Directory containing whole-slide images. |

### Segmentation Entry

Required when starting at `segmentation`:

| Parameter | Description |
|---|---|
| `--crop_root` | Directory of pre-cropped patches, usually one subdirectory per sample. |

### Features Entry With Roots

Required when `--from_stage features --input_mode roots`:

| Parameter | Description |
|---|---|
| `--image_root` | Root directory for image tiles. |
| `--mat_root` | Root directory for matching MAT masks. |

Pairing rule: for each image at `<image_root>/<relpath>.<img_ext>`, the MAT file must exist at `<mat_root>/<relpath>.mat`.

### Features Entry With Samplesheet

Required when `--from_stage features --input_mode samplesheet`:

```csv
sample_id,image_path,mat_path
case1,/data/images/case1/tile.png,/data/mats/case1/tile.mat
```

Rows with empty paths, missing files, or duplicate normalized `sample_id` values are rejected.

### Prediction Entry

Required when starting at `prediction`:

| Parameter | Description |
|---|---|
| `--features_root` | Directory containing feature CSV files. |

## Parameter Reference

| Parameter | Default | Notes |
|---|---|---|
| `from_stage` | `crop` | One of `crop`, `segmentation`, `features`, `prediction`. |
| `to_stage` | `prediction` | One of `crop`, `segmentation`, `features`, `prediction`. |
| `slide_root` | `null` | Required when starting from crop. |
| `crop_root` | `null` | Required when starting from segmentation. |
| `features_root` | `null` | Required when starting from prediction. |
| `input_mode` | `roots` | `roots` or `samplesheet` for features entry. |
| `image_root` | `null` | Required for features roots mode. |
| `mat_root` | `null` | Required for features roots mode. |
| `samplesheet` | `null` | Required for features samplesheet mode. |
| `slide_exts` | `.ndpi,.svs,.tif,.tiff` | Whole-slide extensions for crop stage. |
| `tile_size` | `1250` | Crop tile size. |
| `mean_threshold` | `220` | Bright-tile mean threshold. |
| `std_threshold` | `15` | Bright-tile standard deviation threshold. |
| `drop_partial_tiles` | `true` | Drop partial edge tiles. |
| `crop_recursive` | `false` | Recursively scan slide root in crop stage. |
| `seg_batch_size` | `8` | Segmentation batch size. |
| `seg_patch_size` | `256` | Segmentation patch size. |
| `seg_stride` | `80` | Segmentation stride. |
| `seg_padding` | `120` | Segmentation padding. |
| `seg_device` | `cuda` | `cuda` or `cpu`. |
| `seg_n_devices` | `1` | Number of segmentation devices. |
| `seg_checkpoint` | `/opt/heip/models/last.ckpt` | In-container checkpoint path. |
| `crop_filter_container` | placeholder | DockerHub crop/filter image. |
| `seg_container` | placeholder | DockerHub segmentation image. |
| `container` | placeholder | DockerHub features/prediction image. |
| `publish_crops` | `false` | Publish intermediate crop tiles under `outdir/crops/`. |
| `publish_segmentation` | `false` | Publish intermediate MAT masks under `outdir/segmentation_mats/`. |
| `outdir` | `results/celltype` | Published output root. |
| `workers` | `4` | Worker count for feature and prediction tasks. |
| `recursive` | `true` | Recursive image scan in features roots mode. |
| `image_exts` | `.png,.jpg,.jpeg,.tif,.tiff,.bmp` | Feature-stage image extensions. |
| `max_images` | `null` | Optional cap on image pairs. |
| `skip_existing` | `false` | Skip existing feature outputs. |
| `mat_key` | `null` | Optional MAT instance-map key. |
| `inst_type_key` | `inst_type` | Optional nucleus type key. |
| `padding` | `10` | Crop padding in pixels. |
| `use_gpu` | `false` | Toggle NucXplore WGPU extraction. |
| `save_crops` | `true` | Save feature-stage nucleus crops. |
| `save_pre_normalized_crops` | `true` | Save pre-normalized crops. |
| `save_post_normalized_crops` | `true` | Save post-normalized crops. |
| `stain_normalization_features` | `true` | Enable stain-normalized feature groups. |
| `model_path` | `/opt/nucxplore/models/Final_XGB_Model_FullData.pkl` | In-container XGBoost model path. |
| `encoder_path` | `/opt/nucxplore/models/final_label_encoder.pkl` | In-container label encoder path. |
| `fail_on_missing_model_features` | `true` | Must remain true for supported prediction runs. |

## Params File

```bash
nextflow run ./nucxplore-pipeline -profile docker -params-file params.example.yaml
```

Edit `params.example.yaml` or copy it to a run-specific file before production use. Replace all placeholder container names with real DockerHub images.

## Outputs

Under `outdir`:

| Path | Contents |
|---|---|
| `features/` | Per-image NucXplore feature CSVs. |
| `predictions/` | Per-image CSVs with `Predicted_Label` and `Confidence_Score`. |
| `nuclei/` | Optional feature-stage nucleus crop outputs when `save_crops=true`. |
| `logs/` | Stage manifests and logs. |
| `crops/` | Published intermediate crop tiles when `publish_crops=true`. |
| `segmentation_mats/` | Published intermediate MAT masks when `publish_segmentation=true`. |

## Error Behavior

| Condition | Behavior |
|---|---|
| Missing model feature columns | Hard failure with path and missing column names. |
| Model or encoder load failure | Hard failure. |
| Missing input pair | Hard failure. |
| Invalid samplesheet row | Hard failure. |
| Empty prediction input CSV | Marked as `skipped_empty` in manifest. |
| Invalid stage name | Hard failure with allowed values. |
| Missing required entry input | Hard failure with hint. |

## Troubleshooting

| Error or symptom | Fix |
|---|---|
| `Crop stage requires --crop_filter_container` | Provide a real DockerHub crop/filter image. |
| `Segmentation stage requires --seg_container` | Provide a real DockerHub RGCI/HEIP image. |
| `Features/prediction stages require --container` | Provide a real DockerHub features/prediction image. |
| `Invalid --from_stage` or `--to_stage` | Use `crop`, `segmentation`, `features`, or `prediction`. |
| `--slide_root is required` | Provide `--slide_root` when starting from crop. |
| `--crop_root is required` | Provide `--crop_root` when starting from segmentation. |
| `--features_root is required` | Provide `--features_root` when running prediction-only. |
| Missing MAT pairs | Confirm mirrored relative paths and `.mat` suffix under `mat_root`. |
| Missing feature columns | Confirm extraction output schema matches the model feature names. |
| Local sandbox lock issues | Retry with `XDG_CACHE_HOME=/tmp/xdg-cache` if your environment requires it. |

## Validation

Users can run the stub contract checks after cloning the repository:

```bash
bash tests/run_stub_pipeline_checks.sh
```

These checks validate pipeline contracts without requiring production DockerHub images or full WSI data.
