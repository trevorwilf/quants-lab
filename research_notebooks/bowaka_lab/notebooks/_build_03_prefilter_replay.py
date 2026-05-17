"""Build ``notebooks/03_prefilter_replay.ipynb``.

Replay the Bowaka daily prefilter across every signal date in the window,
producing ``candidates.parquet`` and ``funnel.json`` under
``artifacts/{run_id}/`` for downstream notebooks (04, 05, 06, 10).
"""

from __future__ import annotations

from pathlib import Path

import nbformat

from _notebook_common import BOOTSTRAP, code_cell, finalize, md_cell

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "03_prefilter_replay.ipynb"


TITLE = """# 03 — Prefilter replay

Replay the Bowaka daily prefilter across every signal date in the configured
window. Produces two artifacts in ``artifacts/{RUN_ID}/``:

- ``candidates.parquet`` — one row per (signal_date, symbol) that passed the
  gates, ranked by ``signal_strength``.
- ``funnel.json`` — aggregated funnel counts matching ``[Report §20.1 §5]``,
  plus per-session breakdowns for the weekly report.

Downstream notebooks (04 backtest, 05 entry counterfactuals, 06 exit surface,
10 Optuna) consume these artifacts directly — no recomputation.
"""


PARAMETERS = '''import os

RUN_ID         = "bt_iex_default"
DATA_ROOT      = os.environ.get(
    "BOWAKA_DATA_ROOT",
    "research_notebooks/bowaka_lab/db_tools/bowaka_data",
)
ARTIFACTS_ROOT = "research_notebooks/bowaka_lab/artifacts"
FEED           = "iex"
START_DATE     = "2025-01-02"
END_DATE       = "2026-05-15"
REBUILD        = False    # if False and candidates.parquet exists, skip to inline diagnostics

# Prefilter knobs (mirror configs/bowaka_backtest_iex_exploratory.yml defaults)
LOOKBACK_DAYS         = 20
ATR_DAYS              = 14
EMA_DAYS              = 10
EMA_SLOPE_LOOKBACK    = 3
PRICE_MIN             = 1.0
PRICE_MAX             = 20.0
AVG_DOLLAR_VOLUME_MIN = 200_000
RVOL_MIN              = 1.5
ATR_PCT_MIN           = 0.06
RANGE_EXPANSION_MIN   = 1.25
CLOSE_LOCATION_MIN    = 0.60
EMA_DISTANCE_MIN      = 0.0
EMA_SLOPE_MIN         = 0.0
'''


DERIVED = '''from datetime import date
from pathlib import Path

import pandas as pd

from bowaka_lab.config.models import BowakaBacktestConfig
from bowaka_lab.data.calendar import USEquityCalendar
from bowaka_lab.data.parquet_io import load_daily_bars_from_root
from bowaka_lab.features.prefilter import (
    aggregate_prefilter_funnel,
    replay_prefilter_over_window,
)
from bowaka_lab.utils import (
    ArtifactPaths,
    artifact_exists,
    load_json,
    load_parquet,
    save_json,
    save_parquet,
)

# Resolve roots relative to the discovered repo_root, not CWD, so the notebook
# works from anywhere under research_notebooks/.
data_root      = Path(DATA_ROOT)      if Path(DATA_ROOT).is_absolute()      else (repo_root / DATA_ROOT).resolve()
artifacts_root = Path(ARTIFACTS_ROOT) if Path(ARTIFACTS_ROOT).is_absolute() else (repo_root / ARTIFACTS_ROOT).resolve()
DAILY_ROOT = data_root / "parquet/bars/vendor=alpaca" / f"feed={FEED}" / "timeframe=1d/adjustment=raw"

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
})

cal = USEquityCalendar(cfg.calendar.exchange)
paths = ArtifactPaths.for_run(RUN_ID, artifacts_root)
paths.ensure_dir()

print(f"data_root:      {data_root}")
print(f"daily root:     {DAILY_ROOT}")
print(f"artifacts:      {paths.root}")
print(f"window:         {cfg.data.start_date} -> {cfg.data.end_date}")
'''


FAST_PATH = '''candidates_df = None
funnel = None

if not REBUILD and artifact_exists(paths, "candidates") and artifact_exists(paths, "funnel"):
    print("Fast path: artifacts already exist; loading instead of recomputing.")
    candidates_df = load_parquet(paths.candidates)
    funnel = load_json(paths.funnel)
    print(f"  candidates: {candidates_df.shape[0]:,} rows")
    print(f"  funnel:     {{k: v for k, v in funnel.items() if k != 'per_session'}}")
else:
    print("Will replay prefilter from daily bars. Set REBUILD=True to force.")
'''


LOAD_DAILY = '''if candidates_df is None:
    assert DAILY_ROOT.exists(), f"daily root missing: {DAILY_ROOT}"
    print("loading daily bars...")
    daily = load_daily_bars_from_root(DAILY_ROOT)
    print(f"daily rows:    {daily.shape[0]:,}")
    print(f"daily symbols: {daily['symbol'].nunique():,}")
    print(f"sessions:      {daily['session_date'].min()} -> {daily['session_date'].max()}")
else:
    daily = None
'''


REPLAY = '''if candidates_df is None:
    sessions_in_window = cal.sessions(cfg.data.start_date, cfg.data.end_date)
    candidate_signals = sessions_in_window[:-1]
    print(f"replaying prefilter over {len(candidate_signals)} signal dates...")
    csets = replay_prefilter_over_window(
        daily,
        cfg.prefilter,
        signal_dates=candidate_signals,
        next_session_fn=cal.next_session,
        universe=cfg.universe,
    )
    funnel = aggregate_prefilter_funnel(csets)

    # Materialise a flat candidates DataFrame for the artifact.
    rows = []
    for sd, cset in csets.items():
        if cset.candidates.empty:
            continue
        df = cset.candidates.reset_index()
        df["signal_date"] = sd
        df["trade_date"] = cset.trade_date
        rows.append(df)
    candidates_df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(
        columns=["symbol", "signal_date", "trade_date", "rank", "signal_strength"]
    )

    save_parquet(paths.candidates, candidates_df)
    save_json(paths.funnel, funnel)
    print(f"  wrote {paths.candidates}")
    print(f"  wrote {paths.funnel}")

print()
print("funnel totals:")
for k in ("universe_with_features", "passed_universe_gates", "candidates",
          "rejected_by_signal_gates", "excluded_by_instrument_class"):
    print(f"  {k}: {funnel[k]:,}")
'''


FUNNEL_TABLE = '''try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

funnel_df = pd.DataFrame(
    [
        {"stage": k, "count": int(funnel[k])}
        for k in ("universe_with_features", "passed_universe_gates", "candidates",
                  "rejected_by_signal_gates", "excluded_by_instrument_class")
    ]
)
print(funnel_df.to_string(index=False))

if plt is not None:
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.barh(funnel_df["stage"], funnel_df["count"])
    ax.set_xlabel("rows")
    ax.set_title(f"Prefilter funnel — {RUN_ID}")
    fig.tight_layout()
    plt.show()
'''


CANDIDATE_DIAG = '''if candidates_df.empty:
    print("No candidates in window — relax gate thresholds and re-run with REBUILD=True.")
else:
    per_session = candidates_df.groupby("signal_date").size()
    print("candidates per signal_date:")
    print(per_session.describe().to_string())

    print()
    print("signal_strength distribution:")
    print(candidates_df["signal_strength"].describe().to_string())

    print()
    print("Top 10 most-frequent symbols across the window:")
    top_syms = candidates_df["symbol"].value_counts().head(10)
    print(top_syms.to_string())

    if plt is not None:
        fig, axes = plt.subplots(1, 2, figsize=(12, 3))
        per_session.hist(ax=axes[0], bins=30)
        axes[0].set_title("candidates per signal_date")
        axes[0].set_xlabel("count")
        candidates_df["signal_strength"].hist(ax=axes[1], bins=30)
        axes[1].set_title("signal_strength distribution")
        axes[1].set_xlabel("strength")
        fig.tight_layout()
        plt.show()
'''


NEXT = """## Next

Open **`notebooks/04_single_config_backtest.ipynb`** to run the portfolio
backtester against these candidates."""


def main() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        md_cell(TITLE),
        code_cell(BOOTSTRAP, tag="bootstrap"),
        md_cell("## Configuration"),
        code_cell(PARAMETERS, tag="parameters"),
        md_cell("## Derived paths + config"),
        code_cell(DERIVED, tag="derived"),
        md_cell("## Decide: rebuild or load existing"),
        code_cell(FAST_PATH, tag="fast_path"),
        md_cell("## Load daily bars"),
        code_cell(LOAD_DAILY, tag="load_daily"),
        md_cell("## Replay prefilter"),
        code_cell(REPLAY, tag="replay"),
        md_cell("## Funnel diagnostics"),
        code_cell(FUNNEL_TABLE, tag="funnel_diag"),
        md_cell("## Candidate rank distribution"),
        code_cell(CANDIDATE_DIAG, tag="candidate_diag"),
        md_cell(NEXT),
    ]
    finalize(nb)
    nbformat.write(nb, NB_PATH)
    print(f"wrote {NB_PATH}")


if __name__ == "__main__":
    main()
