"""Build ``notebooks/run_backtest.ipynb`` — the single end-to-end pipeline.

Pattern mirrors ``db_tools/_build_notebook.py``: cell sources live here in one
editable file so the notebook stays in sync after edits. Run this whenever
the body changes:

    python notebooks/_build_run_backtest_notebook.py
"""

from __future__ import annotations

from pathlib import Path

import nbformat

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "run_backtest.ipynb"


TITLE = """# Bowaka Backtest — single end-to-end run

One notebook, three stages:

1. **Load** daily + minute parquet produced by ``db_tools/bowaka_backfill.ipynb``.
2. **Replay** the daily prefilter across every signal_date in the configured
   window (vectorised via ``replay_prefilter_over_window`` — seconds, not minutes).
3. **Backtest** with ``BowakaPortfolioBacktester`` using the default 8% stop /
   15% target / 3-session hold; emit trade ledger, exit-reason summary, and a
   Markdown + JSON report.

Edit the **Configuration** cell below and run all cells. No other cell needs
hand-tuning. Safe to re-run after a backfill update — the loader picks up
whatever's on disk.
"""


BOOTSTRAP = '''# Notebook bootstrap cell. Keep this in every bowaka_lab notebook.
from pathlib import Path
import sys

repo_root = Path.cwd()
while repo_root != repo_root.parent and not (repo_root / "research_notebooks").exists():
    repo_root = repo_root.parent

bowaka_project = repo_root / "research_notebooks" / "bowaka_lab"
src_path = bowaka_project / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import bowaka_lab
from bowaka_lab.utils.env import load_project_dotenv

_loaded_env = load_project_dotenv()
print(f"bowaka_lab {bowaka_lab.__version__}")
print(
    f"bowaka_lab bootstrap: .env loaded from {_loaded_env}"
    if _loaded_env
    else "bowaka_lab bootstrap: no .env found (env vars must be set in shell)"
)
'''


IMPORTS = '''from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json

import pandas as pd

from bowaka_lab.config.models import (
    BowakaBacktestConfig,
)
from bowaka_lab.data.calendar import USEquityCalendar
from bowaka_lab.data.parquet_io import (
    MinuteBarLoader,
    candidates_dict_to_source,
    load_daily_bars_from_root,
)
from bowaka_lab.features.prefilter import (
    aggregate_prefilter_funnel,
    replay_prefilter_over_window,
)
from bowaka_lab.metrics.trade_metrics import per_trade_metrics, summary_stats
from bowaka_lab.metrics.diagnostics import exit_reason_distribution
from bowaka_lab.reports.markdown import ReportInputs
from bowaka_lab.reports.weekly_report import generate_weekly_report
from bowaka_lab.sim.portfolio_engine import BowakaPortfolioBacktester
from bowaka_lab.utils.io import to_parquet_safe
'''


PARAMETERS = '''# --- Data location -------------------------------------
DATA_ROOT = "research_notebooks/bowaka_lab/db_tools/bowaka_data"  # backfill output
ARTIFACTS_DIR = "research_notebooks/bowaka_lab/artifacts/run_backtest"
RUN_ID = "bt_iex_default"

# --- Backtest window -----------------------------------
START_DATE = "2025-01-02"
END_DATE   = "2026-05-15"
FEED       = "iex"

# --- Prefilter knobs (universe + signal gates) ---------
PRICE_MIN              = 1.0
PRICE_MAX              = 20.0
AVG_DOLLAR_VOLUME_MIN  = 200_000
LOOKBACK_DAYS          = 20
ATR_DAYS               = 14
EMA_DAYS               = 10
EMA_SLOPE_LOOKBACK     = 3
RVOL_MIN               = 1.5
ATR_PCT_MIN            = 0.06
RANGE_EXPANSION_MIN    = 1.25
CLOSE_LOCATION_MIN     = 0.60
EMA_DISTANCE_MIN       = 0.0
EMA_SLOPE_MIN          = 0.0

# --- Entry / exit geometry -----------------------------
ENTRY_RULE     = "fixed_time_0945"
SLIPPAGE_BPS   = 25
STOP_PCT       = 0.08
TARGET_PCT     = 0.15
MAX_HOLD_DAYS  = 3

# --- Portfolio sizing ----------------------------------
PER_TRADE_NOTIONAL        = 5_000
MAX_CONCURRENT_POSITIONS  = 18
MAX_TOTAL_ENTRIES_PER_DAY = 25
'''


PATHS_AND_CONFIG = '''data_root = Path(DATA_ROOT)
if not data_root.is_absolute():
    data_root = bowaka_project.parent.parent / data_root
artifacts_dir = Path(ARTIFACTS_DIR)
if not artifacts_dir.is_absolute():
    artifacts_dir = bowaka_project.parent.parent / artifacts_dir
artifacts_dir.mkdir(parents=True, exist_ok=True)

DAILY_ROOT  = data_root / "parquet/bars/vendor=alpaca" / f"feed={FEED}" / "timeframe=1d/adjustment=raw"
MINUTE_ROOT = data_root / "parquet/bars/vendor=alpaca" / f"feed={FEED}" / "timeframe=1m/adjustment=raw"

assert DAILY_ROOT.exists(),  f"daily root missing: {DAILY_ROOT}"
assert MINUTE_ROOT.exists(), f"minute root missing: {MINUTE_ROOT}"

cfg = BowakaBacktestConfig.model_validate({
    "data": {"vendor": "alpaca", "feed": FEED, "adjustment": "raw",
             "start_date": START_DATE, "end_date": END_DATE},
    "prefilter": {
        "lookback_days": LOOKBACK_DAYS, "atr_days": ATR_DAYS,
        "ema_days": EMA_DAYS, "ema_slope_lookback": EMA_SLOPE_LOOKBACK,
        "price_min": PRICE_MIN, "price_max": PRICE_MAX,
        "avg_dollar_volume_min": AVG_DOLLAR_VOLUME_MIN,
        "rvol_min": RVOL_MIN, "atr_pct_min": ATR_PCT_MIN,
        "range_expansion_min": RANGE_EXPANSION_MIN,
        "close_location_min": CLOSE_LOCATION_MIN,
        "ema_distance_min": EMA_DISTANCE_MIN, "ema_slope_min": EMA_SLOPE_MIN,
        "score": {"bounded": False},
    },
    "entry": {"default_rule": ENTRY_RULE, "slippage_bps": SLIPPAGE_BPS},
    "exits": {"stop_pct": STOP_PCT, "target_pct": TARGET_PCT,
              "max_hold_days": MAX_HOLD_DAYS},
    "portfolio": {"per_trade_notional": PER_TRADE_NOTIONAL,
                  "max_concurrent_positions": MAX_CONCURRENT_POSITIONS,
                  "max_total_entries_per_day": MAX_TOTAL_ENTRIES_PER_DAY},
})

cal = USEquityCalendar(cfg.calendar.exchange)
print(f"data_root:     {data_root}")
print(f"daily root:    {DAILY_ROOT}")
print(f"minute root:   {MINUTE_ROOT}")
print(f"artifacts:     {artifacts_dir}")
print(f"window:        {cfg.data.start_date} -> {cfg.data.end_date}")
print(f"entry:         {cfg.entry.default_rule}, slip={cfg.entry.slippage_bps}bps")
print(f"exits:         stop={cfg.exits.stop_pct} target={cfg.exits.target_pct} hold={cfg.exits.max_hold_days}")
'''


LOAD_DAILY = '''print("loading daily bars...")
daily = load_daily_bars_from_root(DAILY_ROOT)
print(f"daily rows:    {daily.shape[0]:,}")
print(f"daily symbols: {daily['symbol'].nunique():,}")
print(f"sessions:      {daily['session_date'].min()} -> {daily['session_date'].max()}")
'''


REPLAY = '''sessions_in_window = cal.sessions(cfg.data.start_date, cfg.data.end_date)
candidate_signals = sessions_in_window[:-1]  # the final session has no next-session inside window

print(f"replaying prefilter over {len(candidate_signals)} signal dates...")
candidates_by_signal = replay_prefilter_over_window(
    daily,
    cfg.prefilter,
    signal_dates=candidate_signals,
    next_session_fn=cal.next_session,
    universe=cfg.universe,
)

# Hand the backtester ranked candidate frames (not full CandidateSet objects).
candidate_frames = {}
total_candidates = 0
for sd, cset in candidates_by_signal.items():
    if cset.candidates.empty:
        continue
    df = cset.candidates.reset_index()
    df["signal_date"] = sd
    candidate_frames[sd] = df
    total_candidates += df.shape[0]
print(f"signal dates with candidates: {len(candidate_frames):,}")
print(f"total candidate rows:         {total_candidates:,}")
if candidate_frames:
    sample_sd = next(iter(candidate_frames))
    print()
    print(f"sample candidates for {sample_sd}:")
    print(candidate_frames[sample_sd][["symbol", "rank", "signal_strength"]].head(10).to_string(index=False))
'''


RUN_BT = '''candidate_source = candidates_dict_to_source(candidate_frames)
minute_bars_for = MinuteBarLoader(MINUTE_ROOT)

print("running backtester...")
runner = BowakaPortfolioBacktester(
    cfg,
    candidate_source=candidate_source,
    minute_bars_for=minute_bars_for,
    calendar=cal,
)
result = runner.run()
trades_df = result.trades_df()
print(f"trades emitted: {trades_df.shape[0]}")
if not trades_df.empty:
    try:
        from IPython.display import display
        display(trades_df.head(10))
    except Exception:
        print(trades_df.head(10).to_string(index=False))
'''


DIAGNOSTICS = '''if trades_df.empty:
    print("No trades — check the candidate counts above and your gate thresholds.")
else:
    trades = per_trade_metrics(trades_df, stop_pct=cfg.exits.stop_pct)
    summary = summary_stats(trades)
    print("=== summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    print()
    print("=== exit reasons ===")
    exits = exit_reason_distribution(trades)
    try:
        from IPython.display import display
        display(exits)
    except Exception:
        print(exits.to_string(index=False))

    daily_pnl = trades.groupby("trade_date")["pnl"].sum().reset_index()
    daily_pnl["cumulative_pnl"] = daily_pnl["pnl"].cumsum()
    try:
        ax = daily_pnl.plot(x="trade_date", y="cumulative_pnl", figsize=(10, 4), legend=False)
        ax.set_title("Cumulative PnL ($)")
        ax.set_ylabel("PnL")
    except Exception:
        print(daily_pnl.tail(10).to_string(index=False))
'''


PERSIST_AND_REPORT = '''trades_path = artifacts_dir / f"{RUN_ID}_trades.parquet"
if not trades_df.empty:
    # to_parquet_safe JSON-encodes dict/list columns (e.g. trades_df has an
    # all-empty `diagnostics` struct that vanilla pyarrow refuses to write).
    to_parquet_safe(trades_df, trades_path)
    print(f"wrote {trades_path}")

if not trades_df.empty:
    trades_for_report = per_trade_metrics(trades_df, stop_pct=cfg.exits.stop_pct)
else:
    trades_for_report = trades_df

funnel = aggregate_prefilter_funnel(candidates_by_signal)
print("funnel totals:", {k: v for k, v in funnel.items() if k != "per_session"})

res = generate_weekly_report(
    output_dir=artifacts_dir,
    inputs=ReportInputs(
        run_id=RUN_ID,
        config_hash="sha256:notebook_run",
        data_feed=cfg.data.feed,
        universe_mode=cfg.universe.mode,
        trades=trades_for_report,
        prefilter_funnel=funnel,
        known_limitations=["IEX-only feed (exploratory)", "current-universe survivorship-biased"],
        next_actions=[
            "Iterate on the prefilter gates and re-run.",
            "Switch FEED to 'sip' once a subscription is active.",
            "Re-run after the next weekly backfill to extend the window.",
        ],
    ),
)
print(f"markdown report: {res.markdown_path}")
print(f"json summary:    {res.summary_path}")
print(json.dumps(res.summary["performance"], indent=2))
'''


def _code(source: str, tag: str | None = None) -> nbformat.NotebookNode:
    cell = nbformat.v4.new_code_cell(source)
    if tag is not None:
        cell.metadata["tags"] = [tag]
    return cell


def main() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_markdown_cell(TITLE),
        _code(BOOTSTRAP),
        _code(IMPORTS),
        nbformat.v4.new_markdown_cell("## Configuration\n\nEdit these and re-run all cells."),
        _code(PARAMETERS, tag="parameters"),
        nbformat.v4.new_markdown_cell("## Paths + backtest config"),
        _code(PATHS_AND_CONFIG, tag="config"),
        nbformat.v4.new_markdown_cell("## Load daily bars from the backfill"),
        _code(LOAD_DAILY, tag="load_daily"),
        nbformat.v4.new_markdown_cell("## Replay prefilter across the window"),
        _code(REPLAY, tag="replay"),
        nbformat.v4.new_markdown_cell("## Run the backtester"),
        _code(RUN_BT, tag="backtest"),
        nbformat.v4.new_markdown_cell("## Diagnostics"),
        _code(DIAGNOSTICS, tag="diagnostics"),
        nbformat.v4.new_markdown_cell("## Persist + report"),
        _code(PERSIST_AND_REPORT, tag="report"),
    ]
    # Default kernel name "python3" works in both the JupyterLab Docker image
    # (/opt/conda/envs/quants-lab/bin/python) and a Windows install (where
    # python3 was patched to C:\\Python312\\python.exe).
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb.metadata["language_info"] = {"name": "python", "version": "3.12"}
    nbformat.write(nb, NB_PATH)
    print(f"wrote {NB_PATH}")


if __name__ == "__main__":
    main()
