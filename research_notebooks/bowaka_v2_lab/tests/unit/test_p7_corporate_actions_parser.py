"""P7 §3.4/§5.3 — corporate-actions parser (pure logic over the REAL Alpaca shape).

Event shapes captured live from ``GET /v1beta1/corporate-actions`` (no-symbols
window query, 2024-06-03..14). Pins that the normaliser keys each event on the
AFFECTED symbol, picks a canonical ``effective_date``, and classifies delisting /
symbol-change / split — the contract the PIT/survivorship master builder relies on.
"""
from __future__ import annotations

from bowaka_common.marketdata.corporate_actions import (
    CA_COLUMNS,
    normalise_ca_event,
    parse_corporate_actions_response,
)

# Real response shape (Alpaca, 2024-06-03..14 window, no symbols filter).
_RESP = {
    "corporate_actions": {
        "forward_splits": [{
            "cusip": "032095101", "due_bill_redemption_date": "2024-06-12",
            "ex_date": "2024-06-12", "id": "da0693c2", "new_rate": 2, "old_rate": 1,
            "payable_date": "2024-06-11", "process_date": "2024-06-12",
            "record_date": "2024-05-31", "symbol": "APH",
        }],
        "reverse_splits": [{
            "ex_date": "2024-06-12", "id": "68cd8942", "new_cusip": "06777U200",
            "new_rate": 1, "old_cusip": "06777U101", "old_rate": 100,
            "payable_date": "2024-06-12", "process_date": "2024-06-12",
            "record_date": "2024-06-12", "symbol": "BNED",
        }],
        "name_changes": [{
            "id": "76d6dc2b", "new_cusip": "06777U101", "new_symbol": "BNED",
            "old_cusip": "067BAS012", "old_symbol": "067BAS012", "process_date": "2024-06-11",
        }],
        "cash_mergers": [{
            "acquiree_cusip": "358CVR025", "acquiree_symbol": "358CVR025",
            "effective_date": "2024-06-04", "id": "8bf3ce03", "payable_date": "2024-06-04",
            "process_date": "2024-06-04", "rate": 0.01895669,
        }],
        "spin_offs": [{
            "ex_date": "2024-06-03", "id": "48ec8707", "new_cusip": "007975113",
            "new_rate": 0.47698, "new_symbol": "007975113", "process_date": "2024-06-03",
            "record_date": "2024-05-31", "source_cusip": "007975600", "source_rate": 1,
            "source_symbol": "AEZS",
        }],
        "worthless_removals": [{
            "cusip": "067RGT019", "id": "84141642", "process_date": "2024-06-13",
            "symbol": "067RGT019",
        }],
        "cash_dividends": [{
            "cusip": "037833100", "ex_date": "2024-08-12", "foreign": False,
            "id": "522935ff", "payable_date": "2024-08-15", "process_date": "2024-08-15",
            "rate": 0.25, "record_date": "2024-08-09", "symbol": "AAPL",
        }],
    },
    "next_page_token": None,
}


def _by_type(rows: list[dict]) -> dict[str, dict]:
    return {r["ca_type"]: r for r in rows}


def test_parser_flattens_all_types_with_stable_columns() -> None:
    rows = parse_corporate_actions_response(_RESP)
    assert len(rows) == 7
    for r in rows:
        assert set(r.keys()) == set(CA_COLUMNS), r
        assert r["symbol"]                    # every row resolves an affected symbol
        assert r["effective_date"]            # and a canonical effective date


def test_forward_and_reverse_splits_classified() -> None:
    rows = _by_type(parse_corporate_actions_response(_RESP))
    fwd = rows["forward_splits"]
    assert fwd["symbol"] == "APH" and fwd["is_split"] is True
    assert fwd["effective_date"] == "2024-06-12"          # ex_date is the split date
    assert fwd["old_rate"] == 1 and fwd["new_rate"] == 2
    assert fwd["is_delisting"] is False and fwd["is_symbol_change"] is False
    rev = rows["reverse_splits"]
    assert rev["symbol"] == "BNED" and rev["is_split"] is True
    assert rev["old_rate"] == 100 and rev["new_rate"] == 1


def test_name_change_keys_old_symbol_and_carries_new() -> None:
    nc = _by_type(parse_corporate_actions_response(_RESP))["name_changes"]
    assert nc["symbol"] == "067BAS012"          # keyed on the PRE-change symbol
    assert nc["new_symbol"] == "BNED"
    assert nc["is_symbol_change"] is True and nc["is_delisting"] is False
    assert nc["effective_date"] == "2024-06-11"  # process_date (no ex_date on a rename)


def test_cash_merger_delists_the_acquiree() -> None:
    m = _by_type(parse_corporate_actions_response(_RESP))["cash_mergers"]
    assert m["symbol"] == "358CVR025"            # the (delisted) acquiree, not the acquirer
    assert m["is_delisting"] is True
    assert m["effective_date"] == "2024-06-04"   # effective_date (no ex_date on a merger)


def test_worthless_removal_is_a_delisting() -> None:
    w = _by_type(parse_corporate_actions_response(_RESP))["worthless_removals"]
    assert w["symbol"] == "067RGT019" and w["is_delisting"] is True
    assert w["effective_date"] == "2024-06-13"   # process_date


def test_spin_off_keys_source_not_a_delisting() -> None:
    s = _by_type(parse_corporate_actions_response(_RESP))["spin_offs"]
    assert s["symbol"] == "AEZS"                 # source continues (NOT delisted)
    assert s["is_delisting"] is False and s["is_split"] is False
    assert s["new_symbol"] == "007975113"        # the spun-off entity


def test_cash_dividend_is_neither_delisting_split_nor_rename() -> None:
    d = _by_type(parse_corporate_actions_response(_RESP))["cash_dividends"]
    assert d["symbol"] == "AAPL" and d["rate"] == 0.25
    assert not (d["is_delisting"] or d["is_split"] or d["is_symbol_change"])


def test_unusable_event_without_symbol_is_dropped() -> None:
    # A merger row with no acquiree symbol resolves no affected symbol -> dropped.
    assert normalise_ca_event("cash_mergers", {"effective_date": "2024-06-04", "rate": 1.0}) is None
    assert parse_corporate_actions_response({"corporate_actions": {}}) == []
    assert parse_corporate_actions_response({}) == []
