<#
.SYNOPSIS
    Verify the Bowaka v2 lab at the Phase 0-7 contract. v3: fixes the v2
    function-return-stream bug that mangled the leg-summary table; runs
    BOTH verification CLIs (verify-bayesian-fix for Phases 0-3,
    verify-realism-stress for Phases 1-5 of the Phases-4-7 prompt =
    audit Phases 4-7); aggregates everything into one paste-back artifact.

.DESCRIPTION
    Run from research_notebooks\bowaka_v2_lab. By default uses
    `py -3.12` via the Windows Python Launcher. Same flags as v2 plus
    -SkipRealismStress for cases where verify-realism-stress hasn't been
    built yet (i.e. before Phase 5 of the Phases-4-7 prompt lands).

.PARAMETER PythonExe
    Path to the Python interpreter. Default: `py`.
.PARAMETER PythonExtraArgs
    Extra args. Default: `@("-3.12")`.
.PARAMETER SkipShortRun
    Skip Section 7 of verify-bayesian-fix (the 3-trial walk-forward).
.PARAMETER SkipRealismStress
    Skip the verify-realism-stress CLI (use during/before the Phases-4-7
    prompt's Phase 5).
.PARAMETER StartDocker
    Bring up optuna-postgres before the suite.
.PARAMETER OutDir
    Where to drop the aggregated report. Default: `artifacts\verification`.

.EXAMPLE
    .\verify_phases_0_7.ps1

.EXAMPLE
    # Skip Section 7 + the new CLI (run during Phase 0 of the new prompt)
    .\verify_phases_0_7.ps1 -SkipShortRun -SkipRealismStress
#>
[CmdletBinding()]
param(
    [string]$PythonExe = "py",
    [string[]]$PythonExtraArgs = @("-3.12"),
    [switch]$SkipShortRun,
    [switch]$SkipRealismStress,
    [switch]$StartDocker,
    [string]$OutDir = "artifacts\verification"
)

$ErrorActionPreference = "Continue"
$ProgressPreference    = "SilentlyContinue"

# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------
if (-not (Test-Path "src\bowaka_v2_lab")) {
    Write-Error "Run this from research_notebooks\bowaka_v2_lab."
    exit 2
}
if (-not (Test-Path "..\bowaka_common\src")) {
    Write-Error "Cannot find ..\bowaka_common\src."
    exit 2
}
$env:PYTHONPATH = "src;..\bowaka_common\src"
$labRoot = (Get-Location).Path
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$logDir = Join-Path $labRoot "artifacts\verification\logs_$timestamp"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $labRoot $OutDir) | Out-Null
$reportPath = Join-Path $labRoot $OutDir "phases_0_7_aggregate_$timestamp.md"

# ---------------------------------------------------------------------------
# Python sanity check
# ---------------------------------------------------------------------------
Write-Host "=== Bowaka v2 Phases 0-7 verification (v3) ===" -ForegroundColor Cyan
Write-Host "  PythonExe:       $PythonExe"
Write-Host "  PythonExtraArgs: $(if ($PythonExtraArgs.Count -gt 0) { $PythonExtraArgs -join ' ' } else { '(none)' })"
Write-Host "  SkipShortRun:    $SkipShortRun"
Write-Host "  SkipRealismStress: $SkipRealismStress"

# Probe interpreter
$versionOutput = & $PythonExe @PythonExtraArgs --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Could not run '$PythonExe $($PythonExtraArgs -join ' ') --version'. Output: $versionOutput"
    Write-Host "Try:  .\verify_phases_0_7.ps1 -PythonExe C:\Python312\python.exe -PythonExtraArgs @()" -ForegroundColor Yellow
    exit 2
}
$pyVersionLine = ($versionOutput | Where-Object { "$_" -match "Python\s+\d" } | Select-Object -First 1)
if (-not $pyVersionLine) { $pyVersionLine = "$($versionOutput | Select-Object -First 1)" }
Write-Host "  python version:  $pyVersionLine"

# Probe imports
$importProbe = & $PythonExe @PythonExtraArgs -c "import sys, pytest, bowaka_v2_lab; print('OK', sys.version.split()[0], 'pytest', pytest.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Imports failed: $importProbe"
    exit 2
}
Write-Host "  $importProbe"
Write-Host ""

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
# Leg runner — v3: route Tee-Object through Out-Host so test output does
# NOT bubble up as function output. v2's bug was that the function
# emitted the entire pytest log as its return value, polluting the
# leg-summary table.
# ---------------------------------------------------------------------------
$script:results = @()

function Invoke-Leg {
    param(
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] [string[]]$ArgList,
        [Parameter(Mandatory)] [string]$LogFile
    )
    Write-Host "--- $Name ---" -ForegroundColor Cyan
    $shown = ($ArgList -join ' ')
    Write-Host "    command: $PythonExe $($PythonExtraArgs -join ' ') $shown" -ForegroundColor DarkGray
    $fullArgs = @()
    if ($PythonExtraArgs.Count -gt 0) { $fullArgs += $PythonExtraArgs }
    $fullArgs += $ArgList
    $sw = [Diagnostics.Stopwatch]::StartNew()
    # The | Out-Host at the end consumes the pipeline output so it does NOT
    # become the function's return value. The exit code is captured via
    # $LASTEXITCODE in the caller's scope.
    & $PythonExe @fullArgs *>&1 | Tee-Object -FilePath $LogFile | Out-Host
    $rc = $LASTEXITCODE
    $sw.Stop()
    $secs = [int]$sw.Elapsed.TotalSeconds
    $color = if ($rc -eq 0) { "Green" } else { "Yellow" }
    Write-Host "    exit=$rc, elapsed=${secs}s" -ForegroundColor $color
    Write-Host ""
    $script:results += [pscustomobject]@{
        Name = $Name; Exit = $rc; Seconds = $secs; LogFile = $LogFile
    }
}

$notLive = "not live_alpaca and not live_paper and not live_mongo and not slow"

# ---------------------------------------------------------------------------
# Leg 1: unit + parity
# ---------------------------------------------------------------------------
$leg1Log = Join-Path $logDir "1_unit_parity.log"
Invoke-Leg "unit + parity" @(
    "-m","pytest","tests/unit","tests/parity",
    "-q","--tb=short","-m",$notLive
) $leg1Log

# ---------------------------------------------------------------------------
# Leg 2: integration + reconcile
# ---------------------------------------------------------------------------
$leg2Log = Join-Path $logDir "2_integration_reconcile.log"
Invoke-Leg "integration + reconcile" @(
    "-m","pytest","tests/integration","tests/reconcile",
    "--timeout=120","--timeout-method=thread",
    "-q","--tb=short","-m",$notLive
) $leg2Log

# ---------------------------------------------------------------------------
# Leg 3: verify-bayesian-fix CLI (Phases 0-3 evidence)
# ---------------------------------------------------------------------------
$leg3Log = Join-Path $logDir "3_verify_bayesian_fix.log"
$cli1Args = @("-m","bowaka_v2_lab.cli","verify-bayesian-fix")
if ($SkipShortRun) { $cli1Args += "--skip-short-run" }
Invoke-Leg "verify-bayesian-fix CLI (Phases 0-3)" $cli1Args $leg3Log

# Find the CLI's report
$cli1ReportLine = (Get-Content $leg3Log | Where-Object { $_ -match "^VERIFICATION_REPORT:\s*(.+)$" } | Select-Object -Last 1)
$cli1ReportPath = $null
if ($cli1ReportLine -match "^VERIFICATION_REPORT:\s*(.+)$") {
    $cli1ReportPath = $Matches[1].Trim()
}
$cli1OverallLine = (Get-Content $leg3Log | Where-Object { $_ -match "^OVERALL:" } | Select-Object -Last 1)

# ---------------------------------------------------------------------------
# Leg 4: verify-realism-stress CLI (Phases 4-7 evidence)
# ---------------------------------------------------------------------------
$leg4Log = Join-Path $logDir "4_verify_realism_stress.log"
$cli2ReportPath = $null
$cli2OverallLine = "(skipped)"
if (-not $SkipRealismStress) {
    Invoke-Leg "verify-realism-stress CLI (Phases 4-7)" @(
        "-m","bowaka_v2_lab.cli","verify-realism-stress"
    ) $leg4Log
    $cli2ReportLine = (Get-Content $leg4Log | Where-Object { $_ -match "^VERIFICATION_REPORT:\s*(.+)$" } | Select-Object -Last 1)
    if ($cli2ReportLine -match "^VERIFICATION_REPORT:\s*(.+)$") {
        $cli2ReportPath = $Matches[1].Trim()
    }
    $cli2OverallLine = (Get-Content $leg4Log | Where-Object { $_ -match "^OVERALL:" } | Select-Object -Last 1)
} else {
    Write-Host "--- verify-realism-stress CLI (Phases 4-7) ---" -ForegroundColor Cyan
    Write-Host "    SKIPPED via -SkipRealismStress" -ForegroundColor Yellow
    $script:results += [pscustomobject]@{
        Name = "verify-realism-stress CLI (Phases 4-7) [SKIPPED]"
        Exit = 0; Seconds = 0; LogFile = "(skipped)"
    }
    Write-Host ""
}

# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------
$maxRc = ($script:results | Measure-Object -Property Exit -Maximum).Maximum
$overall = if ($maxRc -eq 0) { "PASS" } else { "FAIL" }

function Get-LogTail($path, $n) {
    if ($path -and (Test-Path $path)) {
        $tail = Get-Content $path -Tail $n -ErrorAction SilentlyContinue
        return ($tail -join "`r`n")
    }
    return "(no log)"
}

$report = @()
$report += "# Bowaka v2 — Phases 0-7 aggregate verification report"
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
$report += "- options: SkipShortRun=$SkipShortRun, SkipRealismStress=$SkipRealismStress, StartDocker=$StartDocker"
$report += ""
$report += "## Leg summary"
$report += ""
$report += "| Leg | Exit | Elapsed (s) |"
$report += "|---|---:|---:|"
foreach ($r in $script:results) {
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

$report += "## Leg 3 — verify-bayesian-fix CLI (Phases 0-3)"
$report += ""
$report += "- stdout summary: $cli1OverallLine"
$report += "- cli report path: $cli1ReportPath"
$report += ""
$report += "### CLI report contents"
$report += ""
if ($cli1ReportPath -and (Test-Path $cli1ReportPath)) {
    $report += (Get-Content $cli1ReportPath -Raw)
} else {
    $report += "(CLI report not found at the path it printed)"
    $report += ""
    $report += "### Leg 3 log tail (40 lines)"
    $report += ""
    $report += '```'
    $report += (Get-LogTail $leg3Log 40)
    $report += '```'
}
$report += ""

$report += "## Leg 4 — verify-realism-stress CLI (Phases 4-7)"
$report += ""
if ($SkipRealismStress) {
    $report += "- SKIPPED via -SkipRealismStress flag (CLI may not yet be built; use during Phase 0 of the Phases-4-7 prompt)"
} else {
    $report += "- stdout summary: $cli2OverallLine"
    $report += "- cli report path: $cli2ReportPath"
    $report += ""
    $report += "### CLI report contents"
    $report += ""
    if ($cli2ReportPath -and (Test-Path $cli2ReportPath)) {
        $report += (Get-Content $cli2ReportPath -Raw)
    } else {
        $report += "(CLI report not found at the path it printed)"
        $report += ""
        $report += "### Leg 4 log tail (40 lines)"
        $report += ""
        $report += '```'
        $report += (Get-LogTail $leg4Log 40)
        $report += '```'
    }
}
$report += ""

$report += "## Overall"
$report += ""
if ($overall -eq "PASS") {
    $report += "**OVERALL: PASS** _(all legs returned 0)_"
    $report += ""
    $report += "_Note: deferred cells (SIP_DATA_UNAVAILABLE, REAL_LOGS_DEFERRED, BELOW_MIN_SESSIONS, lake adjusted-partition missing) count as PASS-equivalent. They signal external pre-requisites, not defects._"
} else {
    $report += "**OVERALL: FAIL** _(at least one leg returned non-zero)_"
}
$report += ""

$report -join "`r`n" | Set-Content -Path $reportPath -Encoding UTF8

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
foreach ($r in $script:results) {
    $color = if ($r.Exit -eq 0) { "Green" } else { "Yellow" }
    Write-Host ("  {0,-50} exit={1} elapsed={2}s" -f $r.Name, $r.Exit, $r.Seconds) -ForegroundColor $color
}
Write-Host ""
Write-Host "AGGREGATE_REPORT: $reportPath" -ForegroundColor Cyan
$overallColor = if ($overall -eq "PASS") { "Green" } else { "Yellow" }
Write-Host "OVERALL: $overall" -ForegroundColor $overallColor
Write-Host ""
Write-Host "Paste the aggregate report contents back to the planner agent." -ForegroundColor Cyan

exit $maxRc
