"""Edit all 3 sweep notebooks using json.load/json.dump per the spec."""
import json
import sys


NB_DIR = "E:/tradingsoftware/quants-lab/research_notebooks/market_lab/pmm_dynamic/notebooks/pmm_dynamic"

NOTEBOOKS = {
    "multi_pair": {
        "path": f"{NB_DIR}/pmm_dynamic_multi_pair_sweep.ipynb",
        "config_cell_idx": 3,
        "sweep_cell_idx": 8,
        "var_style": "upper",
    },
    "multi_exchange": {
        "path": f"{NB_DIR}/pmm_dynamic_multi_exchange_sweep_mexc_nonkyc.ipynb",
        "config_cell_idx": 3,
        "sweep_cell_idx": 8,
        "var_style": "lower",
    },
    "single_pair": {
        "path": f"{NB_DIR}/pmm_dynamic_single_pair_sweep_mexc_xmr_usdt.ipynb",
        "config_cell_idx": 3,
        "sweep_cell_idx": 7,
        "var_style": "upper",
    },
}


def get_bar_var(style):
    return "BAR_INTERVAL_SECONDS" if style == "upper" else "bar_interval_seconds"


def edit_config_cell(source_lines, style):
    """Phase 1A: Add VALIDATION_CONTROLLER_COMPAT after SEARCH_CONTROLLER_COMPAT."""
    new_lines = []
    already_present = any("VALIDATION_CONTROLLER_COMPAT" in l for l in source_lines)
    for line in source_lines:
        new_lines.append(line)
        if (not already_present
            and line.strip().startswith("SEARCH_CONTROLLER_COMPAT")
            and "=" in line
            and "controller_compat" not in line.lower()):
            new_lines.append("VALIDATION_CONTROLLER_COMPAT = True\n")
    return new_lines


def edit_sweep_cell(source_lines, style):
    """Apply all sweep cell edits."""
    source = "".join(source_lines)
    bar_var = get_bar_var(style)

    # ── Phase 1B: Add new imports after CandleSimRunner ──
    new_imports = (
        "from pmm_lab.objective.recent_window import evaluate_recent_window\n"
        "from pmm_lab.objective.holdout import evaluate_holdout\n"
        "from pmm_lab.objective.dataset_split import split_for_release_gate\n"
        "from pmm_lab.optuna.sensitivity import compute_sensitivity\n"
        "from pmm_lab.optuna.clustering import analyze_top_k\n"
        "from pmm_lab.parity.feature_parity import check_feature_parity_frozen\n"
        "from pmm_lab.parity.fixtures import load_frozen_fixture\n"
        "from dataclasses import replace as _replace\n"
    )
    anchor = "from pmm_lab.sim.runner import CandleSimRunner\n"
    source = source.replace(anchor, anchor + new_imports, 1)

    # ── Phase 3A: Add dataset split BEFORE "# ── Exchange rules ──" ──
    dataset_split_block = (
        "\n"
        "    # ── Dataset split for release gate ──\n"
        "    try:\n"
        "        dataset_slices = split_for_release_gate(candles, recent_days=28, holdout_fraction=0.20, min_pre_release_bars=200, min_holdout_bars=50)\n"
        "        dev_candles = dataset_slices.dev_candles\n"
        "        dev_dataset_hash = hash_candles(dev_candles)\n"
        '        print(f"  Split: dev={len(dev_candles)} holdout={len(dataset_slices.holdout_candles)} recent={len(dataset_slices.recent_release_candles)}")\n'
        "    except ValueError as e:\n"
        '        print(f"  Split failed ({e}), using full candles")\n'
        "        dataset_slices = None\n"
        "        dev_candles = candles\n"
        "        dev_dataset_hash = dataset_hash\n"
        "\n"
    )
    source = source.replace(
        "    # ── Exchange rules ──\n",
        dataset_split_block + "    # ── Exchange rules ──\n",
        1,
    )

    # ── Phase 3C: Change optimization to use dev_candles ──
    # Only inside factory_kwargs block
    factory_start = source.find("factory_kwargs=dict(")
    if factory_start >= 0:
        factory_end = source.find("),\n", factory_start)
        if factory_end >= 0:
            factory_end += 3  # include ),\n
            old_block = source[factory_start:factory_end]
            new_block = old_block.replace("candles=candles,", "candles=dev_candles,", 1)
            new_block = new_block.replace("dataset_hash=dataset_hash,", "dataset_hash=dev_dataset_hash,", 1)
            source = source[:factory_start] + new_block + source[factory_end:]

    # ── Phase 0D: Change YAML export paths ──
    source = source.replace("_best.yaml", "_screening_best.yaml")

    # ── Phase 1C: Add validation block BEFORE "    # ── Record result ──" ──
    validation_block = (
        "\n"
        "    # ── Finalist validation ──\n"
        "    val_config = _replace(best_config, controller_compat=VALIDATION_CONTROLLER_COMPAT)\n"
        "\n"
        "    recent_window_result = None\n"
        "    try:\n"
        "        recent_window_result = evaluate_recent_window(\n"
        "            full_candles=candles, config=val_config, pair_rules=pair_rules,\n"
       f"            bar_interval_seconds={bar_var},\n"
        "            recent_days=28, run_stress=True, objective_version=OBJECTIVE_VERSION,\n"
        "        )\n"
        '        print(f"  Recent 28d: {\'PASS\' if recent_window_result.passed else \'FAIL\'} ' + '\\u2014 {recent_window_result.reason}")\n'
        "    except Exception as e:\n"
        '        print(f"  Recent 28d: ERROR \\u2014 {e}")\n'
        "\n"
        "    holdout_report = None\n"
        "    try:\n"
        "        from pmm_lab.objective.holdout import split_holdout\n"
        "        dev_candles_h, holdout_candles_h = split_holdout(candles, 0.20, min_holdout_bars=50)\n"
        '        holdout_candidates = [(val_config, best.get("robust_score", 0.0))]\n'
        "        for t_idx in range(1, min(5, len(top_candidates))):\n"
        "            tc = top_candidates[t_idx]\n"
        '            tc_config = canonicalize_params(tc["params"], pair_rules, ref_price)[0]\n'
        "            if tc_config is not None:\n"
        "                tc_config = _replace(tc_config, controller_compat=VALIDATION_CONTROLLER_COMPAT)\n"
        '                holdout_candidates.append((tc_config, tc.get("phase1_score", 0.0)))\n'
        "        holdout_report = evaluate_holdout(\n"
       f"            holdout_candles_h, holdout_candidates, pair_rules, {bar_var},\n"
        "            run_stress=True, objective_version=OBJECTIVE_VERSION,\n"
        "            full_candles=candles, holdout_start_idx=len(dev_candles_h),\n"
        "        )\n"
        '        print(f"  Holdout: {\'PASS\' if holdout_report.exported_holdout_passed else \'FAIL\'}")\n'
        "    except Exception as e:\n"
        '        print(f"  Holdout: ERROR \\u2014 {e}")\n'
        "\n"
        "    sensitivity_report = None\n"
        "    sensitivity_penalty = None\n"
        "    try:\n"
        "        sensitivity_report = compute_sensitivity(\n"
       f'            best["params"], candles, pair_rules, {bar_var}, ref_price,\n'
        "            objective_version=OBJECTIVE_VERSION, controller_compat=VALIDATION_CONTROLLER_COMPAT,\n"
        "        )\n"
        "        sensitivity_penalty = sensitivity_report.sensitivity_penalty\n"
        '        print(f"  Sensitivity: penalty={sensitivity_penalty:.4f}")\n'
        "    except Exception as e:\n"
        '        print(f"  Sensitivity: ERROR \\u2014 {e}")\n'
        "\n"
        "    cluster_report = None\n"
        "    try:\n"
        "        cluster_report = analyze_top_k(study, k=min(10, len(ranked)))\n"
        '        print(f"  Clustering: {\'CLUSTERED\' if cluster_report.is_clustered else \'SCATTERED\'}")\n'
        "    except Exception as e:\n"
        '        print(f"  Clustering: ERROR \\u2014 {e}")\n'
        "\n"
        "    parity_result = None\n"
        "    long_parity_result = None\n"
        "    try:\n"
        "        from pathlib import Path as _Path\n"
        "        _fix_base = _Path(__file__).resolve().parent.parent if '__file__' in dir() else _Path(\"fixtures\")\n"
        "        if not _fix_base.is_dir():\n"
        '            _fix_base = _Path("research_notebooks/market_lab/pmm_dynamic/fixtures")\n'
        "        if not _fix_base.is_dir():\n"
        '            _fix_base = _Path("fixtures")\n'
        '        _short = _fix_base / "short_100bar_compat"\n'
        "        if _short.is_dir():\n"
        "            _f = load_frozen_fixture(str(_short))\n"
        "            parity_result = check_feature_parity_frozen(_f.candles, _f.expected_features, _f.config_params)\n"
        '        _long = _fix_base / "long_500bar_compat"\n'
        "        if _long.is_dir():\n"
        "            _lf = load_frozen_fixture(str(_long))\n"
        "            long_parity_result = check_feature_parity_frozen(_lf.candles, _lf.expected_features, _lf.config_params)\n"
        """        print(f"  Parity: short={'PASS' if parity_result and parity_result.passed else 'N/A'}, long={'PASS' if long_parity_result and long_parity_result.passed else 'N/A'}")\n"""
        "    except Exception as e:\n"
        '        print(f"  Parity: ERROR \\u2014 {e}")\n'
        "\n"
        "    full_validation_executed = all([recent_window_result is not None, holdout_report is not None])\n"
        "\n"
    )
    source = source.replace(
        "    # ── Record result ──\n",
        validation_block + "    # ── Record result ──\n",
        1,
    )

    # ── Phase 1H: Add validation results to result_entry ──
    old_result_tail = (
        '        "study_name": study_name,\n'
        '    }\n'
        '    sweep_results.append(result_entry)\n'
    )
    new_result_tail = (
        '        "study_name": study_name,\n'
        '        "recent_window_result": recent_window_result,\n'
        '        "holdout_report": holdout_report,\n'
        '        "sensitivity_report": sensitivity_report,\n'
        '        "sensitivity_penalty": sensitivity_penalty,\n'
        '        "cluster_report": cluster_report,\n'
        '        "parity_result": parity_result,\n'
        '        "long_parity_result": long_parity_result,\n'
        '        "full_validation_executed": full_validation_executed,\n'
        '        "dataset_slices": dataset_slices if \'dataset_slices\' in dir() else None,\n'
        '    }\n'
        '    sweep_results.append(result_entry)\n'
    )
    source = source.replace(old_result_tail, new_result_tail, 1)

    # ── Phase 0A + 1G: Replace analysis_status dict ──
    old_analysis = (
        '            analysis_status = {\n'
        '                "preflight_passed": preflight_passed,\n'
        '                "score_gate_passed": score_gate_passed,\n'
        '                "analysis_gate_passed": analysis_gate_passed,\n'
        '            }\n'
    )
    new_analysis = (
        '            analysis_status = {\n'
        '                "report_mode": "validated" if full_validation_executed else "screening",\n'
        '                "preflight": "PASS" if preflight_passed else "FAIL",\n'
        '                "score": "PASS" if score_gate_passed else "FAIL",\n'
        '                "analysis": "PASS" if analysis_gate_passed else "FAIL",\n'
        '            }\n'
    )
    source = source.replace(old_analysis, new_analysis, 1)

    # ── Phase 0B: Update score_summary dict ──
    old_score = (
        '            score_summary = {\n'
        '                "phase1_best": best.get("phase1_score"),\n'
        '                "robust_score": best["robust_score"],\n'
        '                "baseline_score": best["baseline_score"],\n'
        '                "worst_score": best["worst_score"],\n'
        '                "worst_scenario": best["worst_scenario"],\n'
        '            }\n'
    )
    new_score = (
        '            score_summary = {\n'
        '                "phase1": best.get("phase1_score"),\n'
        '                "robust": best["robust_score"],\n'
        '                "baseline_score": best["baseline_score"],\n'
        '                "worst": best["worst_score"],\n'
        '                "worst_scenario": best["worst_scenario"],\n'
        '                "min_robust_score": MIN_ROBUST_SCORE,\n'
        '                "score_gate_passed": score_gate_passed,\n'
        '            }\n'
    )
    source = source.replace(old_score, new_score, 1)

    # ── Phase 0D: Add validated_best.yaml copy after all_pass ──
    old_allpass = '            all_pass = all(checks.values())\n'
    new_allpass = (
        '            all_pass = all(checks.values())\n'
        '            if all_pass:\n'
        '                import shutil\n'
        '                _validated_path = yaml_path.replace("_screening_best.yaml", "_validated_best.yaml")\n'
        '                shutil.copy2(yaml_path, _validated_path)\n'
        '                print(f"  VALIDATED  yaml={_validated_path}")\n'
    )
    source = source.replace(old_allpass, new_allpass, 1)

    # ── Phase 1D: Update run_stop_ship_checks call ──
    old_checks = (
        '            checks = run_stop_ship_checks(\n'
        '                best_metrics=best_metrics, best_objective=best_obj,\n'
        '                walkforward_result=wf_result, stress_report=best_stress,\n'
        '                dataset_audit=audit, validation_result=yaml_val,\n'
        '            )\n'
    )
    new_checks = (
        '            checks = run_stop_ship_checks(\n'
        '                best_metrics=best_metrics, best_objective=best_obj,\n'
        '                walkforward_result=wf_result, stress_report=best_stress,\n'
        '                dataset_audit=audit, validation_result=yaml_val,\n'
        '                holdout_report=holdout_report,\n'
        '                sensitivity_penalty=sensitivity_penalty,\n'
        '                recent_window_result=recent_window_result,\n'
        '                parity_result=parity_result,\n'
        '                long_parity_result=long_parity_result,\n'
        '                cluster_report=cluster_report,\n'
        '            )\n'
    )
    source = source.replace(old_checks, new_checks, 1)

    # ── Phase 1E: Update build_validation_coverage call ──
    old_coverage = (
        '            coverage = build_validation_coverage(\n'
        '                dataset_audit=audit,\n'
        '                validation_result=yaml_val,\n'
        '                walkforward_result=wf_result,\n'
        '                stress_report=best_stress,\n'
        '            )\n'
    )
    new_coverage = (
        '            coverage = build_validation_coverage(\n'
        '                dataset_audit=audit,\n'
        '                validation_result=yaml_val,\n'
        '                walkforward_result=wf_result,\n'
        '                stress_report=best_stress,\n'
        '                holdout_report=holdout_report,\n'
        '                sensitivity_report=sensitivity_report,\n'
        '                recent_window_result=recent_window_result,\n'
        '                parity_result=parity_result,\n'
        '                long_parity_result=long_parity_result,\n'
        '                cluster_report=cluster_report,\n'
        '            )\n'
    )
    source = source.replace(old_coverage, new_coverage, 1)

    # ── Phase 1F: Update generate_report call ──
    old_gen_tail = (
        '                canonical_config=best_config,\n'
        '            )\n'
    )
    new_gen_tail = (
        '                canonical_config=best_config,\n'
        '                holdout_report=holdout_report,\n'
        '                sensitivity_report=sensitivity_report,\n'
        '                recent_window_result=recent_window_result,\n'
        '                cluster_report=cluster_report,\n'
        '                parity_result=parity_result,\n'
        '                long_parity_result=long_parity_result,\n'
        '            )\n'
    )
    source = source.replace(old_gen_tail, new_gen_tail, 1)

    # ── Phase 0A: Remove analysis_gate_passed from the block before the if ──
    # The "analysis_gate_passed" check used to only gate on preflight+score.
    # The analysis_status dict is now updated above. No additional changes needed
    # since the old keys (preflight_passed etc.) on result_entry stay.

    return source.splitlines(True)


def process_notebook(name, info):
    print(f"\nProcessing {name}: {info['path']}")

    with open(info["path"], "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Edit config cell
    config_cell = nb["cells"][info["config_cell_idx"]]
    assert config_cell["cell_type"] == "code", f"Config cell {info['config_cell_idx']} is not code"
    config_cell["source"] = edit_config_cell(config_cell["source"], info["var_style"])

    # Edit sweep cell
    sweep_cell = nb["cells"][info["sweep_cell_idx"]]
    assert sweep_cell["cell_type"] == "code", f"Sweep cell {info['sweep_cell_idx']} is not code"
    sweep_cell["source"] = edit_sweep_cell(sweep_cell["source"], info["var_style"])

    # Clear outputs
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            cell["outputs"] = []
            cell["execution_count"] = None

    with open(info["path"], "w", encoding="utf-8", newline="\n") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")

    print(f"  Written: {info['path']}")


def main():
    for name, info in NOTEBOOKS.items():
        process_notebook(name, info)
    print("\nAll notebooks edited successfully.")


if __name__ == "__main__":
    main()
