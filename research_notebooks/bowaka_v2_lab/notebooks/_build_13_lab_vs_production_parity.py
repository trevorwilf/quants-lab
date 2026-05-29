"""Build notebook 13 — production-vs-lab parity."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _notebook_common import make_notebook, write_notebook  # noqa: E402


HERE = Path(__file__).resolve().parent


def main() -> None:
    nb = make_notebook([
        {"type": "code", "source": (
            "# Papermill parameters — override via `papermill -p <name> <value>` or in-place.\n"
            "START_DATE = '2026-05-19'      # parity-window inclusive start (ISO date)\n"
            "END_DATE   = '2026-05-23'      # parity-window inclusive end   (ISO date)\n"
            "SYMBOLS    = None              # optional list[str]; default = small PIT sample\n"
            "PROD_CONFIG_PATH = 'research_notebooks/bowaka_v2_lab/reference/source_strategy/scripts/bowaka_v2_config.yaml'\n"
            "LAB_CONFIG_PATH  = 'research_notebooks/bowaka_v2_lab/configs/bowaka_v2_actual_iex_current_code.yml'\n"
            "LAKE_ROOT  = None              # default = bowaka_common.resolve_market_data_root()\n"
            "COST_STRESS = 'conservative'   # passed to both sides identically\n"
            "RUN_LABEL  = None              # default = UTC timestamp folder name\n"
        )},
        {"type": "markdown", "source": (
            "# 13 — Production-vs-Lab Parity\n\n"
            "Empirical agreement between the production-side backtester\n"
            "(`reference/source_strategy/scripts/bowaka_v2_backtest.py`) and the lab's\n"
            "`run_config_backtest` over a chosen window. Audit §14.5 thresholds drive the\n"
            "stop-ship verdict; failing rows point at a specific divergence class.\n\n"
            "**Requires Phase 0's fix landed** — pre-fix the production side always read\n"
            "deterministic synthetic data and the parity metrics are meaningless."
        )},
        {"type": "code", "source": (
            "# Resolve lake root + a sensible default universe.\n"
            "import datetime as _dt\n"
            "from pathlib import Path\n"
            "\n"
            "from bowaka_common.marketdata.store import resolve_market_data_root\n"
            "from bowaka_common.marketdata.catalog import available_symbols\n"
            "\n"
            "_lake_root = Path(LAKE_ROOT).resolve() if LAKE_ROOT else resolve_market_data_root(None, create=False)\n"
            "print(f'lake_root: {_lake_root}')\n"
            "\n"
            "_start = _dt.date.fromisoformat(START_DATE)\n"
            "_end   = _dt.date.fromisoformat(END_DATE)\n"
            "\n"
            "if SYMBOLS is None:\n"
            "    # Default: first 5 IEX split_adjusted symbols on disk — small, fast, real.\n"
            "    _syms = available_symbols(_lake_root, timeframe='1d', vendor='alpaca',\n"
            "                              feed='iex', adjustment='split_adjusted')[:5]\n"
            "else:\n"
            "    _syms = [str(s) for s in SYMBOLS]\n"
            "print(f'universe: {_syms} ({len(_syms)} symbols)')\n"
            "print(f'window:   {_start} -> {_end}')\n"
        )},
        {"type": "code", "source": (
            "# Run both sides + compute parity.\n"
            "from bowaka_v2_lab.parity import run_parity, render_markdown_report\n"
            "\n"
            "_label = RUN_LABEL or _dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')\n"
            "_run_root = Path('research_notebooks/bowaka_v2_lab/artifacts/parity/lab_vs_production') / _label\n"
            "_run_root.mkdir(parents=True, exist_ok=True)\n"
            "print(f'run_root: {_run_root}')\n"
            "\n"
            "report = run_parity(\n"
            "    start_date=_start, end_date=_end,\n"
            "    symbols=_syms,\n"
            "    prod_config_path=Path(PROD_CONFIG_PATH),\n"
            "    lab_config_path=Path(LAB_CONFIG_PATH),\n"
            "    lake_root=_lake_root,\n"
            "    cost_stress=COST_STRESS,\n"
            "    run_root=_run_root,\n"
            ")\n"
            "print(f'prod_n_trades={report.prod_n_trades}  lab_n_trades={report.lab_n_trades}')\n"
            "print(f'trade_intersection_rate={report.trade_intersection_rate:.4f}')\n"
            "print(f'fill_price_mae_bps={report.fill_price_mae_bps:.4f}')\n"
            "print(f'passes_audit_thresholds={report.passes_audit_thresholds}')\n"
            "if report.failing_metrics:\n"
            "    print(f'failing metrics: {report.failing_metrics}')\n"
        )},
        {"type": "code", "source": (
            "# Persist the paste-back Markdown.\n"
            "_md_path = _run_root / 'parity_report.md'\n"
            "render_markdown_report(report, output_path=_md_path)\n"
            "print(f'wrote: {_md_path}')\n"
            "print()\n"
            "print(_md_path.read_text(encoding='utf-8'))\n"
        )},
    ])
    write_notebook(nb, HERE / "13_lab_vs_production_parity.ipynb")
    print("Built 13_lab_vs_production_parity.ipynb")


if __name__ == "__main__":
    main()
