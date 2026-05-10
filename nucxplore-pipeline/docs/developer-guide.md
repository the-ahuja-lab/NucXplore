# nucxplore-pipeline Developer Guide

Contributor guide for the Nextflow pipeline. Detailed maintenance notes live in [`../../wiki/Developer-Guide.md`](../../wiki/Developer-Guide.md).

## Layout

| Path | Purpose |
|---|---|
| `main.nf` | Four-stage workflow and stage validation. |
| `nextflow.config` | Defaults and profile includes. |
| `conf/docker.config` | Docker runtime options and per-process images. |
| `bin/crop_and_filter.py` | WSI tiling/filtering CLI. |
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

## Docker Images

```bash
bash scripts/build_docker_images.sh
```

Default tags:

```text
ahujalab/nucxplore-crop-filter:latest
ahujalab/nucxplore-rgci-seg:latest
ahujalab/nucxplore-cell-type-prediction:latest
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
| `docs/user-guide.md` | Concise key-parameter mention if important. |
| `../wiki/Pipeline-Parameters.md` | Full reference. |
| `tests/` | Contract coverage. |

Pipeline validation is local. Current GitHub Actions are package-only unless a future task adds pipeline CI.
