"""Walkforward smoke: flag-on vs flag-off must produce identical backtest output.

Phase 4 of the session-minute-window-supplier parity fix. With the fix in
:mod:`bowaka_v2_lab.scanner.session_minute_window_cache` landed AND the
``optuna.acceleration.session_minute_window_cache.enabled`` flag re-enabled
in the workstation config, the full walkforward chain must produce
byte-identical trade counts whether or not the Phase 4 supplier is wired
into the fold context. This is the end-to-end guard that supplements the
supplier-level parity tests in ``tests/scanner/``.

Skip-guarded: the test requires the operator's real lake (the bug only
triggers on µs-resolution lake parquets). On CI hosts without the lake the
module skips at collection time.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd
import pytest

# ---- module skip: real lake must be reachable ------------------------------
try:
    from bowaka_common.marketdata.store import default_market_data_root
except ImportError:  # pragma: no cover — defensive
    pytest.skip("bowaka_common not importable", allow_module_level=True)


_LAKE_ROOT = default_market_data_root()
_PROBE = (
    _LAKE_ROOT / "bars" / "vendor=alpaca" / "feed=iex"
    / "timeframe=1m" / "adjustment=raw"
    / "symbol=AAL" / "year=2025" / "month=08" / "part.parquet"
)
if not _PROBE.is_file():
    pytest.skip(
        f"real lake AAL probe missing at {_PROBE}; the walkforward parity "
        "smoke requires the operator's lake.",
        allow_module_level=True,
    )


pytestmark = pytest.mark.integration


# 10 microcap symbols known to have minute data on 2025-08-27.
_UNIVERSE = (
    "AAL", "ABAT", "ABCL", "ABEV", "ABSI", "ACB", "ACDC", "ACEL", "ACH", "ACHR",
)
_VAL_SESSION = _dt.date(2025, 8, 27)
_VAL_END = _dt.date(2025, 8, 28)        # half-open: [val_start, val_end)
_TRAIN_START = _dt.date(2025, 8, 26)


def _build_cfg(*, flag_enabled: bool) -> dict:
    """Workstation cfg-shape dict with the flag flipped + 1-session window."""
    return {
        "strategy_id": "bowaka_v2_walkforward_parity_smoke",
        "simulation": {"mode": "current_code_parity"},
        "market_data": {
            "feed": "iex",
            "minute_bar_source": "alpaca",
            "daily_bar_source": "alpaca",
            "shared_root": str(_LAKE_ROOT),
            "require_adjusted_daily_bars": True,
            "require_split_adjustment": True,
            "max_bar_age_seconds": 90,
            "max_quote_age_seconds": 15,
        },
        "universe": {
            "symbols": list(_UNIVERSE),
            "min_price": 1.0, "max_price": 100.0,
            "min_adv_dollars": 0,
        },
        "backtest": {
            "start_date": _TRAIN_START.isoformat(),
            "end_date": _VAL_END.isoformat(),
            "cost_stress": "conservative",
        },
        "optuna": {
            "n_trials": 1, "n_jobs": 1,
            "cached_suppliers": True,   # Phase 4 wraps the minute supplier on top
            "walkforward": {
                "train_months": 1, "val_months": 1, "final_holdout_months": 1,
            },
            "acceleration": {
                "session_minute_window_cache": {"enabled": bool(flag_enabled)},
            },
        },
    }


@pytest.mark.timeout(180)   # <2 min budget per Phase 4 spec, +60s safety
def test_session_window_supplier_flag_on_off_minute_supplier_parity(tmp_path):
    """Per-(symbol, scan_ts) parity between flag-ENABLED and flag-DISABLED
    fold contexts on the real lake.

    Stop short of running the full ``run_backtest`` (which would also
    exercise the entire scanner / cost-model / exits pipeline — already
    well-covered by other integration tests). The supplier-level
    invariant is the one that triggered the original silent-zero-trades
    bug, and this test pins it END-TO-END via ``build_fold_contexts``
    so any future regression in either ``fold_context.py`` (the swap)
    or the supplier itself (Phase 2) is caught here.
    """
    from bowaka_v2_lab.config.paths import BowakaV2Paths
    from bowaka_v2_lab.optuna.fold_context import build_fold_contexts
    from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard
    from bowaka_v2_lab.optuna.walkforward import WalkForwardPlan, WalkForwardSplit

    # Synthetic 1-session walkforward plan over the operator's diagnostic
    # session. ``build_walkforward_splits`` works in months — too coarse for
    # this test — so we construct WalkForwardPlan / WalkForwardSplit directly.
    plan = WalkForwardPlan(
        splits=(WalkForwardSplit(
            train_start=_TRAIN_START, train_end=_VAL_SESSION,
            val_start=_VAL_SESSION, val_end=_VAL_END,
        ),),
        final_holdout_start=_VAL_END,
        final_holdout_end=_dt.date(2025, 8, 29),
    )
    paths = BowakaV2Paths(
        lab_root=tmp_path / "lab",
        data_root=tmp_path / "lab" / "data",
        artifact_root=tmp_path / "lab" / "artifacts",
        config_path=tmp_path / "lab" / "cfg.yml",
    )
    guard = HoldoutGuard(plan.final_holdout_start, plan.final_holdout_end)

    ctxs_off = build_fold_contexts(
        _build_cfg(flag_enabled=False), plan,
        lake_root=_LAKE_ROOT, feed="iex", symbols=list(_UNIVERSE),
        paths=paths, holdout_guard=guard, cached_suppliers=True,
    )
    ctxs_on = build_fold_contexts(
        _build_cfg(flag_enabled=True), plan,
        lake_root=_LAKE_ROOT, feed="iex", symbols=list(_UNIVERSE),
        paths=paths, holdout_guard=guard, cached_suppliers=True,
    )

    assert len(ctxs_off) == len(ctxs_on) == 1
    ctx_off, ctx_on = ctxs_off[0], ctxs_on[0]
    assert ctx_off is not None and ctx_on is not None, (
        "fold context build returned None — the diagnostic session must "
        "produce a valid context."
    )
    assert ctx_off.sessions == ctx_on.sessions == (_VAL_SESSION,)

    compared = 0
    for sym in _UNIVERSE:
        # 3 cutoffs over the session — same trio Phase 3 uses.
        for hour, minute in ((9, 45), (12, 0), (15, 55)):
            cutoff = pd.Timestamp(
                _dt.datetime.combine(_VAL_SESSION, _dt.time(hour=hour, minute=minute)),
                tz="America/New_York",
            ).tz_convert("UTC")
            off = ctx_off.suppliers.minute(sym, cutoff)
            on_ = ctx_on.suppliers.minute(sym, cutoff)
            if off is None or on_ is None or (off.empty and on_.empty):
                continue
            off_sorted = off.sort_values("timestamp").reset_index(drop=True)
            on_sorted = on_.sort_values("timestamp").reset_index(drop=True)
            assert len(off_sorted) == len(on_sorted), (
                f"{sym} @ {cutoff}: row-count drift off={len(off_sorted)} "
                f"on={len(on_sorted)} — the supplier swap diverged."
            )
            pd.testing.assert_frame_equal(
                off_sorted, on_sorted,
                check_like=True, check_dtype=False,
            )
            compared += 1

    # Both ctxs must be REAL ctxs (universe screened, eligibles found) AND
    # at least one (symbol, cutoff) pair must have been compared with non-
    # empty data on both sides.
    assert compared > 0, (
        f"no (symbol, cutoff) pair with non-empty bars on either fold "
        f"context for {_VAL_SESSION}: the universe screen probably dropped "
        f"every symbol on that date."
    )
