# NucXplore Pipeline

Nextflow DSL2 workflow for whole-slide crop/filtering, NucXplore nucleus
segmentation, NucXplore feature extraction, and XGBoost cell-type prediction.

## Execution model

| Stage | Name | Runtime | Input | Published output |
|---|---|---|---|---|
| Crop/filter | `crop` | Local `nucxplore-local` environment; parallel per slide | WSI files | `crops/` when requested |
| Segmentation | `segmentation` | Segmentation container; one task at a time | Tile directories | `segmentation_mats/` when requested |
| Features | `features` | Local `nucxplore-local` environment; parallel per tile | Matched RGB/MAT pairs | `features/`, optional `nuclei/` |
| Prediction | `prediction` | Prediction container; one batch at a time | Legacy/dual feature CSVs | `predictions/`, `logs/` |

Docker is enabled by default for the two containerized stages. Use
`-profile apptainer` or `-profile singularity` to select another engine.

## Requirements

- Nextflow 25.04.7 or compatible release with Java 17+
- Micromamba or Conda
- Docker, Apptainer, or Singularity
- NVIDIA runtime only when `seg_device=cuda`
- Local `HEIP/HEIP/src` and `HEIP/HEIP/last.ckpt` when building the
  segmentation image

Create the local environment:

```bash
micromamba env create -f nucxplore-pipeline/environment.yml
```

The environment pins NucXplore 0.3.0 from the configured TestPyPI release
channel while resolving third-party dependencies from PyPI/conda-forge.

## Full run

From the repository root:

```bash
nextflow run ./nucxplore-pipeline \
  --slide_root /data/slides \
  --outdir /data/results
```

Hosted, reproducible run:

```bash
nextflow run the-ahuja-lab/NucXplore -r <release-tag> \
  --slide_root /data/slides \
  --outdir /data/results
```

Default images:

```text
ahujalab/nucxplore-seg:latest
ahujalab/nucxplore-cell-type-prediction:latest
```

Pin immutable image tags or digests for production runs instead of relying on
`latest`.

## Reproducible demo

The [demo launcher](examples/demo/README.md) provides two checksum-pinned runs:

```bash
# GTEX-1117F-0126.svs: crop -> segmentation -> features -> prediction
bash nucxplore-pipeline/examples/demo/run_demo.sh full

# Eight prepared PNG/MAT pairs: features -> prediction
bash nucxplore-pipeline/examples/demo/run_demo.sh intermediate
```

CPU segmentation is the portable default; CUDA can be selected for the
full-slide run when the segmentation image contains CUDA-enabled PyTorch.
Generated data, work files, and results are kept outside the tracked pipeline
source.

## Partial runs

```bash
# Features only from mirrored image/MAT roots
nextflow run ./nucxplore-pipeline \
  --stage features \
  --image_root /data/images \
  --mat_root /data/mats \
  --save_crops false \
  --outdir /data/results

# Prediction only from existing model-compatible CSVs
nextflow run ./nucxplore-pipeline \
  --stage prediction \
  --features_root /data/features \
  --outdir /data/results
```

Use `--stage <name>` for one stage or `--from_stage <start>
--to_stage <end>` for a contiguous range. Feature inputs can also be supplied
through a validated samplesheet; see the [user guide](docs/user-guide.md).

## Feature and model contract

Feature extraction always performs deterministic Vahadane normalization.
`pre_norm_*` values come from the raw tile and `post_norm_*` values from the
normalized tile. There is no normalization opt-out.

| Schema | Pipeline use |
|---|---|
| `legacy` | Default. Produces all 129 named inputs required by prediction. |
| `dual` | Preserves the model inputs and appends corrected V2 features. |
| `v2` | Corrected analysis-only schema; prediction intentionally rejects it because model fields are absent. |

The bundled classifier and encoder come from `WSI_Sample_Adnan`. The model uses
126 of 129 features, including 46 `post_norm_*` fields and all seven Hu moments.
The SHA-256 hashes, serialization versions, labels, and usage contract are in
[`models/model_manifest.json`](models/model_manifest.json). The encoder label
strings are emitted exactly as trained.

## Outputs

| Path under `outdir` | Contents |
|---|---|
| `features/` | Per-tile CSVs and `.csv.schema.json` provenance sidecars. |
| `predictions/` | Input rows plus `Predicted_Label` and `Confidence_Score`. |
| `nuclei/` | Optional masked raw-image nucleus crops. |
| `logs/` | Crop, segmentation, input-preparation, and prediction manifests/logs. |
| `crops/` | Crop tiles when `publish_crops=true`. |
| `segmentation_mats/` | Segmentation outputs when `publish_segmentation=true`. |

## Build containers

```bash
bash nucxplore-pipeline/scripts/build_docker_images.sh
```

This builds only the segmentation and prediction images. Crop/filter and
feature extraction intentionally run in the local environment.

## Validate

```bash
cd nucxplore-pipeline
python -m pytest -q
bash tests/run_stub_pipeline_checks.sh
```

The GitHub Actions workflow also validates the Rust package, built wheels on
Python 3.10/3.12, prediction artifact contracts, and Nextflow stage contracts.

## Documentation

- [User guide](docs/user-guide.md)
- [Developer guide](docs/developer-guide.md)
- [Complete parameter reference](../wiki/Pipeline-Parameters.md)
- [Containers and validation](../wiki/Docker-and-Validation.md)
