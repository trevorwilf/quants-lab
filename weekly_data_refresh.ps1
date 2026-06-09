#!/usr/bin/env pwsh
# weekly_data_refresh.ps1
#
# Scheduled WEEKLY refresh of the shared market-data lake (SIP bars + NBBO quotes)
# on the fast native container FS (/opt/market_data_cache). Designed to run every
# Friday after the US market close so the lake -- and, the next morning, the scan
# matrices -- include the just-completed week.
#
# What it does, INSIDE the ql-jupyter container:
#   - exports MARKET_DATA_ROOT=/opt/market_data_cache (the fast native lake the
#     notebook-10 study + scan matrices read; the slow in-repo 9p lake is NOT used)
#   - runs the incremental SIP backfill with --quotes: daily bars, minute bars,
#     and SIP NBBO quotes in ONE pass. Resume-aware -- only NEW (symbol, session)
#     pairs are fetched, so re-runs are cheap.
#   - rpm defaults to 8000 (headroom under the 10000 SIP limit, in case the data
#     key is shared with live trading). Quote fetch uses 16 worker threads.
#
# It does NOT reduce the symbol universe: quotes are fetched for every symbol that
# has bars, so raising max_candidates_per_scan later (50, 100, ...) needs no
# re-download.
#
#   .\weekly_data_refresh.ps1                      # last 10 days, sip, quotes, 8000 rpm
#   .\weekly_data_refresh.ps1 -LookbackDays 14     # widen the window (after a missed week)
#   .\weekly_data_refresh.ps1 -Rpm 10000           # full SIP limit (off-hours only)
#   .\weekly_data_refresh.ps1 -RebuildMatrices     # also rebuild scan matrices afterward
#
# The lookback window keeps the resume-coverage scan small. It MUST exceed the gap
# since the last successful run; the default 10 covers a normal weekly cadence with
# buffer for holidays. Widen it (e.g. -LookbackDays 21) if you skip a week or two.
# Nothing already present is re-downloaded regardless -- a wider window only costs a
# slightly longer resume scan.
#
# US regular close is 16:00 ET; extended trading runs to 20:00 ET (= 18:00 in the
# container's Mountain Time, MST/MDT -- the 2h ET->MT offset is constant across DST,
# so no seasonal schedule change is needed). Schedule for Friday evening local so
# the full session is final and Alpaca has published the consolidated SIP tape.
#
# DO NOT register a standalone scheduled task for THIS script (and do NOT register a
# separate Saturday rebuild_scan_matrices.ps1 task). The scheduled entry point is
# scheduled_weekly_refresh.ps1 -- it wraps this refresh + the matrix rebuild behind
# a STUDY GUARD so neither can clobber a running notebook-10 study. An unguarded
# standalone refresh/rebuild on its own clock can corrupt a live study. Run this
# script by hand only (e.g. an off-cycle catch-up).
#
# Requires ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY in the container env or repo .env.

param(
    [int]    $LookbackDays = 10,
    [int]    $Rpm          = 8000,
    [int]    $QuoteWorkers = 16,
    [string] $Feed         = "sip",
    [switch] $RebuildMatrices
)
$ErrorActionPreference = "Stop"
$Container = "ql-jupyter"
$Python    = "/opt/conda/envs/quants-lab/bin/python"
$LakeRoot  = "/opt/market_data_cache"

$running = docker ps --filter "name=$Container" --filter "status=running" --format "{{.Names}}"
if ($running -ne $Container) {
    Write-Error "Container '$Container' is not running. Start the stack first:`n  docker compose -f quantslab_desktop_compose.yaml up -d"
    exit 1
}

$start   = (Get-Date).AddDays(-$LookbackDays).ToString("yyyy-MM-dd")
$ts      = Get-Date -Format "yyyyMMdd_HHmmss"
$hostLog = Join-Path $PSScriptRoot "weekly_data_refresh_$ts.log"

Write-Host "[weekly] feed=$Feed start=$start rpm=$Rpm quotes=on workers=$QuoteWorkers lake=$LakeRoot"
Write-Host "[weekly] log: $hostLog"

# MARKET_DATA_ROOT + QUOTE_FETCH_WORKERS are exported INSIDE the container, NOT via
# `docker exec -e` (Git Bash / MSYS on Windows rewrites a bare /opt/... argument into
# a Windows path). --end defaults to the config's `auto`, which advances to the
# latest complete session on its own.
$inner = @"
set -euo pipefail
export MARKET_DATA_ROOT=$LakeRoot
export QUOTE_FETCH_WORKERS=$QuoteWorkers
cd /quants-lab
$Python scripts/backfill_market_data.py --feed $Feed --quotes --start $start --rpm $Rpm
"@

# `bash -lc` mis-parses CR in a multi-line script: CRLF leaves a trailing \r on
# every line (e.g. `export MARKET_DATA_ROOT=/opt/...​\r` -> wrong path, `cd ...\r`
# -> wrong dir). Normalize to LF before handing the script to the container.
$inner = $inner -replace "`r", ""
docker exec $Container bash -lc $inner 2>&1 | Tee-Object -FilePath $hostLog
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Error "[weekly] data refresh FAILED (exit $code) - see $hostLog"
    exit $code
}
Write-Host "[weekly] data refresh complete -> $hostLog"

if ($RebuildMatrices) {
    Write-Host "[weekly] rebuilding scan matrices (validation + holdout)..."
    & (Join-Path $PSScriptRoot "rebuild_scan_matrices.ps1")
    exit $LASTEXITCODE
}
exit 0
