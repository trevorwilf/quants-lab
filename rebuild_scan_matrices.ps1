#!/usr/bin/env pwsh
# rebuild_scan_matrices.ps1
#
# Rebuild the bowaka_v2 SIP scan matrices (validation + holdout) used by the
# vectorized walk-forward studies and the top-N robustness/holdout sweep.
#
# Runs INSIDE the ql-jupyter container (which holds the quants-lab conda env).
# The matrices are a rebuildable cache on the container overlay
# (/opt/scan_matrix_cache/sip/{validation,holdout}); this script regenerates
# them from the current SIP lake. Intended to be scheduled WEEKLY so the
# matrices stay in sync with the nightly market-data backfill.
#
#   .\rebuild_scan_matrices.ps1                 # SIP val + holdout, verify each
#   .\rebuild_scan_matrices.ps1 -Workers 10     # override worker count
#   .\rebuild_scan_matrices.ps1 -Config configs/_local_container_matrix_sip.yml
#
# Register as a weekly Windows scheduled task (Saturday 02:00, your user):
#   schtasks /Create /TN "bowaka_v2 SIP scan-matrix rebuild" /SC WEEKLY /D SAT /ST 02:00 `
#     /TR "pwsh -NoProfile -ExecutionPolicy Bypass -File E:\tradingsoftware\quants-lab\rebuild_scan_matrices.ps1"
#
# Schedule it for a window when NO study is running — a rebuild overwrites the
# store a running study reads from. Requires SIP bars present in the lake
# (build fails loud otherwise).
#
param(
    [string]$Config    = "configs/_local_container_matrix_sip.yml",
    [int]   $Workers   = 8,
    [string]$StoreBase = "/opt/scan_matrix_cache/sip"
)
$ErrorActionPreference = "Stop"
$Container = "ql-jupyter"

$running = docker ps --filter "name=$Container" --filter "status=running" --format "{{.Names}}"
if ($running -ne $Container) {
    Write-Error "Container '$Container' is not running. Start the stack first:`n  docker compose -f quantslab_desktop_compose.yaml up -d"
    exit 1
}

# MARKET_DATA_ROOT is exported INSIDE the container, NOT via `docker exec -e`:
# Git Bash / MSYS on a Windows host rewrites a bare /opt/... argument into a
# Windows path (e.g. C:/Program Files/Git/opt/...), silently mis-targeting the
# lake. Exporting it inside the bash -lc string (one argument) avoids that.
$inner = @"
set -euo pipefail
export MARKET_DATA_ROOT=/opt/market_data_cache
export PYTHONPATH=src:../bowaka_common/src
cd /quants-lab/research_notebooks/bowaka_v2_lab
mkdir -p artifacts/cache/scan_matrix/build_logs
PY=/opt/conda/envs/quants-lab/bin/python
echo "[rebuild] start `$(date -u +%FT%TZ)  config=$Config  workers=$Workers  store=$StoreBase"
for scope in validation holdout; do
  echo "[rebuild] ===== build `$scope ====="
  `$PY -m bowaka_v2_lab.cli scan-matrix build  --config $Config --scope `$scope --workers $Workers --store-root $StoreBase/`$scope
  echo "[rebuild] ===== verify `$scope ====="
  `$PY -m bowaka_v2_lab.cli scan-matrix verify --config $Config --store-root $StoreBase/`$scope --vectorized-check
done
echo "[rebuild] DONE `$(date -u +%FT%TZ)"
"@

$ts      = Get-Date -Format "yyyyMMdd_HHmmss"
$hostLog = Join-Path $PSScriptRoot "rebuild_scan_matrices_$ts.log"
Write-Host "Rebuilding SIP scan matrices (validation + holdout) -> $StoreBase"
Write-Host "Log: $hostLog"
docker exec $Container bash -lc $inner 2>&1 | Tee-Object -FilePath $hostLog
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Error "scan-matrix rebuild FAILED (exit $code) - see $hostLog"
}
exit $code
