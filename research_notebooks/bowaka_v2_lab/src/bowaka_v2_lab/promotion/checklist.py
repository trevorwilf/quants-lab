"""Promotion-checklist callables.

Per [Report §19] / realism remediation Phase 8:
- QuantReviewerChecklist: 15 items
- SoftwareEngineerChecklist: 15 items
- StrategyOwnerChecklist: 6 items

Each callable takes ``(run_dir: Path)`` and returns ``(status, evidence)`` where
``status`` is ``"pass" | "fail" | "unknown"`` and **``evidence`` is a ``dict``**
(realism Phase 8 Task 4 — every check records structured evidence, not just a
free-text string).

Realism Phase 8 hardened the quant-reviewer checks ``qr.04``-``qr.10`` so they
inspect artifact *content* — an empty data-quality report, a placeholder dataset
hash, low quote coverage, a stub report, an unannotated config mismatch or a
trade count below the configured minimum all fail the gate. The pre-Phase-8
"file exists" checks are no longer sufficient.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Literal

#: A checklist result — ``(status, evidence_dict)``. ``evidence`` is always a
#: dict so downstream tooling (the promotion gate, the report renderer) gets a
#: structured record per check.
CHECKLIST_RESULT = tuple[Literal["pass", "fail", "unknown"], dict[str, Any]]

#: Default minimum closed-trade count for ``qr.09`` when the config does not set
#: ``promotion.min_trade_count``.
DEFAULT_MIN_TRADE_COUNT = 30
#: Default realism-mode historical-quote-coverage floor (percent) for ``qr.06``.
DEFAULT_MIN_QUOTE_COVERAGE_PCT = 98.0


# --------------------------------------------------------------------------
# small artifact readers
# --------------------------------------------------------------------------
def _read_json(run_dir: Path, filename: str) -> tuple[dict | None, str | None]:
    """``(doc, error)`` — ``doc`` is None on missing/corrupt; ``error`` describes why."""
    p = Path(run_dir) / filename
    if not p.is_file():
        return None, f"{filename} missing"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception as e:  # noqa: BLE001
        return None, f"{filename} unreadable: {e}"


def _read_yaml(run_dir: Path, filename: str) -> tuple[dict | None, str | None]:
    p = Path(run_dir) / filename
    if not p.is_file():
        return None, f"{filename} missing"
    try:
        import yaml

        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}, None
    except Exception as e:  # noqa: BLE001
        return None, f"{filename} unreadable: {e}"


# --------------------------------------------------------------------------
# generic existence / field checks (still dict-evidence)
# --------------------------------------------------------------------------
def _exists_check(run_dir: Path, filename: str) -> CHECKLIST_RESULT:
    p = Path(run_dir) / filename
    if p.is_file():
        return ("pass", {"artifact": filename, "present": True})
    return ("fail", {"artifact": filename, "present": False,
                     "detail": f"{filename} missing"})


def _summary_field(run_dir: Path, key: str, *, expect_truthy: bool = True) -> CHECKLIST_RESULT:
    doc, err = _read_json(run_dir, "summary.json")
    if doc is None:
        return ("unknown", {"detail": err})
    v = doc.get(key)
    ok = bool(v) if expect_truthy else (v is not None)
    return ("pass" if ok else "fail", {"field": key, "value": v})


def _run_manifest_field(run_dir: Path, key: str) -> CHECKLIST_RESULT:
    doc, err = _read_json(run_dir, "run_manifest.json")
    if doc is None:
        return ("unknown", {"detail": err})
    v = doc.get(key)
    return ("pass" if v else "fail", {"field": key, "value": v})


# --------------------------------------------------------------------------
# qr.04 — data-quality report must be substantive
# --------------------------------------------------------------------------
def _data_quality_report_check(run_dir: Path) -> CHECKLIST_RESULT:
    """``data_quality_report.json`` must carry a non-empty ``checks`` list AND no
    *required* check may be ``fail``.

    Realism Phase 2 made the DQ report substantive; Phase 8 additionally fails
    the gate when any required data-quality check failed.
    """
    doc, err = _read_json(run_dir, "data_quality_report.json")
    if doc is None:
        return ("fail", {"detail": err})
    checks = doc.get("checks")
    if not isinstance(checks, list) or len(checks) == 0:
        return ("fail", {"detail": "data_quality_report.json has empty checks",
                         "n_checks": 0})
    required_failures = list(doc.get("required_failures") or [])
    failed = [c.get("name") for c in checks if c.get("status") == "fail"]
    if required_failures:
        return ("fail", {"detail": f"required DQ check(s) failed: {required_failures}",
                         "n_checks": len(checks), "required_failures": required_failures,
                         "failed_checks": failed})
    return ("pass", {"n_checks": len(checks), "required_failures": [],
                     "failed_checks": failed,
                     "passed": doc.get("passed", 0), "warned": doc.get("warned", 0)})


# --------------------------------------------------------------------------
# qr.05 — dataset lineage must be real (no run_hash[:16] placeholder)
# --------------------------------------------------------------------------
def _dataset_lineage_check(run_dir: Path) -> CHECKLIST_RESULT:
    """``dataset_hash`` must NOT be the legacy ``run_hash[:16]`` placeholder, and
    the dataset provider must not claim ``fixture`` unless the run genuinely used
    fixture data.

    The pre-Phase-2 lineage stub set ``dataset_hash = run_hash[:16]``; a run that
    regressed to that placeholder cannot be promoted. A genuinely-synthetic run
    (``dataset_regime == synthetic``) legitimately reports ``provider: fixture``
    — that is honest and is NOT failed here; an unannotated ``fixture`` provider
    on a *lake* run is the failure.
    """
    man, err = _read_json(run_dir, "run_manifest.json")
    if man is None:
        return ("fail", {"detail": err})
    lineage = man.get("lineage") or {}
    dataset_hash = str(man.get("dataset_hash") or lineage.get("dataset_hash") or "")
    run_hash = str(man.get("run_hash") or (man.get("extras") or {}).get("run_hash") or "")
    provider = str(lineage.get("dataset_provider")
                   or (man.get("dataset_lineage") or {}).get("provider") or "")
    regime = str(lineage.get("dataset_regime")
                 or (man.get("dataset_lineage") or {}).get("regime") or "")

    if not dataset_hash:
        return ("fail", {"detail": "run_manifest.json carries no dataset_hash"})
    # The placeholder: dataset_hash == run_hash[:16].
    if run_hash and dataset_hash == run_hash[:16]:
        return ("fail", {
            "detail": "dataset_hash is the legacy run_hash[:16] placeholder — "
                      "dataset lineage was never computed",
            "dataset_hash": dataset_hash, "run_hash": run_hash,
        })
    # provider == fixture is honest only when the regime is genuinely synthetic.
    if provider == "fixture" and regime not in ("synthetic", ""):
        return ("fail", {
            "detail": f"dataset provider is 'fixture' but the dataset regime is "
                      f"'{regime}' — a lake run must not report a fixture provider",
            "provider": provider, "regime": regime,
        })
    return ("pass", {"dataset_hash": dataset_hash, "provider": provider,
                     "regime": regime, "placeholder": False})


# --------------------------------------------------------------------------
# qr.06 — quote coverage acceptable (realism mode)
# --------------------------------------------------------------------------
def _quote_coverage_check(run_dir: Path) -> CHECKLIST_RESULT:
    """Historical-quote coverage must be acceptable for a realism-mode run.

    Reads the ``quote_coverage`` check the backtester appends to
    ``data_quality_report.json`` at finalize. In ``intended_realism`` mode that
    check is ``fail`` when coverage is below ``simulation.min_quote_coverage_pct``;
    Phase 8 surfaces that as a promotion-gate failure. In non-realism modes the
    check is informational — the gate ``pass``es but records the measured
    coverage so a reviewer still sees it.
    """
    doc, err = _read_json(run_dir, "data_quality_report.json")
    if doc is None:
        return ("fail", {"detail": err})
    checks = doc.get("checks") or []
    qc = next((c for c in checks if c.get("name") == "quote_coverage"), None)
    if qc is None:
        # No finalize quote-coverage check was recorded — cannot assert coverage.
        return ("unknown", {"detail": "no quote_coverage check in "
                                      "data_quality_report.json"})
    evidence = qc.get("evidence") or {}
    coverage = evidence.get("historical_quote_coverage_pct")
    threshold = evidence.get("min_quote_coverage_pct", DEFAULT_MIN_QUOTE_COVERAGE_PCT)
    status = "fail" if qc.get("status") == "fail" else "pass"
    return (status, {
        "historical_quote_coverage_pct": coverage,
        "min_quote_coverage_pct": threshold,
        "quote_coverage_status": qc.get("status"),
        "candidates_total": evidence.get("candidates_total"),
        "candidates_with_quote": evidence.get("candidates_with_quote"),
        "detail": evidence.get("detail", "quote coverage check"),
    })


# --------------------------------------------------------------------------
# qr.07 — report.md is not a stub
# --------------------------------------------------------------------------
#: Substrings that mark a report as a non-substantive stub.
_STUB_MARKERS: tuple[str, ...] = ("stub", "phase n fills", "phase 5 fills")


def _no_stub_report_check(run_dir: Path) -> CHECKLIST_RESULT:
    """``report.md`` must not contain stub language (``stub`` / ``Phase N fills``)."""
    p = Path(run_dir) / "report.md"
    if not p.is_file():
        return ("fail", {"detail": "report.md missing"})
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        return ("fail", {"detail": f"report.md unreadable: {e}"})
    lowered = text.lower()
    hits = [m for m in _STUB_MARKERS if m in lowered]
    if hits:
        return ("fail", {"detail": f"report.md contains stub language: {hits}",
                         "markers": hits})
    return ("pass", {"report_bytes": len(text), "markers": []})


# --------------------------------------------------------------------------
# qr.08 — config parity clean (no unannotated mismatch)
# --------------------------------------------------------------------------
def _config_parity_check(run_dir: Path) -> CHECKLIST_RESULT:
    """``config_diff_vs_actual_bowaka_v2.yaml`` must have no unannotated
    ``mismatch`` row — every divergence from the frozen live contract must be
    either reconciled (``match``) or declared an ``intentional_override``.

    When the frozen contract was unavailable on the build host the diff carries
    a ``note`` and zero rows — that is ``unknown`` (parity could not be checked),
    not a hard fail.
    """
    doc, err = _read_yaml(run_dir, "config_diff_vs_actual_bowaka_v2.yaml")
    if doc is None:
        return ("fail", {"detail": err})
    rows = doc.get("rows") or []
    note = doc.get("note")
    if not rows and note:
        return ("unknown", {"detail": f"parity not computed: {note}"})
    mismatches = [str(r.get("path")) for r in rows
                  if r.get("parity_status") == "mismatch"]
    summary = doc.get("summary") or {}
    if mismatches:
        return ("fail", {
            "detail": f"{len(mismatches)} unannotated config mismatch(es) vs the "
                      f"live contract",
            "mismatch_count": len(mismatches),
            "mismatch_paths": mismatches[:50],
            "summary": summary,
        })
    return ("pass", {"mismatch_count": 0, "summary": summary})


# --------------------------------------------------------------------------
# qr.09 — minimum closed-trade count
# --------------------------------------------------------------------------
def _min_trade_count_check(run_dir: Path) -> CHECKLIST_RESULT:
    """``summary.json['n_trades']`` must be at least the configured minimum.

    The threshold is ``promotion.min_trade_count`` from the run's
    ``config_snapshot.json`` (default :data:`DEFAULT_MIN_TRADE_COUNT`). A run
    with too few trades is statistically uninformative and cannot be promoted.
    """
    summary, s_err = _read_json(run_dir, "summary.json")
    if summary is None:
        return ("fail", {"detail": s_err})
    n_trades = summary.get("n_trades")
    if n_trades is None:
        return ("fail", {"detail": "summary.json has no n_trades"})
    cfg, _ = _read_json(run_dir, "config_snapshot.json")
    threshold = DEFAULT_MIN_TRADE_COUNT
    if isinstance(cfg, dict):
        promo = cfg.get("promotion") or {}
        if isinstance(promo, dict) and promo.get("min_trade_count") is not None:
            try:
                threshold = int(promo["min_trade_count"])
            except (TypeError, ValueError):
                threshold = DEFAULT_MIN_TRADE_COUNT
    try:
        n = int(n_trades)
    except (TypeError, ValueError):
        return ("fail", {"detail": f"n_trades is not an integer: {n_trades!r}"})
    if n < threshold:
        return ("fail", {"detail": f"n_trades={n} is below the minimum {threshold}",
                         "n_trades": n, "min_trade_count": threshold})
    return ("pass", {"n_trades": n, "min_trade_count": threshold})


# --------------------------------------------------------------------------
# qr.10 — walk-forward holdout present (optuna runs only)
# --------------------------------------------------------------------------
def _walkforward_holdout_check(run_dir: Path) -> CHECKLIST_RESULT:
    """Walk-forward holdout evidence — required only for ``optuna`` runs.

    For a plain ``backtest`` run there is no walk-forward holdout to check, so
    the item ``pass``es with a "not applicable" note. For an ``optuna`` run a
    ``walkforward_holdout.json`` artifact must be present (Phase 9 will enforce
    that the holdout fold was untouched during tuning); its absence fails the
    gate. This is the structurally-correct Phase-8 placeholder.
    """
    man, err = _read_json(run_dir, "run_manifest.json")
    run_kind = (man or {}).get("run_kind", "backtest")
    rd = Path(run_dir)
    holdout_paths = [
        rd / "walkforward_holdout.json",
        rd.parent / "optuna" / "walkforward_holdout.json",
    ]
    found = next((p for p in holdout_paths if p.is_file()), None)
    if run_kind != "optuna":
        return ("pass", {"run_kind": run_kind,
                         "detail": "not an optuna run — walk-forward holdout "
                                   "not applicable",
                         "holdout_present": found is not None})
    if found is None:
        return ("fail", {"run_kind": run_kind,
                         "detail": "optuna run is missing a walkforward_holdout.json "
                                   "artifact"})
    return ("pass", {"run_kind": run_kind, "holdout_present": True,
                     "holdout_artifact": str(found)})


# ----- 15 Quant Reviewer items
QUANT_REVIEWER_CHECKLIST: dict[str, Callable[[Path], CHECKLIST_RESULT]] = {
    "qr.01_run_manifest_present":          lambda rd: _exists_check(rd, "run_manifest.json"),
    "qr.02_dataset_manifest_present":      lambda rd: _exists_check(rd, "dataset_manifest.json"),
    "qr.03_code_manifest_present":         lambda rd: _exists_check(rd, "code_manifest.json"),
    # Phase 8 — content-inspecting quant-reviewer checks.
    "qr.04_data_quality_report_present":   _data_quality_report_check,
    "qr.05_dataset_lineage_present":       _dataset_lineage_check,
    "qr.06_quote_coverage_acceptable":     _quote_coverage_check,
    "qr.07_no_stub_report":                _no_stub_report_check,
    "qr.08_config_parity_clean":           _config_parity_check,
    "qr.09_min_trade_count":               _min_trade_count_check,
    "qr.10_walkforward_holdout_present":   _walkforward_holdout_check,
    # qr.11-15 — structural summary / manifest fields (kept from pre-Phase-8).
    "qr.11_summary_has_run_id":            lambda rd: _summary_field(rd, "run_id"),
    "qr.12_summary_has_feed":              lambda rd: _summary_field(rd, "feed"),
    "qr.13_summary_has_n_trades":          lambda rd: _summary_field(rd, "n_trades", expect_truthy=False),
    "qr.14_summary_has_max_drawdown":      lambda rd: _summary_field(rd, "max_drawdown_pct", expect_truthy=False),
    "qr.15_run_manifest_has_dataset_hash": lambda rd: _run_manifest_field(rd, "dataset_hash"),
}


# ----- 15 Software Engineer items
SOFTWARE_ENGINEER_CHECKLIST: dict[str, Callable[[Path], CHECKLIST_RESULT]] = {
    f"se.{i + 1:02d}_artifact_{name}": (lambda rd, n=name: _exists_check(rd, n)) for i, name in enumerate([
        "config_snapshot.json", "fills.parquet", "orders.parquet", "positions.parquet",
        "gate_dump.parquet", "execution_quality.parquet",
    ])
} | {
    "se.07_run_manifest_strategy_id":      lambda rd: _run_manifest_field(rd, "strategy_id"),
    "se.08_run_manifest_config_hash":      lambda rd: _run_manifest_field(rd, "config_hash"),
    "se.09_run_manifest_code_manifest_hash": lambda rd: _run_manifest_field(rd, "code_manifest_hash"),
    "se.10_run_manifest_created_at":       lambda rd: _run_manifest_field(rd, "created_at"),
    "se.11_summary_accepted_count":        lambda rd: _summary_field(rd, "accepted_count", expect_truthy=False),
    "se.12_summary_rejected_count":        lambda rd: _summary_field(rd, "rejected_count", expect_truthy=False),
    "se.13_summary_broker_reject_count":   lambda rd: _summary_field(rd, "broker_reject_count", expect_truthy=False),
    "se.14_summary_ambiguous_bar_count":   lambda rd: _summary_field(rd, "ambiguous_bar_count", expect_truthy=False),
    "se.15_summary_cost_stress":           lambda rd: _summary_field(rd, "cost_stress"),
}


# ----- 6 Strategy Owner items
STRATEGY_OWNER_CHECKLIST: dict[str, Callable[[Path], CHECKLIST_RESULT]] = {
    "so.01_summary_present":               lambda rd: _exists_check(rd, "summary.json"),
    "so.02_report_md_present":             lambda rd: _exists_check(rd, "report.md"),
    "so.03_run_manifest_feed":             lambda rd: _run_manifest_field(rd, "feed"),
    "so.04_summary_net_return_pct":        lambda rd: _summary_field(rd, "net_return_pct", expect_truthy=False),
    "so.05_summary_win_rate":              lambda rd: _summary_field(rd, "win_rate", expect_truthy=False),
    "so.06_dataset_manifest_present":      lambda rd: _exists_check(rd, "dataset_manifest.json"),
}


def run_all_checklists(run_dir: Path) -> dict[str, CHECKLIST_RESULT]:
    """Run every checklist item and return ``{item_id: (status, evidence_dict)}``."""
    out: dict[str, CHECKLIST_RESULT] = {}
    for name, fn in QUANT_REVIEWER_CHECKLIST.items():
        out[name] = fn(run_dir)
    for name, fn in SOFTWARE_ENGINEER_CHECKLIST.items():
        out[name] = fn(run_dir)
    for name, fn in STRATEGY_OWNER_CHECKLIST.items():
        out[name] = fn(run_dir)
    return out
