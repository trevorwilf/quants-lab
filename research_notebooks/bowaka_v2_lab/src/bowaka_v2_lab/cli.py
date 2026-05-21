"""Bowaka v2 lab CLI.

Sub-commands:

- ``env-check`` — validate environment + config; exit 0 if OK.
- ``smoke``    — run a one-session smoke backtest.
- ``run-backtest`` — run the comprehensive backtest.
- ``build-universe`` — build a point-in-time universe snapshot.
- ``build-volume-curve`` — build the intraday volume curve.
- ``replay-scanner`` — historical scanner replay.

The five commands above are config-driven: with a research config
(``market_data.*_source: alpaca``) they read the shared market-data lake;
with the smoke / fixture config they use deterministic synthetic data.
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


def _cmd_run_backtest(args: argparse.Namespace) -> int:
    from .cli_runners import run_backtest_command

    print(json.dumps(run_backtest_command(args.config, run_dir=args.run_dir), indent=2, default=str))
    return 0


def _cmd_smoke(args: argparse.Namespace) -> int:
    from .cli_runners import run_backtest_command

    print(json.dumps(
        run_backtest_command(args.config, smoke=True, run_dir=args.run_dir), indent=2, default=str
    ))
    return 0


def _cmd_build_universe(args: argparse.Namespace) -> int:
    from .cli_runners import build_universe_command

    print(json.dumps(build_universe_command(args.config, out_path=args.out), indent=2, default=str))
    return 0


def _cmd_build_volume_curve(args: argparse.Namespace) -> int:
    from .cli_runners import build_volume_curve_command

    print(json.dumps(build_volume_curve_command(args.config, out_path=args.out), indent=2, default=str))
    return 0


def _cmd_replay_scanner(args: argparse.Namespace) -> int:
    from .cli_runners import replay_scanner_command

    print(json.dumps(replay_scanner_command(args.config, run_dir=args.run_dir), indent=2, default=str))
    return 0


def _cmd_optuna(args: argparse.Namespace) -> int:
    from .optuna.walkforward_runner import run_walkforward_study

    result = run_walkforward_study(args.config, n_trials=args.n_trials, n_jobs=args.n_jobs)
    print(json.dumps(result, indent=2, default=str))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bowaka-v2-lab", description="Bowaka v2 lab CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    env = sub.add_parser("env-check", help="validate config + environment")
    env.add_argument("--config", required=True, help="path to a v2 lab YAML config")
    env.set_defaults(func=_cmd_env_check)

    smoke = sub.add_parser("smoke", help="run a one-session smoke backtest")
    smoke.add_argument("--config", required=True)
    smoke.add_argument("--run-dir", default=None, help="override the backtest run directory")
    smoke.set_defaults(func=_cmd_smoke)

    bt = sub.add_parser("run-backtest", help="run the comprehensive backtest")
    bt.add_argument("--config", required=True)
    bt.add_argument("--run-dir", default=None, help="override the backtest run directory")
    bt.set_defaults(func=_cmd_run_backtest)

    bu = sub.add_parser("build-universe", help="build a point-in-time universe snapshot")
    bu.add_argument("--config", required=True)
    bu.add_argument("--out", default=None, help="override the snapshot output path")
    bu.set_defaults(func=_cmd_build_universe)

    bvc = sub.add_parser("build-volume-curve", help="build the intraday volume curve")
    bvc.add_argument("--config", required=True)
    bvc.add_argument("--out", default=None, help="override the volume-curve output path")
    bvc.set_defaults(func=_cmd_build_volume_curve)

    rs = sub.add_parser("replay-scanner", help="historical scanner replay")
    rs.add_argument("--config", required=True)
    rs.add_argument("--run-dir", default=None, help="override the replay run directory")
    rs.set_defaults(func=_cmd_replay_scanner)

    opt = sub.add_parser("optuna", help="run a real walk-forward Optuna study against the lake")
    opt.add_argument("--config", required=True)
    opt.add_argument("--n-trials", type=int, default=None, help="override optuna.n_trials")
    opt.add_argument("--n-jobs", type=int, default=None, help="override optuna.n_jobs")
    opt.set_defaults(func=_cmd_optuna)

    pg = sub.add_parser("promotion-gate", help="run promotion checklist + bundler (Phase 9)")
    pg.add_argument("--run-id", required=True)
    pg.add_argument("--artifacts-root", default=None,
                     help="override artifacts/ root; defaults to research_notebooks/bowaka_v2_lab/artifacts")
    pg.set_defaults(func=_cmd_promotion_gate)

    return p


def _cmd_promotion_gate(args: argparse.Namespace) -> int:
    """Run the promotion checklist + bundle, write a verdict JSON, exit 0 iff all P0 checks pass."""
    from .promotion.bundler import bundle_review_package
    from .promotion.checklist import run_all_checklists
    from .promotion.suitability import decide_suitability

    repo_root = Path(__file__).resolve().parents[4]
    artifacts_root = Path(args.artifacts_root) if args.artifacts_root else (
        repo_root / "research_notebooks" / "bowaka_v2_lab" / "artifacts"
    )
    run_dir = artifacts_root / "runs" / args.run_id
    if not run_dir.is_dir():
        print(json.dumps({"status": "error", "error": f"run_dir not found: {run_dir}"}), file=sys.stderr)
        return 2

    results = run_all_checklists(run_dir)
    tier = decide_suitability(run_dir, results)
    # Bundle, tolerating optional artifacts.
    promotion_root = artifacts_root / "promotion"
    try:
        bundle_dir = bundle_review_package(
            source_run_dir=run_dir,
            promotion_root=promotion_root,
            run_id=args.run_id,
        )
        bundle_status = "ok"
    except FileNotFoundError as e:
        bundle_dir = None
        bundle_status = f"failed: {e}"

    # P0 = every checklist item must be "pass" (no fail/unknown).
    p0_failures = [k for k, (s, _) in results.items() if s != "pass"]
    out = {
        "run_id": args.run_id,
        "run_dir": str(run_dir),
        "tier": tier,
        "p0_failures": p0_failures,
        "p0_passed": len(p0_failures) == 0,
        "bundle_dir": str(bundle_dir) if bundle_dir else None,
        "bundle_status": bundle_status,
        "checklist_results": {k: {"status": s, "evidence": ev} for k, (s, ev) in results.items()},
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if (out["p0_passed"] and bundle_status == "ok") else 1


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
