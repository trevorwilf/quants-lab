"""Edit all 3 sweep notebooks: preflight fallback + analysis gate export block."""
import json
import sys

NOTEBOOKS = {
    "multi_pair": {
        "path": "notebooks/pmm_dynamic/pmm_dynamic_multi_pair_sweep.ipynb",
        "sweep_cell": 8,
        "var_style": "upper",  # CONNECTOR, INTERVAL, BAR_INTERVAL_SECONDS
    },
    "multi_exchange": {
        "path": "notebooks/pmm_dynamic/pmm_dynamic_multi_exchange_sweep_mexc_nonkyc.ipynb",
        "sweep_cell": 8,
        "var_style": "lower",  # connector, interval, bar_interval_seconds
    },
    "single_pair": {
        "path": "notebooks/pmm_dynamic/pmm_dynamic_single_pair_sweep_mexc_xmr_usdt.ipynb",
        "sweep_cell": 7,
        "var_style": "upper",
    },
}

# ── Preflight fix (same for all 3) ──
OLD_PREFLIGHT_EXCEPT = 'except Exception as e:\n    print(f"Preflight info: {e}")'
NEW_PREFLIGHT_EXCEPT = (
    'except Exception as e:\n'
    '    print(f"Preflight info: {e}")\n'
    '    # Ensure preflight_report is always defined even on failure\n'
    '    preflight_report = type("FailedPreflight", (), {"passed": False, "errors": [str(e)]})()'
)


def build_export_block_raw(var_style):
    """Build the new analysis gate + export block with correct indentation."""
    if var_style == "lower":
        CONN = "connector"
        INTV = "interval"
        BAR_SEC = "bar_interval_seconds"
    else:
        CONN = "CONNECTOR"
        INTV = "INTERVAL"
        BAR_SEC = "BAR_INTERVAL_SECONDS"

    lines = []
    a = lines.append

    a('    # ── Analysis gate ──')
    a('    preflight_passed = getattr(preflight_report, "passed", False) if "preflight_report" in dir() else False')
    a('    score_gate_passed = best["robust_score"] >= MIN_ROBUST_SCORE')
    a('    analysis_gate_passed = preflight_passed and score_gate_passed')
    a('')
    a('    result_entry["preflight_passed"] = preflight_passed')
    a('    result_entry["score_gate_passed"] = score_gate_passed')
    a('    result_entry["analysis_gate_passed"] = analysis_gate_passed')
    a('')
    a('    if analysis_gate_passed:')
    a('        try:')
    a('            export_params = ExportParams(')
    a(f'                connector_name={CONN},')
    a('                trading_pair=pair,')
    a(f'                candles_connector={CONN},')
    a('                candles_trading_pair=pair,')
    a(f'                interval={INTV},')
    a('            )')
    a('')
    a('            yaml_path = export_yaml(')
    a('                config=best_config,')
    a(f'                output_path=f"artifacts/sweep/{{{CONN}}}/{{pair}}_{{{INTV}}}_best.yaml",')
    a('                export_params=export_params,')
    a('                metadata={')
    a('                    "dataset_hash": dataset_hash,')
    a('                    "trial": best["trial_number"],')
    a('                    "phase1_score": best["phase1_score"],')
    a('                    "robust_score": best["robust_score"],')
    a('                    "worst_scenario": best["worst_scenario"],')
    a('                    "worst_score": best["worst_score"],')
    a('                    "sweep_date": datetime.now(timezone.utc).isoformat(),')
    a('                },')
    a('            )')
    a('')
    a('            # Validate exported YAML')
    a('            yaml_val = validate_yaml_file(yaml_path)')
    a('')
    a('            # Walk-forward for report')
    a('            wf_result = run_walk_forward(')
    a('                candles=candles, config=best_config, pair_rules=pair_rules,')
    a(f'                bar_interval_seconds={BAR_SEC}, dataset_hash=dataset_hash,')
    a('                train_days=train_days, test_days=test_days, step_days=step_days,')
    a('                objective_version=OBJECTIVE_VERSION,')
    a('            )')
    a('')
    a('            checks = run_stop_ship_checks(')
    a('                best_metrics=best_metrics, best_objective=best_obj,')
    a('                walkforward_result=wf_result, stress_report=best_stress,')
    a('                dataset_audit=audit, validation_result=yaml_val,')
    a('            )')
    a('')
    a('            coverage = build_validation_coverage(')
    a('                dataset_audit=audit,')
    a('                validation_result=yaml_val,')
    a('                walkforward_result=wf_result,')
    a('                stress_report=best_stress,')
    a('            )')
    a('')
    a('            score_summary = {')
    a('                "phase1_best": best.get("phase1_score"),')
    a('                "robust_score": best["robust_score"],')
    a('                "baseline_score": best["baseline_score"],')
    a('                "worst_score": best["worst_score"],')
    a('                "worst_scenario": best["worst_scenario"],')
    a('            }')
    a('            analysis_status = {')
    a('                "preflight_passed": preflight_passed,')
    a('                "score_gate_passed": score_gate_passed,')
    a('                "analysis_gate_passed": analysis_gate_passed,')
    a('            }')
    a('            run_provenance = {')
    a('                "n_trials": N_TRIALS,')
    a('                "n_jobs": N_JOBS,')
    a('                "objective_version": OBJECTIVE_VERSION,')
    a('                "controller_compat": SEARCH_CONTROLLER_COMPAT,')
    a('                "sweep_date": datetime.now(timezone.utc).isoformat(),')
    a('            }')
    a('')
    a('            generate_report(')
    a('                study_name=study_name,')
    a('                dataset_summary={')
    a(f'                    "connector": {CONN}, "trading_pair": pair, "interval": {INTV},')
    a('                    "n_candles": len(candles), "dataset_hash": dataset_hash,')
    a('                    "n_trials_phase1": N_TRIALS, "n_candidates_stressed": len(top_candidates),')
    a('                    "total_amount_quote_search_min": 25.0,')
    a('                    "total_amount_quote_search_max": 1000.0,')
    a('                    "total_amount_quote_ideal": best_config.total_amount_quote,')
    a('                    "search_controller_compat": SEARCH_CONTROLLER_COMPAT,')
    a('                },')
    a('                best_params=best["params"], best_metrics=best_metrics, best_objective=best_obj,')
    a('                walkforward_result=wf_result, stress_report=best_stress,')
    a('                stop_ship_checks=checks,')
    a(f'                output_path=f"artifacts/sweep/{{{CONN}}}/{{pair}}_{{{INTV}}}_report.md",')
    a('                score_summary=score_summary,')
    a('                analysis_status=analysis_status,')
    a('                run_provenance=run_provenance,')
    a('                validation_coverage=coverage,')
    a('                dataset_audit=audit,')
    a('                yaml_validation_result=yaml_val,')
    a('                preflight_report=preflight_report if "preflight_report" in dir() else None,')
    a('                canonical_config=best_config,')
    a('            )')
    a('')
    a('            result_entry["exported"] = True')
    a('            result_entry["yaml_path"] = yaml_path')
    a('            all_pass = all(checks.values())')
    a('            result_entry["all_checks_pass"] = all_pass')
    a("            print(f\"  EXPORTED  yaml={yaml_path}  checks={'ALL PASS' if all_pass else 'SOME FAIL'}\")")
    a('        except Exception as e:')
    a('            print(f"  Export failed: {e}")')
    a('            result_entry["exported"] = False')
    a('    else:')
    a('        result_entry["exported"] = False')
    a('        if not preflight_passed:')
    a('            print(f"  GATE FAIL: preflight did not pass")')
    a('        if not score_gate_passed:')
    a("            print(f\"  GATE FAIL: robust={best['robust_score']:.4f} < {MIN_ROBUST_SCORE}\")")

    return "\n".join(lines)


def process_notebook(name, info):
    nb_path = info["path"]
    sweep_cell_idx = info["sweep_cell"]
    var_style = info["var_style"]

    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # ── 1. Fix Cell 4 preflight ──
    cell4_src = "".join(nb["cells"][4]["source"])
    if OLD_PREFLIGHT_EXCEPT in cell4_src:
        cell4_src = cell4_src.replace(OLD_PREFLIGHT_EXCEPT, NEW_PREFLIGHT_EXCEPT)
        lines = cell4_src.split("\n")
        nb["cells"][4]["source"] = [
            line + "\n" if i < len(lines) - 1 else line
            for i, line in enumerate(lines)
        ]
        print(f"  [{name}] Cell 4: preflight fallback added")
    elif "FailedPreflight" in cell4_src:
        print(f"  [{name}] Cell 4: already has FailedPreflight (skipping)")
    else:
        print(f"  [{name}] Cell 4: WARNING - could not find except block to replace")

    # ── 2. Fix sweep cell imports ──
    sweep_src = "".join(nb["cells"][sweep_cell_idx]["source"])

    # Add build_validation_coverage to imports if missing
    if "build_validation_coverage" not in sweep_src:
        old_import = "from pmm_lab.report.report_md import generate_report, run_stop_ship_checks"
        new_import = "from pmm_lab.report.report_md import generate_report, run_stop_ship_checks, build_validation_coverage"
        if old_import in sweep_src:
            sweep_src = sweep_src.replace(old_import, new_import)
            print(f"  [{name}] Sweep cell: added build_validation_coverage import")
        else:
            print(f"  [{name}] Sweep cell: WARNING - could not find report import line")

    # Ensure validate_yaml_file import exists (it already does in all 3, but check)
    if "from pmm_lab.export.validate_export import validate_yaml_file" not in sweep_src:
        old_hb = "from pmm_lab.export.hb_yaml import export_yaml, ExportParams"
        new_hb = old_hb + "\nfrom pmm_lab.export.validate_export import validate_yaml_file"
        if old_hb in sweep_src:
            sweep_src = sweep_src.replace(old_hb, new_hb)
            print(f"  [{name}] Sweep cell: added validate_yaml_file import")

    # ── 3. Replace export block ──
    old_marker = '    # ── Export if profitable ──\n'
    old_export_start = '    if best["robust_score"] >= MIN_ROBUST_SCORE:'

    export_comment_idx = sweep_src.find(old_marker)
    if export_comment_idx == -1:
        export_comment_idx = sweep_src.find(old_export_start)
        if export_comment_idx == -1:
            print(f"  [{name}] Sweep cell: WARNING - could not find export block")
            return

    # Find `total_elapsed` which comes after the export block
    total_elapsed_marker = "\ntotal_elapsed = time.time()"
    total_elapsed_idx = sweep_src.find(total_elapsed_marker)
    if total_elapsed_idx == -1:
        print(f"  [{name}] Sweep cell: WARNING - could not find total_elapsed marker")
        return

    # Build new block
    new_block = build_export_block_raw(var_style)

    sweep_src = sweep_src[:export_comment_idx] + new_block + sweep_src[total_elapsed_idx:]

    print(f"  [{name}] Sweep cell: export block replaced")

    # ── 4. Write back ──
    lines = sweep_src.split("\n")
    nb["cells"][sweep_cell_idx]["source"] = [
        line + "\n" if i < len(lines) - 1 else line
        for i, line in enumerate(lines)
    ]

    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")

    print(f"  [{name}] Saved: {nb_path}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for name, info in NOTEBOOKS.items():
        print(f"\nProcessing {name}...")
        process_notebook(name, info)

    # ── Verify compilation ──
    print("\n=== Verification ===")
    errors = []
    for name, info in NOTEBOOKS.items():
        nb_path = info["path"]
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
        for i, cell in enumerate(nb["cells"]):
            if cell["cell_type"] == "code":
                src = "".join(cell["source"])
                try:
                    compile(src, f"{nb_path}:cell{i}", "exec")
                except SyntaxError as e:
                    errors.append(f"  {name} cell {i} line {e.lineno}: {e.msg}")

    if errors:
        print("COMPILATION ERRORS:")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print("All cells compile OK")

    # Check key patterns
    for name, info in NOTEBOOKS.items():
        nb_path = info["path"]
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
        all_src = "".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")

        checks = [
            ("FailedPreflight", "FailedPreflight" in all_src),
            ("build_validation_coverage", "build_validation_coverage" in all_src),
            ("validate_yaml_file", "validate_yaml_file" in all_src),
            ("analysis_gate_passed", "analysis_gate_passed" in all_src),
            ("score_summary", "score_summary" in all_src),
            ("run_provenance", "run_provenance" in all_src),
            ("objective_version=OBJECTIVE_VERSION", "objective_version=OBJECTIVE_VERSION" in all_src),
        ]
        failed = [c[0] for c in checks if not c[1]]
        if failed:
            print(f"  {name}: MISSING patterns: {failed}")
            sys.exit(1)
        else:
            print(f"  {name}: all patterns present")

    print("\nDone!")


if __name__ == "__main__":
    main()
