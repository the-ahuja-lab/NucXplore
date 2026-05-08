# nuxplore-cell-type-prediction ExecPlan

> Superseded historical plan. Current pipeline requirements are governed by
> `plans/upstream-crop-segmentation-nextflow.md`,
> `plans/consolidate-library-pipeline-repo.md`, and
> `plans/consolidation-review-follow-up.md`.

## Task

Implement the standalone `nuxplore-cell-type-prediction` Nextflow pipeline that extracts NuXplore features and applies the baked XGBoost cell-type prediction model to raw image/MAT data.

## Goal

A user can run a command like:

```bash
nextflow run main.nf \
  --image_root /data/images \
  --mat_root /data/mats \
  --outdir /data/results \
  -profile docker
```

or:

```bash
nextflow run main.nf -params-file params.yaml -profile docker
```

and receive per-image feature CSVs annotated with `Predicted_Label` and `Confidence_Score`, plus optional crop outputs and run summaries.

## Scope

- Modules:
  - Standalone Nextflow pipeline repository, separate from the NuXplore featurizer repository.
  - DockerHub-hosted runtime image containing NuXplore, Python dependencies, model artifacts, and prediction CLI.
  - Python cell-type prediction CLI translated from the first notebook cell.
  - Nextflow DSL2 workflow, config, params schema, and examples.
- Files likely involved:
  - `main.nf`
  - `nextflow.config`
  - `conf/*.config`
  - `bin/cell_type_predict.py`
  - `bin/samplesheet_to_pairs.py`
  - `params.example.yaml`
  - `docs/usage.md`
  - `tests/fixtures/*`
- Downstream impact:
  - Adds a standalone workflow around the DockerHub-hosted NuXplore cell-type prediction image.
  - Does not modify the separate NuXplore featurizer repository.
- Out of scope:
  - Retraining the model.
  - Changing model semantics.
  - Building or publishing the DockerHub image unless explicitly requested in this pipeline repository.
  - Notebook plotting/count summary cells 1 and 2.

## Context

The active featurizer package is `nuxplore/`, a Rust + PyO3 Python project. The Nextflow pipeline will live in its own repository directory, `nuxplore-cell-type-prediction/`. Existing batch extraction is exposed inside the Docker image by `nuxplore.batch` and accepts paired image/MAT roots, writing per-image CSVs and optional crops. The first cell of `CellTypePred.ipynb` loads:

- `Final_XGB_Model_FullData.pkl`: pickled `xgboost.sklearn.XGBClassifier`.
- `final_label_encoder.pkl`: pickled `sklearn.preprocessing.LabelEncoder`.

Notebook cell 0 behavior:

1. Loads each feature CSV from an input root.
2. Gets expected feature names from `model.get_booster().feature_names`.
3. Fails with a descriptive error if expected model feature columns are missing.
4. Runs `model.predict()` and `model.predict_proba()`.
5. Writes original columns plus `Predicted_Label` and `Confidence_Score`.

The user-provided `/home/adnanraza/Downloads/model_output_HPT_Final_Holy/` path was not present during discovery. Equivalent model files exist at `/home/adnanraza/nuxplore_project/model_output_HPT_Final_Holy/model_output_HPT_Final_Holy/`.

## Current Documentation References

Fetched through Context7 MCP on 2026-05-02:

- Nextflow `/nextflow-io/nextflow`:
  - DSL2 uses explicit `workflow` and `process` blocks.
  - `nextflow run main.nf -params-file params.json` supports external JSON/YAML parameters.
  - Process `container 'image:tag'` runs commands inside Docker when Docker is enabled.
  - New typed `params { input: Path }` syntax exists with the strict parser, but the first implementation should prefer broadly compatible standard params unless repo policy requires strict syntax.
- Docker `/docker/docs`:
  - Use Python slim base images, separate dependency installation for cache efficiency, BuildKit cache mounts when available, and non-root runtime users.
  - Copy application source after dependency layers.
- XGBoost `/dmlc/xgboost`:
  - `XGBClassifier` supports `predict`, `predict_proba`, and `get_booster()` through the scikit-learn interface.
- scikit-learn `/scikit-learn/scikit-learn`:
  - `LabelEncoder.inverse_transform()` converts predicted numeric classes back to original labels.
  - `joblib.load()` is standard for loading persisted estimators/encoders, but versions must be pinned or recorded for reproducibility.

## Constraints

- Do not edit the NuXplore featurizer repository for pipeline-only work.
- Keep notebook translation deterministic and explicit; do not silently swallow all errors like the notebook does.
- Container must run without host Python/Rust dependencies.
- Model artifacts are baked into the DockerHub-hosted image, not stored in the pipeline repository.
- Avoid committing secrets, environment files, generated wheels, and unrelated large derived outputs.
- Use the smallest workflow that supports normal Nextflow conventions: CLI params, `-params-file`, `-profile docker`, `publishDir`, and trace/report outputs.

## Resolved Requirements

1. Pipeline name: `nuxplore-cell-type-prediction`.
2. Repository layout: standalone Nextflow repo under `nuxplore-cell-type-prediction/`, separate from the NuXplore featurizer repo.
3. v1 input: raw image/MAT data only; no precomputed feature CSV mode.
4. Pairing modes: support both mirrored relative paths via flags and samplesheet CSV.
5. Docker image: hosted on DockerHub; exact image name/tag is configurable and will be decided later.
6. Model artifacts: baked into the Docker image, not committed to this pipeline repo.
7. Missing model feature columns: fail the run with a descriptive error.
8. Notebook plotting/count summary cells: out of scope for v1.

## Evidence

- User report:
  - Need Docker image baked with featurizer and models.
  - First notebook chunk should become a Python script.
  - Workflow should become a Nextflow pipeline taking input files/configs as flags or parameter file.
- Input data:
  - `/home/adnanraza/Downloads/CellTypePred.ipynb`, 4 cells.
  - `/home/adnanraza/nuxplore_project/CellTypePred.ipynb`, same 4-cell notebook.
  - `/home/adnanraza/nuxplore_project/model_output_HPT_Final_Holy/model_output_HPT_Final_Holy/Final_XGB_Model_FullData.pkl`, about 10.8 MB.
  - `/home/adnanraza/nuxplore_project/model_output_HPT_Final_Holy/model_output_HPT_Final_Holy/final_label_encoder.pkl`, about 593 bytes.
- Related code:
  - `nuxplore/python/nuxplore/batch.py` already provides CLI-level paired image/MAT feature extraction.

## Progress

- [x] 2026-05-02T15:01Z — Read repo guidance and NuXplore structure.
- [x] 2026-05-02T15:01Z — Queried Context7 for current Nextflow, Docker, XGBoost, and scikit-learn guidance.
- [x] 2026-05-02T15:01Z — Inspected first notebook cell and confirmed prediction logic.
- [x] 2026-05-02T15:01Z — Located model files in project path; Downloads model directory was absent.
- [x] 2026-05-02T15:01Z — Resolved input modes, DockerHub ownership, missing-feature behavior, plotting scope, and standalone repo name.
- [x] 2026-05-02T15:01Z — Created `nuxplore-cell-type-prediction/` scaffold with `bin/`, `conf/`, `docs/`, `tests/fixtures/`, and `plans/`.
- [ ] Implement milestones below.

## Discovery Log

- Finding: Existing NuXplore batch CLI can already create feature CSVs from image/MAT roots.
  Evidence: `nuxplore/python/nuxplore/batch.py` exposes `--image-root`, `--mat-root`, `--output-csv-root`, `--output-nuclei-root`, crop flags, metadata flags, and worker controls.
  Impact: Nextflow can compose extraction and prediction as separate processes instead of reimplementing extraction.

- Finding: Notebook cell 0 silently ignores empty files, missing feature columns, and all exceptions.
  Evidence: cell lines 39-45 and 64-65.
  Impact: Production CLI should report structured failures; optional skip behavior can preserve compatibility.

- Finding: Model expects exact feature names from `model.get_booster().feature_names`.
  Evidence: notebook line 79.
  Impact: Prediction CLI must align columns exactly and validate feature coverage before inference.

- Finding: User-specified Downloads model directory was missing.
  Evidence: `ls /home/adnanraza/Downloads/model_output_HPT_Final_Holy` failed.
  Impact: Implementation needs a confirmed source for model artifacts before Docker build is reproducible.

## Decision Log

- Decision: Use a two-step Nextflow workflow: `EXTRACT_FEATURES` then `PREDICT_CELL_TYPES`.
  Reason: Keeps featurizer and model inference independently testable and mirrors current code boundaries.
  Date: 2026-05-02

- Decision: Bake the model files into the default Docker image under `/opt/nuxplore/models/`.
  Reason: User requested a Docker image baked with featurizer and models; this avoids runtime model path ambiguity.
  Date: 2026-05-02

- Decision: Implement prediction as a real CLI, not notebook-derived global constants.
  Reason: Nextflow needs configurable input/output paths, threads, and failure behavior.
  Date: 2026-05-02

## Milestones

### Milestone 1 — Define Pipeline Contract

Goal:

Document and freeze params before implementation.

Edits:
- `nuxplore-cell-type-prediction/params.example.yaml`: define mirrored-root and samplesheet examples, output directory, workers, GPU flag, crop flags, model paths, missing-feature failure behavior, and container image.
- `nuxplore-cell-type-prediction/docs/usage.md`: document invocation, expected input layouts, outputs, and assumptions.

Proposed params:

```yaml
image_root: null
mat_root: null
samplesheet: null
input_mode: roots
outdir: results/celltype
recursive: true
image_exts: .png,.jpg,.jpeg,.tif,.tiff,.bmp
workers: 4
max_images: null
skip_existing: false
mat_key: null
inst_type_key: inst_type
padding: 10
use_gpu: false
save_crops: true
save_pre_normalized_crops: true
save_post_normalized_crops: true
stain_normalization_features: true
model_path: /opt/nuxplore/models/Final_XGB_Model_FullData.pkl
encoder_path: /opt/nuxplore/models/final_label_encoder.pkl
container: docker.io/<owner>/<image>:<tag>
```

Validation:
- Manual review against resolved requirements.
- `nextflow config -profile docker` once config exists.

Risk:
- Samplesheet column names must be frozen early to avoid downstream churn.

### Milestone 2 — Translate Notebook Cell 0 to Python CLI

Goal:

Create an auditable predictor that annotates feature CSVs.

Edits:
- `nuxplore-cell-type-prediction/bin/cell_type_predict.py`: implement CLI.
- Optional `tests/test_cell_type_predict.py`: unit tests using a small fake model/encoder or monkeypatched predictor.

CLI shape:

```bash
cell_type_predict.py \
  --input-features /work/features \
  --output-dir /work/predictions \
  --model /opt/nuxplore/models/Final_XGB_Model_FullData.pkl \
  --encoder /opt/nuxplore/models/final_label_encoder.pkl \
  --workers 4
```

Implementation details:
- Load model and encoder once per process.
- Read `.csv` recursively and mirror relative output paths.
- Use `model.get_booster().feature_names` as authoritative feature order.
- Validate missing columns and empty CSVs.
- Add `Predicted_Label` and `Confidence_Score`.
- Emit a manifest JSON/CSV with processed, skipped, and failed files.
- Use `threadpoolctl.threadpool_limits(limits=workers)` and optionally `os.sched_setaffinity` on Linux.
- Return non-zero with a descriptive error if expected feature columns are missing.

Validation:
- `python -m py_compile nuxplore-cell-type-prediction/bin/cell_type_predict.py`
- Unit test for feature alignment, output columns, and failure behavior.
- Smoke test on a tiny CSV if representative feature columns can be generated.

Risk:
- Loading the pickled XGBoost model requires compatible `xgboost`, `scikit-learn`, `joblib`, `numpy`, and Python versions.

### Milestone 3 — Define Docker Image Contract

Goal:

Define how the pipeline consumes the DockerHub image that includes NuXplore, the predictor CLI, dependencies, and model artifacts.

Edits:
- `nuxplore-cell-type-prediction/nextflow.config`: make image configurable through `params.container`.
- `nuxplore-cell-type-prediction/docs/usage.md`: document expected image contents and DockerHub override.

Proposed design:
- DockerHub image name is TBD and remains a required/overridable parameter.
- Image must provide `python -m nuxplore.batch`.
- Image must provide `cell_type_predict.py` on `PATH`.
- Image must include model files at `/opt/nuxplore/models/Final_XGB_Model_FullData.pkl` and `/opt/nuxplore/models/final_label_encoder.pkl`.

Validation:
- `docker run --rm <image> python -c "import nuxplore, xgboost, sklearn, pandas"`
- `docker run --rm <image> python -m nuxplore.batch --help`
- `docker run --rm <image> cell_type_predict.py --help`

Risk:
- `xgboost` wheels can increase image size.
- Pickle compatibility may require matching dependency versions from the training environment; inspect model metadata during implementation.

### Milestone 4 — Implement Nextflow DSL2 Workflow

Goal:

Make `nextflow run` orchestrate extraction and prediction inside the Docker image.

Edits:
- `nuxplore-cell-type-prediction/main.nf`: DSL2 workflow.
- `nuxplore-cell-type-prediction/nextflow.config`: params, Docker profile, process resources, reports/traces.
- `nuxplore-cell-type-prediction/conf/docker.config`: optional profile split if config grows.
- `nuxplore-cell-type-prediction/bin/samplesheet_to_pairs.py`: validate samplesheet and stage/mirror pairs if needed.

Process design:

1. `EXTRACT_FEATURES`
   - Input: either image/MAT roots or a validated samplesheet with image/MAT pairs.
   - Command: `python -m nuxplore.batch --image-root ... --mat-root ... --output-csv-root features --output-nuclei-root nuclei ...`
   - Output: `features/`, optional `nuclei/`, extraction log.

2. `PREDICT_CELL_TYPES`
   - Input: extracted `features/` directory.
   - Command: `cell_type_predict.py --input-features features --output-dir predictions --model ... --encoder ...`
   - Output: `predictions/`, prediction manifest.

3. Workflow publishes:
   - `${params.outdir}/features`
   - `${params.outdir}/predictions`
   - `${params.outdir}/nuclei` when crops are enabled
   - `${params.outdir}/logs`

Validation:
- `nextflow run main.nf --help` if help block is implemented.
- `nextflow run main.nf -profile docker -params-file params.example.yaml` on a tiny fixture.
- `nextflow run main.nf --image_root <fixture_images> --mat_root <fixture_mats> --outdir results/test -profile docker`.
- `nextflow run main.nf --samplesheet <fixture_samplesheet.csv> --outdir results/test -profile docker`.

Risk:
- Supporting both root and samplesheet modes requires clear validation to prevent ambiguous input params.

### Milestone 5 — Add Fixtures and End-to-End Validation

Goal:

Prove the container and workflow work with minimal representative data.

Edits:
- `nuxplore-cell-type-prediction/tests/fixtures/`: tiny image/MAT pair and samplesheet if license-safe.
- `tests/test_pipeline_contract.py` or shell smoke test script if Python test framework is preferred.

Validation:
- Pull or reference the DockerHub image chosen by the user.
- Run NuXplore extraction on fixture.
- Run prediction on extracted CSV.
- Run full Nextflow pipeline with Docker profile.
- Confirm output CSVs contain `Predicted_Label` and `Confidence_Score`.

Risk:
- If a tiny fixture does not produce every model-required feature, a model-compatible synthetic feature CSV may be needed for predictor tests while full extraction tests stay separate.

### Milestone 6 — Documentation and Release Hygiene

Goal:

Make the pipeline usable by someone without notebook context.

Edits:
- `nuxplore-cell-type-prediction/README.md` and `nuxplore-cell-type-prediction/docs/usage.md`: quickstart, params table, DockerHub image configuration, output layout, troubleshooting.
- `CHANGELOG.md`: add entry if repo adopts changelog for user-visible behavior.

Validation:
- Follow docs from a clean checkout.
- Confirm commands are copy-pasteable.

Risk:
- Docs can become stale if params change late; update docs after workflow validation.

## Implementation Notes

### Prediction CLI Error Policy

Recommended default behavior:

- Empty CSV: record as skipped in manifest; do not produce annotated CSV.
- Missing feature columns: fail with a descriptive error listing missing column names and the affected CSV.
- Model load failure: fail immediately.
- Per-file read/write failure: record failure and return non-zero at end.

This is stricter than the notebook and better for pipelines where silent omissions are dangerous.

### Dependency Pinning

Start with broad pins only if model compatibility is unknown:

```text
numpy
pandas
joblib
threadpoolctl
xgboost
scikit-learn
scipy
pillow
```

During implementation, load the pickle in a controlled environment and record exact versions that work. Then pin `xgboost` and `scikit-learn` at minimum, because pickle compatibility is sensitive.

### Nextflow Config Shape

Use conventional params in `nextflow.config`:

```groovy
params.image_root = null
params.mat_root = null
params.samplesheet = null
params.input_mode = 'roots'
params.outdir = 'results/celltype'
params.container = 'docker.io/<owner>/<image>:<tag>'

docker.enabled = false

profiles {
  docker {
    docker.enabled = true
    process.container = params.container
  }
}
```

Use `-params-file params.yaml` for full config and `--name value` flags for quick runs, matching current Nextflow docs.

### Samplesheet Contract

Use a CSV with one row per image/MAT pair. Proposed required columns:

```csv
sample_id,image_path,mat_path
case001,/data/images/case001/tile01.png,/data/mats/case001/tile01.mat
```

Optional columns can be added later for metadata, but v1 should keep the schema minimal.

## Validation Plan

- Unit tests:
  - Predictor feature alignment.
  - Missing feature behavior.
  - Label decoding and confidence output.
- Integration tests:
  - NuXplore batch extraction CLI on fixture.
  - Prediction CLI on generated or synthetic CSV.
- Container checks:
  - Import smoke test.
  - Predictor help command.
  - Model load command.
- Nextflow checks:
  - `nextflow config -profile docker`.
  - Full local Docker profile run on fixture.
- Performance checks:
  - Record runtime on a small representative cohort.
  - Defer optimization until measured bottlenecks exist.
- Regression checks:
  - Compare predictor output against notebook cell 0 on the same feature CSV.

## Recovery / Rollback

- Safe retry:
  - Delete only generated `results/`, `.nextflow*`, and Docker build artifacts after explicit confirmation.
  - Re-run Nextflow with `-resume` when process outputs are cacheable.
- Rollback:
  - Remove pipeline files without touching `nuxplore/src/` if implementation is isolated.
- Files to inspect if validation fails:
  - `work/*/.command.log`
  - `work/*/.command.err`
  - prediction manifest
  - extracted feature CSV headers
  - Docker image dependency versions

## Completion Summary

Fill when complete.

Changed:
- N/A

Validated:
- N/A

New dependencies added:
- Planned: `xgboost`, `scikit-learn`, `joblib`, `pandas`, `threadpoolctl`; exact versions pending model-load validation.

Remaining:
- Resolve open questions before implementation.

Lessons:
- N/A

## CHANGELOG.md Entry

Draft final entry:

Add Dockerized Nextflow cell-type prediction pipeline
Creates a reproducible workflow for NuXplore feature extraction and XGBoost cell-type annotation.
Reason: enables `nextflow run` execution with baked models and featurizer.
