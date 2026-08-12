# CHANGELOG

Append-only. Most recent entries first.

Use short, telegraphic style:
- verb + object
- no articles
- concise lines

One entry per task.

## 2026-08-12 — fix Hu moments collapsing to zero (A04)

compute Hu moments via raw→central→normalized→Hu pipeline (`moments::calculate_hu_moments`) instead of mirroring the Python `moments_normalized(binary_mask)` call pattern; add ellipse regression tests
Files/Modules: `src/lib.rs`
Impact: `hu_moment_1..7` now contain real invariant values (previously constant 0.0 for every nucleus on modern scikit-image)
Reason: the deliberate parity mirror treats pixels as moments and divides by `image[0,0]=0` → NaN → zeros

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
