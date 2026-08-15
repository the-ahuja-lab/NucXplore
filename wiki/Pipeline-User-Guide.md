# Pipeline User Guide

The NucXplore pipeline is a Nextflow workflow for whole-slide crop/filtering, RGCI/HEIP segmentation, NucXplore feature extraction, and XGBoost cell-type prediction.

## Stages

| Stage | `--stage` value | Execution | Purpose |
|---|---|---|---|
| Crop/filter | `crop` | Conda, parallel per slide | Tile whole-slide images and remove blank or partial tiles. |
| RGCI/HEIP segmentation | `segmentation` | Container, sequential | Segment nuclei from crop tiles and write MAT masks. |
| NucXplore features | `features` | Conda, parallel per image | Extract nucleus-level feature CSVs and optional crops. |
| Cell-type prediction | `prediction` | Container, sequential | Apply the bundled XGBoost model and label encoder. |

The default run is `crop` through `prediction`. Stage ranges must be contiguous.

**Stage selection:**
- **Single stage**: `--stage <name>` (equivalent to `--from_stage <name> --to_stage <name>`)
- **Custom range**: `--from_stage <start> --to_stage <end>`

## Execution Model

- **Crop/filter**: slides are discovered and processed in parallel (one Nextflow task per slide)
- **Segmentation**: runs sequentially (`maxForks=1`) to avoid GPU contention
- **Featurizer**: runs in parallel (one Nextflow task per tile) — each tile's features extracted independently; failed tiles do not block others
- **Prediction**: runs as a single batch task (`maxForks=1`) processing all feature CSVs together

## Requirements

| Requirement | Notes |
|---|---|
| Nextflow | Installed on the host. |
| Conda environment `nucxplore-local` | Required for crop/filter and featurizer stages. |
| Container engine | Docker (default), Apptainer, or Singularity for containerized stages. |
| CUDA runtime | Required only when segmentation uses `seg_device=cuda`. |
| Segmentation image | `--seg_container` must be a valid image with RGCI/HEIP. |
| Prediction image | `--container` must be a valid image with XGBoost model + encoder. |

## Conda Environment Setup

Create the environment once before running the pipeline:

```bash
micromamba env create -f nucxplore-pipeline/environment.yml
```

## Container Image Requirements

Two container images are required when running segmentation or prediction:

| Parameter | Stage | Default image |
|---|---|---|
| `--seg_container` | Segmentation | `ahujalab/nucxplore-seg:latest` |
| `--container` | Prediction | `ahujalab/nucxplore-cell-type-prediction:latest` |

Crop/filter and featurizer do **not** use containers — they run locally via the conda environment.

The container engine is selected by profile:
- Default (no profile): Docker
- `-profile apptainer`: Apptainer
- `-profile singularity`: Singularity

## Full Pipeline

Hosted repository:

```bash
nextflow run the-ahuja-lab/NucXplore -r <release-tag> \
  --slide_root /data/slides \
  --seg_container <seg_image> \
  --container <pred_image> \
  --outdir /data/results
```

Local checkout from repo root:

```bash
nextflow run ./nucxplore-pipeline \
  --slide_root /data/slides \
  --seg_container <seg_image> \
  --container <pred_image> \
  --outdir /data/results
```

From inside `nucxplore-pipeline/`:

```bash
nextflow run . \
  --slide_root /data/slides \
  --seg_container <seg_image> \
  --container <pred_image> \
  --outdir /data/results
```

`slide_root` must contain files matching `slide_exts`. Container images can use Docker, Apptainer, or Singularity depending on the active profile.

Feature extraction always performs Vahadane normalization. The bundled model
uses normalized fields and corrected Hu moments; there is no supported
normalization opt-out.

## Partial Runs

### Crop Only (conda, parallel per slide)

```bash
nextflow run ./nucxplore-pipeline \
  --stage crop \
  --slide_root /data/slides \
  --publish_crops true \
  --outdir /data/results
```

### Segmentation Only (container, sequential)

```bash
nextflow run ./nucxplore-pipeline \
  --stage segmentation \
  --crop_root /data/crops \
  --seg_container <seg_image> \
  --publish_segmentation true \
  --outdir /data/results
```

### Features Only From Mirrored Roots (conda, parallel)

```bash
nextflow run ./nucxplore-pipeline \
  --stage features \
  --input_mode roots \
  --image_root /data/images \
  --mat_root /data/mats \
  --outdir /data/results
```

Pairing rule: for each image at `<image_root>/<relpath>.<ext>`, a MAT file must exist at `<mat_root>/<relpath>.mat`.

### Features Through Prediction From Samplesheet

Features run in conda; prediction runs in container:

```bash
nextflow run ./nucxplore-pipeline \
  --from_stage features --to_stage prediction \
  --input_mode samplesheet \
  --samplesheet /data/samplesheet.csv \
  --container <pred_image> \
  --outdir /data/results
```

Samplesheet format:

```csv
sample_id,image_path,mat_path
case1,/data/images/case1/tile.png,/data/mats/case1/tile.mat
```

Rows with empty paths, missing files, or duplicate normalized `sample_id` values fail validation.

### Prediction Only (container, sequential)

```bash
nextflow run ./nucxplore-pipeline \
  --stage prediction \
  --features_root /data/features \
  --container <pred_image> \
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
