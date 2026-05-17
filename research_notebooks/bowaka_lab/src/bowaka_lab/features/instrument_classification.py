"""Instrument-class classifier mirroring ``bowaka_prefilter.classify_instrument``.

Order of precedence (per ``[Report §11]`` and legacy ``classify_instrument``):

1. ``ticker_blocklist`` (legacy uses "leveraged_etp" label for blocked tickers).
2. Name keyword scan in order ``leveraged → inverse → etn``; first match wins.
3. ``asset_class == etf`` → label etf.
4. Default: operating_equity.

The output dict carries ``instrument_class``,
``eligible_for_bowaka_equity_bucket`` (False for any non-operating class),
and a ``classification_reason`` string usable for diagnostic CSVs.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_NAME_KEYWORDS: dict[str, list[str]] = {
    "leveraged": ["2X", "3X", "BULL", "BEAR", "DAILY", "LEVERAGED"],
    "inverse": ["INVERSE", "SHORT", "BEAR"],
    "etn": ["ETN"],
}


@dataclass
class InstrumentClassification:
    instrument_class: str
    eligible_for_bowaka_equity_bucket: bool
    classification_reason: str


def classify_instrument(
    symbol: str,
    *,
    name: str | None = None,
    asset_class: str | None = None,
    ticker_blocklist: list[str] | None = None,
    name_keywords: dict[str, list[str]] | None = None,
) -> InstrumentClassification:
    ticker = (symbol or "").upper()
    name_upper = (name or "").upper()
    block = set((ticker_blocklist or []))
    kw = name_keywords or DEFAULT_NAME_KEYWORDS

    if ticker in block:
        return InstrumentClassification(
            instrument_class="leveraged_etp",
            eligible_for_bowaka_equity_bucket=False,
            classification_reason="ticker_blocklist",
        )

    for cls, label in (
        ("leveraged", "leveraged_etp"),
        ("inverse", "inverse_etp"),
        ("etn", "etn"),
    ):
        for token in kw.get(cls, []) or []:
            t = str(token).upper().strip()
            if t and t in name_upper:
                return InstrumentClassification(
                    instrument_class=label,
                    eligible_for_bowaka_equity_bucket=False,
                    classification_reason=f"name_keyword:{cls}:{t}",
                )

    asset_class_lower = (asset_class or "").lower()
    if asset_class_lower in {"etf", "us_etf"}:
        return InstrumentClassification(
            instrument_class="etf",
            eligible_for_bowaka_equity_bucket=False,
            classification_reason="asset_class:etf",
        )

    return InstrumentClassification(
        instrument_class="operating_equity",
        eligible_for_bowaka_equity_bucket=True,
        classification_reason="default_operating_equity",
    )
