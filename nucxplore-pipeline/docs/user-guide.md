# nucxplore-pipeline User Guide

Concise guide for running the Nextflow pipeline. Detailed usage, parameter, and troubleshooting pages live in [`../../wiki/Pipeline-User-Guide.md`](../../wiki/Pipeline-User-Guide.md) and [`../../wiki/Pipeline-Parameters.md`](../../wiki/Pipeline-Parameters.md).

## Requirements

| Requirement | Notes |
|---|---|
| Nextflow | Runs the workflow. |
| Conda environment `nucxplore-local` | Required for crop/filter + featurizer (run locally). See conda setup below. |
| Container engine | Docker (default), Apptainer, or Singularity for segmentation + prediction. |
| CUDA runtime | Required only for GPU segmentation with `seg_device=cuda`. |
| Input data | WSI files, crop tiles, image/MAT pairs, or feature CSVs depending on entry stage. |

## Conda Setup

```bash
micromamba env create -f nucxplore-pipeline/environment.yml
```

## Full Pipeline

```bash
nextflow run the-ahuja-lab/NucXplore -r <release-tag> \
  --slide_root /data/slides \
  --seg_container <seg_image> \
  --container <pred_image> \
  --outdir /data/results
```

Local checkout:

```bash
nextflow run ./nucxplore-pipeline \
  --slide_root /data/slides \
  --seg_container <seg_image> \
  --container <pred_image> \
  --outdir /data/results
```

Crop/filter + featurizer run in conda; segmentation + prediction run in containers.

## Partial Runs

```bash
# Crop only (conda, parallel per slide)
nextflow run ./nucxplore-pipeline \
  --stage crop \
  --slide_root /data/slides \
  --publish_crops true \
  --outdir /data/results

# Segmentation only (container, sequential)
nextflow run ./nucxplore-pipeline \
  --stage segmentation \
  --crop_root /data/crops \
  --seg_container <seg_image> \
  --publish_segmentation true \
  --outdir /data/results

# Features only (conda)
nextflow run ./nucxplore-pipeline \
  --stage features \
  --image_root /data/images \
  --mat_root /data/mats \
  --outdir /data/results

# Prediction only (container, sequential)
nextflow run ./nucxplore-pipeline \
  --stage prediction \
  --features_root /data/features \
  --container <pred_image> \
  --outdir /data/results
```

## Key Parameters

| Parameter | Default | Use |
|---|---|---|
| `stage` | `null` | Single-stage shorthand. Overrides `from_stage`/`to_stage`. |
| `from_stage` | `crop` | First stage to run. |
| `to_stage` | `prediction` | Last stage to run. |
| `slide_root` | `null` | Required for crop entry. |
| `crop_root` | `null` | Required for segmentation entry. |
| `image_root`, `mat_root` | `null` | Required for features roots mode. |
| `features_root` | `null` | Required for prediction entry. |
| `outdir` | `results/celltype` | Published output root. |
| `workers` | `4` | Prediction worker count (featurizer parallelism is per-tile via Nextflow tasks). |
| `use_gpu` | `false` | NucXplore WGPU feature extraction. |
| `feature_schema` | `legacy` | Select `legacy`, `dual`, or standalone corrected `v2`. |
| `seg_device` | `cuda` | Segmentation device, `cuda` or `cpu`. |
| `seg_container` | `ahujalab/nucxplore-seg:latest` | Segmentation container image. |
| `container` | `ahujalab/nucxplore-cell-type-prediction:latest` | Prediction container image. |

The current XGBoost model requires legacy feature names. Use `dual` when both
prediction and corrected V2 analysis are needed. V2 has 89 numeric features plus
`nucleus_id`; pipeline CSVs additionally carry `nucleus_type`. V2-only files
intentionally fail legacy-model prediction. See the package
[feature-schema reference](../../nucxplore/docs/feature-schemas.md).

Vahadane normalization is mandatory. The model installed from
`WSI_Sample_Adnan` uses 46 normalized fields and all seven corrected Hu moments,
so an unnormalized or historical feature file is not an equivalent input.

Full reference: [`../../wiki/Pipeline-Parameters.md`](../../wiki/Pipeline-Parameters.md).

## Outputs

| Path | Contents |
|---|---|
| `features/` | Nucleus-level feature CSVs. |
| `predictions/` | Cell-type predictions and confidence scores. |
| `nuclei/` | Optional crop PNGs. |
| `logs/` | Manifests and logs. |

## Validate Clone

```bash
python -m pytest -q
bash tests/run_stub_pipeline_checks.sh
```
