"""Regression: the scan-matrix BUILD and VERIFY must resolve the SAME symbol
set for the dataset_hash.

Bug (found 2026-06-02 during operator matrix prep): ``build_scan_matrix``
hashes the PIT-eligible union when ``universe.symbols`` is empty (a screener
config), but ``_expected_manifest_dataset_hash`` (the verify drift check) read
raw ``universe.symbols`` (= ``[]``) with no PIT fallback. The two symbol sets
differ, so ``symbol_universe_hash`` differs, so ``dataset_hash`` differs, and
EVERY screener matrix false-positives on ``dataset_hash_drift`` — a failure no
rebuild can clear (the rebuild reproduces the same mismatch).

Fixed by sharing :func:`_resolve_lineage_symbols` between both paths. These
tests pin the contract; they run lake-free (fixture market-data => the synthetic
lineage regime) so they are deterministic on any host.
"""
from __future__ import annotations

import datetime as dt

import bowaka_v2_lab.scanner.scan_matrix as sm
from bowaka_v2_lab.config.hashing import canonical_strategy_hash
from bowaka_v2_lab.data.lineage import build_dataset_lineage


def _screener_cfg() -> dict:
    """A screener config (no explicit ``universe.symbols``) on fixture feeds.

    Fixture bar sources keep ``build_dataset_lineage`` in the synthetic regime,
    so the hash is a pure function of {feed, date_range, symbol_universe_hash,
    lab_config_hash} — no lake / filesystem needed.
    """
    return {
        "market_data": {
            "feed": "iex",
            "minute_bar_source": "fixture",
            "daily_bar_source": "fixture",
        },
        "backtest": {"start_date": "2025-08-01", "end_date": "2025-11-30"},
        "universe": {  # screener — deliberately NO `symbols`
            "asset_classes": ["operating_equity"],
            "max_price": 20.0,
            "min_price": 1.0,
            "min_adv_dollars": 250000,
        },
    }


def _lab_hash(cfg: dict) -> str:
    # Mirror _expected_manifest_dataset_hash's own try/except so the test's
    # build-side hash uses the exact same lab_config_hash branch.
    try:
        return canonical_strategy_hash(cfg)
    except Exception:  # noqa: BLE001
        return "unknown"


def test_resolve_lineage_symbols_explicit_symbols_win_over_pit() -> None:
    cfg = {"universe": {"symbols": ["AAA", "BBB"]}}
    out = sm._resolve_lineage_symbols(cfg, eligible_pit={dt.date(2025, 8, 27): ("ZZZ",)})
    assert out == ["AAA", "BBB"]


def test_resolve_lineage_symbols_unions_pit_first_seen_dedup() -> None:
    d1, d2 = dt.date(2025, 8, 27), dt.date(2025, 8, 28)
    out = sm._resolve_lineage_symbols(
        {"universe": {}}, eligible_pit={d1: ("A", "B"), d2: ("B", "C")},
    )
    assert out == ["A", "B", "C"]


def test_resolve_lineage_symbols_empty_when_no_pit_no_sessions() -> None:
    assert sm._resolve_lineage_symbols({"universe": {}}) == []


def test_verify_reproduces_build_dataset_hash_for_screener(monkeypatch) -> None:
    """The core regression: verify recomputes the build's hash, not an empty-set
    hash, for a screener config."""
    cfg = _screener_cfg()
    union = ["AAA", "BBB", "CCC"]
    sessions = [dt.date(2025, 8, 27), dt.date(2025, 8, 28)]

    # Stub the PIT probe so the verifier's union is deterministic + lake-free.
    monkeypatch.setattr(
        sm, "_eligible_pit_union_for_lineage",
        lambda cfg, sessions, lake_root: {sessions[0]: tuple(union)},
    )

    lab_hash = _lab_hash(cfg)
    build_hash = build_dataset_lineage(
        cfg=cfg, symbols=union,
        start=cfg["backtest"]["start_date"], end=cfg["backtest"]["end_date"],
        lab_config_hash=lab_hash,
    )["dataset_hash"]

    manifest = {
        "sessions": [s.isoformat() for s in sessions],
        "dataset_hash": build_hash,
    }

    # FIXED behaviour: verify reproduces the build's hash -> no drift.
    assert sm._expected_manifest_dataset_hash(manifest, cfg) == build_hash

    # And the OLD behaviour (empty symbols) WOULD have diverged -> proves the
    # asymmetry this test guards against was real, not theoretical.
    empty_hash = build_dataset_lineage(
        cfg=cfg, symbols=[],
        start=cfg["backtest"]["start_date"], end=cfg["backtest"]["end_date"],
        lab_config_hash=lab_hash,
    )["dataset_hash"]
    assert empty_hash != build_hash
