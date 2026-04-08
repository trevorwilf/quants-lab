#!/usr/bin/env python3
"""Verify tp_min_notional_failures plumbing fix."""

import json
import os
import ast

# ── Resolve paths ──
BASE_CANDIDATES = [
    "research_notebooks/market_lab/pmm_dynamic",
    "quants-lab/research_notebooks/market_lab/pmm_dynamic",
    "quants-lab/quants-lab/research_notebooks/market_lab/pmm_dynamic",
]
BASE = None
for c in BASE_CANDIDATES:
    if os.path.isdir(c):
        BASE = c
        break
if BASE is None:
    print("ERROR: Cannot find market_lab directory. Run from the repo root.")
    exit(1)

METRICS_PY = os.path.join(BASE, "pmm_lab/metrics/metrics.py")
RUNNER_PY = os.path.join(BASE, "pmm_lab/deploy/runner.py")
FINALIST_PY = os.path.join(BASE, "pmm_lab/deploy/finalist_validation.py")
REPORT_PY = os.path.join(BASE, "pmm_lab/report/report_md.py")
NB_MAIN = os.path.join(BASE, "notebooks/pmm_dynamic/pmm_dynamic_multi_exchange_sweep_mexc_nonkyc.ipynb")
NB_RETEST = os.path.join(BASE, "notebooks/pmm_dynamic/pmm_dynamic_retest_sweep.ipynb")

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def nb_cell_source(path, cell_idx):
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)
    return "".join(nb["cells"][cell_idx]["source"])

def nb_find_cell_with(path, needle):
    """Return (cell_index, source_str) for the first code cell containing needle."""
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)
    for ci, cell in enumerate(nb["cells"]):
        src = "".join(cell["source"])
        if needle in src and cell["cell_type"] == "code":
            return ci, src
    return None, None

results = []

# ──────────────────────────────────────────────
# CHECK 1: Metrics dataclass has tp_min_notional_failures field
# ──────────────────────────────────────────────
metrics_src = read(METRICS_PY)
if "tp_min_notional_failures" in metrics_src and "class Metrics" in metrics_src:
    if "tp_min_notional_failures: int" in metrics_src or "tp_min_notional_failures:int" in metrics_src:
        results.append(("PASS", "Metrics dataclass: tp_min_notional_failures field present", ""))
    else:
        results.append(("FAIL", "Metrics: tp_min_notional_failures mentioned but not as a typed field",
                         "Add 'tp_min_notional_failures: int = 0' to the Metrics dataclass body."))
else:
    results.append(("FAIL", "Metrics dataclass: tp_min_notional_failures field MISSING",
                     "Add 'tp_min_notional_failures: int = 0' after 'open_trade_count' in the Metrics dataclass."))

# ──────────────────────────────────────────────
# CHECK 2: compute_metrics() passes tp_min_notional_failures to Metrics()
# ──────────────────────────────────────────────
metrics_return_idx = metrics_src.find("return Metrics(")
if metrics_return_idx >= 0:
    metrics_return_block = metrics_src[metrics_return_idx:metrics_return_idx+1000]
    if "tp_min_notional_failures" in metrics_return_block:
        results.append(("PASS", "compute_metrics(): tp_min_notional_failures passed to Metrics()", ""))
    else:
        results.append(("FAIL", "compute_metrics(): tp_min_notional_failures NOT in return Metrics(...)",
                         "Add 'tp_min_notional_failures=result.tp_min_notional_failures,' to the return Metrics(...) block."))
else:
    results.append(("FAIL", "compute_metrics(): cannot find 'return Metrics(' in metrics.py",
                     "Unexpected file structure — inspect manually."))

# ──────────────────────────────────────────────
# CHECK 3: runner.py passes tp_min_notional_failures to generate_report
# ──────────────────────────────────────────────
runner_src = read(RUNNER_PY)
gen_idx = runner_src.find("generate_report(")
while gen_idx >= 0 and "import" in runner_src[max(0, gen_idx-50):gen_idx]:
    gen_idx = runner_src.find("generate_report(", gen_idx + 1)
if gen_idx >= 0:
    runner_call_block = runner_src[gen_idx:gen_idx+800]
    if "tp_min_notional_failures" in runner_call_block:
        results.append(("PASS", "runner.py: tp_min_notional_failures passed to generate_report()", ""))
    else:
        results.append(("FAIL", "runner.py: tp_min_notional_failures NOT passed to generate_report()",
                         "Add 'tp_min_notional_failures=metrics.tp_min_notional_failures,' to the generate_report() call."))
else:
    results.append(("FAIL", "runner.py: cannot find generate_report() call", "Unexpected file structure."))

# ──────────────────────────────────────────────
# CHECK 4: finalist_validation.py passes tp_min_notional_failures
# ──────────────────────────────────────────────
finalist_src = read(FINALIST_PY)
gen_idx = finalist_src.find("generate_report(")
while gen_idx >= 0 and "import" in finalist_src[max(0, gen_idx-50):gen_idx]:
    gen_idx = finalist_src.find("generate_report(", gen_idx + 1)
if gen_idx >= 0:
    finalist_call_block = finalist_src[gen_idx:gen_idx+1200]
    if "tp_min_notional_failures" in finalist_call_block:
        results.append(("PASS", "finalist_validation.py: tp_min_notional_failures passed", ""))
    else:
        results.append(("FAIL", "finalist_validation.py: tp_min_notional_failures NOT passed",
                         "Add 'tp_min_notional_failures=dev_metrics.tp_min_notional_failures,' to the generate_report() call."))
else:
    results.append(("FAIL", "finalist_validation.py: cannot find generate_report() call", ""))

# ──────────────────────────────────────────────
# CHECK 5: Main sweep notebook passes tp_min_notional_failures
# ──────────────────────────────────────────────
ci, nb_src = nb_find_cell_with(NB_MAIN, "generate_report(")
if nb_src:
    call_idx = nb_src.find("generate_report(")
    while call_idx >= 0 and "import" in nb_src[max(0, call_idx-30):call_idx]:
        call_idx = nb_src.find("generate_report(", call_idx + 1)
    found = False
    search_from = 0
    all_calls_have_it = True
    call_count = 0
    while True:
        idx = nb_src.find("generate_report(", search_from)
        if idx < 0:
            break
        if "import" in nb_src[max(0, idx-30):idx]:
            search_from = idx + 1
            continue
        call_count += 1
        block = nb_src[idx:idx+2000]
        paren_depth = 0
        end = len(block)
        for j, ch in enumerate(block):
            if ch == "(":
                paren_depth += 1
            elif ch == ")":
                paren_depth -= 1
                if paren_depth == 0:
                    end = j
                    break
        call_block = block[:end]
        if "tp_min_notional_failures" not in call_block:
            all_calls_have_it = False
        search_from = idx + 1

    if call_count == 0:
        results.append(("FAIL", "Main notebook: no generate_report() call found (unexpected)", ""))
    elif all_calls_have_it:
        results.append(("PASS", f"Main notebook: tp_min_notional_failures in all {call_count} generate_report() call(s)", ""))
    else:
        results.append(("FAIL", f"Main notebook: tp_min_notional_failures MISSING from generate_report()",
                         "Add 'tp_min_notional_failures=best_metrics.tp_min_notional_failures,' before output_path= in the call."))
else:
    results.append(("FAIL", "Main notebook: cannot find cell with generate_report()", ""))

# ──────────────────────────────────────────────
# CHECK 6: Retest notebook passes tp_min_notional_failures
# ──────────────────────────────────────────────
ci2, nb2_src = nb_find_cell_with(NB_RETEST, "generate_report(")
if nb2_src:
    call_idx = nb2_src.find("generate_report(")
    while call_idx >= 0 and "import" in nb2_src[max(0, call_idx-30):call_idx]:
        call_idx = nb2_src.find("generate_report(", call_idx + 1)
    all_ok = True
    count = 0
    sf = 0
    while True:
        idx = nb2_src.find("generate_report(", sf)
        if idx < 0:
            break
        if "import" in nb2_src[max(0, idx-30):idx]:
            sf = idx + 1
            continue
        count += 1
        block = nb2_src[idx:idx+2000]
        paren_depth = 0
        end = len(block)
        for j, ch in enumerate(block):
            if ch == "(":
                paren_depth += 1
            elif ch == ")":
                paren_depth -= 1
                if paren_depth == 0:
                    end = j
                    break
        if "tp_min_notional_failures" not in block[:end]:
            all_ok = False
        sf = idx + 1
    if count == 0:
        results.append(("FAIL", "Retest notebook: no generate_report() call found", ""))
    elif all_ok:
        results.append(("PASS", f"Retest notebook: tp_min_notional_failures in all {count} call(s)", ""))
    else:
        results.append(("FAIL", "Retest notebook: tp_min_notional_failures MISSING from generate_report()",
                         "Add 'tp_min_notional_failures=best_metrics.tp_min_notional_failures,' before output_path= in the call."))
else:
    results.append(("FAIL", "Retest notebook: cannot find cell with generate_report()", ""))

# ──────────────────────────────────────────────
# CHECK 7 (optional): Recent info print lines cleaned up
# ──────────────────────────────────────────────
OLD_FSTRING = """{\", \".join(f\"{d}d\""""
for nb_path, nb_name in [(NB_MAIN, "Main notebook"), (NB_RETEST, "Retest notebook")]:
    with open(nb_path, encoding="utf-8") as f:
        raw = f.read()
    if OLD_FSTRING in raw:
        results.append(("WARN", f"{nb_name}: Recent info print uses nested double-quote f-string (valid but harder to read)",
                         "Optional: replace with single-quote variant for readability."))
    else:
        results.append(("PASS", f"{nb_name}: Recent info print line OK", ""))

# ──────────────────────────────────────────────
# REPORT
# ──────────────────────────────────────────────
print("=" * 70)
print("tp_min_notional_failures PLUMBING VERIFICATION")
print("=" * 70)
fails = 0
warns = 0
for status, check, fix in results:
    icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠"}[status]
    print(f"  {icon} [{status}] {check}")
    if fix:
        print(f"          → {fix}")
    if status == "FAIL":
        fails += 1
    if status == "WARN":
        warns += 1

print()
if fails == 0 and warns == 0:
    print("ALL CHECKS PASSED.")
elif fails == 0:
    print(f"No failures, {warns} warning(s) — review optional items above.")
else:
    print(f"{fails} FAILURE(S), {warns} warning(s) — apply fixes below.")
print("=" * 70)
