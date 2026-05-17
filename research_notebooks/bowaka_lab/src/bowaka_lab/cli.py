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
