"""Build ``notebooks/04_single_config_backtest.ipynb``.

The modular replacement for ``run_backtest.ipynb``: reads
``candidates.parquet`` from notebook 03, runs ``BowakaPortfolioBacktester``,
writes ``trades.parquet`` + ``summary.json`` + ``config.json``.
"""

from __future__ import annotations

from pathlib import Path

import nbformat

from _notebook_common import BOOTSTRAP, code_cell, finalize, md_cell

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "04_single_config_backtest.ipynb"


TITLE = """# 04 — Single-config backtest

Run :class:`bowaka_lab.sim.portfolio_engine.BowakaPortfolioBacktester` against
the candidates emitted by notebook **03**. Produces:

- ``trades.parquet`` — one row per simulated trade.
- ``summary.json`` — aggregate stats (trade_count, win_rate, mean_pnl_pct,
  total_pnl, exits_by_reason).
- ``config.json`` — full backtest config snapshot for reproducibility.

This notebook does NOT generate the final weekly report — that's notebook 11.
It DOES print the funnel from notebook 03 for sanity.
"""


PARAMETERS = '''import os

RUN_ID         = "bt_iex_default"
DATA_ROOT      = os.environ.get(
    "BOWAKA_DATA_ROOT",
    "research_notebooks/bowaka_lab/db_tools/bowaka_data",
)
ARTIFACTS_ROOT = "research_notebooks/bowaka_lab/artifacts"
FEED           = "iex"
REBUILD        = False

ENTRY_RULE     = "fixed_time_0945"
SLIPPAGE_BPS   = 25
STOP_PCT       = 0.08
TARGET_PCT     = 0.15
MAX_HOLD_DAYS  = 3

PER_TRADE_NOTIONAL        = 5_000
MAX_CONCURRENT_POSITIONS  = 18
MAX_TOTAL_ENTRIES_PER_DAY = 25
'''


DERIVED = '''from datetime import date
from pathlib import Path

import pandas as pd

from bowaka_lab.config.models import BowakaBacktestConfig
from bowaka_lab.data.calendar import USEquityCalendar
from bowaka_lab.data.parquet_io import MinuteBarLoader, candidates_dict_to_source
from bowaka_lab.metrics.trade_metrics import per_trade_metrics, summary_stats
from bowaka_lab.metrics.diagnostics import exit_reason_distribution
from bowaka_lab.sim.portfolio_engine import BowakaPortfolioBacktester
from bowaka_lab.utils import (
    ArtifactPaths,
    artifact_exists,
    load_json,
    load_parquet,
    save_json,
    save_parquet,
)


data_root      = Path(DATA_ROOT)      if Path(DATA_ROOT).is_absolute()      else (repo_root / DATA_ROOT).resolve()
artifacts_root = Path(ARTIFACTS_ROOT) if Path(ARTIFACTS_ROOT).is_absolute() else (repo_root / ARTIFACTS_ROOT).resolve()
MINUTE_ROOT = data_root / "parquet/bars/vendor=alpaca" / f"feed={FEED}" / "timeframe=1m/adjustment=raw"

paths = ArtifactPaths.for_run(RUN_ID, artifacts_root)
paths.ensure_dir()
assert paths.candidates.exists(), (
    f"candidates artifact missing: {paths.candidates}\\n"
    "Run notebook 03_prefilter_replay first."
)

cfg = BowakaBacktestConfig.model_validate({
    "data": {"vendor": "alpaca", "feed": FEED, "adjustment": "raw",
             "start_date": "2025-01-02", "end_date": "2026-05-15"},
    "entry": {"default_rule": ENTRY_RULE, "slippage_bps": SLIPPAGE_BPS},
    "exits": {"stop_pct": STOP_PCT, "target_pct": TARGET_PCT,
              "max_hold_days": MAX_HOLD_DAYS},
    "portfolio": {"per_trade_notional": PER_TRADE_NOTIONAL,
                  "max_concurrent_positions": MAX_CONCURRENT_POSITIONS,
                  "max_total_entries_per_day": MAX_TOTAL_ENTRIES_PER_DAY},
})

cal = USEquityCalendar(cfg.calendar.exchange)
print(f"artifacts:     {paths.root}")
print(f"minute root:   {MINUTE_ROOT}")
print(f"entry:         {cfg.entry.default_rule}, slip={cfg.entry.slippage_bps}bps")
print(f"exits:         stop={cfg.exits.stop_pct} target={cfg.exits.target_pct} hold={cfg.exits.max_hold_days}")
'''


LOAD_CANDIDATES = '''candidates_df = load_parquet(paths.candidates)
print(f"candidates loaded: {candidates_df.shape[0]:,} rows")

# Reshape into the dict the backtester expects: signal_date -> per-day DataFrame.
candidate_frames = {
    sd: g.reset_index(drop=True)
    for sd, g in candidates_df.groupby("signal_date", sort=False)
}
candidate_source = candidates_dict_to_source(candidate_frames)
minute_bars_for  = MinuteBarLoader(MINUTE_ROOT)
print(f"signal dates with candidates: {len(candidate_frames):,}")
'''


RUN_BACKTEST = '''trades_df = None
summary = None

if not REBUILD and artifact_exists(paths, "trades") and artifact_exists(paths, "summary"):
    print("Fast path: trades.parquet + summary.json already exist; loading.")
    trades_df = load_parquet(paths.trades)
    summary = load_json(paths.summary)
else:
    runner = BowakaPortfolioBacktester(
        cfg,
        candidate_source=candidate_source,
        minute_bars_for=minute_bars_for,
        calendar=cal,
    )
    result = runner.run()
    trades_df = result.trades_df()

    save_parquet(paths.trades, trades_df)
    save_json(paths.config, cfg.model_dump(mode="json"))

    if trades_df.empty:
        summary = {"trade_count": 0, "win_rate": 0.0, "mean_pnl_pct": 0.0,
                   "total_pnl": 0.0, "exits_by_reason": {}}
    else:
        scored = per_trade_metrics(trades_df, stop_pct=cfg.exits.stop_pct)
        stats = summary_stats(scored)
        exits = (scored["exit_reason"].value_counts().to_dict()
                 if "exit_reason" in scored.columns else {})
        summary = {**stats, "exits_by_reason": exits}
    save_json(paths.summary, summary)

print(f"trades:  {trades_df.shape[0]:,}")
print(f"wrote {paths.trades}")
print(f"wrote {paths.summary}")
print(f"wrote {paths.config}")
'''


SUMMARY = '''import json

print(json.dumps({k: v for k, v in summary.items() if k != "exits_by_reason"}, indent=2))
print()
print("Exits by reason:")
for reason, count in (summary.get("exits_by_reason") or {}).items():
    print(f"  {reason}: {count}")

if not trades_df.empty:
    try:
        from IPython.display import display
        display(trades_df.head(10))
    except Exception:
        print(trades_df.head(10).to_string(index=False))
'''


EQUITY = '''try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

if not trades_df.empty and plt is not None and "pnl" in trades_df.columns:
    daily = trades_df.groupby("trade_date")["pnl"].sum().reset_index()
    daily["cumulative_pnl"] = daily["pnl"].cumsum()
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(daily["trade_date"].astype(str), daily["cumulative_pnl"], marker="o", linewidth=1)
    ax.set_title(f"Cumulative PnL ($) — {RUN_ID}")
    ax.set_xlabel("trade_date")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    plt.show()
else:
    print("(no trades to plot or matplotlib unavailable)")
'''


FUNNEL_CHECK = '''if artifact_exists(paths, "funnel"):
    funnel = load_json(paths.funnel)
    totals = {k: v for k, v in funnel.items() if k != "per_session"}
    print("Prefilter funnel (from notebook 03):")
    for k, v in totals.items():
        print(f"  {k}: {int(v):,}")
    assert int(funnel.get("candidates", 0)) > 0, (
        "Funnel reports zero candidates — re-run notebook 03 with REBUILD=True."
    )
else:
    print("funnel.json missing — run notebook 03 first.")
'''


NEXT = """## Next

- Run **05/06/07/08** for counterfactuals, exits, signal-fade, and liquidity
  analysis.
- Run **11_weekly_research_report.ipynb** to aggregate everything into the
  final Markdown + JSON report."""


def main() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        md_cell(TITLE),
        code_cell(BOOTSTRAP, tag="bootstrap"),
        md_cell("## Configuration"),
        code_cell(PARAMETERS, tag="parameters"),
        md_cell("## Paths + backtest config"),
        code_cell(DERIVED, tag="derived"),
        md_cell("## Load candidates from notebook 03"),
        code_cell(LOAD_CANDIDATES, tag="load_candidates"),
        md_cell("## Run backtest"),
        code_cell(RUN_BACKTEST, tag="run_backtest"),
        md_cell("## Trade summary + exit reasons"),
        code_cell(SUMMARY, tag="summary"),
        md_cell("## Equity curve"),
        code_cell(EQUITY, tag="equity"),
        md_cell("## Funnel sanity (read from notebook 03 artifact)"),
        code_cell(FUNNEL_CHECK, tag="funnel_check"),
        md_cell(NEXT),
    ]
    finalize(nb)
    nbformat.write(nb, NB_PATH)
    print(f"wrote {NB_PATH}")


if __name__ == "__main__":
    main()
