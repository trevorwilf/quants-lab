#!/usr/bin/env python
"""Merge the out-of-sample holdout numbers produced by ``score_finalist_holdout.py``
into an existing top-N robustness report, WITHOUT re-running any backtests.

Background: ``topn_robustness_sweep.py`` writes the report (.md + .json sidecar)
when the sweep runs. When the holdout-scope scan-matrix is not yet available the
holdout columns come out blank (``—``) and the combined score is dev-objective +
neighbour-mean only. ``score_finalist_holdout.py`` later scores the SAME finalists
on the reserved holdout window but only prints a log table — it does not write
back into the report. This adapter bridges the two:

  1. parse the holdout log table (trial · net% · obj · trades · dd),
  2. patch each finalist's ``holdout_score`` / ``holdout_metrics`` / clear
     ``holdout_error`` in the sweep JSON, and
  3. re-emit through the sweep's own ``_emit`` so ``_finalize_verdict`` recomputes
     the combined score (now incl. holdout), re-ranks, re-picks the winner, and
     re-renders every holdout column/block + winner YAMLs — canonical formatting.

It builds the walk-forward plan directly from the config dates so it never touches
the lake (unlike the sweep's ``_setup`` → ``_resolve_symbols``).

    cd research_notebooks/bowaka_v2_lab
    PYTHONPATH="src;../bowaka_common/src" python scripts/_merge_holdout_into_report.py \
        --json artifacts/optuna/topn_robustness.json \
        --log  artifacts/score_finalist_holdout.log \
        --config artifacts/resolved_configs/walkforward_resolved.yml \
        --out  artifacts/optuna/topn_robustness.md
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import yaml

import topn_robustness_sweep as tn  # noqa: E402  (same scripts/ dir on sys.path)
from bowaka_v2_lab.optuna.walkforward import build_walkforward_splits

# A holdout table row, e.g.:
#   3503 |       +96.31% |                 +411.22% | obj 0.695 · 90 trades · dd +23.75%
_ROW = re.compile(
    r"^\s*(?P<trial>\d+)\s*\|\s*(?P<net>[-+]?\d+(?:\.\d+)?)%\s*\|"
    r"[^|]*\|\s*obj\s*(?P<obj>[-+]?\d+(?:\.\d+)?)\b"
    r".*?(?P<trades>\d+)\s*trades"
    r".*?dd\s*(?P<dd>[-+]?\d+(?:\.\d+)?)%",
)


def parse_log(log_path: Path) -> dict[int, dict]:
    """Return {trial_number: {net_return_pct, max_drawdown_pct, n_trades, obj}} (decimals)."""
    out: dict[int, dict] = {}
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _ROW.match(line)
        if not m:
            continue
        out[int(m["trial"])] = {
            "net_return_pct": float(m["net"]) / 100.0,
            "max_drawdown_pct": float(m["dd"]) / 100.0,
            "n_trades": int(m["trades"]),
            "obj": float(m["obj"]),
        }
    return out


def build_plan(cfg: dict):
    bt = cfg.get("backtest", {}) or {}
    wf = (cfg.get("optuna", {}) or {}).get("walkforward", {}) or {}
    return build_walkforward_splits(
        full_start=tn.wr._to_date(bt["start_date"]),
        full_end=tn.wr._to_date(bt["end_date"]),
        train_months=int(wf.get("train_months", 6)),
        val_months=int(wf.get("val_months", 1)),
        final_holdout_months=int(wf.get("final_holdout_months", 1)),
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", required=True, help="topn_robustness.json to patch + re-emit")
    p.add_argument("--log", required=True, help="score_finalist_holdout.log to parse")
    p.add_argument("--config", required=True, help="resolved walk-forward config (for the plan)")
    p.add_argument("--out", required=True, help="markdown out path (overwrites in place)")
    p.add_argument("--neighbours", type=int, default=7)
    p.add_argument(
        "--cfg-display",
        default="research_notebooks/bowaka_v2_lab/artifacts/resolved_configs/walkforward_resolved.yml",
        help="string shown in the report's `config:` header line",
    )
    args = p.parse_args()

    doc = json.loads(Path(args.json).read_text(encoding="utf-8"))
    results = doc.get("finalists") or []
    holdout = parse_log(Path(args.log))
    print(f"parsed {len(holdout)} holdout rows from log: trials {sorted(holdout)}")

    patched, missing = 0, []
    for r in results:
        num = r.get("number")
        h = holdout.get(num)
        if h is None:
            missing.append(num)
            continue
        r["holdout_score"] = h["obj"]
        r["holdout_metrics"] = {
            "net_return_pct": h["net_return_pct"],
            "max_drawdown_pct": h["max_drawdown_pct"],
            "worst_day_loss_pct": None,
            "n_trades": h["n_trades"],
            "fill_rate": None,
        }
        r["holdout_error"] = None
        patched += 1
    print(f"patched {patched}/{len(results)} finalists; missing holdout for: {missing}")
    if missing:
        raise SystemExit(f"refusing to emit: {len(missing)} finalists have no holdout row")

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    plan = build_plan(cfg)
    study_name = doc.get("study") or "unknown_study"
    ts = time.strftime("%Y-%m-%d %H:%M:%S") + " (holdout merged from score_finalist_holdout.log)"

    # _emit re-sorts/re-finalizes/re-renders + re-exports winner YAMLs + rewrites the JSON.
    return tn._emit(results, study_name, args.cfg_display, plan,
                    args.neighbours, ts, Path(args.out), base_cfg=cfg)


if __name__ == "__main__":
    raise SystemExit(main())
