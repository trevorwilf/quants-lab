"""Temporary script to apply notebook edits for Fix 1, 2, 3."""
import json


def patch_cell3(source_lines):
    """Fix 1: Replace misleading comment and add PHASE2_CONTROLLER_COMPAT."""
    result = []
    i = 0
    while i < len(source_lines):
        line = source_lines[i]

        # Replace the misleading comment block before SEARCH_CONTROLLER_COMPAT
        if "# Feature computation mode for search AND stress/validation." in line:
            result.append("# Feature computation mode for Phase 1 search.\n")
            result.append("# False = fast vectorized (broad search), True = controller-equivalent sliding window.\n")
            i += 1
            # Skip remaining old comment lines (2 more lines)
            while i < len(source_lines) and source_lines[i].startswith("# ") and "SEARCH_CONTROLLER_COMPAT" not in source_lines[i]:
                i += 1
            continue

        # Also handle the shorter comment variant (retest notebook)
        if "# Feature computation mode for search AND stress/validation.\n" == line:
            result.append("# Feature computation mode for Phase 1 search.\n")
            i += 1
            continue

        # After VALIDATION_CONTROLLER_COMPAT = True, add PHASE2_CONTROLLER_COMPAT
        if line.rstrip("\n") == "VALIDATION_CONTROLLER_COMPAT = True":
            result.append(line)
            result.append("\n")
            result.append("# Phase 2 stress-testing controller mode \u2014 controls signal generation for stress candidates.\n")
            result.append("# True = controller-equivalent sliding window (same as validation; slower but realistic).\n")
            result.append("# False = fast vectorized (same as search; faster but not controller-equivalent).\n")
            result.append("# NOTE: changing this from True to False changes Phase 2 ranking semantics and which\n")
            result.append("# strategy wins. Treat as a research decision, not a performance tweak.\n")
            result.append("PHASE2_CONTROLLER_COMPAT = True  # preserves current effective behavior\n")
            i += 1
            continue

        result.append(line)
        i += 1
    return result


def patch_cell8(source_lines):
    """Fix 1 + Fix 2 + Fix 3 changes to Cell 8."""
    result = []
    i = 0
    while i < len(source_lines):
        line = source_lines[i]

        # Fix 1: Add PHASE2_CONTROLLER_COMPAT to _required_config list
        if '"VALIDATION_CONTROLLER_COMPAT", "SEARCH_CONTROLLER_COMPAT",' in line:
            result.append('    "VALIDATION_CONTROLLER_COMPAT", "SEARCH_CONTROLLER_COMPAT", "PHASE2_CONTROLLER_COMPAT",\n')
            i += 1
            continue

        # Fix 1: Add PHASE2_CONTROLLER_COMPAT fallback after SEARCH_CONTROLLER_COMPAT fallback
        if line.rstrip("\n") == "        SEARCH_CONTROLLER_COMPAT = False":
            result.append(line)
            result.append("    if \"PHASE2_CONTROLLER_COMPAT\" not in globals():\n")
            result.append("        PHASE2_CONTROLLER_COMPAT = True\n")
            i += 1
            continue

        # Fix 1: Add Phase 2 controller_compat override after canonicalize in Phase 2
        if "config, reject = canonicalize_params(trial.params, pair_rules, ref_price)" in line:
            result.append(line)
            i += 1
            # Next line should be: if config is not None:
            if i < len(source_lines) and "if config is not None:" in source_lines[i]:
                result.append(source_lines[i])
                i += 1
                # Add the override line
                result.append("                config = _replace(config, controller_compat=PHASE2_CONTROLLER_COMPAT)\n")
            continue

        # Fix 1: Add Phase 2 print line before the dedup print
        if "Deduped:" in line and "print" in line:
            result.append("        print(f\"  Phase 2: controller_compat={PHASE2_CONTROLLER_COMPAT} (search={SEARCH_CONTROLLER_COMPAT})\")\n")
            result.append(line)
            i += 1
            continue

        # Fix 2: Replace _recent_runner signal computation with SharedSignalCache
        if "_recent_runner = CandleSimRunner(val_config, pair_rules)" in line.strip():
            if i + 1 < len(source_lines) and "_recent_signals = _recent_runner.compute_signals(candles)" in source_lines[i + 1]:
                indent = line[: len(line) - len(line.lstrip())]
                result.append(indent + "from pmm_lab.objective.signal_cache import SharedSignalCache\n")
                result.append(indent + "_shared_cache = SharedSignalCache()\n")
                result.append(indent + '_recent_signals = _shared_cache.get_or_compute(val_config, "full", candles, pair_rules)\n')
                i += 2  # skip both old lines
                continue

        # Fix 2: Add shared_signal_cache to evaluate_recent_window
        if "precomputed_signals=_recent_signals," in line and "shared_signal_cache" not in line:
            if i + 1 < len(source_lines) and "shared_signal_cache" in source_lines[i + 1]:
                result.append(line)
                i += 1
                continue
            result.append(line)
            indent = line[: len(line) - len(line.lstrip())]
            result.append(indent + "shared_signal_cache=_shared_cache,\n")
            i += 1
            continue

        # Fix 2: Add shared_signal_cache to evaluate_holdout
        if "full_candles=candles, holdout_start_idx=holdout_start_idx," in line and "shared_signal_cache" not in line:
            if i + 1 < len(source_lines) and "shared_signal_cache" in source_lines[i + 1]:
                result.append(line)
                i += 1
                continue
            result.append(line)
            indent = line[: len(line) - len(line.lstrip())]
            result.append(indent + "shared_signal_cache=_shared_cache,\n")
            i += 1
            continue

        # Fix 2: Add shared_signal_cache to compute_sensitivity
        if "objective_version=OBJECTIVE_VERSION, controller_compat=VALIDATION_CONTROLLER_COMPAT," in line and "shared_signal_cache" not in line:
            result.append(line)
            indent = line[: len(line) - len(line.lstrip())]
            result.append(indent + "shared_signal_cache=_shared_cache,\n")
            i += 1
            continue

        # Fix 3: Replace signal_cache = {} with precomputed signals
        if line.strip() == "signal_cache = {}":
            indent = line[: len(line) - len(line.lstrip())]
            result.append(indent + "from pmm_lab.objective.phase2_parallel import precompute_unique_signals\n")
            result.append(indent + "signal_cache = precompute_unique_signals(\n")
            result.append(indent + "    top_candidates=top_candidates,\n")
            result.append(indent + "    candles=dev_candles,\n")
            result.append(indent + "    pair_rules=pair_rules,\n")
            result.append(indent + "    max_workers=N_JOBS,\n")
            result.append(indent + ")\n")
            i += 1
            continue

        result.append(line)
        i += 1
    return result


for path in [
    "notebooks/pmm_dynamic/pmm_dynamic_retest_sweep.ipynb",
    "notebooks/pmm_dynamic/pmm_dynamic_multi_exchange_sweep_mexc_nonkyc.ipynb",
]:
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)

    nb["cells"][3]["source"] = patch_cell3(nb["cells"][3]["source"])
    nb["cells"][8]["source"] = patch_cell8(nb["cells"][8]["source"])

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")

    print(f"Patched: {path.split('/')[-1]}")

print("Done!")
