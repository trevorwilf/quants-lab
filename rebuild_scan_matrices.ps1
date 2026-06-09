#!/usr/bin/env pwsh
# rebuild_scan_matrices.ps1
#
# Rebuild the bowaka_v2 scan matrices (validation + holdout) that notebook 10's
# walk-forward study and top-N holdout sweep consume.
#
# It resolves the SAME base config notebook 10 uses (configs/_local_container_matrix.yml)
# the SAME way (resolve_walkforward_config, feed auto-detected from the lake), then builds
# + verifies each scope at the store_root the fold-context resolves to. Building against
# the notebook's resolved config is REQUIRED so the matrix config-hash matches what the
# study/sweep checks (a matrix built from a different config is silently rejected).
#
# Runs INSIDE the ql-jupyter container. The matrices are a rebuildable cache on the
# container overlay; this regenerates them from the current lake.
#
#   .\rebuild_scan_matrices.ps1                 # default notebook config, 6 workers
#   .\rebuild_scan_matrices.ps1 -Workers 10
#   .\rebuild_scan_matrices.ps1 -Config configs/_local_container_matrix.yml
#
# DO NOT register a standalone scheduled task for this script. The weekly schedule is
# scheduled_weekly_refresh.ps1, which runs the lake refresh + this rebuild behind a
# STUDY GUARD. A rebuild OVERWRITES the matrix store a running study reads, so an
# unguarded scheduled rebuild can clobber a live multi-day study. Run this by hand
# only, when NO study/sweep is active (e.g. to clear a MATRICES_STALE.flag left by a
# deferred weekly run). Requires SIP (or IEX) bars in the lake (build fails loud).
#
param(
    [string]$Config  = "configs/_local_container_matrix.yml",
    [int]   $Workers = 6
)
$ErrorActionPreference = "Stop"
$Container = "ql-jupyter"

$running = docker ps --filter "name=$Container" --filter "status=running" --format "{{.Names}}"
if ($running -ne $Container) {
    Write-Error "Container '$Container' is not running. Start the stack first:`n  docker compose -f quantslab_desktop_compose.yaml up -d"
    exit 1
}

# MARKET_DATA_ROOT is exported INSIDE the container (NOT via `docker exec -e`): Git Bash /
# MSYS on a Windows host rewrites a bare /opt/... argument into a Windows path. The Python
# heredoc resolves the config + per-scope store roots exactly as notebook 10 does, then
# builds + verifies both scopes.
$inner = @"
set -euo pipefail
export MARKET_DATA_ROOT=/opt/market_data_cache
export PYTHONPATH=src:../bowaka_common/src
cd /quants-lab/research_notebooks/bowaka_v2_lab
echo "[rebuild] start config=$Config workers=$Workers"
/opt/conda/envs/quants-lab/bin/python - "$Config" "$Workers" <<'PYEOF'
import sys, subprocess
from bowaka_v2_lab.optuna.autoconfig import resolve_walkforward_config
from bowaka_v2_lab.scanner.scan_matrix import resolve_scan_matrix_store_root
from bowaka_v2_lab.config.loader import load_config

base, workers = sys.argv[1], sys.argv[2]
resolved = "/tmp/scan_matrix_rebuild_resolved.yml"
r = resolve_walkforward_config(base, feed_override="auto", out_path=resolved)
print(f"[rebuild] resolved feed={r.feed} mode={r.mode}", flush=True)
sm = load_config(resolved)["optuna"]["acceleration"]["scan_matrix"]
for scope in ("validation", "holdout"):
    root = str(resolve_scan_matrix_store_root(sm, scope))
    print(f"[rebuild] ===== build {scope} -> {root} =====", flush=True)
    subprocess.run([sys.executable, "-m", "bowaka_v2_lab.cli", "scan-matrix", "build",
                    "--config", resolved, "--scope", scope, "--workers", str(workers),
                    "--store-root", root], check=True)
    print(f"[rebuild] ===== verify {scope} =====", flush=True)
    subprocess.run([sys.executable, "-m", "bowaka_v2_lab.cli", "scan-matrix", "verify",
                    "--config", resolved, "--store-root", root, "--vectorized-check"], check=True)
print("[rebuild] DONE", flush=True)
PYEOF
"@

$ts      = Get-Date -Format "yyyyMMdd_HHmmss"
$hostLog = Join-Path $PSScriptRoot "rebuild_scan_matrices_$ts.log"
Write-Host "Rebuilding scan matrices (validation + holdout) for $Config"
Write-Host "Log: $hostLog"
# `bash -lc` mis-parses CR in a multi-line script: CRLF breaks the embedded
# heredoc (the closing `PYEOF\r` never matches `PYEOF`, so the build silently
# no-ops and exits 0). Normalize to LF before handing the script to the container.
$inner = $inner -replace "`r", ""
docker exec $Container bash -lc $inner 2>&1 | Tee-Object -FilePath $hostLog
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Error "scan-matrix rebuild FAILED (exit $code) - see $hostLog"
}
exit $code
