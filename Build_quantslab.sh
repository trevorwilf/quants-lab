#!/usr/bin/env bash
# =============================================================================
# Build_quantslab.sh
#
# Builds the custom quants-lab Docker image from the local repo.
# Run this from the ROOT of the quants-lab repository.
#
# Usage:
#   chmod +x Build_quantslab.sh
#   ./Build_quantslab.sh
#
# Options:
#   --no-cache    Force a full rebuild (skip Docker layer cache)
#   --gpu         Also install CUDA/cupy/numba-cuda into the image
# =============================================================================
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
IMAGE_NAME="hummingbot/quants-lab"
IMAGE_TAG="desktop"
FULL_TAG="${IMAGE_NAME}:${IMAGE_TAG}"
DOCKERFILE="Dockerfile"

# ── Parse arguments ───────────────────────────────────────────────────────────
DOCKER_BUILD_ARGS=""
INSTALL_GPU="false"

for arg in "$@"; do
    case "$arg" in
        --no-cache)  DOCKER_BUILD_ARGS="--no-cache" ;;
        --gpu)       INSTALL_GPU="true" ;;
        *)           echo "Unknown argument: $arg"; exit 1 ;;
    esac
done

# ── Pre-flight checks ────────────────────────────────────────────────────────
echo "============================================================"
echo "  Quants-Lab Docker Image Builder"
echo "============================================================"
echo ""

# Must be run from repo root
if [ ! -f "Dockerfile" ]; then
    echo "ERROR: Dockerfile not found in current directory."
    echo "       Run this script from the root of the quants-lab repo."
    exit 1
fi

if [ ! -f "environment.yml" ]; then
    echo "ERROR: environment.yml not found. Are you in the quants-lab repo root?"
    exit 1
fi

if [ ! -d "core" ]; then
    echo "ERROR: core/ directory not found. Are you in the quants-lab repo root?"
    exit 1
fi

if [ ! -f "cli.py" ]; then
    echo "ERROR: cli.py not found. Are you in the quants-lab repo root?"
    exit 1
fi

# Docker must be available
if ! command -v docker &>/dev/null; then
    echo "ERROR: docker is not installed or not in PATH."
    exit 1
fi

echo "  Image tag:    ${FULL_TAG}"
echo "  Dockerfile:   ${DOCKERFILE}"
echo "  No-cache:     ${DOCKER_BUILD_ARGS:-no}"
echo "  GPU build:    ${INSTALL_GPU}"
echo ""

# ── Build ─────────────────────────────────────────────────────────────────────
echo ">>> Building image: ${FULL_TAG} ..."
echo ""

docker build \
    ${DOCKER_BUILD_ARGS} \
    -f "${DOCKERFILE}" \
    -t "${FULL_TAG}" \
    .

echo ""
echo ">>> Base image built successfully."

# ── GPU overlay (optional) ────────────────────────────────────────────────────
if [ "${INSTALL_GPU}" = "true" ]; then
    echo ""
    echo ">>> Installing GPU packages (cupy-cuda12x, numba-cuda) ..."

    GPU_DOCKERFILE=$(mktemp /tmp/Dockerfile.gpu.XXXXXX)
    cat > "${GPU_DOCKERFILE}" <<'GPUEOF'
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
SHELL ["conda", "run", "-n", "quants-lab", "/bin/bash", "-c"]
RUN pip install --no-cache-dir "cupy-cuda12x[ctk]" "numba-cuda[cu12]"
GPUEOF

    docker build \
        ${DOCKER_BUILD_ARGS} \
        --build-arg BASE_IMAGE="${FULL_TAG}" \
        -f "${GPU_DOCKERFILE}" \
        -t "${FULL_TAG}" \
        .

    rm -f "${GPU_DOCKERFILE}"
    echo ">>> GPU packages installed."
fi

# ── Verify ────────────────────────────────────────────────────────────────────
echo ""
echo ">>> Verifying image ..."

# Check conda env exists
docker run --rm "${FULL_TAG}" conda run -n quants-lab python -c "
import sys
print(f'  Python:     {sys.version}')
"

# Check critical imports
docker run --rm "${FULL_TAG}" conda run -n quants-lab python -c "
import hummingbot; print(f'  hummingbot:  OK')
import optuna;     print(f'  optuna:      OK')
import psycopg2;   print(f'  psycopg2:    OK')
import pymongo;    print(f'  pymongo:     OK')
import pandas;     print(f'  pandas:      OK')
import plotly;     print(f'  plotly:      OK')
" 2>/dev/null || {
    echo ""
    echo "WARNING: Some imports failed. The image built but may be missing packages."
    echo "         This can happen if upstream packages changed. Check environment.yml."
}

echo ""
echo "============================================================"
echo "  BUILD COMPLETE"
echo "  Image: ${FULL_TAG}"
echo ""
echo "  Next steps:"
echo "    docker compose -f quantslab_desktop_compose.yaml up -d"
echo "============================================================"
