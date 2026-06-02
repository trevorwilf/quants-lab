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
            "# Universe selection. Default mirrors what bowaka_v2 actually does live:\n"
            "# build the PIT universe via the lab config's universe: criteria, screen\n"
            "# to eligible_for_bowaka_equity_bucket, then monitor those symbols on\n"
            "# both sides. Set SYMBOLS=[list] to override (debugging / unit-style runs);\n"
            "# set MAX_UNIVERSE_SIZE=N to cap the screened result for fast smoke tests.\n"
            "SYMBOLS = None\n"
            "MAX_UNIVERSE_SIZE = None\n"
            "PROD_CONFIG_PATH = 'research_notebooks/bowaka_v2_lab/reference/source_strategy/scripts/bowaka_v2_config.yaml'\n"
            "LAB_CONFIG_PATH  = 'research_notebooks/bowaka_v2_lab/configs/bowaka_v2_actual_iex_current_code.yml'\n"
            "LAKE_ROOT  = None              # default = bowaka_common.resolve_market_data_root()\n"
            "COST_STRESS = 'base'           # passed to both sides identically; matches prod default\n"
            "RUN_LABEL  = None              # default = UTC timestamp folder name\n"
            "TIMEOUT_SEC = 1800             # production subprocess timeout (seconds, per session in chunked mode)\n"
            "CHUNK_PER_SESSION = True       # True: per-session timing prints; False: single subprocess, canonical numerics\n"
            "PARALLEL_WORKERS = 1           # >1: run session blocks across N worker subprocesses (implies chunked; identical output; capped at 16)\n"
        )},
        {"type": "markdown", "source": (
            "# 13 — Production-vs-Lab Parity\n\n"
            "Empirical agreement between the production-side backtester\n"
            "(`reference/source_strategy/scripts/bowaka_v2_backtest.py`) and the lab's\n"
            "in-process backtester over a chosen window. Audit §14.5 thresholds drive\n"
            "the stop-ship verdict; failing rows point at a specific divergence class.\n\n"
            "**Mirrors what bowaka_v2 actually does live.** Universe screening runs first:\n"
            "the lab's `build_pit_universe_for_sessions` resolves the PIT universe for\n"
            "each session in the window, then `eligible_symbols(...)` reduces to the\n"
            "survivors of the bowaka equity-bucket screen. With `CHUNK_PER_SESSION=True`\n"
            "(default), EACH session's prod + lab are pointed at THAT session's eligible\n"
            "survivors (one symbols file per session) — matching the live\n"
            "screen-per-session flow and the lab's per-session PIT intersection (Phase 0\n"
            "universe symmetry). The legacy window-union is available via\n"
            "`per_session_universe=False`.\n\n"
            "Override knobs: `SYMBOLS=[...]` to pass an explicit list (debugging);\n"
            "`MAX_UNIVERSE_SIZE=N` to cap the screened universe to N symbols (fast smoke).\n\n"
            "**Progress visibility.** With `CHUNK_PER_SESSION=True` (default) the runner\n"
            "iterates session-by-session and prints `[i/N] DATE prod=Xs lab=Ys avg=... eta=...`\n"
            "after each session, so you can see it's not hung. Trade-off: each lab session\n"
            "starts at `initial_bankroll` (no carry-forward equity), so sizing-dependent\n"
            "trade quantities can differ from the full-window run. Trade counts, entry/exit\n"
            "times, and exit reasons are unaffected. For canonical numerics on a chosen\n"
            "window, flip to `CHUNK_PER_SESSION=False`.\n\n"
            "**Parallel sessions.** Set `PARALLEL_WORKERS=N` (>1) to run contiguous\n"
            "session blocks across N worker subprocesses — **identical output**, faster\n"
            "wall-clock on long multi-session windows (each worker warms its caches\n"
            "once). Capped at 16 (the parity path opens no PostgreSQL connection); it\n"
            "implies chunked mode.\n\n"
            "**Requires Phase 0's fix landed** — pre-fix the production side always read\n"
            "deterministic synthetic data and the parity metrics are meaningless."
        )},
        {"type": "code", "source": (
            "# Resolve lake root + bowaka-v2 universe screen.\n"
            "import datetime as _dt\n"
            "from pathlib import Path\n"
            "\n"
            "from bowaka_common.marketdata.store import resolve_market_data_root\n"
            "from bowaka_v2_lab.parity import build_parity_universe\n"
            "\n"
            "_lake_root = Path(LAKE_ROOT).resolve() if LAKE_ROOT else resolve_market_data_root(None, create=False)\n"
            "print(f'lake_root: {_lake_root}')\n"
            "\n"
            "_start = _dt.date.fromisoformat(START_DATE)\n"
            "_end   = _dt.date.fromisoformat(END_DATE)\n"
            "\n"
            "if SYMBOLS is not None:\n"
            "    _syms = [str(s) for s in SYMBOLS]\n"
            "    _src  = 'explicit'\n"
            "else:\n"
            "    _syms = build_parity_universe(\n"
            "        start_date=_start, end_date=_end,\n"
            "        lab_config_path=Path(LAB_CONFIG_PATH),\n"
            "        lake_root=_lake_root,\n"
            "        max_universe_size=MAX_UNIVERSE_SIZE,\n"
            "    )\n"
            "    _src = ('pit_screen_capped' if MAX_UNIVERSE_SIZE else 'pit_screen')\n"
            "if not _syms:\n"
            "    raise RuntimeError('parity universe is empty after screening — check the window and lab config')\n"
            "print(f'universe ({_src}): {len(_syms)} symbols; head={_syms[:5]} tail={_syms[-5:]}')\n"
            "print(f'window:   {_start} -> {_end}')\n"
        )},
        {"type": "code", "source": (
            "# Pre-flight workload estimate. Lets you cancel a run that's about to\n"
            "# eat hours before kicking off both subprocesses.\n"
            "import exchange_calendars as _xcals\n"
            "import pandas as _pd\n"
            "\n"
            "_cal = _xcals.get_calendar('XNYS')\n"
            "_sessions = [_pd.Timestamp(s).date() for s in _cal.sessions_in_range(\n"
            "    _pd.Timestamp(_start), _pd.Timestamp(_end))] or [_start]\n"
            "_n_symdays = len(_syms) * len(_sessions)\n"
            "print(f'sessions:      {len(_sessions)} XNYS days')\n"
            "print(f'symbols:       {len(_syms)} ({_src})')\n"
            "print(f'symbol-days:   {_n_symdays:,}  (prod + lab each scan this many)')\n"
            "print(f'timeout:       {TIMEOUT_SEC}s per side')\n"
            "if _n_symdays > 5_000:\n"
            "    print()\n"
            "    print(f'WARNING: {_n_symdays:,} symbol-days is a real-universe parity run.')\n"
            "    print(f'  - first runs: set MAX_UNIVERSE_SIZE=30 (cap to 30 syms) or pin SYMBOLS=[...].')\n"
            "    print(f'  - real runs:  expect minutes to ~1 hour; bump TIMEOUT_SEC if needed.')\n"
            "    print(f'  - progress:   tail -f <run_root>/production/production.stderr.log')\n"
        )},
        {"type": "code", "source": (
            "# Run both sides + compute parity.\n"
            "from bowaka_v2_lab.parity import run_parity, render_markdown_report\n"
            "\n"
            "_label = RUN_LABEL or _dt.datetime.now(_dt.UTC).strftime('%Y%m%dT%H%M%SZ')\n"
            "_run_root = Path('research_notebooks/bowaka_v2_lab/artifacts/parity/lab_vs_production') / _label\n"
            "_run_root.mkdir(parents=True, exist_ok=True)\n"
            "print(f'run_root:      {_run_root}')\n"
            "print(f'progress log:  {_run_root}/production/production.stderr.log')\n"
            "\n"
            "report = run_parity(\n"
            "    start_date=_start, end_date=_end,\n"
            "    symbols=_syms,\n"
            "    prod_config_path=Path(PROD_CONFIG_PATH),\n"
            "    lab_config_path=Path(LAB_CONFIG_PATH),\n"
            "    lake_root=_lake_root,\n"
            "    cost_stress=COST_STRESS,\n"
            "    run_root=_run_root,\n"
            "    timeout_sec=int(TIMEOUT_SEC),\n"
            "    chunk_per_session=bool(CHUNK_PER_SESSION) or int(PARALLEL_WORKERS) > 1,\n"
            "    parallel_workers=int(PARALLEL_WORKERS),\n"
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
