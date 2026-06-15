#!/usr/bin/env pwsh
# rebuild_scan_matrices.ps1
#
# Rebuild the bowaka_v2 scan matrices that notebook 10's walk-forward study + top-N holdout
# sweep consume. By default it rebuilds BOTH active matrix families (they are DISTINCT
# matrices -- different windows / walk-forward -- so both must be built):
#   * IR  (intended_realism)  configs/_local_container_matrix.yml
#                             -> /opt/scan_matrix_cache/validation[/holdout]
#   * fast_realism            configs/_fastrealism_study.yml
#                             -> /opt/scan_matrix_cache/fast_realism/validation[/holdout]
#
# For each config it resolves the SAME way the study/sweep does (resolve_walkforward_config,
# feed auto-detected from the lake), PRESERVING the config's simulation mode: a config whose
# simulation.mode == fast_realism is resolved with mode_override=fast_realism (plain feed=auto
# on the SIP lake would otherwise auto-derive intended_realism + mismatch the matrix hash);
# every other config resolves under auto (-> intended_realism on the SIP lake). Building
# against the resolved config is REQUIRED so the matrix config-hash matches what the study/
# sweep checks (a matrix built from a different config is silently rejected). Each config is
# resolved to its OWN /tmp file -- the source configs are never modified.
#
# Runs INSIDE the ql-jupyter container. The matrices are a rebuildable cache on the persistent
# ql_scan_matrix Docker volume (mounted at /opt/scan_matrix_cache); this regenerates them from
# the CURRENT lake -- so the latest bars/quotes AND corporate-actions (survivorship) are baked
# into the rebuilt matrices.
#
#   .\rebuild_scan_matrices.ps1                                          # IR + fast_realism, 6 workers
#   .\rebuild_scan_matrices.ps1 -Workers 10
#   .\rebuild_scan_matrices.ps1 -Configs configs/_fastrealism_study.yml  # just one family
#
# DO NOT register a standalone scheduled task for this script. The weekly schedule is
# scheduled_weekly_refresh.ps1, which runs the lake refresh + this rebuild behind a STUDY
# GUARD. A rebuild OVERWRITES the matrix store a running study reads, so an unguarded scheduled
# rebuild can clobber a live multi-day study. Run this by hand only, when NO study/sweep is
# active. Requires SIP (or IEX) bars in the lake (build fails loud).
#
param(
    [string[]]$Configs = @("configs/_local_container_matrix.yml", "configs/_fastrealism_study.yml"),
    [int]     $Workers = 6
)
$ErrorActionPreference = "Stop"
$Container = "ql-jupyter"

$running = docker ps --filter "name=$Container" --filter "status=running" --format "{{.Names}}"
if ($running -ne $Container) {
    Write-Error "Container '$Container' is not running. Start the stack first:`n  docker compose -f quantslab_desktop_compose.yaml up -d"
    exit 1
}

# Guard: matrices must land on the persistent ql_scan_matrix volume, not the container overlay
# (the overlay is wiped on recreate). Warn loudly if not (a named volume is its own /proc/mounts entry).
$mtxBacking = (docker exec $Container sh -c "grep -q ' /opt/scan_matrix_cache ' /proc/mounts && echo VOLUME || echo OVERLAY" 2>&1 | Out-String).Trim()
if ($mtxBacking -ne "VOLUME") {
    Write-Warning "[rebuild] /opt/scan_matrix_cache is NOT a mounted volume (backing=$mtxBacking) -- matrices would be on the ephemeral overlay (lost on recreate). Mount ql_scan_matrix (see quantslab_desktop_compose.yaml)."
}

$cfgArgs = ($Configs | ForEach-Object { '"' + $_ + '"' }) -join ' '

# MARKET_DATA_ROOT exported INSIDE the container (MSYS rewrites a bare /opt/... -e arg on a
# Windows host). The python heredoc resolves EACH config + its per-scope store root exactly as
# the study/sweep does, then builds + verifies both scopes for each config.
$inner = @"
set -euo pipefail
export MARKET_DATA_ROOT=/opt/market_data_cache
export PYTHONPATH=src:../bowaka_common/src
cd /quants-lab/research_notebooks/bowaka_v2_lab
echo "[rebuild] configs=$cfgArgs workers=$Workers"
/opt/conda/envs/quants-lab/bin/python - "$Workers" $cfgArgs <<'PYEOF'
import sys, subprocess
from bowaka_v2_lab.optuna.autoconfig import resolve_walkforward_config
from bowaka_v2_lab.scanner.scan_matrix import resolve_scan_matrix_store_root
from bowaka_v2_lab.config.loader import load_config

workers = sys.argv[1]
configs = sys.argv[2:]
for i, base in enumerate(configs):
    raw = load_config(base)
    declared = (raw.get("simulation") or {}).get("mode")
    out_path = f"/tmp/scan_matrix_rebuild_{i}.yml"
    kwargs = {"feed_override": "auto", "out_path": out_path}
    if declared == "fast_realism":
        kwargs["mode_override"] = "fast_realism"
    r = resolve_walkforward_config(base, **kwargs)
    print(f"[rebuild] ===== {base}: feed={r.feed} mode={r.mode} =====", flush=True)
    sm = load_config(out_path)["optuna"]["acceleration"]["scan_matrix"]
    for scope in ("validation", "holdout"):
        root = str(resolve_scan_matrix_store_root(sm, scope))
        print(f"[rebuild] build {base} {scope} -> {root}", flush=True)
        subprocess.run([sys.executable, "-m", "bowaka_v2_lab.cli", "scan-matrix", "build",
                        "--config", out_path, "--scope", scope, "--workers", str(workers),
                        "--store-root", root], check=True)
        print(f"[rebuild] verify {base} {scope}", flush=True)
        subprocess.run([sys.executable, "-m", "bowaka_v2_lab.cli", "scan-matrix", "verify",
                        "--config", out_path, "--store-root", root, "--vectorized-check"], check=True)
print("[rebuild] DONE all configs", flush=True)
PYEOF
"@

$ts      = Get-Date -Format "yyyyMMdd_HHmmss"
$hostLog = Join-Path $PSScriptRoot "rebuild_scan_matrices_$ts.log"
Write-Host "Rebuilding scan matrices for: $($Configs -join ', ')"
Write-Host "Log: $hostLog"
# bash -lc mis-parses CR: CRLF breaks the embedded heredoc (closing PYEOF\r never matches PYEOF).
$inner = $inner -replace "`r", ""
docker exec $Container bash -lc $inner 2>&1 | Tee-Object -FilePath $hostLog
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Error "scan-matrix rebuild FAILED (exit $code) - see $hostLog"
}
exit $code
