"""Parse the pasted Notebook 10 output into a canonical summary.

This is the audit's Appendix D.1 regression-fixture summary. It is the
exact failure shape the validity gates added in Phase 0 must reject.
"""
from __future__ import annotations
import ast, json, re
from pathlib import Path

_TRIAL_RE = re.compile(
    r"Trial (\d+) finished with value: (-?[\d.]+) and parameters: (\{.*?\})\."
    r" Best is trial \d+ with value:",
    re.DOTALL,
)
_PADDED_RE = re.compile(
    r"incumbent baseline padded \d+ search-space key\(s\) absent from "
    r"the contract with search-space defaults: (\[[^\]]*\])"
)

def parse(log_path: Path) -> dict:
    text = log_path.read_text()
    trials = []
    for m in _TRIAL_RE.finditer(text):
        num = int(m.group(1)); val = float(m.group(2))
        params = ast.literal_eval(m.group(3))
        trials.append({"number": num, "value": val, "params": params})
    trials.sort(key=lambda t: t["number"])
    sk = "exits.signal_fade.score_thresholds.soft"
    hk = "exits.signal_fade.score_thresholds.hard"
    ck = "exits.signal_fade.score_thresholds.critical"
    padded_keys: list[str] = []
    pm = _PADDED_RE.search(text)
    if pm:
        padded_keys = sorted(ast.literal_eval(pm.group(1)))
    summary = {
        "fixture_source": str(log_path.name),
        "parsed_trials": len(trials),
        "trial_numbers_min": min((t["number"] for t in trials), default=None),
        "trial_numbers_max": max((t["number"] for t in trials), default=None),
        "missing_trial_numbers": sorted(
            set(range(min((t["number"] for t in trials), default=0),
                      max((t["number"] for t in trials), default=-1) + 1))
            - {t["number"] for t in trials}
        ),
        "unique_objective_values": sorted(set(t["value"] for t in trials)),
        "incumbent_padded_keys": padded_keys,
        "has_dynamic_categorical_error": (
            "CategoricalDistribution does not support dynamic value space" in text
        ),
        "soft_gt_hard_count": sum(1 for t in trials if t["params"][sk] > t["params"][hk]),
        "hard_gt_critical_count": sum(1 for t in trials if t["params"][hk] > t["params"][ck]),
        "target_le_stop_count": sum(
            1 for t in trials
            if t["params"]["exits.target_pct"] <= t["params"]["exits.stop_pct"]
        ),
        "trial_0_max_quote_age_seconds": (
            trials[0]["params"].get("execution.max_quote_age_seconds")
            if trials and trials[0]["number"] == 0 else None
        ),
        "trial_0_max_spread_bps": (
            trials[0]["params"].get("execution.max_spread_bps")
            if trials and trials[0]["number"] == 0 else None
        ),
    }
    return summary

if __name__ == "__main__":
    here = Path(__file__).parent
    summary = parse(here / "raw_output.log")
    (here / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
