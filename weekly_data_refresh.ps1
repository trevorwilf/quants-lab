#!/usr/bin/env pwsh
# weekly_data_refresh.ps1
#
# Scheduled WEEKLY refresh of the shared market-data lake on the fast native container
# FS (/opt/market_data_cache). ONE command updates EVERY dataset the bowaka_v2_lab
# backtester / scan matrices / realism gates consume:
#
#   CRITICAL (must succeed -- a failure aborts the run + flags the lake stale):
#     * daily + minute SIP bars, SIP NBBO quotes  (scripts/backfill_market_data.py)
#     * raw trade tape (--trades, PA.2) + fine sub-minute NBBO (--quotes-fine, PA.3)
#
#   SUPPLEMENTARY (best-effort -- a source hiccup WARNs but never loses the bars/quotes
#   refresh or blocks the matrix rebuild):
#     * Nasdaq trade halts  -> statuses/            (scripts/backfill_halts.py, JSON-RPC)
#     * official open/close auctions                (scripts/backfill_auctions.py)
#     * corporate actions (survivorship/adjustment) (scripts/backfill_corporate_actions.py)
#
# Designed to run every Friday after the US close so the lake -- and, the next morning,
# the scan matrices -- include the just-completed week.
#
# WINDOWS / resume behaviour, per dataset:
#   - bars/quotes/trades/quotes-fine: incremental over a short LOOKBACK window
#     (-LookbackDays). Resume-aware -- only NEW (symbol, session) pairs are fetched, so
#     re-runs are cheap. The window MUST exceed the gap since the last successful run;
#     the default 10 covers a normal weekly cadence with holiday buffer. Widen it
#     (-LookbackDays 21) after a skipped week. Nothing already present is re-downloaded.
#   - auctions: re-fetch the SAME short lookback window with --force, then merge + dedupe
#     by session_date. (The plain resume check skips a symbol whose end-MONTH file exists,
#     so on a same-month weekly run it would miss the new week -- --force is required for
#     a correct weekly increment; the short window keeps it cheap.)
#   - halts + corporate-actions: re-fetch the FULL history window every run
#     (-HaltsStart / -CorpActionsStart .. today). Both are idempotent -- halts do a
#     COMPLETE per-(symbol,day) overwrite (so the window must cover each halt's start day,
#     which a full re-fetch guarantees), corp-actions dedupe on the Alpaca event id -- and
#     small (a few minutes), so this self-bootstraps an absent partition AND keeps the
#     whole history complete without a separate one-off backfill. Widen the start to cover
#     more history; it only costs a slightly longer (still idempotent) re-fetch.
#
# Trade buffer is RAM-bounded (TRADE_FLUSH_EVERY_SESSIONS); trades/ + quotes_fine/ are
# SIBLING paths so they never drift the canonical quote_partitions_hash. --quotes-fine
# roughly DOUBLES quote-fetch time (it re-streams NBBO at a finer cadence) -- pass
# -SkipQuotesFine to drop it; -SkipTrades / -SkipHalts / -SkipAuctions / -SkipCorpActions
# likewise drop those datasets. rpm defaults to 8000 (headroom under the 10000 SIP limit).
#
# It does NOT reduce the symbol universe: quotes/auctions are fetched for every symbol
# that has bars, so raising max_candidates_per_scan later needs no re-download.
#
#   .\weekly_data_refresh.ps1                      # everything: last 10d bars/quotes/trades/fine + full halts/auctions/CA
#   .\weekly_data_refresh.ps1 -LookbackDays 21     # widen the bars/quotes/auctions window (after a missed week)
#   .\weekly_data_refresh.ps1 -HaltsStart 2024-01-01 -CorpActionsStart 2024-01-01  # deeper halt/CA history
#   .\weekly_data_refresh.ps1 -SkipQuotesFine -SkipTrades   # canonical bars/quotes + supplementary only
#   .\weekly_data_refresh.ps1 -Rpm 10000           # full SIP limit (off-hours only)
#   .\weekly_data_refresh.ps1 -RebuildMatrices     # also rebuild scan matrices afterward
#
# US regular close is 16:00 ET; extended trading runs to 20:00 ET (= 18:00 container
# Mountain Time; the 2h ET->MT offset is constant across DST). Schedule for Friday
# evening local so the session is final + Alpaca has published the consolidated SIP tape.
#
# DO NOT register a standalone scheduled task for THIS script (nor a separate Saturday
# rebuild_scan_matrices.ps1 task). The scheduled entry point is scheduled_weekly_refresh.ps1
# -- it wraps this refresh + the matrix rebuild behind a STUDY GUARD so neither clobbers a
# running notebook-10 study. An unguarded run on its own clock can corrupt a live study.
# Run this script by hand only (an off-cycle catch-up), and NOT while a study is active.
#
# Requires ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY in the container env or repo .env.
# Halts additionally need outbound access to nasdaqtrader.com (the JSON-RPC halt source).

param(
    [int]    $LookbackDays = 10,
    [int]    $Rpm          = 8000,
    [int]    $QuoteWorkers = 16,
    [string] $Feed         = "sip",
    [int]    $FineQuoteSamplesPerMinute = 4,
    [string] $HaltsStart       = "2025-08-01",
    [string] $CorpActionsStart = "2025-08-01",
    [switch] $SkipTrades,
    [switch] $SkipQuotesFine,
    [switch] $SkipHalts,
    [switch] $SkipAuctions,
    [switch] $SkipCorpActions,
    [switch] $RebuildMatrices
)
$ErrorActionPreference = "Stop"
$Container = "ql-jupyter"
$Python    = "/opt/conda/envs/quants-lab/bin/python"
$LakeRoot  = "/opt/market_data_cache"
$LabDir    = "/quants-lab/research_notebooks/bowaka_v2_lab"

$running = docker ps --filter "name=$Container" --filter "status=running" --format "{{.Names}}"
if ($running -ne $Container) {
    Write-Error "Container '$Container' is not running. Start the stack first:`n  docker compose -f quantslab_desktop_compose.yaml up -d"
    exit 1
}

$start   = (Get-Date).AddDays(-$LookbackDays).ToString("yyyy-MM-dd")
$today   = (Get-Date).ToString("yyyy-MM-dd")
$ts      = Get-Date -Format "yyyyMMdd_HHmmss"
$hostLog = Join-Path $PSScriptRoot "weekly_data_refresh_$ts.log"

# Canonical bars/quotes fill-realism stages (PA.2/PA.3): kept current alongside bars/quotes.
$fillFlags = ""
if (-not $SkipTrades)     { $fillFlags += " --trades" }
if (-not $SkipQuotesFine) { $fillFlags += " --quotes-fine --quotes-fine-samples-per-minute $FineQuoteSamplesPerMinute" }

# Supplementary lab datasets -- each guarded with `|| { WARN; supp_fail=1; }` so a source
# hiccup never aborts the critical refresh (set -e) nor blocks the rebuild. Empty when the
# matching -Skip flag is set (-> a harmless blank line in the inner script).
$haltCmd = ""
if (-not $SkipHalts) {
    $haltCmd = "$Python scripts/backfill_halts.py --start $HaltsStart --end $today || { echo 'WARN: halts backfill FAILED'; supp_fail=1; }"
}
$auctionCmd = ""
if (-not $SkipAuctions) {
    $auctionCmd = "$Python scripts/backfill_auctions.py --feed $Feed --start $start --end $today --force --workers $QuoteWorkers || { echo 'WARN: auctions backfill FAILED'; supp_fail=1; }"
}
$corpCmd = ""
if (-not $SkipCorpActions) {
    $corpCmd = "$Python scripts/backfill_corporate_actions.py --start $CorpActionsStart --end $today --workers 6 || { echo 'WARN: corp-actions backfill FAILED'; supp_fail=1; }"
}

Write-Host "[weekly] feed=$Feed start=$start today=$today rpm=$Rpm workers=$QuoteWorkers lake=$LakeRoot"
Write-Host "[weekly] critical: bars/quotes trades=$(-not $SkipTrades) quotes_fine=$(-not $SkipQuotesFine)"
Write-Host "[weekly] supplementary: halts=$(-not $SkipHalts)($HaltsStart..) auctions=$(-not $SkipAuctions) corp_actions=$(-not $SkipCorpActions)($CorpActionsStart..)"
Write-Host "[weekly] log: $hostLog"

# MARKET_DATA_ROOT + the *_FETCH_WORKERS / flush knobs are exported INSIDE the container,
# NOT via `docker exec -e` (Git Bash / MSYS on Windows rewrites a bare /opt/... argument
# into a Windows path). Critical bars/quotes run under `set -e` (a failure aborts the whole
# inner script -> non-zero exit -> host stale-flags + skips the rebuild). The supplementary
# lab backfills then run from the lab dir (their own PYTHONPATH), each guarded so a failure
# only WARNs + sets supp_fail; the inner script still `exit 0`s -> the matrix rebuild
# proceeds on the fresh bars/quotes (which the matrices depend on; halts/auctions/CA do not).
$inner = @"
set -euo pipefail
export MARKET_DATA_ROOT=$LakeRoot
export QUOTE_FETCH_WORKERS=$QuoteWorkers
export TRADE_FETCH_WORKERS=$QuoteWorkers
export QUOTE_FINE_FETCH_WORKERS=$QuoteWorkers
export TRADE_FLUSH_EVERY_SESSIONS=3
cd /quants-lab
$Python scripts/backfill_market_data.py --feed $Feed --quotes$fillFlags --start $start --rpm $Rpm
echo '[weekly] critical bars/quotes refresh OK -- starting supplementary lab datasets'
cd $LabDir
export PYTHONPATH=src:../bowaka_common/src
supp_fail=0
$haltCmd
$auctionCmd
$corpCmd
if [ "`$supp_fail" = "1" ]; then echo 'WARN: one or more supplementary backfills FAILED (bars/quotes OK; matrices will still rebuild)'; fi
exit 0
"@

# `bash -lc` mis-parses CR in a multi-line script: CRLF leaves a trailing \r on every line
# (e.g. `export MARKET_DATA_ROOT=/opt/...\r` -> wrong path). Normalize to LF before exec.
$inner = $inner -replace "`r", ""
docker exec $Container bash -lc $inner 2>&1 | Tee-Object -FilePath $hostLog
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Error "[weekly] CRITICAL data refresh FAILED (exit $code) - see $hostLog"
    exit $code
}

# Surface any supplementary (non-fatal) failures prominently: the lake bars/quotes are
# current, but halts/auctions/corp-actions may be incomplete this run.
$warns = Select-String -Path $hostLog -Pattern 'WARN:' -SimpleMatch -ErrorAction SilentlyContinue
if ($warns) {
    Write-Warning "[weekly] $($warns.Count) supplementary-backfill warning(s) - see $hostLog"
    $warns | ForEach-Object { Write-Warning ("[weekly]   " + $_.Line.Trim()) }
}

Write-Host "[weekly] data refresh complete -> $hostLog"

if ($RebuildMatrices) {
    Write-Host "[weekly] rebuilding scan matrices (validation + holdout)..."
    & (Join-Path $PSScriptRoot "rebuild_scan_matrices.ps1")
    exit $LASTEXITCODE
}
exit 0
