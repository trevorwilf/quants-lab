"""Build ``notebooks/11_weekly_research_report.ipynb``.

Aggregate every artifact under ``artifacts/{run_id}/`` into the final
Markdown + JSON weekly report.
"""

from __future__ import annotations

from pathlib import Path

import nbformat

from _notebook_common import BOOTSTRAP, code_cell, finalize, md_cell

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "11_weekly_research_report.ipynb"


TITLE = """# 11 — Weekly research report

Aggregate every artifact under ``artifacts/{RUN_ID}/`` into the final
Markdown + JSON report. Notebooks 03 → 04 must have run; everything else is
optional and shows "_no data_" when missing.

Prerequisites (minimum to produce a useful report):

- ``candidates.parquet`` from notebook **03**
- ``funnel.json`` from notebook **03**
- ``trades.parquet`` from notebook **04**
- ``summary.json`` from notebook **04**
- ``config.json`` from notebook **04**

Optional inputs that enrich sections:

- ``cf_entry.parquet`` (notebook 05)
- ``cf_exit.parquet`` (notebook 06)
- ``signal_fade.parquet`` (notebook 07)
- ``liquidity_buckets.parquet`` (notebook 08)
- ``reconciliation.parquet`` (notebook 09)
- ``optuna_trials.parquet`` + ``optuna_best.json`` (notebook 10)
"""


PARAMETERS = '''RUN_ID         = "bt_iex_default"
ARTIFACTS_ROOT = "research_notebooks/bowaka_lab/artifacts"
'''


DERIVED = '''from pathlib import Path

import pandas as pd

from bowaka_lab.metrics.trade_metrics import per_trade_metrics
from bowaka_lab.reports.markdown import ReportInputs
from bowaka_lab.reports.weekly_report import generate_weekly_report
from bowaka_lab.utils import (
    ArtifactPaths,
    artifact_exists,
    load_json,
    load_parquet,
)


artifacts_root = Path(ARTIFACTS_ROOT) if Path(ARTIFACTS_ROOT).is_absolute() else (repo_root / ARTIFACTS_ROOT).resolve()
paths = ArtifactPaths.for_run(RUN_ID, artifacts_root)
paths.ensure_dir()
print(f"artifacts: {paths.root}")
'''


CHECK_PREREQUISITES = '''# Explicit per-artifact existence checks via the typed ArtifactPaths
# properties. Operators see exactly which artifact is missing without
# having to grep the directory tree.
required_files = {
    "candidates":     paths.candidates,
    "funnel":         paths.funnel,
    "trades":         paths.trades,
    "summary":        paths.summary,
    "config":         paths.config,
}
optional_files = {
    "cf_entry":       paths.cf_entry,
    "cf_exit":        paths.cf_exit,
    "signal_fade":    paths.signal_fade,
    "liquidity":      paths.liquidity,
    "reconciliation": paths.reconciliation,
    "optuna_trials":  paths.optuna_trials,
    "optuna_best":    paths.optuna_best,
}

required_status = {name: p.exists() for name, p in required_files.items()}
optional_status = {name: p.exists() for name, p in optional_files.items()}

print("Required artifacts:")
for name, ok in required_status.items():
    print(f"  {name:20s} {'OK' if ok else 'MISSING'}  -> {required_files[name]}")

print()
print("Optional artifacts (sections that render '_no data_' when missing):")
for name, ok in optional_status.items():
    print(f"  {name:20s} {'OK' if ok else 'missing'}  -> {optional_files[name]}")

missing_required = [k for k, v in required_status.items() if not v]
assert not missing_required, (
    f"Missing required artifacts: {missing_required}.\\n"
    "Run notebooks 03 and 04 first."
)
'''


BUILD_INPUTS = '''funnel  = load_json(paths.funnel)     if required_status["funnel"]  else None
config  = load_json(paths.config)     if required_status["config"]  else {}
summary = load_json(paths.summary)    if required_status["summary"] else {}

trades_df = load_parquet(paths.trades) if required_status["trades"] else pd.DataFrame()
if not trades_df.empty:
    stop_pct = float(config.get("exits", {}).get("stop_pct", 0.08))
    trades_for_report = per_trade_metrics(trades_df, stop_pct=stop_pct)
else:
    trades_for_report = trades_df

cf_entry        = load_parquet(paths.cf_entry)        if optional_status["cf_entry"]        else None
cf_exit         = load_parquet(paths.cf_exit)         if optional_status["cf_exit"]         else None
signal_fade_df  = load_parquet(paths.signal_fade)     if optional_status["signal_fade"]     else None
liquidity_df    = load_parquet(paths.liquidity)       if optional_status["liquidity"]       else None
reconciliation  = load_parquet(paths.reconciliation)  if optional_status["reconciliation"]  else None
optuna_trials   = load_parquet(paths.optuna_trials)   if optional_status["optuna_trials"]   else None
optuna_best     = load_json(paths.optuna_best)        if optional_status["optuna_best"]     else None

# ReportInputs accepts a single ``counterfactuals`` DataFrame. We concatenate
# the two grids when both exist so the report's Sections 10/11 can render
# from one consolidated frame (the renderer groups by entry_rule or by
# (stop_pct, target_pct) on its own).
cf_frames = [df for df in (cf_entry, cf_exit) if df is not None and not df.empty]
counterfactuals_df = pd.concat(cf_frames, ignore_index=True) if cf_frames else pd.DataFrame()

inputs = ReportInputs(
    run_id=RUN_ID,
    config_hash="sha256:notebook_11",
    data_feed=(config.get("data", {}) or {}).get("feed", "iex"),
    universe_mode=(config.get("universe", {}) or {}).get("mode", "alpaca_current_assets"),
    prefilter_funnel=funnel,
    trades=trades_for_report,
    counterfactuals=counterfactuals_df,
    reconciliation=reconciliation,
    known_limitations=[
        "IEX-only feed (exploratory)" if (config.get("data", {}) or {}).get("feed") == "iex" else "",
        "current-universe survivorship-biased" if (config.get("universe", {}) or {}).get("mode") == "alpaca_current_assets" else "",
    ],
    next_actions=[
        "Refine prefilter gates and re-run 03 + 04.",
        "Inspect Section 13 (liquidity buckets) for ADV-tier recommendations.",
        "If 09 reconciliation surfaced implementation_mismatch rows, resolve before the next paper run.",
    ],
)
print("ReportInputs built; sections will render as follows:")
print(f"  trades:           {0 if trades_for_report.empty else len(trades_for_report)}")
print(f"  counterfactuals:  {0 if counterfactuals_df.empty else len(counterfactuals_df)}")
print(f"  signal_fade:      {'present' if signal_fade_df is not None and not signal_fade_df.empty else 'missing'}")
print(f"  liquidity:        {'present' if liquidity_df is not None and not liquidity_df.empty else 'missing'}")
print(f"  reconciliation:   {'present' if reconciliation is not None and not reconciliation.empty else 'missing'}")
print(f"  optuna:           {'present' if optuna_best else 'missing'}")
'''


GENERATE = '''res = generate_weekly_report(output_dir=paths.root, inputs=inputs)
print(f"wrote {res.markdown_path}")
print(f"wrote {res.summary_path}")
'''


PREVIEW = '''try:
    from IPython.display import Markdown, display
    display(Markdown(res.markdown_path.read_text(encoding="utf-8")))
except Exception:
    print(res.markdown_path.read_text(encoding="utf-8"))
'''


FOOTER = '''# Reprint the research-status footer for visibility.
flags = []
if (config.get("data", {}) or {}).get("feed") == "iex":
    flags.append("iex_feed_exploratory")
if (config.get("universe", {}) or {}).get("mode") == "alpaca_current_assets":
    flags.append("current_universe_survivorship_biased")
if optuna_trials is None or (optuna_trials is not None and optuna_trials.empty):
    flags.append("walk_forward_not_run")
if reconciliation is not None and not reconciliation.empty:
    if "implementation_mismatch" in set(reconciliation.get("classification", pd.Series([], dtype=str))):
        flags.append("paper_implementation_mismatch_unresolved")

print("Research-status flags:")
for f in flags:
    print(f"  - {f}")
'''


def main() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        md_cell(TITLE),
        code_cell(BOOTSTRAP, tag="bootstrap"),
        md_cell("## Configuration"),
        code_cell(PARAMETERS, tag="parameters"),
        md_cell("## Derived paths"),
        code_cell(DERIVED, tag="derived"),
        md_cell("## Check prerequisites"),
        code_cell(CHECK_PREREQUISITES, tag="prereqs"),
        md_cell("## Build ReportInputs"),
        code_cell(BUILD_INPUTS, tag="build_inputs"),
        md_cell("## Generate report"),
        code_cell(GENERATE, tag="generate"),
        md_cell("## Preview"),
        code_cell(PREVIEW, tag="preview"),
        md_cell("## Research-status footer"),
        code_cell(FOOTER, tag="footer"),
    ]
    finalize(nb)
    nbformat.write(nb, NB_PATH)
    print(f"wrote {NB_PATH}")


if __name__ == "__main__":
    main()
