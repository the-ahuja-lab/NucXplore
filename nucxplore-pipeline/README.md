# NucXplore Pipeline

Nextflow workflow for whole-slide crop/filtering, RGCI/HEIP segmentation, NucXplore feature extraction, and XGBoost cell-type prediction.

## Quick Start

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

The default container tags are:

```text
ahujalab/nucxplore-crop-filter:latest
ahujalab/nucxplore-rgci-seg:latest
ahujalab/nucxplore-cell-type-prediction:latest
```

## Stages

| Stage | `from_stage` / `to_stage` | Input | Output |
|---|---|---|---|
| Crop/filter | `crop` | WSI files | PNG crop tiles |
| Segmentation | `segmentation` | crop tiles | MAT instance masks |
| Features | `features` | image/MAT pairs | feature CSVs and optional crops |
| Prediction | `prediction` | feature CSVs | prediction CSVs |

Run a subset with `--from_stage` and `--to_stage`.

## Common Runs

```bash
# Features only from paired roots
nextflow run ./nucxplore-pipeline -profile docker \
  --from_stage features --to_stage features \
  --image_root /data/images \
  --mat_root /data/mats \
  --outdir /data/results

# Prediction only from existing feature CSVs
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
| `nuclei/` | Optional feature-stage crop PNGs. |
| `logs/` | Stage logs and manifests. |
| `crops/` | Published crop tiles when `publish_crops=true`. |
| `segmentation_mats/` | Published MAT masks when `publish_segmentation=true`. |

## Documentation

- User guide: [`docs/user-guide.md`](docs/user-guide.md)
- Developer guide: [`docs/developer-guide.md`](docs/developer-guide.md)
- Full wiki: [`../wiki/Pipeline-User-Guide.md`](../wiki/Pipeline-User-Guide.md)
- Parameters: [`../wiki/Pipeline-Parameters.md`](../wiki/Pipeline-Parameters.md)

## Validate

```bash
bash tests/run_stub_pipeline_checks.sh
python -m pytest tests/test_pipeline_contract.py tests/test_cell_type_predict.py
```
