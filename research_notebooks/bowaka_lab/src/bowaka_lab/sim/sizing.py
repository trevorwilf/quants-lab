"""Phase fidelity-5: source-aligned sizing resolution.

Three modes:

- ``equal_slice`` (source default) — per-trade dollars =
  ``fraction × bankroll / max_concurrent_positions``. ``fraction`` defaults
  to ``max_gross_exposure_pct`` (auto-coupled) but can be explicit.
- ``risk_per_trade`` — qty = ``floor(target_risk_dollars /
  (close × (stop_pct + slip_pct)))``. Resolved per candidate (not session).
- ``legacy_fixed_notional`` — back-compat. Uses ``per_trade_notional``.

The exact-mode invariant cluster (Phase fidelity-1) is extended in Phase 5 to
require ``equal_slice`` + explicit ``bankroll_dollars`` + explicit
``equal_slice_bankroll_fraction``.
"""

from __future__ import annotations

from bowaka_lab.config.models import PortfolioConfig


def resolve_per_trade_dollars(portfolio: PortfolioConfig) -> float:
    """Resolve the per-trade dollar size for the session.

    For ``risk_per_trade``, this function raises — the caller must use
    :func:`resolve_qty_risk_per_trade` because the quantity depends on the
    candidate's stop_pct + close.
    """
    if portfolio.sizing_mode == "legacy_fixed_notional":
        if portfolio.per_trade_notional is None:
            raise ValueError("legacy_fixed_notional requires per_trade_notional to be set")
        return float(portfolio.per_trade_notional)

    if portfolio.sizing_mode == "equal_slice":
        if portfolio.bankroll_dollars is None:
            # Back-compat path: when bankroll isn't set, fall through to the
            # legacy per_trade_notional. Avoids breaking pre-Phase-5 tests.
            if portfolio.per_trade_notional is not None:
                return float(portfolio.per_trade_notional)
            raise ValueError(
                "equal_slice requires bankroll_dollars (or per_trade_notional for legacy mode)"
            )
        fraction = portfolio.equal_slice_bankroll_fraction
        if fraction is None:
            # Auto-couple to max_gross_exposure_pct.
            mge = portfolio.max_gross_exposure_pct
            fraction = min(1.0, float(mge)) if (mge is not None and mge > 0) else 1.0
        fraction = float(fraction)
        if not (0.0 < fraction <= 1.0):
            raise ValueError(
                f"equal_slice_bankroll_fraction={fraction} must be in (0, 1]"
            )
        n = max(1, int(portfolio.max_concurrent_positions))
        return float(fraction * portfolio.bankroll_dollars / n)

    if portfolio.sizing_mode == "risk_per_trade":
        raise NotImplementedError(
            "risk_per_trade requires per-candidate stop context; "
            "use resolve_qty_risk_per_trade instead"
        )

    raise ValueError(f"Unknown sizing_mode={portfolio.sizing_mode!r}")


def resolve_qty_risk_per_trade(
    *,
    target_risk_dollars: float,
    close: float,
    stop_pct: float,
    expected_stop_slippage_pct: float,
) -> int:
    """qty = floor(target_risk / (close × (stop_pct + slip_pct))).

    Returns 0 when inputs are degenerate. Matches source
    ``bowaka_strategy._per_trade_dollars_for_slate`` risk_per_trade branch.
    """
    if close <= 0 or target_risk_dollars <= 0:
        return 0
    per_share_loss = max(1e-9, float(close) * (float(stop_pct) + float(expected_stop_slippage_pct)))
    qty = int(float(target_risk_dollars) / per_share_loss)
    return max(0, qty)
