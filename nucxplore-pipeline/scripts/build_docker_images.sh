#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CROP_IMAGE="${CROP_IMAGE:-ahujalab/nucxplore-crop-filter:latest}"
SEG_IMAGE="${SEG_IMAGE:-ahujalab/nucxplore-rgci-seg:latest}"
PRED_IMAGE="${PRED_IMAGE:-ahujalab/nucxplore-cell-type-prediction:latest}"

cd "$REPO_ROOT"

docker build \
  -f nucxplore-pipeline/Dockerfile.crop-filter \
  -t "$CROP_IMAGE" \
  .

docker build \
  -f nucxplore-pipeline/Dockerfile.rgci-seg \
  -t "$SEG_IMAGE" \
  .

docker build \
  -f nucxplore-pipeline/Dockerfile \
  -t "$PRED_IMAGE" \
  .

printf 'Built images:\n  %s\n  %s\n  %s\n' "$CROP_IMAGE" "$SEG_IMAGE" "$PRED_IMAGE"
