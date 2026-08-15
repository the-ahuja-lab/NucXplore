# CHANGELOG

Append-only. Most recent entries first.

Use short, telegraphic style:
- verb + object
- no articles
- concise lines

One entry per task.

## 2026-08-14 — clean repository and synchronize documentation

remove generated build/work/cache outputs and obsolete crop-filter container path; refresh root, package, pipeline, wiki, contributor, model, installation, validation, and release documentation
Files/Modules: READMEs, `docs/`, `wiki/`, ignore rules, container build helper, changelogs
Impact: current 0.3.0 normalization/schema/model/runtime contracts are documented consistently; repository checkout no longer carries disposable local outputs
Reason: make repository easier to install, validate, review, and release without stale operational guidance

## 2026-08-14 — rename segmentation image

rename segmentation container from `nucxplore-rgci-seg` to `nucxplore-seg`; synchronize Dockerfile, environment, process, defaults, tests, scripts, and docs
Files/Modules: `nucxplore-pipeline/`, root and wiki documentation
Impact: production commands and defaults now use `ahujalab/nucxplore-seg:latest`
Reason: align container branding with NucXplore pipeline ownership

## 2026-08-13 — pin the 129-feature extraction schema with regression tests

add `feature_schema_tests` asserting the exact 129-feature key set + nucleus_id (130 keys), finite values, nonzero Hu moments, and positive NND in the full pipeline
Files/Modules: `nucxplore/src/lib.rs`
Impact: any change to the feature contract (names, additions, removals) now fails CI; guards audit findings A04-A07
Reason: previous tests only asserted >= 60 features, so Hu-zero and schema regressions were invisible

## 2026-08-13 — improve wiki diagram legibility

reflow homepage, system-context, and Nextflow diagrams into taller layouts with larger rendered labels
Files/Modules: `wiki/assets/diagrams/home-*.png`, `wiki/assets/diagrams/architecture-system-context.png`, `wiki/assets/diagrams/architecture-pipeline-flow.png`, `CHANGELOG.md`
Impact: desktop, mobile, and low-vision documentation readers
Reason: wide diagram layouts compressed labels at the wiki content width

## 2026-08-13 — polish wiki accessibility and readability

add readable typography, visible focus, underlined content links, responsive tables, accessible full-resolution diagrams, dark-mode framing, reduced-motion handling, and print styles
Files/Modules: `mkdocs.yml`, `wiki/Home.md`, `wiki/Architecture.md`, `wiki/assets/stylesheets/extra.css`, `CHANGELOG.md`
Impact: keyboard, mobile, low-vision, dark-mode, and documentation readers
Reason: make dense technical pages easier to scan, navigate, zoom, and read across devices

## 2026-08-13 — clean repository and pre-render documentation diagrams

remove agent instructions and implementation plans; replace Mermaid runtime diagrams with static PNG assets
Files/Modules: `wiki/Home.md`, `wiki/Architecture.md`, `wiki/Developer-Guide.md`, `wiki/assets/diagrams/*`, `mkdocs.yml`, repository agent and plan files
Impact: repository contributors and hosted documentation readers
Reason: keep public source focused on product code and make architecture diagrams render without client-side JavaScript

## 2026-08-12 — document system and pipeline architecture

add editable system, feature-engine, pipeline, and deployment diagrams with detailed stage and data-flow contracts
Files/Modules: `wiki/Home.md`, `wiki/Architecture.md`, `mkdocs.yml`, `PLAN.md`, `CHANGELOG.md`
Impact: hosted documentation users, pipeline operators, contributors
Reason: explain how package internals and containerized workflow stages connect from input to published results

## 2026-08-12 — refresh hosted documentation homepage

add NucXplore feature overview hero and restructure homepage around capabilities, quick starts, workflow, and guide routes
Files/Modules: `wiki/Home.md`, `wiki/assets/nucxplore-feature-overview.png`, `PLAN.md`, `CHANGELOG.md`
Impact: hosted GitHub Pages readers
Reason: present NucXplore as a navigable product site while retaining detailed wiki documentation

## 2026-08-12 — publish hosted documentation site

render existing wiki pages with MkDocs Material and deploy them to GitHub Pages on documentation changes
Files/Modules: `mkdocs.yml`, `.github/workflows/deploy-pages.yml`, `PLAN.md`, `CHANGELOG.md`
Impact: documentation readers and maintainers
Reason: provide navigable hosted documentation at the repository GitHub Pages URL
## 2026-08-12 — fix Hu moments collapsing to zero in Rust extractor

replace bug-mirroring `python_style_hu_moments` with the correct raw→central→normalized→Hu pipeline; add ellipse regression tests
Files/Modules: `nucxplore/src/lib.rs`, `nucxplore/CHANGELOG.md`
Impact: `hu_moment_1..7` in extracted features are now real invariants instead of constant zeros
Reason: audit finding A04 — the Python-mirroring call pattern yields NaN→0 on modern scikit-image
## 2026-08-13 — prepare 0.3.0 scientific release

restore mandatory deterministic tile-level Vahadane normalization; calculate legacy and V2 Hu invariants from central moments; require NumPy at runtime; add batch dependency extra, license and package metadata; enforce rustfmt, strict Clippy, full-target Rust tests, wheel tests, and pipeline Python contracts in CI
Files/Modules: Rust feature extraction and normalization, Python packaging, release CI, schema documentation
Impact: `post_norm_*` now contains normalized measurements; Hu columns are meaningful; release version and algorithm revision advance to 0.3.0/v3.0
Reason: eliminate silent scientific fallbacks and make release artifacts reproducible and testable

## 2026-08-13 — refine and document V2.1 features

replace approximate V2 gradient summaries with mask-aware cell HOG; replace exterior-filled CCSM enhancement with genuine masked CLAHE; stabilize 90-column schema order and sidecar metadata; document schema accounting and corrected algorithms
Files/Modules: V2/HOG/CCSM feature kernels, Python schema writers and stubs, package/pipeline guides
Impact: V2 values improve without changing V2 names/count; legacy model schema remains unchanged
Reason: exclude rectangular-crop background rigorously and make corrected schema reproducible and auditable

## 2026-08-13 — document original pre/post duplication audit

record exact audit of 248 Sample_For_Adnan CSVs, 79,321 nuclei, 47 feature pairs, and 3,728,087 paired values; clarify 100% equality and schema compatibility rationale; correct earlier exploratory CCSM interpretation
Files/Modules: `nucxplore/docs/feature-schemas.md`, validation wiki
Impact: documents why V2 has 89 numeric features while legacy retains 129 model feature names
Reason: provide reproducible statistical evidence for removing redundant normalization-era aliases only from V2

## 2026-08-13 — remove normalization and replace prediction artifacts

remove stain normalization implementation and public controls; compute raw patch features once and mirror values into legacy pre/post columns; export one raw crop set; replace XGBoost model and label encoder
Files/Modules: `nucxplore/src/lib.rs`, `nucxplore/src/stain_norm/` (removed), Python API/stubs/tests/docs, `nucxplore-pipeline/models/`, predictor, Dockerfile, configuration
Impact: crop layout changes to `nuclei/`; removed normalization arguments are no longer accepted; prediction uses 129-feature `xgboost_best_model.pkl` and `label_encoder.pkl`
Reason: reproduce effective Python reference feature generation and use supplied replacement classifier artifacts

## 2026-05-16 — per-tile featurizer processing

replace batch featurizer (one task for ALL tiles) with per-tile parallel tasks via DISCOVER_PAIRS + EXTRACT_FEATURES_PER_TILE; add extract_single_tile.py and discover_pairs.py helpers; update prediction process to PREDICT_CELL_TILES; add --input-csv mode to cell_type_predict.py
Files/Modules: `nucxplore-pipeline/bin/extract_single_tile.py`, `nucxplore-pipeline/bin/discover_pairs.py`, `nucxplore-pipeline/bin/cell_type_predict.py`, `nucxplore-pipeline/main.nf`, `nucxplore-pipeline/nextflow.config`, `nucxplore-pipeline/conf/containers.config`, `nucxplore-pipeline/tests/run_stub_pipeline_checks.sh`, `nucxplore-pipeline/tests/test_pipeline_contract.py`
Impact: featurizer now parallel per-tile; each task is independent with per-tile output CSVs; stub tests fixed to work with Docker-enabled defaults
Reason: per-tile granularity gives better parallelism, resilience, and resource utilization; failed tiles don't block all other tiles

## 2026-05-14 — conda env for crop/features, per-slide parallelism, engine profiles

move crop/filter and featurizer from Docker to local `nucxplore-local` conda env; feed slides individually for parallel crop processing; add `maxForks 1` on seg + prediction; restructure profiles for docker/apptainer/singularity
Files/Modules: `nucxplore-pipeline/environment.yml`, `nucxplore-pipeline/bin/crop_and_filter.py`, `nucxplore-pipeline/main.nf`, `nucxplore-pipeline/nextflow.config`, `nucxplore-pipeline/conf/containers.config`, `nucxplore-pipeline/conf/docker.config` (removed), `nucxplore-pipeline/tests/run_stub_pipeline_checks.sh`, `nucxplore-pipeline/params.example.yaml`, `wiki/Pipeline-Parameters.md`, `wiki/Pipeline-User-Guide.md`
Impact: pipeline users must create conda env; `--crop_filter_container` removed; crop runs locally; add `-profile apptainer|singularity`
Reason: Docker overhead for CPU-only stages; per-slide parallelism for crop speed; sequential GPU/ML to avoid resource contention

## 2026-05-14 — add --stage shorthand for pipeline single-stage runs

add `--stage` param as single-stage shorthand; `--from_stage`/`--to_stage` remains for custom ranges
Files/Modules: `nucxplore-pipeline/main.nf`, `nucxplore-pipeline/nextflow.config`, `nucxplore-pipeline/tests/run_stub_pipeline_checks.sh`, `nucxplore-pipeline/params.example.yaml`, `wiki/Pipeline-Parameters.md`, `wiki/Pipeline-User-Guide.md`
Impact: pipeline users
Reason: simpler CLI for single-stage runs

## 2026-05-14 — remove stain normalization from featurizer

remove `stain_normalization_features` parameter and `NUQR_ENABLE_STAIN_NORMALIZATION` gate; feature extraction always runs on raw image
Files/Modules: `nucxplore/src/lib.rs`, `nucxplore/python/nucxplore/batch.py`, `nucxplore/python/nucxplore/batch.pyi`, `nucxplore/python/nucxplore/__init__.pyi`, `nucxplore/python/nuqr_featurizer/__init__.pyi`, `nucxplore/tests/test_batch_api.py`, `nucxplore-pipeline/main.nf`, `nucxplore-pipeline/nextflow.config`, `nucxplore-pipeline/tests/test_pipeline_contract.py`, `nucxplore-pipeline/params.example.yaml`, `wiki/*`, `AGENTS.md`
Impact: no behavioral change (env var default was already false); all API callers must drop the removed parameter
Reason: make default explicit and remove dead code path

### Validation

build fresh wheel from modified source; run on all 249 tiles of `Sample_For_Adnan` against precomputed `feat_output/`
- 249/249 completed, 0 failed, 141.4s (8 workers)
- per-tile Pearson R ≥ 0.999999999999999 for all 129 numeric features
- 119 features at exact R = 1.000000000000000
- 6 hu_moment features at R = 0.999999999999996 (compiler reassociation noise)
- 4 features (euler_number, hu_moment_7, both hog_min) have zero variance in this dataset
Results at: `/home/iqr/nucxplore_pipeline_test/Sample_For_Adnan/validation_results/`

## 2026-05-11 — publish package releases to TestPyPI

route package publish workflow to TestPyPI using `TEST_PYPI_API_TOKEN`
Files/Modules: `.github/workflows/publish-pypi.yml`, `CHANGELOG.md`, `nucxplore/CHANGELOG.md`
Impact: package maintainers using `nucxplore-v*` tags or manual publish workflow
Reason: private repo cannot use GitHub environment setup for trusted publishing

## 2026-05-10 — refresh public docs and wiki pages

make root/package/pipeline docs concise and add detailed GitHub-wiki-ready pages for current APIs, pipeline parameters, Docker, validation, and developer workflows
Files/Modules: `README.md`, `nucxplore/README.md`, `nucxplore/docs/*`, `nucxplore-pipeline/README.md`, `nucxplore-pipeline/docs/*`, `wiki/*`, `plans/documentation-current-code.md`, `PLAN.md`, `CHANGELOG.md`, `nucxplore/CHANGELOG.md`, `nucxplore-pipeline/CHANGELOG.md`
Impact: package users, pipeline users, contributors, GitHub wiki publishing
Reason: align documentation with current code while keeping public-facing entrypoints concise

## 2026-05-09 — generate Docker reference CSVs and tolerance-based validation

create `Docker_References/GTEX-1F75B-0126/` with feature/prediction CSVs from verified pipeline run; add `nucxplore-pipeline/scripts/validate_against_reference.py` with exact check for non-CCSM and tolerance check for CCSM features; run same-build comparison (passes at 100%) and cross-build comparison against old Conda precomputed (massive drift — confirms old references used fundamentally different codebase)
Files/Modules: `Docker_References/README.md`, `Docker_References/GTEX-1F75B-0126/features/*`, `Docker_References/GTEX-1F75B-0126/predictions/*`, `nucxplore-pipeline/scripts/validate_against_reference.py`, `CHANGELOG.md`, `nucxplore-pipeline/CHANGELOG.md`
Impact: downstream validation uses Docker reference; old Conda-based Sample_For_Adnan data is from different codebase, not a reliable target for exact match
Reason: CCSM features have ULP-level non-determinism from floating-point reassociation; use tolerance for CCSM, exact for everything else

## 2026-05-09 — fix Nextflow CLI boolean parsing

parse boolean params explicitly so CLI string `false` disables feature flags
Files/Modules: `nucxplore-pipeline/main.nf`, `nucxplore-pipeline/tests/test_pipeline_contract.py`, `nucxplore-pipeline/tests/run_stub_pipeline_checks.sh`, `nucxplore-pipeline/CHANGELOG.md`, `PLAN.md`
Impact: pipeline users passing boolean params such as `--stain_normalization_features false`
Reason: Groovy `as Boolean` treated non-empty string `false` as truthy, so no-stain runs still used stain-normalization features

## 2026-05-08 — fix publishing of directory outputs

publish declared directory outputs instead of nested globs and align crop output dir name with published `crops`
Files/Modules: `nucxplore-pipeline/main.nf`, `nucxplore-pipeline/CHANGELOG.md`
Impact: pipeline users expecting crops, segmentation MATs, features, nuclei, and predictions under `--outdir`
Reason: run completed successfully but only logs were published; data remained in Nextflow work directories

## 2026-05-08 — use NVIDIA runtime for SEG Docker GPU

switch CUDA segmentation Docker options from `--gpus all` to NVIDIA runtime env flags
Files/Modules: `nucxplore-pipeline/conf/docker.config`, `nucxplore-pipeline/CHANGELOG.md`
Impact: Docker GPU segmentation users on hosts using NVIDIA CDI/runtime hook
Reason: local Docker rejects direct `--gpus` hook invocation and requires `--runtime=nvidia`

## 2026-05-08 — use ahujalab local Docker image tags

set pipeline defaults, examples, and local build/run helpers to `ahujalab/...:latest` images
Files/Modules: `README.md`, `nucxplore-pipeline/nextflow.config`, `nucxplore-pipeline/params.example.yaml`, `nucxplore-pipeline/README.md`, `nucxplore-pipeline/docs/user-guide.md`, `nucxplore-pipeline/docs/developer-guide.md`, `nucxplore-pipeline/scripts/build_docker_images.sh`, `nucxplore-pipeline/scripts/run_local_svs_pipeline.sh`
Impact: local Docker pipeline users
Reason: Nextflow Docker runs should reference the same local tags built by helper scripts before falling back to pull behavior

## 2026-05-08 — fix segmentation task GPU and cancellation behavior

declare SEG accelerator resource, run segmentation CLI with exec, and cover contract in tests
Files/Modules: `nucxplore-pipeline/main.nf`, `nucxplore-pipeline/tests/test_pipeline_contract.py`, `nucxplore-pipeline/CHANGELOG.md`, `PLAN.md`
Impact: pipeline users running RGCI/HEIP segmentation
Reason: make CUDA SEG intent explicit and prevent orphaned Python inference after Nextflow cancellation

## 2026-05-08 — simplify local Docker Nextflow execution

build feature image from local maturin wheel, add local image/run helpers, keep Docker tasks on host UID
Files/Modules: `nucxplore-pipeline/Dockerfile`, `nucxplore-pipeline/Dockerfile.crop-filter`, `nucxplore-pipeline/conf/docker.config`, `nucxplore-pipeline/scripts/build_docker_images.sh`, `nucxplore-pipeline/scripts/run_local_svs_pipeline.sh`, `nucxplore-pipeline/README.md`, `nucxplore-pipeline/docs/developer-guide.md`
Impact: local pipeline users and Docker image maintainers
Reason: avoid unpublished PyPI dependency for featurizer and make Nextflow micromamba/Docker run path repeatable

## 2026-05-08 — fix review follow-up gaps

format MAT parser tests, create direct CLI output/log parents, label superseded historical plans
Files/Modules: `nucxplore/src/io/mat.rs`, `nucxplore-pipeline/bin/crop_and_filter.py`, `nucxplore-pipeline/bin/rgci_seg_to_mat.py`, `plans/cell-type-prediction-nextflow.md`, `plans/documentation-split-cleanup.md`
Impact: package CI, direct pipeline CLI users, contributors reading plans
Reason: complete review findings after validating codebase against active consolidation plans

## 2026-05-07 — fix package import and MAT parser correctness (milestone 4 of consolidation-review-follow-up)

lazy-load batch imports, fix MAT v5 small-element total size, remove orphaned _core.pyi stub
Files/Modules: `nucxplore/python/nucxplore/__init__.py`, `nucxplore/src/io/mat.rs`, `nucxplore/python/nuqr_featurizer/_core.pyi`
Impact: package users, MAT file consumers
Reason: bare import nucxplore failed without numpy due to top-level batch import; MAT small elements computed wrong total_size (4+align8 instead of 8), desynchronizing parser; nuqr_featurizer._core.pyi was orphaned

## 2026-05-07 — fix pipeline runtime failures: empty inputs, required outputs, Docker build (milestone 3 of consolidation-review-follow-up)

fix empty-input handling in crop/seg scripts, make optional Nextflow outputs truly optional, fix rgci-seg Docker build
Files/Modules: `nucxplore-pipeline/Dockerfile.rgci-seg`, `nucxplore-pipeline/main.nf`, `nucxplore-pipeline/bin/crop_and_filter.py`, `nucxplore-pipeline/bin/rgci_seg_to_mat.py`, `nucxplore-pipeline/tests/test_pipeline_contract.py`
Impact: pipeline users, Docker image maintainers
Reason: empty crop/seg input returned success then failed downstream; nuclei/predictions/** outputs were required even when validly absent; Dockerfile.rgci-seg copied checkpoint into missing directory

## 2026-05-07 — align pipeline docs, container placeholders, and Dockerfile install mode (milestone 2 of consolidation-review-follow-up)

add root facade nextflow run . examples, align container default, add dual-mode feature/prediction Dockerfile
Files/Modules: `nucxplore-pipeline/README.md`, `nucxplore-pipeline/docs/user-guide.md`, `nucxplore-pipeline/docs/developer-guide.md`, `nucxplore-pipeline/nextflow.config`, `nucxplore-pipeline/Dockerfile`, `nucxplore-pipeline/main.nf`
Impact: pipeline users and Docker image maintainers
Reason: root nextflow.config facade under-documented; container placeholder differed across config/docs; Dockerfile always built from source despite docs describing PyPI production installs

## 2026-05-07 — align release workflow and docs (milestone 1 of consolidation-review-follow-up)

add workflow_dispatch to publish-pypi.yml and document ABI3 wheel coverage in developer guide
Files/Modules: `.github/workflows/publish-pypi.yml`, `nucxplore/docs/developer-guide.md`
Impact: package release maintainers
Reason: manual dispatch was documented but not implemented; ABI3 coverage (one wheel per OS for Python 3.8+) was implicit

## 2026-05-07 — consolidate package and pipeline into single repo

add root README, nextflow.config facade, AGENTS.md, .gitignore, .dockerignore, and CHANGELOG for combined repository
Files/Modules: **README.md, **nextflow.config, **AGENTS.md, **.gitignore, **.dockerignore, **CHANGELOG.md, `nucxplore-pipeline/` (renamed from `nucxplore-cell-type-prediction/`)
Impact: all users and contributors
Reason: single GitHub repository for both library and pipeline; package-only PyPI publishing via nucxplore-v* tags; root nextflow.config enables nextflow run <org>/<repo> -r <tag>
