#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SVS_PATH="${1:-/storage2/iqr_dna/nuxplore_pipeline/nuxplore_project/GTEX-1117F-0126.svs}"
RUN_ROOT="${RUN_ROOT:-$HOME/nucxplore_pipeline_runs/$(date +%Y%m%d_%H%M%S)}"
NEXTFLOW_BIN="${NEXTFLOW_BIN:-/home/iqr/micromamba/envs/nextflow/bin/nextflow}"
NEXTFLOW_ENV_BIN="$(dirname "$NEXTFLOW_BIN")"

CROP_IMAGE="${CROP_IMAGE:-ahujalab/nucxplore-crop-filter:latest}"
SEG_IMAGE="${SEG_IMAGE:-ahujalab/nucxplore-rgci-seg:latest}"
PRED_IMAGE="${PRED_IMAGE:-ahujalab/nucxplore-cell-type-prediction:latest}"

if [[ ! -f "$SVS_PATH" ]]; then
  printf 'SVS file not found: %s\n' "$SVS_PATH" >&2
  exit 1
fi

if [[ ! -x "$NEXTFLOW_BIN" ]]; then
  printf 'Nextflow not found or not executable: %s\n' "$NEXTFLOW_BIN" >&2
  printf 'Set NEXTFLOW_BIN or use /home/iqr/micromamba/envs/nextflow/bin/nextflow.\n' >&2
  exit 1
fi

mkdir -p "$RUN_ROOT/nucxplore-pipeline/slides"
rm -rf "$RUN_ROOT/nucxplore-pipeline"
cp -a "$REPO_ROOT/nucxplore-pipeline" "$RUN_ROOT/nucxplore-pipeline"
mkdir -p "$RUN_ROOT/nucxplore-pipeline/slides"
cp "$SVS_PATH" "$RUN_ROOT/nucxplore-pipeline/slides/"

cat > "$RUN_ROOT/params.yaml" <<EOF
from_stage: crop
to_stage: prediction
slide_root: ./slides
outdir: ./results
slide_exts: .svs
tile_size: 1250
mean_threshold: 220
std_threshold: 15
drop_partial_tiles: true
seg_device: cpu
seg_n_devices: 0
crop_filter_container: $CROP_IMAGE
seg_container: $SEG_IMAGE
container: $PRED_IMAGE
fail_on_missing_model_features: true
publish_crops: true
publish_segmentation: true
workers: 4
EOF

printf 'Run root: %s\n' "$RUN_ROOT"
printf 'SVS: %s\n' "$SVS_PATH"
printf 'Nextflow: %s\n' "$NEXTFLOW_BIN"

export PATH="$NEXTFLOW_ENV_BIN:$PATH"
export JAVA_CMD="$NEXTFLOW_ENV_BIN/java"
unset JAVA_HOME

cd "$RUN_ROOT/nucxplore-pipeline"
"$NEXTFLOW_BIN" run . \
  -profile docker \
  -params-file "$RUN_ROOT/params.yaml" \
  -w "$RUN_ROOT/work"

printf '\nPipeline completed. Results: %s\n' "$RUN_ROOT/nucxplore-pipeline/results"
