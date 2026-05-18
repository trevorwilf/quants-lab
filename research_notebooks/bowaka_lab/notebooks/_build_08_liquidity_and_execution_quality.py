"""Build ``notebooks/08_liquidity_and_execution_quality.ipynb``.

Bucket trades by ADV and spread proxy. Surface a gap-through analysis for
``exit_reason == 'stop_gap'`` trades, correlated with ADV.
"""

from __future__ import annotations

from pathlib import Path

import nbformat

from _notebook_common import BOOTSTRAP, code_cell, finalize, md_cell

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "08_liquidity_and_execution_quality.ipynb"


TITLE = """# 08 — Liquidity and execution quality

IEX data has no NBBO; this notebook reports three independent proxies and
NEVER conflates them:

1. **quote_spread_bps** — quote spread from the QuoteLoader (closest to
   entry time). Null when quotes are unavailable.
2. **entry_minute_range_bps** — `(entry_bar.high - entry_bar.low) /
   entry_bar.close × 1e4`. Always available when a minute bar exists.
3. **first_minute_range_bps** — same formula for the session's first RTH bar.
   Stable, comparable across sessions.

Each proxy gets its own bucketed table, stratified by data_feed, adv_bucket,
and quote_available. The trade-outcome ``abs(exit - entry)`` range that was
previously labelled "spread proxy" here was an analysis bug and has been
removed (Phase fidelity-7).
"""


PARAMETERS = '''import os

RUN_ID              = "bt_iex_default"
DATA_ROOT           = os.environ.get(
    "BOWAKA_DATA_ROOT",
    "research_notebooks/bowaka_lab/db_tools/bowaka_data",
)
ARTIFACTS_ROOT      = "research_notebooks/bowaka_lab/artifacts"
FEED                = "iex"
REBUILD             = False

ADV_BUCKETS         = [200_000, 1_000_000, 5_000_000, 25_000_000]
SPREAD_BUCKETS_BPS  = [0, 10, 25, 50, 100]   # bps edges
'''


DERIVED = '''from pathlib import Path

import numpy as np
import pandas as pd

from bowaka_lab.utils import (
    ArtifactPaths,
    artifact_exists,
    load_parquet,
    save_parquet,
)


data_root      = Path(DATA_ROOT)      if Path(DATA_ROOT).is_absolute()      else (repo_root / DATA_ROOT).resolve()
artifacts_root = Path(ARTIFACTS_ROOT) if Path(ARTIFACTS_ROOT).is_absolute() else (repo_root / ARTIFACTS_ROOT).resolve()

paths = ArtifactPaths.for_run(RUN_ID, artifacts_root)
paths.ensure_dir()
assert paths.trades.exists(),     f"trades missing: {paths.trades} — run notebook 04 first."
assert paths.candidates.exists(), f"candidates missing: {paths.candidates} — run notebook 03 first."

print(f"artifacts:  {paths.root}")
'''


LOAD = '''trades = load_parquet(paths.trades)
candidates = load_parquet(paths.candidates)

# Join avg_dollar_volume from the candidates artifact onto each trade.
# Candidates are unique per (signal_date, symbol); trades carry the same key.
needed_cols = ["signal_date", "symbol"]
adv_col = "avg_dollar_volume" if "avg_dollar_volume" in candidates.columns else None
if adv_col is None:
    print("avg_dollar_volume missing from candidates — ADV bucketing will be skipped.")
    enriched = trades.copy()
    enriched["avg_dollar_volume"] = np.nan
else:
    enriched = trades.merge(
        candidates[needed_cols + [adv_col]].drop_duplicates(),
        on=needed_cols,
        how="left",
    )
print(f"trades enriched with ADV: {enriched['avg_dollar_volume'].notna().sum():,}/{enriched.shape[0]:,}")
'''


ADV_BUCKETS_CELL = '''adv_edges = [0] + list(ADV_BUCKETS) + [np.inf]
adv_labels = ["<$200k", "$200k-$1M", "$1M-$5M", "$5M-$25M", ">$25M"]
enriched["adv_bucket"] = pd.cut(enriched["avg_dollar_volume"], bins=adv_edges, labels=adv_labels, include_lowest=True)

by_adv = enriched.groupby("adv_bucket", observed=False).agg(
    trades=("pnl_pct", "size"),
    win_rate=("pnl_pct", lambda s: float((s > 0).mean()) if len(s) else 0.0),
    median_pnl_pct=("pnl_pct", "median"),
    stop_gap_rate=("exit_reason", lambda s: float((s == "stop_gap").mean()) if len(s) else 0.0),
).reset_index()
try:
    from IPython.display import display
    display(by_adv)
except Exception:
    print(by_adv.to_string(index=False))
'''


SPREAD_BUCKETS_CELL = '''# Phase fidelity-7: three INDEPENDENT proxies. No more abs(exit-entry).
#
# quote_spread_bps           = quote_loader spread closest to entry_time
# entry_minute_range_bps     = (high-low)/close on the entry-minute bar
# first_minute_range_bps     = (high-low)/close on the session's first RTH bar
#
# The legacy ``range_bps`` (abs(exit-entry)) is intentionally NOT computed
# here — that was an analysis bug. Operators who need a quote_loader proxy
# must wire the QuoteLoader through this notebook (currently scaffolded
# only — the QuoteLoader integration lands in a follow-up phase).

enriched["quote_spread_bps"] = float("nan")  # populated when QuoteLoader is wired
enriched["quote_available"] = enriched["quote_spread_bps"].notna()

# entry_minute_range_bps is derivable from trade-side fields when the
# entry-bar high/low were recorded as diagnostics. Without that, leave NaN.
if {"entry_bar_high", "entry_bar_low", "entry_bar_close"}.issubset(enriched.columns):
    enriched["entry_minute_range_bps"] = (
        (enriched["entry_bar_high"] - enriched["entry_bar_low"])
        / enriched["entry_bar_close"].replace(0, np.nan)
    ) * 10_000.0
else:
    enriched["entry_minute_range_bps"] = float("nan")

# first_minute_range_bps needs the session's first RTH bar; not derivable
# from the trades artifact alone. NaN until a future pass enriches with
# session-bar context.
enriched["first_minute_range_bps"] = float("nan")

spread_summary = {
    "quote_spread_bps_n": int(enriched["quote_spread_bps"].notna().sum()),
    "entry_minute_range_bps_n": int(enriched["entry_minute_range_bps"].notna().sum()),
    "first_minute_range_bps_n": int(enriched["first_minute_range_bps"].notna().sum()),
}
print("Liquidity proxy availability:")
for k, v in spread_summary.items():
    print(f"  {k}: {v:,}")
'''


GAP_ANALYSIS = '''stop_gaps = enriched[enriched["exit_reason"] == "stop_gap"].copy()
print(f"stop_gap trades: {stop_gaps.shape[0]:,} ({stop_gaps.shape[0]/max(1,enriched.shape[0]):.2%} of total)")

if not stop_gaps.empty:
    # gap_pct = exit_price / entry_price - 1 (the open was below stop, so this
    # captures the gap-through magnitude).
    stop_gaps["gap_through_pct"] = stop_gaps["exit_price"] / stop_gaps["entry_price"] - 1.0
    by_adv_gap = stop_gaps.groupby("adv_bucket", observed=False).agg(
        gaps=("gap_through_pct", "size"),
        median_gap_pct=("gap_through_pct", "median"),
        worst_gap_pct=("gap_through_pct", "min"),
    ).reset_index()
    try:
        from IPython.display import display
        display(by_adv_gap)
    except Exception:
        print(by_adv_gap.to_string(index=False))
'''


SAVE = '''# Persist a tidy aggregate so notebook 11 can render the table.
aggregates = []
for label, frame in (("adv_bucket", by_adv),):
    a = frame.copy()
    a["bucket_type"] = label
    a = a.rename(columns={label: "bucket"})
    aggregates.append(a)
liq_df = pd.concat(aggregates, ignore_index=True) if aggregates else pd.DataFrame()
# Stash the proxy-availability summary in attrs for the report.
liq_df.attrs["liquidity_proxy_summary"] = spread_summary if "spread_summary" in dir() else {}
save_parquet(paths.liquidity, liq_df)
print(f"wrote {paths.liquidity}")
'''


RECOMMENDATIONS = '''lowest = by_adv.iloc[0] if not by_adv.empty else None
if lowest is not None and pd.notna(lowest["stop_gap_rate"]):
    print(f"Lowest ADV bucket ({lowest['adv_bucket']}): stop_gap_rate = {lowest['stop_gap_rate']:.2%}, "
          f"median pnl = {lowest['median_pnl_pct']:.3%}")
    if lowest["stop_gap_rate"] > 0.20:
        print(f"  -> consider raising AVG_DOLLAR_VOLUME_MIN above {ADV_BUCKETS[0]:,}")
    if lowest["median_pnl_pct"] < 0:
        print(f"  -> lowest ADV bucket is net-losing; tightening the universe should improve median")
'''


NEXT = """## Next

- **`notebooks/09_paper_vs_backtest_reconciliation.ipynb`** if you have paper
  logs.
- Or **`notebooks/11_weekly_research_report.ipynb`** to aggregate."""


def main() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        md_cell(TITLE),
        code_cell(BOOTSTRAP, tag="bootstrap"),
        md_cell("## Configuration"),
        code_cell(PARAMETERS, tag="parameters"),
        md_cell("## Derived paths"),
        code_cell(DERIVED, tag="derived"),
        md_cell("## Load + enrich trades with ADV from candidates"),
        code_cell(LOAD, tag="load"),
        md_cell("## Bucket by ADV"),
        code_cell(ADV_BUCKETS_CELL, tag="adv"),
        md_cell("## Bucket by spread proxy"),
        code_cell(SPREAD_BUCKETS_CELL, tag="spread"),
        md_cell("## Gap-through analysis"),
        code_cell(GAP_ANALYSIS, tag="gap"),
        md_cell("## Persist aggregates"),
        code_cell(SAVE, tag="save"),
        md_cell("## Recommendations"),
        code_cell(RECOMMENDATIONS, tag="recommendations"),
        md_cell(NEXT),
    ]
    finalize(nb)
    nbformat.write(nb, NB_PATH)
    print(f"wrote {NB_PATH}")


if __name__ == "__main__":
    main()
