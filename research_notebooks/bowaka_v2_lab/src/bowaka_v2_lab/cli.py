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
- ``config-parity`` — diff a config vs the frozen contract; non-zero exit on an
  undeclared divergence (realism remediation 2 Phase 0).
- ``dq-report`` — run the multi-level data-quality stack for a config; non-zero
  exit when a required check fails for the config's mode (realism remediation 2
  Phase 3).
- ``promotion-gate`` — checklist + bundler (Phase 9).
- ``reconcile`` — paper-vs-lab reconciliation (Phase 10, scaffolding only).
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

    print(json.dumps(
        run_backtest_command(
            args.config, run_dir=args.run_dir,
            allow_smoke=args.allow_smoke_optimization,
            allow_synthetic_universe=args.allow_synthetic_universe,
        ),
        indent=2, default=str,
    ))
    return 0


def _cmd_smoke(args: argparse.Namespace) -> int:
    from .cli_runners import run_backtest_command

    print(json.dumps(
        run_backtest_command(
            args.config, smoke=True, run_dir=args.run_dir,
            allow_synthetic_universe=args.allow_synthetic_universe,
        ),
        indent=2, default=str,
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

    print(json.dumps(
        replay_scanner_command(
            args.config, run_dir=args.run_dir,
            allow_synthetic_universe=args.allow_synthetic_universe,
        ),
        indent=2, default=str,
    ))
    return 0


def _cmd_import_actual_config(args: argparse.Namespace) -> int:
    """Generate a lab config from the frozen contract."""
    from .reference.import_config import import_actual_config

    dest = import_actual_config(
        out_path=args.out,
        feed=args.feed,
        mode=args.mode,
        feed_thresholds=args.feed_thresholds,
        purpose=args.purpose,
    )
    payload = {
        "status": "ok",
        "command": "import-actual-config",
        "out": str(dest),
        "feed": args.feed,
        "mode": args.mode,
        "feed_thresholds": args.feed_thresholds,
        "purpose": args.purpose,
    }
    if args.feed_thresholds == "sip_tightened":
        payload["parity_sidecar"] = str(
            Path(args.out).with_name(f"{Path(args.out).stem}.parity_sidecar.yaml")
        )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_config_parity(args: argparse.Namespace) -> int:
    """Print a config's parity diff vs the frozen contract.

    Exits non-zero if any leaf diverges from the contract without being declared
    in the config's ``<stem>.parity_sidecar.yaml`` (realism remediation 2
    Phase 0). A clean config — or one whose every diff is declared — exits 0.
    """
    from .config.parity_sidecar import classify_config_parity, load_parity_sidecar
    from .reference import contract_available, load_actual_contract

    cfg = load_config(args.config)
    if not contract_available():
        print(json.dumps({
            "status": "error",
            "command": "config-parity",
            "error": "frozen contract unavailable — cannot compute the parity diff",
        }), file=sys.stderr)
        return 2
    sidecar = load_parity_sidecar(args.config)
    result = classify_config_parity(
        {k: v for k, v in cfg.items() if k != "_source_path"},
        load_actual_contract(),
        sidecar=sidecar,
    )
    undeclared = result["undeclared"]
    payload = {
        "status": "ok" if not undeclared else "parity_violation",
        "command": "config-parity",
        "config_path": str(args.config),
        "summary": result["summary"],
        "declared_diffs": result["declared"],
        "undeclared_diffs": undeclared,
        "parity_clean": not undeclared,
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if not undeclared else 1


def _cmd_verify_bayesian_fix(args: argparse.Namespace) -> int:
    """Emit the Bayesian-optimization-fix verification report (audit 2026-05-29
    Phase 3). Exit 0 only when every PASS/FAIL row is PASS."""
    from .devtools.verify_bayesian_fix import main as _vbf_main

    argv = ["--config", args.config, "--n-trials", str(args.n_trials)]
    if args.out:
        argv += ["--out", args.out]
    if getattr(args, "skip_short_run", False):
        argv += ["--skip-short-run"]
    if getattr(args, "checks_only", False):
        argv += ["--checks-only"]
    return int(_vbf_main(argv))


def _cmd_verify_lake(args: argparse.Namespace) -> int:
    """Verify the shared market-data lake's completeness against the realism contract.

    Audit 2026-05-23 §P0-004 / §P0-005 (Phase 1). Reports a structured JSON
    summary of every check and exits non-zero under ``--intended-realism``
    when any required check fails.
    """
    from .data.verify_lake import verify_lake

    if args.lake:
        lake_root = Path(args.lake)
    elif os.environ.get("MARKET_DATA_ROOT"):
        lake_root = Path(os.environ["MARKET_DATA_ROOT"])
    else:
        repo_root = Path(__file__).resolve().parents[4]
        lake_root = repo_root / "research_notebooks" / "market_data"

    result = verify_lake(
        lake_root, feed=args.feed,
        intended_realism=bool(getattr(args, "intended_realism", False)),
    )
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True, default=str))
    if result.intended_realism and not result.passed:
        return 1
    return 0


def _cmd_dq_report(args: argparse.Namespace) -> int:
    """Run the full multi-level data-quality stack for a config.

    Writes ``artifacts/data_quality_report_<config_stem>.json`` and exits
    non-zero when any *required* check fails for the config's
    ``simulation.mode`` (realism remediation 2 Phase 3, audit §P0-010).
    """
    from .cli_runners import dq_report_command

    result = dq_report_command(
        args.config, start=args.start, end=args.end, out_path=args.out
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result.get("required_failure") is None else 1


def _cmd_optuna(args: argparse.Namespace) -> int:
    """Run a walk-forward Optuna study, OR (``--final-holdout``) score the
    untouched holdout once against a chosen parameter set.

    ``--final-holdout`` is the ONLY sanctioned read of the holdout window: the
    study itself never touches it (the HoldoutGuard raises if a tuning fold
    would overlap it). The parameter set is taken from ``--params-json`` or, by
    default, the ``best_params`` of ``--study-results``.
    """
    if getattr(args, "final_holdout", False):
        from .optuna.holdout import _load_params, score_final_holdout

        params = _load_params(
            params_json=args.params_json,
            study_results_json=args.study_results,
        )
        result = score_final_holdout(
            args.config, params,
            allow_smoke=args.allow_smoke_optimization,
            out_path=args.out,
        )
        print(json.dumps(result, indent=2, default=str))
        return 0

    from .optuna.walkforward_runner import run_walkforward_study

    # Realism remediation 2 Phase 8 — Optuna's n_startup_trials IS the random-
    # search baseline (the first N trials are pure random samples before TPE
    # kicks in). The CLI exposes both names for clarity.
    n_startup = args.n_startup_trials
    if n_startup is None and getattr(args, "random_search_trials", None) is not None:
        n_startup = args.random_search_trials

    result = run_walkforward_study(
        args.config, n_trials=args.n_trials, n_jobs=args.n_jobs,
        n_startup_trials=n_startup,
        allow_smoke=args.allow_smoke_optimization,
        allow_current_code_parity_study=getattr(
            args, "allow_current_code_parity_study", False),
        tier=getattr(args, "tier", None),
        incumbent_trial=getattr(args, "incumbent_trial", False),
    )
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
    smoke.add_argument("--allow-synthetic-universe", action="store_true",
                       help="use the synthetic universe (smoke_fixture mode only)")
    smoke.set_defaults(func=_cmd_smoke)

    bt = sub.add_parser("run-backtest", help="run the comprehensive backtest")
    bt.add_argument("--config", required=True)
    bt.add_argument("--run-dir", default=None, help="override the backtest run directory")
    bt.add_argument("--allow-smoke-optimization", action="store_true",
                    help="permit run-backtest on a simulation.mode=smoke_fixture config")
    bt.add_argument("--allow-synthetic-universe", action="store_true",
                    help="use the synthetic universe instead of the point-in-time "
                         "universe; permitted only when simulation.mode=smoke_fixture")
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
    rs.add_argument("--allow-synthetic-universe", action="store_true",
                    help="use the synthetic universe (smoke_fixture mode only)")
    rs.set_defaults(func=_cmd_replay_scanner)

    opt = sub.add_parser(
        "optuna",
        help="run a walk-forward Optuna study, or score the final holdout",
    )
    opt.add_argument("--config", required=True)
    opt.add_argument("--n-trials", type=int, default=None, help="override optuna.n_trials")
    opt.add_argument("--n-jobs", type=int, default=None, help="override optuna.n_jobs")
    opt.add_argument("--n-startup-trials", type=int, default=None,
                     help="override optuna.n_startup_trials (random trials before TPE)")
    opt.add_argument("--allow-smoke-optimization", action="store_true",
                     help="permit walk-forward optimization on a simulation.mode=smoke_fixture config")
    # Realism remediation 2 Phase 8 (audit §P0-011): current_code_parity opt-in.
    opt.add_argument("--allow-current-code-parity-study", action="store_true",
                     help="explicitly opt in to running an Optuna study against a "
                          "simulation.mode=current_code_parity config (paper-"
                          "reconciliation-only; requires --tier research_only)")
    opt.add_argument("--tier", default=None,
                     choices=["research_only", "backtesting_only",
                              "paper_candidate", "live_candidate"],
                     help="declare the study's suitability tier explicitly "
                          "(current_code_parity studies require research_only)")
    opt.add_argument("--incumbent-trial", action="store_true",
                     help="pin trial 0 to the actual-contract parameter set (the "
                          "incumbent baseline) so the optimizer's best is judged "
                          "against the live config")
    opt.add_argument("--random-search-trials", type=int, default=None,
                     help="alias for --n-startup-trials: pure-random trials before "
                          "TPE-guided search begins (Optuna's n_startup_trials)")
    # Phase 9: final-holdout scoring. Scores a chosen parameter set against the
    # untouched holdout window exactly once and records the result.
    opt.add_argument("--final-holdout", action="store_true",
                     help="score the untouched final-holdout window ONCE against a "
                          "fixed parameter set (the only sanctioned holdout read)")
    opt.add_argument("--study-results", default=None,
                     help="path to a study results JSON; --final-holdout scores its "
                          "best_params against the holdout")
    opt.add_argument("--params-json", default=None,
                     help="path to a JSON parameter set for --final-holdout "
                          "(overrides --study-results)")
    opt.add_argument("--out", default=None,
                     help="override the output path for the --final-holdout result JSON")
    opt.set_defaults(func=_cmd_optuna)

    cp = sub.add_parser(
        "config-parity",
        help="diff a config vs the frozen contract; exit non-zero on an "
             "undeclared divergence",
    )
    cp.add_argument("--config", required=True, help="path to a v2 lab YAML config")
    cp.set_defaults(func=_cmd_config_parity)

    dq = sub.add_parser(
        "dq-report",
        help="run the multi-level data-quality stack for a config; exit "
             "non-zero if a required check fails for the config's mode",
    )
    dq.add_argument("--config", required=True, help="path to a v2 lab YAML config")
    dq.add_argument("--start", default=None,
                    help="start date (YYYY-MM-DD); defaults to backtest.start_date")
    dq.add_argument("--end", default=None,
                    help="end date (YYYY-MM-DD); defaults to backtest.end_date")
    dq.add_argument("--out", default=None,
                    help="override the data_quality_report_<stem>.json output path")
    dq.set_defaults(func=_cmd_dq_report)

    iac = sub.add_parser(
        "import-actual-config",
        help="generate a lab config from the frozen contract",
    )
    iac.add_argument("--out", default="configs/bowaka_v2_intended_realism.yml",
                     help="output path for the generated config")
    iac.add_argument("--feed", default="sip", choices=["sip", "iex"],
                     help="market_data.feed for the generated config")
    iac.add_argument("--mode", default="intended_realism",
                     choices=["intended_realism", "current_code_parity"],
                     help="simulation.mode for the generated config")
    iac.add_argument("--feed-thresholds", dest="feed_thresholds", default="actual",
                     choices=["actual", "sip_tightened"],
                     help="signal thresholds: 'actual' copies the contract "
                          "(IEX-relaxed) verbatim; 'sip_tightened' overlays the "
                          "audit's SIP-intended thresholds + writes a parity sidecar")
    iac.add_argument("--purpose", default="backtest",
                     choices=["backtest", "optuna"],
                     help="config purpose: 'backtest' is a one-shot run; 'optuna' "
                          "emits a walk-forward study config (adds optuna: block + "
                          "run.kind: optuna) per realism remediation 2 Phase 8")
    iac.set_defaults(func=_cmd_import_actual_config)

    pg = sub.add_parser("promotion-gate", help="run promotion checklist + bundler (Phase 9)")
    pg.add_argument("--run-id", required=True)
    pg.add_argument("--artifacts-root", default=None,
                     help="override artifacts/ root; defaults to research_notebooks/bowaka_v2_lab/artifacts")
    pg.set_defaults(func=_cmd_promotion_gate)

    # Audit 2026-05-23 §P0-004 / §P0-005 (Phase 1) — verify lake completeness.
    vl = sub.add_parser(
        "verify-lake",
        help="check the shared market-data lake for required partitions; "
             "exit non-zero under --intended-realism when a required check fails",
    )
    vl.add_argument(
        "--lake",
        default=None,
        help="lake root; defaults to $MARKET_DATA_ROOT or the in-repo lake",
    )
    vl.add_argument("--feed", default="iex", choices=["iex", "sip"],
                    help="feed under which the bars / quotes are partitioned")
    vl.add_argument("--intended-realism", action="store_true",
                    help="fail closed when any required check fails (the realism "
                         "contract requires bars + quotes + statuses + corporate "
                         "actions + asset snapshots + non-raw adjustment)")
    vl.set_defaults(func=_cmd_verify_lake)

    # Audit 2026-05-29 Appendix B + F (Phase 3) — Bayesian-fix verification report.
    vbf = sub.add_parser(
        "verify-bayesian-fix",
        help="emit the operator-pasteable Bayesian-optimization-fix verification "
             "report (PASS/FAIL grid for each P0 finding); exit non-zero on any FAIL",
    )
    vbf.add_argument(
        "--config",
        default="configs/bowaka_v2_actual_iex_current_code_optuna.workstation.yml",
    )
    vbf.add_argument("--n-trials", type=int, default=3)
    vbf.add_argument("--out", default=None)
    vbf.add_argument("--skip-short-run", action="store_true",
                     help="skip Section 7 (the 3-trial study short-run)")
    vbf.add_argument("--checks-only", action="store_true",
                     help="run only the fast direct checks; skip the test-backed "
                          "sections (Section 4, Section 1 row 3, Section 5 "
                          "sentinel/manifest, Section 8)")
    vbf.set_defaults(func=_cmd_verify_bayesian_fix)

    rec = sub.add_parser(
        "reconcile",
        help="paper-vs-lab reconciliation (Phase 10 — scaffolding only)",
    )
    rec.add_argument("--paper-logs-root", default=None,
                     help="directory of paper-trading session logs; falls back to "
                          "$BOWAKA_V2_PAPER_LOGS_ROOT, then reconcile.paper_logs_root "
                          "in --config. Absent everywhere -> a scaffolding-only "
                          "report is written and the command exits 0.")
    rec.add_argument("--session-date", required=True,
                     help="the paper trading session to reconcile (YYYY-MM-DD)")
    rec.add_argument("--config", default=None,
                     help="v2 lab config; the lab is replayed in current_code_parity "
                          "mode. Required to run a real reconciliation.")
    rec.add_argument("--out", default=None,
                     help="output directory for reconciliation_report.{md,json}")
    rec.set_defaults(func=_cmd_reconcile)

    # Speedup report §6.4 / matrix doc §12 — scan-matrix builder + verifier.
    sm = sub.add_parser(
        "scan-matrix",
        help="Build / verify the precomputed scan feature matrix (Phase 8).",
    )
    sm_sub = sm.add_subparsers(dest="scan_matrix_cmd", required=True)
    smb = sm_sub.add_parser("build", help="Build the per-session matrix partitions.")
    smb.add_argument("--config", required=True)
    smb.add_argument("--scope", choices=["validation", "holdout", "full_history"],
                     default="validation")
    smb.add_argument("--workers", type=int, default=8)
    smb.add_argument("--reserve-system-gib", type=float, default=32.0)
    smb.add_argument("--max-optuna-workers", type=int, default=8)
    smb.add_argument("--store-root", default=None)
    smb.set_defaults(func=_cmd_scan_matrix_build)

    smv = sm_sub.add_parser("verify", help="Spot-check a built matrix against legacy features.")
    smv.add_argument("--store-root", required=True)
    smv.add_argument("--config", required=True)
    smv.add_argument("--sample-count", type=int, default=10)
    smv.add_argument(
        "--vectorized-check", action="store_true",
        help="Also run the Phase 4 vectorized-vs-scalar score spot check; on "
             "success the parity_proof marker records verifier_version=2 "
             "(required to enable runtime_mode='vectorized').",
    )
    smv.set_defaults(func=_cmd_scan_matrix_verify)

    # Speedup report v2 §1.4 / §8.3 / §9 / Phase 5 — finalist evaluation CLI.
    ef = sub.add_parser(
        "evaluate-finalists",
        help="Run the Stage B finalist evaluation pipeline on a finished study.",
    )
    ef.add_argument("--study-dir", required=True,
                    help="Artifact directory containing <study_name>.json")
    ef.add_argument("--config", required=True,
                    help="Config carrying the finalist_evaluation: block")
    ef.add_argument("--output", required=True,
                    help="Directory for finalist_report.json")
    ef.set_defaults(func=_cmd_evaluate_finalists)

    return p


def _cmd_scan_matrix_build(args: argparse.Namespace) -> int:
    """Build the scan matrix per matrix doc §12 phase 1."""
    from .scanner.scan_matrix import build_scan_matrix

    store_root = Path(args.store_root) if args.store_root else None
    out = build_scan_matrix(
        args.config,
        scope=args.scope,
        workers=int(args.workers),
        reserve_gib=float(args.reserve_system_gib),
        max_optuna_workers=int(args.max_optuna_workers),
        store_root=store_root,
    )
    print(json.dumps({
        "status": "ok", "command": "scan-matrix build",
        "scope": args.scope, "store_root": str(out),
    }, indent=2))
    return 0


def _cmd_scan_matrix_verify(args: argparse.Namespace) -> int:
    """Verify the built matrix; on success, write the parity-proof marker."""
    import datetime as _dt

    from .scanner.scan_matrix import verify_scan_matrix

    vectorized_check = bool(getattr(args, "vectorized_check", False))
    report = verify_scan_matrix(
        Path(args.store_root), args.config, sample_count=int(args.sample_count),
        vectorized_check=vectorized_check,
    )
    ok = report.get("status") in ("ok", "warn")
    if ok:
        # Speedup report v2 §6.1 / §10.6 — record a parity-proof marker the
        # runtime opt-in guard reads. verifier_version=1 admits the
        # compatibility runtime (Phase 3); verifier_version=2 (the vectorized
        # spot check ran clean) additionally admits the vectorized runtime.
        verifier_version = 2 if (vectorized_check and report.get("vectorized_checked")) else 1
        proof = {
            "matrix_id": report.get("matrix_id"),
            "config_input_hash": report.get("config_input_hash"),
            "dataset_hash": report.get("dataset_hash"),
            "verified_at_utc": _dt.datetime.utcnow().isoformat() + "Z",
            "verifier_version": verifier_version,
            "sampled": report.get("sampled"),
        }
        (Path(args.store_root) / "parity_proof.json").write_text(
            json.dumps(proof, indent=2, default=str), encoding="utf-8",
        )
    print(json.dumps(report, indent=2, default=str))
    return 0 if ok else 1


def _cmd_evaluate_finalists(args: argparse.Namespace) -> int:
    """Run the Phase 5 finalist evaluation pipeline.

    Speedup report v2 §1.4 / §9. Loads the study artifact JSON, fetches the
    completed trials (currently from the artifact's recorded ``best_params``
    + neighbour rows; a full storage reload would require PostgreSQL access
    — left to the operator wrapping this CLI with their own storage URL),
    then re-runs each finalist via the
    :func:`bowaka_v2_lab.optuna.evaluate_finalists.evaluate_finalists` API.
    """
    from .config.loader import load_config
    from .optuna.evaluate_finalists import (
        FinalistEvaluationConfig, evaluate_finalists,
    )

    cfg = load_config(args.config)
    fe_doc = (cfg.get("finalist_evaluation") or {})
    finalist_cfg = FinalistEvaluationConfig(
        top_k=int(fe_doc.get("top_k", 15)),
        include_incumbent=bool(fe_doc.get("include_incumbent", True)),
        full_artifacts=bool(fe_doc.get("full_artifacts", True)),
        score_final_holdout=bool(fe_doc.get("score_final_holdout", True)),
        stress_scenarios=list(fe_doc.get("stress_scenarios") or []),
        local_parameter_perturbation=dict(
            fe_doc.get("local_parameter_perturbation") or {}
        ),
    )
    # The CLI path delegates the scoring callables to the caller via the
    # study's storage URL. Tests pass their own stubs; this CLI smoke checks
    # the config parsing only (and emits a placeholder finalist_report so
    # the operator sees a meaningful error message until the scoring
    # callable wiring is supplied).
    study_dir = Path(args.study_dir)
    artifact = list(study_dir.glob("*.json"))
    summary = {
        "status": "skipped",
        "reason": (
            "evaluate-finalists CLI requires a storage URL or in-process "
            "study handle to reload completed trials. Use the Python API "
            "directly with completed_trials + scorers, or wrap this CLI."
        ),
        "study_dir": str(study_dir),
        "study_artifact_glob": [str(p) for p in artifact[:5]],
        "finalist_cfg": {
            "top_k": finalist_cfg.top_k,
            "include_incumbent": finalist_cfg.include_incumbent,
            "score_final_holdout": finalist_cfg.score_final_holdout,
            "stress_scenarios": [s.get("name") for s in finalist_cfg.stress_scenarios],
        },
    }
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "finalist_report.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, default=str))
    return 0


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


def _cmd_reconcile(args: argparse.Namespace) -> int:
    """Paper-vs-lab reconciliation (Phase 10 — scaffolding only).

    Resolves the paper-log directory from ``--paper-logs-root``, then
    ``$BOWAKA_V2_PAPER_LOGS_ROOT``, then (if a config is given)
    ``reconcile.paper_logs_root``. When NO paper logs are resolved the command
    writes a scaffolding-only ``reconciliation_report.{md,json}`` and exits 0
    with a clear message — it never fabricates paper data (the Phase-10
    operator constraint). When paper logs ARE resolved and a config is given,
    it replays the session against the lab in ``current_code_parity`` mode.
    """
    from .reconcile.replay import replay_paper_session
    from .reconcile.report import build_reconcile_report, render_realism_reconciliation_report

    out_dir = Path(args.out) if args.out else (
        Path(__file__).resolve().parents[4]
        / "research_notebooks" / "bowaka_v2_lab" / "artifacts" / "reconcile"
        / args.session_date
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    def _emit_scaffold(reason: str, note: str, **extra: object) -> int:
        """Write a scaffolding-only report, print the JSON summary, exit 0.

        Routes through ``build_reconcile_report`` with no rows so the report
        carries the standard section set and the scaffolding-only calibration
        advice (it never fabricates paper data — Phase-10 operator constraint).
        """
        render_realism_reconciliation_report(
            build_reconcile_report(
                args.session_date, [], scaffolding_only=True, note=note
            ),
            out_dir=out_dir,
        )
        print(json.dumps({
            "status": "ok", "command": "reconcile", "scaffolding_only": True,
            "reason": reason, "session_date": args.session_date,
            "out_dir": str(out_dir), **extra,
        }, indent=2, sort_keys=True))
        return 0

    # Resolve the paper-logs root: flag > env var > config.
    paper_logs_root = args.paper_logs_root or os.environ.get("BOWAKA_V2_PAPER_LOGS_ROOT")
    if not paper_logs_root and args.config:
        try:
            cfg = load_config(args.config)
            paper_logs_root = ((cfg.get("reconcile") or {}).get("paper_logs_root")) or None
        except Exception:  # noqa: BLE001 — a bad config must not crash the scaffold path
            paper_logs_root = None

    if not paper_logs_root:
        # No paper logs anywhere — never fabricate paper data (Phase-10
        # operator constraint); write a scaffolding-only report and exit 0.
        return _emit_scaffold(
            reason="no paper logs provided",
            note="no paper logs provided (--paper-logs-root absent, "
                 "$BOWAKA_V2_PAPER_LOGS_ROOT unset); wrote a scaffolding-only "
                 "report. Supply a paper-log directory to run a real "
                 "paper-vs-lab reconciliation.",
        )

    if not args.config:
        # Paper logs given but no config — the lab cannot be replayed without one.
        return _emit_scaffold(
            reason="paper logs present but no --config",
            note=f"paper logs at {paper_logs_root} but no --config given; the "
                 "lab cannot be replayed without a config. Pass --config to run "
                 "the paper-vs-lab reconciliation.",
            paper_logs_root=str(paper_logs_root),
        )

    # Full path — replay the paper session against the lab and reconcile.
    replay = replay_paper_session(
        args.session_date, paper_logs_root, args.config,
        run_dir=(out_dir / "lab_run"),
    )
    report = build_reconcile_report(
        replay.session_date, replay.rows,
        scaffolding_only=replay.scaffolding_only, note=replay.note,
    )
    render_realism_reconciliation_report(report, out_dir=out_dir)
    print(json.dumps({
        "status": "ok",
        "command": "reconcile",
        "scaffolding_only": replay.scaffolding_only,
        "session_date": replay.session_date,
        "paper_logs_root": str(paper_logs_root),
        "lab_run_dir": replay.lab_run_dir,
        "n_paper_candidates": replay.n_paper_candidates,
        "n_lab_candidates": replay.n_lab_candidates,
        "n_rows": len(replay.rows),
        "out_dir": str(out_dir),
    }, indent=2, sort_keys=True))
    return 0


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
