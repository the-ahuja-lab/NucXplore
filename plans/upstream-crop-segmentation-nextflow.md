# EXECPLAN: upstream crop and segmentation Nextflow integration

## Task

Extend `nuxplore-cell-type-prediction/` so the default Nextflow run performs crop/filtering, RGCI/HEIP segmentation, NuXplore feature generation, and cell-type prediction, while still allowing independently callable stages.

## Goal

A user can run the full pipeline from whole-slide images to predictions by default, or run any contiguous stage range by setting `--from_stage` and `--to_stage`.

## Scope

- Modules: `nuxplore-cell-type-prediction/` Nextflow pipeline, crop/filter CLI, RGCI/HEIP segmentation wrapper, stage-specific Docker images, pipeline docs/tests.
- Files likely involved: `nuxplore-cell-type-prediction/main.nf`, `nextflow.config`, `conf/docker.config`, `bin/crop_and_filter.py`, `bin/rgci_seg_to_mat.py` or equivalent wrapper, Dockerfiles for crop/filter and CUDA segmentation, `README.md`, `docs/usage.md`, `tests/*`.
- Downstream impact: changes default pipeline behavior from feature-to-prediction to full slide-to-prediction, while preserving the current flow through `--from_stage features --to_stage prediction`.
- Out of scope: retraining models, changing NuXplore feature semantics, notebook execution in production, publishing Docker images unless explicitly requested, broad HEIP refactors unrelated to pipeline integration.

## Context

The active workflow is `nuxplore-cell-type-prediction/main.nf`. It currently validates `params.input_mode`, prepares optional image/MAT samplesheets, runs `EXTRACT_FEATURES` with `nuxplore.batch`, runs `PREDICT_CELL_TYPES` with `cell_type_predict.py`, and exports features/predictions/nuclei. The workflow expects image roots and MAT roots as inputs.

The new upstream references are notebook-derived. `CropAndFiltering.ipynb` crops WSI files with `tiffslide`, tile size `1250`, level `0`, filters bright low-variance tiles with mean threshold `220` and standard deviation threshold `15`, then removes partial tiles by enforcing tensor shape `[3, 1250, 1250]`. `RGCI_Seg_HEIP.ipynb` loads HEIP code from `HEIP/HEIP`, uses `HEIP/HEIP/last.ckpt`, and runs `SlidingWindowInferer` with patch size `256`, stride `80`, padding `120`, and batch size `8`.

Notebook-local paths must become parameters. Slide inputs become `params.slide_root` or a samplesheet column. Crop outputs become process work output `cropped` and optional published intermediates. Segmentation inputs come from `cropped` or `params.crop_root`. Segmentation outputs become process work output `segmentation_mats` and optional published intermediates. The checkpoint is baked into the CUDA segmentation image at `/opt/heip/models/last.ckpt`, with a development override only if useful.

The user confirmed `RGCI_Seg_HEIP.ipynb` is the intended notebook, the requested `RGCI_Seg_HEG.ipynb` name was a typo, segmentation should produce MAT files for NuXplore, the segmentation image should be CUDA-based, `last.ckpt` should be baked into that image, and the default pipeline should be full slide-to-prediction while allowing intermediate entry/exit.

## Constraints

- Follow repo `AGENTS.md` and global OpenCode guidance: targeted discovery, minimal safe edits, independently testable milestones, restartable ExecPlan.
- Preserve current feature-to-prediction behavior through flags even though the default changes.
- Do not preserve hard-coded notebook paths in CLI, Docker, Nextflow config, or docs.
- Do not destructively filter by deleting user inputs; write only accepted tiles to stage outputs.
- Keep public pipeline params explicit and validated before stages run.
- Keep segmentation GPU-specific behavior guarded by a dedicated CUDA container/profile/resource label.
- Avoid unrelated NuXplore, HEIP, or notebook refactors.

## Evidence

- User report: requested four Nextflow stages: crop/filter, RGCI segmentation, feature generation, cell-type prediction.
- User report: each stage must be independently callable or combined in normal Nextflow workflow use.
- User report: Docker images are needed for filtering and segmentation based on `CropAndFiltering.ipynb` and `RGCI_Seg_HEIP.ipynb`.
- User clarification: segmentation outputs MAT files for NuXplore.
- Existing code: `nuxplore-cell-type-prediction/main.nf` currently implements `PREPARE_SAMPLESHEET`, `EXTRACT_FEATURES`, `PREDICT_CELL_TYPES`, and `EXPORT_RESULTS`.
- Existing code: `HEIP/HEIP/src/scripts/infer_wsi.py` documents JSON output, so the MAT-emitting RGCI/HEIP command or wrapper remains to be identified before implementation.
- Existing config: `nuxplore-cell-type-prediction/conf/docker.config` currently applies one global `params.container` to all processes.

## Progress

- [x] 2026-05-04T12:59Z — Read repo and global OpenCode AGENTS guidance, existing pipeline files, notebooks, HEIP script, README, and changelog.
- [x] 2026-05-04T12:59Z — Updated root `AGENTS.md` with upstream notebook, HEIP code, MAT output, CUDA, and checkpoint-baking references.
- [x] 2026-05-04T12:59Z — Converted initial draft into this ExecPlan format required for large multi-module work.
- [x] 2026-05-04T12:59Z — Milestone 1 implemented: stage params, validation, docs, contract test update.
- [x] 2026-05-04T14:00Z — Milestone 2 implemented: crop/filter CLI, Dockerfile, Nextflow process, stub checks pass.
- [x] 2026-05-04T15:30Z — Milestone 3 implemented: RGCI/HEIP segmentation CLI (MAT output), CUDA Dockerfile, RGCI_SEG process, per-process GPU config, stub checks pass. Confirmed HEIP defaults to MAT output with `inst_map`+`inst_type` — no JSON→MAT conversion needed.
- [x] 2026-05-04T16:15Z — Milestone 4 implemented: full workflow wiring with index-based stage branching, removed EXPORT_RESULTS in favor of per-process publishDir, added prediction-only mode, intermediate publish via `publish_crops`/`publish_segmentation`. All 10 stage-combination stub contracts pass (crop-only, seg-only, features-only, pred-only, crop→seg, seg→features, features→pred, crop→pred etc).
- [x] 2026-05-04T17:00Z — Milestone 5 implemented: README updated with full-pipeline quickstart and per-stage container table; docs/usage.md updated with container flags in examples, fix output layout path, per-container troubleshooting; params.example.yaml updated with upstream stage params. Re-ran stub checks — all 10 pass.

## Discovery Log

- Finding: Current Nextflow pipeline starts at feature extraction and requires image/MAT roots or a pair samplesheet.
  Evidence: `nuxplore-cell-type-prediction/main.nf` validates `params.image_root`, `params.mat_root`, or `params.samplesheet` and calls `EXTRACT_FEATURES` before prediction.
  Impact: Full pipeline must add upstream channels while preserving the current path for users who already have image/MAT inputs.

- Finding: Crop notebook combines three concerns: WSI tiling, blank/background filtering, and partial-tile removal.
  Evidence: `CropAndFiltering.ipynb` lines with `tile_size = 1250`, mean/std thresholds, and `desired_shape = torch.Size([3, 1250, 1250])`.
  Impact: Production CLI should make these independent params and avoid deleting source or intermediate user files.

- Finding: Segmentation notebook uses notebook-global hard-coded paths and duplicates model initialization.
  Evidence: `RGCI_Seg_HEIP.ipynb` defines `valid_img_root_dir`, `save_root_dir`, and `path_to_weights` in cells.
  Impact: Production segmentation must be a CLI or wrapper with explicit paths and no notebook globals.

- Finding: Checked HEIP CLI documents JSON annotations, not MAT outputs.
  Evidence: `HEIP/HEIP/src/scripts/infer_wsi.py` docstring says masks are saved as `.json` files for QuPath.
  Impact: Resolution found — `SlidingWindowInferer` defaults to `.mat` output when `save_format` is not passed; the JSON output in `infer_wsi.py` is a deliberate override. No conversion step needed.

## Decision Log

- Decision: Use an ExecPlan in `plans/upstream-crop-segmentation-nextflow.md`.
  Reason: Work spans multiple modules, Docker images, CLIs, Nextflow branching, tests, and likely more than one session.
  Date: 2026-05-04

- Decision: Use `from_stage` and `to_stage` rather than a fixed enum like `workflow_mode`.
  Reason: It supports individual stages and contiguous combined workflows without enumerating every valid combination.
  Date: 2026-05-04

- Decision: Default to `from_stage = crop` and `to_stage = prediction`.
  Reason: User requested full pipeline as the default while retaining intermediate entry through flags.
  Date: 2026-05-04

- Decision: Build a CUDA segmentation image with `last.ckpt` baked at `/opt/heip/models/last.ckpt`.
  Reason: User requested CUDA and checkpoint baking; this avoids runtime checkpoint ambiguity.
  Date: 2026-05-04

- Decision: Keep current feature-to-prediction behavior via `--from_stage features --to_stage prediction`.
  Reason: Preserves compatibility for existing users and tests.
  Date: 2026-05-04

## Milestones

### Milestone 1 — Stage Contract And Validation

Goal:

Define the public pipeline contract before implementation.

Edits:
- `nuxplore-cell-type-prediction/nextflow.config`: add `from_stage`, `to_stage`, crop params, segmentation params, standalone `crop_root` and `features_root`, stage containers, and publish-intermediate flags.
- `nuxplore-cell-type-prediction/main.nf`: add validation for legal stage order and required inputs by entry stage.
- `nuxplore-cell-type-prediction/docs/usage.md`: document full and partial invocation patterns.

Validation:
- `nextflow config` -> config renders without syntax errors.
- `nextflow run main.nf -stub-run --from_stage features --to_stage prediction --image_root <fixture> --mat_root <fixture>` -> current behavior remains wireable.

Risk:

Changing defaults can surprise users; docs and compatibility flags must be explicit.

### Milestone 2 — Crop And Filtering CLI/Image

Goal:

Replace `CropAndFiltering.ipynb` with a parameterized, deterministic crop/filter stage.

Edits:
- `nuxplore-cell-type-prediction/bin/crop_and_filter.py`: implement WSI discovery, tiling, filtering, partial-tile handling, manifest output, and stable sample naming.
- `nuxplore-cell-type-prediction/Dockerfile.crop-filter`: add runtime with `tiffslide`, OpenSlide libraries, `pillow`, `opencv-python-headless`, `numpy`, and the CLI.
- `nuxplore-cell-type-prediction/main.nf`: add `CROP_AND_FILTER` process emitting `cropped`, `crop_manifest.json`, and `crop.log`.
- `nuxplore-cell-type-prediction/tests/*`: add CLI-level or stub contract checks.

Validation:
- `python -m py_compile bin/crop_and_filter.py` from `nuxplore-cell-type-prediction/` -> no syntax errors.
- `nextflow run main.nf -stub-run --from_stage crop --to_stage crop --slide_root <fixture>` -> crop-only channel contract passes.
- One tiny real WSI/fixture smoke run -> manifest reports tiles and filters as expected.

Risk:

WSI formats need OpenSlide-compatible system libraries; image naming must match the segmentation stage.

### Milestone 3 — RGCI/HEIP Segmentation CLI/Image

Goal:

Add a CUDA segmentation stage that consumes crop folders and emits NuXplore-compatible MAT masks.

Edits:
- `nuxplore-cell-type-prediction/bin/rgci_seg_to_mat.py` or equivalent: wrap the confirmed MAT-emitting RGCI/HEIP inference path.
- `nuxplore-cell-type-prediction/Dockerfile.rgci-seg`: add CUDA/PyTorch/HEIP runtime and bake `HEIP/HEIP/last.ckpt` to `/opt/heip/models/last.ckpt`.
- `nuxplore-cell-type-prediction/main.nf`: add `RGCI_SEG` process with `label 'segmentation'`, `container params.seg_container`, crop input, MAT output, manifest, and log.
- `nuxplore-cell-type-prediction/conf/docker.config`: add per-process containers and CUDA run options/profile handling for segmentation.
- `nuxplore-cell-type-prediction/tests/*`: add segmentation stub contract checks.

Validation:
- `python -m py_compile bin/rgci_seg_to_mat.py` -> no syntax errors.
- `nextflow run main.nf -stub-run --from_stage segmentation --to_stage segmentation --crop_root <fixture>` -> segmentation-only channel contract passes.
- CUDA smoke run on one crop folder -> MAT files are produced in mirrored layout.

Risk:

The checked HEIP CLI currently documents JSON output; MAT output requires the correct RGCI wrapper or additional conversion code.

### Milestone 4 — Full Workflow Wiring

Goal:

Wire crop output to segmentation, segmentation MAT output to NuXplore features, and feature output to prediction.

Edits:
- `nuxplore-cell-type-prediction/main.nf`: branch channels based on `from_stage` and `to_stage` and connect all four stages.
- `nuxplore-cell-type-prediction/main.nf`: update `EXPORT_RESULTS` to publish final outputs and optional intermediates without overwriting user inputs.
- `nuxplore-cell-type-prediction/nextflow.config`: set default `from_stage = 'crop'` and `to_stage = 'prediction'`.
- `nuxplore-cell-type-prediction/tests/run_stub_pipeline_checks.sh`: cover full, crop-only, segmentation-only, features-only, prediction-only, and features-to-prediction modes.

Validation:
- `bash tests/run_stub_pipeline_checks.sh` from `nuxplore-cell-type-prediction/` -> all stub contracts pass.
- `python -m pytest -q tests/test_pipeline_contract.py` -> pytest wrapper passes.
- `nextflow run main.nf -stub-run --from_stage crop --to_stage prediction --slide_root <fixture>` -> full channel contract passes.

Risk:

Nextflow branching can produce unclear errors if required entry-stage params are missing; validation should fail early with explicit messages.

### Milestone 5 — Documentation And Changelog

Goal:

Document user-visible behavior and record the durable outcome.

Edits:
- `nuxplore-cell-type-prediction/README.md`: update quickstart for full default mode and partial-stage examples.
- `nuxplore-cell-type-prediction/docs/usage.md`: document inputs, outputs, containers, GPU requirements, and stage flags.
- `nuxplore-cell-type-prediction/CHANGELOG.md`: add top entry after implementation is validated.

Validation:
- Manual doc review against CLI params and process outputs.
- Re-run stub checks after docs/config changes if examples touch tested commands.

Risk:

Docs can drift from params; keep examples minimal and based on validated commands.

## Implementation Notes

- Stage order is `crop`, `segmentation`, `features`, `prediction`.
- Default params should be `from_stage = 'crop'` and `to_stage = 'prediction'`.
- Crop standalone entry requires `slide_root` or future `slide_samplesheet`.
- Segmentation standalone entry requires `crop_root`.
- Feature standalone entry requires `image_root` and `mat_root`.
- Prediction standalone entry requires `features_root`.
- Full mode connects `CROP_AND_FILTER.cropped` to both segmentation crop input and feature image input.
- Full mode connects `RGCI_SEG.segmentation_mats` to feature MAT input.
- Segmentation MAT filenames and relative paths must mirror cropped image filenames and relative paths.
- Crop filenames should preferably be HEIP-compatible `patch_x-<x>_y-<y>.png`, pending final confirmation.
- Stage-specific containers should replace the current single global `params.container` assignment in Docker profile.

## Validation Plan

- Unit tests: Python syntax checks and focused tests for crop/filter naming, filtering decisions, and manifest generation.
- Integration tests: Nextflow stub runs for full, individual stages, and current feature-to-prediction compatibility path.
- CLI/manual checks: tiny real crop/filter run and one CUDA segmentation smoke run.
- Performance checks: none required unless crop/segmentation runtime optimization is requested; measure before optimizing.
- Regression checks: existing feature-to-prediction stub and pytest contract must continue to pass.

## Recovery / Rollback

- Safe retry: rerun failed Nextflow stages with `-resume` after fixing CLI/config issues.
- Rollback: revert new crop/segmentation processes and reset defaults to `--from_stage features --to_stage prediction` if full mode is not ready.
- Files to inspect if validation fails: `nextflow.log`, stage `*.log` outputs, `crop_manifest.json`, `segmentation_manifest.json`, `main.nf`, `nextflow.config`, `conf/docker.config`.

## Completion Summary

Changed:
- `nuxplore-cell-type-prediction/bin/crop_and_filter.py` — new CLI: WSI tiling with blank/partial-tile filtering, HEIP-compatible naming, manifest output
- `nuxplore-cell-type-prediction/bin/rgci_seg_to_mat.py` — new CLI: HEIP SlidingWindowInferer with MAT output (inst_map+inst_type keys), CUDA support
- `nuxplore-cell-type-prediction/Dockerfile.crop-filter` — slim Python image with tiffslide, OpenSlide, pillow, opencv, numpy
- `nuxplore-cell-type-prediction/Dockerfile.rgci-seg` — CUDA image (pytorch/pytorch:1.13.1-cuda11.7) with cellseg-models-pytorch, pytorch-lightning, HEIP src/ and last.ckpt baked in
- `nuxplore-cell-type-prediction/main.nf` — 4-stage workflow (CROP_AND_FILTER, RGCI_SEG, EXTRACT_FEATURES, PREDICT_CELL_TYPES); stageIdx helper for index-based comparisons; per-process publishDir replacing EXPORT_RESULTS; intermediate publish via enabled flags; 10 stage-combination branches
- `nuxplore-cell-type-prediction/nextflow.config` — stage params, crop/seg params, per-stage containers, publish flags
- `nuxplore-cell-type-prediction/conf/docker.config` — per-process container via withName with --gpus all for segmentation
- `nuxplore-cell-type-prediction/README.md` — full-pipeline quickstart, per-stage container table, partial examples
- `nuxplore-cell-type-prediction/docs/usage.md` — full param table, all running examples with container flags, per-container troubleshooting
- `nuxplore-cell-type-prediction/params.example.yaml` — upstream stage params, stage control, per-stage containers
- `nuxplore-cell-type-prediction/tests/run_stub_pipeline_checks.sh` — 10 stub contracts covering all stage combinations
- `HEIP/src` referenced in Dockerfile.rgci-seg; no modifications to HEIP notebook code

Validated:
- `nextflow config -o flat` — clean
- `python3 -m py_compile bin/crop_and_filter.py bin/rgci_seg_to_mat.py bin/cell_type_predict.py bin/samplesheet_to_pairs.py` — all clean
- 10 stub pipeline checks pass (legacy roots, legacy samplesheet, features-only, crop-only ×2, seg-only, crop→seg, seg→features, pred-only, full crop→prediction)
- Config validation branches: all 10 stage-combination ranges produce correct container requirement checks

New dependencies added:
- Dockerfile.crop-filter: `tiffslide`, `opencv-python-headless`
- Dockerfile.rgci-seg: `cellseg-models-pytorch==0.1.16`, `pytorch-lightning==1.9.5`, `omegaconf==2.3.0`, `timm`, `scikit-image`, `scikit-learn`, `scipy`, `tqdm`
- Base images: `python:3.12-slim` (crop), `pytorch/pytorch:1.13.1-cuda11.7-cudnn8-runtime` (seg)

Remaining:
- (none — all milestones complete)

Lessons:
- HEIP SlidingWindowInferer defaults to .mat output (not JSON). The infer_wsi.py CLI's JSON output is a deliberate `save_format=".json"` override. No conversion step needed.
- Nextflow 26.x does not allow `if` statements in .config files. Container validation must live in main.nf.
- Groovy string comparison (`<=`, `>=`) uses lexicographic order, not stage order. Stage comparisons must use index-based logic.
