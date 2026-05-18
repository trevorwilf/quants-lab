"""Verbatim excerpt of source ``classify_instrument`` for parity tests.

Lifted from ``reference/source_strategy/scripts/bowaka_prefilter.py``
(lines 324-397). Importing the source module directly fails on missing
``alpaca`` deps, so only the function under test plus the
``INSTRUMENT_CLASSES`` constant are copied here. Update this file IF AND
ONLY IF the source bowaka_prefilter.py changes.
"""

from __future__ import annotations

# Phase 2.3 — instrument classification.
INSTRUMENT_CLASSES = {
    "operating_equity", "leveraged_etp", "inverse_etp", "etn",
    "etf", "preferred", "warrant", "unit", "right",
}


def classify_instrument(symbol: str, asset_meta: dict, cfg: dict) -> dict:
    """Verbatim port of bowaka_prefilter.classify_instrument."""
    rules = cfg.get("instrument_rules") or {}
    name = str(asset_meta.get("name") or "").upper()
    ticker = (symbol or "").upper()

    block = set((rules.get("ticker_blocklist") or []))
    if ticker in block:
        return {
            "instrument_class": "leveraged_etp",
            "eligible_for_bowaka_equity_bucket": False,
            "classification_reason": "ticker_blocklist",
        }

    kw = rules.get("name_keywords") or {}
    for cls, label in (
        ("leveraged", "leveraged_etp"),
        ("inverse", "inverse_etp"),
        ("etn", "etn"),
    ):
        for token in (kw.get(cls) or []):
            t = str(token).upper().strip()
            if t and t in name:
                return {
                    "instrument_class": label,
                    "eligible_for_bowaka_equity_bucket": False,
                    "classification_reason": f"name_keyword:{cls}:{t}",
                }

    asset_class = str(asset_meta.get("asset_class") or "").lower()
    if asset_class in {"etf", "us_etf"}:
        return {
            "instrument_class": "etf",
            "eligible_for_bowaka_equity_bucket": False,
            "classification_reason": "asset_class:etf",
        }

    return {
        "instrument_class": "operating_equity",
        "eligible_for_bowaka_equity_bucket": True,
        "classification_reason": "default_operating_equity",
    }
