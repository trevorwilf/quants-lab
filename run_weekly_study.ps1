#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Launch the weekly notebook-10 walk-forward study (papermill, in-container) with
  xmrig arbitration: stop the miner for the study, restart it when the run ends.

.DESCRIPTION
  Started by scheduled_weekly_refresh.ps1 STEP 6 via the ON-DEMAND scheduled task
  'bowaka_v2 weekly study run'. It MUST run as its own scheduled task, not as a
  child of the weekly wrapper: Task Scheduler kills the whole process tree of a
  task at its ExecutionTimeLimit, which would murder this 20-60h study mid-run
  and leave xmrig stopped. The aux task carries a 100h limit
  and RunLevel Highest (xmrig typically runs elevated for MSR/huge-pages access;
  a non-elevated task could not stop it). Safe to fire by hand any time:
      Start-ScheduledTask -TaskName "bowaka_v2 weekly study run"

  Flow:
    STEP 0  container up + STUDY GUARD (abort if a study/sweep is already active —
            never start a second study on the same store)
    STEP 1  notebook-10 READINESS gate (scripts/check_nb10_ready.py: contract
            parity, stale flag, matrix freshness over the fold-val window,
            Optuna storage). NOT READY -> abort; nothing killed, nothing run.
    STEP 2  xmrig: if running, STOP it (and remember that it was running).
            A kill failure ABORTS (a study racing a miner ~doubles runtime).
    STEP 3  papermill 10_optuna_walkforward.ipynb — NOTEBOOK DEFAULTS (5000
            trials + Top-N finalist sweep) -> dated output notebook
            research_notebooks/bowaka_v2_lab/notebooks/runs/10_optuna_walkforward_<ts>.ipynb
            papermill saves the output notebook AFTER EVERY CELL, so you can
            open the dated copy in Jupyter MID-RUN and watch results appear.
            All normal artifacts (reports, deployable YAMLs, the Postgres
            study) are produced exactly as in a manual run.
    STEP 4  FINALLY: restart xmrig from $XmrigDir — only if STEP 2 stopped it —
            on success AND on failure. A papermill failure additionally writes
            WEEKLY_STUDY_FAILED.flag with the log pointer (the weekly wrapper
            escalates a present flag at its next run).

  -DryRun runs STEPs 0-1 and xmrig DETECTION, logging every decision, without
  stopping xmrig or launching papermill.
#>
param(
    [string] $Container = "ql-jupyter",
    [string] $XmrigDir  = "E:\xmrig-6.25.0",
    [string] $XmrigExe  = "xmrig_6.26.0_Custome.exe",
    [switch] $DryRun
)
$ErrorActionPreference = "Stop"
$Python   = "/opt/conda/envs/quants-lab/bin/python"
$repo     = $PSScriptRoot
$ts       = Get-Date -Format "yyyyMMdd_HHmmss"
$hostLog  = Join-Path $repo "run_weekly_study_$ts.log"
$failFlag = Join-Path $repo "WEEKLY_STUDY_FAILED.flag"
$labDir   = "/quants-lab/research_notebooks/bowaka_v2_lab"
$nbIn     = "$labDir/notebooks/10_optuna_walkforward.ipynb"
$nbOutRel = "research_notebooks/bowaka_v2_lab/notebooks/runs/10_optuna_walkforward_$ts.ipynb"
$nbOut    = "/quants-lab/$nbOutRel"

function Log([string]$m) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
    Write-Host $line
    Add-Content -LiteralPath $hostLog -Value $line
}

Log "=== run_weekly_study start (DryRun=$DryRun) ==="

# --- container up? -----------------------------------------------------------
$running = docker ps --filter "name=$Container" --filter "status=running" --format "{{.Names}}"
if ($running -ne $Container) {
    Log "FATAL: container '$Container' not running -- study not launched."
    exit 1
}

# --- STEP 0: study guard ------------------------------------------------------
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$guardOut = (docker exec $Container bash -lc "cd /quants-lab && $Python scripts/check_study_active.py" 2>&1 | Out-String).Trim()
$guardRc  = $LASTEXITCODE
$ErrorActionPreference = $prevEAP
Log "Study guard: rc=$guardRc | $guardOut"
if (-not (($guardRc -eq 1) -and ($guardOut -match '-> IDLE'))) {
    Log "A study/sweep is already active (or the guard is inconclusive) -- NOT launching another. xmrig untouched."
    exit 0
}

# --- STEP 1: notebook-10 readiness gate ---------------------------------------
$readyCmd = "cd $labDir && PYTHONPATH=src:../bowaka_common/src MARKET_DATA_ROOT=/opt/market_data_cache $Python scripts/check_nb10_ready.py"
$ErrorActionPreference = "Continue"
$readyOut = (docker exec $Container bash -lc $readyCmd 2>&1 | Out-String).Trim()
$readyRc  = $LASTEXITCODE
$ErrorActionPreference = $prevEAP
$readyOut -split "`n" | ForEach-Object { Log ("  " + $_.Trim()) }
if ($readyRc -ne 0) {
    Set-Content -LiteralPath $failFlag -Value "run_weekly_study $ts aborted: notebook-10 readiness gate FAILED (rc=$readyRc) -- see run_weekly_study_$ts.log. xmrig untouched; no study launched."
    Log "NOT READY -- study not launched, xmrig untouched. Wrote $failFlag."
    exit 1
}

# --- STEP 2: stop xmrig -------------------------------------------------------
$procName = [System.IO.Path]::GetFileNameWithoutExtension($XmrigExe)
$xmrigProc = Get-Process -Name $procName -ErrorAction SilentlyContinue
$xmrigWasRunning = $null -ne $xmrigProc
Log "xmrig ($procName): $(if ($xmrigWasRunning) { 'RUNNING (pid ' + (($xmrigProc | Select-Object -First 1).Id) + ') -- will stop for the study and restart after' } else { 'not running -- nothing to stop; will NOT auto-start it after' })"

if ($DryRun) {
    Log "(DryRun) Would $(if ($xmrigWasRunning) {'stop xmrig, '} )launch papermill:"
    Log "(DryRun)   $nbIn -> $nbOut (kernel python3, notebook defaults: 5000 trials + Top-N sweep)"
    Log "=== run_weekly_study end (DryRun) ==="
    exit 0
}

if ($xmrigWasRunning) {
    try {
        Stop-Process -Name $procName -Force -ErrorAction Stop
    } catch {
        Set-Content -LiteralPath $failFlag -Value "run_weekly_study $ts aborted: could not stop xmrig ($($_.Exception.Message)) -- is the task running elevated (RunLevel Highest)? No study launched."
        Log "FATAL: could not stop xmrig: $($_.Exception.Message) -- aborting (a study racing the miner ~doubles runtime). Wrote $failFlag."
        exit 1
    }
    Start-Sleep -Seconds 5
    if (Get-Process -Name $procName -ErrorAction SilentlyContinue) {
        Set-Content -LiteralPath $failFlag -Value "run_weekly_study $ts aborted: xmrig survived Stop-Process. No study launched."
        Log "FATAL: xmrig still running after Stop-Process -- aborting. Wrote $failFlag."
        exit 1
    }
    Log "xmrig stopped."
}

# --- STEP 3: papermill (blocking; the aux task allows 100h) --------------------
$null = New-Item -ItemType Directory -Force -Path (Join-Path $repo "research_notebooks\bowaka_v2_lab\notebooks\runs")
$inner = @"
set -euo pipefail
export MARKET_DATA_ROOT=/opt/market_data_cache
cd $labDir
/opt/conda/envs/quants-lab/bin/papermill "$nbIn" "$nbOut" -k python3 --cwd "$labDir"
"@
$inner = $inner -replace "`r", ""
Log "Launching papermill: $nbIn -> $nbOut (notebook defaults; open the dated copy in Jupyter to watch progress)"
$code = 1
try {
    # 2026-07-01 incident class: native stderr in a pipeline under EAP='Stop'
    # kills the script while the container process lives. Judge by exit code.
    $ErrorActionPreference = "Continue"
    docker exec $Container bash -lc $inner 2>&1 | Tee-Object -FilePath $hostLog -Append
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prevEAP
} finally {
    # --- STEP 4: restart xmrig (success, failure, or exception) ---------------
    if ($xmrigWasRunning) {
        try {
            Start-Process -FilePath (Join-Path $XmrigDir $XmrigExe) -WorkingDirectory $XmrigDir -WindowStyle Minimized
            Start-Sleep -Seconds 5
            if (Get-Process -Name $procName -ErrorAction SilentlyContinue) {
                Log "xmrig restarted from $XmrigDir."
            } else {
                Log "WARNING: xmrig restart did not produce a running process -- start it by hand from $XmrigDir."
            }
        } catch {
            Log "WARNING: xmrig restart FAILED: $($_.Exception.Message) -- start it by hand from $XmrigDir."
        }
    } else {
        Log "xmrig was not running before the study -- leaving it off."
    }
}

if ($code -ne 0) {
    Set-Content -LiteralPath $failFlag -Value "Weekly notebook-10 study FAILED $ts (papermill exit $code). Executed-so-far notebook: $nbOutRel ; log: run_weekly_study_$ts.log"
    Log "FATAL: papermill exited $code -- wrote $failFlag. The partially-executed notebook (with the error cell) is at $nbOutRel."
    exit $code
}
if (Test-Path -LiteralPath $failFlag) { Remove-Item -LiteralPath $failFlag -Force; Log "Cleared $failFlag." }
Log "Weekly study COMPLETE. Executed notebook: $nbOutRel (open it in Jupyter for full cell outputs)."
Log "=== run_weekly_study DONE ==="
exit 0

# ------------------------------------------------------------------------------
# REGISTER the on-demand aux task (one-time; RunLevel Highest so an elevated
# xmrig can be stopped; 100h limit for the 20-60h study + sweep):
#
#   $pwsh = (Get-Command pwsh).Source
#   $act  = New-ScheduledTaskAction -Execute $pwsh -Argument '-NoProfile -ExecutionPolicy Bypass -File "E:\tradingsoftware\quants-lab\run_weekly_study.ps1"'
#   $prn  = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
#   $set  = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 100) -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
#   Register-ScheduledTask -TaskName "bowaka_v2 weekly study run" -Action $act -Principal $prn -Settings $set -Force
#
# (No trigger: STEP 6 of scheduled_weekly_refresh.ps1 starts it, or run it by
#  hand with Start-ScheduledTask.)
# ------------------------------------------------------------------------------
