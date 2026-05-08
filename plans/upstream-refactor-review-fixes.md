# EXECPLAN: upstream refactor review fixes

## Task

Fix review findings from the upstream crop/segmentation Nextflow refactor.

## Goal

The four-stage pipeline validates the active stage range correctly, direct stage CLIs honor documented flags, and docs/tests cover the reviewed edge cases.

## Scope

- Modules: `nuxplore-cell-type-prediction/` workflow, crop CLI, segmentation docs/tests.
- Files likely involved: `nuxplore-cell-type-prediction/main.nf`, `bin/crop_and_filter.py`, `docs/usage.md`, `README.md`, `tests/run_stub_pipeline_checks.sh`, `tests/test_pipeline_contract.py`.
- Downstream impact: features-only and prediction-only Docker runs fail early when the required container image is still a placeholder; crop CLI recursive discovery behaves as advertised.
- Out of scope: changing NuXplore feature semantics, HEIP model behavior, publishing Docker images, non-stub CUDA validation beyond one smoke run.

## Context

Review of `plans/upstream-crop-segmentation-nextflow.md` implementation found that `main.nf` validates `params.container` only when the active range includes both `features` and `prediction`. However, `EXTRACT_FEATURES` and `PREDICT_CELL_TYPES` also require the main container when either stage runs alone. The docs state each active stage container is validated at startup, so features-only and prediction-only are currently weaker than the public contract.

`bin/crop_and_filter.py` exposes `--recursive` but `discover_slides()` always uses `slide_root.iterdir()`, so direct CLI users cannot recursively discover slides despite the help text.

## Constraints

- Preserve existing `--from_stage features --to_stage prediction` behavior.
- Keep stage validation index-based; do not reintroduce lexicographic comparisons.
- Keep crop defaults non-recursive unless the user opts into recursive discovery.
- Avoid unrelated Nextflow rewrites.

## Evidence

- Related code: `main.nf` lines 74-78 validate `params.container` only when `toIdx >= prediction`.
- Related code: `PREDICT_CELL_TYPES` and `EXTRACT_FEATURES` run under `params.container` via `conf/docker.config` lines 6-7.
- Related code: `bin/crop_and_filter.py` lines 27-34 use `slide_root.iterdir()` and never read `args.recursive`.
- Related docs: `docs/usage.md` lines 231-237 state active stage containers are validated at startup.

## Progress

- [x] 2026-05-04T00:00Z — Fix validation for any active features or prediction stage.
- [x] 2026-05-04T00:00Z — Wire crop CLI recursive discovery to `--recursive` and add a narrow test.
- [x] 2026-05-04T00:00Z — Remove unused segmentation params/docs for MAT-only mode.

## Discovery Log

- Finding: Features-only and prediction-only modes can reach Docker execution without rejecting the placeholder main image.
  Evidence: `main.nf` validates main container only for ranges where `fromIdx <= features && toIdx >= prediction`.
  Impact: The run fails later with a Docker image error instead of the intended early validation message.

- Finding: `crop_and_filter.py --recursive` is documented but ignored.
  Evidence: `discover_slides()` has no recursive parameter and always scans only direct children.
  Impact: Direct crop-stage CLI use misses nested WSI files.

## Decision Log

- Decision: Treat these as follow-up fixes, not a new broad refactor.
  Reason: Each issue is localized and independently testable.
  Date: 2026-05-04

## Milestones

### Milestone 1 — Active Stage Container Validation

Goal:

Reject placeholder `params.container` whenever `features` or `prediction` is active.

Edits:
- `nuxplore-cell-type-prediction/main.nf`: change main-container validation to cover `fromIdx <= stageIdx('features') && toIdx >= stageIdx('features')` or `fromIdx <= stageIdx('prediction') && toIdx >= stageIdx('prediction')`.
- `nuxplore-cell-type-prediction/tests/run_stub_pipeline_checks.sh`: add negative checks for features-only and prediction-only placeholder container validation if feasible without Docker.

Validation:
- `nextflow run main.nf -stub-run --from_stage features --to_stage features ...` without `--container` -> fails with the intended validation message.
- `nextflow run main.nf -stub-run --from_stage prediction --to_stage prediction ...` without `--container` -> fails with the intended validation message.
- `bash tests/run_stub_pipeline_checks.sh` -> passes after valid container args are supplied to all affected positive cases.

Risk:

Tests that relied on stub mode bypassing container validation must pass an explicit stub image.

### Milestone 2 — Crop Recursive Discovery

Goal:

Make `crop_and_filter.py --recursive` discover nested slides while preserving non-recursive default behavior.

Edits:
- `nuxplore-cell-type-prediction/bin/crop_and_filter.py`: pass `args.recursive` into slide discovery and use `rglob('*')` only when true.
- `nuxplore-cell-type-prediction/tests/`: add a small CLI or unit-style check for nested discovery if practical.

Validation:
- `python3 -m py_compile bin/crop_and_filter.py` -> no syntax errors.
- Direct CLI smoke with nested fixture and `--recursive` -> manifest reports nested slide discovery, or a narrow Python-level test validates `discover_slides()`.

Risk:

Recursive WSI scans can be expensive; keep opt-in only.

### Milestone 3 — Segmentation Param/Docs Consistency

Goal:

Ensure documented segmentation params match actual MAT-output CLI behavior.

Edits:
- `nuxplore-cell-type-prediction/nextflow.config`, `docs/usage.md`, `params.example.yaml`: either remove unused `seg_geo_format`/`seg_offsets` or wire them through only if MAT output actually supports them.

Validation:
- Manual doc review against `rgci_seg_to_mat.py --help` and `main.nf` command line.

Risk:

If these params are intended future JSON options, mark them out of current MAT mode instead of silently advertising them.

## Validation Plan

- CLI syntax: `python3 -m py_compile bin/crop_and_filter.py bin/rgci_seg_to_mat.py bin/cell_type_predict.py bin/samplesheet_to_pairs.py`.
- Nextflow contract: `bash tests/run_stub_pipeline_checks.sh` when `nextflow` is available.
- Manual: inspect validation errors for features-only and prediction-only placeholder container runs.

## Recovery / Rollback

- Safe retry: changes are localized to validation, discovery, and docs/tests.
- Rollback: revert the touched files for the milestone that fails validation.
- Files to inspect if validation fails: `main.nf`, `tests/run_stub_pipeline_checks.sh`, `.nextflow.log`.

## Completion Summary

Changed:
- `nuxplore-cell-type-prediction/main.nf:74-75`: validate `params.container` for any active features or prediction stage, not only when both run
- `nuxplore-cell-type-prediction/bin/crop_and_filter.py:27,31`: `discover_slides()` honors `--recursive` flag via `rglob("*")`
- `nuxplore-cell-type-prediction/nextflow.config`: removed unused `seg_geo_format` and `seg_offsets` params
- `nuxplore-cell-type-prediction/docs/usage.md`: removed `seg_geo_format`/`seg_offsets` from param table
- `nuxplore-cell-type-prediction/params.example.yaml`: removed `seg_geo_format`/`seg_offsets`
- `nuxplore-cell-type-prediction/tests/run_stub_pipeline_checks.sh`: added negative container validation checks and `--container` to features-only positive test
- `nuxplore-cell-type-prediction/tests/test_pipeline_contract.py`: added `test_crop_slide_discovery_honors_recursive_flag`, wrapper uses micromamba for nextflow

Validated:
- `micromamba run -n nextflow bash tests/run_stub_pipeline_checks.sh` — all 12 checks pass (2 negative container + 10 pipeline)
- `python3 -m pytest nuxplore-cell-type-prediction/tests/test_pipeline_contract.py -v` — 2/2 tests pass (45s)
- `grep -rn seg_geo_format nuxplore-cell-type-prediction/` — no results, clean removal
- `python3 -m py_compile bin/crop_and_filter.py bin/rgci_seg_to_mat.py bin/cell_type_predict.py bin/samplesheet_to_pairs.py` — clean

New dependencies added:
- None.

Remaining:
- (none)

Lessons:
- Stub contract tests must include negative validation paths, not only successful stage combinations.
- Pytest wrapping of bash test scripts requires env alignment (micromamba for nextflow).

## CHANGELOG.md Entry

Draft:

fix upstream stage contract gaps
Reason: enforce active-stage container validation and align crop CLI/docs with advertised behavior
