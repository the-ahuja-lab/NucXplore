# Pipeline User Guide

The NucXplore pipeline is a Nextflow workflow for whole-slide crop/filtering, RGCI/HEIP segmentation, NucXplore feature extraction, and XGBoost cell-type prediction.

## Stages

| Stage | `from_stage` / `to_stage` value | Purpose |
|---|---|---|
| Crop/filter | `crop` | Tile whole-slide images and remove blank or partial tiles. |
| RGCI/HEIP segmentation | `segmentation` | Segment nuclei from crop tiles and write MAT masks. |
| NucXplore features | `features` | Extract nucleus-level feature CSVs and optional crops. |
| Cell-type prediction | `prediction` | Apply the bundled XGBoost model and label encoder. |

The default run is `crop` through `prediction`. Stage ranges must be contiguous.

## Requirements

| Requirement | Notes |
|---|---|
| Nextflow | Installed on the host. |
| Docker | Required for `-profile docker`. |
| CUDA runtime | Required only when segmentation uses `seg_device=cuda`. |
| Docker images | Defaults are `ahujalab/...:latest`; Docker uses local tags first, then pulls if absent. |

## Full Pipeline

Hosted repository:

```bash
nextflow run <org>/<repo> -r <tag> -profile docker \
  --slide_root /data/slides \
  --outdir /data/results
```

Local checkout from repo root:

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --slide_root /data/slides \
  --outdir /data/results
```

From inside `nucxplore-pipeline/`:

```bash
nextflow run . -profile docker \
  --slide_root /data/slides \
  --outdir /data/results
```

`slide_root` must contain files matching `slide_exts`.

## Partial Runs

### Crop Only

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage crop --to_stage crop \
  --slide_root /data/slides \
  --publish_crops true \
  --outdir /data/results
```

### Segmentation Only

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage segmentation --to_stage segmentation \
  --crop_root /data/crops \
  --publish_segmentation true \
  --outdir /data/results
```

### Features Only From Mirrored Roots

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage features --to_stage features \
  --input_mode roots \
  --image_root /data/images \
  --mat_root /data/mats \
  --outdir /data/results
```

Pairing rule: for each image at `<image_root>/<relpath>.<ext>`, a MAT file must exist at `<mat_root>/<relpath>.mat`.

### Features From Samplesheet

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage features --to_stage prediction \
  --input_mode samplesheet \
  --samplesheet /data/samplesheet.csv \
  --outdir /data/results
```

Samplesheet format:

```csv
sample_id,image_path,mat_path
case1,/data/images/case1/tile.png,/data/mats/case1/tile.mat
```

Rows with empty paths, missing files, or duplicate normalized `sample_id` values fail validation.

### Prediction Only

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage prediction --to_stage prediction \
  --features_root /data/features \
  --outdir /data/results
```

## Outputs

| Path under `outdir` | Contents |
|---|---|
| `features/` | Per-image NucXplore feature CSVs. |
| `predictions/` | CSVs with `Predicted_Label` and `Confidence_Score`. |
| `nuclei/` | Feature-stage nucleus crop outputs when `save_crops=true`. |
| `logs/` | Stage manifests and logs. |
| `crops/` | Intermediate crop tiles when `publish_crops=true`. |
| `segmentation_mats/` | Intermediate MAT masks when `publish_segmentation=true`. |

## Error Behavior

| Condition | Behavior |
|---|---|
| Invalid stage name | Hard failure with allowed values. |
| Missing entry input | Hard failure with a stage-specific hint. |
| Invalid samplesheet row | Hard failure. |
| Missing image/MAT pair | Hard failure for staged samplesheets; warnings and skipped tasks for root pairing. |
| Missing model feature columns | Hard failure with missing column names. |
| Empty prediction input CSV | Marked `skipped_empty` in prediction manifest. |
| Model or encoder load failure | Hard failure. |

## Boolean Parameters

Nextflow CLI booleans are parsed explicitly. Values such as `false`, `0`, `no`, `off`, and empty/null values are false; `true`, `1`, `yes`, `y`, and `on` are true.

Examples:

```bash
--stain_normalization_features false
--save_crops false
--publish_crops true
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `--slide_root is required` | Provide `slide_root` when starting from `crop`. |
| `--crop_root is required` | Provide `crop_root` when starting from `segmentation`. |
| `--features_root is required` | Provide `features_root` for prediction-only runs. |
| Missing MAT pairs | Confirm mirrored relative paths and `.mat` suffix under `mat_root`. |
| Missing feature columns | Confirm feature output schema matches the model feature names. |
| CUDA unavailable | Set `--seg_device cpu` or configure NVIDIA Docker runtime. |
| Local cache lock issues | Retry with `XDG_CACHE_HOME=/tmp/xdg-cache`. |

## Stub Validation

```bash
cd nucxplore-pipeline
bash tests/run_stub_pipeline_checks.sh
```

Stub checks validate contracts without production Docker images or full WSI inputs.
