#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Scheduled Friday wrapper around weekly_data_refresh.ps1 + rebuild_scan_matrices.ps1
  that adds (1) an Alpaca-API-down check with hourly retry and (2) a STUDY GUARD
  that DEFERS the whole run while a notebook-10 study / Top-N finalist sweep is
  active.

.DESCRIPTION
  This is the ONLY thing that should touch the lake or the scan-matrix store on a
  schedule, so it never collides with a multi-day study. Do NOT also register the
  standalone weekly_data_refresh.ps1 / rebuild_scan_matrices.ps1 tasks.

  WHY the guard covers the REFRESH too (not just the rebuild): a running study
  reads the lake DIRECTLY per fold and reads the matrix store; the whole-lake
  dataset_hash drifts on ANY lake change, and daily bars are retroactively
  split-adjusted -- so refreshing the lake mid-study can silently corrupt it, not
  merely leave matrices stale. Therefore if a study/sweep is active we defer the
  ENTIRE run; next week's -LookbackDays 15 re-covers the skipped week.

  Flow:
    STEP 0  Alpaca health check (scripts/alpaca_health_check.py, SIP feed). DOWN ->
            wait 1h and retry up to -AlpacaMaxRetries; AUTH/config error -> abort.
    STEP 1  Study guard (scripts/check_study_active.py). Proceeds ONLY on a clean
            rc==1 + '-> IDLE'; ANY other result (ACTIVE, or a docker/script/OOM
            failure) DEFERS the whole run (fail-safe).
    STEP 2  Lake refresh: weekly_data_refresh.ps1 -LookbackDays N -Rpm R. ONE pass now
            refreshes ALL lake datasets -- bars/quotes/trades/fine PLUS halts, official
            auctions, and corporate actions (-HaltsStart / -CorpActionsStart set the
            halt/CA full-history re-fetch window; every dataset is on by default).
    STEP 3  Re-check the guard (a study may have started during the refresh). Not
            idle -> SKIP the rebuild + write MATRICES_STALE.flag + warn.
    STEP 4  rebuild_scan_matrices.ps1 -- rebuilds the fast_realism matrices
            (validation + holdout) from the refreshed lake. The FR config anchors its
            window to the LATEST lake session (backtest.{start,end}_date: auto), so each
            weekly rebuild re-targets the freshest data -> tuned params track the latest
            data, and notebook 10 (same config + lake) reuses this matrix with no
            launch-time rebuild. Clears the stale flag. (Set explicit dates in the config
            to freeze the window; IR is retired -- pass -Configs to rebuild it.)

.NOTES
  REGISTRATION (mandatory shape -- Docker Desktop is per-user, so the task MUST
  run as the interactive user with Docker Desktop running; SYSTEM or
  'run whether logged on or not' has NO container and the first `docker exec`
  fails). Register with Register-ScheduledTask as user 'trevo', logged-on
  (Interactive) -- see the footer of this file for the exact command. The host
  must be logged on (Docker Desktop running) at Friday 18:30 MT for it to run.

  Live trading on the host is unaffected (this only touches the quants-lab lake +
  matrix store in the ql-jupyter container).

  -DryRun runs the Alpaca + guard checks and logs the decision WITHOUT refreshing
  or rebuilding -- use it to validate the guard while a study is running.
#>
[CmdletBinding()]
param(
    [int]    $LookbackDays     = 15,
    [int]    $Rpm              = 9000,
    [int]    $AlpacaMaxRetries = 6,      # hourly retries for Alpaca downtime (6h)
    [int]    $RetryIntervalSec = 3600,
    [string] $HaltsStart       = "2023-09-01",   # full-history halt re-fetch window start (-> weekly_data_refresh.ps1)
    [string] $CorpActionsStart = "2023-09-01",   # full-history corp-actions re-fetch window start (2026-06-23: pushed 2025-08-01 -> 2023-09-01 to match the deeper minute/daily backfill floor; CA drives survivorship over the new fold windows)
    [string] $Container        = "ql-jupyter",
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"
$Python    = "/opt/conda/envs/quants-lab/bin/python"
$repo      = $PSScriptRoot
$ts        = Get-Date -Format "yyyyMMdd_HHmmss"
$hostLog   = Join-Path $repo "scheduled_weekly_refresh_$ts.log"
$staleFlag = Join-Path $repo "MATRICES_STALE.flag"

function Log([string]$m) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
    Write-Host $line
    Add-Content -LiteralPath $hostLog -Value $line
}

# Run the study guard. Returns Idle=$true ONLY on a clean rc==1 + '-> IDLE'
# sentinel; every other outcome (ACTIVE rc==0, docker/script/OOM failure -> any
# other code, garbled output) is treated as NOT idle so the run is deferred.
function Test-StudyIdle {
    $out = (docker exec $Container bash -lc "cd /quants-lab && $Python scripts/check_study_active.py" 2>&1 | Out-String).Trim()
    $rc  = $LASTEXITCODE
    $idle = (($rc -eq 1) -and ($out -match '-> IDLE'))
    return [PSCustomObject]@{ Idle = $idle; Rc = $rc; Out = $out }
}

Log "=== scheduled_weekly_refresh start (DryRun=$DryRun LookbackDays=$LookbackDays Rpm=$Rpm HaltsStart=$HaltsStart CorpActionsStart=$CorpActionsStart) ==="

# Escalate if a prior run left matrices stale (visible, not silent).
if (Test-Path -LiteralPath $staleFlag) {
    $age = [int]((Get-Date) - (Get-Item -LiteralPath $staleFlag).LastWriteTime).TotalHours
    Log "WARNING: MATRICES_STALE.flag present (${age}h old) -- a prior run refreshed the lake but did NOT rebuild matrices. They are stale until a rebuild succeeds."
}

# --- container up? ---------------------------------------------------------
$running = docker ps --filter "name=$Container" --filter "status=running" --format "{{.Names}}"
if ($running -ne $Container) {
    Log "FATAL: container '$Container' not running (is Docker Desktop up + are you logged on?). Aborting -- next week re-covers."
    exit 1
}

# --- STEP 0: Alpaca health check + hourly retry ----------------------------
$alpacaCmd = "cd /quants-lab && PYTHONPATH=research_notebooks/bowaka_common/src $Python scripts/alpaca_health_check.py"
$alpacaUp  = $false
for ($i = 1; $i -le $AlpacaMaxRetries; $i++) {
    $out = (docker exec $Container bash -lc $alpacaCmd 2>&1 | Out-String).Trim()
    $rc  = $LASTEXITCODE
    Log "Alpaca check (attempt $i/$AlpacaMaxRetries): rc=$rc | $out"
    if ($rc -eq 0) { $alpacaUp = $true; break }
    if ($rc -eq 2) { Log "FATAL: Alpaca credential/entitlement error (not transient) -- aborting."; exit 2 }
    if ($DryRun)   { Log "(DryRun) Alpaca DOWN -- would sleep 1h and retry; not sleeping in DryRun."; break }
    if ($i -lt $AlpacaMaxRetries) {
        Log "Alpaca DOWN -- sleeping $([int]($RetryIntervalSec/60))min, then retry..."
        Start-Sleep -Seconds $RetryIntervalSec
    }
}
if (-not $alpacaUp) {
    if ($DryRun) { Log "(DryRun) Alpaca not confirmed up -- would abort; next week's -LookbackDays $LookbackDays re-covers." }
    else { Log "Alpaca still down after $AlpacaMaxRetries hourly attempts -- aborting. Next week's -LookbackDays $LookbackDays re-covers."; exit 1 }
}

# --- STEP 1: study guard (defer the ENTIRE run if a study/sweep is active) ---
$g = Test-StudyIdle
Log "Study guard: rc=$($g.Rc) | $($g.Out)"

if ($DryRun) {
    Log "(DryRun) Decision: $(if ($g.Idle) {'IDLE -> would refresh the lake + rebuild matrices.'} else {'NOT idle -> would DEFER the entire run (no refresh, no rebuild).'})"
    Log "(DryRun) No refresh/rebuild performed."
    Log "=== scheduled_weekly_refresh end (DryRun) ==="
    exit 0
}

if (-not $g.Idle) {
    Log "STUDY/SWEEP ACTIVE (or guard inconclusive rc=$($g.Rc)) -- DEFERRING the entire run."
    Log "  Refreshing the lake mid-study can corrupt it (per-fold lake reads + whole-lake dataset_hash drift), so nothing was touched."
    Log "  Next week's -LookbackDays $LookbackDays re-covers this week. To run now, wait until no study is active and run this script by hand."
    Log "=== scheduled_weekly_refresh end (deferred) ==="
    exit 0
}

# --- STEP 2: lake refresh --------------------------------------------------
# 2026-07-01 incident fix: PRE-SET the stale flag before the lake is touched and
# clear it only after a successful matrix rebuild (STEP 4). On 2026-06-26 the
# wrapper was killed mid-refresh (native stderr + EAP='Stop' NativeCommandError)
# so the failure branches below never ran: the lake mutated, no flag was written,
# and the next study silently ran ~15x degraded against the stale matrix. With
# the flag pre-set, ANY death mode (exception, reboot, logoff) leaves the
# breadcrumb, and the study-side freshness gate refuses to start.
Set-Content -LiteralPath $staleFlag -Value "Lake refresh STARTED $ts and has not completed a matrix rebuild yet (in progress, or the wrapper died mid-run). Run rebuild_scan_matrices.ps1 (or rerun scheduled_weekly_refresh.ps1) before starting a study."
Log "Pre-set stale-marker $staleFlag (cleared only after a successful matrix rebuild)."
Log "IDLE + Alpaca UP -- running lake refresh (ALL datasets: bars/quotes/trades/fine + halts/auctions/corp-actions; weekly_data_refresh.ps1 -LookbackDays $LookbackDays -Rpm $Rpm -HaltsStart $HaltsStart -CorpActionsStart $CorpActionsStart)..."
try {
    & (Join-Path $repo "weekly_data_refresh.ps1") -LookbackDays $LookbackDays -Rpm $Rpm -HaltsStart $HaltsStart -CorpActionsStart $CorpActionsStart
} catch {
    Set-Content -LiteralPath $staleFlag -Value "Lake refresh CRASHED $ts ($($_.Exception.Message)); the lake may be partially written + dataset_hash drifted. Rerun the refresh + rebuild_scan_matrices.ps1 before starting a study."
    Log "FATAL: lake refresh threw: $($_.Exception.Message) -- stale-marker kept. Skipping rebuild."
    exit 1
}
if ($LASTEXITCODE -ne 0) {
    $rc = $LASTEXITCODE
    Set-Content -LiteralPath $staleFlag -Value "Lake refresh FAILED $ts (exit $rc); the lake may be partially written + dataset_hash drifted. Rerun the refresh + rebuild_scan_matrices.ps1 before starting a study."
    Log "FATAL: lake refresh failed (exit $rc) -- wrote $staleFlag (lake may be partial). Skipping rebuild."
    exit $rc
}
Log "Lake refresh complete."

# --- STEP 3: re-check guard (a study may have started during the refresh) ---
$g2 = Test-StudyIdle
Log "Study guard (pre-rebuild re-check): rc=$($g2.Rc) | $($g2.Out)"
if (-not $g2.Idle) {
    Log "A study/sweep started during the refresh -- SKIPPING the rebuild (a rebuild would clobber the store it reads)."
    Set-Content -LiteralPath $staleFlag -Value "Lake refreshed $ts but matrices NOT rebuilt (a study/sweep started during the refresh). Run rebuild_scan_matrices.ps1 once idle. NB: that just-started study is reading the refreshed lake -- restart it after rebuilding."
    Log "WARNING: lake refreshed but matrices NOT rebuilt -> STALE. Wrote $staleFlag. Rebuild with .\rebuild_scan_matrices.ps1 once idle."
    Log "=== scheduled_weekly_refresh end (rebuild skipped, stale) ==="
    exit 0
}

# --- STEP 4: rebuild scan matrices (validation + holdout) ------------------
Log "Still idle -- rebuilding scan matrices (validation + holdout)..."
try {
    & (Join-Path $repo "rebuild_scan_matrices.ps1")
    $rc = $LASTEXITCODE
} catch {
    Set-Content -LiteralPath $staleFlag -Value "Lake refreshed $ts but matrix rebuild CRASHED ($($_.Exception.Message)). Rerun rebuild_scan_matrices.ps1 before starting a study."
    Log "matrix rebuild threw: $($_.Exception.Message) -- stale-marker kept."
    exit 1
}
if ($rc -ne 0) {
    Set-Content -LiteralPath $staleFlag -Value "Lake refreshed $ts but matrix rebuild FAILED (exit $rc). Rerun rebuild_scan_matrices.ps1 before starting a study."
    Log "matrix rebuild FAILED (exit $rc) -- wrote $staleFlag. Rerun rebuild_scan_matrices.ps1."
    exit $rc
}
if (Test-Path -LiteralPath $staleFlag) { Remove-Item -LiteralPath $staleFlag -Force; Log "Cleared stale-marker (matrices rebuilt)." }
Log "=== scheduled_weekly_refresh DONE -- lake refreshed + matrices rebuilt ==="
exit 0

# ---------------------------------------------------------------------------
# REGISTER the weekly task (Friday 18:30 Mountain Time). MUST run as the
# interactive user 'trevo' with Docker Desktop running -- do NOT use SYSTEM or
# 'run whether user is logged on or not' (no Docker engine in that session, so
# every `docker exec` fails). Register via the ScheduledTasks module (avoids
# schtasks /TR quoting issues + pins the pwsh path + sets an 8h time limit so
# the 6h Alpaca-retry window can't be truncated):
#
#   $pwsh = (Get-Command pwsh).Source
#   $act  = New-ScheduledTaskAction -Execute $pwsh -Argument '-NoProfile -ExecutionPolicy Bypass -File "E:\tradingsoftware\quants-lab\scheduled_weekly_refresh.ps1"'
#   $trg  = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At 6:30pm
#   $prn  = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
#   $set  = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 8) -StartWhenAvailable -WakeToRun -DontStopOnIdleEnd
#   Register-ScheduledTask -TaskName "bowaka_v2 weekly data refresh" -Action $act -Trigger $trg -Principal $prn -Settings $set -Force
# ---------------------------------------------------------------------------
