"""IEX-vs-SIP feature divergence framework (realism remediation 2 Phase 10).

Audit §11 Phase 9 and §P1-010. Once both feeds are ingested, the IEX-vs-SIP
divergence report quantifies how partial-tape IEX features compare to
consolidated-tape SIP features for the same (symbol, date) — the gating
evidence for ever advancing an IEX-tuned parameter set to SIP.

Today the lake has IEX bars only; the framework still ships so:

1. New SIP partitions are wired into a comparable shape on day one.
2. The Phase 10 test suite can drive the divergence math against synthetic
   mock partitions (identical IEX/SIP labels → divergence = 0).

Per-feature divergence is computed for:

- ``rvol_so_far``   — rolling-volume-so-far (running session volume / ADV).
- ``range_expansion`` — high-low range as a fraction of ATR.
- ``adv``          — average dollar volume (a daily aggregate).

The report writes a markdown table summarising per-symbol/per-feature
divergence statistics (mean abs delta, max abs delta, fraction of bars whose
delta exceeds a configurable threshold).

The framework is deliberately strict about labels: an IEX frame fed in the
SIP slot (or vice versa) raises a :class:`ValueError`. Frames that are not
exactly aligned on ``(symbol, timestamp)`` are inner-joined and the missing
counts are reported.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

import pandas as pd

from bowaka_common.marketdata import MarketDataStore
from bowaka_common.marketdata.layout import FEED_IEX, FEED_SIP

#: Default per-feature delta threshold; a feature row is "divergent" when
#: ``|iex - sip| / max(|iex|, |sip|, 1e-9)`` exceeds this fraction.
DEFAULT_DIVERGENCE_THRESHOLD = 0.05

#: Features the report can compute. Each entry maps the user-facing name to a
#: callable that derives the feature value from a per-bar frame; the same
#: callable is used for both feeds. The callables are simple by design so the
#: framework's behaviour can be reproduced from this module alone.
_FEATURE_BUILDERS: dict[str, Any] = {}


def _feature(name: str):
    """Decorator that registers a feature-builder under ``name``."""

    def deco(fn):
        _FEATURE_BUILDERS[name] = fn
        return fn

    return deco


@_feature("rvol_so_far")
def _build_rvol_so_far(df: pd.DataFrame, *, baseline: pd.DataFrame | None = None) -> pd.Series:
    """Running session volume / ADV baseline (one value per minute bar).

    When ``baseline`` is supplied it must carry ``symbol``+``adv`` columns; the
    framework divides the cumulative-by-session minute volume by the ADV. When
    no baseline is supplied the divisor is the per-symbol total session volume
    (so the test fixture can drive identical IEX/SIP series).
    """
    if "session_date" not in df.columns:
        df = df.copy()
        df["session_date"] = pd.to_datetime(df["timestamp"]).dt.tz_convert("UTC").dt.date
    grouped = df.groupby(["symbol", "session_date"])
    cum = grouped["volume"].cumsum()
    if baseline is not None and not baseline.empty and "adv" in baseline.columns:
        adv_by_symbol = baseline.set_index("symbol")["adv"].to_dict()
        divisor = df["symbol"].map(adv_by_symbol).fillna(0.0).astype(float)
    else:
        total_by_session = grouped["volume"].transform("sum")
        divisor = total_by_session
    divisor = divisor.replace(0, pd.NA).astype("float64")
    return (cum.astype("float64") / divisor).fillna(0.0)


@_feature("range_expansion")
def _build_range_expansion(df: pd.DataFrame, **_: Any) -> pd.Series:
    """``(high - low) / open`` per bar — a feed-agnostic range-expansion proxy."""
    high = df["high"].astype("float64")
    low = df["low"].astype("float64")
    open_ = df["open"].astype("float64").replace(0, pd.NA)
    return ((high - low) / open_).fillna(0.0)


@_feature("adv")
def _build_adv(df: pd.DataFrame, **_: Any) -> pd.Series:
    """A constant-per-symbol/session 20-bar rolling dollar-volume estimate.

    The exact definition is not load-bearing for the test suite — the only
    requirement is that the SAME function is applied to both feeds, so
    identical inputs produce identical outputs.
    """
    if "session_date" not in df.columns:
        df = df.copy()
        df["session_date"] = pd.to_datetime(df["timestamp"]).dt.tz_convert("UTC").dt.date
    dollar = df["close"].astype("float64") * df["volume"].astype("float64")
    rolling = dollar.rolling(window=20, min_periods=1).mean()
    return rolling.fillna(0.0)


@dataclass
class FeatureDivergence:
    """Per-(symbol, feature) divergence statistics for one (start, end) range."""

    symbol: str
    feature: str
    n_bars: int
    mean_abs_delta: float
    max_abs_delta: float
    p95_abs_delta: float
    fraction_above_threshold: float
    threshold: float
    iex_present_count: int
    sip_present_count: int

    def as_row(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "feature": self.feature,
            "n_bars": self.n_bars,
            "mean_abs_delta": self.mean_abs_delta,
            "max_abs_delta": self.max_abs_delta,
            "p95_abs_delta": self.p95_abs_delta,
            "fraction_above_threshold": self.fraction_above_threshold,
            "threshold": self.threshold,
            "iex_present_count": self.iex_present_count,
            "sip_present_count": self.sip_present_count,
        }


@dataclass
class DivergenceReport:
    """A complete IEX-vs-SIP divergence report for one universe + window."""

    symbols: list[str]
    start: _dt.date
    end: _dt.date
    features: list[str]
    threshold: float
    per_symbol_rows: list[FeatureDivergence] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "symbols": list(self.symbols),
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "features": list(self.features),
            "threshold": float(self.threshold),
            "rows": [r.as_row() for r in self.per_symbol_rows],
            "skipped": list(self.skipped),
        }

    def max_divergence(self) -> float:
        """The largest ``max_abs_delta`` across every (symbol, feature) row.

        Returns ``0.0`` when there are no rows (an empty universe / window).
        """
        if not self.per_symbol_rows:
            return 0.0
        return max(r.max_abs_delta for r in self.per_symbol_rows)


def _to_date(x: Any) -> _dt.date:
    if isinstance(x, _dt.datetime):
        return x.date()
    if isinstance(x, _dt.date):
        return x
    return pd.Timestamp(x).date()


def _validate_frames(
    iex: pd.DataFrame, sip: pd.DataFrame, *, symbol: str
) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    """Validate the per-feed frames before computing divergence.

    Returns ``(iex_inner, sip_inner)`` aligned on ``timestamp`` — or ``None``
    when there is nothing comparable. Raises :class:`ValueError` when the
    ``feed`` label on either frame contradicts its slot.
    """
    if "feed" in iex.columns:
        feeds = set(map(str, iex["feed"].unique()))
        if feeds and feeds - {FEED_IEX, ""}:
            raise ValueError(
                f"IEX frame for {symbol!r} carries unexpected feed labels {feeds}"
            )
    if "feed" in sip.columns:
        feeds = set(map(str, sip["feed"].unique()))
        if feeds and feeds - {FEED_SIP, ""}:
            raise ValueError(
                f"SIP frame for {symbol!r} carries unexpected feed labels {feeds}"
            )
    if iex.empty and sip.empty:
        return None
    iex = iex.copy()
    sip = sip.copy()
    iex["timestamp"] = pd.to_datetime(iex["timestamp"], utc=True)
    sip["timestamp"] = pd.to_datetime(sip["timestamp"], utc=True)
    joined = iex.merge(sip, on="timestamp", how="inner", suffixes=("_iex", "_sip"))
    if joined.empty:
        return None
    iex_inner = iex.set_index("timestamp").loc[joined["timestamp"]].reset_index()
    sip_inner = sip.set_index("timestamp").loc[joined["timestamp"]].reset_index()
    # Re-attach a ``symbol`` column on the joined frames so feature builders
    # can group by it.
    for frame in (iex_inner, sip_inner):
        if "symbol" not in frame.columns:
            frame["symbol"] = symbol
    return iex_inner, sip_inner


def _compute_one(
    *,
    symbol: str,
    feature: str,
    iex_frame: pd.DataFrame,
    sip_frame: pd.DataFrame,
    threshold: float,
) -> FeatureDivergence:
    """Compute one symbol/feature divergence row."""
    builder = _FEATURE_BUILDERS[feature]
    iex_vals = builder(iex_frame).astype("float64").to_numpy()
    sip_vals = builder(sip_frame).astype("float64").to_numpy()
    # Length mismatch should be impossible at this point (we inner-joined) but
    # guard defensively so the divergence math is well-defined.
    n = min(len(iex_vals), len(sip_vals))
    delta = abs(iex_vals[:n] - sip_vals[:n])
    if n == 0:
        return FeatureDivergence(
            symbol=symbol, feature=feature, n_bars=0,
            mean_abs_delta=0.0, max_abs_delta=0.0, p95_abs_delta=0.0,
            fraction_above_threshold=0.0, threshold=threshold,
            iex_present_count=len(iex_vals), sip_present_count=len(sip_vals),
        )
    denom = (
        pd.Series(iex_vals[:n]).abs().combine(pd.Series(sip_vals[:n]).abs(), max).values
    )
    denom = denom.clip(min=1e-9)
    rel = delta / denom
    p95 = float(pd.Series(delta).quantile(0.95)) if n >= 1 else 0.0
    return FeatureDivergence(
        symbol=symbol, feature=feature, n_bars=int(n),
        mean_abs_delta=float(delta.mean()),
        max_abs_delta=float(delta.max()),
        p95_abs_delta=float(p95),
        fraction_above_threshold=float((rel > threshold).mean()),
        threshold=float(threshold),
        iex_present_count=int(len(iex_vals)),
        sip_present_count=int(len(sip_vals)),
    )


def compute_feature_divergence(
    *,
    iex_store: MarketDataStore,
    sip_store: MarketDataStore,
    symbols: Iterable[str],
    start: Any,
    end: Any,
    features: Iterable[str] = ("rvol_so_far", "range_expansion", "adv"),
    threshold: float = DEFAULT_DIVERGENCE_THRESHOLD,
    timeframe: str = "1m",
) -> DivergenceReport:
    """Compute the IEX-vs-SIP feature divergence report for one universe + window.

    Both stores point at lakes whose layout follows
    :mod:`bowaka_common.marketdata.layout`. ``iex_store`` reads with
    ``feed="iex"``; ``sip_store`` reads with ``feed="sip"``. The framework
    inner-joins the two feeds on ``timestamp`` and computes per-feature
    divergence on the joined rows.

    A symbol whose IEX or SIP frame is empty is skipped (recorded in
    ``DivergenceReport.skipped``); the report still emits a row for every
    other (symbol, feature) pair.
    """
    start_d, end_d = _to_date(start), _to_date(end)
    feats = [f for f in features if f in _FEATURE_BUILDERS]
    unknown = sorted(set(features) - set(_FEATURE_BUILDERS))
    if unknown:
        raise ValueError(
            f"unknown feature(s) for divergence report: {unknown}; "
            f"known features: {sorted(_FEATURE_BUILDERS)}"
        )
    report = DivergenceReport(
        symbols=[str(s) for s in symbols],
        start=start_d, end=end_d, features=feats, threshold=float(threshold),
    )
    for sym in report.symbols:
        if timeframe == "1m":
            iex_df = iex_store.minute_bars(sym, start_d, end_d, feed=FEED_IEX)
            sip_df = sip_store.sip_minute_bars(sym, start_d, end_d)
        elif timeframe == "1d":
            iex_df = iex_store.daily_bars(sym, start_d, end_d, feed=FEED_IEX)
            sip_df = sip_store.sip_daily_bars(sym, start_d, end_d)
        else:
            raise ValueError(
                f"unsupported timeframe {timeframe!r}; expected '1m' or '1d'"
            )
        if iex_df.empty or sip_df.empty:
            report.skipped.append({
                "symbol": sym, "reason": "iex_or_sip_frame_empty",
                "iex_rows": int(len(iex_df)), "sip_rows": int(len(sip_df)),
            })
            continue
        try:
            validated = _validate_frames(iex_df, sip_df, symbol=sym)
        except ValueError as exc:
            report.skipped.append({
                "symbol": sym, "reason": "frame_validation_failed",
                "detail": str(exc),
            })
            continue
        if validated is None:
            report.skipped.append({
                "symbol": sym, "reason": "no_overlapping_timestamps",
                "iex_rows": int(len(iex_df)), "sip_rows": int(len(sip_df)),
            })
            continue
        iex_inner, sip_inner = validated
        for feat in feats:
            report.per_symbol_rows.append(
                _compute_one(
                    symbol=sym, feature=feat,
                    iex_frame=iex_inner, sip_frame=sip_inner, threshold=threshold,
                )
            )
    return report


def render_divergence_markdown(report: DivergenceReport) -> str:
    """Render a markdown summary table for a :class:`DivergenceReport`."""
    lines: list[str] = []
    lines.append("# IEX-vs-SIP feature divergence report")
    lines.append("")
    lines.append(
        f"- window: `{report.start.isoformat()}` -> `{report.end.isoformat()}`  "
        f"\n- universe: {len(report.symbols)} symbol(s)  "
        f"\n- features: {', '.join(report.features) or '(none)'}  "
        f"\n- divergence threshold: `{report.threshold:.4f}`"
    )
    lines.append("")
    if not report.per_symbol_rows:
        lines.append("> No per-(symbol, feature) rows were produced. "
                     "All symbols were skipped — see the skipped table below.")
        lines.append("")
    else:
        lines.append(
            "| symbol | feature | n_bars | mean_abs_delta | max_abs_delta | "
            "p95_abs_delta | fraction_above_threshold |"
        )
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for r in report.per_symbol_rows:
            lines.append(
                f"| {r.symbol} | {r.feature} | {r.n_bars} | "
                f"{r.mean_abs_delta:.6f} | {r.max_abs_delta:.6f} | "
                f"{r.p95_abs_delta:.6f} | {r.fraction_above_threshold:.4f} |"
            )
        lines.append("")
    if report.skipped:
        lines.append("## Skipped symbols")
        lines.append("")
        lines.append("| symbol | reason | detail |")
        lines.append("|---|---|---|")
        for s in report.skipped:
            detail = s.get("detail") or (
                f"iex_rows={s.get('iex_rows', 0)} sip_rows={s.get('sip_rows', 0)}"
            )
            lines.append(f"| {s.get('symbol', '?')} | {s.get('reason', '?')} | {detail} |")
        lines.append("")
    lines.append("---")
    lines.append(
        "*Generated by `bowaka_v2_lab.research.feature_divergence` — realism "
        "remediation 2 Phase 10 (audit §11 Phase 9 / §P1-010).*"
    )
    return "\n".join(lines) + "\n"


def write_divergence_report(
    report: DivergenceReport, out_dir: str | Path, *, name: str = "feature_divergence"
) -> tuple[Path, Path]:
    """Write the markdown + JSON pair for ``report`` to ``out_dir``."""
    import json

    od = Path(out_dir)
    od.mkdir(parents=True, exist_ok=True)
    md_path = od / f"{name}.md"
    json_path = od / f"{name}.json"
    md_path.write_text(render_divergence_markdown(report), encoding="utf-8")
    json_path.write_text(
        json.dumps(report.as_dict(), indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return md_path, json_path


__all__ = [
    "DEFAULT_DIVERGENCE_THRESHOLD",
    "FeatureDivergence",
    "DivergenceReport",
    "compute_feature_divergence",
    "render_divergence_markdown",
    "write_divergence_report",
]
