"""P7 §3.4/§5.3 — real point-in-time / survivorship asset master.

Derives, per symbol, a listing / delisting / rename timeline from the normalised
corporate-actions stream (``bowaka_common.marketdata.corporate_actions`` + the
``corporate_actions/`` lake partition) plus per-symbol first-bar dates, REPLACING the
single future-dated asset-master snapshot. The universe builder queries it as-of each
session date so a backtest never trades a name before it listed, after it delisted, or
after it was renamed away (the silent survivorship hole this closes).

PIT HAZARD (flagged loudly — §5.3): Alpaca gives NO guarantee on a CA's announcement /
creation time, so this master is keyed on the EFFECTIVE date (ex / effective /
process), NOT the point-in-time the market first KNEW. A delisting/rename therefore
takes effect in the sim on its effective date, which is conservative for entry (a
soon-to-delist name stays tradable until the effective date) — acceptable + documented
here rather than silently presented as true announcement-time PIT. To get true PIT one
must snapshot the CA table daily; until then this is ex/effective-date survivorship.
"""
from __future__ import annotations

import datetime as _dt
import logging
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional

logger = logging.getLogger(__name__)

#: One-line PIT-hazard banner surfaced (once) when a master is built from CA data.
CA_PIT_HAZARD = (
    "PIT-master survivorship is EFFECTIVE-DATE based (ex/effective/process), NOT "
    "announcement-time PIT — Alpaca exposes no CA creation time. Conservative for "
    "entry; document as ex/effective-date survivorship (§5.3)."
)


def _to_date(v: Any) -> Optional[_dt.date]:
    if v is None or v == "":
        return None
    if isinstance(v, _dt.date) and not isinstance(v, _dt.datetime):
        return v
    if isinstance(v, _dt.datetime):
        return v.date()
    try:
        s = str(v)[:10]
        y, m, d = s.split("-")
        return _dt.date(int(y), int(m), int(d))
    except Exception:  # noqa: BLE001 — unparseable date -> unknown
        return None


@dataclass
class PitSymbolRecord:
    """A symbol's point-in-time lifecycle derived from corporate actions + bar data."""

    symbol: str
    listing_date: Optional[_dt.date] = None       # first known trading day (data start)
    delisting_date: Optional[_dt.date] = None     # CA delisting effective date (None = live)
    delisting_reason: Optional[str] = None        # ca_type of the delisting event
    renamed_to: Optional[str] = None              # successor symbol after a name change
    rename_date: Optional[_dt.date] = None        # effective date of the rename-away
    renamed_from: Optional[str] = None            # predecessor symbol (rename-in)
    last_bar_date: Optional[_dt.date] = None       # last bar seen (data-coverage end)

    def status_as_of(self, on: _dt.date) -> str:
        """``not_yet_listed`` | ``renamed_away`` | ``delisted`` | ``active`` as of ``on``."""
        if self.listing_date is not None and on < self.listing_date:
            return "not_yet_listed"
        # A rename-away ends this symbol's identity; the successor carries on.
        if self.rename_date is not None and on >= self.rename_date:
            return "renamed_away"
        if self.delisting_date is not None and on >= self.delisting_date:
            return "delisted"
        return "active"

    def is_active_as_of(self, on: _dt.date) -> bool:
        return self.status_as_of(on) == "active"

    def eligible_as_of(
        self, on: _dt.date, *, trading_days_available: Optional[int] = None,
        min_history_trading_days: int = 0,
    ) -> tuple[bool, Optional[str]]:
        """``(eligible, reason)`` — active as-of ``on`` AND (when a count is given)
        carrying at least ``min_history_trading_days`` of prior history.

        ``trading_days_available`` is the count of the symbol's daily bars STRICTLY
        before ``on`` (the caller — universe builder — computes it from the daily
        history it already reads). ``None`` skips the history gate (legacy-safe)."""
        status = self.status_as_of(on)
        if status != "active":
            return False, status
        if (min_history_trading_days and trading_days_available is not None
                and trading_days_available < int(min_history_trading_days)):
            return False, "insufficient_history"
        return True, None


@dataclass
class PitMaster:
    """Per-symbol :class:`PitSymbolRecord` map with as-of queries (§3.4/§5.3)."""

    records: dict[str, PitSymbolRecord] = field(default_factory=dict)

    def get(self, symbol: str) -> Optional[PitSymbolRecord]:
        return self.records.get(str(symbol))

    def status_as_of(self, symbol: str, on: _dt.date) -> str:
        rec = self.records.get(str(symbol))
        # Unknown symbol: no survivorship record -> treat as not-listed (fail-closed,
        # the OPPOSITE of the _status_active("") blank-is-active bug this replaces).
        return rec.status_as_of(on) if rec is not None else "unknown"

    def is_active_as_of(self, symbol: str, on: _dt.date) -> bool:
        return self.status_as_of(symbol, on) == "active"

    def eligible_as_of(
        self, symbol: str, on: _dt.date, *, trading_days_available: Optional[int] = None,
        min_history_trading_days: int = 0,
    ) -> tuple[bool, Optional[str]]:
        rec = self.records.get(str(symbol))
        if rec is None:
            return False, "unknown"
        return rec.eligible_as_of(
            on, trading_days_available=trading_days_available,
            min_history_trading_days=min_history_trading_days,
        )


def build_pit_master(
    ca_rows: Iterable[Mapping[str, Any]],
    *,
    listing_dates: Optional[Mapping[str, Any]] = None,
    last_bar_dates: Optional[Mapping[str, Any]] = None,
    warn_hazard: bool = True,
) -> PitMaster:
    """Build a :class:`PitMaster` from normalised CA rows + per-symbol bar dates.

    ``ca_rows`` are :data:`bowaka_common.marketdata.corporate_actions.CA_COLUMNS`
    dicts (e.g. ``store.all_corporate_actions().to_dict("records")``). ``listing_dates``
    / ``last_bar_dates`` map symbol -> first / last daily-bar date (data coverage).
    Earliest delisting effective date wins; the earliest rename-away sets the identity
    cutover. Emits the :data:`CA_PIT_HAZARD` banner once (``warn_hazard``).
    """
    if warn_hazard:
        logger.warning(CA_PIT_HAZARD)
    listing_dates = {str(k): _to_date(v) for k, v in (listing_dates or {}).items()}
    last_bar_dates = {str(k): _to_date(v) for k, v in (last_bar_dates or {}).items()}

    rows = [dict(r) for r in ca_rows]
    symbols: set[str] = set(listing_dates) | set(last_bar_dates)
    for r in rows:
        for k in ("symbol", "new_symbol"):
            v = r.get(k)
            if v:
                symbols.add(str(v))

    records: dict[str, PitSymbolRecord] = {
        s: PitSymbolRecord(
            symbol=s, listing_date=listing_dates.get(s), last_bar_date=last_bar_dates.get(s),
        )
        for s in symbols
    }

    for r in rows:
        sym = r.get("symbol")
        if not sym:
            continue
        sym = str(sym)
        rec = records.get(sym)
        if rec is None:
            rec = records[sym] = PitSymbolRecord(symbol=sym)
        eff = _to_date(r.get("effective_date"))
        if r.get("is_delisting") and eff is not None:
            if rec.delisting_date is None or eff < rec.delisting_date:
                rec.delisting_date = eff
                rec.delisting_reason = str(r.get("ca_type") or "delisted")
        if r.get("is_symbol_change"):
            new_sym = r.get("new_symbol")
            if new_sym and eff is not None:
                if rec.rename_date is None or eff < rec.rename_date:
                    rec.rename_date = eff
                    rec.renamed_to = str(new_sym)
                succ = records.get(str(new_sym))
                if succ is None:
                    succ = records[str(new_sym)] = PitSymbolRecord(symbol=str(new_sym))
                succ.renamed_from = sym
                # The successor lists no later than the rename effective date.
                if succ.listing_date is None or eff < succ.listing_date:
                    succ.listing_date = succ.listing_date or eff

    return PitMaster(records=records)


__all__ = ["PitSymbolRecord", "PitMaster", "build_pit_master", "CA_PIT_HAZARD"]
