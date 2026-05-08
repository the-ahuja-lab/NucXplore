# CHANGELOG

Append-only. Most recent entries first.

Use short, telegraphic style:
- verb + object
- no articles
- concise lines

One entry per task.

## 2026-05-07 — document package-only CI scope for pipeline

add CI-scope notes to pipeline README and developer guide confirming GitHub Actions are package-only
Files/Modules: `README.md`, `docs/developer-guide.md`, `CHANGELOG.md`
Impact: pipeline contributors
Reason: clarify that no pipeline CI workflow exists; validation is local

## 2026-05-07 — update pipeline docs for combined repository

update pipeline README, user guide, developer guide, params example, and changelog for monorepo layout at `nucxplore-pipeline/`
Files/Modules: `README.md`, `docs/user-guide.md`, `docs/developer-guide.md`, `params.example.yaml`, `CHANGELOG.md`
Impact: pipeline users and contributors
Reason: single GitHub repository for both library and pipeline; update all run examples to use `./nucxplore-pipeline` or `nextflow run <org>/<repo>`; add hosted run pattern; update micromamba env guidance

## 2026-05-06 — split pipeline documentation

split user and developer pipeline docs
Files/Modules: `README.md`, `docs/user-guide.md`, `docs/developer-guide.md`, `docs/usage.md`, `CHANGELOG.md`
Impact: `nucxplore-cell-type-prediction` users and contributors
Reason: make pipeline repository documentation clean for separate git repository usage and DockerHub-hosted runtime images

## 2026-05-06 — full validation run (library + pipeline)

run all 131 Rust/Python/Nextflow tests and benchmarks; fix Python 3.8 `PathLike[str]` incompatibility in `io.py`; document results in `plans/validation-report.md`
Files/Modules: `nucxplore/tests/*` (Rust), `nucxplore/python/nucxplore/io.py`, `nucxplore-cell-type-prediction/tests/*`, `plans/validation-report.md`
Impact: all 115 Rust tests, 14 Python tests, 12 Nextflow stub scenarios pass; `io.py` now Python 3.8 compatible
Reason: comprehensive validation baseline before further development

## 2026-05-05 — rename project nomenclature to NucXplore

rename code identifiers from nuxplore/NuXplore to nucxplore/NucXplore across package, pipeline, and docs; no logic changes
Files/Modules: `nuxplore/` (Cargo.toml, pyproject.toml, Rust src, Python wrappers, scripts, tests, benches), `nuxplore-cell-type-prediction/` (main.nf, nextflow.config, Dockerfile*, params.example.yaml, bin/*.py, tests, docs/usage.md, README.md)
Impact: package/pipeline/Docker/config/docs users must use `nucxplore` / `NucXplore` nomenclature
Reason: align all identifiers with current project name without changing extraction or prediction behavior

## 2026-05-05 — stabilize local Docker images

pin feature/prediction deps, rebuild crop/filter deps, and switch RGCI/HEIP image to micromamba Python 3.9 env
Files/Modules: `Dockerfile`, `Dockerfile.crop-filter`, `Dockerfile.rgci-seg`, `envs/rgci-seg.yml`, `conf/docker.config`, `main.nf`, `nextflow.config`, `.dockerignore`, `../.dockerignore`, `../HEIP/HEIP/src/unet.py`
Impact: `nuxplore-cell-type-prediction` Docker users
Reason: local images now build against compatible Python/PyTorch/cellseg-models versions; segmentation avoids pretrained-weight downloads before checkpoint load; Docker GPU flag is only applied for CUDA segmentation runs; crop recursion is controlled by `--crop_recursive`

## 2026-05-04 — fix upstream stage contract gaps

enforce active feature/prediction container validation and recursive crop discovery
Files/Modules: `main.nf`, `bin/crop_and_filter.py`, `tests/run_stub_pipeline_checks.sh`, `tests/test_pipeline_contract.py`, `nextflow.config`, `docs/usage.md`
Impact: `nuxplore-cell-type-prediction` users
Reason: features-only and prediction-only Docker runs now reject placeholder containers early; `crop_and_filter.py --recursive` discovers nested slides as advertised; unsupported segmentation GeoJSON params no longer appear in current MAT-mode config/docs

## 2026-05-04 — document full four-stage pipeline contract

update docs, params example, and README for crop→seg→features→prediction default
Files/Modules: `README.md`, `docs/usage.md`, `params.example.yaml`
Impact: `nuxplore-cell-type-prediction` users
Reason: match documentation to current pipeline behavior — full-pipeline quickstart, per-stage container flags in all examples, updated output layout, per-container troubleshooting entries

## 2026-05-04 — wire full four-stage pipeline

wire crop→seg→features→prediction with stage indexing and per-process output publishing
Files/Modules: `main.nf` (workflow rewrite, stageIdx helper, removed EXPORT_RESULTS, per-process publishDir with enabled flags)
Impact: `nuxplore-cell-type-prediction` users
Reason: index-based stage comparison fixes lexicographic ordering bug; default `--from_stage crop --to_stage prediction` runs all four stages; standalone prediction-only mode added; intermediate publish controlled via `publish_crops`/`publish_segmentation` flags; all 10 stage-combination stub contracts pass

## 2026-05-04 — add RGCI/HEIP segmentation stage

add CUDA segmentation stage producing NuXplore-compatible MAT masks from crop tiles
Files/Modules: `bin/rgci_seg_to_mat.py`, `Dockerfile.rgci-seg`, `main.nf` (RGCI_SEG process, stageIdx helper, container validation), `conf/docker.config` (--gpus all for segmentation), `tests/run_stub_pipeline_checks.sh`
Impact: `nuxplore-cell-type-prediction` users
Reason: replace notebook-based HEIP inference with deterministic CLI; default MAT output (no JSON→MAT conversion needed); `inst_map`+`inst_type` keys match NuXplore expectations; runs standalone `--from_stage segmentation --to_stage segmentation` or downstream of crop; CUDA guard via dedicated container with `--gpus all`

## 2026-05-04 — add crop/filter CLI and Nextflow process

add WSI crop and blank/partial-tile filter stage
Files/Modules: `bin/crop_and_filter.py`, `Dockerfile.crop-filter`, `main.nf` (CROP_AND_FILTER process), `conf/docker.config` (per-process container), `tests/run_stub_pipeline_checks.sh`, `tests/fixtures/celltype/slides/`
Impact: `nuxplore-cell-type-prediction` users
Reason: replace notebook-based WSI tiling with deterministic CLI; emit HEIP-compatible `patch_x-{x}_y-{y}.png` tiles organized by slide name; run as standalone `--from_stage crop --to_stage crop` or upstream stage in full pipeline

## 2026-05-02 — add pipeline workflow and docs

add standalone Nextflow cell-type prediction workflow
Files/Modules: `main.nf`, `nextflow.config`, `conf/docker.config`, `bin/cell_type_predict.py`, `bin/samplesheet_to_pairs.py`, `tests/fixtures/celltype`, `tests/run_stub_pipeline_checks.sh`, `tests/test_pipeline_contract.py`, `README.md`, `docs/usage.md`
Impact: `nuxplore-cell-type-prediction` users
Reason: provide reproducible DockerHub-backed pipeline with roots/samplesheet modes, strict validation, and testable run contract

Follow-up: execute non-stub end-to-end run against final DockerHub image tag
