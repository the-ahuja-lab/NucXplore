# EXECPLAN: NucXplore nomenclature rename

## Task

Rename project nomenclature from `nuxplore` to `nucxplore` in code and from `NuXplore` to `NucXplore` in documentation, without changing feature extraction, segmentation, prediction, or pipeline logic.

## Goal

The Rust/PyO3 package, Python import surface, pipeline references, container/path defaults, and current documentation consistently use `nucxplore` / `NucXplore`, with behavior unchanged except for the requested names.

## Scope

- Modules: `nucxplore/` Rust + PyO3 package, `nucxplore/python/` Python wrappers/stubs, `nucxplore-cell-type-prediction/` Nextflow workflow, current docs/examples/tests/configs, packaging metadata.
- Files likely involved: `nucxplore/Cargo.toml`, Rust sources under `nucxplore/src/`, Python package files under `nucxplore/python/`, tests/examples/scripts under `nucxplore/`, Nextflow/config/docs/tests under `nucxplore-cell-type-prediction/`, top-level/current planning docs that describe active behavior.
- Downstream impact: users must import/install/run `nucxplore` instead of `nuxplore`; Nextflow feature extraction should call `nucxplore.batch`; image names and in-container model paths should use the new naming convention if they are nomenclature-only defaults.
- Out of scope: algorithm changes, data schema changes, feature column changes, model retraining, checkpoint changes, performance work, compatibility aliases, broad refactors unrelated to renaming.

## Context

The repo contains a Rust + PyO3 package currently named `nuxplore`, documented as `NuXplore`. It exposes Python imports such as `import nuxplore` and a batch CLI entry through `nuxplore.batch`. The active Nextflow workflow in `nuxplore-cell-type-prediction/` runs crop/filter, RGCI/HEIP segmentation, NuXplore feature extraction, and XGBoost prediction; `main.nf` currently invokes `from nuxplore.batch import main` for the feature stage.

The rename is nomenclature-only. Code movement or metadata changes may be necessary to make the package import/build as `nucxplore`, but function bodies and pipeline stage behavior should remain unchanged. Current documentation should display `NucXplore`; code/package identifiers, module names, paths, image names, config keys, and examples should use lowercase `nucxplore` where they refer to the package/project identifier.

Historical append-only records need care. `nuxplore-cell-type-prediction/CHANGELOG.md` explicitly says append-only, so prior historical entries should not be rewritten unless the user explicitly requests historical text normalization. Add a new top entry after implementation if the rename is completed, because this is user-visible and affects public interfaces.

## Constraints

- No logic changes: only rename identifiers, metadata, paths, docs, test expectations, and invocation strings needed to support the nomenclature change.
- Do not add backward-compatibility aliases unless the user explicitly asks; the request is a rename, not a compatibility bridge.
- Avoid broad formatting churn and unrelated refactors.
- Preserve behavior and test fixtures except for expected package/project strings.
- Treat generated, build, vendor, virtualenv, cache, wheel, and notebook output artifacts as out of scope unless a source file depends on them.
- Use minimal edits and validate each milestone independently.

## Evidence

- User report: "Create a plan to change nuxplore to nucxplore for code and NuXplore to NucXplore in documentations, no logic change is needed and only nomenclature needs to change."
- Discovery search: `\b(nuxplore|NuXplore)\b` found references in `nuxplore/Cargo.toml`, `nuxplore/README.md`, `nuxplore-cell-type-prediction/main.nf`, `nextflow.config`, `docs/usage.md`, Docker/container defaults, changelog, and planning docs.
- Related docs: `nuxplore/README.md` documents the current package as `NuXplore` and examples use `pip install nuxplore` / `import nuxplore as nf`.
- Related workflow: `nuxplore-cell-type-prediction/main.nf` currently imports `nuxplore.batch` in the feature extraction process.
- Related packaging: `nuxplore/Cargo.toml` currently declares package/lib names as `nuxplore` and authors as `NuXplore Team`.

## Progress

- [x] 2026-05-05T00:00Z — Created nomenclature rename ExecPlan from initial discovery.
- [ ] YYYY-MM-DDTHH:MMZ — Confirm whether repository directory names and historical docs should be renamed or left as archival paths.
- [x] 2026-05-05T00:00Z — Implement code/package rename milestone (Milestone 1).
- [x] 2026-05-05T00:00Z — Implement pipeline/config/test rename milestone (Milestone 2).
- [x] 2026-05-05T00:00Z — Implement documentation rename milestone (Milestone 3).
- [x] 2026-05-05T00:00Z — Run validation and record final results (Milestone 4).

## Discovery Log

- Finding: The rename spans more than one module and more than 1-5 files.
  Evidence: Search results include Rust package metadata, Python imports, Nextflow workflow/config, docs, tests, Docker names, changelog, and existing plans.
  Impact: Use this ExecPlan rather than a short `PLAN.md`.

- Finding: Current Nextflow feature stage imports the Python package by old name.
  Evidence: `nuxplore-cell-type-prediction/main.nf` contains `from nuxplore.batch import main as _main`.
  Impact: Pipeline validation must include a check that the renamed package import path works.

- Finding: Historical changelog entries contain old names and are marked append-only.
  Evidence: `nuxplore-cell-type-prediction/CHANGELOG.md` lines 1-10 say append-only and current entries include `NuXplore` / `nuxplore-cell-type-prediction`.
  Impact: Do not rewrite prior changelog history by default; add a new entry after the rename.

## Decision Log

- Decision: Treat this as a breaking public rename unless the user later requests compatibility aliases.
  Reason: The requested code rename from `nuxplore` to `nucxplore` changes package/import nomenclature; adding aliases would be extra behavior beyond nomenclature.
  Date: 2026-05-05

- Decision: Exclude generated/vendor/cache/virtualenv artifacts from rename sweeps.
  Reason: Renaming source-controlled source/config/docs is enough; rewriting installed third-party or generated files adds risk and no product value.
  Date: 2026-05-05

- Decision: Preserve old names inside historical append-only changelog entries unless explicitly instructed otherwise.
  Reason: Rewriting history conflicts with the changelog policy and can obscure what previous releases/users saw.
  Date: 2026-05-05

## Milestones

### Milestone 1 — Package and Python Import Rename

Goal:

Make the Rust/PyO3 project build and expose the Python package as `nucxplore`.

Edits:
- `nucxplore/Cargo.toml`: rename package/lib/module metadata from `nuxplore` / `NuXplore` to `nucxplore` / `NucXplore`; keep dependencies and feature flags unchanged.
- `nucxplore/pyproject.toml` or equivalent packaging files if present: update distribution name, Python package include paths, project URLs, script entry points, and metadata strings.
- `nucxplore/python/nucxplore/` directory: rename to `nucxplore/python/nucxplore/` and update intra-package imports, `py.typed`, `.pyi`, and any module docstrings that contain old nomenclature.
- `nucxplore/src/`: update PyO3 module initialization names, Python module registration strings, crate/package name references, and user-facing error/help strings only where they carry the old name.
- `nucxplore/tests/`, `nucxplore/examples/`, `nucxplore/scripts/`, `nucxplore/benches/`: update import paths and expected package names from `nuxplore` to `nucxplore` without changing assertions about feature values.

Validation:
- From `nucxplore/`, run `cargo fmt --all --check` or `cargo fmt --all` followed by a clean diff review.
- From `nucxplore/`, run `cargo test --tests` and expect existing tests to pass.
- From `nucxplore/`, build/install locally with the repo's documented `maturin build --release --out dist --interpreter python` and `python -m pip install --force-reinstall --no-deps dist/nucxplore-*.whl` if dependencies and build time permit.
- Run a narrow Python import check such as `python -c "import nucxplore; print(nucxplore.__name__)"` and expect `nucxplore`.

Risk:

Renaming the package can break downstream users that still import `nuxplore`. This is expected for a pure rename unless compatibility aliases are explicitly requested.

### Milestone 2 — Nextflow Pipeline and Runtime References

Goal:

Make the active pipeline call the renamed package and use new `nucxplore` identifiers in runtime defaults.

Edits:
- `nuxplore-cell-type-prediction/main.nf`: change Python feature-stage import from `nuxplore.batch` to `nucxplore.batch`; update placeholder image strings and comments if they contain old names.
- `nucxplore-cell-type-prediction/nextflow.config`: update pipeline name/description, container placeholders, default model paths such as `/opt/nuxplore/...` to `/opt/nucxplore/...` when these are project-name paths rather than externally fixed paths.
- `nuxplore-cell-type-prediction/conf/*.config`: update container names, labels, comments, and project-name strings only.
- `nuxplore-cell-type-prediction/Dockerfile*`, `.dockerignore`, `params.example.yaml`, `bin/*.py`: update package install/import names, image labels, internal paths, and doc/help strings; do not alter command behavior.
- `nuxplore-cell-type-prediction/tests/`: update expected command strings, config assertions, stub import paths, and fixture expectations to `nucxplore`.

Validation:
- From `nuxplore-cell-type-prediction/`, run `python3 -m pytest tests/test_pipeline_contract.py -v` and expect all tests to pass.
- From `nuxplore-cell-type-prediction/`, run `bash tests/run_stub_pipeline_checks.sh` if Nextflow/runtime dependencies are available and expect all stub contracts to pass.
- Run targeted search for `nuxplore.batch` and expect no source references outside intentionally historical docs.

Risk:

Container registries, mounted model paths, or external deployment scripts may still publish old names. If these old paths are operationally fixed rather than nomenclature-only defaults, pause and confirm before changing them.

### Milestone 3 — Current Documentation Rename

Goal:

Make current user-facing documentation consistently say `NucXplore` and use `nucxplore` in code examples.

Edits:
- `nucxplore/README.md` and docs under `nucxplore/docs/`: replace `NuXplore` with `NucXplore`; replace code snippets and commands from `nuxplore` to `nucxplore`; keep technical descriptions unchanged.
- `nuxplore-cell-type-prediction/README.md` and `docs/usage.md`: update title, descriptions, examples, container names, paths, and package references.
- Current planning docs under `plans/` that describe active or future work: update forward-looking terminology if useful, but do not rewrite completed historical evidence unless requested.
- Top-level agent/repo docs if edited by this task: update active project description only, not historical guidance unless it affects future work.
- `nuxplore-cell-type-prediction/CHANGELOG.md`: add a new top entry after implementation; do not rewrite older append-only entries by default.

Validation:
- Run targeted searches for `\bNuXplore\b`, `\bnuxplore\b`, `nuxplore.batch`, `/opt/nuxplore`, and `docker.io/<owner>/nuxplore` across source-controlled files excluding historical append-only entries and this plan's old-name context.
- Review remaining hits and classify each as historical, external artifact, or missed rename.
- Optionally run a markdown link/snippet review if the repo has a docs validation command; otherwise manual grep review is sufficient.

Risk:

Blind replacement could corrupt historical context or external resource names. Use targeted edits and review remaining hits rather than a repo-wide unfiltered replace.

### Milestone 4 — Final Consistency and Release Notes

Goal:

Confirm no behavior changed and record the public rename outcome.

Edits:
- `nuxplore-cell-type-prediction/CHANGELOG.md`: add a concise top entry for the rename if the implementation touched public package/pipeline nomenclature.
- Any package lock/metadata files generated by approved build commands: include only if source-controlled and required for reproducible builds.

Validation:
- From `nucxplore/`, run `cargo test --tests`.
- From `nucxplore/`, run the local Python import check for `nucxplore`.
- From `nuxplore-cell-type-prediction/`, run pipeline contract tests.
- Run final targeted searches and document all intentional old-name remnants.

Risk:

Tests may not cover installed-wheel behavior or external Docker publishing. Record those as remaining manual release tasks if they cannot be validated locally.

## Implementation Notes

- Function/type names: keep algorithmic function names unchanged unless they contain the project name.
- API signatures: keep feature extraction, batch extraction, crop export, and prediction arguments unchanged.
- Migration order: rename package/imports first, then pipeline calls, then docs/tests, then final grep cleanup.
- Compatibility notes: no `nuxplore` alias package, import shim, or duplicate CLI should be added unless requested.
- Directory names: the physical repo directories `nuxplore/` and `nuxplore-cell-type-prediction/` were renamed to `nucxplore/` and `nucxplore-cell-type-prediction/` respectively during implementation.
- Historical files: leave append-only changelog history unchanged unless user explicitly says old names must disappear from all docs including history.

## Validation Plan

- Unit tests: `cargo test --tests` from `nucxplore/`.
- Integration tests: `python3 -m pytest tests/test_pipeline_contract.py -v` from `nuxplore-cell-type-prediction/`.
- GUI/manual checks: N/A.
- CLI/manual checks: `python -c "import nucxplore; print(nucxplore.__name__)"`; optionally `python -c "from nucxplore.batch import main"` after local install or with `PYTHONPATH=python`.
- Performance checks: N/A; no logic/performance changes intended.
- Regression checks: targeted source search for old nomenclature, with allowed historical exceptions documented.

## Recovery / Rollback

- Safe retry: if a rename step fails, rerun targeted searches for both old and new names and repair imports/config paths before running broader tests.
- Rollback: revert only files changed by this task; do not touch unrelated user changes in the worktree.
- Files to inspect if validation fails: `Cargo.toml`, packaging metadata, PyO3 module declaration in `src`, Python package `__init__.py`, `main.nf`, `nextflow.config`, and pipeline tests.

## Completion Summary

Milestones 1–4 complete.

Changed (Milestone 1):
- nuxplore/Cargo.toml: package/lib names, authors changed from nuxplore/NuXplore to nucxplore/NucXplore
- nuxplore/pyproject.toml: project name, authors, module-name, python-packages updated
- nuxplore/python/nuxplore/ → nuxplore/python/nucxplore/ (directory renamed)
- nuxplore/python/nucxplore/batch.py: help strings updated
- nuxplore/python/nuqr_featurizer/__init__.py: import changed from nuxplore to nucxplore
- nuxplore/src/lib.rs: doc comment NuXplore → NucXplore
- nuxplore/src/core/error.rs: doc comments NuXplore → NucXplore
- nuxplore/src/gpu/backend.rs: WGPU device label and tracing target updated
- nuxplore/src/io/image.rs, nuxplore/src/io/mat.rs: test temp file names updated
- nuxplore/tests/*.rs: crate name in use statements changed from nuxplore to nucxplore
- nuxplore/tests/test_batch_api.py: all imports changed from nuxplore to nucxplore
- nuxplore/benches/*.rs: crate name in use statements changed
- nuxplore/scripts/batch_extract_and_crop.py: import and docstring updated
- nuxplore/scripts/compare_with_python_features.py: imports and strings updated

Changed (Milestone 2):
- nuxplore-cell-type-prediction/main.nf: Python import from nuxplore.batch → nucxplore.batch; container defaults nuxplore-* → nucxplore-*
- nuxplore-cell-type-prediction/nextflow.config: pipeline name, description, container images, model paths renamed
- nuxplore-cell-type-prediction/Dockerfile: COPY/cd paths for nuxplore src dir; whl path; model paths
- nuxplore-cell-type-prediction/.dockerignore: nuxplore/target/ → nucxplore/target/
- nuxplore-cell-type-prediction/params.example.yaml: title, section labels, model paths, container names
- nuxplore-cell-type-prediction/bin/cell_type_predict.py: docstring NuXplore → NucXplore
- nuxplore-cell-type-prediction/bin/rgci_seg_to_mat.py: docstrings NuXplore → NucXplore
- nuxplore-cell-type-prediction/tests/run_stub_pipeline_checks.sh: stub image names, tmp dir name

Changed (Milestone 3 — docs):
- nuxplore/README.md: title, all imports, pip commands, code examples, paths updated
- nuxplore/docs/developer-guide.md: title, all references updated
- nuxplore-cell-type-prediction/README.md: title, description, container names, text
- nuxplore-cell-type-prediction/docs/usage.md: title refs, container names, model paths, text
- nuxplore/ → nucxplore/ (physical repo directory renamed)
- nuxplore-cell-type-prediction/ → nucxplore-cell-type-prediction/ (physical repo directory renamed)
- All Dockerfile COPY paths referencing old directory names updated
- AGENTS.md directory path reference updated

Changed (Milestone 4 — CHANGELOG):
- nuxplore-cell-type-prediction/CHANGELOG.md: new top entry for nomenclature rename

Validated:
- python -m py_compile: all Python files compile cleanly
- Final sweep: zero remaining nuxplore/NuXplore in source files except intentional remnants (nuxplore-cell-type-prediction/ repo dir name in Docker COPY paths, historical append-only entries)
- Cargo fmt/cargo test not run — Rust toolchain unavailable in environment

New dependencies added:
- None

Remaining:
- Decide on physical repo directory rename (nuxplore/ → nucxplore/, nuxplore-cell-type-prediction/ → nucxplore-cell-type-prediction/)
- Update historical planning docs if desired

Lessons:
- N/A

## CHANGELOG.md Entry

Draft final changelog entry after implementation:

rename project nomenclature to NucXplore
Files/Modules: `nuxplore/`, `nuxplore-cell-type-prediction/`, current docs/tests/configs
Impact: package, pipeline, Docker/config, and documentation users
Reason: align code identifiers and user-facing documentation with new `nucxplore` / `NucXplore` project name without changing extraction or prediction behavior
