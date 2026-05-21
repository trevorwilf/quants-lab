#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Mirror the read-only live Bowaka v2 strategy source into the quants-lab repo
  and (re)generate the frozen parity contract.

.DESCRIPTION
  The quants-lab Python dependencies live only inside the `ql-jupyter` Docker
  container, which cannot see the live strategy source on the Windows host.
  The Bowaka v2 realism remediation needs to read that live source (for the
  frozen contract and the parity test-suite). This script bridges the gap:

    STEP 1  Copy the live *.py / *.yaml / *.yml files from the live strategy
            directory into:
              research_notebooks\bowaka_v2_lab\reference\source_strategy\scripts\
            This is a LOCAL, git-ignored mirror. The copy is byte-exact
            (Copy-Item performs no transformation), so the SHA-256 of the
            mirrored config equals the SHA-256 of the live config -- parity
            checks hold.

    STEP 2  Generate (the "formatting" of the data):
              research_notebooks\bowaka_v2_lab\reference\actual_bowaka_v2_contract.yaml
            This is the machine-readable, deterministically-formatted contract.
            It is produced by the container's Python from the mirrored config
            (sections extracted, source SHA-256 embedded, keys sorted). This
            file IS committed to git -- it is the durable parity anchor.

  Re-running is safe and idempotent: the mirror is rebuilt clean and the
  contract is regenerated.

.NOTES
  Just run it -- no arguments needed:   .\mirror_bowaka_v2_source.ps1
  Requires: the ql-jupyter container running; Docker Desktop available.
#>
[CmdletBinding()]
param(
    [string]$SourceRoot = "E:\stocktradingsoftware\openalgo\strategies\scripts",
    [string]$Container  = "ql-jupyter"
)

$ErrorActionPreference = "Stop"
$repoRoot = $PSScriptRoot
$mirror   = Join-Path $repoRoot "research_notebooks\bowaka_v2_lab\reference\source_strategy\scripts"
$contract = Join-Path $repoRoot "research_notebooks\bowaka_v2_lab\reference\actual_bowaka_v2_contract.yaml"

Write-Host ""
Write-Host "=== Bowaka v2 live-source mirror + contract generation ===" -ForegroundColor Cyan
Write-Host "  live source : $SourceRoot"
Write-Host "  mirror      : $mirror"
Write-Host "  contract    : $contract"
Write-Host ""

# --- validate the live source ------------------------------------------
if (-not (Test-Path -LiteralPath $SourceRoot -PathType Container)) {
    Write-Error "Live source directory not found: $SourceRoot"
    exit 1
}
$liveConfig = Join-Path $SourceRoot "bowaka_v2_config.yaml"
if (-not (Test-Path -LiteralPath $liveConfig -PathType Leaf)) {
    Write-Error "Live config not found: $liveConfig"
    exit 1
}

# --- STEP 1: rebuild the mirror (byte-exact copy) ----------------------
Write-Host "STEP 1  Copying live source -> mirror ..." -ForegroundColor Yellow
if (Test-Path -LiteralPath $mirror) {
    Remove-Item -LiteralPath $mirror -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $mirror | Out-Null

$copied = 0
foreach ($pattern in @("*.py", "*.yaml", "*.yml")) {
    Get-ChildItem -LiteralPath $SourceRoot -Filter $pattern -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $mirror -Force
        $copied++
    }
}
if ($copied -eq 0) {
    Write-Error "No .py/.yaml/.yml files found under $SourceRoot"
    exit 1
}
Write-Host "        copied $copied file(s)." -ForegroundColor Green
Write-Host ""

# --- STEP 2: generate the formatted contract (in the container) --------
Write-Host "STEP 2  Generating actual_bowaka_v2_contract.yaml via '$Container' ..." -ForegroundColor Yellow

# Confirm the container is up.
$running = (docker ps --filter "name=$Container" --format "{{.Names}}" 2>$null)
if ($running -notcontains $Container) {
    Write-Error "Container '$Container' is not running. Start Docker Desktop / the QuantsLab stack and re-run."
    Write-Host  "(STEP 1 succeeded -- the mirror is populated -- so only STEP 2 needs a retry.)" -ForegroundColor DarkYellow
    exit 1
}

$inner = "cd /quants-lab/research_notebooks/bowaka_v2_lab && " +
         "PYTHONPATH=src:../bowaka_common/src " +
         "/opt/conda/envs/quants-lab/bin/python -m bowaka_v2_lab.reference"
docker exec $Container bash -lc $inner
if ($LASTEXITCODE -ne 0) {
    Write-Error "Contract generation failed (exit $LASTEXITCODE)."
    Write-Host  "(STEP 1 succeeded -- the mirror is populated -- so only STEP 2 needs a retry.)" -ForegroundColor DarkYellow
    exit $LASTEXITCODE
}

# --- verify ------------------------------------------------------------
if (-not (Test-Path -LiteralPath $contract -PathType Leaf)) {
    Write-Error "Contract file was not created: $contract"
    exit 1
}

Write-Host ""
Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "  mirror populated : $mirror"
Write-Host "  contract written : $contract"
Write-Host ""
Write-Host "The mirror is git-ignored; the contract is committed. You can now" -ForegroundColor Cyan
Write-Host "tell Claude Code to continue the Bowaka v2 realism remediation."   -ForegroundColor Cyan
