"""Phase fidelity-7: notebook 08 must NOT compute abs(exit - entry) as a
'spread proxy'. That was an analysis bug; the new design uses three
independent proxies (quote, entry-minute range, first-minute range).
"""

from __future__ import annotations

from pathlib import Path

BUILDER = (
    Path(__file__).resolve().parents[2]
    / "notebooks"
    / "_build_08_liquidity_and_execution_quality.py"
)


def test_builder_does_not_compute_abs_exit_minus_entry():
    src = BUILDER.read_text(encoding="utf-8")
    # The legacy bug was `abs(exit_price - entry_price)`. Reject any
    # variant of that expression appearing as a proxy computation.
    assert "(exit_price - entry_price)" not in src.replace(" ", ""), (
        "notebook 08 still computes (exit_price - entry_price) as a proxy"
    )
    assert "exit_price - entry_price" not in src.replace(" ", ""), (
        "notebook 08 still references exit_price - entry_price"
    )


def test_builder_declares_three_independent_proxies():
    src = BUILDER.read_text(encoding="utf-8")
    for proxy in ("quote_spread_bps", "entry_minute_range_bps", "first_minute_range_bps"):
        assert proxy in src, f"notebook 08 must reference {proxy!r}"
