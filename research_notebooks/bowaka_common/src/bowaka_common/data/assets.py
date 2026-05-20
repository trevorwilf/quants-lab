"""Fetch and classify Alpaca US equity assets into a snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from bowaka_common.utils.hashing import stable_hash
from bowaka_common.utils.ids import asset_snapshot_id

OPERATING_EQUITY = "operating_equity"
LEVERAGED_ETP = "leveraged_etp"
INVERSE_ETP = "inverse_etp"
ETN = "etn"
ETF = "etf"
SPAC = "spac"
PREFERRED = "preferred"
UNKNOWN = "unknown"


_LEVERAGED_HINTS = (
    "2x",
    "3x",
    "leveraged",
    "ultra",
    "ultrapro",
    "daily 2x",
    "daily 3x",
    "bull 2x",
    "bull 3x",
)
_INVERSE_HINTS = (
    "inverse",
    "short",
    "bear",
    "ultrashort",
    "ultrabear",
    "-1x",
    "-2x",
    "-3x",
    "proshares short",
)
_ETN_HINTS = ("etn", "exchange-traded note", "exchange traded note")
_ETF_HINTS = ("etf", "fund", "trust", "spdr", "ishares", "vanguard")
_SPAC_HINTS = ("acquisition corp", "acquisition corporation", "spac")
_PREFERRED_HINTS = ("preferred ", " pfd ", " preferred,")


def classify_instrument(name: str) -> tuple[str, str]:
    """Classify an asset by name. Returns (instrument_class, reason).

    Inverse hints take precedence over leveraged because instruments like
    "Direxion Daily Small Cap Bear 3X" match both ("3x" and "bear"); they are
    inverse first.
    """
    if not name:
        return OPERATING_EQUITY, "default_operating_equity"
    n = name.lower()
    if any(h in n for h in _INVERSE_HINTS):
        return INVERSE_ETP, "name_contains_inverse_hint"
    if any(h in n for h in _LEVERAGED_HINTS):
        return LEVERAGED_ETP, "name_contains_leveraged_hint"
    if any(h in n for h in _ETN_HINTS):
        return ETN, "name_contains_etn_hint"
    if any(h in n for h in _ETF_HINTS):
        return ETF, "name_contains_etf_hint"
    if any(h in n for h in _SPAC_HINTS):
        return SPAC, "name_contains_spac_hint"
    if any(h in n for h in _PREFERRED_HINTS):
        return PREFERRED, "name_contains_preferred_hint"
    return OPERATING_EQUITY, "default_operating_equity"


def normalize_symbol_key(symbol: str) -> str:
    """Bowaka uses canonical uppercase symbols; class-share dots replaced by `-`."""
    if symbol is None:
        return ""
    return symbol.strip().upper().replace(".", "-")


@dataclass
class AssetRow:
    snapshot_id: str
    symbol: str
    symbol_key: str
    name: str
    exchange: str
    venue_code: str
    asset_class: str
    tradable: bool
    marginable: bool
    shortable: bool
    fractionable: bool
    status: str
    instrument_class: str
    classification_reason: str


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _exchange_to_venue(exchange: str | None) -> str:
    if not exchange:
        return ""
    e = exchange.upper()
    return {
        "NASDAQ": "XNAS",
        "NYSE": "XNYS",
        "ARCA": "ARCX",
        "AMEX": "XASE",
        "BATS": "BATS",
        "OTC": "OTCM",
    }.get(e, e)


def build_asset_snapshot(
    raw_assets: Iterable[Any],
    *,
    vendor: str = "alpaca",
    captured_at: datetime | None = None,
    allowed_exchanges: list[str] | None = None,
) -> tuple[dict, list[AssetRow]]:
    """Build (snapshot_metadata, asset_rows) from a sequence of Alpaca assets.

    ``raw_assets`` may contain dataclass-like objects with attribute access or
    plain dicts. The function does not call out to Alpaca; the caller is
    expected to fetch the list via ``AlpacaClient.call(trading.get_all_assets, ...)``.
    """
    captured_at = captured_at or datetime.now(timezone.utc)
    snap_id = asset_snapshot_id(vendor=vendor, captured_at=captured_at)

    rows: list[AssetRow] = []
    allowed = {e.upper() for e in (allowed_exchanges or [])} if allowed_exchanges else None
    for raw in raw_assets:
        exchange = str(_get(raw, "exchange", "") or "")
        if isinstance(exchange, str) and exchange.startswith("AssetExchange."):
            exchange = exchange.split(".", 1)[1]
        if allowed and exchange.upper() not in allowed:
            continue
        symbol = str(_get(raw, "symbol", "") or "")
        if not symbol:
            continue
        status = _get(raw, "status", "")
        status_str = status.value if hasattr(status, "value") else str(status)
        asset_class = _get(raw, "asset_class", "us_equity")
        asset_class_str = asset_class.value if hasattr(asset_class, "value") else str(asset_class)
        name = str(_get(raw, "name", "") or "")
        ic, reason = classify_instrument(name)
        rows.append(
            AssetRow(
                snapshot_id=snap_id,
                symbol=symbol,
                symbol_key=normalize_symbol_key(symbol),
                name=name,
                exchange=exchange,
                venue_code=_exchange_to_venue(exchange),
                asset_class=asset_class_str,
                tradable=bool(_get(raw, "tradable", False)),
                marginable=bool(_get(raw, "marginable", False)),
                shortable=bool(_get(raw, "shortable", False)),
                fractionable=bool(_get(raw, "fractionable", False)),
                status=status_str,
                instrument_class=ic,
                classification_reason=reason,
            )
        )

    asset_hash = stable_hash([r.__dict__ for r in rows])
    metadata = {
        "snapshot_id": snap_id,
        "vendor": vendor,
        "created_at": captured_at.isoformat(),
        "allowed_exchanges": sorted(list(allowed)) if allowed else None,
        "asset_count": len(rows),
        "asset_hash": asset_hash,
        "source": "alpaca_trading_assets",
        "notes": "Current asset universe. Survivorship-biased for historical backtests.",
    }
    return metadata, rows


def assets_to_dataframe(rows: list[AssetRow]) -> pd.DataFrame:
    return pd.DataFrame([r.__dict__ for r in rows])


def load_latest_asset_snapshot(data_root: Path | str) -> pd.DataFrame:
    """Load the most-recent asset_snapshot parquet under ``data_root``.

    Looks for files under ``<data_root>/parquet/assets/vendor=alpaca/snapshot_id=*/assets.parquet``,
    matching the layout from ``db_tools/_backfill_lib.py::assets_file``.

    Sort key: the partition mtime, then the snapshot_id (lexicographic) as a
    tie-breaker. Returns an empty DataFrame with the expected columns when no
    snapshot is present so callers can branch on ``snapshot.empty`` without
    handling ``FileNotFoundError`` separately.

    Attaches ``snapshot_id`` to the returned DataFrame's ``attrs`` so the
    prefilter persistence path can lineage-tag candidates with it.
    """
    data_root = Path(data_root)
    assets_root = data_root / "parquet" / "assets" / "vendor=alpaca"
    snapshot_files = sorted(
        assets_root.glob("snapshot_id=*/assets.parquet"),
        key=lambda p: (p.stat().st_mtime if p.exists() else 0, p.parent.name),
    )
    if not snapshot_files:
        empty = pd.DataFrame(
            columns=[
                "snapshot_id", "symbol", "symbol_key", "name", "exchange",
                "venue_code", "asset_class", "tradable", "marginable", "shortable",
                "fractionable", "status", "instrument_class", "classification_reason",
            ]
        )
        empty.attrs["snapshot_id"] = ""
        return empty
    latest = snapshot_files[-1]
    df = pd.read_parquet(latest)
    snapshot_id = latest.parent.name.split("=", 1)[1] if "=" in latest.parent.name else ""
    df.attrs["snapshot_id"] = snapshot_id
    return df
