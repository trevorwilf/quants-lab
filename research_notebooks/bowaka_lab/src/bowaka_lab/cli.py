"""Bowaka Lab CLI.

Subcommands:

    env-check        Print environment and dependency status.
    smoke            Smoke-test the package; --offline-fixtures runs without network.

Phase >0 phases will register additional subcommands (fetch-assets, replay-prefilter,
backtest, reconcile-paper, report).
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
