"""Build notebook 09 — paper-vs-backtest reconciliation."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _notebook_common import make_notebook, write_notebook  # noqa: E402


HERE = Path(__file__).resolve().parent


def main() -> None:
    nb = make_notebook([
        {"type": "code", "source": (
            "# Papermill parameter cell.\n"
            "PAPER_LOGS_DIR = 'tests/fixtures/paper_logs_minimal'\n"
        )},
        {"type": "markdown", "source": "# 09 — Paper-vs-Backtest Reconciliation"},
        {"type": "code", "source": (
            "from pathlib import Path\n"
            "from bowaka_v2_lab.reconcile import (import_paper_logs, compare_candidates,\n"
            "  compute_slippage_residuals, render_reconciliation_report)\n"
            "imp = import_paper_logs(PAPER_LOGS_DIR)\n"
            "print('candidates:', len(imp.candidates), 'decisions:', len(imp.decisions))\n"
            "print('drift issues:', len(imp.drift_issues))\n"
            "# In a real run we'd load sim artifacts; here we substitute the paper candidates as a no-op pair.\n"
            "cmp_c = compare_candidates(imp.candidates, imp.candidates, window_seconds=120)\n"
            "cmp_d = compare_candidates(imp.decisions, imp.decisions, window_seconds=120)\n"
            "residuals = compute_slippage_residuals(imp.fills, imp.fills)\n"
            "md = render_reconciliation_report(candidate_match=cmp_c, decision_match=cmp_d,\n"
            "  broker_reject_mismatches=[], slippage_residuals=residuals)\n"
            "print(md[:600])\n"
        )},
    ])
    write_notebook(nb, HERE / "09_paper_vs_backtest_reconciliation.ipynb")
    print("Built 09_paper_vs_backtest_reconciliation.ipynb")


if __name__ == "__main__":
    main()
