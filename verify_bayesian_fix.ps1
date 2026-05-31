<#
.SYNOPSIS
    Verify the Bowaka v2 lab Bayesian-optimization fix (Phases 0-3 of the
    2026-05-29 audit). v2: fixes the v1 hung-REPL bug, autodetects
    Python 3.12 via the py launcher, and sanity-checks imports before
    kicking off the long-running test legs.

.DESCRIPTION
    Run from research_notebooks\bowaka_v2_lab. By default uses the Python
    Launcher (`py -3.12`) — the verification report showed CC was
    implemented on 3.12.6, so 3.12 is where the lab deps live. If you
    don't have the py launcher, pass -PythonExe explicitly.

.PARAMETER PythonExe
    Path to the Python interpreter. Default: `py` (the Windows Python
    Launcher).
.PARAMETER PythonExtraArgs
    Extra args inserted between PythonExe and the script args. Default:
    `@("-3.12")` to force the 3.12 install via the launcher. Pass
    `@()` if PythonExe is already a versioned executable like
    `C:\Python312\python.exe`.
.PARAMETER SkipShortRun
    Pass through to verify-bayesian-fix; skips Section 7 (the 3-trial
    walk-forward short-run).
.PARAMETER StartDocker
    Bring up optuna-postgres before the suite. Off by default.
.PARAMETER OutDir
    Where to drop the aggregated report. Default: `artifacts\verification`.

.EXAMPLE
    # Default: uses py launcher to select 3.12
    .\verify_bayesian_fix.ps1

.EXAMPLE
    # Explicit interpreter path (no launcher)
    .\verify_bayesian_fix.ps1 -PythonExe C:\Python312\python.exe -PythonExtraArgs @()

.EXAMPLE
    # Skip Section 7 (no docker available)
    .\verify_bayesian_fix.ps1 -SkipShortRun
#>
[CmdletBinding()]
param(
    [string]$PythonExe = "py",
    [string[]]$PythonExtraArgs = @("-3.12"),
    [switch]$SkipShortRun,
    [switch]$StartDocker,
    [string]$OutDir = "artifacts\verification"
)

$ErrorActionPreference = "Continue"
$ProgressPreference    = "SilentlyContinue"

# ---------------------------------------------------------------------------
# Preconditions: must run from lab dir; PYTHONPATH set
# ---------------------------------------------------------------------------
if (-not (Test-Path "src\bowaka_v2_lab")) {
    Write-Error "Run this from research_notebooks\bowaka_v2_lab (no src\bowaka_v2_lab here)."
    exit 2
}
if (-not (Test-Path "..\bowaka_common\src")) {
    Write-Error "Cannot find ..\bowaka_common\src - script must run from inside research_notebooks\bowaka_v2_lab."
    exit 2
}
$env:PYTHONPATH = "src;..\bowaka_common\src"
$labRoot = (Get-Location).Path
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$logDir = Join-Path $labRoot "artifacts\verification\logs_$timestamp"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $labRoot $OutDir) | Out-Null
$reportPath = Join-Path $labRoot $OutDir "bayesian_fix_verification_aggregate_$timestamp.md"

# ---------------------------------------------------------------------------
# Python sanity check — fail fast if wrong interpreter or missing deps
# ---------------------------------------------------------------------------
Write-Host "=== Bowaka v2 Bayesian-optimization fix verification (v2) ===" -ForegroundColor Cyan
Write-Host "  PythonExe:       $PythonExe"
Write-Host "  PythonExtraArgs: $(if ($PythonExtraArgs.Count -gt 0) { $PythonExtraArgs -join ' ' } else { '(none)' })"

function Invoke-Python {
    param([string[]]$ArgList, [string]$LogFile = $null)
    $fullArgs = @()
    if ($PythonExtraArgs.Count -gt 0) { $fullArgs += $PythonExtraArgs }
    $fullArgs += $ArgList
    if ($LogFile) {
        & $PythonExe @fullArgs *>&1 | Tee-Object -FilePath $LogFile
    } else {
        & $PythonExe @fullArgs *>&1
    }
    return $LASTEXITCODE
}

# Probe 1: interpreter resolves and reports its version
Write-Host "  probing interpreter ..." -NoNewline
$versionOutput = & $PythonExe @PythonExtraArgs --version 2>&1
$rcVer = $LASTEXITCODE
if ($rcVer -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Error "Could not run '$PythonExe $($PythonExtraArgs -join ' ') --version' (exit=$rcVer). Output: $versionOutput"
    Write-Host ""
    Write-Host "Try one of:" -ForegroundColor Yellow
    Write-Host "  .\verify_bayesian_fix.ps1 -PythonExe py -PythonExtraArgs @('-3.12')"
    Write-Host "  .\verify_bayesian_fix.ps1 -PythonExe C:\Python312\python.exe -PythonExtraArgs @()"
    Write-Host ""
    Write-Host "Find candidates with:  py --list ; Get-Command python ; where.exe python" -ForegroundColor Yellow
    exit 2
}
Write-Host " OK"
$pyVersionLine = ($versionOutput | Where-Object { "$_" -match "Python\s+\d" } | Select-Object -First 1)
if (-not $pyVersionLine) { $pyVersionLine = "$($versionOutput | Select-Object -First 1)" }
Write-Host "  python version:  $pyVersionLine"

# Probe 2: pytest + bowaka_v2_lab import
Write-Host "  probing imports (pytest, bowaka_v2_lab) ..." -NoNewline
$importProbe = & $PythonExe @PythonExtraArgs -c "import sys; import pytest; import bowaka_v2_lab; print('OK', sys.version.split()[0], 'pytest', pytest.__version__)" 2>&1
$rcImp = $LASTEXITCODE
if ($rcImp -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Host "  $importProbe" -ForegroundColor Red
    Write-Host ""
    Write-Host "Either the wrong Python is selected, or its environment is missing lab deps." -ForegroundColor Yellow
    Write-Host "The earlier verification report showed CC ran on Python 3.12.6 - those deps are installed under 3.12."
    Write-Host "Find that interpreter and pass it explicitly. Useful commands:" -ForegroundColor Yellow
    Write-Host "  py --list"
    Write-Host "  Get-Command python"
    Write-Host "  where.exe python"
    exit 2
}
Write-Host " OK"
Write-Host "  $importProbe"
Write-Host ""

# ---------------------------------------------------------------------------
# System info
# ---------------------------------------------------------------------------
function Get-Git($rev) {
    try {
        $r = & git rev-parse $rev 2>$null
        if ($LASTEXITCODE -eq 0) { return $r.Trim() } else { return "unknown" }
    } catch { return "unknown" }
}
$labCommit = Get-Git "HEAD"
$devCommit = Get-Git "dev"
$workingDirty = (& git status --porcelain 2>$null | Measure-Object).Count -gt 0
Write-Host "  lab HEAD:        $labCommit"
Write-Host "  dev HEAD:        $devCommit"
Write-Host "  dirty:           $workingDirty"
Write-Host "  logs dir:        $logDir"
Write-Host ""

if ($StartDocker) {
    Write-Host "Starting optuna-postgres ..." -ForegroundColor Cyan
    & docker compose -f "..\..\quantslab_desktop_compose.yaml" up -d optuna-postgres
    Start-Sleep -Seconds 3
}

# ---------------------------------------------------------------------------
# Leg runner — parameter name is ArgList (NOT Args). $Args is a PowerShell
# automatic variable; using it as a param name in v1 caused the splat
# `@Args` to expand to an empty automatic, launching bare `python` (REPL)
# instead of `python -m pytest ...`. That is the v1 hang.
# ---------------------------------------------------------------------------
$results = @()
function Invoke-Leg {
    param(
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] [string[]]$ArgList,
        [Parameter(Mandatory)] [string]$LogFile
    )
    Write-Host "--- $Name ---" -ForegroundColor Cyan
    $shown = ($ArgList -join ' ')
    Write-Host "    command: $PythonExe $($PythonExtraArgs -join ' ') $shown" -ForegroundColor DarkGray
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $rc = Invoke-Python -ArgList $ArgList -LogFile $LogFile
    $sw.Stop()
    $secs = [int]$sw.Elapsed.TotalSeconds
    $color = if ($rc -eq 0) { "Green" } else { "Yellow" }
    Write-Host "    exit=$rc, elapsed=${secs}s" -ForegroundColor $color
    Write-Host ""
    $script:results += [pscustomobject]@{ Name = $Name; Exit = $rc; Seconds = $secs; LogFile = $LogFile }
    return $rc
}

$notLive = "not live_alpaca and not live_paper and not live_mongo and not slow"

# ---------------------------------------------------------------------------
# Leg 1: unit + parity
# ---------------------------------------------------------------------------
$leg1Log = Join-Path $logDir "1_unit_parity.log"
$rc1 = Invoke-Leg "unit + parity" @(
    "-m","pytest","tests/unit","tests/parity",
    "-q","--tb=short","-m",$notLive
) $leg1Log

# ---------------------------------------------------------------------------
# Leg 2: integration + reconcile
# ---------------------------------------------------------------------------
$leg2Log = Join-Path $logDir "2_integration_reconcile.log"
$rc2 = Invoke-Leg "integration + reconcile" @(
    "-m","pytest","tests/integration","tests/reconcile",
    "--timeout=120","--timeout-method=thread",
    "-q","--tb=short","-m",$notLive
) $leg2Log

# ---------------------------------------------------------------------------
# Leg 3: targeted tests (CLI's missing rows)
# ---------------------------------------------------------------------------
$leg3Log = Join-Path $logDir "3_targeted.log"
$targetedTests = @(
    "tests/integration/test_walkforward_writes_failed_artifact_on_invalid_study.py",
    "tests/integration/test_walkforward_rejects_degraded_folds_in_valid_trial_filter.py",
    "tests/integration/test_current_code_parity_full_fold_preflight_blocks_empty_pit_universe.py",
    "tests/integration/test_current_code_parity_full_fold_preflight_blocks_missing_minute_coverage.py",
    "tests/integration/test_current_code_parity_full_fold_preflight_warns_missing_quotes_but_records_limitation.py",
    "tests/integration/test_manifest_partition_adjustment_consistency.py",
    "tests/integration/test_run_manifest_records_effective_daily_adjustment.py",
    "tests/integration/test_autoconfig_capability_probe_uses_adjustment.py",
    "tests/integration/test_incumbent_baseline_trial_zero_matches_contract.py",
    "tests/integration/test_walkforward_runner_invalid_study.py"
)
$existingTargeted = $targetedTests | Where-Object { Test-Path $_ }
$missingTargeted  = $targetedTests | Where-Object { -not (Test-Path $_) }
if ($missingTargeted.Count -gt 0) {
    Write-Host "    skipping non-existent: $($missingTargeted -join ', ')" -ForegroundColor Yellow
}
$rc3 = Invoke-Leg "targeted gap-coverage tests" (@("-m","pytest") + $existingTargeted + @("-v","--tb=short")) $leg3Log

# ---------------------------------------------------------------------------
# Leg 4: verification CLI
# ---------------------------------------------------------------------------
$leg4Log = Join-Path $logDir "4_verify_cli.log"
$cliArgList = @("-m","bowaka_v2_lab.cli","verify-bayesian-fix")
if ($SkipShortRun) { $cliArgList += "--skip-short-run" }
$rc4 = Invoke-Leg "verify-bayesian-fix CLI" $cliArgList $leg4Log

# Find the CLI's own report
$cliReportLine = (Get-Content $leg4Log | Where-Object { $_ -match "^VERIFICATION_REPORT:\s*(.+)$" } | Select-Object -Last 1)
$cliReportPath = $null
if ($cliReportLine -match "^VERIFICATION_REPORT:\s*(.+)$") {
    $cliReportPath = $Matches[1].Trim()
}
$cliOverallLine = (Get-Content $leg4Log | Where-Object { $_ -match "^OVERALL:" } | Select-Object -Last 1)

# ---------------------------------------------------------------------------
# Aggregate report
# ---------------------------------------------------------------------------
$maxRc = ($results | Measure-Object -Property Exit -Maximum).Maximum
$overall = if ($maxRc -eq 0) { "PASS" } else { "FAIL" }

function Get-LogTail($path, $n) {
    if (Test-Path $path) {
        $tail = Get-Content $path -Tail $n -ErrorAction SilentlyContinue
        return ($tail -join "`r`n")
    }
    return "(no log)"
}

$report = @()
$report += "# Bowaka v2 Bayesian-optimization fix — aggregate verification report"
$report += ""
$report += "- generated_at: $((Get-Date).ToUniversalTime().ToString('o'))"
$report += "- lab_root: $labRoot"
$report += "- lab HEAD: $labCommit"
$report += "- dev HEAD: $devCommit"
$report += "- working tree dirty: $workingDirty"
$report += "- python: $pyVersionLine"
$report += "- python_exe: $PythonExe $($PythonExtraArgs -join ' ')"
$report += "- import_probe: $importProbe"
$report += "- PYTHONPATH: $($env:PYTHONPATH)"
$report += "- options: SkipShortRun=$SkipShortRun, StartDocker=$StartDocker"
$report += ""
$report += "## Leg summary"
$report += ""
$report += "| Leg | Exit | Elapsed (s) |"
$report += "|---|---:|---:|"
foreach ($r in $results) {
    $report += "| $($r.Name) | $($r.Exit) | $($r.Seconds) |"
}
$report += "| **MAX** | **$maxRc** | — |"
$report += ""

$report += "## Leg 1 — unit + parity (last 40 lines)"
$report += ""
$report += '```'
$report += (Get-LogTail $leg1Log 40)
$report += '```'
$report += ""

$report += "## Leg 2 — integration + reconcile (last 80 lines)"
$report += ""
$report += '```'
$report += (Get-LogTail $leg2Log 80)
$report += '```'
$report += ""

$report += "## Leg 3 — targeted gap-coverage tests (last 80 lines)"
$report += ""
$report += '```'
$report += (Get-LogTail $leg3Log 80)
$report += '```'
$report += ""

$report += "## Leg 4 — verify-bayesian-fix CLI"
$report += ""
$report += "- stdout summary: $cliOverallLine"
$report += "- cli report path: $cliReportPath"
$report += ""
$report += "### CLI report contents"
$report += ""
if ($cliReportPath -and (Test-Path $cliReportPath)) {
    $report += (Get-Content $cliReportPath -Raw)
} else {
    $report += "(CLI report not found at the path it printed)"
    $report += ""
    $report += "### Leg 4 log tail (40 lines)"
    $report += ""
    $report += '```'
    $report += (Get-LogTail $leg4Log 40)
    $report += '```'
}
$report += ""

$report += "## Overall"
$report += ""
if ($overall -eq "PASS") {
    $report += "**OVERALL: PASS** _(all legs returned 0 — ready for Phases 4-7)_"
} else {
    $report += "**OVERALL: FAIL** _(at least one leg returned non-zero — promotion to Phases 4-7 is BLOCKED)_"
}
$report += ""

$report -join "`r`n" | Set-Content -Path $reportPath -Encoding UTF8

# ---------------------------------------------------------------------------
# Final stdout summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
foreach ($r in $results) {
    $color = if ($r.Exit -eq 0) { "Green" } else { "Yellow" }
    Write-Host ("  {0,-35} exit={1} elapsed={2}s" -f $r.Name, $r.Exit, $r.Seconds) -ForegroundColor $color
}
Write-Host ""
Write-Host "AGGREGATE_REPORT: $reportPath" -ForegroundColor Cyan
$overallColor = if ($overall -eq "PASS") { "Green" } else { "Yellow" }
Write-Host "OVERALL: $overall" -ForegroundColor $overallColor
Write-Host ""
Write-Host "Paste the contents of the aggregate report file above back to the planner agent." -ForegroundColor Cyan

exit $maxRc