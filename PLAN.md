# PLAN

Use for current task only.

## Task

Fix review gaps found after checking the codebase against the active consolidation plans.

## Goal

The repository passes the documented formatting/validation checks, direct crop and segmentation CLIs create requested output/log parent directories, and superseded historical plans are clearly labeled so they are not mistaken for active requirements.

## Scope

- Module: root plan metadata, `nucxplore/` Rust package, `nucxplore-pipeline/` direct CLIs.
- Files likely involved: `nucxplore/src/io/mat.rs`, `nucxplore-pipeline/bin/crop_and_filter.py`, `nucxplore-pipeline/bin/rgci_seg_to_mat.py`, `plans/cell-type-prediction-nextflow.md`, `plans/documentation-split-cleanup.md`.
- Downstream impact: package CI, direct pipeline CLI users, contributors reading plans.

## Constraints

- Preserve CLI flags and existing public behavior except fixing missing parent directory handling.
- Keep Rust changes formatting-only unless a test exposes a real behavior issue.
- Do not rewrite historical plan bodies; add minimal superseded notices only.
- No unrelated refactors.

## Evidence

- Failing command: `micromamba run -n rustenv cargo fmt --all --check` reports formatting diff in `nucxplore/src/io/mat.rs`.
- Failing command: `python3 bin/crop_and_filter.py --log-file <missing-parent>/crop.log ...` raises `FileNotFoundError` before processing.
- Failing command: `python3 bin/rgci_seg_to_mat.py --log-file <missing-parent>/segment.log ...` raises `FileNotFoundError` before processing.
- Related context: `plans/cell-type-prediction-nextflow.md` and `plans/documentation-split-cleanup.md` encode older standalone/separate-repository assumptions superseded by `plans/consolidate-library-pipeline-repo.md` and `plans/consolidation-review-follow-up.md`.

## Discovery

1. `cargo fmt --all --check` -> only formatting drift observed in MAT parser test helper area.
2. Direct CLI parent-dir smoke checks -> both CLIs fail while constructing `logging.FileHandler` if `--log-file` parent does not exist.
3. Plan text review -> stale plans remain useful history but conflict with current monorepo/NucXplore contract if read as active plans.

## Implementation

1. [Modify] `nucxplore/src/io/mat.rs`: run/apply Rust formatting only.
2. [Modify] `nucxplore-pipeline/bin/crop_and_filter.py`: create parent directories before opening `--log-file` and before writing `--output-manifest`.
3. [Modify] `nucxplore-pipeline/bin/rgci_seg_to_mat.py`: create parent directories before opening `--log-file` and before writing `--output-manifest`.
4. [Modify] stale plan files: add a short top notice that each is superseded by later consolidation plans; leave historical content intact.
5. [Verify] Run formatting, direct CLI repro checks, package tests, and pipeline tests listed below.

## Validation

- Tests: `micromamba run -n rustenv cargo test --tests`
- Tests: `micromamba run -n rustenv python3 -m pytest tests/test_batch_api.py -q`
- Tests: `micromamba run -n nextflow python -m pytest tests/test_cell_type_predict.py tests/test_pipeline_contract.py -q`
- Lint/format: `micromamba run -n rustenv cargo fmt --all --check`
- Repro command: direct crop CLI with nested missing `--log-file` and `--output-manifest` parents should return the intended empty-input nonzero status, not `FileNotFoundError`.
- Repro command: direct RGCI segmentation CLI with nested missing `--log-file` and `--output-manifest` parents should return the intended empty-input nonzero status, not `FileNotFoundError`.
- Benchmark: N/A

## Risks

- Compatibility break: none expected.
- Data loss: none expected; changes create directories only for explicitly requested outputs/logs.
- Downstream behavior change: direct CLIs become more permissive for missing output parent directories.

## Done When

- [x] Specific test(s) pass
- [x] Linting/formatting passed or marked N/A
- [x] Intended behavior verified
- [x] Downstream impact checked
- [x] No unrelated files changed
- [x] CHANGELOG.md updated if required

## Completion Summary

- Changed: formatted `nucxplore/src/io/mat.rs`; added parent directory creation for crop/segmentation CLI log and manifest paths; labeled two superseded historical plans; added root changelog entry.
- Validated: `cargo fmt --all --check`; pipeline Python syntax compile; direct CLI parent-dir repros; `cargo test --tests`; package batch pytest; pipeline pytest.
- Assumptions: Plan notices clarify stale historical plans without rewriting their original records.
