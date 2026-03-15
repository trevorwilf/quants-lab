# all_tests.ps1
# Runs all pmm_lab tests with output to both console and log file.
#
# Usage:
#   .\all_tests.ps1                    # Run from repo root or pmm_dynamic dir
#   .\all_tests.ps1 -Verbose           # Show extra timing info
#   .\all_tests.ps1 -Quick             # Unit tests only (fast)

param(
    [switch]$Quick,
    [switch]$Verbose
)

# --- Resolve project directory ---
$scriptDir = $PSScriptRoot
$pmmDynamic = $null

# Check if we're already in pmm_dynamic
if (Test-Path (Join-Path $PWD "pmm_lab")) {
    $pmmDynamic = $PWD.Path
}
# Check if we're in quants-lab root
elseif (Test-Path (Join-Path $PWD "research_notebooks\market_lab\pmm_dynamic\pmm_lab")) {
    $pmmDynamic = Join-Path $PWD "research_notebooks\market_lab\pmm_dynamic"
}
# Check script's own location
elseif (Test-Path (Join-Path $scriptDir "pmm_lab")) {
    $pmmDynamic = $scriptDir
}
elseif (Test-Path (Join-Path $scriptDir "research_notebooks\market_lab\pmm_dynamic\pmm_lab")) {
    $pmmDynamic = Join-Path $scriptDir "research_notebooks\market_lab\pmm_dynamic"
}
else {
    Write-Host "ERROR: Cannot find pmm_dynamic directory. Run from repo root or pmm_dynamic dir." -ForegroundColor Red
    exit 1
}

# --- Setup ---
$logFile = Join-Path $pmmDynamic "test_results.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$testPath = if ($Quick) { "tests/unit" } else { "tests" }
$label = if ($Quick) { "UNIT TESTS ONLY" } else { "ALL TESTS" }

# --- Header ---
$header = @"
============================================================
  pmm_lab Test Run — $label
  Directory: $pmmDynamic
  Started:   $timestamp
============================================================
"@

Write-Host $header -ForegroundColor Cyan
$header | Out-File -FilePath $logFile -Encoding UTF8

# --- Run pytest with tee to both console and file ---
Push-Location $pmmDynamic

$startTime = Get-Date

try {
    if ($Verbose) {
        python -m pytest $testPath -v --tb=long 2>&1 | Tee-Object -FilePath $logFile -Append
    }
    else {
        python -m pytest $testPath -v --tb=short 2>&1 | Tee-Object -FilePath $logFile -Append
    }
    $exitCode = $LASTEXITCODE
}
catch {
    Write-Host "ERROR: pytest failed to run: $_" -ForegroundColor Red
    "ERROR: pytest failed to run: $_" | Out-File -FilePath $logFile -Append -Encoding UTF8
    $exitCode = 1
}

$endTime = Get-Date
$elapsed = ($endTime - $startTime).TotalSeconds

# --- Footer ---
$footer = @"

============================================================
  Completed: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
  Elapsed:   $([math]::Round($elapsed, 1))s
  Exit code: $exitCode
  Log file:  $logFile
============================================================
"@

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host $footer -ForegroundColor Green
}
else {
    Write-Host $footer -ForegroundColor Red
}
$footer | Out-File -FilePath $logFile -Append -Encoding UTF8

Pop-Location
exit $exitCode
