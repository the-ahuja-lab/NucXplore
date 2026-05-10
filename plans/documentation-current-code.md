# ExecPlan: documentation current-code refresh

## Task
Update public documentation to match current NucXplore code and move detailed content into GitHub-wiki-style pages.

## Goal
Keep repository READMEs and user guides concise and user-oriented while providing detailed reference material under local wiki markdown pages ready to copy or publish to a GitHub wiki.

## Scope
- Root repository overview and release boundary.
- `nucxplore/` package README and docs.
- `nucxplore-pipeline/` README and docs.
- New wiki markdown pages for detailed package, pipeline, Docker, validation, and developer content.
- Changelog entries for the documentation behavior change.

## Constraints
- Documentation only; no code or public API changes.
- Avoid generated, target, work, dist, and environment directories.
- Keep public-facing docs concise.
- Base detailed content on current code, config, tests, and scripts.

## Discovery Log
- 2026-05-10: repo `AGENTS.md` identifies two maintained subprojects: Rust/PyO3 package and Nextflow pipeline.
- 2026-05-10: root `CHANGELOG.md` recent entries identify Docker references, CLI boolean parsing, publish outputs, Docker image tags, GPU segmentation behavior, and local Docker run helpers as recent behavior to document.

## Implementation Plan
1. Inspect public API stubs, package metadata, pipeline config, scripts, and tests.
2. Replace concise public docs with current quick-start, install, run, and troubleshooting paths.
3. Add detailed wiki markdown pages under `wiki/` for long-form content.
4. Update changelogs for documentation refresh.
5. Validate markdown links and referenced commands/files with targeted searches.

## Validation
- Documentation link/file existence audit with a small shell or grep command.
- No runtime tests expected because changes are documentation only.

## Progress
- [x] Created ExecPlan.
- [x] Current API and pipeline parameters mapped.
- [x] Public docs updated.
- [x] Wiki pages created.
- [x] Changelogs updated.
- [x] Documentation audit complete.

## Completion Summary
- Changed: concise root/package/pipeline docs; added wiki pages for package usage, pipeline usage, parameters, Docker/validation, and developer workflow; updated changelogs.
- Validated: `python3` markdown relative-link audit checked 32 markdown files; all relative links resolve.
- Assumptions: local `wiki/*.md` files are the repo-side source for GitHub wiki pages; no runtime tests were required because changes are documentation-only.
