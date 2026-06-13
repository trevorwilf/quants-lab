"""P5 (L18) — tape-replay sale-condition eligibility filter.

The tape-replay oracle replayed EVERY print as continuous executable liquidity,
including odd-lot (``I``), average-price (``B``/``W``), out-of-sequence (``Z``/``L``),
derivatively-priced (``4``) and auction (``O``/``M``/``Q``/``5``/``6``) prints —
manufacturing liquidity (Round-2: a 100-share no-fill became a full 600/600 fill).
The filter keeps only continuous prints.

These are pure-function tests of the filter logic + a small constructed-tape test
of the replay mechanics. The DECISIVE realism claim — that the filter drops the
right prints on the actual SIP tape and corrects the over-fill — is asserted on
the REAL tape in ``tests/integration/test_real_data_lane.py`` (P2 lane).
"""
from __future__ import annotations

import pandas as pd
import pytest

from bowaka_v2_lab.sim.tape_fill import (
    _print_is_eligible,
    _TAPE_INELIGIBLE_CONDITIONS,
    replay_tape_fill,
)


# --------------------------------------------------------------------------
# _print_is_eligible — pure logic
# --------------------------------------------------------------------------
@pytest.mark.parametrize("cond", [" ", "", "@", " ,F", " ,T", " ,9", " ,F,T", None, "nan"])
def test_eligible_conditions_pass(cond) -> None:
    assert _print_is_eligible(cond) is True


@pytest.mark.parametrize(
    "cond",
    [" ,I", " ,F,I", " ,M", " ,Q", " ,O", " ,6", " ,5", " ,B", " ,W", " ,4", " ,Z", " ,L"],
)
def test_ineligible_conditions_dropped(cond) -> None:
    assert _print_is_eligible(cond) is False


def test_strictest_rule_wins_any_ineligible_code_excludes() -> None:
    # A regular-sale print that ALSO carries an odd-lot flag is excluded.
    assert _print_is_eligible(" ,F,I") is False
    # An out-of-sequence average-price print is excluded.
    assert _print_is_eligible(" ,Z,B") is False
    # No ineligible code -> eligible even with several benign codes.
    assert _print_is_eligible(" ,F,T,P") is True


def test_ineligible_set_matches_documented_codes() -> None:
    # CTS {I,B,W,4,Z,L,O,M,Q} + UTP auction {5,6}.
    assert _TAPE_INELIGIBLE_CONDITIONS == frozenset(
        {"I", "B", "W", "4", "Z", "L", "O", "M", "Q", "5", "6"}
    )


# --------------------------------------------------------------------------
# replay_tape_fill — filter mechanics on a constructed tape
# --------------------------------------------------------------------------
def _tape(rows: list[tuple[str, float, float, str]]) -> pd.DataFrame:
    base = pd.Timestamp("2025-08-01T14:00:00Z")
    return pd.DataFrame([
        {"timestamp": base + pd.Timedelta(seconds=i), "price": p, "size": s, "conditions": c}
        for i, (_, p, s, c) in enumerate(rows)
    ])


def test_replay_excludes_odd_lot_volume() -> None:
    """A 600-share order sees only the eligible (regular-sale) volume, not the
    odd-lot prints — so it partials instead of over-filling on fabricated depth."""
    tape = _tape([
        ("a", 10.0, 100.0, " "),       # eligible 100
        ("b", 10.0, 50.0, " ,I"),      # odd-lot — dropped
        ("c", 10.0, 50.0, " ,I"),      # odd-lot — dropped
        ("d", 10.0, 100.0, " ,F"),     # eligible 100
        ("e", 10.0, 30.0, " ,I"),      # odd-lot — dropped
    ])
    r = replay_tape_fill(tape, qty=600, start_ts="2025-08-01T14:00:00Z",
                         window_seconds=300, participation=1.0)
    # Only 200 eligible shares (100 + 100); the rest of the request is unfilled.
    assert r.filled is False
    assert r.filled_qty == 200
    assert r.window_qty == 200          # eligible volume only (not 330)


def test_replay_all_odd_lot_window_is_no_fill() -> None:
    """The Round-2 over-fill scenario (mechanics): a window of ONLY odd-lot /
    auction prints supplies no continuous liquidity -> no fill (was a full fill)."""
    tape = _tape([
        ("a", 10.0, 100.0, " ,I"),
        ("b", 10.0, 100.0, " ,I"),
        ("c", 10.0, 100.0, " ,M"),     # official close (auction)
        ("d", 10.0, 100.0, " ,Q"),     # official open (auction)
    ])
    r = replay_tape_fill(tape, qty=100, start_ts="2025-08-01T14:00:00Z",
                         window_seconds=300, participation=1.0)
    assert r.filled is False
    assert r.filled_qty == 0


def test_replay_no_conditions_column_is_safe_fallback() -> None:
    """A tape WITHOUT a conditions column passes everything (legacy behavior) so
    older fixtures still fill — the filter is opt-in on column presence."""
    tape = _tape([("a", 10.0, 100.0, " "), ("b", 10.0, 100.0, " ,I")]).drop(columns=["conditions"])
    r = replay_tape_fill(tape, qty=150, start_ts="2025-08-01T14:00:00Z",
                         window_seconds=300, participation=1.0)
    assert r.filled is True
    assert r.filled_qty == 150          # both prints counted (no filter without the column)
