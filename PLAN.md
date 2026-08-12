# PLAN

## Task
Refresh the hosted documentation homepage with the supplied NucXplore overview image and a ChemicalDice-inspired content structure.

## Goal
Present NucXplore with a clear hero, overview, capabilities, quick starts, and documentation routes while preserving the current Material theme.

## Scope
- Module: hosted documentation homepage
- Files likely involved: `wiki/Home.md`, `wiki/assets/nucxplore-feature-overview.png`, `PLAN.md`, `CHANGELOG.md`
- Downstream impact: hosted GitHub Pages readers

## Constraints
- Keep the current MkDocs Material theme unchanged
- Use the supplied image as the hero visual
- Keep content grounded in existing package and pipeline documentation
- Preserve links to all detailed wiki pages

## Evidence
- Input file: `/tmp/codex-clipboard-F4CbRV.png` (512×221 RGBA PNG)
- Related context: ChemicalDice landing page leads with a concise description and overview graphic, followed by overview and usage-oriented sections.

## Discovery
1. Browser snapshot of the ChemicalDice site → product statement, overview image, overview, capabilities, and practical usage content lead the page.
2. `wiki/Home.md` → current homepage is a documentation index without a product-level hero or quick start.
3. `README.md` and detailed guides → package installation/API and full Nextflow invocation are current supported entry paths.

## Implementation
1. [Add] `wiki/assets/nucxplore-feature-overview.png`: store the supplied hero visual.
2. [Modify] `wiki/Home.md`: add hero, overview, capabilities, quick starts, workflow, and documentation links.
3. [Verify] Run strict MkDocs build and inspect the rendered homepage in a browser.

## Validation
- Tests: `mkdocs build --strict`
- Lint/format: `git diff --check`
- Repro command: serve the built site and inspect desktop/mobile screenshots
- Benchmark: N/A

## Risks
- Compatibility break: none expected
- Data loss: none expected
- Downstream behavior change: homepage content and visual presentation change

## Done When
- [x] Strict MkDocs build passes
- [x] Hero image renders at the top of the homepage
- [x] Homepage links and quick starts are valid
- [x] Desktop and mobile layouts are visually checked
- [x] No unrelated files changed
- [x] `CHANGELOG.md` updated

## Completion Summary
- Changed: added supplied overview diagram and rebuilt the homepage around product overview, usage paths, quick starts, workflow, and documentation routes.
- Validated: strict MkDocs build, generated asset/link assertions, `git diff --check`, and browser inspection at 1440×1000 and 390×844.
- Assumptions: the supplied diagram is approved for publication in this repository.
