"""Build the v2 lab notebooks 01-08 and 11.

Run from the lab root:
    python notebooks/_build_all.py

Every notebook is real and config-driven: with a research config
(``market_data.*_source: alpaca``) it reads the shared market-data lake; with the
smoke / fixture config it uses deterministic synthetic data. No smoke stubs.
"""
from __future__ import annotations

from pathlib import Path

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
            {"type": "markdown", "source": "# 01 — Shared Data Inventory\n\nInventories local `data/fixtures/` **and** the shared market-data lake."},
            {"type": "code", "source": (
                "from pathlib import Path\n"
                "from bowaka_v2_lab.config import load_config, BowakaV2Paths\n"
                "from bowaka_v2_lab.config.models import BowakaV2Config\n"
                "from bowaka_common.marketdata import available_symbols, date_coverage, resolve_market_data_root\n"
                "cfg = load_config(CONFIG_PATH)\n"
                "validated = BowakaV2Config.model_validate(cfg)\n"
                "paths = BowakaV2Paths.from_config(validated, repo_root=Path('.').resolve())\n"
                "_feed = cfg.get('market_data', {}).get('feed', 'iex')\n"
                "# --- local fixtures ---\n"
                "fix_root = Path(paths.data_root) / 'fixtures'\n"
                "files = sorted(p.relative_to(fix_root) for p in fix_root.rglob('*.parquet')) if fix_root.is_dir() else []\n"
                "print(f'local fixtures: {len(files)} parquet file(s) under {fix_root}')\n"
                "for f in files[:20]:\n    print('  ', f)\n"
                "# --- shared market-data lake ---\n"
                "lake_root = resolve_market_data_root(cfg.get('market_data', {}).get('shared_root'), create=False)\n"
                "daily_syms = available_symbols(lake_root, timeframe='1d', feed=_feed)\n"
                "minute_syms = available_symbols(lake_root, timeframe='1m', feed=_feed)\n"
                "print(f'shared lake: {lake_root} (feed={_feed})')\n"
                "print(f'  daily-bar symbols:  {len(daily_syms)}')\n"
                "print(f'  minute-bar symbols: {len(minute_syms)}')\n"
                "for sym in daily_syms[:10]:\n"
                "    cov = date_coverage(sym, lake_root, timeframe='1d', feed=_feed)\n"
                "    print(f'    {sym}: ' + (f'{cov[0]} -> {cov[1]}' if cov else '(no coverage)'))\n"
            )},
        ],
    )
    _build(
        "02_universe_backfill_and_snapshot.ipynb",
        [
            {"type": "markdown", "source": "# 02 — Universe Backfill & PIT Snapshot\n\nBuilds a point-in-time universe snapshot. Symbols and price/ADV baselines come from the shared lake (research config) or are synthetic (smoke config)."},
            {"type": "code", "source": (
                "import pandas as pd\n"
                "from bowaka_v2_lab.config import load_config\n"
                "from bowaka_v2_lab.backtest_runner import resolve_symbols, config_sessions, uses_lake\n"
                "from bowaka_v2_lab.scanner.universe_builder import build_universe_snapshot\n"
                "cfg = load_config(CONFIG_PATH)\n"
                "md = cfg.get('market_data', {})\n"
                "session = config_sessions(cfg)[-1]\n"
                "syms = resolve_symbols(cfg)\n"
                "cols = ['symbol', 'prior_close', 'avg_dollar_volume_20d']\n"
                "if uses_lake(cfg):\n"
                "    from bowaka_v2_lab.data.suppliers import build_daily_cache_from_lake\n"
                "    cache = build_daily_cache_from_lake(md.get('shared_root'), syms, session, feed=md.get('feed', 'iex'))\n"
                "    baselines = cache[cols] if not cache.empty else pd.DataFrame(columns=cols)\n"
                "else:\n"
                "    baselines = pd.DataFrame([{'symbol': s, 'prior_close': 100.0,\n"
                "                               'avg_dollar_volume_20d': 5_000_000} for s in syms])\n"
                "asset_master = pd.DataFrame([{'symbol': s, 'exchange': 'NASDAQ', 'venue_code': 'XNAS',\n"
                "  'instrument_class': 'operating_equity', 'eligible_for_bowaka_equity_bucket': True}\n"
                "  for s in syms])\n"
                "snap = build_universe_snapshot(asset_master=asset_master, daily_baselines=baselines,\n"
                "  cfg=cfg, session_date=session)\n"
                "n_pass = len(snap['symbols'])\n"
                "print('session', session, '-', n_pass, 'symbols pass the universe gate',\n"
                "      'of', len(syms), 'candidates')\n"
            )},
        ],
    )
    _build(
        "03_volume_curve_build.ipynb",
        [
            {"type": "markdown", "source": "# 03 — Volume Curve Build\n\nBuilds the intraday volume curve from real lake minute bars (research config) or the synthetic default (smoke config)."},
            {"type": "code", "source": (
                "import pandas as pd\n"
                "from bowaka_v2_lab.config import load_config\n"
                "from bowaka_v2_lab.backtest_runner import resolve_symbols, uses_lake\n"
                "from bowaka_v2_lab.features.volume_curve import build_volume_curve_from_minute_bars, synthesize_default_curve\n"
                "cfg = load_config(CONFIG_PATH)\n"
                "md = cfg.get('market_data', {})\n"
                "bt = cfg.get('backtest', {})\n"
                "if uses_lake(cfg):\n"
                "    from bowaka_common.marketdata import MarketDataStore\n"
                "    store = MarketDataStore(md.get('shared_root'))\n"
                "    syms = resolve_symbols(cfg, cap=25)\n"
                "    start = pd.Timestamp(bt.get('start_date'))\n"
                "    end = pd.Timestamp(bt.get('end_date', bt.get('start_date'))) + pd.Timedelta(days=1)\n"
                "    frames = []\n"
                "    for s in syms:\n"
                "        df = store.minute_bars(s, start, end, feed=md.get('feed', 'iex'))\n"
                "        if not df.empty:\n"
                "            frames.append(df)\n"
                "    if frames:\n"
                "        curve = build_volume_curve_from_minute_bars(pd.concat(frames, ignore_index=True))\n"
                "        source = 'lake minute bars (' + str(len(frames)) + ' symbols)'\n"
                "    else:\n"
                "        curve = synthesize_default_curve()\n"
                "        source = 'synthetic_default (no lake minute bars in range)'\n"
                "else:\n"
                "    curve = synthesize_default_curve()\n"
                "    source = 'synthetic_default (fixture config)'\n"
                "print('volume curve source:', source)\n"
                "print('rows:', len(curve))\n"
                "print(curve.head(10))\n"
            )},
        ],
    )
    _build(
        "04_intraday_event_replay.ipynb",
        [
            {"type": "markdown", "source": "# 04 — Intraday Event Replay\n\nReplays the scanner over a session. Bars and the daily cache come from the shared lake (research config) or are synthetic (smoke config)."},
            {"type": "code", "source": (
                "import pandas as pd\n"
                "from pathlib import Path\n"
                "from bowaka_v2_lab.config import load_config\n"
                "from bowaka_v2_lab.backtest_runner import (resolve_symbols, config_sessions,\n"
                "  resolve_suppliers, resolve_daily_cache)\n"
                "from bowaka_v2_lab.scanner.replay import replay_scanner\n"
                "from bowaka_v2_lab.sim.replay_fixtures import synthetic_universe\n"
                "cfg = load_config(CONFIG_PATH)\n"
                "syms = resolve_symbols(cfg)\n"
                "session = config_sessions(cfg)[0]\n"
                "scan_ts = [pd.Timestamp(str(session) + 'T14:00:00', tz='UTC')]\n"
                "bars_supplier, _ = resolve_suppliers(cfg)\n"
                "daily_cache = resolve_daily_cache(cfg, syms, session)\n"
                "universe = synthetic_universe(syms)\n"
                "run_dir = Path('research_notebooks/bowaka_v2_lab/artifacts/runs') / ('replay_nb_' + str(session))\n"
                "summary = replay_scanner(cfg=cfg, universe_snapshot=universe, daily_cache=daily_cache,\n"
                "  volume_curve=None, scan_timestamps=scan_ts, bars_supplier=bars_supplier, run_dir=run_dir)\n"
                "print('replay session:', session)\n"
                "print(summary)\n"
            )},
        ],
    )
    _build(
        "05_single_config_backtest.ipynb",
        [
            {"type": "markdown", "source": "# 05 — Single Config Backtest\n\nRuns a real backtest over the config's `backtest` window against the shared market-data lake (research config) or synthetic data (smoke config)."},
            {"type": "code", "source": (
                "from bowaka_v2_lab.backtest_runner import run_config_backtest\n"
                "result = run_config_backtest(CONFIG_PATH)\n"
                "print('run_id:', result.run_id)\n"
                "print('run_dir:', result.run_dir)\n"
                "print('summary:', result.summary)\n"
            )},
        ],
    )
    _build(
        "06_execution_cost_and_liquidity_study.ipynb",
        [
            {"type": "markdown", "source": "# 06 — Execution Cost & Liquidity Study\n\nRuns a real backtest, then profiles its entry decisions by ADV bucket, spread bucket, and time of day."},
            {"type": "code", "source": (
                "import pandas as pd\n"
                "from bowaka_v2_lab.backtest_runner import run_config_backtest\n"
                "from bowaka_v2_lab.reports.liquidity_execution import (adv_bucket_distribution,\n"
                "  spread_bucket_distribution, time_of_day_buckets)\n"
                "result = run_config_backtest(CONFIG_PATH)\n"
                "print('backtest summary:', result.summary)\n"
                "dec_path = result.run_dir / 'entry_decisions.parquet'\n"
                "if dec_path.is_file():\n"
                "    decisions = pd.read_parquet(dec_path)\n"
                "    print('entry decisions:', len(decisions))\n"
                "    print('--- ADV-bucket distribution ---')\n"
                "    print(adv_bucket_distribution(decisions))\n"
                "    print('--- spread-bucket distribution ---')\n"
                "    print(spread_bucket_distribution(decisions))\n"
                "    print('--- time-of-day distribution ---')\n"
                "    print(time_of_day_buckets(decisions))\n"
                "else:\n"
                "    print('no entry_decisions.parquet at', dec_path)\n"
            )},
        ],
    )
    _build(
        "07_ablation_and_delay_sensitivity.ipynb",
        [
            {"type": "markdown", "source": "# 07 — Ablation & Delay Sensitivity\n\nRuns a real backtest at each entry-delay setting and tabulates how performance degrades with delay."},
            {"type": "code", "source": (
                "from bowaka_v2_lab.backtest_runner import run_config_backtest\n"
                "from bowaka_v2_lab.reports.delay_sensitivity import delay_sensitivity_grid, standard_delays\n"
                "summaries = {}\n"
                "for d in standard_delays():\n"
                "    result = run_config_backtest(CONFIG_PATH,\n"
                "      param_overrides={'backtest': {'entry_delay_minutes': d}})\n"
                "    summaries[d] = result.summary\n"
                "    print('delay', d, 'min ->', result.summary.get('n_trades'), 'trades')\n"
                "print(delay_sensitivity_grid(summaries))\n"
            )},
        ],
    )
    _build(
        "08_counterfactual_exits_and_holds.ipynb",
        [
            {"type": "markdown", "source": "# 08 — Counterfactual Exits & Holds\n\nKeeps entries fixed and re-runs real backtests with alternative exit / hold parameters to compare outcomes."},
            {"type": "code", "source": (
                "from bowaka_v2_lab.config import load_config\n"
                "from bowaka_v2_lab.backtest_runner import run_config_backtest\n"
                "from bowaka_v2_lab.research.counterfactuals import run_counterfactual_grid\n"
                "base_cfg = load_config(CONFIG_PATH)\n"
                "result = run_counterfactual_grid(\n"
                "    base_cfg=base_cfg,\n"
                "    exit_variants=[{'max_hold_days': 1}, {'max_hold_days': 5}, {'take_profit_pct': 0.10}],\n"
                "    backtest_runner=lambda cfg: run_config_backtest(cfg).summary,\n"
                ")\n"
                "print(result)\n"
            )},
        ],
    )
    _build(
        "11_weekly_research_report.ipynb",
        [
            {"type": "markdown", "source": "# 11 — Weekly Research Report\n\nRuns a real backtest and renders the run report (with suitability tier)."},
            {"type": "code", "source": (
                "from bowaka_v2_lab.backtest_runner import run_config_backtest\n"
                "from bowaka_v2_lab.reports.render_run_report import render_run_report\n"
                "result = run_config_backtest(CONFIG_PATH)\n"
                "report_md = render_run_report(result.run_dir, suitability='backtesting_only')\n"
                "(result.run_dir / 'report.md').write_text(report_md, encoding='utf-8')\n"
                "print('report written to', result.run_dir / 'report.md')\n"
                "print(report_md[:800])\n"
            )},
        ],
    )


if __name__ == "__main__":
    main()
    print("Built notebooks 01-08 and 11.")
