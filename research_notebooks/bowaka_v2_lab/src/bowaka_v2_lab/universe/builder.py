"""Point-in-time universe builder (realism remediation Phase 3).

Replaces the synthetic ``synthetic_universe(symbols)`` fan-out with a daily
*point-in-time* universe built from the shared lake's asset snapshot plus
**prior-day** daily bars. The live universe filters (audit ref P0-005, the
frozen contract ``universe`` block) are applied in a fixed order; every
rejection is recorded on the per-symbol :class:`UniverseRecord`.

No current-day leakage
----------------------
``prior_close`` and ``prior_avg_dollar_volume_20d`` are computed **only** from
daily bars dated *strictly before* the session date. The session's own bar is
never read. Flipping the session-day price or volume cannot change which
symbols are eligible — see ``tests/unit/test_universe_no_leakage.py``.

Instrument-class heuristic
--------------------------
The lake asset master has no instrument-class field (``asset_class`` is
``us_equity`` for every row). ETF / ETN / leveraged / inverse / warrant / unit /
right / preferred symbols therefore cannot be identified from the master; this
module classifies them with a **heuristic** over the asset ``name`` (and a small
symbol-suffix rule for warrants / units / rights). A heuristic-classified symbol
gets ``instrument_class = "heuristic"`` and is treated as ``unknown`` for the
gate, honouring the Phase-0 ``simulation.unknown_instrument_class_policy``:
``fail_open`` keeps it, ``fail_closed`` excludes it with reason
``unknown_instrument_class``. Symbols the heuristic positively recognises as an
excluded class are excluded with ``excluded_instrument_class`` regardless of the
policy (the contract excludes those classes outright).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional

import pandas as pd

# --------------------------------------------------------------------------
# Contract-derived defaults (frozen contract `universe` block / P0-005).
# --------------------------------------------------------------------------
#: Exchanges the live universe admits.
DEFAULT_ALLOWED_EXCHANGES: tuple[str, ...] = ("NASDAQ", "NYSE", "AMEX", "ARCA", "BATS")
#: Exchange codes treated as OTC (always excluded).
_OTC_EXCHANGES: frozenset[str] = frozenset({"OTC", "OTCBB", "OTCM", "OTCMKTS", "PINK"})
#: Live ticker blocklist (additive with any ``cfg`` entries).
DEFAULT_TICKER_BLOCKLIST: tuple[str, ...] = ("TSLL", "CONL", "SMCX")
DEFAULT_PRICE_MIN: float = 1.0
DEFAULT_PRICE_MAX: float = 20.0
DEFAULT_ADV_MIN: float = 250_000.0

#: Exchange → MIC venue code.
_VENUE_CODE_BY_EXCHANGE: dict[str, str] = {
    "NASDAQ": "XNAS",
    "NYSE": "XNYS",
    "AMEX": "XASE",
    "ARCA": "ARCX",
    "BATS": "BATS",
}

#: Daily-bar lookback window when reading the lake for prior baselines.
_DAILY_LOOKBACK_DAYS: int = 400
#: Trailing sessions averaged for ``prior_avg_dollar_volume_20d``.
_ADV_WINDOW: int = 20


# --------------------------------------------------------------------------
# Instrument-class heuristic.
# --------------------------------------------------------------------------
#: Name-keyword → instrument class. Order matters: leveraged / inverse before
#: the generic ETF/ETN tokens so a "Direxion Daily ... Bull 2X" name lands as
#: leveraged_etp, not etf. Each pattern is matched against the upper-cased,
#: space-padded asset name (so " R " etc. match standalone words).
_NAME_KEYWORD_RULES: tuple[tuple[str, str], ...] = (
    # Inverse first: "UltraShort"/"-1X" etc. mark an inverse ETP even though
    # they also contain a leveraged token ("Ultra"). A genuine inverse fund
    # must not be mis-classed as plain leveraged.
    ("inverse_etp", r"\b(?:INVERSE|ULTRASHORT|ULTRA SHORT)\b|\bBEAR\b|\bSHORT\b"
                    r"|(?<![A-Z0-9])-(?:1|1\.5|2|3)X\b"),
    ("leveraged_etp", r"\b(?:1\.5X|2X|3X|ULTRA|ULTRAPRO|BULL|LEVERAGED)\b"),
    ("etn", r"\b(?:ETN|EXCHANGE TRADED NOTE|EXCHANGE-TRADED NOTE)\b|\bNOTES?\b"),
    ("etf", r"\b(?:ETF|EXCHANGE TRADED FUND|EXCHANGE-TRADED FUND|INDEX FUND)\b"),
    ("preferred", r"\b(?:PREFERRED|PFD|DEPOSITARY SHARES?)\b"),
    ("warrant", r"\bWARRANTS?\b"),
    ("unit", r"\bUNITS?\b"),
    ("right", r"\bRIGHTS?\b"),
)
#: Issuer/family tokens that mark a pooled-investment vehicle (ETF/ETP/ETN).
#: These families issue exclusively funds, so a name containing one is an ETF
#: even when it lacks the literal "ETF" token.
_ETF_FAMILY_RULES: tuple[tuple[str, str], ...] = (
    ("leveraged_etp", r"\b(?:DIREXION|PROSHARES ULTRA|GRANITESHARES \d)\b"),
    ("etf", r"\b(?:ISHARES|PROSHARES|SPDR|VANGUARD|INVESCO QQQ|WISDOMTREE|"
            r"GLOBAL X|FIRST TRUST|VANECK|ARK |ARKK|GRANITESHARES|"
            r"DEFIANCE|ROUNDHILL|SIMPLIFY|YIELDMAX)\b"),
)
_NAME_KEYWORD_COMPILED: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (cls, re.compile(pat)) for cls, pat in _NAME_KEYWORD_RULES
)
_ETF_FAMILY_COMPILED: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (cls, re.compile(pat)) for cls, pat in _ETF_FAMILY_RULES
)

#: Symbol-suffix → instrument class. Alpaca encodes warrant / unit / right
#: share classes with these trailing letters (e.g. ``AACBR`` = AACB rights,
#: ``AACIW`` = AACI warrants, ``AACBU`` = AACB units). A 5th-letter suffix is
#: only treated as a class marker when the symbol is >= 5 chars (so a genuine
#: 1-4 char ticker ending in W/U/R is never mis-classed) AND the name does not
#: read as an operating company; see :func:`classify_instrument`.
_SYMBOL_SUFFIX_CLASS: dict[str, str] = {"W": "warrant", "U": "unit", "R": "right"}

#: Instrument classes excluded by the live contract universe block.
_EXCLUDED_CLASSES: frozenset[str] = frozenset(
    {"etf", "leveraged_etp", "inverse_etp", "etn", "warrant", "unit", "right", "preferred"}
)
#: The one tradable class.
_OPERATING_EQUITY = "operating_equity"
#: Heuristic / unknown sentinel.
_HEURISTIC = "heuristic"


def classify_instrument(symbol: str, name: str) -> tuple[str, str]:
    """Heuristically classify a US-equity symbol.

    Returns ``(instrument_class, basis)`` where ``basis`` is one of
    ``"name_keyword"``, ``"etf_family"``, ``"symbol_suffix"`` or ``"default"``.

    The asset master carries no instrument-class field, so this is a best-effort
    heuristic. A symbol whose name positively matches an excluded-class keyword
    is returned with that concrete class. A symbol matched only by the
    symbol-suffix rule (an ambiguous signal) is returned as :data:`_HEURISTIC`
    so the caller can apply the unknown-class policy. Everything else defaults
    to :data:`_OPERATING_EQUITY`.
    """
    upper_name = " " + str(name or "").upper().strip() + " "
    ticker = str(symbol or "").upper().strip()

    # 1. Name keywords — strongest signal, concrete class.
    for cls, pattern in _NAME_KEYWORD_COMPILED:
        if pattern.search(upper_name):
            return cls, "name_keyword"

    # 2. Issuer/family tokens — pooled-vehicle issuers, concrete class.
    for cls, pattern in _ETF_FAMILY_COMPILED:
        if pattern.search(upper_name):
            return cls, "etf_family"

    # 3. Symbol-suffix heuristic — ambiguous; flag as heuristic/unknown.
    #    Only for >=5-char symbols (Alpaca's warrant/unit/right convention).
    if len(ticker) >= 5 and ticker[-1] in _SYMBOL_SUFFIX_CLASS:
        # Guard: if the name clearly reads as an operating company
        # ("INC", "CORP", "CO", "LTD", "PLC", "GROUP", "HOLDINGS" without a
        # warrant/unit/right token) keep it as operating equity. The suffix
        # letter is then incidental, not a class marker.
        looks_operating = re.search(
            r"\b(?:INC|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|PLC|"
            r"GROUP|HOLDINGS?|TECHNOLOGIES|INDUSTRIES)\b",
            upper_name,
        )
        has_class_word = re.search(r"\b(?:WARRANT|UNIT|RIGHT)S?\b", upper_name)
        if not looks_operating or has_class_word:
            return _HEURISTIC, "symbol_suffix"

    return _OPERATING_EQUITY, "default"


# --------------------------------------------------------------------------
# Universe record.
# --------------------------------------------------------------------------
@dataclass
class UniverseRecord:
    """One symbol's point-in-time universe entry for a session.

    ``eligible_for_bowaka_equity_bucket`` is True only when ``rejection_reasons``
    is empty. ``instrument_class`` is one of the concrete classes, ``heuristic``
    (symbol-suffix-only signal, treated as unknown) or ``operating_equity``.
    """

    symbol: str
    instrument_class: str
    venue_code: str
    prior_close: Optional[float]
    prior_avg_dollar_volume_20d: Optional[float]
    eligible_for_bowaka_equity_bucket: bool
    rejection_reasons: list[str] = field(default_factory=list)
    as_of_assets_snapshot_id: Optional[str] = None
    #: How ``instrument_class`` was derived (forensics; not part of the gate).
    classification_basis: str = "default"
    #: Exchange code from the asset master (forensics / artifact column).
    exchange: Optional[str] = None


# --------------------------------------------------------------------------
# Config extraction.
# --------------------------------------------------------------------------
def _universe_cfg(cfg: Mapping[str, Any]) -> dict[str, Any]:
    """The ``universe`` config section as a plain dict (never None)."""
    return dict((cfg.get("universe") if cfg else None) or {})


def _allowed_exchanges(ucfg: Mapping[str, Any]) -> set[str]:
    raw = ucfg.get("allowed_exchanges")
    if not raw:
        return {e.upper() for e in DEFAULT_ALLOWED_EXCHANGES}
    return {str(e).upper() for e in raw}


def _ticker_blocklist(ucfg: Mapping[str, Any]) -> set[str]:
    block = {t.upper() for t in DEFAULT_TICKER_BLOCKLIST}
    for extra in ucfg.get("ticker_blocklist") or []:
        block.add(str(extra).upper())
    return block


def _price_band(ucfg: Mapping[str, Any]) -> tuple[Optional[float], Optional[float]]:
    """``(price_min, price_max)`` — contract keys, with ``min_price`` aliases."""
    p_min = ucfg.get("price_min", ucfg.get("min_price", DEFAULT_PRICE_MIN))
    p_max = ucfg.get("price_max", ucfg.get("max_price", DEFAULT_PRICE_MAX))
    return (
        float(p_min) if p_min is not None else None,
        float(p_max) if p_max is not None else None,
    )


def _adv_min(ucfg: Mapping[str, Any]) -> Optional[float]:
    """``avg_dollar_volume_min`` (contract) or legacy ``min_adv_dollars``."""
    adv = ucfg.get("avg_dollar_volume_min", ucfg.get("min_adv_dollars", DEFAULT_ADV_MIN))
    return float(adv) if adv is not None else None


def _venue_code_for(exchange: Optional[str]) -> str:
    return _VENUE_CODE_BY_EXCHANGE.get(str(exchange or "").upper(), "XNAS")


# --------------------------------------------------------------------------
# Prior-day baselines (no current-day leakage).
# --------------------------------------------------------------------------
def _as_date(x: Any) -> _dt.date:
    if isinstance(x, _dt.datetime):
        return x.date()
    if isinstance(x, _dt.date):
        return x
    return pd.Timestamp(x).date()


def _prior_session_dates(df: pd.DataFrame) -> pd.Series:
    """Per-row session date for a lake daily-bar frame."""
    if "session_date" in df.columns:
        return pd.to_datetime(df["session_date"]).dt.date
    return pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date


def _compute_prior_baselines(
    daily_df: pd.DataFrame, session_date: _dt.date
) -> tuple[Optional[float], Optional[float]]:
    """``(prior_close, prior_avg_dollar_volume_20d)`` from bars *before* the session.

    Only sessions strictly earlier than ``session_date`` contribute — the
    session's own bar is never read, so there is no current-day leakage.
    Returns ``(None, None)`` when no prior bars exist.
    """
    if daily_df is None or daily_df.empty:
        return None, None
    sd = _prior_session_dates(daily_df)
    prior = daily_df.assign(_sd=sd)
    prior = prior[prior["_sd"] < session_date].sort_values("_sd")
    if prior.empty:
        return None, None
    close = prior["close"].astype(float)
    volume = prior["volume"].astype(float)
    prior_close = float(close.iloc[-1])
    prior_adv = float((close * volume).tail(_ADV_WINDOW).mean())
    return prior_close, prior_adv


# Speedup hotfix 2026-05-26 — process-local cache of each symbol's FULL daily
# history, keyed by (str(lake_store_lake_root), symbol, feed). The PIT
# universe builder calls ``lake_store.daily_bars(symbol, start, end, feed)``
# per (session × symbol); consecutive sessions share 99.5% of the
# ``_DAILY_LOOKBACK_DAYS`` window, so without this cache each fold makes
# (n_sessions × n_symbols) ≈ 134k parquet reads on the live IEX lake. With
# the cache: n_symbols ≈ 6,400 reads per (lake, feed) PER WORKER PROCESS.
# The lake is immutable within a study; a re-ingest creates a fresh process.
#: Cached payload per (lake_root, symbol, feed). ``close_x_volume`` is the
#: precomputed dollar-volume product (eliminates the broadcast multiply in
#: _compute_prior_baselines). ``session_dates`` is a numpy-aligned date
#: array so per-session mask construction is a single int comparison.
class _CachedDailyHistory:
    __slots__ = ("close", "volume", "session_dates", "close_x_volume")

    def __init__(self, df: pd.DataFrame) -> None:
        if df is None or df.empty:
            self.close = None
            self.volume = None
            self.session_dates = None
            self.close_x_volume = None
            return
        if "session_date" in df.columns:
            sd = pd.to_datetime(df["session_date"]).dt.date
        else:
            sd = (
                pd.to_datetime(df["timestamp"], utc=True)
                .dt.tz_convert("America/New_York")
                .dt.date
            )
        # Sort once by session date so iloc-tail() at the end is the last N days.
        order = sd.argsort()
        sd_sorted = sd.values[order]
        close_sorted = df["close"].astype(float).values[order]
        volume_sorted = df["volume"].astype(float).values[order]
        self.session_dates = sd_sorted
        self.close = close_sorted
        self.volume = volume_sorted
        self.close_x_volume = close_sorted * volume_sorted


_PIT_DAILY_FULL_HISTORY_CACHE: dict[tuple[str, str, str], _CachedDailyHistory] = {}


def _full_daily_history(
    lake_store: Any, symbol: str, *, feed: str,
) -> _CachedDailyHistory:
    """Cached full daily history for ``symbol`` on ``lake_store``.

    Reads ``lake_store.daily_bars(symbol, 1970-01-01, today, feed=feed)`` once
    per ``(lake_root, symbol, feed)`` triple, then returns the same compact
    payload (numpy arrays + precomputed close×volume) on subsequent calls.
    Cache is process-local — fresh worker processes start cold (intended;
    spawn workers cannot share the parent's cache).
    """
    lake_root_str = ""
    if hasattr(lake_store, "lake_root"):
        lake_root_str = str(getattr(lake_store, "lake_root"))
    elif hasattr(lake_store, "root"):
        lake_root_str = str(getattr(lake_store, "root"))
    key = (lake_root_str, str(symbol), str(feed))
    cached = _PIT_DAILY_FULL_HISTORY_CACHE.get(key)
    if cached is not None:
        return cached
    full_start = _dt.date(1970, 1, 1)
    full_end = _dt.date.today()
    try:
        df = lake_store.daily_bars(symbol, full_start, full_end, feed=feed)
    except Exception:  # noqa: BLE001
        df = pd.DataFrame()
    payload = _CachedDailyHistory(df)
    _PIT_DAILY_FULL_HISTORY_CACHE[key] = payload
    return payload


def _pit_daily_history_cache_clear() -> None:
    """Test hook: clear the per-symbol full-history cache."""
    _PIT_DAILY_FULL_HISTORY_CACHE.clear()


def _build_prior_baselines_map(
    symbols: Iterable[str],
    session_date: _dt.date,
    lake_store: Any,
    *,
    feed: str,
) -> dict[str, tuple[Optional[float], Optional[float]]]:
    """Map ``symbol -> (prior_close, prior_adv_20d)`` for one session.

    Reads the lake's daily bars over a trailing window ending the day before
    ``session_date``. A symbol with no lake bars maps to ``(None, None)``.

    Speedup hotfix 2026-05-26: backed by
    :func:`_full_daily_history` — each symbol's full daily parquet is read
    ONCE per worker, then sliced in-memory for every (session, symbol) probe.
    20× cold-start speedup on the live IEX lake.
    """
    import numpy as _np

    out: dict[str, tuple[Optional[float], Optional[float]]] = {}
    if lake_store is None:
        return {s: (None, None) for s in symbols}
    # The legacy path used start = session_date - 400d, end = session_date - 1d.
    # The compute below uses ``< session_date`` so we don't need an inclusive
    # upper bound — slice everything strictly earlier.
    for symbol in symbols:
        h = _full_daily_history(lake_store, symbol, feed=feed)
        if h.session_dates is None:
            out[symbol] = (None, None)
            continue
        # Sessions are pre-sorted; use searchsorted to find the cutoff.
        cutoff_idx = int(_np.searchsorted(h.session_dates, session_date, side="left"))
        if cutoff_idx == 0:
            out[symbol] = (None, None)
            continue
        prior_close = float(h.close[cutoff_idx - 1])
        adv_slice = h.close_x_volume[max(0, cutoff_idx - _ADV_WINDOW):cutoff_idx]
        if len(adv_slice) == 0:
            out[symbol] = (None, None)
            continue
        prior_adv = float(_np.mean(adv_slice))
        out[symbol] = (prior_close, prior_adv)
    return out


# --------------------------------------------------------------------------
# Asset-master access.
# --------------------------------------------------------------------------
def _load_asset_master(
    lake_store: Any,
) -> tuple[pd.DataFrame, Optional[str]]:
    """Return ``(asset_master_df, snapshot_id)`` from the lake store.

    Falls back to ``(empty, None)`` when no store / no snapshot is available.
    """
    if lake_store is None:
        return pd.DataFrame(), None
    snapshot_id: Optional[str] = None
    if hasattr(lake_store, "latest_snapshot_id"):
        try:
            snapshot_id = lake_store.latest_snapshot_id()
        except Exception:  # noqa: BLE001
            snapshot_id = None
    df = pd.DataFrame()
    if hasattr(lake_store, "assets"):
        try:
            df = lake_store.assets(snapshot_id)
        except Exception:  # noqa: BLE001
            df = pd.DataFrame()
    if (snapshot_id is None) and (not df.empty) and ("snapshot_id" in df.columns):
        vals = df["snapshot_id"].dropna().unique()
        if len(vals):
            snapshot_id = str(vals[0])
    return df, snapshot_id


def _status_active(status: Any) -> bool:
    s = str(status or "").strip().lower()
    return s in {"active", "active_tradable", ""}


# --------------------------------------------------------------------------
# Builder.
# --------------------------------------------------------------------------
def build_pit_universe(
    session_date: Any,
    cfg: Mapping[str, Any],
    lake_store: Any,
) -> dict[str, UniverseRecord]:
    """Build the point-in-time universe for one session.

    Filters are applied in this fixed order (each appends a rejection reason —
    the build records *all* applicable reasons, it does not short-circuit):

    1. ``allowed_exchanges`` → ``exchange_not_allowed``
    2. OTC exclusion → ``otc``
    3. instrument-class exclusion → ``excluded_instrument_class`` /
       ``unknown_instrument_class`` (the latter honours
       ``simulation.unknown_instrument_class_policy``)
    4. ticker blocklist → ``blocklist``
    5. price band on ``prior_close`` → ``price_below_min`` / ``price_above_max``
    6. ``avg_dollar_volume_min`` on ``prior_avg_dollar_volume_20d`` →
       ``adv_below_min``
    7. delisting (asset master ``status`` != active) → ``delisted``

    A symbol with no prior-day bar cannot be price/ADV gated; it is rejected
    with ``no_prior_bar``.

    Parameters
    ----------
    session_date:
        The trading session the universe is *for*. All baselines use bars
        strictly before this date.
    cfg:
        The run config (``universe`` + ``simulation`` sections are consulted).
    lake_store:
        A :class:`bowaka_common.marketdata.MarketDataStore` (or any object
        exposing ``assets`` / ``latest_snapshot_id`` / ``daily_bars``). ``None``
        yields an empty universe.

    Returns
    -------
    dict[str, UniverseRecord]
        One record per asset-master symbol, keyed by symbol.
    """
    session = _as_date(session_date)
    ucfg = _universe_cfg(cfg)
    md = dict((cfg.get("market_data") if cfg else None) or {})
    feed = str(md.get("feed", "iex"))

    # Phase-0 unknown-instrument-class policy from the simulation contract.
    from ..config.models import SimulationConfig

    sim_cfg = SimulationConfig.model_validate((cfg.get("simulation") if cfg else None) or {})
    unknown_policy = sim_cfg.unknown_instrument_class_policy  # fail_open | fail_closed

    allowed = _allowed_exchanges(ucfg)
    blocklist = _ticker_blocklist(ucfg)
    p_min, p_max = _price_band(ucfg)
    adv_min = _adv_min(ucfg)

    asset_master, snapshot_id = _load_asset_master(lake_store)
    if asset_master.empty:
        return {}

    symbols = [str(s) for s in asset_master["symbol"].tolist()]
    baselines = _build_prior_baselines_map(symbols, session, lake_store, feed=feed)

    records: dict[str, UniverseRecord] = {}
    for _, row in asset_master.iterrows():
        symbol = str(row["symbol"]).strip()
        if not symbol:
            continue
        exchange = str(row.get("exchange") or "").strip()
        name = str(row.get("name") or "")
        prior_close, prior_adv = baselines.get(symbol, (None, None))
        instrument_class, basis = classify_instrument(symbol, name)
        reasons: list[str] = []

        # 1. allowed_exchanges.
        if exchange.upper() not in allowed:
            reasons.append("exchange_not_allowed")

        # 2. OTC exclusion (also a status / exchange-code heuristic).
        if ucfg.get("exclude_otc", True) and exchange.upper() in _OTC_EXCHANGES:
            reasons.append("otc")

        # 3. instrument-class exclusion.
        if instrument_class in _EXCLUDED_CLASSES:
            reasons.append("excluded_instrument_class")
        elif instrument_class == _HEURISTIC:
            # Ambiguous (symbol-suffix-only) → treat as unknown; apply policy.
            if unknown_policy == "fail_closed":
                reasons.append("unknown_instrument_class")
            # fail_open → kept; instrument_class stays "heuristic".

        # 4. ticker blocklist.
        if symbol.upper() in blocklist:
            reasons.append("blocklist")

        # 5. price band on the PRIOR close (no current-day leakage).
        if prior_close is None:
            reasons.append("no_prior_bar")
        else:
            if p_min is not None and prior_close < p_min:
                reasons.append("price_below_min")
            if p_max is not None and prior_close > p_max:
                reasons.append("price_above_max")

        # 6. ADV minimum on the PRIOR 20d dollar volume.
        if adv_min is not None:
            if prior_adv is None:
                if "no_prior_bar" not in reasons:
                    reasons.append("adv_below_min")
            elif prior_adv < adv_min:
                reasons.append("adv_below_min")

        # 7. delisting / survivorship (asset master status as of the snapshot).
        if not _status_active(row.get("status")):
            reasons.append("delisted")

        records[symbol] = UniverseRecord(
            symbol=symbol,
            instrument_class=instrument_class,
            venue_code=_venue_code_for(exchange),
            prior_close=prior_close,
            prior_avg_dollar_volume_20d=prior_adv,
            eligible_for_bowaka_equity_bucket=(not reasons),
            rejection_reasons=reasons,
            as_of_assets_snapshot_id=snapshot_id,
            classification_basis=basis,
            exchange=exchange or None,
        )
    return records


def build_pit_universe_for_sessions(
    sessions: Iterable[Any],
    cfg: Mapping[str, Any],
    lake_store: Any,
) -> dict[_dt.date, dict[str, UniverseRecord]]:
    """Build a point-in-time universe for each session in ``sessions``.

    Returns ``{session_date: {symbol: UniverseRecord}}``. Each session is built
    independently so its baselines stay strictly prior to that session.
    """
    out: dict[_dt.date, dict[str, UniverseRecord]] = {}
    for s in sessions:
        sd = _as_date(s)
        out[sd] = build_pit_universe(sd, cfg, lake_store)
    return out


# --------------------------------------------------------------------------
# Snapshot shape + hashing (consumed by the scanner / backtester).
# --------------------------------------------------------------------------
def eligible_symbols(records: Mapping[str, UniverseRecord]) -> list[str]:
    """Sorted list of symbols eligible for the bowaka equity bucket."""
    return sorted(s for s, r in records.items() if r.eligible_for_bowaka_equity_bucket)


def universe_hash(records: Mapping[str, UniverseRecord]) -> str:
    """``sha256:<hex>`` of the sorted eligible-symbol list for a session.

    Deterministic: the same eligible set always hashes identically. Two sessions
    with the same eligible symbols share a hash even if rejected symbols differ.
    """
    payload = "\n".join(eligible_symbols(records)).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def to_scanner_snapshot(
    records: Mapping[str, UniverseRecord],
) -> dict[str, Any]:
    """Convert PIT records to the scanner's ``universe_snapshot`` dict.

    The scanner (``evaluate_one_scan`` / ``build_candidate_event``) consumes
    ``{"universe_hash", "symbols": [{symbol, exchange, venue_code,
    instrument_class, eligible_for_bowaka_equity_bucket}, ...]}``. Only
    **eligible** symbols are scanned, so only they appear here. The snapshot
    also carries a ``synthetic: False`` marker so the backtester can refuse a
    synthetic universe in non-smoke modes.
    """
    symbols: list[dict[str, Any]] = []
    for symbol in eligible_symbols(records):
        r = records[symbol]
        symbols.append(
            {
                "symbol": r.symbol,
                "exchange": r.exchange,
                "venue_code": r.venue_code,
                "instrument_class": r.instrument_class,
                "eligible_for_bowaka_equity_bucket": True,
            }
        )
    return {"universe_hash": universe_hash(records), "symbols": symbols, "synthetic": False}


def funnel(records: Mapping[str, UniverseRecord]) -> dict[str, Any]:
    """Build the per-session universe funnel: starting count + per-reason counts.

    The per-reason counts are *not* mutually exclusive — one symbol can carry
    several reasons — so they do not sum to ``starting_count``. ``eligible_count``
    is the exact number that passed every filter.
    """
    by_reason: dict[str, int] = {}
    for r in records.values():
        for reason in r.rejection_reasons:
            by_reason[reason] = by_reason.get(reason, 0) + 1
    return {
        "starting_count": len(records),
        "eligible_count": sum(
            1 for r in records.values() if r.eligible_for_bowaka_equity_bucket
        ),
        "rejected_count": sum(
            1 for r in records.values() if not r.eligible_for_bowaka_equity_bucket
        ),
        "rejections_by_reason": dict(sorted(by_reason.items())),
    }


__all__ = [
    "UniverseRecord",
    "build_pit_universe",
    "build_pit_universe_for_sessions",
    "classify_instrument",
    "eligible_symbols",
    "universe_hash",
    "to_scanner_snapshot",
    "funnel",
    "DEFAULT_ALLOWED_EXCHANGES",
    "DEFAULT_TICKER_BLOCKLIST",
]
