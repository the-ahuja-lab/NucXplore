# nucxplore-pipeline User Guide

Concise guide for running the Nextflow pipeline. Detailed usage, parameter, and troubleshooting pages live in [`../../wiki/Pipeline-User-Guide.md`](../../wiki/Pipeline-User-Guide.md) and [`../../wiki/Pipeline-Parameters.md`](../../wiki/Pipeline-Parameters.md).

## Requirements

| Requirement | Notes |
|---|---|
| Nextflow | Runs the workflow. |
| Docker | Required for `-profile docker`. |
| CUDA runtime | Required only for GPU segmentation with `seg_device=cuda`. |
| Input data | WSI files, crop tiles, image/MAT pairs, or feature CSVs depending on entry stage. |

## Full Pipeline

```bash
nextflow run <org>/<repo> -r <tag> -profile docker \
  --slide_root /data/slides \
  --outdir /data/results
```

Local checkout:

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --slide_root /data/slides \
  --outdir /data/results
```

## Partial Runs

```bash
# Crop only
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage crop --to_stage crop \
  --slide_root /data/slides \
  --publish_crops true \
  --outdir /data/results

# Segmentation only
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage segmentation --to_stage segmentation \
  --crop_root /data/crops \
  --publish_segmentation true \
  --outdir /data/results

# Features only
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage features --to_stage features \
  --image_root /data/images \
  --mat_root /data/mats \
  --outdir /data/results

# Prediction only
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage prediction --to_stage prediction \
  --features_root /data/features \
  --outdir /data/results
```

## Key Parameters

| Parameter | Default | Use |
|---|---|---|
| `from_stage` | `crop` | First stage to run. |
| `to_stage` | `prediction` | Last stage to run. |
| `slide_root` | `null` | Required for crop entry. |
| `crop_root` | `null` | Required for segmentation entry. |
| `image_root`, `mat_root` | `null` | Required for features roots mode. |
| `features_root` | `null` | Required for prediction entry. |
| `outdir` | `results/celltype` | Published output root. |
| `workers` | `4` | Feature/prediction worker count. |
| `use_gpu` | `false` | NucXplore WGPU feature extraction. |
| `seg_device` | `cuda` | Segmentation device, `cuda` or `cpu`. |

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
bash tests/run_stub_pipeline_checks.sh
```
