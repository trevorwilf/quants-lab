"""Promotion-checklist callables.

Per [Report §19]:
- QuantReviewerChecklist: 15 items
- SoftwareEngineerChecklist: 15 items
- StrategyOwnerChecklist: 6 items

Each callable takes ``(run_dir: Path)`` and returns ``(status, evidence)`` where
``status`` is ``"pass" | "fail" | "unknown"``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal


CHECKLIST_RESULT = tuple[Literal["pass", "fail", "unknown"], str]


def _exists_check(run_dir: Path, filename: str) -> CHECKLIST_RESULT:
    p = Path(run_dir) / filename
    return ("pass", f"{filename} present") if p.is_file() else ("fail", f"{filename} missing")


def _data_quality_report_check(run_dir: Path) -> CHECKLIST_RESULT:
    """data_quality_report.json must be present AND carry a non-empty ``checks`` list.

    Realism Phase 2 made the DQ report substantive; an empty ``checks`` list now
    means the report was never populated, which fails the promotion gate.
    """
    p = Path(run_dir) / "data_quality_report.json"
    if not p.is_file():
        return ("fail", "data_quality_report.json missing")
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return ("fail", f"data_quality_report.json unreadable: {e}")
    checks = doc.get("checks")
    if not isinstance(checks, list) or len(checks) == 0:
        return ("fail", "data_quality_report.json has empty checks")
    return ("pass", f"data_quality_report.json present with {len(checks)} checks")


def _summary_field(run_dir: Path, key: str, *, expect_truthy: bool = True) -> CHECKLIST_RESULT:
    p = Path(run_dir) / "summary.json"
    if not p.is_file():
        return ("unknown", "summary.json missing")
    s = json.loads(p.read_text(encoding="utf-8"))
    v = s.get(key)
    ok = bool(v) if expect_truthy else (v is not None)
    return ("pass" if ok else "fail", f"{key}={v}")


def _run_manifest_field(run_dir: Path, key: str) -> CHECKLIST_RESULT:
    p = Path(run_dir) / "run_manifest.json"
    if not p.is_file():
        return ("unknown", "run_manifest.json missing")
    m = json.loads(p.read_text(encoding="utf-8"))
    v = m.get(key)
    return ("pass" if v else "fail", f"{key}={v}")


# ----- 15 Quant Reviewer items
QUANT_REVIEWER_CHECKLIST: dict[str, Callable[[Path], CHECKLIST_RESULT]] = {
    "qr.01_run_manifest_present":         lambda rd: _exists_check(rd, "run_manifest.json"),
    "qr.02_dataset_manifest_present":     lambda rd: _exists_check(rd, "dataset_manifest.json"),
    "qr.03_code_manifest_present":        lambda rd: _exists_check(rd, "code_manifest.json"),
    "qr.04_data_quality_report_present":  _data_quality_report_check,
    "qr.05_candidate_events_present":     lambda rd: _exists_check(rd, "candidate_events.parquet"),
    "qr.06_entry_decisions_present":      lambda rd: _exists_check(rd, "entry_decisions.parquet"),
    "qr.07_trades_present":               lambda rd: _exists_check(rd, "trades.parquet"),
    "qr.08_daily_equity_present":         lambda rd: _exists_check(rd, "daily_equity.parquet"),
    "qr.09_summary_present":              lambda rd: _exists_check(rd, "summary.json"),
    "qr.10_report_md_present":            lambda rd: _exists_check(rd, "report.md"),
    "qr.11_summary_has_run_id":           lambda rd: _summary_field(rd, "run_id"),
    "qr.12_summary_has_feed":             lambda rd: _summary_field(rd, "feed"),
    "qr.13_summary_has_n_trades":         lambda rd: _summary_field(rd, "n_trades", expect_truthy=False),
    "qr.14_summary_has_max_drawdown":     lambda rd: _summary_field(rd, "max_drawdown_pct", expect_truthy=False),
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
    """Run every checklist item and return a dict of ``item_id -> (status, evidence)``."""
    out: dict[str, CHECKLIST_RESULT] = {}
    for name, fn in QUANT_REVIEWER_CHECKLIST.items():
        out[name] = fn(run_dir)
    for name, fn in SOFTWARE_ENGINEER_CHECKLIST.items():
        out[name] = fn(run_dir)
    for name, fn in STRATEGY_OWNER_CHECKLIST.items():
        out[name] = fn(run_dir)
    return out
