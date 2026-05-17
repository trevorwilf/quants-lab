"""Build ``notebooks/07_signal_fade_study.ipynb``.

Score signal fade at 15:45 ET on the entry day for each trade in
``trades.parquet``. Save ``signal_fade.parquet`` and tabulate counterfactual
exits at thresholds {None, 6, 7, 8, 9}.
"""

from __future__ import annotations

from pathlib import Path

import nbformat

from _notebook_common import BOOTSTRAP, code_cell, finalize, md_cell

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "07_signal_fade_study.ipynb"


TITLE = """# 07 — Signal-fade study

For each trade in ``trades.parquet`` from notebook **04**, compute the
signal-fade score at 15:45 ET of the entry day per ``[Report §13]``. Persist
per-trade score, bucket ({none, soft, hard, critical}), and triggered
components. Tabulate counterfactual "exit at 15:45 if score ≥ T" for the
default threshold variants.

A second log-only fade is computed at 16:05 ET to confirm the post-close
convention — that pass never produces an executable exit.
"""


PARAMETERS = '''import os

RUN_ID                = "bt_iex_default"
DATA_ROOT             = os.environ.get(
    "BOWAKA_DATA_ROOT",
    "research_notebooks/bowaka_lab/db_tools/bowaka_data",
)
ARTIFACTS_ROOT        = "research_notebooks/bowaka_lab/artifacts"
FEED                  = "iex"
REBUILD               = False

RTH_EVAL_TIME         = "15:45"   # ET; primary fade evaluation
AFTER_CLOSE_EVAL_TIME = "16:05"   # ET; analytics-only (never executable)
EXECUTE_THRESHOLDS    = [None, 6, 7, 8, 9]   # what-if exit thresholds
'''


DERIVED = '''from datetime import date, time
from pathlib import Path

import numpy as np
import pandas as pd

from bowaka_lab.data.calendar import USEquityCalendar
from bowaka_lab.data.parquet_io import MinuteBarLoader
from bowaka_lab.features.signal_fade_features import assemble_intraday_context
from bowaka_lab.sim.signal_fade import compute_signal_fade_score
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
assert paths.trades.exists(), (
    f"trades artifact missing: {paths.trades}\\n"
    "Run notebook 04_single_config_backtest first."
)
cal = USEquityCalendar()
minute_loader = MinuteBarLoader(MINUTE_ROOT)
print(f"artifacts:  {paths.root}")
print(f"rth eval:   {RTH_EVAL_TIME}  after-close: {AFTER_CLOSE_EVAL_TIME}")
print(f"thresholds: {EXECUTE_THRESHOLDS}")
'''


LOAD_TRADES = '''trades_df = load_parquet(paths.trades)
print(f"trades loaded: {trades_df.shape[0]:,}")
if trades_df.empty:
    print("No trades — run notebook 04 first.")
'''


COMPUTE_FADE = '''# Parse the HH:MM eval-time strings once into (hours, minutes) so we can
# build per-session UTC timestamps inline below — keeping the cell strictly
# orchestration-only (no def/class).
_rth_h, _rth_m = (int(x) for x in RTH_EVAL_TIME.split(":"))
_ac_h,  _ac_m  = (int(x) for x in AFTER_CLOSE_EVAL_TIME.split(":"))

fade_rows = []
fade_df = None

if not REBUILD and artifact_exists(paths, "signal_fade"):
    print("Fast path: signal_fade.parquet exists; loading.")
    fade_df = load_parquet(paths.signal_fade)
else:
    if not trades_df.empty:
        sessions = sorted(set(trades_df["trade_date"]))
        n = len(sessions)
        for i, sess in enumerate(sessions, start=1):
            day_trades = trades_df[trades_df["trade_date"] == sess]
            symbols = day_trades["symbol"].astype(str).unique().tolist()
            bars = minute_loader(sess, symbols)
            if bars.empty:
                continue
            _sess_ny = pd.Timestamp(sess).tz_localize("America/New_York")
            rth_ts = (_sess_ny + pd.Timedelta(hours=_rth_h, minutes=_rth_m)).tz_convert("UTC")
            ac_ts  = (_sess_ny + pd.Timedelta(hours=_ac_h,  minutes=_ac_m)).tz_convert("UTC")
            for _, t in day_trades.iterrows():
                sym = t["symbol"]
                entry_price = float(t["entry_price"])
                entry_time = pd.Timestamp(t["entry_time"])
                if entry_time.tz is None:
                    entry_time = entry_time.tz_localize("UTC")
                sym_bars = bars[bars["symbol"] == sym].sort_values("timestamp")
                if sym_bars.empty:
                    continue
                prior_close = float(t.get("entry_price")) - 0.0  # not always available; entry_price is a safe stand-in
                for label, ts in (("rth", rth_ts), ("after_close", ac_ts)):
                    bars_through = sym_bars[sym_bars["timestamp"] <= ts]
                    if bars_through.empty:
                        continue
                    ctx = assemble_intraday_context(
                        bars_through_now=bars_through,
                        entry_price=entry_price,
                        entry_time=entry_time,
                        now_ts=ts,
                        prior_close=prior_close,
                        session_date=sess,
                    )
                    current_return = (ctx.current_price / entry_price) - 1.0 if entry_price else 0.0
                    mfe_pct = float(t.get("mfe_pct", current_return) or 0.0)
                    res = compute_signal_fade_score(
                        entry_price=entry_price,
                        mfe_pct=mfe_pct,
                        current_return_pct=current_return,
                        minutes_since_entry=ctx.minutes_since_entry,
                        intraday=ctx,
                    )
                    triggered = [c.name for c in res.components]
                    fade_rows.append({
                        "trade_id": t.get("trade_id"),
                        "symbol": sym,
                        "trade_date": sess,
                        "eval_label": label,
                        "eval_time": str(ts),
                        "score": int(res.score),
                        "bucket": res.bucket,
                        "current_price": float(ctx.current_price),
                        "current_return_pct": float(current_return),
                        "mfe_pct": float(mfe_pct),
                        "triggered_components": triggered,
                    })
            if i % 25 == 0:
                print(f"  {i}/{n} sessions processed")
    fade_df = pd.DataFrame(fade_rows)
    save_parquet(paths.signal_fade, fade_df)
    print(f"wrote {paths.signal_fade}")

print(f"fade rows: {fade_df.shape[0]:,}")
'''


BUCKET_DIST = '''rth = fade_df[fade_df["eval_label"] == "rth"]
ac  = fade_df[fade_df["eval_label"] == "after_close"]

if rth.empty:
    print("no RTH fade rows")
else:
    print("RTH (15:45 ET) bucket distribution:")
    print(rth["bucket"].value_counts().to_string())
    print()
    # Cross-tab with the actual exit_reason from trades_df.
    if "trade_id" in trades_df.columns and "exit_reason" in trades_df.columns:
        joined = rth.merge(
            trades_df[["trade_id", "exit_reason", "pnl_pct"]],
            on="trade_id",
            how="left",
        )
        ct = pd.crosstab(joined["bucket"], joined["exit_reason"])
        print("RTH bucket × actual exit_reason:")
        try:
            from IPython.display import display
            display(ct)
        except Exception:
            print(ct.to_string())

if not ac.empty:
    print()
    print("After-close (16:05 ET, log-only) bucket distribution:")
    print(ac["bucket"].value_counts().to_string())
'''


THRESHOLDS = '''rth_with_pnl = (rth.merge(trades_df[["trade_id", "pnl_pct"]], on="trade_id", how="left")
                if not rth.empty and "trade_id" in trades_df.columns else pd.DataFrame())

if rth_with_pnl.empty:
    print("no rth fade rows to threshold")
else:
    rows = []
    for thr in EXECUTE_THRESHOLDS:
        if thr is None:
            label = "no_fade_exit"
            actual_pnl_when_exited = rth_with_pnl["pnl_pct"]
            n_exited = 0
        else:
            mask = rth_with_pnl["score"] >= int(thr)
            n_exited = int(mask.sum())
            # Counterfactual: trades where mask is True exit at 15:45 — use
            # current_return_pct AT 15:45 as the realised pnl for those trades.
            cf_pnl = rth_with_pnl["pnl_pct"].copy()
            cf_pnl.loc[mask] = rth_with_pnl.loc[mask, "current_return_pct"]
            actual_pnl_when_exited = cf_pnl
            label = f"threshold>={thr}"
        rows.append({
            "label": label,
            "n_would_exit": n_exited,
            "median_pnl_pct_after_cf": float(actual_pnl_when_exited.median()) if len(actual_pnl_when_exited) else 0.0,
            "mean_pnl_pct_after_cf": float(actual_pnl_when_exited.mean()) if len(actual_pnl_when_exited) else 0.0,
        })
    thr_df = pd.DataFrame(rows)
    try:
        from IPython.display import display
        display(thr_df)
    except Exception:
        print(thr_df.to_string(index=False))
'''


NEXT = """## Next

- **`notebooks/08_liquidity_and_execution_quality.ipynb`** for ADV / spread /
  gap-through analysis.
- Or jump to **`notebooks/11_weekly_research_report.ipynb`** to aggregate."""


def main() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        md_cell(TITLE),
        code_cell(BOOTSTRAP, tag="bootstrap"),
        md_cell("## Configuration"),
        code_cell(PARAMETERS, tag="parameters"),
        md_cell("## Derived paths + helpers"),
        code_cell(DERIVED, tag="derived"),
        md_cell("## Load trades"),
        code_cell(LOAD_TRADES, tag="load_trades"),
        md_cell("## Compute fade score at 15:45 ET (and log-only at 16:05 ET)"),
        code_cell(COMPUTE_FADE, tag="compute_fade"),
        md_cell("## Bucket distribution + bucket × exit_reason cross-tab"),
        code_cell(BUCKET_DIST, tag="bucket_dist"),
        md_cell("## Execute-threshold counterfactual"),
        code_cell(THRESHOLDS, tag="thresholds"),
        md_cell(NEXT),
    ]
    finalize(nb)
    nbformat.write(nb, NB_PATH)
    print(f"wrote {NB_PATH}")


if __name__ == "__main__":
    main()
