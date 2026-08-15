#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIPELINE_DIR="$REPO_ROOT"
FIXTURE_ROOT="$PIPELINE_DIR/tests/fixtures/celltype"
OUT_ROOT="/tmp/nucxplore_celltype_m5"

rm -rf "$OUT_ROOT"
mkdir -p "$OUT_ROOT"

pushd "$PIPELINE_DIR" >/dev/null

# Stub container images for containerized stages (segmentation + prediction).
SEG_IMG=stub/nucxplore-seg:latest
MAIN_IMG=stub/nucxplore-cell-type-prediction:latest

expect_failure_contains() {
  local expected="$1"
  shift
  local log_file="$OUT_ROOT/expected-failure.log"

  set +e
  "$@" >"$log_file" 2>&1
  local status=$?
  set -e

  if [[ "$status" -eq 0 ]]; then
    printf 'Expected command to fail: %s\n' "$*" >&2
    return 1
  fi
  if ! grep -Fq "$expected" "$log_file"; then
    printf 'Expected failure to contain: %s\n' "$expected" >&2
    cat "$log_file" >&2
    return 1
  fi
}

# ---- container validation: prediction stage rejects placeholder ----
expect_failure_contains "Prediction stage requires --container" \
  nextflow run main.nf -profile stub \
    -stub-run \
    --stage prediction \
    --features_root "$FIXTURE_ROOT/features" \
    --outdir "$OUT_ROOT/pred-placeholder" \
    --container 'docker.io/<owner>/nucxplore-cell-type-prediction:<tag>'

# ---- container validation: segmentation stage rejects placeholder ----
expect_failure_contains "Segmentation stage requires --seg_container" \
  nextflow run main.nf -profile stub \
    -stub-run \
    --stage segmentation \
    --seg_device cpu \
    --crop_root "$FIXTURE_ROOT/roots/images" \
    --outdir "$OUT_ROOT/seg-placeholder" \
    --seg_container 'docker.io/<owner>/nucxplore-seg:<tag>'

# ---- single-stage check (--stage features) ----
nextflow run main.nf -profile stub \
  -stub-run \
  --stage features \
  --input_mode roots \
  --image_root "$FIXTURE_ROOT/roots/images" \
  --mat_root "$FIXTURE_ROOT/roots/mats" \
  --outdir "$OUT_ROOT/features-only"

# ---- single-stage check (--stage crop) ----
nextflow run main.nf -profile stub \
  -stub-run \
  --stage crop \
  --slide_root "$FIXTURE_ROOT/slides" \
  --outdir "$OUT_ROOT/crop-only"

test -f "$OUT_ROOT/crop-only/logs/crop_manifest.json"
test -f "$OUT_ROOT/crop-only/logs/crop.log"

# ---- single-stage crop with second fixture ----
nextflow run main.nf -profile stub \
  -stub-run \
  --stage crop \
  --slide_root "$FIXTURE_ROOT/roots/images" \
  --outdir "$OUT_ROOT/crop-only-2"

# ---- single-stage check (--stage segmentation) ----
nextflow run main.nf -profile stub \
  -stub-run \
  --stage segmentation \
  --seg_device cpu \
  --crop_root "$FIXTURE_ROOT/roots/images" \
  --outdir "$OUT_ROOT/seg-only" \
  --seg_container "$SEG_IMG"

test -f "$OUT_ROOT/seg-only/logs/segmentation_manifest.json"
test -f "$OUT_ROOT/seg-only/logs/segment.log"

# ---- single-stage check (--stage prediction) ----
nextflow run main.nf -profile stub \
  -stub-run \
  --stage prediction \
  --features_root "$FIXTURE_ROOT/features" \
  --outdir "$OUT_ROOT/pred-only" \
  --container "$MAIN_IMG"

test -f "$OUT_ROOT/pred-only/logs/predict.log"

# ---- two-stage range (features -> prediction) with roots ----
nextflow run main.nf -profile stub \
  -stub-run \
  --from_stage features --to_stage prediction \
  --input_mode roots \
  --image_root "$FIXTURE_ROOT/roots/images" \
  --mat_root "$FIXTURE_ROOT/roots/mats" \
  --outdir "$OUT_ROOT/roots" \
  --container "$MAIN_IMG"

test -f "$OUT_ROOT/roots/logs/manifest.json"
test -f "$OUT_ROOT/roots/logs/manifest.csv"
test -f "$OUT_ROOT/roots/logs/predict.log"

# ---- two-stage range with samplesheet ----
nextflow run main.nf -profile stub \
  -stub-run \
  --from_stage features --to_stage prediction \
  --input_mode samplesheet \
  --samplesheet "$FIXTURE_ROOT/samplesheet.csv" \
  --outdir "$OUT_ROOT/samplesheet" \
  --container "$MAIN_IMG"

test -f "$OUT_ROOT/samplesheet/logs/prepare_inputs_manifest.json"
test -f "$OUT_ROOT/samplesheet/logs/manifest.json"
test -f "$OUT_ROOT/samplesheet/logs/manifest.csv"
test -f "$OUT_ROOT/samplesheet/logs/predict.log"

# ---- range: crop-to-segmentation ----
nextflow run main.nf -profile stub \
  -stub-run \
  --from_stage crop --to_stage segmentation \
  --seg_device cpu \
  --slide_root "$FIXTURE_ROOT/slides" \
  --outdir "$OUT_ROOT/crop-to-seg" \
  --seg_container "$SEG_IMG"

test -f "$OUT_ROOT/crop-to-seg/logs/crop_manifest.json"
test -f "$OUT_ROOT/crop-to-seg/logs/crop.log"
test -f "$OUT_ROOT/crop-to-seg/logs/segmentation_manifest.json"
test -f "$OUT_ROOT/crop-to-seg/logs/segment.log"

# ---- range: seg-to-features ----
nextflow run main.nf -profile stub \
  -stub-run \
  --from_stage segmentation --to_stage features \
  --crop_root "$FIXTURE_ROOT/roots/images" \
  --outdir "$OUT_ROOT/seg-to-features" \
  --seg_container "$SEG_IMG"

test -f "$OUT_ROOT/seg-to-features/logs/segmentation_manifest.json"
test -f "$OUT_ROOT/seg-to-features/logs/segment.log"

# ---- full pipeline (crop -> prediction) ----
nextflow run main.nf -profile stub \
  -stub-run \
  --from_stage crop --to_stage prediction \
  --slide_root "$FIXTURE_ROOT/slides" \
  --outdir "$OUT_ROOT/full" \
  --seg_container "$SEG_IMG" \
  --container "$MAIN_IMG"

test -f "$OUT_ROOT/full/logs/crop_manifest.json"
test -f "$OUT_ROOT/full/logs/crop.log"
test -f "$OUT_ROOT/full/logs/segmentation_manifest.json"
test -f "$OUT_ROOT/full/logs/segment.log"
test -f "$OUT_ROOT/full/logs/predict.log"
test -f "$OUT_ROOT/full/logs/manifest.json"
test -f "$OUT_ROOT/full/logs/manifest.csv"

popd >/dev/null

echo "OK milestone5 stub checks passed"
