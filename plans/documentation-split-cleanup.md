# EXECPLAN

> Superseded historical plan. Its separate-repository documentation assumptions
> were replaced by the monorepo contract in
> `plans/consolidate-library-pipeline-repo.md` and
> `plans/consolidation-review-follow-up.md`.

## Task

Clean and split documentation into user-facing and developer-facing guides for the future separate package-library and Nextflow-pipeline repositories.

## Goal

Users can install and run NucXplore or the Nextflow pipeline from concise user docs, while contributors can build, test, package, and maintain each repository from separate developer docs.

## Scope

- Modules: `nucxplore/` package docs, `nucxplore-cell-type-prediction/` pipeline docs.
- Files likely involved: `nucxplore/README.md`, `nucxplore/docs/user-guide.md`, `nucxplore/docs/developer-guide.md`, `nucxplore/CHANGELOG.md`, `nucxplore-cell-type-prediction/README.md`, `nucxplore-cell-type-prediction/docs/user-guide.md`, `nucxplore-cell-type-prediction/docs/developer-guide.md`, `nucxplore-cell-type-prediction/docs/usage.md`, `nucxplore-cell-type-prediction/params.example.yaml`, `nucxplore-cell-type-prediction/CHANGELOG.md`.
- Downstream impact: documentation consumers, DockerHub image naming expectations, future repository split expectations.
- Out of scope: code changes, Docker image builds, package publishing, Nextflow behavior changes.

## Context

The current workspace contains both future repositories. `nucxplore/` is the Rust + PyO3 package library. `nucxplore-cell-type-prediction/` is the separate Nextflow pipeline. The user explicitly wants docs to reflect that the pipeline and package will be separate git repositories and Docker images will be hosted on Docker Hub.

Current behavior: package README mixes setup, usage, API, and developer notes; package has `docs/developer-guide.md` but no user guide. Pipeline README and `docs/usage.md` are user-oriented; pipeline has no developer guide.

Desired behavior: each repository has a short README that points to `docs/user-guide.md` and `docs/developer-guide.md`; user docs focus on installation/setup/usage/outputs/troubleshooting; developer docs focus on source layout, local development, validation, Docker/publishing contracts, and maintenance.

## Constraints

- Preserve backward compatibility unless explicitly told otherwise.
- Avoid unrelated refactors.
- Keep public APIs stable unless change is required.
- Use smallest safe migration path.
- Validate each milestone independently.

## Evidence

- User report: requested updated and cleaned documentation, with separate developer and user versions, and future separate repositories for package and pipeline with DockerHub images.

## Progress

- [x] 2026-05-06T00:00Z — Inventoried existing README, usage, developer guide, params, and changelog docs.
- [x] 2026-05-06T00:00Z — Rewrite package docs.
- [x] 2026-05-06T00:00Z — Rewrite pipeline docs.
- [x] 2026-05-06T00:00Z — Update changelog entries and validate links/content.

## Discovery Log

- Finding: Package docs have `README.md` and `docs/developer-guide.md`, but no user guide.
  Evidence: `nucxplore/docs/` only contains `developer-guide.md`.
  Impact: add package user guide and make README an entrypoint.
- Finding: Pipeline docs have user usage content in `docs/usage.md`, but no developer guide.
  Evidence: `nucxplore-cell-type-prediction/docs/usage.md` exists; no pipeline developer guide found.
  Impact: replace/add split docs while keeping README concise.
- Finding: Pipeline config still uses placeholder DockerHub image names.
  Evidence: `nextflow.config` and `params.example.yaml` contain `docker.io/<owner>/...` placeholders.
  Impact: docs should explain placeholders and DockerHub-hosted images without claiming final tags.

## Decision Log

- Decision: Keep README files short and put canonical details in `docs/user-guide.md` and `docs/developer-guide.md`.
  Reason: matches future separate repository layout and avoids duplicating long setup instructions.
  Date: 2026-05-06
- Decision: Retain `docs/usage.md` as a compatibility pointer to the new pipeline user guide.
  Reason: existing links and users may already reference that path.
  Date: 2026-05-06

## Milestones

### Milestone 1 — Package Docs

Goal: Package repository has clean user and developer docs.

Edits:
- `nucxplore/README.md`: concise package overview and doc links.
- `nucxplore/docs/user-guide.md`: install, setup, API, batch, GPU, troubleshooting.
- `nucxplore/docs/developer-guide.md`: cleaned contributor/build/test/release docs.
- `nucxplore/CHANGELOG.md`: durable documentation outcome.

Validation:
- Manual read/link consistency check.

Risk: Documentation could overstate published image/package names; use placeholders where final DockerHub owner/tag is unknown.

### Milestone 2 — Pipeline Docs

Goal: Pipeline repository has clean user and developer docs and explicit DockerHub/separate-repo assumptions.

Edits:
- `nucxplore-cell-type-prediction/README.md`: concise pipeline overview and doc links.
- `nucxplore-cell-type-prediction/docs/user-guide.md`: canonical user setup/usage/params/outputs/troubleshooting.
- `nucxplore-cell-type-prediction/docs/developer-guide.md`: source layout, local checks, DockerHub image contract, release notes.
- `nucxplore-cell-type-prediction/docs/usage.md`: compatibility pointer.
- `nucxplore-cell-type-prediction/CHANGELOG.md`: documentation outcome.

Validation:
- Manual read/link consistency check.

Risk: Docs can mention DockerHub hosting while final owner/tag remains unset; keep placeholders explicit.

## Implementation Notes

- API signatures must remain documentation-only and align with current README/developer guide.
- Do not change Dockerfiles, Python, Rust, or Nextflow workflow code.
- Keep `params.example.yaml` aligned with documented parameter defaults.

## Validation Plan

- Unit tests: N/A, documentation-only.
- Integration tests: N/A, documentation-only.
- CLI/manual checks: check all referenced paths exist and current parameter names match `nextflow.config` / `params.example.yaml`.
- Performance checks: N/A.
- Regression checks: keep `docs/usage.md` as pointer for existing links.

## Recovery / Rollback

- Safe retry: reapply documentation edits only.
- Rollback: revert changed Markdown files if requested.
- Files to inspect if validation fails: README files, docs guides, changelogs, `nextflow.config`, `params.example.yaml`.

## Completion Summary

Changed:
- Split package docs into concise README, `docs/user-guide.md`, `docs/developer-guide.md`, and package changelog.
- Split pipeline docs into concise README, `docs/user-guide.md`, `docs/developer-guide.md`, compatibility `docs/usage.md`, params example alignment, and changelog entry.

Validated:
- `python3 - <<'PY' ... PY` link and parameter consistency check passed.

New dependencies added:
- None

Remaining:
- Replace DockerHub placeholders with final owner/tag when release images are published.

Lessons:
- Keep `docs/usage.md` as a pointer because historical plans and changelog entries reference that path.

## CHANGELOG.md Entry

Document split user/developer guides
Reason: make package and pipeline docs ready for separate repositories and DockerHub-hosted runtime images.
