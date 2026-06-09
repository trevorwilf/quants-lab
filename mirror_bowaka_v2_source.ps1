#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Mirror the read-only live Bowaka v2 strategy source into the quants-lab repo,
  (re)generate the frozen parity contract, and regenerate the lab configs from it
  so the lab immediately uses the new live screener / signal values.

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

    STEP 3  Regenerate the lab configs FROM the new contract (the bit that makes
            the lab actually USE the new values). The contract is only the
            anchor; runs read screener / signal thresholds from the loaded config
            files, so a new contract alone changes nothing. This step re-runs the
            contract -> config mapper for every GENERATED-marked config under
              research_notebooks\bowaka_v2_lab\configs\
            (auto-discovered by the header marker, so hand-tuned .workstation /
            .matrix overlays are NOT touched) and prints a per-config summary.
            It also warns if a new live threshold has drifted outside the
            hardcoded optuna search bounds (optuna/search_space.py).

  Re-running is safe and idempotent: the mirror is rebuilt clean, the contract is
  regenerated, and the configs are rewritten byte-identically when already in sync.

  NOT covered automatically (by design -- these need operator judgement):
    * The optuna SEARCH bounds in optuna/search_space.py are hardcoded code, not
      data; STEP 3 only WARNS if a live value drifts outside them.
    * Hand-tuned overlays (.workstation / .matrix) are not regenerated; rebuild
      them from the refreshed *_optuna base if you run studies against them.
    * Studies pin trial 0 (the incumbent) + the per-fold parity reference from
      the CONTRACT directly, so those pick up the new values from STEP 2 alone.

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

# --- STEP 3: regenerate the lab configs from the new contract ----------
# The contract is only the anchor; runs read screener / signal thresholds from
# the loaded config files. Re-run the contract -> config mapper for every
# GENERATED-marked config so the lab uses the new live values (hand-tuned
# .workstation / .matrix overlays carry no marker and are left untouched).
Write-Host ""
Write-Host "STEP 3  Regenerating lab configs from the new contract via '$Container' ..." -ForegroundColor Yellow

$innerCfg = "cd /quants-lab/research_notebooks/bowaka_v2_lab && " +
            "PYTHONPATH=src:../bowaka_common/src " +
            "/opt/conda/envs/quants-lab/bin/python -m bowaka_v2_lab.cli regen-actual-configs"
docker exec $Container bash -lc $innerCfg
if ($LASTEXITCODE -ne 0) {
    Write-Error "Config regeneration failed (exit $LASTEXITCODE)."
    Write-Host  "(STEPS 1-2 succeeded -- the mirror + contract are current -- so only STEP 3 needs a retry.)" -ForegroundColor DarkYellow
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "  mirror populated : $mirror"
Write-Host "  contract written : $contract"
Write-Host "  lab configs      : regenerated from the contract (see STEP 3 summary above)"
Write-Host ""
Write-Host "The mirror is git-ignored; the contract + regenerated configs are committed." -ForegroundColor Cyan
Write-Host "Review 'git diff' on reference/ + configs/ to see the new live values, then commit." -ForegroundColor Cyan
Write-Host "NB: optuna SEARCH bounds (optuna/search_space.py) are NOT auto-updated -- heed any" -ForegroundColor Cyan
Write-Host "    drift WARNING printed in STEP 3, and rebuild any .workstation/.matrix overlays." -ForegroundColor Cyan
