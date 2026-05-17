"""Build ``notebooks/09_paper_vs_backtest_reconciliation.ipynb``.

Compare live paper-trading logs to the backtest replay. Skips gracefully if
``BOWAKA_PAPER_LOGS_ROOT`` is unset.
"""

from __future__ import annotations

from pathlib import Path

import nbformat

from _notebook_common import BOOTSTRAP, code_cell, finalize, md_cell

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "09_paper_vs_backtest_reconciliation.ipynb"


TITLE = """# 09 — Paper vs backtest reconciliation

Compares the simulated trade ledger (``trades.parquet`` from notebook 04) to
the live paper-trading logs. Requires ``BOWAKA_PAPER_LOGS_ROOT`` in ``.env``
pointing at the legacy Bowaka log root. Without it, the notebook exits
gracefully.

Surfaces classifications per ``[Report §15.4]``:
``candidate_match`` / ``candidate_missing_in_backtest`` /
``data_feed_mismatch`` / ``entry_timing_mismatch`` / ``fill_model_mismatch`` /
``exit_rule_mismatch`` / ``implementation_mismatch`` /
``broker_rejection_mismatch`` / ``paper_log_corruption`` /
``test_ledger_contamination``.
"""


PARAMETERS = '''import os

RUN_ID                = "bt_iex_default"
ARTIFACTS_ROOT        = "research_notebooks/bowaka_lab/artifacts"
PAPER_LOGS_ROOT       = os.environ.get("BOWAKA_PAPER_LOGS_ROOT")
PRODUCTION_ACCOUNT_ID = os.environ.get("ALPACA_ACCOUNT_ID") or None
REBUILD               = False
'''


DERIVED = '''from pathlib import Path

import pandas as pd

from bowaka_lab.reconcile.paper_log_importer import (
    load_daily_summary,
    load_per_trade_logs,
    load_trade_ledger,
)
from bowaka_lab.reconcile.replay_comparator import (
    detect_ledger_contamination,
    reconcile,
)
from bowaka_lab.utils import (
    ArtifactPaths,
    artifact_exists,
    load_parquet,
    save_parquet,
)


artifacts_root = Path(ARTIFACTS_ROOT) if Path(ARTIFACTS_ROOT).is_absolute() else (repo_root / ARTIFACTS_ROOT).resolve()
paths = ArtifactPaths.for_run(RUN_ID, artifacts_root)
paths.ensure_dir()
assert paths.trades.exists(), f"trades missing: {paths.trades} — run notebook 04 first."

paper_root = Path(PAPER_LOGS_ROOT).expanduser().resolve() if PAPER_LOGS_ROOT else None
print(f"artifacts:    {paths.root}")
print(f"paper_root:   {paper_root}")
'''


EARLY_EXIT = '''if paper_root is None or not paper_root.exists():
    print()
    print("BOWAKA_PAPER_LOGS_ROOT is not set or path does not exist; skipping reconciliation.")
    print("Set BOWAKA_PAPER_LOGS_ROOT in your .env (root of the paper-trading log tree)")
    print("and re-run this notebook. Nothing else to do.")
    skip_remaining = True
else:
    skip_remaining = False
'''


LOAD_PAPER = '''if not skip_remaining:
    summary = load_daily_summary(paper_root / "daily_summary.jsonl")
    ledger  = load_trade_ledger(paper_root / "trade_ledger.jsonl")
    trades_dir = paper_root / "trades"
    per_trade = load_per_trade_logs(trades_dir) if trades_dir.exists() else None
    print(f"daily_summary: rows={summary.df.shape[0]:,} errors={summary.errors.shape[0]:,}")
    print(f"trade_ledger:  rows={ledger.df.shape[0]:,} errors={ledger.errors.shape[0]:,}")
    if per_trade is not None:
        print(f"per-trade:     rows={per_trade.df.shape[0]:,} errors={per_trade.errors.shape[0]:,}")
'''


RUN_RECONCILE = '''reconciliation_df = None

if not skip_remaining:
    if not REBUILD and artifact_exists(paths, "reconciliation"):
        print("Fast path: reconciliation.parquet exists; loading.")
        reconciliation_df = load_parquet(paths.reconciliation)
    else:
        backtest_trades = load_parquet(paths.trades)
        paper_trades = summary.df if not summary.df.empty else pd.DataFrame()

        reconciliation_df = reconcile(
            paper_trades=paper_trades,
            backtest_trades=backtest_trades,
            production_account=PRODUCTION_ACCOUNT_ID,
        )
        save_parquet(paths.reconciliation, reconciliation_df)
        print(f"wrote {paths.reconciliation}")

    print(f"reconciliation rows: {reconciliation_df.shape[0]:,}")
'''


CLASSIFICATION = '''if not skip_remaining and reconciliation_df is not None and not reconciliation_df.empty:
    counts = reconciliation_df["classification"].value_counts()
    try:
        from IPython.display import display
        display(counts.to_frame("count"))
    except Exception:
        print(counts.to_string())

    # Highlight the most actionable buckets.
    for cls in ("implementation_mismatch", "test_ledger_contamination", "broker_rejection_mismatch"):
        subset = reconciliation_df[reconciliation_df["classification"] == cls]
        if not subset.empty:
            print()
            print(f"=== {cls}: {subset.shape[0]} rows ===")
            print(subset.head(10).to_string(index=False))

    # Ledger contamination detector (orthogonal, raw-ledger pattern).
    if not skip_remaining:
        contam = detect_ledger_contamination(ledger.df, production_account=PRODUCTION_ACCOUNT_ID)
        if not contam.empty:
            print()
            print(f"=== ledger contamination heuristics: {contam.shape[0]} rows ===")
            print(contam.head(10).to_string(index=False))
'''


ACTIONS = '''if not skip_remaining and reconciliation_df is not None and not reconciliation_df.empty:
    # Anything that's not candidate_match needs an operator decision.
    actionable = reconciliation_df[reconciliation_df["classification"] != "candidate_match"]
    print()
    print(f"actionable rows (non-match): {actionable.shape[0]:,}")
    if not actionable.empty:
        print()
        print("Distribution of actionable classifications:")
        print(actionable["classification"].value_counts().to_string())
'''


NEXT = """## Next

Open **`notebooks/11_weekly_research_report.ipynb`** to aggregate every
artifact you've produced into the final Markdown + JSON report."""


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
        code_cell(EARLY_EXIT, tag="early_exit"),
        md_cell("## Load paper logs"),
        code_cell(LOAD_PAPER, tag="load_paper"),
        md_cell("## Reconcile paper ↔ backtest"),
        code_cell(RUN_RECONCILE, tag="reconcile"),
        md_cell("## Classification breakdown"),
        code_cell(CLASSIFICATION, tag="classification"),
        md_cell("## Action items"),
        code_cell(ACTIONS, tag="actions"),
        md_cell(NEXT),
    ]
    finalize(nb)
    nbformat.write(nb, NB_PATH)
    print(f"wrote {NB_PATH}")


if __name__ == "__main__":
    main()
