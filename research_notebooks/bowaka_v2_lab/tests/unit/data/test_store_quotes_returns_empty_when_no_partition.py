"""Phase 5 (audit 2026-05-29 §9 Phase 7) — quotes() empty on a SIP-less lake."""
from __future__ import annotations

from pathlib import Path

from bowaka_common.marketdata import MarketDataStore


def test_quotes_empty_when_no_partition(tmp_path: Path) -> None:
    store = MarketDataStore(str(tmp_path))
    df = store.quotes("AAA", "2024-09-03", "2024-09-04", feed="sip")
    assert df is not None
    assert df.empty
