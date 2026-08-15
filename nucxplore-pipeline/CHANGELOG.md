# CHANGELOG

Append-only. Most recent entries first.

Use short, telegraphic style:
- verb + object
- no articles
- concise lines

One entry per task.

## 2026-08-15 — standardize segmentation name and prediction labels

rename segmentation CLI and contracts to NucXplore; correct eight label-encoder class names without changing class order; refresh workflow diagrams
Files/Modules: segmentation CLI/Dockerfile/Nextflow/tests, prediction encoder/manifest/tests, pipeline docs and diagrams
Impact: runtime identifiers and output labels match current product terminology and documented prediction classes
Reason: remove legacy naming and fix capitalization/spelling at the prediction artifact boundary

## 2026-08-14 — remove obsolete crop-filter image path

stop building unused crop-filter container; remove stale Dockerfile; document two-image runtime, hosted repository, mandatory normalization, current model manifest, and CI gates
Files/Modules: pipeline README/guides, wiki, Docker build helper, ignore rules
Impact: build helper now produces only segmentation and prediction images; documentation matches active conda/container split
Reason: eliminate dead deployment surface and conflicting operational instructions

## 2026-08-14 — rename segmentation image

rename segmentation Dockerfile, environment, process, defaults, test placeholders, and image tag to `nucxplore-seg`
Files/Modules: segmentation Docker assets, Nextflow configuration/workflow, build/run scripts, tests, docs
Impact: build and run `ahujalab/nucxplore-seg:latest`; old image name is no longer referenced by active configuration
Reason: use product-level image naming while retaining NucXplore as implementation detail

## 2026-08-14 — replace cell-type prediction artifacts

replace bundled XGBoost classifier and label encoder with `WSI_Sample_Adnan` artifacts; update hashes, labels, and model-use contract
Files/Modules: `models/`, prediction artifact tests
Impact: predictions use new 4,000-tree model; model actively uses normalized features and corrected Hu moments
Reason: deploy user-supplied WSI classifier and matching encoder

## 2026-08-13 — adopt mandatory normalized 0.3.0 features

make Vahadane normalization unconditional; record v3.0 algorithm provenance; retain 129-name prediction schema; verify bundled model ignores normalized and Hu inputs; expand release contracts
Files/Modules: per-tile extraction, Nextflow metadata, model audit, tests and guides
Impact: no normalization opt-out; pre/post values become distinct without changing bundled-model decisions
Reason: restore intended feature semantics while preserving validated classifier behavior

## 2026-08-13 — publish V2.1 schema metadata

write deterministic feature order and sidecars with schema revision/count; expose documented legacy, dual, and V2 pipeline selection
Files/Modules: per-tile helper, Nextflow configuration/contracts, pipeline guides
Impact: V2 stays 90 API columns; legacy prediction remains default
Reason: make corrected feature output auditable without breaking model compatibility

## 2026-08-13 — use raw features and replacement classifier

remove stain normalization and split crop controls; preserve 129-column model schema by duplicating raw patch features into pre/post namespaces; bake `xgboost_best_model.pkl` and `label_encoder.pkl`; pin artifact-compatible prediction dependencies
Files/Modules: package Rust/Python API, `bin/extract_single_tile.py`, `bin/cell_type_predict.py`, `models/`, `Dockerfile`, configuration, tests, docs
Impact: feature crops publish under `nuclei/`; prediction labels may differ from historical model outputs by design
Reason: match effective Python reference behavior and deploy supplied replacement artifacts

## 2026-05-16 — per-tile featurizer processing

replace batch featurizer with per-tile parallel via DISCOVER_PAIRS + EXTRACT_FEATURES_PER_TILE; add extract_single_tile.py and discover_pairs.py; rename PREDICT_CELL_TYPES to PREDICT_CELL_TILES; add --input-csv to cell_type_predict.py; fix stub tests for Docker-enabled defaults (copy pipeline to /home/iqr/ for Docker filesystem access)
Files/Modules: `bin/extract_single_tile.py` (new), `bin/discover_pairs.py` (new), `bin/cell_type_predict.py`, `main.nf`, `nextflow.config`, `conf/containers.config`, `tests/run_stub_pipeline_checks.sh`, `tests/test_pipeline_contract.py`, `CHANGELOG.md`
Impact: featurizer runs per-tile parallel; each CSV is produced independently; failed tiles don't block others
Reason: per-tile granularity for better parallelism and fault isolation

## 2026-05-14 — conda env for crop/features, per-slide parallelism, engine profiles

move CROP_AND_FILTER and EXTRACT_FEATURES from Docker to `nucxplore-local` conda env; per-slide parallel crop via `--slide-path`; add `maxForks 1` to NUCXPLORE_SEG and PREDICT_CELL_TYPES; replace `conf/docker.config` with `conf/containers.config` for multi-engine support; add apptainer/singularity profiles; remove `crop_filter_container` param
Files/Modules: `environment.yml` (new), `bin/crop_and_filter.py`, `main.nf`, `nextflow.config`, `conf/containers.config` (new), `conf/docker.config` (deleted), `tests/run_stub_pipeline_checks.sh`, `params.example.yaml`, `CHANGELOG.md`
Impact: users must create `nucxplore-local` conda env; `--crop_filter_container` removed; crop runs locally; `-profile apptainer|singularity` now available
Reason: large Docker overhead for CPU-only stages; per-slide parallelism improves crop throughput; sequential seg+pred avoids GPU/ML resource contention

## 2026-05-14 — add --stage shorthand for single-stage runs

add `--stage` param as single-stage shorthand; `--from_stage`/`--to_stage` remains for custom ranges; default stays full pipeline
Files/Modules: `main.nf`, `nextflow.config`, `tests/run_stub_pipeline_checks.sh`, `params.example.yaml`, `CHANGELOG.md`
Impact: pipeline users; `--stage features` replaces `--from_stage features --to_stage features`
Reason: simpler CLI for single-stage runs

## 2026-05-10 — refresh pipeline docs and wiki pages

make pipeline README and guides concise; move detailed run examples, parameter reference, Docker image contract, validation, and troubleshooting content to wiki pages
Files/Modules: `README.md`, `docs/user-guide.md`, `docs/developer-guide.md`, `docs/usage.md`, `../wiki/Pipeline-User-Guide.md`, `../wiki/Pipeline-Parameters.md`, `../wiki/Docker-and-Validation.md`, `../wiki/Developer-Guide.md`, `CHANGELOG.md`
Impact: pipeline users, Docker image maintainers, contributors
Reason: align docs with current defaults, explicit boolean parsing, published output directories, and local `ahujalab/...:latest` image workflow

## 2026-05-09 — add Docker reference CSVs and tolerance validation script

create `Docker_References/GTEX-1F75B-0126/` from verified pipeline run; add `scripts/validate_against_reference.py` with tolerance-based CCSM check and exact non-CCSM check; document historical reference drift
Files/Modules: `../Docker_References/README.md`, `../Docker_References/GTEX-1F75B-0126/*`, `scripts/validate_against_reference.py`, `../CHANGELOG.md`, `CHANGELOG.md`
Impact: deterministic validation for downstream CI; CCSM tolerance avoids false failures from ULP drift
Reason: CCSM has sub-ULP non-determinism from floating-point reassociation; exact check for everything else

## 2026-05-09 — fix CLI boolean parsing

parse boolean params explicitly so string `false` disables feature flags
Files/Modules: `main.nf`, `tests/test_pipeline_contract.py`, `tests/run_stub_pipeline_checks.sh`, `CHANGELOG.md`
Impact: Nextflow users passing CLI booleans such as `--stain_normalization_features false`
Reason: Groovy `as Boolean` kept non-empty string `false` truthy and emitted `--stain-normalization-features`

## 2026-05-08 — fix publishing of directory outputs

publish `crops`, `segmentation_mats`, `features`, `nuclei`, and `predictions` directory outputs by declared output name
Files/Modules: `main.nf`, `CHANGELOG.md`
Impact: all full pipeline runs and stage runs that expect published data directories
Reason: directory output contents were produced in work dirs but skipped by `publishDir` nested glob patterns

## 2026-05-08 — use NVIDIA runtime for SEG Docker GPU

switch CUDA segmentation container options to `--runtime=nvidia` with NVIDIA visibility env
Files/Modules: `conf/docker.config`, `CHANGELOG.md`
Impact: CUDA segmentation Docker runs
Reason: host NVIDIA container runtime rejects direct `--gpus all` CDI hook invocation

## 2026-05-08 — use ahujalab local Docker image tags

set default containers, docs, params example, and local helpers to `ahujalab/...:latest`
Files/Modules: `nextflow.config`, `params.example.yaml`, `README.md`, `docs/user-guide.md`, `docs/developer-guide.md`, `scripts/build_docker_images.sh`, `scripts/run_local_svs_pipeline.sh`, `CHANGELOG.md`
Impact: local Docker users
Reason: align Nextflow container names with locally built images and Docker pull fallback behavior

## 2026-05-08 — fix SEG GPU declaration and cancellation

declare NUCXPLORE_SEG accelerator resource and exec segmentation CLI from task script
Files/Modules: `main.nf`, `tests/test_pipeline_contract.py`, `CHANGELOG.md`
Impact: segmentation-only and crop-to-segmentation pipeline users
Reason: make CUDA scheduling intent visible to Nextflow and reduce orphaned Python processes after cancellation

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

pin feature/prediction deps, rebuild crop/filter deps, and switch NucXplore image to micromamba Python 3.9 env
Files/Modules: `Dockerfile`, `Dockerfile.crop-filter`, `Dockerfile.nucxplore-seg`, `envs/nucxplore-seg.yml`, `conf/docker.config`, `main.nf`, `nextflow.config`, `.dockerignore`, `../.dockerignore`, `../HEIP/HEIP/src/unet.py`
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

## 2026-05-04 — add NucXplore segmentation stage

add CUDA segmentation stage producing NuXplore-compatible MAT masks from crop tiles
Files/Modules: `bin/nucxplore_seg_to_mat.py`, `Dockerfile.nucxplore-seg`, `main.nf` (NUCXPLORE_SEG process, stageIdx helper, container validation), `conf/docker.config` (--gpus all for segmentation), `tests/run_stub_pipeline_checks.sh`
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
