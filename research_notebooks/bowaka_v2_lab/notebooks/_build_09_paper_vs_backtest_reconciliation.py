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
            "# Papermill parameters.\n"
            "CONFIG_PATH = 'research_notebooks/bowaka_v2_lab/configs/bowaka_v2_backtest_smoke.yml'\n"
            "PAPER_LOGS_DIR = 'research_notebooks/bowaka_v2_lab/tests/fixtures/paper_logs_minimal'\n"
        )},
        {"type": "markdown", "source": (
            "# 09 — Paper-vs-Backtest Reconciliation\n\n"
            "Reconciles paper-trading logs against a **real backtest's** sim artifacts —\n"
            "candidate, decision, and fill records are matched paper-vs-sim. Point\n"
            "`PAPER_LOGS_DIR` at real paper logs and `CONFIG_PATH` at a backtest config\n"
            "covering the same period for a meaningful reconciliation."
        )},
        {"type": "code", "source": (
            "import pandas as pd\n"
            "from bowaka_v2_lab.reconcile import (import_paper_logs, compare_candidates,\n"
            "  compute_slippage_residuals, render_reconciliation_report)\n"
            "from bowaka_v2_lab.backtest_runner import run_config_backtest\n"
            "# 1. paper logs\n"
            "imp = import_paper_logs(PAPER_LOGS_DIR)\n"
            "print('paper:', len(imp.candidates), 'candidates,', len(imp.decisions), 'decisions,',\n"
            "      len(imp.fills), 'fills; drift issues:', len(imp.drift_issues))\n"
            "# 2. a real backtest provides the sim side\n"
            "result = run_config_backtest(CONFIG_PATH)\n"
            "_rd = result.run_dir\n"
            "sim_candidates = pd.read_parquet(_rd / 'candidate_events.parquet').to_dict('records')\n"
            "sim_decisions = pd.read_parquet(_rd / 'entry_decisions.parquet').to_dict('records')\n"
            "sim_fills = pd.read_parquet(_rd / 'fills.parquet').to_dict('records')\n"
            "print('sim:', len(sim_candidates), 'candidates,', len(sim_decisions), 'decisions,',\n"
            "      len(sim_fills), 'fills')\n"
            "# 3. reconcile paper vs sim\n"
            "cmp_c = compare_candidates(imp.candidates, sim_candidates, window_seconds=120)\n"
            "cmp_d = compare_candidates(imp.decisions, sim_decisions, window_seconds=120)\n"
            "residuals = compute_slippage_residuals(imp.fills, sim_fills)\n"
            "md = render_reconciliation_report(candidate_match=cmp_c, decision_match=cmp_d,\n"
            "  broker_reject_mismatches=[], slippage_residuals=residuals)\n"
            "print('candidates:', cmp_c.n_match, 'match /', cmp_c.n_miss, 'miss /', cmp_c.n_extra, 'extra')\n"
            "print(md[:800])\n"
        )},
    ])
    write_notebook(nb, HERE / "09_paper_vs_backtest_reconciliation.ipynb")
    print("Built 09_paper_vs_backtest_reconciliation.ipynb")


if __name__ == "__main__":
    main()
