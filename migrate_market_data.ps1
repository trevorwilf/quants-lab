#!/usr/bin/env pwsh
# migrate_market_data.ps1
#
# Migrate the legacy bowaka_lab parquet tree into the shared market-data lake.
#
# Runs inside the ql-jupyter Docker container, which has the quants-lab conda
# environment (pyarrow, pandas, ...). The Windows host has neither `make` nor a
# quants-lab Python env, so the migration must run in the container.
#
#   .\migrate_market_data.ps1 --verify-only     # dry inspection first
#   .\migrate_market_data.ps1                   # the real migration
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
docker exec $Container bash -lc "cd /quants-lab && $Python scripts/migrate_market_data.py$extra"
exit $LASTEXITCODE
