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
# CONFIG_PATH is the single source of truth for the backtest profile.
# Swap to ``configs/bowaka_exact_current_strategy.yml`` to run the
# source-strategy paper-mode profile (signal_fade off, ADV tiers, etc.).
CONFIG_PATH    = "research_notebooks/bowaka_lab/configs/bowaka_research_variant.yml"
REBUILD        = False    # if False and candidates.parquet exists, skip to inline diagnostics

# Optional explicit research overrides — None = use the YAML value.
OVERRIDE_START_DATE = None
OVERRIDE_END_DATE   = None
'''


DERIVED = '''from datetime import date
from pathlib import Path

import pandas as pd

from bowaka_lab.config import (
    assert_exact_mode_invariants,
    compute_config_hash,
    load_config_file,
)
from bowaka_lab.data.assets import load_latest_asset_snapshot
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
config_path    = Path(CONFIG_PATH)    if Path(CONFIG_PATH).is_absolute()    else (repo_root / CONFIG_PATH).resolve()

cfg = load_config_file(config_path)
# Explicit research overrides (operator opt-in): swap start/end without
# editing the YAML.
if OVERRIDE_START_DATE is not None or OVERRIDE_END_DATE is not None:
    cfg = cfg.model_copy(update={
        "data": cfg.data.model_copy(update={
            **({"start_date": OVERRIDE_START_DATE} if OVERRIDE_START_DATE else {}),
            **({"end_date":   OVERRIDE_END_DATE}   if OVERRIDE_END_DATE   else {}),
        }),
    })

# Load the latest asset snapshot before the invariant check so exact mode can
# fail closed on an empty snapshot.
asset_snapshot = load_latest_asset_snapshot(data_root)
asset_snapshot_id = asset_snapshot.attrs.get("snapshot_id", "")
print(f"asset_snapshot: rows={asset_snapshot.shape[0]:,}  snapshot_id={asset_snapshot_id!r}")

assert_exact_mode_invariants(cfg, asset_snapshot=asset_snapshot)
config_hash = compute_config_hash(cfg)

DAILY_ROOT = data_root / "parquet/bars/vendor=alpaca" / f"feed={cfg.data.feed}" / "timeframe=1d/adjustment=raw"

cal = USEquityCalendar(cfg.calendar.exchange)
paths = ArtifactPaths.for_run(RUN_ID, artifacts_root)
paths.ensure_dir()

print(f"config:         {config_path}")
print(f"fidelity_mode:  {cfg.project.fidelity_mode}")
print(f"config_hash:    {config_hash}")
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
        asset_snapshot=asset_snapshot if not asset_snapshot.empty else None,
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
    # Lineage tag every candidates row with the config hash + data feed +
    # asset snapshot id so Phase 8 paper-vs-backtest reconciliation can pin
    # which dataset the row came from.
    if not candidates_df.empty:
        candidates_df["config_hash"]       = config_hash
        candidates_df["data_feed"]         = cfg.data.feed
        candidates_df["asset_snapshot_id"] = asset_snapshot_id

    # Persist EVERY decision (passed + rejected) so notebooks 05/06/07 can
    # build rejected-candidate counterfactuals.
    all_decisions_rows = []
    for sd, cset in csets.items():
        if cset.all_decisions is None or cset.all_decisions.empty:
            continue
        df = cset.all_decisions.reset_index()
        df["signal_date"] = sd
        df["trade_date"] = cset.trade_date
        all_decisions_rows.append(df)
    if all_decisions_rows:
        all_decisions_df = pd.concat(all_decisions_rows, ignore_index=True)
    else:
        all_decisions_df = pd.DataFrame(columns=[
            "symbol", "signal_date", "trade_date", "passed_prefilter",
            "rejection_reasons", "instrument_class", "classification_reason",
            "final_decision", "signal_strength", "rank",
        ])
    if not all_decisions_df.empty:
        all_decisions_df["config_hash"]       = config_hash
        all_decisions_df["data_feed"]         = cfg.data.feed
        all_decisions_df["asset_snapshot_id"] = asset_snapshot_id

    save_parquet(paths.candidates, candidates_df)
    save_parquet(paths.all_decisions, all_decisions_df)
    save_json(paths.funnel, funnel)
    print(f"  wrote {paths.candidates}")
    print(f"  wrote {paths.all_decisions}  ({all_decisions_df.shape[0]:,} rows)")
    print(f"  wrote {paths.funnel}")

print()
print("funnel totals:")
for k in ("universe_with_features", "passed_universe_gates", "candidates",
          "rejected_by_signal_gates", "excluded_by_instrument_class"):
    print(f"  {k}: {funnel[k]:,}")
print()
print("by instrument_class:")
for cls, counts in (funnel.get("by_instrument_class") or {}).items():
    print(f"  {cls}: n_rows={counts['n_rows']:,}  passed={counts['n_passed_prefilter']:,}  "
          f"eligible={counts['n_eligible_equity_bucket']:,}")
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
