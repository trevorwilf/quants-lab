"""Build all Phase 5 / 6 / 7 notebooks.

Run from the lab root:
    python notebooks/_build_all.py
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _notebook_common import make_notebook, write_notebook  # noqa: E402


HERE = Path(__file__).resolve().parent


def _papermill_param_cell() -> dict:
    return {
        "type": "code",
        "source": (
            "# Papermill parameter cell.\n"
            "CONFIG_PATH = 'research_notebooks/bowaka_v2_lab/configs/bowaka_v2_backtest_smoke.yml'\n"
        ),
    }


def _build(name: str, body_cells: list[dict]) -> None:
    nb = make_notebook([_papermill_param_cell(), *body_cells])
    write_notebook(nb, HERE / name)


def main() -> None:
    _build(
        "01_shared_data_inventory.ipynb",
        [
            {"type": "markdown", "source": "# 01 — Shared Data Inventory\n\nLists fixtures present under `data/fixtures/`."},
            {"type": "code", "source": (
                "from pathlib import Path\n"
                "from bowaka_v2_lab.config import load_config, BowakaV2Paths\n"
                "from bowaka_v2_lab.config.models import BowakaV2Config\n"
                "cfg = load_config(CONFIG_PATH)\n"
                "validated = BowakaV2Config.model_validate(cfg)\n"
                "paths = BowakaV2Paths.from_config(validated, repo_root=Path('.').resolve())\n"
                "fix_root = Path(paths.data_root) / 'fixtures'\n"
                "files = sorted(p.relative_to(fix_root) for p in fix_root.rglob('*.parquet')) if fix_root.is_dir() else []\n"
                "print(f'fixtures found: {len(files)}')\n"
                "for f in files[:20]:\n    print(' ', f)\n"
            )},
        ],
    )
    _build(
        "02_universe_backfill_and_snapshot.ipynb",
        [
            {"type": "markdown", "source": "# 02 — Universe Backfill & PIT Snapshot"},
            {"type": "code", "source": (
                "import datetime as _dt\n"
                "import pandas as pd\n"
                "from bowaka_v2_lab.config import load_config\n"
                "from bowaka_v2_lab.scanner.universe_builder import build_universe_snapshot\n"
                "cfg = load_config(CONFIG_PATH)\n"
                "asset_master = pd.DataFrame([{'symbol': s, 'exchange': 'NASDAQ', 'venue_code': 'XNAS',\n"
                "  'instrument_class': 'operating_equity', 'eligible_for_bowaka_equity_bucket': True}\n"
                "  for s in (cfg.get('universe', {}).get('symbols') or ['AAA','BBB'])])\n"
                "baselines = pd.DataFrame([{'symbol': s, 'prior_close': 100.0, 'avg_dollar_volume_20d': 5_000_000}\n"
                "  for s in (cfg.get('universe', {}).get('symbols') or ['AAA','BBB'])])\n"
                "snap = build_universe_snapshot(asset_master=asset_master, daily_baselines=baselines, cfg=cfg,\n"
                "  session_date=_dt.date.today())\n"
                "print('universe size:', len(snap['symbols']))\n"
            )},
        ],
    )
    _build(
        "03_volume_curve_build.ipynb",
        [
            {"type": "markdown", "source": "# 03 — Volume Curve Build"},
            {"type": "code", "source": (
                "from bowaka_v2_lab.features.volume_curve import synthesize_default_curve, adv_bucket\n"
                "curve = synthesize_default_curve()\n"
                "print(curve.head())\n"
                "print('size:', len(curve))\n"
            )},
        ],
    )
    _build(
        "04_intraday_event_replay.ipynb",
        [
            {"type": "markdown", "source": "# 04 — Intraday Event Replay"},
            {"type": "code", "source": (
                "import datetime as _dt\n"
                "import pandas as pd\n"
                "from pathlib import Path\n"
                "from bowaka_v2_lab.config import load_config\n"
                "from bowaka_v2_lab.scanner.replay import replay_scanner\n"
                "from bowaka_v2_lab.sim.replay_fixtures import synthetic_universe, synthetic_daily_cache\n"
                "cfg = load_config(CONFIG_PATH)\n"
                "syms = cfg.get('universe', {}).get('symbols') or ['AAA','BBB','CCC']\n"
                "universe = synthetic_universe(syms)\n"
                "daily_cache = synthetic_daily_cache(syms)\n"
                "scan_ts = [pd.Timestamp('2024-09-04 14:00:00', tz='UTC')]\n"
                "def supplier(sym, ts):\n"
                "    # Minimal fixture bars.\n"
                "    rows = []\n"
                "    for i in range(30):\n"
                "        rows.append({'timestamp': pd.Timestamp('2024-09-04 13:30:00', tz='UTC') + pd.Timedelta(minutes=i),\n"
                "                      'open': 100+i*0.1, 'high': 100+i*0.2, 'low': 99.5, 'close': 100+i*0.15, 'volume': 1000.0})\n"
                "    return pd.DataFrame(rows)\n"
                "run_dir = Path('artifacts/runs/replay_nb_smoke')\n"
                "summary = replay_scanner(cfg=cfg, universe_snapshot=universe, daily_cache=daily_cache,\n"
                "  volume_curve=None, scan_timestamps=scan_ts, bars_supplier=supplier, run_dir=run_dir)\n"
                "print(summary)\n"
            )},
        ],
    )
    _build(
        "05_single_config_backtest.ipynb",
        [
            {"type": "markdown", "source": "# 05 — Single Config Backtest"},
            {"type": "code", "source": (
                "import datetime as _dt\n"
                "import pandas as pd\n"
                "from pathlib import Path\n"
                "from bowaka_v2_lab.config import load_config, BowakaV2Paths\n"
                "from bowaka_v2_lab.config.models import BowakaV2Config\n"
                "from bowaka_v2_lab.sim.backtester import run_backtest\n"
                "from bowaka_v2_lab.sim.replay_fixtures import synthetic_universe, synthetic_daily_cache\n"
                "cfg = load_config(CONFIG_PATH)\n"
                "validated = BowakaV2Config.model_validate(cfg)\n"
                "paths = BowakaV2Paths.from_config(validated, repo_root=Path('.').resolve())\n"
                "sessions = [_dt.date(2024, 9, 4)]\n"
                "syms = cfg.get('universe', {}).get('symbols') or ['AAA','BBB','CCC']\n"
                "universe = {sessions[0]: synthetic_universe(syms)}\n"
                "daily_cache = {sessions[0]: synthetic_daily_cache(syms)}\n"
                "def minute_supplier(sym, ts):\n"
                "    rows = []\n"
                "    for i in range(30):\n"
                "        rows.append({'timestamp': pd.Timestamp('2024-09-04 13:30:00', tz='UTC') + pd.Timedelta(minutes=i),\n"
                "                      'open': 100+i*0.1, 'high': 100+i*0.2, 'low': 99.5, 'close': 100+i*0.15, 'volume': 5000.0})\n"
                "    return pd.DataFrame(rows)\n"
                "def daily_supplier(sym, d):\n"
                "    return pd.DataFrame([{'symbol': sym, 'session_date': d, 'open': 100.0, 'high': 110.0, 'low': 98.0, 'close': 108.0, 'volume': 100000}])\n"
                "result = run_backtest(cfg=cfg, sessions=sessions,\n"
                "  scan_times_per_session=lambda d: [pd.Timestamp(f'{d}T14:00:00', tz='UTC')],\n"
                "  universe_snapshot_by_session=universe, daily_cache_by_session=daily_cache,\n"
                "  minute_bars_supplier=minute_supplier, daily_bars_supplier=daily_supplier,\n"
                "  initial_bankroll=10_000.0, paths=paths)\n"
                "print('run_id:', result.run_id)\n"
                "print('run_dir:', result.run_dir)\n"
                "print('summary:', result.summary)\n"
            )},
        ],
    )
    _build(
        "06_execution_cost_and_liquidity_study.ipynb",
        [
            {"type": "markdown", "source": "# 06 — Execution Cost & Liquidity Study"},
            {"type": "code", "source": (
                "from bowaka_v2_lab.sim.cost_model import COST_STRESS_LEVELS, slippage_bps\n"
                "for lvl in COST_STRESS_LEVELS:\n"
                "    s = slippage_bps(stress_level=lvl, adv_participation_frac=0.01)\n"
                "    print(f'{lvl}: {s:.2f} bps')\n"
            )},
        ],
    )
    _build(
        "07_ablation_and_delay_sensitivity.ipynb",
        [
            {"type": "markdown", "source": "# 07 — Ablation & Delay Sensitivity"},
            {"type": "code", "source": (
                "from bowaka_v2_lab.reports.delay_sensitivity import delay_sensitivity_grid, standard_delays\n"
                "summaries = {d: {'n_trades': d, 'win_rate': 0.5, 'total_pnl': 100.0*d, 'net_return_pct': 0.01*d}\n"
                "              for d in standard_delays()}\n"
                "print(delay_sensitivity_grid(summaries))\n"
            )},
        ],
    )
    _build(
        "08_counterfactual_exits_and_holds.ipynb",
        [
            {"type": "markdown", "source": "# 08 — Counterfactual Exits & Holds"},
            {"type": "code", "source": (
                "from bowaka_v2_lab.research.counterfactuals import run_counterfactual_grid\n"
                "result = run_counterfactual_grid(\n"
                "    base_cfg={'exits': {'stop_loss_pct': 0.02, 'take_profit_pct': 0.05, 'max_hold_days': 3}},\n"
                "    exit_variants=[{'max_hold_days': 1}, {'max_hold_days': 5}, {'take_profit_pct': 0.10}],\n"
                "    backtest_runner=lambda cfg: {'n_trades': 5, 'win_rate': 0.4, 'net_return_pct': 0.005},\n"
                ")\n"
                "print(result)\n"
            )},
        ],
    )
    _build(
        "11_weekly_research_report.ipynb",
        [
            {"type": "markdown", "source": "# 11 — Weekly Research Report"},
            {"type": "code", "source": (
                "import datetime as _dt\n"
                "import pandas as pd\n"
                "from pathlib import Path\n"
                "from bowaka_v2_lab.config import load_config, BowakaV2Paths\n"
                "from bowaka_v2_lab.config.models import BowakaV2Config\n"
                "from bowaka_v2_lab.sim.backtester import run_backtest\n"
                "from bowaka_v2_lab.sim.replay_fixtures import synthetic_universe, synthetic_daily_cache\n"
                "from bowaka_v2_lab.reports.render_run_report import render_run_report\n"
                "cfg = load_config(CONFIG_PATH)\n"
                "validated = BowakaV2Config.model_validate(cfg)\n"
                "paths = BowakaV2Paths.from_config(validated, repo_root=Path('.').resolve())\n"
                "sessions = [_dt.date(2024, 9, 4)]\n"
                "syms = ['AAA']\n"
                "universe = {sessions[0]: synthetic_universe(syms)}\n"
                "daily_cache = {sessions[0]: synthetic_daily_cache(syms)}\n"
                "def minute_supplier(sym, ts):\n"
                "    rows = []\n"
                "    for i in range(30):\n"
                "        rows.append({'timestamp': pd.Timestamp('2024-09-04 13:30:00', tz='UTC') + pd.Timedelta(minutes=i),\n"
                "                      'open': 100, 'high': 101, 'low': 99, 'close': 100.5, 'volume': 5000.0})\n"
                "    return pd.DataFrame(rows)\n"
                "def daily_supplier(sym, d):\n"
                "    return pd.DataFrame([{'symbol': sym, 'session_date': d, 'open': 100.0, 'high': 110.0, 'low': 98.0, 'close': 108.0, 'volume': 100000}])\n"
                "result = run_backtest(cfg=cfg, sessions=sessions,\n"
                "  scan_times_per_session=lambda d: [pd.Timestamp(f'{d}T14:00:00', tz='UTC')],\n"
                "  universe_snapshot_by_session=universe, daily_cache_by_session=daily_cache,\n"
                "  minute_bars_supplier=minute_supplier, daily_bars_supplier=daily_supplier,\n"
                "  initial_bankroll=10_000.0, paths=paths)\n"
                "report_md = render_run_report(result.run_dir, suitability='backtesting_only')\n"
                "(result.run_dir / 'report.md').write_text(report_md, encoding='utf-8')\n"
                "print('report contains suitability:', 'suitability' in report_md.lower())\n"
                "print(report_md[:500])\n"
            )},
        ],
    )


if __name__ == "__main__":
    main()
    print('Built all Phase 5 notebooks.')
