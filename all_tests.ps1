# all_tests.ps1
# Runs all pmm_lab tests with output to both console and log file.
#
# Usage:
#   .\all_tests.ps1                    # Run all tests (auto-discovery)
#   .\all_tests.ps1 -Verbose           # Show extra timing info
#   .\all_tests.ps1 -Quick             # Unit tests only (fast)
#   .\all_tests.ps1 -Grouped           # Run by category with per-group status

param(
    [switch]$Quick,
    [switch]$Verbose,
    [switch]$Grouped
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
$label = if ($Quick) { "UNIT TESTS ONLY" } elseif ($Grouped) { "GROUPED TESTS" } else { "ALL TESTS" }
$tbFlag = if ($Verbose) { "--tb=long" } else { "--tb=short" }

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

# --- Test group definitions ---
# Each group: label, pytest arguments
# All paths are relative to $pmmDynamic
$testGroups = @(
    # --Core simulation engine --
    @{ Label = "Core Engine";
       Args  = @(
           "tests/unit/test_engine.py",
           "tests/unit/test_engine_config.py",
           "tests/unit/test_engine_parity.py",
           "tests/unit/test_engine_fill_realism.py",
           "tests/unit/test_engine_capacity_bug.py",
           "tests/unit/test_executor_model.py",
           "tests/unit/test_fill_model.py",
           "tests/unit/test_fill_model_v2.py",
           "tests/unit/test_inventory.py",
           "tests/unit/test_fees_maker_taker.py",
           "tests/unit/test_trailing_stop.py",
           "tests/unit/test_volume_and_order_size.py",
           "tests/unit/test_equity.py",
           "tests/unit/test_rebalance.py",
           "tests/unit/test_trade_accounting.py",       # Phase 1: closed vs open trade counting
           "tests/unit/test_final_liquidation.py",       # Phase 1: exit_type labeling
           "tests/unit/test_partial_close.py"            # Phase 3: sell trade partial close handling
       )
    },

    # --Features & alignment --
    @{ Label = "Features & Alignment";
       Args  = @(
           "tests/unit/test_alignment.py",
           "tests/unit/test_feature_controller_compat.py",
           "tests/unit/test_features_parity.py",
           "tests/unit/test_native_parity.py",           # Phase 2: native controller parity
           "tests/unit/test_regime.py",
           "tests/unit/test_simconfig_controller_compat.py",
           "tests/unit/test_controller_compat_propagation.py", # Fix 4: compat propagation
           "-m", "not slow"
       )
    },

    # --Data pipeline & candle audit --
    @{ Label = "Data Pipeline & Audit";
       Args  = @(
           "tests/unit/test_candles.py",
           "tests/unit/test_gaps.py",
           "tests/unit/test_hashing.py",
           "tests/unit/test_mongo_loader.py",
           "tests/unit/test_quality.py",
           "tests/unit/test_synthetic_audit.py"
       )
    },

    # --Strategies --
    @{ Label = "Strategies";
       Args  = @(
           "tests/unit/test_pmm_dynamic_strategy.py",
           "tests/unit/test_bollinger_strategy.py",
           "tests/unit/test_bollinger_engine_integration.py",
           "tests/unit/test_strategy_factory.py",
           "tests/unit/test_strategy_protocol.py",
           "tests/unit/test_generic_runner.py"
       )
    },

    # --Signal caching --
    @{ Label = "Signal Caching";
       Args  = @(
           "tests/unit/test_signal_cache.py",
           "tests/unit/test_signal_cache_shared.py",
           "tests/unit/test_signal_cache_perf.py",
           "tests/unit/test_signal_output.py",
           "tests/unit/test_walkforward_signal_cache_parity.py",
           "tests/unit/test_sensitivity_signal_cache_parity.py"
       )
    },

    # --Objective functions (v1 & v2) --
    @{ Label = "Objectives & Metrics";
       Args  = @(
           "tests/unit/test_objective.py",
           "tests/unit/test_objective_v2.py",
           "tests/unit/test_metrics.py",
           "tests/unit/test_metrics_v2_fields.py",
           "tests/unit/test_robustness.py",
           "tests/unit/test_market_tp_fee_attribution.py"
       )
    },

    # --Stress testing --
    @{ Label = "Stress Testing";
       Args  = @(
           "tests/unit/test_stress.py",
           "tests/unit/test_fold_local_stress.py",
           "tests/unit/test_objective_v2_stress_passthrough.py",
           "tests/unit/test_stress_selection.py"
       )
    },

    # --Holdout & walk-forward --
    @{ Label = "Holdout & Walk-Forward";
       Args  = @(
           "tests/unit/test_holdout.py",
           "tests/unit/test_holdout_warmstart.py",
           "tests/unit/test_holdout_stress_local.py",
           "tests/unit/test_holdout_config_consistency.py",  # Phase 1: export matches holdout config
           "tests/unit/test_holdout_exported_candidate.py", # Fix 3: exported candidate gating
           "tests/unit/test_holdout_signal_cache.py",
           "tests/unit/test_walkforward.py"
       )
    },

    # --Recent-window evaluation --
    @{ Label = "Recent Window";
       Args  = @(
           "tests/unit/test_recent_window.py"
       )
    },

    # --Optuna optimization --
    @{ Label = "Optuna & Optimization";
       Args  = @(
           "tests/unit/test_search_space.py",
           "tests/unit/test_canonicalizer.py",
           "tests/unit/test_sensitivity.py",
           "tests/unit/test_clustering.py",
           "tests/unit/test_parallel.py",
           "tests/unit/test_preflight.py",
           "tests/unit/test_storage.py",
           "tests/unit/test_storage_safety.py",
           "tests/unit/test_optuna_failure_telemetry.py",  # Already existed, was missing from script
           "tests/unit/test_multi_pair_sweep_notebook.py"  # Already existed, was missing from script
       )
    },

    # --Export & validation --
    @{ Label = "Export & Validation";
       Args  = @(
           "tests/unit/test_yaml_export.py",
           "tests/unit/test_yaml_validates.py",
           "tests/unit/test_validate_export_v2.py",
           "tests/unit/test_exchange_rules.py",
           "tests/unit/test_export_contract.py",         # Phase 2: field set contract
           "tests/unit/test_price_rounding.py"            # Phase 3: side-aware rounding
       )
    },

    # --Deploy, report & parity --
    @{ Label = "Deploy & Report";
       Args  = @(
           "tests/unit/test_deploy_package.py",
           "tests/unit/test_pipeline_runner.py",
           "tests/unit/test_pipeline_robustness.py",     # Phase 1: zero-trial, SQLite enforcement
           "tests/unit/test_report.py",
           "tests/unit/test_comparison.py",
           "tests/unit/test_monitor.py",
           "tests/unit/test_parity_harness.py",
           "tests/unit/test_stop_ship_parity.py",        # Phase 2: parity gate in stop-ship
           "tests/unit/test_stop_ship_clustering.py",    # Phase 2: clustering gate in stop-ship
           "tests/unit/test_live_tracker_fees.py",        # Phase 2: fee conversion
           "tests/unit/test_live_tracker_health.py"
       )
    },

    # --Determinism & reproducibility --
    @{ Label = "Determinism & Reproducibility";
       Args  = @(
           "tests/unit/test_determinism.py",
           "tests/unit/test_reproducibility.py",
           "tests/unit/test_replay.py"
       )
    },

    # --Frozen regression (golden values) --
    @{ Label = "Frozen Regression";
       Args  = @(
           "tests/regression/test_determinism_regression.py"
       )
    },

    # --Public Screeners --
    @{ Label = "Public Screeners";
       Args  = @(
           "tests/unit/test_public_screeners.py",
           "tests/unit/test_public_screener_notebooks.py",
           "tests/unit/test_screener_common.py",
           "tests/unit/test_screener_quant_patch.py",
           "tests/unit/test_screener_multi_quote.py"
       )
    },

    # --Integration tests --
    @{ Label = "Integration";
       Args  = @(
           "tests/integration/test_acceptance.py",
           "tests/integration/test_end_to_end.py",
           "tests/integration/test_optuna_smoke.py",
           "tests/integration/test_live_tracker.py",
           "tests/integration/test_mongo_live.py"
       )
    }
)

# --- Run ---
Push-Location $pmmDynamic
$startTime = Get-Date

try {
    if ($Grouped) {
        # --- Grouped mode: run each category separately ---
        $totalPassed  = 0
        $totalFailed  = 0
        $totalSkipped = 0
        $groupResults = @()

        foreach ($group in $testGroups) {
            $lbl = $group.Label
            Write-Host "`n--$lbl --" -ForegroundColor Yellow
            "--$lbl --" | Out-File -FilePath $logFile -Append -Encoding UTF8

            $pytestArgs = @("-m", "pytest") + $group.Args + @("-v", $tbFlag, "-q")
            $output = & python @pytestArgs 2>&1 | Out-String
            $code = $LASTEXITCODE
            Write-Host $output
            $output | Out-File -FilePath $logFile -Append -Encoding UTF8

            # Parse counts from pytest summary line, e.g. "36 passed, 2 failed in 1.5s"
            if ($output -match "(\d+)\s+passed")  { $p = [int]$Matches[1] } else { $p = 0 }
            if ($output -match "(\d+)\s+failed")  { $f = [int]$Matches[1] } else { $f = 0 }
            if ($output -match "(\d+)\s+skipped") { $s = [int]$Matches[1] } else { $s = 0 }

            $totalPassed  += $p
            $totalFailed  += $f
            $totalSkipped += $s
            # Fail on non-zero exit code OR parsed failures OR errors
            if ($output -match "(\d+)\s+error") { $e = [int]$Matches[1] } else { $e = 0 }
            $status = if ($f -eq 0 -and $e -eq 0 -and $code -eq 0) { "PASS" } else { "FAIL" }
            if ($code -ne 0 -and $f -eq 0 -and $e -eq 0) {
                Write-Host "  WARNING: pytest exited $code but no failures parsed — possible collection error" -ForegroundColor Yellow
            }
            if ($code -ne 0 -and $f -eq 0) { $totalFailed += 1 }  # count collection errors as failures
            $groupResults += [PSCustomObject]@{ Group = $lbl; Passed = $p; Failed = $f; Skipped = $s; Status = $status }
        }

        # --- Group summary table ---
        Write-Host "`n`n============================================================" -ForegroundColor Cyan
        Write-Host "  GROUP SUMMARY" -ForegroundColor Cyan
        Write-Host "============================================================" -ForegroundColor Cyan
        $groupResults | Format-Table -AutoSize | Out-String | Write-Host
        Write-Host "  TOTALS: $totalPassed passed, $totalFailed failed, $totalSkipped skipped" -ForegroundColor $(if ($totalFailed -eq 0) { "Green" } else { "Red" })

        $exitCode = if ($totalFailed -eq 0) { 0 } else { 1 }
    }
    else {
        # --- Standard mode: single pytest run (auto-discovery) ---
        $testPath = if ($Quick) { "tests/unit" } else { "tests" }

        if ($Verbose) {
            python -m pytest $testPath -v --tb=long 2>&1 | Tee-Object -FilePath $logFile -Append
        }
        else {
            python -m pytest $testPath -v --tb=short 2>&1 | Tee-Object -FilePath $logFile -Append
        }
        $exitCode = $LASTEXITCODE
    }
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
