"""Phase 7: test/sanity-ledger contamination detection."""

from __future__ import annotations

import pandas as pd

from bowaka_lab.reconcile.replay_comparator import detect_ledger_contamination


def test_test_pattern_trade_id_flagged():
    df = pd.DataFrame(
        [
            {"trade_id": "BOWAKA-TEST-AAPL-100", "ticker": "AAPL", "account_id": "PA1"},
            {"trade_id": "BOWAKA-AAA-1001", "ticker": "AAA", "account_id": "PA1"},
            {"trade_id": "SANITY-XYZ", "ticker": "XYZ", "account_id": "PA1"},
        ]
    )
    flagged = detect_ledger_contamination(df, production_account="PA1")
    flagged_ids = set(flagged["trade_id"].tolist())
    assert "BOWAKA-TEST-AAPL-100" in flagged_ids
    assert "SANITY-XYZ" in flagged_ids
    assert "BOWAKA-AAA-1001" not in flagged_ids


def test_account_id_mismatch_flagged():
    df = pd.DataFrame(
        [
            {"trade_id": "BOWAKA-AAA-1001", "ticker": "AAA", "account_id": "PA2"},
        ]
    )
    flagged = detect_ledger_contamination(df, production_account="PA1")
    assert flagged.shape[0] == 1
    assert "account_id_mismatch" in flagged.iloc[0]["contamination_reason"]


def test_mode_test_flagged():
    df = pd.DataFrame(
        [
            {"trade_id": "BOWAKA-AAA-1001", "ticker": "AAA", "account_id": "PA1", "mode": "test"},
        ]
    )
    flagged = detect_ledger_contamination(df, production_account="PA1")
    assert flagged.shape[0] == 1
    assert "mode_test" in flagged.iloc[0]["contamination_reason"]


def test_known_test_symbols_flagged():
    df = pd.DataFrame(
        [
            {"trade_id": "BOWAKA-T0-1", "ticker": "T0", "account_id": "PA1"},
        ]
    )
    flagged = detect_ledger_contamination(df)
    assert flagged.shape[0] == 1


def test_clean_ledger_not_flagged():
    df = pd.DataFrame(
        [
            {"trade_id": "BOWAKA-AAA-1001", "ticker": "AAA", "account_id": "PA1"},
            {"trade_id": "BOWAKA-BBB-1002", "ticker": "BBB", "account_id": "PA1"},
        ]
    )
    flagged = detect_ledger_contamination(df, production_account="PA1")
    assert flagged.empty
