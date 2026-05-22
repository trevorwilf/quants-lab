"""Phase 10 — fill comparator: signed fill-price delta in bps + qty delta."""
from __future__ import annotations

from bowaka_v2_lab.reconcile.comparators import (
    compare_fill,
    compare_order_size,
    compare_pnl,
    compare_exit_reason,
)
from bowaka_v2_lab.reconcile.schemas import (
    LabExit,
    LabFill,
    LabOrder,
    PaperExit,
    PaperFill,
    PaperOrder,
)


def _pfill(price: float, qty: float = 100.0) -> PaperFill:
    return PaperFill(parent_order_id="po1", symbol="AAA", avg_fill_price=price, filled_qty=qty)


def _lfill(price: float, qty: float = 100.0) -> LabFill:
    return LabFill(parent_order_id="po1", symbol="AAA", avg_fill_price=price, filled_qty=qty)


def test_lab_fills_higher_positive_bps() -> None:
    """Lab fills above paper -> a POSITIVE signed bps delta."""
    cmp = compare_fill(_pfill(100.00), _lfill(100.10))
    # (100.10 - 100.00) / 100.00 * 10_000 = 10 bps.
    assert cmp.price_delta_bps is not None
    assert abs(cmp.price_delta_bps - 10.0) < 1e-6


def test_lab_fills_lower_negative_bps() -> None:
    """Lab fills below paper -> a NEGATIVE signed bps delta."""
    cmp = compare_fill(_pfill(100.00), _lfill(99.95))
    # (99.95 - 100.00) / 100.00 * 10_000 = -5 bps.
    assert cmp.price_delta_bps is not None
    assert abs(cmp.price_delta_bps - (-5.0)) < 1e-6


def test_identical_fill_zero_bps() -> None:
    cmp = compare_fill(_pfill(50.0), _lfill(50.0))
    assert cmp.price_delta_bps == 0.0


def test_fill_qty_delta_signed() -> None:
    """qty_delta is lab_qty - paper_qty (positive => lab over-fills)."""
    cmp = compare_fill(_pfill(10.0, qty=98.0), _lfill(10.0, qty=100.0))
    assert cmp.qty_delta == 2.0
    cmp2 = compare_fill(_pfill(10.0, qty=100.0), _lfill(10.0, qty=95.0))
    assert cmp2.qty_delta == -5.0


def test_missing_fill_not_comparable() -> None:
    assert compare_fill(_pfill(10.0), None).price_delta_bps is None
    assert compare_fill(None, _lfill(10.0)).qty_delta is None


def test_zero_paper_price_guarded() -> None:
    """A zero paper fill price cannot be a bps denominator -> None, no crash."""
    cmp = compare_fill(_pfill(0.0), _lfill(10.0))
    assert cmp.price_delta_bps is None


def test_order_size_delta_signed() -> None:
    """order_size_delta is lab.qty - paper.qty."""
    p = PaperOrder(parent_order_id="po1", symbol="AAA", qty=100.0)
    lab = LabOrder(parent_order_id="po1", symbol="AAA", qty=98.0)
    assert compare_order_size(p, lab) == -2.0
    assert compare_order_size(None, lab) is None


def test_pnl_delta_signed() -> None:
    """pnl_delta is lab.realized_pnl - paper.realized_pnl."""
    p = PaperExit(symbol="AAA", realized_pnl=60.0, exit_reason="take_profit")
    lab = LabExit(symbol="AAA", realized_pnl=-20.0, exit_reason="stop")
    assert compare_pnl(p, lab) == -80.0
    assert compare_pnl(p, None) is None


def test_exit_reason_match() -> None:
    same = compare_exit_reason(
        PaperExit(symbol="AAA", exit_reason="stop"),
        LabExit(symbol="AAA", exit_reason="stop"),
    )
    assert same is True
    diff = compare_exit_reason(
        PaperExit(symbol="AAA", exit_reason="take_profit"),
        LabExit(symbol="AAA", exit_reason="stop"),
    )
    assert diff is False
    assert compare_exit_reason(None, LabExit(symbol="AAA", exit_reason="stop")) is None
