"""verify-realism-stress — Phases 1-5 verification report (audit 2026-05-29).

Mirror of ``verify_bayesian_fix`` for the realism / methodology / paper-recon /
SIP-readiness phases. Sections 9-12 are TEST-BACKED (a subprocess pytest batch
per section — never a nested ``pytest.main``); Section 13 mixes direct
SIP-readiness checks with explicitly-deferred cells (``SIP_DATA_UNAVAILABLE``);
Section 14 aggregates a junit summary. ``--skip-suite`` runs only the fast
direct + deferred rows. Exit 0 iff every row is PASS or DEFERRED.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as _ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_LAB_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class Check:
    section: str
    name: str
    result: str   # "PASS" | "FAIL" | "DEFERRED"


#: Section -> targeted test files (relative to the lab root).
_SECTION_TESTS: dict[str, list[str]] = {
    "9": [
        "tests/unit/sim/test_stress_slippage_offset_applied.py",
        "tests/unit/sim/test_stress_spread_multiplier_applied.py",
        "tests/unit/sim/test_adv_bucket_cap_partial_fill.py",
        "tests/unit/sim/test_adv_bucket_cap_full_fill_in_large_bucket.py",
        "tests/parity/test_stress_matrix_base_point_equals_unstressed_backtest.py",
        "tests/integration/test_paper_candidate_gate_requires_stress_matrix_floor.py",
    ],
    "10": [
        "tests/unit/sim/test_stress_no_fill_on_tight_bar_range.py",
        "tests/unit/sim/test_stress_adverse_selection_bps_applied.py",
        "tests/unit/sim/test_stress_late_day_multiplier_curve.py",
        "tests/unit/optuna/test_gap_through_stop_penalty.py",
        "tests/unit/optuna/test_same_minute_ambiguity_penalty.py",
        "tests/integration/test_stress_envelope_dim_failure_blocks_paper_candidate.py",
        "tests/parity/test_stress_matrix_base_envelope_equals_unstressed.py",
    ],
    "11": [
        "tests/unit/optuna/test_multi_seed_orchestrator_runs_n_studies.py",
        "tests/unit/optuna/test_ensemble_best_selects_highest_median.py",
        "tests/unit/reports/test_parameter_stability_score.py",
        "tests/unit/optuna/test_perturbation_robustness_within_tolerance.py",
        "tests/unit/optuna/test_fold_activity_gates.py",
        "tests/unit/reports/test_regime_segmentation_buckets.py",
        "tests/integration/test_holdout_guard_blocks_tuning_read.py",
        "tests/integration/test_validity_check_refuses_study_without_holdout_guard.py",
    ],
    "12": [
        "tests/unit/reconcile/test_discover_sessions.py",
        "tests/integration/test_reconcile_against_synthetic_fixture.py",
        "tests/integration/test_reconcile_with_no_logs_returns_deferred.py",
        "tests/integration/test_reconcile_below_min_sessions.py",
        "tests/integration/test_promotion_gate_blocks_paper_without_recon.py",
        "tests/integration/test_promotion_gate_blocks_paper_on_threshold_miss.py",
        "tests/integration/test_promotion_gate_allows_paper_on_full_pass.py",
        "tests/unit/reconcile/test_bucketed_fill_error_per_adv.py",
        "tests/integration/test_reconcile_cli_exit_codes.py",
    ],
}

_SECTION_TITLES = {
    "9": "Section 9 — Phase 1: stress matrix part A (quote-adjacent)",
    "10": "Section 10 — Phase 2: stress matrix part B (timing-adjacent)",
    "11": "Section 11 — Phase 3: optimization methodology",
    "12": "Section 12 — Phase 4: paper reconciliation",
    "13": "Section 13 — Phase 5: SIP-readiness scaffolding",
}


def _run_pytest(files: list[str]) -> bool:
    existing = [str(_LAB_ROOT / f) for f in files if (_LAB_ROOT / f).is_file()]
    if not existing:
        return False
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *existing, "-q", "--tb=line",
         "-p", "no:cacheprovider"],
        cwd=str(_LAB_ROOT), env=os.environ.copy(), capture_output=True, text=True,
    )
    return proc.returncode == 0


def _section13_direct() -> list[Check]:
    """Direct (fast, deterministic) SIP-readiness checks + deferred cells."""
    out: list[Check] = []
    with tempfile.TemporaryDirectory() as td:
        from bowaka_common.marketdata import MarketDataStore
        from ..data.halt_feed import read_halt_events
        from ..reports.feed_divergence import feed_divergence_report

        store = MarketDataStore(td)
        q = store.quotes("AAA", "2024-09-03", "2024-09-04", feed="sip")
        out.append(Check("13", "lake reader: quotes() empty when no partition",
                         "PASS" if (q is not None and q.empty) else "FAIL"))

        halts = read_halt_events(td, "AAA", "2024-09-03", "2024-09-04")
        out.append(Check("13", "halt feed reader empty when no partition",
                         "PASS" if halts == [] else "FAIL"))

        rep = feed_divergence_report(
            iex_store=store, sip_store=store, symbols=["AAA"],
            start=_dt.date(2024, 9, 3), end=_dt.date(2024, 9, 4),
        )
        out.append(Check(
            "13", f"feed divergence status when SIP unavailable -> {rep['status']}",
            "DEFERRED" if rep["status"] == "SIP_DATA_UNAVAILABLE" else "FAIL"))

    runbook = _LAB_ROOT / "docs" / "sip_migration_runbook.md"
    out.append(Check("13", "SIP migration runbook present",
                     "PASS" if runbook.is_file() else "FAIL"))
    out.extend(_section13_synthetic_sip())
    return out


def _section13_synthetic_sip() -> list[Check]:
    """Audit 2026-05-29 §9 Phase 7 — exercise the SIP cutover gates against the
    committed synthetic-SIP fixture lake (real-shaped data, no SIP feed needed)."""
    import datetime as _dt2
    import shutil
    import tempfile

    out: list[Check] = []
    fixture = _LAB_ROOT / "tests" / "fixtures" / "sip_synthetic_lake"
    if not fixture.is_dir():
        out.append(Check("13", "SIP synthetic fixture present", "FAIL"))
        return out

    from ..data.halt_feed import read_halt_events
    from ..optuna.preflight import (
        FoldWindow, PreflightError, check_nbbo_quote_coverage,
        run_full_fold_preflight,
    )
    from ..reports.feed_divergence import compute_feed_divergence
    from ..sim.schedule import scan_times_for_session

    syms = ["AAAA", "BBBB", "CCCC", "DDDD", "EEEE"]
    cfg = {
        "strategy_id": "bowaka_v2",
        "market_data": {"feed": "sip", "shared_root": str(fixture),
                        "require_split_adjustment": True,
                        "minute_bar_source": "alpaca", "daily_bar_source": "alpaca"},
        "simulation": {"mode": "intended_realism", "min_quote_coverage_pct": 0.80,
                       "quote_fallback_policy": "require_real"},
        "universe": {"min_adv_dollars": 0, "min_price": 1.0, "max_price": 1000.0},
        "preflight": {"min_pit_universe_per_fold": 3},
    }
    folds = [FoldWindow(fold_id="val_2025-08-04", kind="validation",
                        start=_dt2.date(2025, 8, 4), end=_dt2.date(2025, 8, 22))]

    try:
        run_full_fold_preflight(
            cfg=cfg, folds=folds, symbols=syms, lake_root=str(fixture), feed="sip",
            dataset_hash="d" * 64, config_hash="c" * 64,
            scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
            min_quote_coverage_pct=80.0, mode="intended_realism",
        )
        smoke = "PASS"
    except Exception:  # noqa: BLE001
        smoke = "FAIL"
    out.append(Check("13", "SIP synthetic end-to-end smoke completes", smoke))

    refuses = "FAIL"
    with tempfile.TemporaryDirectory() as td:
        copy = Path(td) / "no_quotes"
        shutil.copytree(fixture, copy)
        shutil.rmtree(copy / "quotes", ignore_errors=True)
        try:
            check_nbbo_quote_coverage(
                sim_mode="intended_realism", feed="sip", lake_root=str(copy),
                universe=syms, fold_windows=folds, min_coverage_pct=80.0,
            )
        except PreflightError:
            refuses = "PASS"
        except Exception:  # noqa: BLE001
            refuses = "FAIL"
    out.append(Check("13", "SIP synthetic NBBO gate refuses missing quotes", refuses))

    try:
        rep = compute_feed_divergence(
            sip_root=fixture, iex_root=fixture, symbols=["AAAA", "BBBB"],
            sessions=["2025-08-25", "2025-08-26"],
        )
        halts = read_halt_events(str(fixture), "AAAA",
                                 _dt2.date(2025, 8, 1), _dt2.date(2025, 8, 29))
        div_ok = rep["status"] == "ok" and rep["n_rows"] >= 2 and len(halts) >= 1
    except Exception:  # noqa: BLE001
        div_ok = False
    out.append(Check("13", "SIP synthetic feed-divergence report produces data",
                     "PASS" if div_ok else "FAIL"))

    try:
        from bowaka_common.marketdata.layout import bars_timeframe_root
        from bowaka_common.marketdata.store import resolve_market_data_root
        real = bars_timeframe_root(
            resolve_market_data_root(None, create=False), "1d",
            vendor="alpaca", feed="sip", adjustment="split_adjusted",
        )
        present = real.is_dir() and any(real.glob("symbol=*"))
    except Exception:  # noqa: BLE001
        present = False
    out.append(Check("13", "real SIP partition present",
                     "PASS" if present else "DEFERRED"))
    return out


def _parse_junit(path: Path) -> Optional[dict]:
    if not path.is_file():
        return None
    try:
        root = _ET.parse(path).getroot()
    except Exception:
        return None
    ts = root if root.tag == "testsuite" else root.find("testsuite")
    if ts is None:
        return None
    tests = int(ts.get("tests", "0"))
    failures = int(ts.get("failures", "0"))
    errors = int(ts.get("errors", "0"))
    skipped = int(ts.get("skipped", "0"))
    return {"tests": tests, "passed": tests - failures - errors - skipped,
            "failed": failures + errors, "skipped": skipped}


def _suite_summary() -> Optional[dict]:
    all_files = [f for files in _SECTION_TESTS.values() for f in files]
    existing = [str(_LAB_ROOT / f) for f in all_files if (_LAB_ROOT / f).is_file()]
    if not existing:
        return None
    junit = _LAB_ROOT / "artifacts" / "test-junit-realism.xml"
    junit.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [sys.executable, "-m", "pytest", *existing, "-q", "--tb=line",
             "-p", "no:cacheprovider", f"--junitxml={junit}"],
            cwd=str(_LAB_ROOT), env=os.environ.copy(), capture_output=True, text=True,
        )
        return _parse_junit(junit)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def run_checks(*, run_suite: bool = True) -> tuple[list[Check], Optional[dict]]:
    checks: list[Check] = []
    for sec in ("9", "10", "11", "12"):
        if run_suite:
            ok = _run_pytest(_SECTION_TESTS[sec])
            checks.append(Check(sec, "targeted test batch", "PASS" if ok else "FAIL"))
        else:
            checks.append(Check(sec, "targeted test batch", "DEFERRED"))
    checks.extend(_section13_direct())
    # Explicitly-deferred environment cells.
    checks.append(Check("11", "multi-seed smoke run (opt-in)", "DEFERRED"))
    checks.append(Check("12", "real-log reconciliation (data/paper_logs)", "DEFERRED"))
    suite = _suite_summary() if run_suite else None
    return checks, suite


def build_report(checks: list[Check], suite: Optional[dict], *, all_passed: bool) -> str:
    import platform

    def _git(rev: str) -> str:
        try:
            return subprocess.run(["git", "rev-parse", rev], capture_output=True,
                                  text=True, cwd=str(_LAB_ROOT)).stdout.strip() or "unknown"
        except Exception:
            return "unknown"

    lines = ["# Bowaka v2 realism + methodology — verification report", ""]
    lines.append(f"- generated_at: {_dt.datetime.now(_dt.UTC).isoformat()}")
    lines.append(f"- lab_commit: {_git('HEAD')}")
    lines.append(f"- python: {sys.version.split()[0]} ({platform.platform()})")
    lines.append("")
    for sec in ("9", "10", "11", "12", "13"):
        rows = [c for c in checks if c.section == sec]
        lines.append(f"## {_SECTION_TITLES[sec]}")
        lines.append("")
        lines.append("| Check | Result |")
        lines.append("|---|---|")
        for c in rows:
            lines.append(f"| {c.name} | {c.result} |")
        lines.append("")
    lines.append("## Section 14 — Test suite summary")
    lines.append("")
    if suite and "error" not in suite:
        lines.append("| Tests | Passed | Failed | Skipped |")
        lines.append("|---:|---:|---:|---:|")
        lines.append(f"| {suite['tests']} | {suite['passed']} | "
                     f"{suite['failed']} | {suite['skipped']} |")
    elif suite and "error" in suite:
        lines.append(f"- aggregation failed: {suite['error']}")
    else:
        lines.append("- not run in this invocation")
    lines.append("")
    lines.append("## Overall")
    lines.append("")
    verdict = "PASS" if all_passed else "FAIL"
    suffix = ("(all sections PASS or DEFERRED)" if all_passed
              else "(at least one FAIL — promotion is BLOCKED)")
    lines.append(f"**OVERALL: {verdict}** _{suffix}_")
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="verify-realism-stress")
    ap.add_argument("--out", default=None)
    ap.add_argument("--skip-suite", action="store_true",
                    help="skip the test-backed section batches + Section 14")
    args = ap.parse_args(argv)

    checks, suite = run_checks(run_suite=not args.skip_suite)
    section14_ok = (
        args.skip_suite
        or (suite is not None and "error" not in suite and suite["failed"] == 0)
    )
    all_passed = all(c.result in ("PASS", "DEFERRED") for c in checks) and section14_ok

    report = build_report(checks, suite, all_passed=all_passed)
    if args.out:
        out_path = Path(args.out)
    else:
        ts = _dt.datetime.now(_dt.UTC).strftime("%Y%m%dT%H%M%SZ")
        out_path = _LAB_ROOT / "artifacts" / "verification" / f"realism_stress_verification_{ts}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"VERIFICATION_REPORT: {out_path}")
    print(f"OVERALL: {'PASS' if all_passed else 'FAIL'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
