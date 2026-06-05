#!/usr/bin/env pwsh
# backfill_market_data.ps1
#
# Incrementally backfill the shared market-data lake from Alpaca, driven by
# config/marketdata_backfill.yml.
#
# Runs inside the ql-jupyter Docker container, which has the quants-lab conda
# environment (pyarrow, pandas, ...). The Windows host has neither `make` nor a
# quants-lab Python env, so the backfill must run in the container.
#
#   .\backfill_market_data.ps1                       # use the config as-is
#   .\backfill_market_data.ps1 --feed sip            # override the feed
#   .\backfill_market_data.ps1 --start 2020-01-01    # override the start date
#   .\backfill_market_data.ps1 --feed sip --quotes --start 2025-01-01
#                                                    # SIP bars + NBBO quotes
#                                                    # (full intended_realism). Quotes
#                                                    # are heavy on a first run — scope
#                                                    # --start; it is incremental.
#
# Requires ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY in the container
# environment or a repo .env (the runner loads .env best-effort).
#
param([Parameter(ValueFromRemainingArguments = $true)] [string[]] $ScriptArgs)

$ErrorActionPreference = "Stop"
$Container = "ql-jupyter"
$Python = "/opt/conda/envs/quants-lab/bin/python"

$running = docker ps --filter "name=$Container" --filter "status=running" --format "{{.Names}}"
if ($running -ne $Container) {
    Write-Error "Container '$Container' is not running. Start the stack first:`n  docker compose -f quantslab_desktop_compose.yaml up -d"
    exit 1
}

$extra = if ($ScriptArgs) { " " + ($ScriptArgs -join " ") } else { "" }
docker exec $Container bash -lc "cd /quants-lab && $Python scripts/backfill_market_data.py$extra"
exit $LASTEXITCODE
