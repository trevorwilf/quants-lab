# =============================================================================
# Build_quantslab.ps1
#
# Builds the custom quants-lab Docker image from the local repo.
# Run this from the ROOT of the quants-lab repository.
#
# Usage:
#   .\Build_quantslab.ps1
#   .\Build_quantslab.ps1 -NoCache
#   .\Build_quantslab.ps1 -Gpu
#   .\Build_quantslab.ps1 -NoCache -Gpu
# =============================================================================

param(
    [switch]$NoCache,
    [switch]$Gpu
)

$ErrorActionPreference = "Stop"

# ── Configuration ─────────────────────────────────────────────────────────────
$ImageName  = "hummingbot/quants-lab"
$ImageTag   = "desktop"
$FullTag    = "${ImageName}:${ImageTag}"
$Dockerfile = "Dockerfile"

# ── Pre-flight checks ────────────────────────────────────────────────────────
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Quants-Lab Docker Image Builder" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Must be run from repo root
if (-not (Test-Path "Dockerfile")) {
    Write-Host "ERROR: Dockerfile not found in current directory." -ForegroundColor Red
    Write-Host "       Run this script from the root of the quants-lab repo." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "environment.yml")) {
    Write-Host "ERROR: environment.yml not found." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "core" -PathType Container)) {
    Write-Host "ERROR: core/ directory not found." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "cli.py")) {
    Write-Host "ERROR: cli.py not found." -ForegroundColor Red
    exit 1
}

# Docker must be available
try {
    docker version | Out-Null
} catch {
    Write-Host "ERROR: docker is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

Write-Host "  Image tag:    $FullTag"
Write-Host "  Dockerfile:   $Dockerfile"
Write-Host "  No-cache:     $NoCache"
Write-Host "  GPU build:    $Gpu"
Write-Host ""

# ── Build ─────────────────────────────────────────────────────────────────────
Write-Host ">>> Building image: $FullTag ..." -ForegroundColor Yellow
Write-Host ""

$buildArgs = @("-f", $Dockerfile, "-t", $FullTag, ".")
if ($NoCache) {
    $buildArgs = @("--no-cache") + $buildArgs
}

docker build @buildArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host ">>> Base image built successfully." -ForegroundColor Green

# ── GPU overlay (optional) ────────────────────────────────────────────────────
if ($Gpu) {
    Write-Host ""
    Write-Host ">>> Installing GPU packages (cupy-cuda12x, numba-cuda) ..." -ForegroundColor Yellow

    $gpuDockerfile = [System.IO.Path]::GetTempFileName()
    @"
ARG BASE_IMAGE
FROM `${BASE_IMAGE}
SHELL ["conda", "run", "-n", "quants-lab", "/bin/bash", "-c"]
RUN pip install --no-cache-dir "cupy-cuda12x[ctk]" "numba-cuda[cu12]"
"@ | Set-Content -Path $gpuDockerfile -Encoding UTF8

    $gpuBuildArgs = @("--build-arg", "BASE_IMAGE=$FullTag", "-f", $gpuDockerfile, "-t", $FullTag, ".")
    if ($NoCache) {
        $gpuBuildArgs = @("--no-cache") + $gpuBuildArgs
    }

    docker build @gpuBuildArgs
    if ($LASTEXITCODE -ne 0) {
        Remove-Item -Path $gpuDockerfile -Force -ErrorAction SilentlyContinue
        Write-Host "ERROR: GPU overlay build failed." -ForegroundColor Red
        exit 1
    }

    Remove-Item -Path $gpuDockerfile -Force -ErrorAction SilentlyContinue
    Write-Host ">>> GPU packages installed." -ForegroundColor Green
}

# ── Verify ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host ">>> Verifying image ..." -ForegroundColor Yellow

docker run --rm $FullTag conda run -n quants-lab python -c @"
import sys
print(f'  Python:     {sys.version}')
"@

docker run --rm $FullTag conda run -n quants-lab python -c @"
import hummingbot; print('  hummingbot:  OK')
import optuna;     print('  optuna:      OK')
import psycopg2;   print('  psycopg2:    OK')
import pymongo;    print('  pymongo:     OK')
import pandas;     print('  pandas:      OK')
import plotly;     print('  plotly:      OK')
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Some imports failed. Check environment.yml." -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  BUILD COMPLETE" -ForegroundColor Green
Write-Host "  Image: $FullTag" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:"
Write-Host "    docker compose -f quantslab_desktop_compose.yaml up -d"
Write-Host "============================================================" -ForegroundColor Cyan
