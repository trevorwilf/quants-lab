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

from bowaka_lab.config import (
    assert_exact_mode_invariants,
    compute_config_hash,
    load_config_file,
)
from bowaka_lab.data.assets import load_latest_asset_snapshot
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


PARAMETERS = '''# --- Data location + config ----------------------------
DATA_ROOT = "research_notebooks/bowaka_lab/db_tools/bowaka_data"  # backfill output
ARTIFACTS_DIR = "research_notebooks/bowaka_lab/artifacts/run_backtest"
RUN_ID = "bt_iex_default"
# Swap to ``configs/bowaka_exact_current_strategy.yml`` for the source-strategy
# paper-mode profile.
CONFIG_PATH = "research_notebooks/bowaka_lab/configs/bowaka_research_variant.yml"

# Optional explicit research overrides on data window — None = use YAML.
OVERRIDE_START_DATE = None
OVERRIDE_END_DATE   = None
'''


PATHS_AND_CONFIG = '''data_root = Path(DATA_ROOT)
if not data_root.is_absolute():
    data_root = bowaka_project.parent.parent / data_root
artifacts_dir = Path(ARTIFACTS_DIR)
if not artifacts_dir.is_absolute():
    artifacts_dir = bowaka_project.parent.parent / artifacts_dir
artifacts_dir.mkdir(parents=True, exist_ok=True)
config_path = Path(CONFIG_PATH)
if not config_path.is_absolute():
    config_path = bowaka_project.parent.parent / config_path

cfg = load_config_file(config_path)
if OVERRIDE_START_DATE is not None or OVERRIDE_END_DATE is not None:
    cfg = cfg.model_copy(update={
        "data": cfg.data.model_copy(update={
            **({"start_date": OVERRIDE_START_DATE} if OVERRIDE_START_DATE else {}),
            **({"end_date":   OVERRIDE_END_DATE}   if OVERRIDE_END_DATE   else {}),
        }),
    })

# Asset snapshot is loaded BEFORE invariants so exact mode fails closed when
# absent. Research mode just gets an empty DataFrame and skips classification.
asset_snapshot = load_latest_asset_snapshot(data_root)
asset_snapshot_id = asset_snapshot.attrs.get("snapshot_id", "")
print(f"asset_snapshot: rows={asset_snapshot.shape[0]:,}  snapshot_id={asset_snapshot_id!r}")

assert_exact_mode_invariants(cfg, asset_snapshot=asset_snapshot)
config_hash = compute_config_hash(cfg)

DAILY_ROOT  = data_root / "parquet/bars/vendor=alpaca" / f"feed={cfg.data.feed}" / "timeframe=1d/adjustment=raw"
MINUTE_ROOT = data_root / "parquet/bars/vendor=alpaca" / f"feed={cfg.data.feed}" / "timeframe=1m/adjustment=raw"

assert DAILY_ROOT.exists(),  f"daily root missing: {DAILY_ROOT}"
assert MINUTE_ROOT.exists(), f"minute root missing: {MINUTE_ROOT}"

cal = USEquityCalendar(cfg.calendar.exchange)
print(f"config:        {config_path}")
print(f"config_hash:   {config_hash}")
print(f"fidelity_mode: {cfg.project.fidelity_mode}")
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
    asset_snapshot=asset_snapshot if not asset_snapshot.empty else None,
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
        config_hash=config_hash,
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
