"""Bowaka v2 lab CLI.

Sub-commands:

- ``env-check`` — validate environment + config; exit 0 if OK.
- ``smoke``    — run a one-shot smoke (Phase 4 wires this).
- ``run-backtest`` — orchestrator for the comprehensive sim (Phase 4).
- ``build-universe`` — point-in-time universe snapshot (Phase 3).
- ``build-volume-curve`` — per-symbol intraday volume curve (Phase 3).
- ``replay-scanner`` — historical scanner replay (Phase 3).
- ``promotion-gate`` — checklist + bundler (Phase 9).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from .config import BowakaV2Paths, load_config
from .config.models import BowakaV2Config


def _cmd_env_check(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    validated = BowakaV2Config.model_validate(cfg)
    repo_root = Path(__file__).resolve().parents[4]
    paths = BowakaV2Paths.from_config(validated, repo_root=repo_root)
    paths.assert_strategy_isolation()
    issues: list[str] = []
    if not os.environ.get("MONGO_URI"):
        issues.append("MONGO_URI is not set (some loaders will fail)")
    if not os.environ.get("BOWAKA_V2_SOURCE_ROOT"):
        issues.append("BOWAKA_V2_SOURCE_ROOT is not set (Phase 3 parity tests require it)")
    summary = {
        "status": "ok",
        "config_path": str(args.config),
        "strategy_id": validated.strategy_id,
        "feed": validated.market_data.feed,
        "lab_root": str(paths.lab_root),
        "data_root": str(paths.data_root),
        "artifact_root": str(paths.artifact_root),
        "warnings": issues,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _placeholder(name: str) -> "callable[[argparse.Namespace], int]":
    def _runner(args: argparse.Namespace) -> int:  # noqa: ARG001
        print(
            json.dumps(
                {
                    "status": "not_implemented_in_phase_1",
                    "command": name,
                    "note": "this command is wired in a later phase",
                },
                indent=2,
            )
        )
        return 0

    return _runner


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bowaka-v2-lab", description="Bowaka v2 lab CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    env = sub.add_parser("env-check", help="validate config + environment")
    env.add_argument("--config", required=True, help="path to a v2 lab YAML config")
    env.set_defaults(func=_cmd_env_check)

    smoke = sub.add_parser("smoke", help="run a smoke backtest (Phase 4)")
    smoke.add_argument("--config", required=True)
    smoke.set_defaults(func=_placeholder("smoke"))

    bt = sub.add_parser("run-backtest", help="run the comprehensive backtest (Phase 4)")
    bt.add_argument("--config", required=True)
    bt.set_defaults(func=_placeholder("run-backtest"))

    bu = sub.add_parser("build-universe", help="build a PIT universe snapshot (Phase 3)")
    bu.add_argument("--config", required=True)
    bu.set_defaults(func=_placeholder("build-universe"))

    bvc = sub.add_parser("build-volume-curve", help="build per-symbol intraday volume curve (Phase 3)")
    bvc.add_argument("--config", required=True)
    bvc.set_defaults(func=_placeholder("build-volume-curve"))

    rs = sub.add_parser("replay-scanner", help="historical scanner replay (Phase 3)")
    rs.add_argument("--config", required=True)
    rs.set_defaults(func=_placeholder("replay-scanner"))

    pg = sub.add_parser("promotion-gate", help="run promotion checklist + bundler (Phase 9)")
    pg.add_argument("--run-id", required=True)
    pg.set_defaults(func=_placeholder("promotion-gate"))

    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as e:  # surface error with exit 2
        print(json.dumps({"status": "error", "error": str(e), "type": type(e).__name__}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
