#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SEG_IMAGE="${SEG_IMAGE:-ahujalab/nucxplore-seg:latest}"
PRED_IMAGE="${PRED_IMAGE:-ahujalab/nucxplore-cell-type-prediction:latest}"

cd "$REPO_ROOT"

docker build \
  -f nucxplore-pipeline/Dockerfile.nucxplore-seg \
  -t "$SEG_IMAGE" \
  .

docker build \
  -f nucxplore-pipeline/Dockerfile \
  -t "$PRED_IMAGE" \
  .

printf 'Built images:\n  %s\n  %s\n' "$SEG_IMAGE" "$PRED_IMAGE"
