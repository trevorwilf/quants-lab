"""Corporate-actions normaliser (P7 §3.4/§5.3 — survivorship + adjustment source).

Pure parser over the real Alpaca ``GET /v1beta1/corporate-actions`` response (the
``symbols`` query param is OPTIONAL, so the producer fetches the WHOLE CA stream by
window — required for survivorship, because a renamed/merged/removed symbol is no
longer in the current universe). The response groups events by type::

    {"corporate_actions": {
        "forward_splits":     [{symbol, ex_date, old_rate, new_rate, ...}],
        "reverse_splits":     [{symbol, ex_date, old_rate, new_rate, ...}],
        "cash_dividends":     [{symbol, ex_date, rate, record_date, ...}],
        "name_changes":       [{old_symbol, new_symbol, process_date, ...}],
        "cash_mergers":       [{acquiree_symbol, effective_date, rate, ...}],
        "stock_mergers":      [{acquiree_symbol, effective_date, ...}],
        "spin_offs":          [{source_symbol, new_symbol, ex_date, ...}],
        "worthless_removals": [{symbol, process_date, ...}],
        "redemptions":        [{symbol, ...}],
        ...},
     "next_page_token": ...}

:func:`parse_corporate_actions_response` flattens that into one normalised row per
event with a canonical ``effective_date`` + survivorship flags, so the PIT master
builder can derive each symbol's listing/delisting/rename timeline without knowing
every type's bespoke shape.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

#: Types that DELIST a symbol (the affected symbol stops trading). For a merger the
#: ACQUIRER survives and the ACQUIREE is delisted, so the keyed symbol is the acquiree.
DELISTING_TYPES: frozenset[str] = frozenset({
    "cash_mergers", "stock_mergers", "stock_and_cash_mergers",
    "worthless_removals", "redemptions",
})
#: Types that RENAME a symbol (the timeline continues under ``new_symbol``).
SYMBOL_CHANGE_TYPES: frozenset[str] = frozenset({"name_changes"})
#: Split / reverse-split / unit-split types (ratio = new_rate / old_rate).
SPLIT_TYPES: frozenset[str] = frozenset({"forward_splits", "reverse_splits", "unit_splits"})

#: The normalised row schema (stable column order for the parquet partition).
CA_COLUMNS: tuple[str, ...] = (
    "ca_type", "symbol", "old_symbol", "new_symbol", "effective_date", "ex_date",
    "process_date", "record_date", "payable_date", "old_rate", "new_rate", "rate",
    "cusip", "id", "is_delisting", "is_symbol_change", "is_split",
)


def _first(ev: Mapping[str, Any], *keys: str) -> Optional[Any]:
    for k in keys:
        v = ev.get(k)
        if v is not None and v != "":
            return v
    return None


def _effective_date(ev: Mapping[str, Any]) -> Optional[str]:
    """The canonical date the action takes effect (PIT ordering key).

    Splits/spin-offs use ``ex_date``; mergers use ``effective_date``; renames /
    worthless removals use ``process_date``. Falls back across them so every event
    carries a date.
    """
    d = _first(ev, "ex_date", "effective_date", "process_date", "payable_date", "record_date")
    return str(d) if d is not None else None


def _keyed_symbol(ca_type: str, ev: Mapping[str, Any]) -> Optional[str]:
    """The PRIMARY symbol the row is keyed on (the one whose timeline this affects).

    Mergers key on the (delisted) acquiree; renames on the pre-change (old) symbol;
    spin-offs on the source; everything else on ``symbol``. Delisted/obscure names
    can surface as a CUSIP-like placeholder — preserved verbatim.
    """
    if ca_type in ("cash_mergers", "stock_mergers", "stock_and_cash_mergers"):
        s = _first(ev, "acquiree_symbol", "symbol")
    elif ca_type == "name_changes":
        s = _first(ev, "old_symbol", "symbol")
    elif ca_type == "spin_offs":
        s = _first(ev, "source_symbol", "symbol")
    else:
        s = _first(ev, "symbol", "acquiree_symbol", "old_symbol", "source_symbol")
    return str(s) if s is not None else None


def normalise_ca_event(ca_type: str, ev: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """Normalise one raw CA event of ``ca_type`` to a :data:`CA_COLUMNS` row.

    Returns ``None`` when no keyed symbol can be resolved (an unusable event).
    """
    ca_type = str(ca_type)
    symbol = _keyed_symbol(ca_type, ev)
    if symbol is None:
        return None
    return {
        "ca_type": ca_type,
        "symbol": symbol,
        "old_symbol": (str(ev["old_symbol"]) if ev.get("old_symbol") else None),
        "new_symbol": (str(ev["new_symbol"]) if ev.get("new_symbol") else None),
        "effective_date": _effective_date(ev),
        "ex_date": (str(ev["ex_date"]) if ev.get("ex_date") else None),
        "process_date": (str(ev["process_date"]) if ev.get("process_date") else None),
        "record_date": (str(ev["record_date"]) if ev.get("record_date") else None),
        "payable_date": (str(ev["payable_date"]) if ev.get("payable_date") else None),
        "old_rate": _first(ev, "old_rate", "source_rate"),
        "new_rate": _first(ev, "new_rate"),
        "rate": _first(ev, "rate"),
        "cusip": _first(ev, "cusip", "acquiree_cusip", "old_cusip", "source_cusip", "new_cusip"),
        "id": (str(ev["id"]) if ev.get("id") else None),
        "is_delisting": ca_type in DELISTING_TYPES,
        "is_symbol_change": ca_type in SYMBOL_CHANGE_TYPES,
        "is_split": ca_type in SPLIT_TYPES,
    }


def parse_corporate_actions_response(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Flatten a corporate-actions response into normalised :data:`CA_COLUMNS` rows.

    Unknown/future types are preserved (flagged only if they fall in the known
    delisting/rename/split sets) so a new Alpaca CA type is never silently dropped.
    """
    out: list[dict[str, Any]] = []
    ca = (data or {}).get("corporate_actions") or {}
    if not isinstance(ca, Mapping):
        return out
    for ca_type, events in ca.items():
        if not isinstance(events, list):
            continue
        for ev in events:
            if not isinstance(ev, Mapping):
                continue
            row = normalise_ca_event(str(ca_type), ev)
            if row is not None:
                out.append(row)
    return out


__all__ = [
    "parse_corporate_actions_response", "normalise_ca_event",
    "DELISTING_TYPES", "SYMBOL_CHANGE_TYPES", "SPLIT_TYPES", "CA_COLUMNS",
]
