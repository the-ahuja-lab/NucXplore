# nucxplore-pipeline Developer Guide

Contributor guide for the Nextflow pipeline. Detailed maintenance notes live in [`../../wiki/Developer-Guide.md`](../../wiki/Developer-Guide.md).

## Layout

| Path | Purpose |
|---|---|
| `main.nf` | Four-stage workflow and segment validation. |
| `nextflow.config` | Defaults and profile includes. |
| `conf/containers.config` | Per-process container assignments (segmentation + prediction only). |
| `environment.yml` | Conda environment for local stages (crop/filter + featurizer). |
| `bin/crop_and_filter.py` | WSI tiling/filtering CLI. |
| `bin/discover_pairs.py` | Matches (tile.png, tile.mat) pairs from crop and MAT roots. |
| `bin/extract_single_tile.py` | Single-tile featurizer CLI. |
| `bin/rgci_seg_to_mat.py` | RGCI/HEIP MAT-mask segmentation CLI. |
| `bin/samplesheet_to_pairs.py` | Samplesheet validation and staging. |
| `bin/cell_type_predict.py` | XGBoost prediction CLI. |
| `tests/` | Stub contract and Python tests. |

## Validate

```bash
bash tests/run_stub_pipeline_checks.sh
python -m pytest tests/test_pipeline_contract.py tests/test_cell_type_predict.py
```

Use `XDG_CACHE_HOME=/tmp/xdg-cache` if the local environment has cache or sandbox lock issues.

## Conda Environment

```bash
micromamba env create -f nucxplore-pipeline/environment.yml
```

Crop/filter, samplesheet prep, and featurizer use this environment (not containers).

## Container Images

Segmentation and prediction run in containers. Default tags:

```text
ahujalab/nucxplore-seg:latest
ahujalab/nucxplore-cell-type-prediction:latest
```

Build with:

```bash
bash scripts/build_docker_images.sh
```

For a local SVS smoke run:

```bash
bash scripts/run_local_svs_pipeline.sh /path/to/slide.svs
```

## Parameter Change Checklist

Update these together for user-visible parameters:

| File | Update |
|---|---|
| `nextflow.config` | Default and grouping. |
| `params.example.yaml` | Example and comments. |
| `README.md` | Quick start and common runs. |
| `docs/user-guide.md` | Concise key-parameter mention if important. |
| `../wiki/Pipeline-Parameters.md` | Full reference. |
| `../wiki/Pipeline-User-Guide.md` | Full usage guide. |
| `tests/` | Contract coverage. |

GitHub Actions runs the pipeline Python contracts and a Nextflow stub-contract
job in addition to Rust and wheel validation.
