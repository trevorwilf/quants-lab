"""Build ``notebooks/02_daily_bar_backfill.ipynb``.

Read-only coverage report for the daily-bar Parquet tree. Does NOT re-fetch.
"""

from __future__ import annotations

from pathlib import Path

import nbformat

from _notebook_common import BOOTSTRAP, code_cell, finalize, md_cell

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "02_daily_bar_backfill.ipynb"


TITLE = """# 02 — Daily-bar coverage

**Read-only.** This notebook inspects the daily-bar Parquet tree on disk —
it does NOT pull new data. To fetch (or extend) the backfill, use
``db_tools/bowaka_backfill.ipynb``.

Shows coverage by date, coverage by symbol (with missing-session detection
against the XNYS calendar), and an audit summary from Mongo
(``bowaka_daily_bar_audits``).
"""


PARAMETERS = '''import os

DATA_ROOT      = os.environ.get(
    "BOWAKA_DATA_ROOT",
    "research_notebooks/bowaka_lab/db_tools/bowaka_data",
)
MONGO_URI      = os.environ.get("MONGO_URI")
MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "bowaka_lab")
FEED           = "iex"
COVERAGE_MIN_PCT = 0.50   # symbols with <X% of expected sessions are flagged
'''


DERIVED = '''from pathlib import Path

import pandas as pd

from bowaka_lab.data.calendar import USEquityCalendar
from bowaka_lab.data.parquet_io import load_daily_bars_from_root


data_root = Path(DATA_ROOT) if Path(DATA_ROOT).is_absolute() else (repo_root / DATA_ROOT).resolve()
DAILY_ROOT = data_root / "parquet/bars/vendor=alpaca" / f"feed={FEED}" / "timeframe=1d/adjustment=raw"
print(f"daily root: {DAILY_ROOT}")
assert DAILY_ROOT.exists(), f"daily root missing: {DAILY_ROOT}\\nRun db_tools/bowaka_backfill.ipynb first."
'''


LOAD = '''print("loading daily bars (this may take 30-90s for a full backfill)...")
daily = load_daily_bars_from_root(DAILY_ROOT)
print(f"rows:    {daily.shape[0]:,}")
print(f"symbols: {daily['symbol'].nunique():,}")
print(f"window:  {daily['session_date'].min()} -> {daily['session_date'].max()}")
'''


BY_DATE = '''try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

per_date = daily.groupby("session_date")["symbol"].nunique().sort_index()
print(f"sessions covered: {per_date.shape[0]:,}")
print(f"distinct symbols per session — min: {int(per_date.min())}, "
      f"median: {int(per_date.median())}, max: {int(per_date.max())}")

if plt is not None and not per_date.empty:
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(per_date.index.astype(str), per_date.values, linewidth=1)
    ax.set_title("Distinct symbols per session_date")
    ax.set_xlabel("session_date")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    plt.show()
'''


BY_SYMBOL = '''per_sym = daily.groupby("symbol")["session_date"].nunique().sort_values()
print(f"sessions-per-symbol — min: {int(per_sym.min())}, "
      f"median: {int(per_sym.median())}, max: {int(per_sym.max())}")

cal = USEquityCalendar()
expected_sessions = len(cal.sessions(daily["session_date"].min(), daily["session_date"].max()))
print(f"expected_sessions across full window: {expected_sessions:,}")

low_coverage = per_sym[per_sym < COVERAGE_MIN_PCT * expected_sessions]
print(f"symbols with < {COVERAGE_MIN_PCT:.0%} coverage: {low_coverage.shape[0]:,}")
print("(top 20)")
print(low_coverage.head(20).to_string())

if plt is not None:
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.hist(per_sym.values, bins=40)
    ax.set_title("Sessions-per-symbol distribution")
    ax.set_xlabel("sessions")
    fig.tight_layout()
    plt.show()
'''


MISSING = '''# Per-symbol gap detection: cluster missing sessions and flag the largest gaps.
all_sessions = pd.DatetimeIndex(cal.sessions(daily["session_date"].min(), daily["session_date"].max())).date

missing_rows = []
sample = per_sym.tail(20).index.tolist()  # 20 most-covered symbols as a sanity sample
for sym in sample:
    have = set(daily.loc[daily["symbol"] == sym, "session_date"].tolist())
    missing = [d for d in all_sessions if d not in have]
    if not missing:
        continue
    # Group consecutive missing days into clusters.
    cluster_start, prev = missing[0], missing[0]
    clusters = []
    for d in missing[1:]:
        if (d - prev).days <= 1:
            prev = d; continue
        clusters.append((cluster_start, prev))
        cluster_start, prev = d, d
    clusters.append((cluster_start, prev))
    missing_rows.append({"symbol": sym, "total_missing": len(missing),
                         "largest_gap": max((b - a).days for a, b in clusters) + 1,
                         "n_clusters": len(clusters)})

if missing_rows:
    miss_df = pd.DataFrame(missing_rows).sort_values("largest_gap", ascending=False)
    print("Missing-session clusters (sample of 20 most-covered symbols):")
    try:
        from IPython.display import display
        display(miss_df)
    except Exception:
        print(miss_df.to_string(index=False))
'''


AUDIT_MONGO = '''if MONGO_URI:
    try:
        from pymongo import MongoClient
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        coll = client[MONGO_DATABASE]["bowaka_daily_bar_audits"]
        rows = list(coll.find({"feed": FEED, "timeframe": "1d"}))
        client.close()
        if rows:
            audits = pd.DataFrame(rows)
            print(f"audits in Mongo: {audits.shape[0]:,}")
            print()
            if "passed_research_audit" in audits.columns:
                print("passed_research_audit counts:")
                print(audits["passed_research_audit"].value_counts().to_string())
        else:
            print("no audits in Mongo yet. Run db_tools/bowaka_backfill Stage 5 to populate.")
    except Exception as exc:
        print(f"Mongo unreachable: {exc}")
else:
    print("MONGO_URI not set — skipping audit summary.")
'''


NEXT = """## Next

Run **`notebooks/03_prefilter_replay.ipynb`** to materialise candidates
from these daily bars."""


def main() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        md_cell(TITLE),
        code_cell(BOOTSTRAP, tag="bootstrap"),
        md_cell("## Configuration"),
        code_cell(PARAMETERS, tag="parameters"),
        md_cell("## Derived paths"),
        code_cell(DERIVED, tag="derived"),
        md_cell("## Load daily bars"),
        code_cell(LOAD, tag="load"),
        md_cell("## Coverage by date"),
        code_cell(BY_DATE, tag="by_date"),
        md_cell("## Coverage by symbol"),
        code_cell(BY_SYMBOL, tag="by_symbol"),
        md_cell("## Missing-session clusters (sample)"),
        code_cell(MISSING, tag="missing"),
        md_cell("## Audit summary from Mongo"),
        code_cell(AUDIT_MONGO, tag="audit_mongo"),
        md_cell(NEXT),
    ]
    finalize(nb)
    nbformat.write(nb, NB_PATH)
    print(f"wrote {NB_PATH}")


if __name__ == "__main__":
    main()
