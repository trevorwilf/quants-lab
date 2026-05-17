"""Build ``notebooks/05_entry_timing_counterfactuals.ipynb``.

Compare 5 entry rules on the same candidates produced by notebook 03.
Writes ``cf_entry.parquet`` for the weekly report aggregator.
"""

from __future__ import annotations

from pathlib import Path

import nbformat

from _notebook_common import BOOTSTRAP, code_cell, finalize, md_cell

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "05_entry_timing_counterfactuals.ipynb"


TITLE = """# 05 — Entry-timing counterfactuals

Replay every candidate produced by notebook 03 against multiple entry rules
(09:35, 09:45, 10:00, opening-range break, VWAP reclaim). Same stop / target /
hold geometry across all variants — only the entry timing changes. Output:
``cf_entry.parquet`` for notebook 11 to aggregate.
"""


PARAMETERS = '''import os

RUN_ID                    = "bt_iex_default"
DATA_ROOT                 = os.environ.get(
    "BOWAKA_DATA_ROOT",
    "research_notebooks/bowaka_lab/db_tools/bowaka_data",
)
ARTIFACTS_ROOT            = "research_notebooks/bowaka_lab/artifacts"
FEED                      = "iex"
REBUILD                   = False

ENTRY_RULES               = [
    "fixed_time_0935",
    "fixed_time_0945",
    "fixed_time_1000",
    "opening_range_break",
    "vwap_reclaim",
]
STOP_PCT                  = 0.08
TARGET_PCT                = 0.15
MAX_HOLD_DAYS             = 3
SIGNAL_FADE_THRESHOLD     = None       # disabled — focus on entry timing
STOP_MANAGER_MODEL        = "none"
INCLUDE_REJECTED          = False     # only entered candidates
'''


DERIVED = '''from pathlib import Path

import pandas as pd

from bowaka_lab.config.models import CounterfactualConfig
from bowaka_lab.data.parquet_io import MinuteBarLoader
from bowaka_lab.sim.counterfactuals import run_grid_for_candidates
from bowaka_lab.sim.fill_model import BowakaFillModel
from bowaka_lab.utils import (
    ArtifactPaths,
    artifact_exists,
    load_parquet,
    save_parquet,
)


data_root      = Path(DATA_ROOT)      if Path(DATA_ROOT).is_absolute()      else (repo_root / DATA_ROOT).resolve()
artifacts_root = Path(ARTIFACTS_ROOT) if Path(ARTIFACTS_ROOT).is_absolute() else (repo_root / ARTIFACTS_ROOT).resolve()
MINUTE_ROOT    = data_root / "parquet/bars/vendor=alpaca" / f"feed={FEED}" / "timeframe=1m/adjustment=raw"

paths = ArtifactPaths.for_run(RUN_ID, artifacts_root)
paths.ensure_dir()
assert paths.candidates.exists(), (
    f"candidates artifact missing: {paths.candidates}\\n"
    "Run notebook 03_prefilter_replay first."
)

cf_cfg = CounterfactualConfig(
    include_rejected_candidates=INCLUDE_REJECTED,
    entry_rules=ENTRY_RULES,
    stop_pct=[STOP_PCT],
    target_pct=[TARGET_PCT],
    max_hold_days=[MAX_HOLD_DAYS],
    signal_fade_thresholds=[SIGNAL_FADE_THRESHOLD],
    stop_manager_models=[STOP_MANAGER_MODEL],
)
fill_model = BowakaFillModel(slippage_bps=25.0)
minute_loader = MinuteBarLoader(MINUTE_ROOT)
print(f"artifacts:  {paths.root}")
print(f"entries:    {ENTRY_RULES}")
print(f"grid size:  {len(ENTRY_RULES)} variants per candidate")
'''


LOAD_CANDIDATES = '''candidates_df = load_parquet(paths.candidates)
print(f"candidates loaded: {candidates_df.shape[0]:,} rows over "
      f"{candidates_df['signal_date'].nunique():,} signal dates")
'''


RUN_GRID = '''outcomes_df = None

if not REBUILD and artifact_exists(paths, "cf_entry"):
    print("Fast path: cf_entry.parquet exists; loading.")
    outcomes_df = load_parquet(paths.cf_entry)
else:
    print("Running counterfactual grid per signal date...")
    all_rows = []
    grouped = candidates_df.groupby("signal_date", sort=True)
    n_sessions = len(grouped)
    for i, (sd, group) in enumerate(grouped, start=1):
        trade_date = group["trade_date"].iloc[0]
        symbols = group["symbol"].astype(str).tolist()
        # Load minute bars once per session, keyed by symbol.
        bars_per_session = minute_loader(trade_date, symbols)
        bars_by_symbol = (
            {s: g.copy() for s, g in bars_per_session.groupby("symbol", sort=False)}
            if not bars_per_session.empty else {}
        )
        out = run_grid_for_candidates(
            candidates=group.reset_index(drop=True),
            minute_bars_by_symbol=bars_by_symbol,
            cfg=cf_cfg,
            fill_model=fill_model,
            signal_date=sd,
            trade_date=trade_date,
        )
        if not out.empty:
            all_rows.append(out)
        if i % 25 == 0:
            print(f"  {i}/{n_sessions} sessions processed")
    outcomes_df = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    save_parquet(paths.cf_entry, outcomes_df)
    print(f"wrote {paths.cf_entry}")

print(f"outcomes rows: {outcomes_df.shape[0]:,}")
'''


SUMMARY = '''if outcomes_df.empty:
    print("no counterfactual outcomes — check candidates/minute bars on disk")
else:
    # Flatten variant.entry_rule for grouping.
    df = outcomes_df.copy()
    df["entry_rule"] = df["variant"].map(
        lambda v: v.get("entry_rule") if isinstance(v, dict) else str(v).split('"entry_rule": "', 1)[-1].split('"', 1)[0]
    )
    entered = df[df["would_enter"]].copy()
    print(f"entered (would_enter=True): {entered.shape[0]:,}")

    by_rule = entered.groupby("entry_rule").agg(
        trades=("pnl_pct", "size"),
        win_rate=("pnl_pct", lambda s: float((s > 0).mean())),
        mean_pnl_pct=("pnl_pct", "mean"),
        median_pnl_pct=("pnl_pct", "median"),
    ).reset_index().sort_values("median_pnl_pct", ascending=False)
    try:
        from IPython.display import display
        display(by_rule)
    except Exception:
        print(by_rule.to_string(index=False))
'''


PLOTS = '''try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

if plt is not None and not outcomes_df.empty:
    entered = outcomes_df.copy()
    entered = entered[entered["would_enter"]]
    entered["entry_rule"] = entered["variant"].map(
        lambda v: v.get("entry_rule") if isinstance(v, dict) else str(v).split('"entry_rule": "', 1)[-1].split('"', 1)[0]
    )
    fig, ax = plt.subplots(figsize=(9, 4))
    data = [entered.loc[entered["entry_rule"] == r, "pnl_pct"].dropna().values
            for r in ENTRY_RULES]
    ax.boxplot(data, labels=ENTRY_RULES, showmeans=True)
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_title(f"PnL distribution by entry rule — {RUN_ID}")
    ax.set_ylabel("pnl_pct")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    plt.show()
'''


NEXT = """## Next

Open **`notebooks/06_exit_surface_and_stop_manager.ipynb`** to sweep the
stop / target / max-hold surface."""


def main() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        md_cell(TITLE),
        code_cell(BOOTSTRAP, tag="bootstrap"),
        md_cell("## Configuration"),
        code_cell(PARAMETERS, tag="parameters"),
        md_cell("## Derived paths + config"),
        code_cell(DERIVED, tag="derived"),
        md_cell("## Load candidates"),
        code_cell(LOAD_CANDIDATES, tag="load_candidates"),
        md_cell("## Build + run entry-rule grid"),
        code_cell(RUN_GRID, tag="run_grid"),
        md_cell("## Per-rule summary"),
        code_cell(SUMMARY, tag="summary"),
        md_cell("## PnL distribution by entry rule"),
        code_cell(PLOTS, tag="plots"),
        md_cell(NEXT),
    ]
    finalize(nb)
    nbformat.write(nb, NB_PATH)
    print(f"wrote {NB_PATH}")


if __name__ == "__main__":
    main()
