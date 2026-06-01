"""Phase 1 — the accelerated lab data path is byte-identical to the legacy one.

``run_lab_backtester(cached_data_path=True)`` (session-minute-window cache +
cached daily/quote/forward suppliers + batch daily cache + objective_minimal)
must produce a ``BacktestResult`` whose trades + candidates are identical to the
legacy uncached path on the same window — proving the speedup changed only data
access, not strategy decisions / fills / exits / numerics.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pytest

_LAB = Path(__file__).resolve().parents[2]
_LAB_CONFIG = _LAB / "configs" / "bowaka_v2_actual_iex_current_code.yml"

pytestmark = pytest.mark.integration


@pytest.mark.timeout(600)
def test_cached_data_path_matches_legacy(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    if not _LAB_CONFIG.is_file():
        pytest.skip(f"lab config not at {_LAB_CONFIG}")
    try:
        from bowaka_common.marketdata.catalog import available_symbols
        from bowaka_common.marketdata.store import resolve_market_data_root
    except ImportError:
        pytest.skip("bowaka_common not importable")
    lake_root = resolve_market_data_root(None, create=False)
    syms = available_symbols(
        lake_root, timeframe="1d", vendor="alpaca", feed="iex",
        adjustment="split_adjusted",
    )
    if "AGNC" not in syms:
        pytest.skip("real lake not present (AGNC not available)")

    from bowaka_v2_lab.parity.normalizers import normalize_lab_output
    from bowaka_v2_lab.parity.runner import run_lab_backtester

    # Strategy-relevant symbols so the window actually trades.
    universe = ["AGNC", "ALHC", "ALT", "ARVN", "BLMN", "CCC", "PACB", "PSEC",
                "SONO", "VNDA"]
    start, end = _dt.date(2026, 5, 19), _dt.date(2026, 5, 20)
    common = dict(start_date=start, end_date=end, symbols=universe,
                  lab_config_path=_LAB_CONFIG, cost_stress="base")

    legacy = run_lab_backtester(**common, cached_data_path=False,
                                run_dir=tmp_path / "legacy")
    cached = run_lab_backtester(**common, cached_data_path=True,
                                run_dir=tmp_path / "cached")

    lt, lc = normalize_lab_output(legacy)
    ct, cc = normalize_lab_output(cached)
    lt.sort(key=lambda t: t.join_key)
    ct.sort(key=lambda t: t.join_key)

    assert [t.join_key for t in lt] == [t.join_key for t in ct], (
        f"trade keys differ: legacy={len(lt)} cached={len(ct)}"
    )
    for a, b in zip(lt, ct):
        assert abs(a.entry_price - b.entry_price) <= 1e-12, (a.symbol, a.entry_price, b.entry_price)
        assert (a.exit_price is None) == (b.exit_price is None)
        if a.exit_price is not None:
            assert abs(a.exit_price - b.exit_price) <= 1e-12
        assert a.exit_reason == b.exit_reason
        assert a.qty_filled == b.qty_filled
        assert abs(a.pnl_dollars - b.pnl_dollars) <= 1e-9
    # Candidate streams identical too.
    assert sorted(c.join_key for c in lc) == sorted(c.join_key for c in cc)
