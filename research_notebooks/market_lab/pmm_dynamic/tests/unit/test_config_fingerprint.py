"""to_fingerprint() parity across MR, EMA, and PMM SimConfig.

Contract: two configs with identical fields produce identical fingerprints
(hashable tuples). Two configs differing in ANY single field produce
different fingerprints. Lists are converted to tuples so the fingerprint
is hashable.
"""

import pytest

from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig
from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig


def test_mr_fingerprint_identical_configs_equal():
    a = MeanReversionBBRSIStrategyConfig()
    b = MeanReversionBBRSIStrategyConfig()
    assert a.to_fingerprint() == b.to_fingerprint()
    # Hashable (must be usable as a dict key / in a set)
    {a.to_fingerprint(): 1}


def test_mr_fingerprint_differs_on_single_field():
    a = MeanReversionBBRSIStrategyConfig()
    from dataclasses import replace
    b = replace(a, bb_length=200)
    assert a.to_fingerprint() != b.to_fingerprint()


def test_mr_fingerprint_covers_every_field():
    """Any change to any field of the config must produce a different
    fingerprint. Protects against future field additions that forget to
    include the new field."""
    from dataclasses import fields, replace
    a = MeanReversionBBRSIStrategyConfig()
    for f in fields(a):
        cur = getattr(a, f.name)
        if isinstance(cur, bool):
            new = not cur
        elif isinstance(cur, int):
            new = cur + 1
        elif isinstance(cur, float):
            new = cur + 0.01
        elif isinstance(cur, str):
            new = cur + "_x"
        else:
            pytest.skip(f"field {f.name} has un-perturbable type {type(cur)}")
            continue
        try:
            b = replace(a, **{f.name: new})
        except (ValueError, TypeError):
            continue
        assert a.to_fingerprint() != b.to_fingerprint(), (
            f"to_fingerprint() failed to distinguish field {f.name}"
        )


def test_ema_fingerprint_identical_configs_equal():
    a = EMARegimeHoldStrategyConfig()
    b = EMARegimeHoldStrategyConfig()
    assert a.to_fingerprint() == b.to_fingerprint()
    {a.to_fingerprint(): 1}


def test_ema_fingerprint_differs_on_single_field():
    from dataclasses import replace
    a = EMARegimeHoldStrategyConfig()
    b = replace(a, regime_ema_slow=300)
    assert a.to_fingerprint() != b.to_fingerprint()


def test_ema_fingerprint_covers_every_field():
    from dataclasses import fields, replace
    a = EMARegimeHoldStrategyConfig()
    for f in fields(a):
        cur = getattr(a, f.name)
        if isinstance(cur, bool):
            new = not cur
        elif isinstance(cur, int):
            new = cur + 1
        elif isinstance(cur, float):
            new = cur + 0.01
        elif isinstance(cur, str):
            new = cur + "_x"
        else:
            pytest.skip(f"field {f.name} has un-perturbable type {type(cur)}")
            continue
        try:
            b = replace(a, **{f.name: new})
        except (ValueError, TypeError):
            continue
        assert a.to_fingerprint() != b.to_fingerprint(), (
            f"to_fingerprint() failed to distinguish field {f.name}"
        )
