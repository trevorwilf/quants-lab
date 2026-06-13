"""P2 / §6 — ENFORCED real-data fidelity lane.

These tests exercise the REAL SIP lake + trades tape. On an ordinary host (no
lake, lane not declared) they SKIP; in the ql-jupyter container with
``BOWAKA_REAL_DATA_LANE=1`` + ``MARKET_DATA_ROOT=/opt/market_data_cache`` they
RUN and a missing lake/tape FAILS (see :mod:`tests._real_data_lane`). This is the
real-tape fidelity assertion the §6 census found missing (PB.5 was only an ad-hoc
script). The committed-subset check is host-runnable.
"""
from __future__ import annotations

import datetime as _dt

import numpy as np
import pandas as pd

from tests._real_data_lane import require_real_tape

_PROBE = "IREN"
_FEED = "sip"


def test_tape_replay_fill_is_honest_on_real_tape() -> None:
    """On the REAL SIP tape the tape-replay fill is size-bounded (never fills more
    than the order, i.e. it cannot manufacture liquidity the way the legacy
    100%-at-bar-price model does) and directionally honest (a marketable buy pays
    >= the trigger, a sell gets <= it). These invariants are exactly what the
    legacy fill model violates."""
    lake_root = require_real_tape(_PROBE, feed=_FEED)
    from bowaka_common.marketdata import MarketDataStore
    from bowaka_v2_lab.data.suppliers import make_trades_supplier
    from bowaka_v2_lab.sim.tape_fill import replay_tape_fill

    store = MarketDataStore(lake_root, vendor="alpaca")
    trades_supplier = make_trades_supplier(lake_root, feed=_FEED)
    # The golden window (dense real tape for IREN).
    w0 = pd.Timestamp(_dt.datetime(2025, 8, 20, 13, 45), tz="UTC")
    w1 = pd.Timestamp(_dt.datetime(2025, 8, 25, 19, 55), tz="UTC")
    mb = store.minute_bars(_PROBE, w0, w1, feed=_FEED)
    assert mb is not None and len(mb) > 0, "no real minute bars for the probe sample"
    mb = mb.sort_values("timestamp").reset_index(drop=True)

    n_checked = 0
    n_partial_or_slipped = 0
    for i in np.linspace(0, len(mb) - 1, min(60, len(mb))).astype(int):
        bar = mb.iloc[int(i)]
        t = pd.Timestamp(bar["timestamp"])
        t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
        px = float(bar["close"])
        if px <= 0:
            continue
        qty = max(int(4000.0 / px), 1)
        tr = trades_supplier(_PROBE, t, t + pd.Timedelta(seconds=300))
        if tr is None or len(tr) == 0:
            continue
        buy = replay_tape_fill(tr, qty=qty, start_ts=t, window_seconds=300,
                               participation=1.0, min_price=px)
        sell = replay_tape_fill(tr, qty=qty, start_ts=t, window_seconds=300,
                                participation=1.0, max_price=px)
        # Size-bounded: NEVER fills more than the order (no manufactured depth).
        assert 0 <= buy.filled_qty <= qty
        assert 0 <= sell.filled_qty <= qty
        assert 0.0 <= buy.fill_fraction <= 1.0
        assert 0.0 <= sell.fill_fraction <= 1.0
        # Directionally honest vs the trigger price.
        if buy.filled_qty > 0:
            assert buy.avg_fill_price >= px - 1e-9
        if sell.filled_qty > 0:
            assert sell.avg_fill_price <= px + 1e-9
        # Track the realism gap vs the legacy 100%-fill / 0-bps model.
        if buy.fill_fraction < 1.0 or sell.fill_fraction < 1.0 \
                or (buy.filled_qty > 0 and buy.avg_fill_price > px + 1e-9) \
                or (sell.filled_qty > 0 and sell.avg_fill_price < px - 1e-9):
            n_partial_or_slipped += 1
        n_checked += 1

    assert n_checked >= 5, f"too few real-tape samples checked ({n_checked}); widen the window"
    # The legacy model claims 100% fill at 0 bps on every point; on the real tape
    # at least some sampled $4k orders give up size or price — the gap is real.
    assert n_partial_or_slipped >= 1, (
        "real tape showed no partial/slipped fills across the sample — unexpected "
        "for marketable $4k orders; verify the tape is real and non-degenerate"
    )


def test_tape_eligibility_filter_drops_ineligible_prints_on_real_tape() -> None:
    """P5/L18: on the REAL SIP tape the eligibility filter drops odd-lot / auction
    / out-of-sequence prints, so the tape-replay fill draws on STRICTLY LESS volume
    than the unfiltered tape — the manufactured-liquidity correction (Round-2:
    counting odd-lots turned a no-fill into a full fill)."""
    lake_root = require_real_tape(_PROBE, feed=_FEED)
    from bowaka_v2_lab.data.suppliers import make_trades_supplier
    from bowaka_v2_lab.sim.tape_fill import _print_is_eligible, replay_tape_fill

    trades_supplier = make_trades_supplier(lake_root, feed=_FEED)
    t = pd.Timestamp(_dt.datetime(2025, 8, 20, 13, 45), tz="UTC")
    tr = None
    for _ in range(40):  # walk forward to a window with a real, condition-tagged tape
        cand = trades_supplier(_PROBE, t, t + pd.Timedelta(seconds=600))
        if cand is not None and len(cand) > 20 and "conditions" in cand.columns:
            tr = cand
            break
        t = t + pd.Timedelta(minutes=20)
    assert tr is not None and len(tr) > 20, "no real tape window with conditions found"

    elig = tr["conditions"].map(_print_is_eligible)
    n_dropped = int((~elig).sum())
    # The supplier MUST pass conditions through (else the filter is a silent no-op)
    # and the real microcap tape carries odd-lot / auction prints to drop.
    assert n_dropped >= 1, "no ineligible prints found — conditions not flowing or tape degenerate"

    qty = 5000
    filt = replay_tape_fill(tr, qty=qty, start_ts=t, window_seconds=600, participation=1.0)
    unfilt = replay_tape_fill(tr.drop(columns=["conditions"]), qty=qty, start_ts=t,
                              window_seconds=600, participation=1.0)
    # The filter only ever REMOVES liquidity (ineligible prints' volume); it can
    # never manufacture more than the unfiltered tape.
    assert filt.window_qty <= unfilt.window_qty
    assert filt.window_qty < unfilt.window_qty, (
        "filter dropped prints but eligible volume == unfiltered — odd-lot/auction "
        "prints carried zero size? verify the real tape"
    )


def test_committed_iex_subset_is_real_not_synthetic(tmp_path) -> None:
    """The committed IEX subset must be REAL data, not the silent synthetic
    fallback — else CI 'real-data' coverage is a no-op (§6). Host-runnable: reads
    the committed subset's manifest, no live lake needed."""
    from tests.fixtures.loader import load_iex_subset

    subset = load_iex_subset(lake_source="committed", tmp_path=tmp_path)
    assert subset.synthetic_fallback is False, (
        f"committed IEX subset resolved as synthetic (source={subset.source}); the "
        "committed real-data subset is missing or was built from a broken lake — "
        "rebuild it from the real lake (scripts/.../build_iex_subset.py)."
    )
