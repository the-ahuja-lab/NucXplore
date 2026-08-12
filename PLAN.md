# PLAN

## Task
Expand the hosted NucXplore documentation with detailed architecture and pipeline flow diagrams.

## Goal
Give users and contributors an accurate visual explanation of the package, feature engine, Nextflow orchestration, alternate entry paths, outputs, and deployment boundaries.

## Scope
- Module: hosted GitHub Pages documentation
- Files likely involved: `wiki/Home.md`, `wiki/Architecture.md`, `mkdocs.yml`, `PLAN.md`, `CHANGELOG.md`
- Downstream impact: hosted documentation readers

## Constraints
- Preserve the current Material theme and supplied hero image
- Ground diagrams in current Rust, Python, and Nextflow code
- Keep the homepage concise and place implementation detail on Architecture
- Treat GitHub Pages as canonical; do not sync the separate GitHub Wiki

## Evidence
- `nucxplore/src/lib.rs`: Python-facing feature orchestration, normalization, per-instance regions, CPU/WGPU feature dispatch, spatial enrichment, and crop export.
- `nucxplore-pipeline/main.nf`: four-stage workflow plus samplesheet preparation and alternate entry stages.
- `nucxplore-pipeline/nextflow.config`: active container, GPU, model, publishing, and stage defaults.

## Discovery
1. Package path is Python API/batch → PyO3 → Rust I/O and instance regions → feature families → Python maps/CSV and optional crops.
2. Pipeline path is crop/filter → RGCI/HEIP segmentation → extraction → XGBoost prediction, with roots, samplesheet, and prediction-only bypasses.
3. MkDocs needs a Mermaid custom fence and a pinned Mermaid runtime; no diagram support is currently configured.

## Implementation
1. [Modify] `wiki/Home.md`: replace text workflow with Mermaid and add a compact architecture preview.
2. [Create] `wiki/Architecture.md`: document system, feature-engine, pipeline, data, compute, failure, and deployment boundaries.
3. [Modify] `mkdocs.yml`: add Architecture navigation and Mermaid rendering.
4. [Verify] strict build, generated routes, live diagrams, responsive layout, dark mode, and deployment.

## Validation
- Tests: `mkdocs build --strict`
- Lint/format: `git diff --check`
- Repro command: local browser inspection at desktop and mobile widths
- Benchmark: N/A

## Risks
- Compatibility break: none expected
- Data loss: none expected
- Downstream behavior change: new documentation route and client-rendered diagrams

## Done When
- [x] Strict MkDocs build passes
- [x] All Mermaid diagrams render without Mermaid console errors
- [x] Homepage and Architecture navigation resolves
- [x] Desktop, mobile, and dark-mode layouts pass visual inspection
- [x] No unrelated files changed
- [x] `CHANGELOG.md` updated

## Completion Summary
- Changed: added Architecture navigation, six Mermaid diagrams across Home and Architecture, and implementation-grounded package, pipeline, failure, output, and deployment documentation.
- Validated: strict MkDocs build; generated route, link, fence, and runtime assertions; desktop/mobile screenshots; dark-mode inspection; `git diff --check`.
- Assumptions: Mermaid CDN availability is acceptable for the hosted documentation.
