# CHANGELOG

Append-only. Most recent entries first.

Use short, telegraphic style:
- verb + object
- no articles
- concise lines

One entry per task.

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
