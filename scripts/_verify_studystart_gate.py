"""Re-run the REAL $2M intended_realism study-start preflight after the
§6.6-compatible denominator fix was threaded into walkforward_runner.py:1972.

Spies on walkforward_runner.run_preflight to dump the FULL per-check table
(passing checks drop out of the abort summary, so we need the spy). Exercises
the real run_walkforward_study code path so this proves the fix is mounted on the
call site the intended_realism abort actually reaches first.
"""
import json
import sys

sys.path[:0] = [
    "/quants-lab/research_notebooks/bowaka_v2_lab/src",
    "/quants-lab/research_notebooks/bowaka_common/src",
]

from bowaka_v2_lab.optuna import walkforward_runner as W  # noqa: E402
from bowaka_v2_lab.data import data_quality as DQ  # noqa: E402

# Spy on the DQ report builder to capture every per-level check's evidence
# (eligible_fraction / missing_fraction / gated) — the preflight summary only
# carries failed-check NAMES, not their fractions.
_orig_dq = DQ.build_data_quality_report
dq_reports = []


def _dq_spy(*a, **k):
    rep = _orig_dq(*a, **k)
    levels = []
    rep_checks = rep["checks"] if isinstance(rep, dict) else getattr(rep, "checks", [])
    for c in rep_checks or []:
        ev = c.get("evidence") if isinstance(c, dict) else getattr(c, "evidence", None)
        ev = ev if isinstance(ev, dict) else {}
        levels.append({
            "name": c.get("name", "?") if isinstance(c, dict) else getattr(c, "name", "?"),
            "status": c.get("status", "?") if isinstance(c, dict) else getattr(c, "status", "?"),
            "ev": {kk: ev[kk] for kk in (
                "gated", "eligible_fraction", "eligible_missing", "eligible_probes",
                "missing_fraction", "missing", "probes",
                "eligible_expected", "expected_pairs", "count", "threshold",
            ) if kk in ev},
        })
    dq_reports.append({"eligible_per_session_passed": k.get("eligible_per_session") is not None, "levels": levels})
    with open("/quants-lab/scripts/_dq_report_capture.json", "w") as fh:
        json.dump(dq_reports, fh, indent=2, default=str)
    return rep


DQ.build_data_quality_report = _dq_spy
# The runner does a *local* `from ..data.data_quality import build_data_quality_report`
# at call time, so patching the module attribute above is sufficient.

_orig = W.run_preflight
calls = []


def _spy(*a, **k):
    res = _orig(*a, **k)
    rows = []
    for c in res.checks:
        rows.append({
            "name": getattr(c, "name", "?"),
            "status": getattr(c, "status", "?"),
            "detail": getattr(c, "detail", None),
            "evidence": getattr(c, "evidence", None),
        })
    calls.append({"passed": res.passed, "checks": rows})
    with open("/quants-lab/scripts/_preflight_capture.json", "w") as fh:
        json.dump(calls, fh, indent=2, default=str)
    return res


W.run_preflight = _spy

result = None
try:
    result = W.run_walkforward_study("/tmp/ir2m.yml", n_trials=1)
    print("run_walkforward_study returned dict keys:", list(result.keys()) if isinstance(result, dict) else type(result))
    if isinstance(result, dict):
        print("  status:", result.get("status"))
        print("  failure_reason:", str(result.get("failure_reason"))[:300])
except Exception as e:  # noqa: BLE001
    print("study raised:", type(e).__name__, str(e)[:300])

print("\n=== run_preflight spy fired %d time(s) ===" % len(calls))
KEYS = [
    "gated", "eligible_fraction", "missing_fraction",
    "eligible_missing", "eligible_probes", "missing", "probes",
    "eligible_expected", "expected_pairs", "count", "threshold",
]
for i, call in enumerate(calls):
    print("\n--- run_preflight call #%d : passed=%s ---" % (i, call["passed"]))
    for c in call["checks"]:
        ev = c["evidence"] if isinstance(c["evidence"], dict) else {}
        summary = {kk: ev[kk] for kk in KEYS if kk in ev}
        print("  [%-5s] %-40s %s" % (c["status"], c["name"], summary))

print("\n=== DQ report per-level checks (study-start, %d build(s)) ===" % len(dq_reports))
for j, rep in enumerate(dq_reports):
    print("\n--- DQ report #%d : eligible_per_session passed in? %s ---" % (j, rep["eligible_per_session_passed"]))
    for lv in rep["levels"]:
        print("  [%-5s] %-40s %s" % (lv["status"], lv["name"], lv["ev"]))
