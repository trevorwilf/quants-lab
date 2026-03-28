"""fix_notebooks.py — Programmatic edits to sweep notebooks.

Applies all remediation fixes from the quant expert review:
- Phase 1: Fix run_stop_ship_checks() and generate_report() wiring
- Phase 1c: Add validate_yaml_file() call
- Phase 2: Fix future-data leakage (candles -> dev_candles)
- Phase 3: Fix holdout to use dataset_slices
- Phase 4: Fix walk-forward objective version and config
- Phase 8: Add run provenance
"""
import json
import re
import sys
from pathlib import Path

NB_DIR = Path(__file__).parent / "notebooks" / "pmm_dynamic"

NOTEBOOKS = {
    "multi_exchange": {
        "path": NB_DIR / "pmm_dynamic_multi_exchange_sweep_mexc_nonkyc.ipynb",
        "sweep_cell_idx": 8,
        "bar_var": "bar_interval_seconds",
        "connector_var": "connector",
        "interval_var": "interval",
    },
    "multi_pair": {
        "path": NB_DIR / "pmm_dynamic_multi_pair_sweep.ipynb",
        "sweep_cell_idx": 8,
        "bar_var": "BAR_INTERVAL_SECONDS",
        "connector_var": "CONNECTOR",
        "interval_var": "INTERVAL",
    },
    "single_pair": {
        "path": NB_DIR / "pmm_dynamic_single_pair_sweep_mexc_xmr_usdt.ipynb",
        "sweep_cell_idx": 7,
        "bar_var": "BAR_INTERVAL_SECONDS",
        "connector_var": "CONNECTOR",
        "interval_var": "INTERVAL",
    },
}


def _replace_once(src, old, new, label):
    """Replace exactly one occurrence of old with new. Fail if not found."""
    if old not in src:
        print(f"  WARNING: '{label}' target not found!")
        return src, False
    count = src.count(old)
    if count > 1:
        print(f"  WARNING: '{label}' found {count} times, replacing first occurrence only")
    result = src.replace(old, new, 1)
    print(f"  OK: {label}")
    return result, True


def fix_notebook(name, info):
    """Apply all fixes to one notebook."""
    path = info["path"]
    cell_idx = info["sweep_cell_idx"]
    bar_var = info["bar_var"]

    print(f"\n{'='*60}")
    print(f"Fixing {name}: {path.name} (cell {cell_idx})")
    print(f"{'='*60}")

    if not path.exists():
        print(f"  ERROR: Notebook not found: {path}")
        return False

    with open(path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    cell = nb["cells"][cell_idx]
    src = "".join(cell["source"])
    original = src
    all_ok = True

    # ── Phase 2: Fix future-data leakage (candles -> dev_candles) ──
    # Pattern: "top_candidates, candles, pair_rules, <bar_var>,"
    old = f"top_candidates, candles, pair_rules, {bar_var},"
    new = f"top_candidates, dev_candles, pair_rules, {bar_var},"
    src, ok = _replace_once(src, old, new, "Phase 2: stress selection dev_candles")
    all_ok = all_ok and ok

    # ── Phase 3: Fix holdout to use dataset_slices ──
    # The holdout block uses flexible indentation. Use the actual pattern found.
    old_holdout = (
        "holdout_report = None\n"
        "    try:\n"
        "        from pmm_lab.objective.holdout import split_holdout\n"
        f"        dev_candles_h, holdout_candles_h = split_holdout(candles, 0.20, min_holdout_bars=50)\n"
        "        holdout_candidates = [(val_config, best.get(\"robust_score\", 0.0))]\n"
        "        for t_idx in range(1, min(5, len(top_candidates))):\n"
        "            tc = top_candidates[t_idx]\n"
        "            tc_config = canonicalize_params(tc[\"params\"], pair_rules, ref_price)[0]\n"
        "            if tc_config is not None:\n"
        "                tc_config = _replace(tc_config, controller_compat=VALIDATION_CONTROLLER_COMPAT)\n"
        "                holdout_candidates.append((tc_config, tc.get(\"phase1_score\", 0.0)))\n"
        "        holdout_report = evaluate_holdout(\n"
        f"            holdout_candles_h, holdout_candidates, pair_rules, {bar_var},\n"
        "            run_stress=True, objective_version=OBJECTIVE_VERSION,\n"
        "            full_candles=candles, holdout_start_idx=len(dev_candles_h),\n"
        "        )"
    )
    new_holdout = (
        "holdout_report = None\n"
        "    try:\n"
        "        if dataset_slices is not None:\n"
        "            holdout_candles_h = dataset_slices.holdout_candles\n"
        "            holdout_start_idx = dataset_slices.holdout_start_idx_in_pre_release\n"
        "        else:\n"
        "            from pmm_lab.objective.holdout import split_holdout\n"
        "            dev_candles_h, holdout_candles_h = split_holdout(candles, 0.20, min_holdout_bars=50)\n"
        "            holdout_start_idx = len(dev_candles_h)\n"
        "        holdout_candidates = [(val_config, best.get(\"robust_score\", 0.0))]\n"
        "        for t_idx in range(1, min(5, len(top_candidates))):\n"
        "            tc = top_candidates[t_idx]\n"
        "            tc_config = canonicalize_params(tc[\"params\"], pair_rules, ref_price)[0]\n"
        "            if tc_config is not None:\n"
        "                tc_config = _replace(tc_config, controller_compat=VALIDATION_CONTROLLER_COMPAT)\n"
        "                holdout_candidates.append((tc_config, tc.get(\"phase1_score\", 0.0)))\n"
        "        holdout_report = evaluate_holdout(\n"
        f"            holdout_candles_h, holdout_candidates, pair_rules, {bar_var},\n"
        "            run_stress=True, objective_version=OBJECTIVE_VERSION,\n"
        "            full_candles=candles, holdout_start_idx=holdout_start_idx,\n"
        "        )"
    )
    src, ok = _replace_once(src, old_holdout, new_holdout, "Phase 3: holdout dataset_slices")
    all_ok = all_ok and ok

    # ── Phase 4: Fix walk-forward objective version and config ──
    # Indentation is 16 spaces (inside try/except inside for loop)
    old_wf = (
        "wf_result = run_walk_forward(\n"
        f"                candles=candles, config=best_config, pair_rules=pair_rules,\n"
        f"                bar_interval_seconds={bar_var}, dataset_hash=dataset_hash,\n"
        "                train_days=train_days, test_days=test_days, step_days=step_days,\n"
        "            )"
    )
    new_wf = (
        "wf_result = run_walk_forward(\n"
        f"                candles=candles, config=val_config, pair_rules=pair_rules,\n"
        f"                bar_interval_seconds={bar_var}, dataset_hash=dataset_hash,\n"
        "                train_days=train_days, test_days=test_days, step_days=step_days,\n"
        "                objective_version=OBJECTIVE_VERSION,\n"
        "            )"
    )
    src, ok = _replace_once(src, old_wf, new_wf, "Phase 4: walk-forward objective_version + val_config")
    all_ok = all_ok and ok

    # ── Phase 1c: Add validate_yaml_file call after export_yaml ──
    if "validation_result = validate_yaml_file(" not in src:
        # Find the end of export_yaml(...) call
        idx = src.find("yaml_path = export_yaml(")
        if idx >= 0:
            depth = 0
            found_start = False
            insert_pos = None
            for i in range(idx, len(src)):
                if src[i] == '(':
                    depth += 1
                    found_start = True
                elif src[i] == ')':
                    depth -= 1
                    if found_start and depth == 0:
                        nl = src.find('\n', i)
                        if nl >= 0:
                            insert_pos = nl + 1
                        else:
                            insert_pos = i + 1
                        break

            if insert_pos is not None:
                # Detect indentation from export_yaml line
                line_start = src.rfind('\n', 0, idx) + 1
                indent = ""
                for ch in src[line_start:idx]:
                    if ch in (' ', '\t'):
                        indent += ch
                    else:
                        break
                validation_line = f"{indent}validation_result = validate_yaml_file(yaml_path)\n"
                src = src[:insert_pos] + validation_line + src[insert_pos:]
                print("  OK: Phase 1c: Added validate_yaml_file() call")
            else:
                print("  WARNING: Phase 1c: Could not find insert position")
                all_ok = False
        else:
            print("  WARNING: Phase 1c: export_yaml call not found")
            all_ok = False
    else:
        print("  SKIP: Phase 1c: validate_yaml_file already present")

    # Also ensure validation_result = None is defined before the try block
    if "validation_result = None" not in src:
        export_idx = src.find("yaml_path = export_yaml(")
        if export_idx >= 0:
            try_idx = src.rfind("try:", 0, export_idx)
            if try_idx >= 0:
                try_line_start = src.rfind('\n', 0, try_idx) + 1
                indent = ""
                for ch in src[try_line_start:try_idx]:
                    if ch in (' ', '\t'):
                        indent += ch
                    else:
                        break
                init_line = f"{indent}validation_result = None\n"
                src = src[:try_line_start] + init_line + src[try_line_start:]
                print("  OK: Phase 1c: Added validation_result = None initialization")
    else:
        print("  SKIP: Phase 1c: validation_result = None already present")

    # ── Phase 1a: Fix run_stop_ship_checks() call ──
    # Indentation is 12 spaces
    old_checks = (
        "checks = run_stop_ship_checks(\n"
        "                best_metrics=best_metrics, best_objective=best_obj,\n"
        "                walkforward_result=wf_result, stress_report=best_stress,\n"
        "            )"
    )
    new_checks = (
        "checks = run_stop_ship_checks(\n"
        "                best_metrics=best_metrics, best_objective=best_obj,\n"
        "                walkforward_result=wf_result, stress_report=best_stress,\n"
        "                dataset_audit=audit,\n"
        "                validation_result=validation_result,\n"
        "                holdout_report=holdout_report,\n"
        "                sensitivity_penalty=sensitivity_penalty,\n"
        "                recent_window_result=recent_window_result,\n"
        "                parity_result=parity_result,\n"
        "                cluster_report=cluster_report,\n"
        "                long_parity_result=long_parity_result,\n"
        "            )"
    )
    src, ok = _replace_once(src, old_checks, new_checks, "Phase 1a: run_stop_ship_checks kwargs")
    all_ok = all_ok and ok

    # ── Phase 8: Add run provenance before generate_report ──
    if "_run_provenance" not in src:
        gen_report_idx = src.find("generate_report(")
        if gen_report_idx >= 0:
            gr_line_start = src.rfind('\n', 0, gen_report_idx) + 1
            indent = ""
            for ch in src[gr_line_start:gen_report_idx]:
                if ch in (' ', '\t'):
                    indent += ch
                else:
                    break
            prov_lines = [
                f"{indent}_run_provenance = {{",
                f'{indent}    "notebook": os.path.basename(__file__) if \'__file__\' in dir() else "jupyter",',
                f'{indent}    "run_timestamp": datetime.now(timezone.utc).isoformat(),',
                f'{indent}    "n_jobs": N_JOBS,',
                f'{indent}    "objective_version": OBJECTIVE_VERSION,',
                f'{indent}    "search_controller_compat": SEARCH_CONTROLLER_COMPAT,',
                f'{indent}    "validation_controller_compat": VALIDATION_CONTROLLER_COMPAT,',
                f'{indent}    "trial_number": best["trial_number"],',
                f"{indent}}}",
                "",
            ]
            prov_block = "\n".join(prov_lines) + "\n"
            src = src[:gr_line_start] + prov_block + src[gr_line_start:]
            print("  OK: Phase 8: Added _run_provenance block")
        else:
            print("  WARNING: Phase 8: generate_report call not found")
            all_ok = False
    else:
        print("  SKIP: Phase 8: _run_provenance already present")

    # ── Phase 1b: Fix generate_report() call — add kwargs ──
    # Check if generate_report already has the new kwargs by looking within its call
    gen_idx = src.find("generate_report(")
    _gen_has_new_kwargs = False
    if gen_idx >= 0:
        # Find closing paren
        _depth = 0
        for _i in range(gen_idx, len(src)):
            if src[_i] == '(': _depth += 1
            elif src[_i] == ')':
                _depth -= 1
                if _depth == 0:
                    _gen_call = src[gen_idx:_i+1]
                    _gen_has_new_kwargs = "sensitivity_report=" in _gen_call
                    break
    ssc_marker = "stop_ship_checks=checks,"
    ssc_idx = src.find(ssc_marker)
    if ssc_idx >= 0 and not _gen_has_new_kwargs:
        ssc_end = ssc_idx + len(ssc_marker)
        op_idx = src.find("output_path=", ssc_end)
        if op_idx >= 0:
            op_line_start = src.rfind('\n', ssc_end, op_idx) + 1
            indent = ""
            for ch in src[op_line_start:op_idx]:
                if ch in (' ', '\t'):
                    indent += ch
                else:
                    break
            new_kwargs = (
                f"\n{indent}holdout_report=holdout_report,\n"
                f"{indent}dataset_audit=audit,\n"
                f"{indent}sensitivity_report=sensitivity_report,\n"
                f"{indent}recent_window_result=recent_window_result,\n"
                f"{indent}cluster_report=cluster_report,\n"
                f"{indent}yaml_validation_result=validation_result,\n"
                f"{indent}dataset_slices=dataset_slices,\n"
                f"{indent}parity_result=parity_result,\n"
                f"{indent}long_parity_result=long_parity_result,\n"
                f"{indent}run_provenance=_run_provenance,\n"
            )
            src = src[:ssc_end] + new_kwargs + indent + src[op_idx:]
            print("  OK: Phase 1b: Added generate_report() kwargs")
        else:
            print("  WARNING: Phase 1b: output_path= not found")
            all_ok = False
    elif _gen_has_new_kwargs:
        print("  SKIP: Phase 1b: generate_report kwargs already present")
    else:
        print("  WARNING: Phase 1b: stop_ship_checks=checks, not found")
        all_ok = False

    if src == original:
        print("  WARNING: No changes were made!")
        return False

    # Write back
    cell["source"] = src.splitlines(keepends=True)
    if cell["source"] and not cell["source"][-1].endswith('\n'):
        cell["source"][-1] += '\n'

    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)

    print(f"  Done! Written {path.name}")
    return all_ok


def main():
    success = True
    for name, info in NOTEBOOKS.items():
        ok = fix_notebook(name, info)
        if not ok:
            success = False
            print(f"\n  ** {name}: Some replacements failed! **")

    if success:
        print("\n\nAll notebooks fixed successfully!")
    else:
        print("\n\nSome fixes failed — review warnings above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
