#!/usr/bin/env bash
set -euo pipefail

readonly RELEASE_BASE_URL="https://github.com/the-ahuja-lab/NucXplore/releases/download/demo-data-v1"
readonly SVS_NAME="GTEX-1117F-0126.svs"
readonly SVS_SHA256="d15569bc5c725a7635692376df34733bbd7fa2288db7e8a271d70b177e80cd93"
readonly ZIP_NAME="Sample_To_Test_Package.zip"
readonly ZIP_SHA256="b571e9eaecf57a11db4f84ab7f0becaaf48b571e25c36ccc00ba9279c8a6987a"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

usage() {
    cat <<'EOF'
Usage:
  run_demo.sh full [OPTIONS]
  run_demo.sh intermediate [OPTIONS]

Modes:
  full          Run crop -> segmentation -> features -> prediction on the SVS.
  intermediate  Run features -> prediction on the packaged PNG/MAT pairs.

Options:
  --run-dir DIR    Data, work, and results directory
                   [default: ./nucxplore-demo/<mode>]
  --asset-dir DIR  Use already-downloaded assets from DIR instead of GitHub
  --device MODE    Segmentation device for full mode: cpu or cuda [default: cpu]
  --resume         Resume the previous Nextflow run in the selected run directory
  -h, --help       Show this help

Requirements: Nextflow 25.04.7+, Java 17+, micromamba/Conda environment
`nucxplore-local`, Docker, curl (unless --asset-dir is used), sha256sum, and
unzip for intermediate mode.
EOF
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

verify_sha256() {
    local file_path="$1"
    local expected="$2"
    local actual
    actual="$(sha256sum "$file_path" | awk '{print $1}')"
    [[ "$actual" == "$expected" ]] || die "Checksum mismatch for $file_path (expected $expected, got $actual)"
}

download_asset() {
    local name="$1"
    local expected_sha="$2"
    local destination="$DATA_DIR/$name"

    if [[ -n "$ASSET_DIR" ]]; then
        destination="$ASSET_DIR/$name"
        [[ -f "$destination" ]] || die "Asset not found: $destination"
    elif [[ ! -f "$destination" ]]; then
        require_command curl
        local partial="$destination.part"
        printf 'Downloading %s\n' "$name" >&2
        curl --fail --location --retry 3 --output "$partial" "$RELEASE_BASE_URL/$name"
        mv -- "$partial" "$destination"
    fi

    verify_sha256 "$destination" "$expected_sha"
    printf '%s\n' "$destination"
}

validate_intermediate_pairs() {
    local image_root="$1"
    local mat_root="$2"
    local image_count=0
    local mat_count=0
    local image_path stem

    [[ -d "$image_root" ]] || die "CroppedTiles directory not found after extraction: $image_root"
    [[ -d "$mat_root" ]] || die "SegmentedFile directory not found after extraction: $mat_root"

    while IFS= read -r -d '' image_path; do
        image_count=$((image_count + 1))
        stem="$(basename "${image_path%.*}")"
        [[ -f "$mat_root/$stem.mat" ]] || die "Missing MAT pair for $(basename "$image_path")"
    done < <(find "$image_root" -maxdepth 1 -type f -iname '*.png' -print0)

    while IFS= read -r -d '' _; do
        mat_count=$((mat_count + 1))
    done < <(find "$mat_root" -maxdepth 1 -type f -iname '*.mat' -print0)

    [[ "$image_count" -eq 8 ]] || die "Expected 8 PNG inputs, found $image_count"
    [[ "$mat_count" -eq 8 ]] || die "Expected 8 MAT inputs, found $mat_count"
}

[[ $# -ge 1 ]] || { usage >&2; exit 1; }

MODE="$1"
shift
[[ "$MODE" == "full" || "$MODE" == "intermediate" ]] || die "Invalid mode '$MODE'; expected full or intermediate"

RUN_DIR=""
ASSET_DIR=""
DEVICE="cpu"
RESUME=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --run-dir)
            [[ $# -ge 2 ]] || die "--run-dir requires a value"
            RUN_DIR="$2"
            shift 2
            ;;
        --asset-dir)
            [[ $# -ge 2 ]] || die "--asset-dir requires a value"
            ASSET_DIR="$2"
            shift 2
            ;;
        --device)
            [[ $# -ge 2 ]] || die "--device requires cpu or cuda"
            DEVICE="$2"
            shift 2
            ;;
        --resume)
            RESUME=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

[[ "$DEVICE" == "cpu" || "$DEVICE" == "cuda" ]] || die "Invalid device '$DEVICE'; expected cpu or cuda"
[[ "$MODE" == "full" || "$DEVICE" == "cpu" ]] || die "--device applies only to full mode"

require_command nextflow
require_command sha256sum
require_command conda

if ! conda run -n nucxplore-local python -c \
    'import importlib.metadata as m, nucxplore.batch as b; assert m.version("nucxplore") == "0.3.0"; assert hasattr(b, "V2_FEATURE_COLUMNS")' \
    >/dev/null 2>&1; then
    die "Conda environment 'nucxplore-local' is missing or incompatible; recreate it from $PIPELINE_DIR/environment.yml"
fi

if [[ -z "$RUN_DIR" ]]; then
    RUN_DIR="$PWD/nucxplore-demo/$MODE"
fi
RUN_DIR="$(mkdir -p "$RUN_DIR" && cd "$RUN_DIR" && pwd)"
DATA_DIR="$RUN_DIR/data"
RESULTS_DIR="$RUN_DIR/results"
WORK_DIR="$RUN_DIR/work"
mkdir -p "$DATA_DIR" "$RESULTS_DIR" "$WORK_DIR"

if [[ -n "$ASSET_DIR" ]]; then
    ASSET_DIR="$(cd "$ASSET_DIR" 2>/dev/null && pwd)" || die "Asset directory not found: $ASSET_DIR"
fi

NEXTFLOW_ARGS=(run "$PIPELINE_DIR" -w "$WORK_DIR")
if [[ "$RESUME" == true ]]; then
    NEXTFLOW_ARGS+=(-resume)
fi

if [[ "$MODE" == "full" ]]; then
    svs_path="$(download_asset "$SVS_NAME" "$SVS_SHA256")"
    slide_root="$(dirname "$svs_path")"
    if [[ -n "$ASSET_DIR" ]]; then
        slide_root="$DATA_DIR/slides"
        mkdir -p "$slide_root"
        ln -sfn "$svs_path" "$slide_root/$SVS_NAME"
    fi
    seg_devices=0
    if [[ "$DEVICE" == "cuda" ]]; then
        seg_devices=1
    fi
    NEXTFLOW_ARGS+=(
        -params-file "$SCRIPT_DIR/full.params.yaml"
        --slide_root "$slide_root"
        --outdir "$RESULTS_DIR"
        --seg_device "$DEVICE"
        --seg_n_devices "$seg_devices"
    )
else
    require_command unzip
    zip_path="$(download_asset "$ZIP_NAME" "$ZIP_SHA256")"
    unzip -oq "$zip_path" -d "$DATA_DIR"
    image_root="$DATA_DIR/Sample_To_Test_Package/CroppedTiles"
    mat_root="$DATA_DIR/Sample_To_Test_Package/SegmentedFile"
    validate_intermediate_pairs "$image_root" "$mat_root"
    NEXTFLOW_ARGS+=(
        -params-file "$SCRIPT_DIR/intermediate.params.yaml"
        --image_root "$image_root"
        --mat_root "$mat_root"
        --outdir "$RESULTS_DIR"
    )
fi

printf 'Mode: %s\nRun directory: %s\nResults: %s\n' "$MODE" "$RUN_DIR" "$RESULTS_DIR"
nextflow "${NEXTFLOW_ARGS[@]}"
