<#
.SYNOPSIS
    Prepare (build + verify + promote) the walk-forward scan matrix that
    powers the fast path in notebooks/10_optuna_walkforward.ipynb.

.DESCRIPTION
    One-shot, schedulable matrix prep for the Bowaka v2 lab. Steps:

      1. (optional) staleness gate  - if -SkipIfFresh and the live matrix
         re-verifies clean, skip the multi-hour rebuild.
      2. build                      - scan-matrix build into a STAGING dir
                                       (never touches the live store on failure).
      3. verify --vectorized-check  - writes parity_proof.json; this script
                                       asserts verifier_version == 2 (the value
                                       runtime_mode='vectorized' requires).
      4. promote                    - atomically swap STAGING -> LIVE, keeping
                                       the previous good matrix as <store>.prev.
      5. (optional) benchmark       - run scripts/benchmark_walkforward_trial.py
                                       for a per-trial sanity check.

    Designed for Windows Task Scheduler. Exit code 0 = matrix ready; non-zero
    = nothing promoted (live store untouched). All output is teed to a
    timestamped log under <store>/build_logs/.

    PRECONDITIONS (created by the scan-matrix speedup CC prompt; run this only
    after that work is merged to dev and the package is installed in the target
    interpreter):
      * scan-matrix build/verify CLI present  (already in repo)
      * store_root resolver fix (Phase 1)     so the runtime actually reads it
      * matrix overlay config (Phase 2)        for the study run (NOT used here;
        build/verify run against the BASE workstation config - identical
        universe/cadence/feed/scope, so the hashes match)
      * benchmark script (Phase 3)             only needed for -Benchmark

    IMPORTANT: -StoreRoot here MUST equal the store_root the overlay points at,
    or the study will not find the matrix. Default below matches the CC spec.

.NOTES
    The matrix is invalidated by config_input_hash (universe/cadence/feed/scope)
    + dataset_hash (lake content) - NOT by a calendar. Schedule weekly, but it
    only pays the full build cost when the WF window rolled forward, the lake
    changed, or the universe/cadence changed. Use -Force for an unconditional
    rebuild; -SkipIfFresh to make a scheduled run a no-op when nothing changed.

.EXAMPLE
    # Safe weekly full rebuild (default), with a post-build per-trial check:
    .\matrix_prep.ps1 -Benchmark

.EXAMPLE
    # Scheduled run that rebuilds only when the matrix has actually drifted:
    .\matrix_prep.ps1 -SkipIfFresh

.EXAMPLE
    # Unconditional rebuild regardless of freshness:
    .\matrix_prep.ps1 -Force
#>

[CmdletBinding()]
param(
    # Repo root on the Windows host.
    [string] $RepoRoot   = 'E:\tradingsoftware\quants-lab',

    # Interpreter that has the lab deps installed (host: py -3.12).
    [string[]] $Python   = @('py', '-3.12'),

    # BASE workstation config (build/verify use this; the overlay is for the run).
    [string] $ConfigPath = 'research_notebooks/bowaka_v2_lab/configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml',

    # Must equal the overlay's scan_matrix.store_root (scope-suffixed).
    [string] $StoreRoot  = 'research_notebooks/bowaka_v2_lab/artifacts/cache/scan_matrix/validation',

    [ValidateSet('validation','holdout','full_history')]
    [string] $Scope      = 'validation',

    [int]    $Workers    = 8,
    [double] $ReserveGiB = 32.0,
    [int]    $SampleCount = 10,

    # Rebuild unconditionally (ignore freshness).
    [switch] $Force,

    # Skip the build if the live matrix re-verifies clean (verifier_version==2).
    [switch] $SkipIfFresh,

    # Run the per-trial benchmark after a successful promote.
    [switch] $Benchmark,
    [int]    $BenchmarkTrials = 8
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# --- resolve paths -----------------------------------------------------------
if (-not (Test-Path -LiteralPath $RepoRoot)) {
    Write-Error "RepoRoot not found: $RepoRoot"; exit 2
}
Set-Location -LiteralPath $RepoRoot

$ConfigFull = Join-Path $RepoRoot $ConfigPath
if (-not (Test-Path -LiteralPath $ConfigFull)) {
    Write-Error "Config not found: $ConfigFull"; exit 2
}

$LiveStore    = Join-Path $RepoRoot $StoreRoot
$StagingStore = "$LiveStore.staging"
$PrevStore    = "$LiveStore.prev"
$LogDir       = Join-Path (Split-Path $LiveStore -Parent) 'build_logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp        = Get-Date -Format 'yyyyMMddTHHmmss'
$LogFile      = Join-Path $LogDir "matrix_prep_$Stamp.log"

Start-Transcript -Path $LogFile -Append | Out-Null
$ExitCode = 0

function Invoke-Cli {
    param([Parameter(Mandatory)][string[]] $CliArgs)
    $exe  = $Python[0]
    $args = @()
    if ($Python.Count -gt 1) { $args += $Python[1..($Python.Count-1)] }
    $args += @('-m', 'bowaka_v2_lab.cli') + $CliArgs
    Write-Host (">> $exe " + ($args -join ' '))
    & $exe @args
    return $LASTEXITCODE
}

function Get-ProofVersion {
    param([Parameter(Mandatory)][string] $Store)
    $proof = Join-Path $Store 'parity_proof.json'
    if (-not (Test-Path -LiteralPath $proof)) { return $null }
    try { return [int]((Get-Content -Raw -LiteralPath $proof | ConvertFrom-Json).verifier_version) }
    catch { return $null }
}

try {
    Write-Host "=== Bowaka v2 scan-matrix prep @ $Stamp ==="
    Write-Host "RepoRoot : $RepoRoot"
    Write-Host "Config   : $ConfigFull"
    Write-Host "Scope    : $Scope"
    Write-Host "LiveStore: $LiveStore"
    Write-Host ""

    # --- 1. staleness gate ---------------------------------------------------
    if ($SkipIfFresh -and -not $Force) {
        if ((Test-Path -LiteralPath (Join-Path $LiveStore 'manifest.json')) -and
            ((Get-ProofVersion -Store $LiveStore) -eq 2)) {
            Write-Host "[freshness] live matrix present with verifier_version=2; re-verifying..."
            $rc = Invoke-Cli @('scan-matrix','verify','--store-root',$LiveStore,
                               '--config',$ConfigFull,'--sample-count',"$SampleCount",
                               '--vectorized-check')
            if ($rc -eq 0 -and (Get-ProofVersion -Store $LiveStore) -eq 2) {
                Write-Host "[freshness] verify clean - live matrix is current; skipping build."
                Stop-Transcript | Out-Null
                exit 0
            }
            Write-Host "[freshness] verify reported drift/failure (rc=$rc) - rebuilding."
        } else {
            Write-Host "[freshness] no valid live matrix - rebuilding."
        }
    }

    # --- 2. build into staging ----------------------------------------------
    if (Test-Path -LiteralPath $StagingStore) {
        Write-Host "[build] removing stale staging: $StagingStore"
        Remove-Item -Recurse -Force -LiteralPath $StagingStore
    }
    Write-Host "[build] building matrix into staging (this is the multi-hour step)..."
    $rc = Invoke-Cli @('scan-matrix','build','--config',$ConfigFull,
                       '--scope',$Scope,'--workers',"$Workers",
                       '--reserve-system-gib',"$ReserveGiB",
                       '--store-root',$StagingStore)
    if ($rc -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $StagingStore 'manifest.json'))) {
        Write-Error "[build] FAILED (rc=$rc). Live store untouched. Staging kept for inspection: $StagingStore"
        $ExitCode = 3; Stop-Transcript | Out-Null; exit $ExitCode
    }
    Write-Host "[build] OK."

    # --- 3. verify staging + write proof ------------------------------------
    Write-Host "[verify] verifying staging with --vectorized-check..."
    $rc = Invoke-Cli @('scan-matrix','verify','--store-root',$StagingStore,
                       '--config',$ConfigFull,'--sample-count',"$SampleCount",
                       '--vectorized-check')
    $ver = Get-ProofVersion -Store $StagingStore
    if ($rc -ne 0 -or $ver -ne 2) {
        Write-Error "[verify] FAILED (rc=$rc, verifier_version=$ver; need 2). Live store untouched. Staging kept: $StagingStore"
        $ExitCode = 4; Stop-Transcript | Out-Null; exit $ExitCode
    }
    Write-Host "[verify] OK (verifier_version=2)."

    # --- 4. atomic-ish promote: staging -> live, keep prev -------------------
    Write-Host "[promote] swapping staging into live..."
    if (Test-Path -LiteralPath $PrevStore) {
        Remove-Item -Recurse -Force -LiteralPath $PrevStore
    }
    if (Test-Path -LiteralPath $LiveStore) {
        Move-Item -LiteralPath $LiveStore -Destination $PrevStore
    } else {
        New-Item -ItemType Directory -Force -Path (Split-Path $LiveStore -Parent) | Out-Null
    }
    try {
        Move-Item -LiteralPath $StagingStore -Destination $LiveStore
    } catch {
        # Roll back to the previous good matrix if the swap failed mid-way.
        if (-not (Test-Path -LiteralPath $LiveStore) -and (Test-Path -LiteralPath $PrevStore)) {
            Move-Item -LiteralPath $PrevStore -Destination $LiveStore
        }
        throw
    }
    Write-Host "[promote] OK. Live matrix: $LiveStore  (previous kept at $PrevStore)"

    # --- 5. optional benchmark ----------------------------------------------
    if ($Benchmark) {
        $bench = Join-Path $RepoRoot 'research_notebooks/bowaka_v2_lab/scripts/benchmark_walkforward_trial.py'
        if (Test-Path -LiteralPath $bench) {
            Write-Host "[benchmark] running $BenchmarkTrials-trial per-trial check..."
            $exe = $Python[0]; $bargs = @()
            if ($Python.Count -gt 1) { $bargs += $Python[1..($Python.Count-1)] }
            $bargs += @($bench, '--n-trials', "$BenchmarkTrials")
            & $exe @bargs
            Write-Host "[benchmark] exit=$LASTEXITCODE (informational; does not gate promote)."
        } else {
            Write-Warning "[benchmark] script not found ($bench) - skipping. (Created by Phase 3 of the CC prompt.)"
        }
    }

    Write-Host ""
    Write-Host "=== MATRIX READY ==="
    Write-Host "Point notebook 10 CONFIG_PATH at the matrix overlay and launch the study."
}
catch {
    Write-Error "matrix prep aborted: $($_.Exception.Message)"
    $ExitCode = 1
}
finally {
    Stop-Transcript | Out-Null
}
exit $ExitCode