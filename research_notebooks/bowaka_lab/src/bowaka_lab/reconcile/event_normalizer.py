"""Normalize paper-log events to a stable schema with dedup-safe event_key.

Event key tuple (per ``[Report §E.2]``):

    (event_type, link_id_or_trade_id, order_id, timestamp, status,
     filled_qty, fill_price)
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def _coerce(v: Any) -> Any:
    if pd.isna(v) if not isinstance(v, (list, dict)) else False:
        return None
    return v


def event_key(event: dict) -> tuple:
    et = event.get("event_type") or event.get("record_type")
    lid = event.get("link_id") or event.get("trade_id")
    oid = event.get("order_id") or (event.get("payload") or {}).get("order_id")
    ts = event.get("ts") or event.get("timestamp")
    status = event.get("status") or (event.get("payload") or {}).get("status")
    filled_qty = event.get("filled_qty") or (event.get("payload") or {}).get("filled_qty")
    fill_price = event.get("fill_price") or (event.get("payload") or {}).get("fill_price")
    return (_coerce(et), _coerce(lid), _coerce(oid), _coerce(ts), _coerce(status), _coerce(filled_qty), _coerce(fill_price))


def normalize_paper_events(events_df: pd.DataFrame) -> pd.DataFrame:
    """Add canonical columns and a deduplicated event_key column.

    Result keeps the first occurrence of each event_key.
    """
    if events_df.empty:
        return events_df

    df = events_df.copy()
    if "event_key" not in df.columns:
        df["event_key"] = df.apply(lambda r: event_key(r.to_dict()), axis=1)

    canonical_lid = df.get("link_id")
    if canonical_lid is None:
        canonical_lid = df.get("trade_id")
    if canonical_lid is not None:
        df["canonical_link_id"] = canonical_lid
    if "ts" not in df.columns and "timestamp" in df.columns:
        df["ts"] = df["timestamp"]
    df = df.drop_duplicates(subset=["event_key"], keep="first").reset_index(drop=True)
    return df
