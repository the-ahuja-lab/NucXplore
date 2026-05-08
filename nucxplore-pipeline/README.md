# NucXplore Pipeline

Nextflow workflow for WSI crop/filtering, RGCI/HEIP nucleus segmentation, NucXplore feature extraction, and XGBoost-based cell-type prediction.

This pipeline lives in the `nucxplore-pipeline/` subdirectory of the [NucXplore](https://github.com/<org>/<repo>) repository. Run it from the hosted repository or from a local checkout.

## Quickstart

### Hosted (from GitHub)

```bash
nextflow run <org>/<repo> -r <tag> -profile docker \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag> \
  --slide_root /data/slides \
  --outdir /data/results
```

### Local checkout (from repo root)

```bash
nextflow run . -profile docker \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag> \
  --slide_root /data/slides \
  --outdir /data/results
```

A root `nextflow.config` facade delegates to `nucxplore-pipeline/main.nf`. The explicit subdirectory invocation also works:

```bash
nextflow run ./nucxplore-pipeline -profile docker \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag> \
  --slide_root /data/slides \
  --outdir /data/results
```

### Local checkout (from pipeline directory)

```bash
cd nucxplore-pipeline
nextflow run . -profile docker \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag> \
  --slide_root /data/slides \
  --outdir /data/results
```

The default stage range is `crop` through `prediction`. Any contiguous stage range can be selected with `--from_stage` and `--to_stage`.

## Stages

| Stage | Name | Main input | Main output |
|---|---|---|---|
| 1 | `crop` | whole-slide images | filtered image tiles |
| 2 | `segmentation` | filtered tiles | MAT instance maps |
| 3 | `features` | image/MAT pairs | NucXplore feature CSVs |
| 4 | `prediction` | feature CSVs | cell-type prediction CSVs |

## Documentation

- User setup and usage: [`docs/user-guide.md`](docs/user-guide.md)
- Developer setup, tests, Docker images, and release workflow: [`docs/developer-guide.md`](docs/developer-guide.md)
- Legacy usage link: [`docs/usage.md`](docs/usage.md)

## CI Scope

GitHub Actions in this repository are scoped to the `nucxplore` Python package only. Pipeline validation runs locally (see developer guide). There is no pipeline CI workflow; add one in a future task if needed.

## Validation

```bash
bash tests/run_stub_pipeline_checks.sh
```

See the user guide for parameters and troubleshooting, and the developer guide for DockerHub publishing expectations.
