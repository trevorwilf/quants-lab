"""Phase 8 — qr.09 fails when the closed-trade count is below the minimum.

``qr.09_min_trade_count`` reads ``summary.json['n_trades']`` and the run's
``config_snapshot.json['promotion']['min_trade_count']`` (default 30). A run
with too few trades is statistically uninformative and fails the gate.
"""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.promotion.checklist import DEFAULT_MIN_TRADE_COUNT, QUANT_REVIEWER_CHECKLIST

_QR09 = QUANT_REVIEWER_CHECKLIST["qr.09_min_trade_count"]


def _write(rd: Path, *, n_trades: int, min_trade_count: int | None) -> None:
    (rd / "summary.json").write_text(
        json.dumps({"n_trades": n_trades}), encoding="utf-8")
    cfg: dict = {"strategy_id": "bowaka_v2"}
    if min_trade_count is not None:
        cfg["promotion"] = {"min_trade_count": min_trade_count}
    (rd / "config_snapshot.json").write_text(json.dumps(cfg), encoding="utf-8")


def test_five_trades_threshold_thirty_fails_qr09(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    _write(rd, n_trades=5, min_trade_count=30)
    status, evidence = _QR09(rd)
    assert status == "fail"
    assert isinstance(evidence, dict)
    assert evidence["n_trades"] == 5
    assert evidence["min_trade_count"] == 30


def test_enough_trades_passes_qr09(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    _write(rd, n_trades=42, min_trade_count=30)
    status, evidence = _QR09(rd)
    assert status == "pass"
    assert evidence["n_trades"] == 42


def test_default_threshold_used_when_config_absent(tmp_path: Path) -> None:
    """No promotion.min_trade_count → the default (30) applies."""
    rd = tmp_path / "run"
    rd.mkdir()
    _write(rd, n_trades=DEFAULT_MIN_TRADE_COUNT - 1, min_trade_count=None)
    status, evidence = _QR09(rd)
    assert status == "fail"
    assert evidence["min_trade_count"] == DEFAULT_MIN_TRADE_COUNT


def test_custom_threshold_from_config_is_honored(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    # 10 trades with a custom floor of 8 → pass.
    _write(rd, n_trades=10, min_trade_count=8)
    status, evidence = _QR09(rd)
    assert status == "pass"
    assert evidence["min_trade_count"] == 8


def test_missing_summary_fails_qr09(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    status, evidence = _QR09(rd)
    assert status == "fail"
    assert isinstance(evidence, dict)
