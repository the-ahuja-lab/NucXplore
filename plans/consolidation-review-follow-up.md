# EXECPLAN

## Task

Resolve review findings that remain after consolidating the NucXplore library and Nextflow pipeline into one repository.

## Goal

The monorepo matches `plans/consolidate-library-pipeline-repo.md`: package-only PyPI release automation is accurate, hosted/root/subdirectory pipeline run docs are consistent, Docker image behavior is reproducible, and current pipeline/library regressions are covered by narrow tests.

## Scope

- Modules: root workflows and metadata, `nucxplore-pipeline/` Nextflow workflow, pipeline Dockerfiles and CLI scripts, `nucxplore/` Python/Rust package boundary.
- Files likely involved: `.github/workflows/publish-pypi.yml`, `nucxplore/docs/developer-guide.md`, `nucxplore-pipeline/README.md`, `nucxplore-pipeline/docs/user-guide.md`, `nucxplore-pipeline/docs/developer-guide.md`, `nucxplore-pipeline/nextflow.config`, `nucxplore-pipeline/params.example.yaml`, `nucxplore-pipeline/Dockerfile*`, `nucxplore-pipeline/main.nf`, `nucxplore-pipeline/bin/*.py`, `nucxplore/pyproject.toml`, `nucxplore/python/nucxplore/__init__.py`, `nucxplore/src/io/mat.rs`, targeted tests.
- Downstream impact: PyPI package installers, GitHub release maintainers, Docker image maintainers, Nextflow pipeline users.
- Out of scope: changing public package name, changing model artifacts, adding DockerHub publishing to package workflows, changing scientific feature semantics except to fix parser/import/output failures.

## Context

The consolidation plan is implemented structurally, but review found mismatches between the desired monorepo contract and current behavior. Root docs and `nextflow.config` exist; `nucxplore-pipeline/` exists; package-only workflows exist. Remaining work is corrective: align release matrix/docs, align container placeholders and install mode, fix Docker build and required-output failures, and fix Python/Rust package import/parser issues.

Current behavior:
- `publish-pypi.yml` builds one wheel per OS using `--interpreter python` and has no `workflow_dispatch`.
- Package developer docs mention manual/TestPyPI dispatch.
- Pipeline docs show hosted, explicit subdirectory, and pipeline-directory examples, but not root-local `nextflow run .` in pipeline docs.
- Feature/prediction container placeholder differs between config and docs/examples.
- Feature/prediction Dockerfile always builds from local source despite docs describing production PyPI install.
- `Dockerfile.rgci-seg` copies `last.ckpt` into a missing directory.
- Nextflow outputs require optional/empty globs in feature/prediction stages.
- Crop/segmentation scripts can return success with no discovered inputs, then fail later as missing Nextflow outputs.
- `nucxplore` import loads optional NumPy-dependent batch code at top level.
- MAT v5 small data elements are parsed with the wrong total size.

Desired behavior:
- Release workflow and docs describe the same supported wheel set and manual trigger policy.
- Docs show hosted `nextflow run <org>/<repo>`, repo-root `nextflow run .`, explicit `nextflow run ./nucxplore-pipeline`, and subdirectory-local `nextflow run .` consistently where advertised.
- Dockerfile behavior matches docs: either production PyPI install is supported by build arg or docs state local-source build only.
- Pipeline errors fail early with clear messages and required outputs match enabled outputs.
- `pip install nucxplore` fresh import works for advertised APIs.
- MAT parser supports small data element tags used by MATLAB v5 files.

## Constraints

- Preserve package and pipeline public names.
- Keep package release automation package-only; do not build/push Docker images from PyPI workflows.
- Preserve existing pipeline stage parameters and stage names unless a change is required to fix broken behavior.
- Prefer narrow tests covering each regression.
- Do not hide real empty-input failures by producing fake data.

## Evidence

- User report: requested review of root codebase, Nextflow pipeline, Docker files, and `nucxplore` Rust library, then comparison with `consolidate-library-pipeline-repo.md`.
- Plan gap: `plans/consolidate-library-pipeline-repo.md` calls for Linux/macOS/Windows wheels for supported Python versions and accurate package-only release docs.
- Review findings: see this plan's Discovery Log.

## Progress

- [x] 2026-05-07T21:27Z — Created follow-up plan from review findings.
- [x] 2026-05-07T22:10Z — Milestone 1 complete: added workflow_dispatch, documented ABI3 coverage.
- [x] 2026-05-07T22:20Z — Milestone 2 complete: root facade docs, container placeholder alignment, dual-mode Dockerfile.
- [x] 2026-05-07T22:45Z — Milestone 3 complete: empty-input nonzero exits, optional outputs, Docker build fix, 3 new tests.
- [x] 2026-05-07T23:00Z — Milestone 4 complete: MAT small-element fix + 2 tests, lazy batch import, removed _core.pyi orphan.

## Discovery Log

- Finding: `publish-pypi.yml` does not build across supported Python versions.
  Evidence: `.github/workflows/publish-pypi.yml` only matrices `os` and passes `--interpreter python`.
  Impact: release artifacts may not match the documented platform/Python support contract.
  Resolution: ABI3 wheel (abi3-py38) covers all supported Python 3.8+ versions. No version matrix needed; added ABI3 explanation to docs.
- Finding: package docs mention manual dispatch/TestPyPI but publish workflow only triggers on `nucxplore-v*` tags.
  Evidence: `nucxplore/docs/developer-guide.md` release section versus `.github/workflows/publish-pypi.yml` triggers.
  Impact: maintainers following docs cannot run the documented workflow.
  Resolution: added workflow_dispatch to publish-pypi.yml.
- Finding: pipeline docs omit root-local facade example in some places.
  Evidence: `nucxplore-pipeline/README.md` and `docs/user-guide.md` emphasize `./nucxplore-pipeline` from repo root.
  Impact: the root `nextflow.config` facade is under-documented for local checkout users.
- Finding: feature/prediction image placeholder is inconsistent.
  Evidence: `nucxplore-pipeline/nextflow.config` uses `docker.io/<owner>/<image>:<tag>` while docs/examples use `nucxplore-cell-type-prediction`.
  Impact: validation and examples disagree on the required parameter value.
- Finding: feature/prediction Dockerfile always builds `nucxplore` from local source.
  Evidence: `nucxplore-pipeline/Dockerfile` copies `nucxplore/` and runs `maturin build`.
  Impact: docs describing production PyPI install are inaccurate unless build args are added.
- Finding: RGCI/HEIP Docker build copies checkpoint into a missing directory.
  Evidence: `nucxplore-pipeline/Dockerfile.rgci-seg` copies to `/opt/heip/models/last.ckpt` without creating `/opt/heip/models`.
  Impact: Docker build can fail.
- Finding: feature and prediction processes require outputs that can be validly absent.
  Evidence: `main.nf` requires `nuclei` even when `save_crops=false`, and requires `predictions/**` even when all CSVs are skipped empty.
  Impact: successful scripts can fail during Nextflow output collection.
- Finding: crop/segmentation scripts accept empty input discovery as success.
  Evidence: `crop_and_filter.py` and `rgci_seg_to_mat.py` return zero failures when no slides/crop folders are found.
  Impact: users get delayed missing-output failures instead of clear invalid-input errors.
- Finding: top-level `nucxplore` import depends on optional NumPy via `.batch` import.
  Evidence: `nucxplore/python/nucxplore/__init__.py` imports `.batch`; `pyproject.toml` leaves `dependencies = []`.
  Impact: fresh installs can fail at `import nucxplore` despite advertised file API.
- Finding: MAT parser mis-sizes MATLAB v5 small data elements.
  Evidence: `nucxplore/src/io/mat.rs` computes small-element total size as `4 + align8(payload_size)` instead of fixed 8 bytes.
  Impact: MAT files with packed short names/scalars can desynchronize parsing.

## Decision Log

- Decision: Use Docker multi-stage targets (`runtime-pypi` / `runtime-source`) for dual install mode.
  Reason: clean separation avoids building Rust toolchain in production; `runtime-source` is last target so it remains the default for backward compatibility.
  Date: 2026-05-07
- Decision: Use `__getattr__` lazy-load for batch module instead of making NumPy a required dependency.
  Reason: preserves advertised dependency-light file API; bare `import nucxplore` works without numpy; batch attrs load on first access.
  Date: 2026-05-07
- Decision: Remove orphaned `nuqr_featurizer/_core.pyi` instead of adding forwarding module.
  Reason: no runtime code imports `nuqr_featurizer._core`; stub was misleading.
  Date: 2026-05-07
- Decision: Keep single ABI3 wheel per OS instead of adding Python-version matrix.
  Reason: Cargo.toml uses `abi3-py38`; one wheel per OS covers all supported Python versions (3.8–3.12). Adding a version matrix would duplicate identical wheels.
  Date: 2026-05-07
- Decision: Treat remaining work as a follow-up corrective ExecPlan, not as edits in the review pass.
  Reason: user requested review comments and a plan; review mode should not implement fixes.
  Date: 2026-05-07

## Milestones

### Milestone 1 — Release Contract

Goal: Make package release workflow and docs consistent.

Edits:
- `.github/workflows/publish-pypi.yml`: either add Python-version wheel matrix or document why one ABI3 wheel per OS is sufficient; add `workflow_dispatch` only if docs keep manual/TestPyPI workflow guidance.
- `nucxplore/docs/developer-guide.md`: align release trigger, TestPyPI, and supported wheel text with the workflow.

Validation:
- `gh workflow view publish-pypi.yml` after push, or YAML review if `gh` is unavailable.
- From `nucxplore/`: `maturin build --release --out dist --interpreter python`.

Risk: widening the matrix can increase release time and artifact duplication; keep ABI3 behavior explicit.

### Milestone 2 — Pipeline Docs And Containers

Goal: Make pipeline run examples and Docker install behavior match current/desired runtime model.

Edits:
- `nucxplore-pipeline/README.md`: add repo-root `nextflow run .` example and keep hosted/subdirectory examples distinct.
- `nucxplore-pipeline/docs/user-guide.md`: add root-local facade example and align container placeholders.
- `nucxplore-pipeline/docs/developer-guide.md`: either document local-source Docker build or add build-arg workflow for production PyPI install.
- `nucxplore-pipeline/nextflow.config` and `params.example.yaml`: use one feature/prediction container placeholder consistently.
- `nucxplore-pipeline/Dockerfile`: if production PyPI install is desired, add build args for PyPI package version versus local source build.

Validation:
- Manual docs search for stale or contradictory run examples.
- From repo root: `nextflow run . -stub-run --from_stage features --to_stage prediction` with test-safe inputs.
- From repo root: `nextflow run ./nucxplore-pipeline -stub-run --from_stage features --to_stage prediction`.

Risk: Docker install mode can affect reproducibility; pin package versions/tags for production builds.

### Milestone 3 — Pipeline Runtime Failures

Goal: Fail early on invalid empty inputs and make Nextflow outputs match valid script behavior.

Edits:
- `nucxplore-pipeline/Dockerfile.rgci-seg`: create `/opt/heip/models` before copying `last.ckpt`.
- `nucxplore-pipeline/main.nf`: make optional outputs optional or ensure scripts always create declared directories/files when successful.
- `nucxplore-pipeline/bin/crop_and_filter.py`: create output/log parent directories and return nonzero for no discovered slides.
- `nucxplore-pipeline/bin/rgci_seg_to_mat.py`: create output/log parent directories and return nonzero for no crop folders.
- `nucxplore-pipeline/tests/*`: add narrow tests for empty input behavior and output contracts.

Validation:
- From `nucxplore-pipeline/`: `python -m pytest tests/test_pipeline_contract.py tests/test_cell_type_predict.py`.
- From `nucxplore-pipeline/`: `bash tests/run_stub_pipeline_checks.sh`.
- Docker build smoke for `Dockerfile.rgci-seg` when HEIP assets are present.

Risk: changing empty-input behavior can break callers relying on no-op success; treat empty stage input as invalid pipeline input.

### Milestone 4 — Package Import And MAT Parser

Goal: Keep advertised package APIs importable and parse MATLAB v5 small data elements correctly.

Edits:
- `nucxplore/python/nucxplore/__init__.py` and/or `nucxplore/pyproject.toml`: lazy-load batch APIs or make NumPy a required dependency.
- `nucxplore/docs/user-guide.md`: keep dependency-light file API claim only if import no longer requires NumPy.
- `nucxplore/src/io/mat.rs`: parse small data elements as fixed 8-byte tags with payload in bytes `4..4+size`.
- `nucxplore/tests/*`: add a MAT small-data-element fixture/test.
- `nucxplore/python/nuqr_featurizer/*`: either add a runtime `_core` forwarding module or remove misleading `_core.pyi` if compatibility does not promise `nuqr_featurizer._core`.

Validation:
- From `nucxplore/`: `python -m py_compile python/nucxplore/batch.py scripts/batch_extract_and_crop.py`.
- From `nucxplore/`: `cargo test --tests`.
- Fresh-env smoke: `python -c "import nucxplore; print(nucxplore.__version__)"` with only declared dependencies installed.

Risk: lazy imports can affect `__all__`/type checker expectations; keep stubs aligned with runtime exports.

## Implementation Notes

- `main.nf` outputs to revisit: `EXTRACT_FEATURES` `path 'nuclei'`, `PREDICT_CELL_TYPES` `path 'predictions/**'`.
- `cell_type_predict.py` succeeds when all discovered CSVs are empty; either Nextflow output glob must be optional or script should write a sentinel/report under `predictions/`.
- MATLAB v5 small data elements are exactly 8 bytes total; do not align their embedded payload beyond the fixed tag.

## Validation Plan

- Unit tests: MAT parser small element test, empty-input CLI tests.
- Integration tests: pipeline contract pytest and stub pipeline script.
- CLI/manual checks: root and subdirectory Nextflow stub commands.
- Regression checks: fresh package import with declared dependencies only.

## Recovery / Rollback

- Safe retry: each milestone is independent and can be reverted by file group.
- Rollback: revert workflow/doc changes separately from runtime parser/pipeline fixes.
- Files to inspect if validation fails: root `nextflow.config`, `nucxplore-pipeline/nextflow.config`, `nucxplore-pipeline/main.nf`, `.github/workflows/publish-pypi.yml`, `nucxplore/src/io/mat.rs`, package stubs.

## Completion Summary

Changed:
- `.github/workflows/publish-pypi.yml` — added workflow_dispatch trigger
- `nucxplore/docs/developer-guide.md` — documented ABI3 coverage, manual dispatch
- `nucxplore-pipeline/README.md` — added root facade `nextflow run .` example
- `nucxplore-pipeline/docs/user-guide.md` — added root facade example
- `nucxplore-pipeline/docs/developer-guide.md` — documented dual Docker install mode
- `nucxplore-pipeline/nextflow.config` — aligned container placeholder
- `nucxplore-pipeline/params.example.yaml` — (container already consistent, no change needed)
- `nucxplore-pipeline/main.nf` — aligned validation placeholder, made nuclei/predictions/** optional
- `nucxplore-pipeline/Dockerfile` — dual-mode multi-stage (runtime-source default, runtime-pypi)
- `nucxplore-pipeline/Dockerfile.rgci-seg` — added `mkdir -p /opt/heip/models`
- `nucxplore-pipeline/bin/crop_and_filter.py` — creates output_root early, returns nonzero for empty input
- `nucxplore-pipeline/bin/rgci_seg_to_mat.py` — validates folders before model load, returns nonzero for empty input
- `nucxplore-pipeline/tests/test_pipeline_contract.py` — 3 new empty-input tests
- `nucxplore/python/nucxplore/__init__.py` — lazy-load batch imports via __getattr__
- `nucxplore/src/io/mat.rs` — fixed small-element total_size (8), added 2 small-element tests
- `nucxplore/python/nuqr_featurizer/_core.pyi` — removed orphaned stub

Validated:
- `pytest tests/test_pipeline_contract.py tests/test_cell_type_predict.py` — 7 passed
- `bash tests/run_stub_pipeline_checks.sh` — all checks passed
- `nextflow run . -stub-run` — root facade works
- `nextflow run ./nucxplore-pipeline -stub-run` — subdirectory works
- `cargo test --tests` — 117 passed (incl. 2 new small-element tests)
- `python3 -m py_compile` — batch.py, batch_extract_and_crop.py, __init__.py all OK
- `import nucxplore` smoke — works without numpy; batch attrs lazy-load on access

New dependencies added:
- None

Remaining:
- None (all 4 milestones complete)

Lessons:
- ABI3 wheels make Python-version matrices unnecessary for PyO3 packages
- Docker multi-stage targets provide clean dual-mode builds without build-arg conditionals
- Python __getattr__ on modules is a clean pattern for optional-dependency lazy loading

## CHANGELOG.md Entry

Draft final changelog entry here before completion.

fix consolidation follow-up gaps
align release workflow/docs, pipeline Docker/output contracts, and package parser/import behavior
Reason: complete monorepo consolidation contract after review
