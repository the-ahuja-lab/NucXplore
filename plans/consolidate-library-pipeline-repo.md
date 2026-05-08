# EXECPLAN

## Task

Consolidate the NucXplore Rust/PyO3 package library and the Nextflow cell-type prediction pipeline into one GitHub repository while keeping release automation limited to building and publishing the `nucxplore` Python wheel to PyPI.

## Goal

The combined repository has one source-of-truth checkout that contains both the package library and the Nextflow workflow. Users can install the library with `pip install nucxplore`, developers can release wheels from the library subdirectory, and users can run the Nextflow pipeline directly from its subdirectory without requiring the pipeline to be packaged or published as part of the library build.

## Scope

- Modules: repository root metadata and docs, `nucxplore/` package library, target `nucxplore-pipeline/` Nextflow pipeline, `.github/workflows/` package-only release automation.
- Files likely involved: root `README.md`, root `nextflow.config`, root `AGENTS.md`, root `CHANGELOG.md`, `.gitignore` / `.dockerignore` if present or needed, `.github/workflows/*.yml`, `nucxplore/README.md`, `nucxplore/docs/user-guide.md`, `nucxplore/docs/developer-guide.md`, `nucxplore/CHANGELOG.md`, current `nucxplore-cell-type-prediction/` files renamed to `nucxplore-pipeline/` (`README.md`, `docs/user-guide.md`, `docs/developer-guide.md`, `docs/usage.md`, `nextflow.config`, `params.example.yaml`, `CHANGELOG.md`, tests, `bin/`, `conf/`, Dockerfiles).
- Downstream impact: package users, PyPI release maintainers, Nextflow users, Docker/runtime image maintainers, documentation links, GitHub Actions permissions and secrets.
- Out of scope unless explicitly approved: changing the `nucxplore` Python package name, publishing the pipeline as a Python package, building or pushing Docker images in the default GitHub release process, changing pipeline stage behavior, moving model artifacts into PyPI wheels, replacing runtime container requirements, or rewriting Nextflow process logic.

## Context

The workspace currently contains two project roots intended as separate repositories:

- `nucxplore/` is the Rust + PyO3 Python package. `pyproject.toml` uses `maturin` with package name `nucxplore`, version `0.2.0`, module `nucxplore._core`, and `python-source = "python"`. Local release commands are run from `nucxplore/`.
- `nucxplore-cell-type-prediction/` is the current Nextflow pipeline directory and will be renamed to `nucxplore-pipeline/` during consolidation. `main.nf` and `nextflow.config` live at that subdirectory root. The workflow runs crop, segmentation, features, and prediction stages. Its docs currently say it is a standalone repository and should consume released wheels or DockerHub-hosted runtime images.
- Current docs explicitly describe a split-repository boundary. The requested desired state reverses that: one GitHub repository containing both directories, with the build/release process only handling the library wheel and PyPI publishing.
- No `.github/workflows/` files were found under either current subproject, so release automation likely needs to be added rather than edited.
- The top-level workspace is not currently a git repository in this environment, so final implementation should be validated in the intended GitHub repository checkout before publishing automation is enabled.

Desired behavior after consolidation:

- Root repository presents itself as the monorepo for NucXplore package plus pipeline.
- `nucxplore/` remains the package build root. Wheel builds run with `working-directory: nucxplore` and do not include pipeline files in the wheel.
- `nucxplore-pipeline/` remains runnable as a Nextflow subdirectory for development, for example `nextflow run ./nucxplore-pipeline -profile docker ...` from the repo root or `nextflow run . -profile docker ...` from inside the pipeline directory.
- GitHub release automation builds and publishes only PyPI artifacts for `nucxplore`; pipeline Docker images remain external/manual unless a later plan adds separate non-release automation.
- Documentation explains the single-repo layout without implying that the Nextflow pipeline is uploaded to PyPI or built by the wheel workflow.
- Normal pipeline users run the hosted GitHub repository with `nextflow run <org>/<repo> -r <tag>` through a root `nextflow.config` facade; cloning is for source review and development only.

## Constraints

- Preserve `pip install nucxplore` functionality and current PyPI package metadata.
- Preserve pipeline run contracts, stage names, parameters, and Docker runtime behavior unless separately requested.
- Avoid broad code refactors; this is primarily repository organization, CI, and documentation work.
- Keep package and pipeline dependency boundaries explicit. The library wheel must not depend on Nextflow, Docker, HEIP checkpoints, model artifacts, XGBoost pipeline models, or pipeline-only scripts.
- Keep release automation least-privilege: PyPI publishing should use trusted publishing or PyPI API tokens only for the package release job.
- Do not add DockerHub publishing to the package wheel build workflow.
- Validate each milestone independently.

## Evidence

- User report: requested a thorough plan to combine the Nextflow pipeline and library into one GitHub repository, keep build process limited to wheel building and PyPI publishing for pip install functionality, allow Nextflow to run from a subdirectory, update documentation accordingly, and ask open questions.
- Current package README: says the library repository is separate from `nucxplore-cell-type-prediction`.
- Current pipeline README: says the pipeline repository is separate and consumes released wheels or DockerHub runtime images.
- Current package config: `nucxplore/pyproject.toml` is already scoped so `maturin` builds only the library from `nucxplore/`.
- Current pipeline config: `nucxplore-cell-type-prediction/main.nf` and `nextflow.config` are already self-contained under a subdirectory.
- Related tests: package validation uses `cargo fmt --all`, `cargo test --tests`, and Python compile checks from `nucxplore/`; pipeline validation uses `bash tests/run_stub_pipeline_checks.sh` and `python -m pytest tests/test_pipeline_contract.py tests/test_cell_type_predict.py` from `nucxplore-cell-type-prediction/`.
- Local tool environments: Nextflow is available in the micromamba environment named `nextflow`; maturin/Rust package build tools are available in the micromamba environment named `rustenv`.
- Nextflow official sharing docs: GitHub-hosted pipelines are run with `nextflow run <org>/<repo>` or a full repository URL; by default Nextflow expects `main.nf` at the pipeline project root, or a different entry script via `manifest.mainScript` in `nextflow.config`.
- Nextflow official CLI/config docs: `nextflow run [options] [project]` supports `-main-script`; remote repositories are cached under `$HOME/.nextflow/assets/`; config files are applied from `$NXF_HOME/config`, project `nextflow.config`, launch `nextflow.config`, then `-c`; `projectDir` is the directory where the main script is located; `includeConfig` relative paths resolve against the including config file.

## Progress

- [x] 2026-05-07T00:00Z — Inventoried current docs, package config, pipeline config, and absence of existing GitHub workflows.
- [x] 2026-05-07T00:00Z — Checked current Nextflow GitHub sharing, CLI, and config documentation with Context7 and official docs.
- [x] 2026-05-07T00:00Z — Resolved Milestone 1 repository contract questions with user decisions.
- [x] 2026-05-07T00:00Z — Implemented Milestone 2: root README, nextflow.config facade, AGENTS.md, .gitignore, .dockerignore, root CHANGELOG.
- [x] 2026-05-07T00:00Z — Implemented Milestone 3: package docs update (README, user-guide, developer-guide, CHANGELOG).
- [x] 2026-05-07T00:00Z — Implemented Milestone 6: documented package-only CI scope in pipeline README and developer guide.
- [x] 2026-05-07T00:00Z — Implemented Milestone 7: end-to-end documentation consistency check; all stale phrases reviewed, command patterns verified.

## Discovery Log

- Finding: Existing documentation encodes a split-repository model.
  Evidence: `nucxplore/README.md` line 5 and `nucxplore-cell-type-prediction/README.md` line 5 describe separate repositories.
  Impact: documentation must be updated in both subprojects plus a new root README should define the monorepo model.
- Finding: The package build is already naturally subdirectory-scoped.
  Evidence: `nucxplore/pyproject.toml` uses `maturin`, `python-source = "python"`, and package lists only `nucxplore` and compatibility package `nuqr_featurizer`.
  Impact: GitHub Actions can safely run wheel builds from `nucxplore/` without moving package code.
- Finding: The pipeline is already naturally subdirectory-runnable.
  Evidence: `nucxplore-cell-type-prediction/main.nf` and `nextflow.config` are colocated, and docs already instruct commands from that directory.
  Impact: no Nextflow logic changes should be required unless repository-relative paths or docs assume standalone repo root.
- Finding: No existing GitHub Actions workflows were found.
  Evidence: glob search for `nucxplore/.github/workflows/*` and `nucxplore-cell-type-prediction/.github/workflows/*` returned no files.
  Impact: add new workflows at combined repo root rather than migrating existing workflow files.
- Finding: Nextflow docs describe GitHub pipeline execution at the repository/project level, not a documented shorthand for running a subdirectory such as `nextflow run org/repo/path`.
  Evidence: official sharing and CLI docs show `nextflow run acme/hello`, `nextflow run https://github.com/acme/hello`, local script/project execution, and alternate entry scripts via `manifest.mainScript` or `-main-script`.
  Impact: for user-facing hosted execution, provide a repository-root Nextflow facade so users can run `nextflow run <org>/<repo> -r <tag>` while keeping implementation files under target `nucxplore-pipeline/`.
- Finding: A root `nextflow.config` can point to a subdirectory entry script using `manifest.mainScript`, and `includeConfig` can compose the subdirectory config.
  Evidence: official docs define `manifest.mainScript`, config lookup order, and relative `includeConfig` path resolution against the including file.
  Impact: add root `nextflow.config` with only the hosted-run facade, e.g. `manifest.mainScript = 'nucxplore-pipeline/main.nf'` and `includeConfig 'nucxplore-pipeline/nextflow.config'`; keep actual pipeline logic and process config in the subdirectory.
- Finding: Current environment cannot execute Nextflow because Java is missing or too old.
  Evidence: `nextflow -version` failed with `ERROR: Cannot find Java or it's a wrong version -- please make sure that Java 17 or later (up to 26) is installed`.
  Impact: run Nextflow validation after activating the `nextflow` micromamba environment, which should provide the expected Java/Nextflow runtime.

## Decision Log

- Decision: Keep `nucxplore/` as the library build root.
  Reason: minimizes packaging risk; current `pyproject.toml`, `Cargo.toml`, tests, docs, and release commands are already based on this root.
  Date: 2026-05-07
- Decision: Rename the pipeline directory from `nucxplore-cell-type-prediction/` to `nucxplore-pipeline/` during consolidation.
  Reason: user selected `nucxplore-pipeline`; the new path is shorter and clearer while preserving the NucXplore brand.
  Date: 2026-05-07
- Decision: Keep GitHub Actions package-only for now; do not add pipeline validation workflow in this consolidation task.
  Reason: user selected package-only Actions so CI/release automation only handles library wheel build/test/publish.
  Date: 2026-05-07
- Decision: Prefer a repository-root `nextflow.config` facade over asking users to pass `-main-script` for normal hosted runs.
  Reason: official `nextflow run <org>/<repo>` UX expects the repository to identify its main script; a root facade preserves that UX while keeping real pipeline code in the subdirectory.
  Date: 2026-05-07
- Decision: Keep root-level Nextflow files minimal and declarative; do not duplicate pipeline logic at root.
  Reason: source code remains reviewable and maintainable under `nucxplore-pipeline/`, while root files only adapt the monorepo layout to Nextflow's hosted repository model.
  Date: 2026-05-07
- Decision: Use `NucXplore` as the public repository/project display name.
  Reason: user selected the project brand for public docs while preserving lowercase `nucxplore` for PyPI/imports.
  Date: 2026-05-07
- Decision: Publish PyPI packages from package-specific tags matching `nucxplore-v*`.
  Reason: avoids accidental package release from pipeline-only repository tags or docs-only tags.
  Date: 2026-05-07
- Decision: Use PyPI trusted publishing via GitHub OIDC.
  Reason: user selected trusted publishing; avoids long-lived PyPI token secrets.
  Date: 2026-05-07
- Decision: Keep Docker image publishing manual/external to package release automation.
  Reason: user selected manual/external Docker handling; package release workflow must not build or push Docker images.
  Date: 2026-05-07
- Decision: Use dual-mode `nucxplore` installation in feature/prediction Docker docs.
  Reason: production images should install released `nucxplore` from PyPI; development images may install from the local source checkout.
  Date: 2026-05-07
- Decision: Maintain root plus subproject changelogs.
  Reason: root changelog records repo-level consolidation outcomes; subproject changelogs record library- or pipeline-specific changes.
  Date: 2026-05-07
- Decision: Keep historical plans/changelog entries intact.
  Reason: user selected preserving completed history; update current public docs only.
  Date: 2026-05-07
- Decision: Build PyPI wheels for Linux, macOS, and Windows.
  Reason: user selected broad platform wheel publishing for supported Python versions.
  Date: 2026-05-07

## Milestones

### Milestone 1 — Confirm Repository Contract

Goal: Lock the consolidation contract before editing docs or CI.

Edits:
- None initially; update this ExecPlan with confirmed answers.

Validation:
- Confirmed repository name `NucXplore`, target pipeline directory `nucxplore-pipeline/`, hosted Nextflow root facade, package-only GitHub Actions, package tags `nucxplore-v*`, PyPI trusted publishing, manual/external Docker publishing, dual-mode Docker `nucxplore` install, root plus subproject changelogs, preserved historical records, and Linux/macOS/Windows wheels.

Risk:
- If directory names or release triggers are guessed incorrectly, documentation and GitHub Actions can encode the wrong public workflow.

### Milestone 2 — Root Monorepo Entry Points

Goal: Add top-level documentation and metadata that explain the combined repository without changing package or pipeline behavior.

Edits:
- `README.md`: add monorepo overview, source layout, quick links, install command, hosted Nextflow run command, developer subdirectory run command, release boundary, and validation summary.
- `nextflow.config`: add a repository-root hosted-run facade with `manifest.mainScript = 'nucxplore-pipeline/main.nf'` and `includeConfig 'nucxplore-pipeline/nextflow.config'` so `nextflow run <org>/<repo>` works from GitHub while actual workflow code remains in the subdirectory.
- `AGENTS.md`: update repository guidelines to describe the combined repo as canonical rather than future separate repositories.
- `.gitignore`: ensure Rust, Python, Nextflow, Docker, build, cache, virtualenv, wheel, and pipeline work directories are ignored without hiding source files.
- `.dockerignore`: keep large local artifacts, virtualenvs, Nextflow work dirs, build outputs, notebooks caches, and model outputs out of Docker build contexts if Dockerfiles remain.
- `CHANGELOG.md`: if a root changelog is desired, create it from the template and add a consolidation documentation entry; otherwise keep subproject changelogs only.

Validation:
- Manual link check: all referenced files exist.
- Confirm root instructions work in principle from a fresh checkout: package commands specify `cd nucxplore`; hosted pipeline commands specify `nextflow run <org>/<repo> -r <tag>`; local developer commands specify either `nextflow run .` from repo root, `nextflow run ./nucxplore-pipeline`, or `cd nucxplore-pipeline && nextflow run .`.

Risk:
- A root README can duplicate subproject docs and drift. Keep root concise and link to canonical subproject guides.

### Milestone 3 — Package Docs For Monorepo Release

Goal: Make library docs accurate for a package subdirectory inside a combined repository.

Edits:
- `nucxplore/README.md`: replace separate-repository language with combined-repo language; keep `pip install nucxplore` quickstart.
- `nucxplore/docs/user-guide.md`: clarify that users install from PyPI and do not need the pipeline subdirectory for library APIs.
- `nucxplore/docs/developer-guide.md`: update repository boundary, local setup paths, validation commands, and release workflow to state all package build/release commands run from `nucxplore/`.
- `nucxplore/CHANGELOG.md`: add a durable documentation/release-boundary entry if docs are changed.

Validation:
- From `nucxplore/`: `python -m py_compile python/nucxplore/batch.py scripts/batch_extract_and_crop.py`.
- From `nucxplore/`: `cargo fmt --all --check` if stable in this repo; otherwise `cargo fmt --all` only if formatting changes are intended.
- From `nucxplore/`: `cargo test --tests` when time/environment permits.
- Manual check that docs do not claim pipeline code is packaged into the wheel.

Risk:
- Users may confuse monorepo checkout with PyPI install. Keep docs explicit: PyPI package is only `nucxplore`; pipeline is run with Nextflow from its directory.

### Milestone 4 — Pipeline Docs For Subdirectory Runs

Goal: Make pipeline docs accurate for running Nextflow from a subdirectory in the combined repository.

Edits:
- Rename `nucxplore-cell-type-prediction/` to `nucxplore-pipeline/` and update path-sensitive references.
- `nucxplore-pipeline/README.md`: replace standalone-repo language; add hosted, root-local, and directory-local run examples.
- `nucxplore-pipeline/docs/user-guide.md`: update clone/setup instructions, command examples, path references, and clarify that PyPI wheel publishing is unrelated to pipeline execution images.
- `nucxplore-pipeline/docs/developer-guide.md`: update repository boundary, source layout, validation commands, and Docker image guidance to reflect combined repo plus package-only release automation.
- `nucxplore-pipeline/docs/usage.md`: keep compatibility pointer accurate.
- `nucxplore-pipeline/params.example.yaml`: update comments only if they reference standalone repository assumptions.
- `nucxplore-pipeline/CHANGELOG.md`: add documentation/consolidation entry.

Validation:
- From repo root: `nextflow run ./nucxplore-pipeline -stub-run --from_stage features --to_stage prediction ...` using existing fixture/placeholder-safe test inputs if available, or run the existing script from the pipeline directory.
- From repo root after adding the facade: `nextflow run . -stub-run --from_stage features --to_stage prediction ...` to prove root `manifest.mainScript` and included subdirectory config resolve correctly.
- From `nucxplore-pipeline/`: `bash tests/run_stub_pipeline_checks.sh`.
- From `nucxplore-pipeline/`: `python -m pytest tests/test_pipeline_contract.py tests/test_cell_type_predict.py`.
- Manual check that public hosted examples use `nextflow run <org>/<repo> -r <tag>`, root checkout examples use `nextflow run .`, explicit developer examples may use `nextflow run ./nucxplore-pipeline`, and subdirectory-local examples use `nextflow run .` from inside `nucxplore-pipeline/`.

Risk:
- Nextflow resolves relative includes and config paths based on launch directory and project directory. Test both root-relative and directory-local invocations if docs advertise both.
- If root `manifest.mainScript` changes `projectDir` to the subdirectory as documented, `bin/` command discovery should continue to use `nucxplore-pipeline/bin`; validate this with stub runs in the `nextflow` micromamba environment.

### Milestone 5 — Package-Only GitHub Actions Release

Goal: Add CI/release automation that builds and publishes only the `nucxplore` library wheel and sdist.

Edits:
- `.github/workflows/package-ci.yml`: PR/push validation for package changes only, using `paths` filters such as `nucxplore/**` and package workflow files. Run package tests from `working-directory: nucxplore`.
- `.github/workflows/publish-pypi.yml`: package-tag-triggered release workflow for wheel/sdist build and PyPI publishing from `nucxplore/` only.
- `nucxplore/docs/developer-guide.md`: document exact release triggers and secrets/trusted publishing setup.

Recommended release workflow shape:
- Trigger PyPI publication only on package tags matching `nucxplore-v*`.
- Use `PyO3/maturin-action` or `maturin` directly to build wheels from `working-directory: nucxplore`.
- Build sdist from `nucxplore/`.
- Upload artifacts for inspection.
- Publish to PyPI with trusted publishing (`id-token: write`); do not require long-lived `PYPI_API_TOKEN` secrets.
- Do not run Docker builds or Docker pushes in this workflow.
- Do not include `nucxplore-pipeline/**` in package artifacts.

Validation:
- `gh workflow view publish-pypi.yml` after push, or GitHub Actions dry review if `gh` is available.
- Locally from `nucxplore/`: `maturin build --release --out dist --interpreter python`.
- Inspect wheel contents with `python -m zipfile -l dist/nucxplore-*.whl` or equivalent safe listing to confirm no pipeline files are included.

Risk:
- Tag strategy must avoid accidental package release when only pipeline changes occur. Use package-specific tags such as `nucxplore-v0.2.0`.

### Milestone 6 — No Pipeline GitHub Actions

Goal: Keep GitHub Actions limited to package validation and PyPI release automation for this consolidation task.

Edits:
- Do not add `.github/workflows/pipeline-ci.yml` in this task.
- `nucxplore-pipeline/docs/developer-guide.md`: document local pipeline validation commands using the `nextflow` micromamba environment.
- Root and pipeline docs: state that GitHub Actions are package-only unless a future task adds pipeline validation.

Validation:
- Confirm `.github/workflows/` contains no pipeline validation workflow.
- Confirm no workflow steps build/push Docker images or run pipeline publishing tasks.

Risk:
- Pipeline regressions will not be caught by GitHub Actions until a future pipeline validation workflow is explicitly added; local validation remains documented.

### Milestone 7 — End-To-End Documentation Consistency

Goal: Ensure all docs agree on the combined repository model.

Edits:
- Search and update stale phrases: `separate repository`, `standalone repository`, `sibling checkout`, `future separate`, and old repository names where they imply split ownership.
- Keep historical changelog entries unchanged except new top entries.
- Update plans only if they are active or directly misleading; do not rewrite old completed plans unless requested.

Validation:
- `rg "separate repository|standalone repository|sibling checkout|future separate" README.md nucxplore nucxplore-pipeline plans -g '*.md'` and review remaining hits.
- Manual check that build commands say `cd nucxplore` or use `working-directory: nucxplore`.
- Manual check that hosted Nextflow commands say `nextflow run <org>/<repo> -r <tag>`, root-local commands say `nextflow run .`, and developer subdirectory commands say `nextflow run ./nucxplore-pipeline` from root or `nextflow run .` from inside `nucxplore-pipeline/`.

Risk:
- Old completed plans and changelog entries may intentionally describe previous decisions. Do not rewrite history unless user wants a clean public history.

## Implementation Notes

- Recommended final repo layout:

```text
<repo>/
  README.md
  AGENTS.md
  .github/workflows/
    package-ci.yml
    publish-pypi.yml
  nucxplore/
    pyproject.toml
    Cargo.toml
    src/
    python/
    tests/
    docs/
  nucxplore-pipeline/
    main.nf
    nextflow.config
    conf/
    bin/
    tests/
    docs/
  plans/
```

- Recommended root `nextflow.config` facade:

```groovy
manifest {
  name = 'nucxplore'
  description = 'NucXplore package and cell-type prediction pipeline'
  mainScript = 'nucxplore-pipeline/main.nf'
}

includeConfig 'nucxplore-pipeline/nextflow.config'
```

- Do not add root workflow logic unless validation proves `manifest.mainScript` cannot support the hosted monorepo layout. If a fallback is needed, prefer a tiny root `main.nf` wrapper only after testing; do not copy pipeline processes to the root.

- Recommended package release command remains:

```bash
micromamba activate rustenv
cd nucxplore
maturin build --release --out dist --interpreter python
```

- Recommended PyPI install command remains:

```bash
python -m pip install nucxplore
```

- Recommended root-relative pipeline run pattern:

```bash
nextflow run <org>/<repo> \
  -r <pipeline-release-tag> \
  -profile docker \
  --slide_root /data/slides \
  --outdir /data/results \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag>
```

- Recommended local checkout root-run pattern:

```bash
micromamba activate nextflow
nextflow run . \
  -profile docker \
  --slide_root /data/slides \
  --outdir /data/results \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag>
```

- Recommended explicit local subdirectory pipeline run pattern for developers:

```bash
micromamba activate nextflow
nextflow run ./nucxplore-pipeline \
  -profile docker \
  --slide_root /data/slides \
  --outdir /data/results \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag>
```

- Recommended subdirectory-local pipeline run pattern:

```bash
micromamba activate nextflow
cd nucxplore-pipeline
nextflow run . \
  -profile docker \
  --slide_root /data/slides \
  --outdir /data/results \
  --crop_filter_container docker.io/<owner>/nucxplore-crop-filter:<tag> \
  --seg_container docker.io/<owner>/nucxplore-rgci-seg:<tag> \
  --container docker.io/<owner>/nucxplore-cell-type-prediction:<tag>
```

- If the pipeline directory is renamed to `pipeline/`, update all docs, tests, plans, and any CI `working-directory` paths in the same milestone. Avoid renaming unless the benefit outweighs broken existing references.
- If root-level GitHub tags are shared by both library and pipeline, use package-specific release tags for PyPI, for example `nucxplore-v0.2.0`, to avoid publishing wheels for pipeline-only releases.
- If GitHub trusted publishing is used, configure PyPI project `nucxplore` with repository, workflow filename, environment, and tag/ref constraints before enabling automatic publication.
- Keep model artifacts and HEIP checkpoint out of PyPI wheels. Pipeline containers or user-provided paths remain responsible for them.
- Local validation should activate `rustenv` for `cargo`, `maturin`, and package Python checks, and `nextflow` for `nextflow run`, stub checks, and pipeline Python checks if that environment owns the pipeline test dependencies.

## Validation Plan

- Unit tests:
  - In `rustenv`, from `nucxplore/`: `cargo test --tests`.
  - In `nextflow`, from `nucxplore-pipeline/`: `python -m pytest tests/test_pipeline_contract.py tests/test_cell_type_predict.py`.
- Integration tests:
  - In `nextflow`, from `nucxplore-pipeline/`: `bash tests/run_stub_pipeline_checks.sh`.
  - In `nextflow`, from repo root: run at least one documented `nextflow run . ... -stub-run` command to validate the hosted-run facade.
  - In `nextflow`, from repo root: run at least one documented `nextflow run ./nucxplore-pipeline ... -stub-run` command if docs keep explicit developer subdirectory invocation.
- CLI/manual checks:
  - In `rustenv`, from `nucxplore/`: `python -m py_compile python/nucxplore/batch.py scripts/batch_extract_and_crop.py`.
  - In `rustenv`, from `nucxplore/`: `maturin build --release --out dist --interpreter python`.
  - Inspect wheel file list and confirm pipeline files are absent.
- Documentation checks:
  - Search for stale split-repo language and review intentional historical mentions.
  - Confirm README/doc links exist.
  - Confirm parameter examples match `nextflow.config` and `params.example.yaml`.
- Performance checks:
  - N/A; no feature extraction performance behavior should change.
- Regression checks:
  - Confirm `pip install nucxplore` remains the documented library install path.
  - Confirm public pipeline usage is `nextflow run <org>/<repo> -r <tag>` and does not require cloning for normal users.
  - Confirm pipeline commands still require runtime containers and do not depend on an editable local package checkout.

## Recovery / Rollback

- Safe retry: documentation and CI edits can be reapplied independently because package and pipeline source behavior should remain unchanged.
- Rollback: revert root docs/workflows first, then subproject docs. No data migration should be involved.
- Files to inspect if package publishing fails: `.github/workflows/publish-pypi.yml`, `nucxplore/pyproject.toml`, `nucxplore/Cargo.toml`, PyPI trusted publishing settings, repository tag/ref.
- Files to inspect if wheel includes pipeline files: `nucxplore/pyproject.toml`, `MANIFEST.in` if added later, maturin build logs, workflow `working-directory`.
- Files to inspect if hosted or root-relative Nextflow run fails: root `nextflow.config`, `nucxplore-pipeline/nextflow.config`, `nucxplore-pipeline/conf/docker.config`, any relative `includeConfig`, `nucxplore-pipeline/main.nf`, `bin/` command discovery, test script assumptions about current working directory.

## Resolved Milestone 1 Contract

1. Public repository/project display name: `NucXplore`.
2. Target pipeline directory: rename `nucxplore-cell-type-prediction/` to `nucxplore-pipeline/`.
3. Hosted Nextflow UX: normal users run `nextflow run <org>/<repo> -r <tag>` through a root `manifest.mainScript` facade; subdirectory commands are for local development/source review.
4. GitHub Actions scope: package only; no pipeline validation workflow in this task.
5. PyPI trigger: package-specific tags matching `nucxplore-v*`.
6. PyPI authentication: trusted publishing via GitHub OIDC.
7. Docker publishing: manual/external; not part of package release workflow.
8. Feature/prediction Docker `nucxplore` install: dual mode, PyPI for production images and local source checkout for development images.
9. Changelogs: root plus subproject changelogs.
10. Historical plans/changelogs: keep completed history intact; update current public docs only.
11. Wheel targets: Linux, macOS, and Windows for supported Python versions.

## Completion Summary

Fill when complete. All milestones implemented.

- DockerHub image names are external artifacts; not renamed
- The `rustenv` micromamba env's default `python` is 2.7; all Python validation used `python3`
- Pipeline Python test dependencies were added to the `nextflow` env during validation

Changed:
- Renamed `nucxplore-cell-type-prediction/` to `nucxplore-pipeline/`
- Created root `README.md`, `nextflow.config`, `AGENTS.md`, `.gitignore`, `.dockerignore`, `CHANGELOG.md`
- Updated `nucxplore/` docs (README, user-guide, developer-guide, CHANGELOG) for monorepo layout
- Updated `nucxplore-pipeline/` docs (README, user-guide, developer-guide, params.example.yaml, CHANGELOG) for monorepo layout
- Created `.github/workflows/package-ci.yml` and `.github/workflows/publish-pypi.yml`
- Updated `nucxplore/docs/developer-guide.md` with release workflow docs
- Updated root, pipeline README, and developer guide with CI scope packaging-only statements
- End-to-end documentation consistency pass completed

Validated:
- 115 Rust tests pass
- 10/10 Nextflow stub scenarios pass
- 4/4 Python pipeline tests pass
- `nextflow run ./nucxplore-pipeline -stub-run` from repo root → exit 0
- `nextflow run . -stub-run` (root facade) → exit 0
- `maturin build --release` succeeds; wheel inspected, no pipeline files
- Both workflow YAML files valid; no Docker steps present
- No stale split-repo language in active docs
- All command patterns verified: hosted, root, subdirectory, build

Changed:
- 

Validated:
- 

New dependencies added:
- None

Remaining:
- Milestone 1 complete; continue with Milestone 2 implementation when requested.

Lessons:
- 

## CHANGELOG.md Entry

Draft final changelog entry after implementation.

consolidate package and pipeline into single GitHub repository
reason: single source-of-truth checkout; package-only PyPI publishing via nucxplore-v* tags; root nextflow.config enables nextflow run <org>/<repo> -r <tag>; pipeline validation is local
