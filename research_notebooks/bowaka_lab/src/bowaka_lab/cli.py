"""Bowaka Lab CLI.

Subcommands:

    env-check          Print environment and dependency status.
    smoke              Smoke-test the package; --offline-fixtures runs without network.
    fetch-assets       Fetch the current Alpaca asset universe; persist snapshot.
    fetch-daily-bars   Fetch daily bars for universe and write Parquet + audit.

Phase >2 phases will register additional subcommands (replay-prefilter, backtest,
reconcile-paper, report).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Callable

import bowaka_lab


_SUBCOMMANDS: dict[str, Callable[[argparse.Namespace], int]] = {}


def _register(name: str):
    def deco(func: Callable[[argparse.Namespace], int]) -> Callable[[argparse.Namespace], int]:
        _SUBCOMMANDS[name] = func
        return func

    return deco


@_register("env-check")
def env_check(args: argparse.Namespace) -> int:
    info = {
        "bowaka_lab_version": bowaka_lab.__version__,
        "python_version": sys.version.split()[0],
        "mongo_uri_set": bool(os.environ.get("MONGO_URI")),
        "alpaca_key_set": bool(os.environ.get("ALPACA_API_KEY_ID")),
        "bowaka_source_strategy_root_set": bool(os.environ.get("BOWAKA_SOURCE_STRATEGY_ROOT")),
        "bowaka_paper_logs_root_set": bool(os.environ.get("BOWAKA_PAPER_LOGS_ROOT")),
    }
    print(json.dumps(info, indent=2))
    return 0


@_register("smoke")
def smoke(args: argparse.Namespace) -> int:
    if not args.offline_fixtures:
        print("smoke: only --offline-fixtures mode is supported in Phase 0", file=sys.stderr)
        return 2
    result = {
        "status": "ok",
        "bowaka_lab_version": bowaka_lab.__version__,
        "mode": "offline_fixtures",
    }
    print(json.dumps(result, indent=2))
    return 0


@_register("fetch-assets")
def fetch_assets(args: argparse.Namespace) -> int:
    from bowaka_lab.config.loader import load_config_file
    from bowaka_lab.data.alpaca_client import AlpacaClient
    from bowaka_lab.data.assets import assets_to_dataframe, build_asset_snapshot

    cfg = load_config_file(args.config)
    client = AlpacaClient()
    try:
        from alpaca.trading.requests import GetAssetsRequest

        raw = client.call(client.trading().get_all_assets, GetAssetsRequest(status="active"))
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2), file=sys.stderr)
        return 1

    metadata, rows = build_asset_snapshot(raw, allowed_exchanges=cfg.universe.allowed_exchanges)
    df = assets_to_dataframe(rows)
    print(
        json.dumps(
            {"status": "ok", "snapshot_id": metadata["snapshot_id"], "asset_count": metadata["asset_count"]},
            indent=2,
        )
    )
    if args.output:
        df.to_parquet(args.output, index=False)
    return 0


@_register("fetch-daily-bars")
def fetch_daily_bars_cmd(args: argparse.Namespace) -> int:
    from bowaka_lab.config.loader import load_config_file
    from bowaka_lab.data.alpaca_client import AlpacaClient
    from bowaka_lab.data.bars import fetch_daily_bars

    cfg = load_config_file(args.config)
    symbols = args.symbols.split(",") if args.symbols else []
    client = AlpacaClient()
    df = fetch_daily_bars(
        client,
        symbols=symbols,
        start=cfg.data.start_date,
        end=cfg.data.end_date,
    )
    print(json.dumps({"status": "ok", "rows": int(df.shape[0]), "symbols": len(symbols)}, indent=2))
    if args.output:
        df.to_parquet(args.output, index=False)
    return 0


@_register("backtest")
def backtest_cmd(args: argparse.Namespace) -> int:
    import pandas as pd

    from bowaka_lab.config.loader import load_config_file
    from bowaka_lab.sim.portfolio_engine import BowakaPortfolioBacktester

    cfg = load_config_file(args.config)
    candidates_all = pd.read_parquet(args.candidates)
    minute_bars_all = pd.read_parquet(args.minute_bars)

    def candidate_source(signal_date):
        return candidates_all[candidates_all["signal_date"] == signal_date].copy()

    def minute_bars_for(trade_date, symbols):
        df = minute_bars_all[
            (minute_bars_all["session_date"] == trade_date) & (minute_bars_all["symbol"].isin(symbols))
        ]
        return df.copy()

    runner = BowakaPortfolioBacktester(
        cfg, candidate_source=candidate_source, minute_bars_for=minute_bars_for
    )
    result = runner.run()
    trades_df = result.trades_df()
    print(json.dumps({"status": "ok", "trade_count": int(trades_df.shape[0])}, indent=2))
    if args.output:
        trades_df.to_parquet(args.output, index=False)
    return 0


@_register("report")
def report_cmd(args: argparse.Namespace) -> int:
    from pathlib import Path

    import pandas as pd

    from bowaka_lab.reports.markdown import ReportInputs
    from bowaka_lab.reports.weekly_report import generate_weekly_report

    trades = pd.read_parquet(args.trades) if args.trades else pd.DataFrame()
    counterfactuals = pd.read_parquet(args.counterfactuals) if args.counterfactuals else pd.DataFrame()
    reconciliation = pd.read_csv(args.reconciliation) if args.reconciliation else None

    inputs = ReportInputs(
        run_id=args.run_id,
        config_hash="sha256:unknown",
        trades=trades,
        counterfactuals=counterfactuals,
        reconciliation=reconciliation,
    )
    res = generate_weekly_report(output_dir=Path(args.output_dir), inputs=inputs)
    print(json.dumps({"status": "ok", "markdown_path": str(res.markdown_path), "summary_path": str(res.summary_path)}, indent=2))
    return 0


@_register("reconcile-paper")
def reconcile_paper_cmd(args: argparse.Namespace) -> int:
    from pathlib import Path

    import pandas as pd

    from bowaka_lab.reconcile.paper_log_importer import load_daily_summary
    from bowaka_lab.reconcile.replay_comparator import reconcile

    paper_root = Path(args.paper_root)
    summary = load_daily_summary(paper_root / "daily_summary.jsonl").df
    bt = pd.read_parquet(args.backtest_trades)
    if not summary.empty:
        paper_trades = summary.copy()
        if "entry_timestamp" in paper_trades.columns:
            paper_trades = paper_trades.rename(columns={"entry_timestamp": "entry_time"})
        paper_trades = paper_trades.rename(columns={"ticker": "symbol", "link_id": "trade_id"})
        if "session_date" not in paper_trades.columns and "entry_time" in paper_trades.columns:
            paper_trades["session_date"] = pd.to_datetime(paper_trades["entry_time"]).dt.date
    else:
        paper_trades = pd.DataFrame()
    out = reconcile(paper_trades=paper_trades, backtest_trades=bt)
    print(json.dumps({"status": "ok", "rows": int(out.shape[0])}, indent=2))
    if args.output:
        out.to_csv(args.output, index=False)
    return 0


@_register("replay-prefilter")
def replay_prefilter_cmd(args: argparse.Namespace) -> int:
    from datetime import date as _date

    import pandas as pd

    from bowaka_lab.config.loader import load_config_file
    from bowaka_lab.data.calendar import USEquityCalendar
    from bowaka_lab.features.daily_features import compute_daily_features
    from bowaka_lab.features.prefilter import apply_prefilter

    cfg = load_config_file(args.config)
    bars = pd.read_parquet(args.bars)
    signal_date = _date.fromisoformat(args.signal_date)
    cal = USEquityCalendar(cfg.calendar.exchange)
    trade_date = cal.next_session(signal_date)
    features = compute_daily_features(bars, cfg.prefilter, signal_date=signal_date)
    cset = apply_prefilter(
        features,
        cfg.prefilter,
        signal_date=signal_date,
        trade_date=trade_date,
        universe=cfg.universe,
    )
    out = {"status": "ok", **cset.metadata, "candidates_count": int(cset.candidates.shape[0])}
    print(json.dumps(out, indent=2))
    if args.output:
        from pathlib import Path

        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(
                {
                    "signal_date": signal_date.isoformat(),
                    "trade_date": trade_date.isoformat(),
                    "metadata": cset.metadata,
                    "candidates": cset.candidates.reset_index().to_dict(orient="records"),
                },
                default=str,
                indent=2,
            )
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bowaka-lab", description="Bowaka Lab CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("env-check", help="Print environment and dependency status")

    smoke_p = sub.add_parser("smoke", help="Smoke-test the package")
    smoke_p.add_argument(
        "--offline-fixtures",
        action="store_true",
        help="Run smoke without network access (uses bundled fixtures only).",
    )

    fa = sub.add_parser("fetch-assets", help="Fetch Alpaca asset universe snapshot")
    fa.add_argument("--config", required=True, help="Path to YAML config")
    fa.add_argument("--output", help="Optional Parquet output path for the snapshot dataframe")

    fdb = sub.add_parser("fetch-daily-bars", help="Fetch daily bars for explicit symbol list")
    fdb.add_argument("--config", required=True, help="Path to YAML config")
    fdb.add_argument("--symbols", help="Comma-separated list of symbols")
    fdb.add_argument("--output", help="Optional Parquet output path")

    rp = sub.add_parser("replay-prefilter", help="Replay prefilter on a Parquet daily-bar set")
    rp.add_argument("--config", required=True, help="Path to YAML config")
    rp.add_argument("--bars", required=True, help="Path to daily bars parquet file")
    rp.add_argument("--signal-date", required=True, help="ISO date for signal_date")
    rp.add_argument("--output", help="Optional output JSON for candidate set")

    bt = sub.add_parser("backtest", help="Run a fixture-based backtest (smoke)")
    bt.add_argument("--config", required=True, help="Path to YAML config")
    bt.add_argument("--candidates", required=True, help="Parquet file with candidates")
    bt.add_argument("--minute-bars", required=True, help="Parquet file with minute bars")
    bt.add_argument("--output", help="Optional Parquet path for trades")

    rec = sub.add_parser("reconcile-paper", help="Reconcile paper logs against a backtest trade ledger")
    rec.add_argument("--paper-root", required=True, help="Directory containing paper-trading data")
    rec.add_argument("--backtest-trades", required=True, help="Parquet file with backtest trades")
    rec.add_argument("--output", help="Optional CSV path for the reconciliation table")

    rep = sub.add_parser("report", help="Generate a weekly research report")
    rep.add_argument("--run-id", required=True, help="Backtest run identifier")
    rep.add_argument("--trades", help="Parquet file with backtest trades")
    rep.add_argument("--counterfactuals", help="Parquet file with counterfactual outcomes")
    rep.add_argument("--reconciliation", help="CSV file with paper-vs-backtest reconciliation")
    rep.add_argument("--output-dir", required=True, help="Directory to write the report and JSON summary")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = _SUBCOMMANDS.get(args.cmd)
    if handler is None:
        parser.error(f"Unknown subcommand: {args.cmd}")
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
