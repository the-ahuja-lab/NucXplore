# CHANGELOG

Append-only. Most recent entries first.

Use short, telegraphic style:
- verb + object
- no articles
- concise lines

One entry per task.

## 2026-08-14 — synchronize package documentation

document Python 3.10+, TestPyPI 0.3.0 install, mandatory Vahadane normalization, schema counts, batch sidecars, and full release validation commands
Files/Modules: package README and user/developer guides
Impact: package examples and scientific semantics match current API
Reason: remove stale install and feature-generation guidance

## 2026-08-13 — pin the 129-feature extraction schema with regression tests

add `feature_schema_tests` asserting the exact 129-feature key set + nucleus_id (130 keys), finite values, nonzero Hu moments, and positive NND in the full pipeline
Files/Modules: `nucxplore/src/lib.rs`
Impact: any change to the feature contract (names, additions, removals) now fails CI; guards audit findings A04-A07
Reason: previous tests only asserted >= 60 features, so Hu-zero and schema regressions were invisible

## 2026-08-12 — fix Hu moments collapsing to zero (A04)

compute Hu moments via raw→central→normalized→Hu pipeline (`moments::calculate_hu_moments`) instead of mirroring the Python `moments_normalized(binary_mask)` call pattern; add ellipse regression tests
Files/Modules: `src/lib.rs`
Impact: `hu_moment_1..7` now contain real invariant values (previously constant 0.0 for every nucleus on modern scikit-image)
Reason: the deliberate parity mirror treats pixels as moments and divides by `image[0,0]=0` → NaN → zeros
## 2026-08-13 — prepare 0.3.0 scientific release

restore always-on deterministic Vahadane normalization and correct Hu moments in every schema; add runtime dependency metadata, MIT license, repository metadata, strict linting, full-target tests, and installed-wheel CI
Files/Modules: `src/lib.rs`, `src/stain_norm/`, package metadata, CI, docs and tests
Impact: raw `pre_norm_*`, normalized `post_norm_*`, valid Hu invariants, version 0.3.0 and algorithm revision v3.0
Reason: make package scientifically correct, reproducible, installable, and release-gated

## 2026-08-13 — refine corrected V2.1 schema

implement mask-aware cell HOG and CLAHE/CCSM; preserve 89 V2 features plus nucleus ID; add stable schema ordering, invariance tests, type signatures, and feature dictionary
Files/Modules: `src/features/`, Python API/stubs, package feature documentation
Impact: V2 values improve; legacy values and current classifier contract remain unchanged
Reason: remove remaining background-crop influence and document corrected feature semantics

## 2026-05-11 — publish package releases to TestPyPI

route package publish workflow to TestPyPI using `TEST_PYPI_API_TOKEN`
Files/Modules: `.github/workflows/publish-pypi.yml`, `CHANGELOG.md`, `../CHANGELOG.md`
Impact: package maintainers using `nucxplore-v*` tags or manual publish workflow
Reason: private repo cannot use GitHub environment setup for trusted publishing

## 2026-05-10 — refresh package docs for current API

make package README and guides concise; move detailed API, crop, batch, GPU, and troubleshooting content to wiki page
Files/Modules: `README.md`, `docs/user-guide.md`, `docs/developer-guide.md`, `../wiki/Package-User-Guide.md`, `../wiki/Developer-Guide.md`, `CHANGELOG.md`
Impact: package users and contributors
Reason: reflect current public fields such as `completed_images`/`failed_images` and keep public docs user-oriented

## 2026-05-07 — add package CI and PyPI publish workflows

add `.github/workflows/package-ci.yml` and `.github/workflows/publish-pypi.yml` for package-only release automation
Files/Modules: `.github/workflows/package-ci.yml`, `.github/workflows/publish-pypi.yml`, `docs/developer-guide.md`, `CHANGELOG.md`
Impact: package maintainers; PyPI release now triggered by nucxplore-v* tags with trusted publishing across Linux/macOS/Windows
Reason: automated wheel builds and PyPI publishing without pipeline Docker interference

## 2026-05-07 — update package docs for combined repository

update package README, user guide, and developer guide to reflect monorepo layout with sibling `nucxplore-pipeline/` directory
Files/Modules: `README.md`, `docs/user-guide.md`, `docs/developer-guide.md`, `CHANGELOG.md`
Impact: NucXplore package users and contributors
Reason: single GitHub repository for both library and pipeline; update Repository Boundary sections, micromamba env name, and release table

## 2026-05-06 — split package documentation

split user and developer package docs
Files/Modules: `README.md`, `docs/user-guide.md`, `docs/developer-guide.md`, `CHANGELOG.md`
Impact: NucXplore package users and contributors
Reason: make package repository documentation clean for separate library repo usage and future pipeline integration
