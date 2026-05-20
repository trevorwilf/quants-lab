"""Pure-function scan loop (port of ``evaluate_one_scan`` from
``bowaka_intraday_scanner.py`` lines 330-546).

§15 remediations applied:

- **Stale-bar enforcement happens BEFORE feature compute** per [Report §15.1 P0]:
  the original archive computed features then sometimes skipped — exposing the
  scanner to lookahead in edge cases.
- **max_entries_per_scan** policy per [Report §15.2 P1]: the emitted candidate
  count is capped at ``min(max_candidates_per_scan, max_entries_per_scan)``
  when both are set.
- Per-symbol gate dumps are returned as a list rather than written via a
  global file handle, so callers (scanner.replay, sim.event_loop) can route
  them anywhere.
"""
from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping, Sequence

import pandas as pd

from ..features import (
    aggregate_forming_session_bar,
    apply_v2_gates,
    compute_forming_session_features,
    compute_signal_strength,
    compute_volume_curve_fraction,
    adv_bucket,
)
from .event_builder import build_candidate_event


SCAN_SKIP_REASONS: tuple[str, ...] = (
    "already_entered_today",
    "no_baselines",
    "bars_fetch_failed",
    "no_bars",
    "stale_bar",
    "gate_failed",
    "max_entries_cap",
)
SCAN_SKIP_REASONS_SET: frozenset[str] = frozenset(SCAN_SKIP_REASONS)


class ScanSkipReason(str, enum.Enum):
    ALREADY_ENTERED_TODAY = "already_entered_today"
    NO_BASELINES = "no_baselines"
    BARS_FETCH_FAILED = "bars_fetch_failed"
    NO_BARS = "no_bars"
    STALE_BAR = "stale_bar"
    GATE_FAILED = "gate_failed"
    MAX_ENTRIES_CAP = "max_entries_cap"


@dataclass
class ScanResult:
    emitted: list[dict[str, Any]] = field(default_factory=list)
    gate_dump: list[dict[str, Any]] = field(default_factory=list)
    universe_size: int = 0


def _config_hash(cfg: Mapping[str, Any]) -> str:
    payload = json.dumps(cfg, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()[:16]


def _iso_utc(ts: Any) -> str:
    pts = pd.Timestamp(ts)
    if pts.tzinfo is None:
        raise ValueError("scan_loop: tz-naive timestamp rejected")
    return pts.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def evaluate_one_scan(
    *,
    cfg: Mapping[str, Any],
    universe_snapshot: Mapping[str, Any],
    daily_cache: pd.DataFrame | None,
    volume_curve: pd.DataFrame | None,
    state: dict[str, Any],
    scan_ts: Any,
    bars_supplier: Callable[[str, Any], pd.DataFrame | None],
) -> ScanResult:
    """Pure scan evaluation. ``bars_supplier`` is the only data-side injection."""
    scanner_cfg = cfg.get("scanner") or {}
    signals_cfg = cfg.get("signals") or {}
    score_cfg = cfg.get("score") or {}
    market_data_cfg = cfg.get("market_data") or cfg.get("data") or {}
    hf_cfg = (cfg.get("historical_features") or {})
    bucket_edges = list(
        (hf_cfg.get("volume_curve") or {}).get(
            "bucket_edges", [250_000, 500_000, 1_000_000, 5_000_000, 20_000_000],
        )
    )
    fallback_share = float(
        (hf_cfg.get("volume_curve") or {}).get("fallback_opening_15m_share", 0.08)
    )
    # Per [Report §15.2 P1]: emitted count capped by min(max_candidates_per_scan, max_entries_per_scan).
    max_candidates = int(scanner_cfg.get("max_candidates_per_scan", 25))
    max_entries = int(scanner_cfg.get("max_entries_per_scan", max_candidates))
    effective_cap = max(0, min(max_candidates, max_entries))

    # Per [Report §15.1 P0]: stale-bar enforcement BEFORE feature compute.
    max_bar_age_seconds = int(market_data_cfg.get("max_bar_age_seconds", 90))

    entered = set(state.get("entered_symbols_today") or [])
    universe_meta_by_sym = {
        s["symbol"]: s for s in universe_snapshot.get("symbols", [])
    }
    cache_by_sym: dict[str, dict[str, Any]] = {}
    if daily_cache is not None and not daily_cache.empty:
        for _, row in daily_cache.iterrows():
            cache_by_sym[row["symbol"]] = row.to_dict()

    universe_hash = universe_snapshot.get("universe_hash", "sha256:unknown")
    config_hash_v = _config_hash(cfg)

    scan_ts_obj = pd.Timestamp(scan_ts)
    if scan_ts_obj.tzinfo is None:
        raise ValueError("evaluate_one_scan: scan_ts must be tz-aware")

    result = ScanResult(universe_size=len(universe_meta_by_sym))
    passing: list[tuple[float, dict[str, Any]]] = []
    for symbol, meta in universe_meta_by_sym.items():
        if symbol in entered:
            result.gate_dump.append({
                "scan_timestamp": _iso_utc(scan_ts),
                "symbol": symbol,
                "skipped": ScanSkipReason.ALREADY_ENTERED_TODAY.value,
            })
            continue

        baselines = cache_by_sym.get(symbol)
        if not baselines:
            result.gate_dump.append({
                "scan_timestamp": _iso_utc(scan_ts),
                "symbol": symbol,
                "skipped": ScanSkipReason.NO_BASELINES.value,
            })
            continue

        adv = baselines.get("avg_dollar_volume_20d")
        prior_atr_pct = baselines.get("prior_atr_pct")
        ema_slope = baselines.get("ema_slope_prior")
        bucket = adv_bucket(adv, bucket_edges)
        vcf = compute_volume_curve_fraction(
            volume_curve, scan_ts_obj, bucket, fallback_opening_15m_share=fallback_share,
        )

        # Fetch minute bars.
        try:
            bars = bars_supplier(symbol, scan_ts_obj)
        except Exception as e:
            result.gate_dump.append({
                "scan_timestamp": _iso_utc(scan_ts),
                "symbol": symbol,
                "skipped": ScanSkipReason.BARS_FETCH_FAILED.value,
                "error": str(e)[:200],
            })
            continue
        if bars is None or len(bars) == 0:
            result.gate_dump.append({
                "scan_timestamp": _iso_utc(scan_ts),
                "symbol": symbol,
                "skipped": ScanSkipReason.NO_BARS.value,
            })
            continue

        # STALE BAR CHECK — per [Report §15.1 P0], BEFORE feature compute.
        ts_col = None
        for c in bars.columns:
            if c.lower() in ("timestamp", "ts"):
                ts_col = c
                break
        if ts_col is not None:
            last_bar_ts = pd.Timestamp(bars[ts_col].iloc[-1])
            if last_bar_ts.tzinfo is None:
                # Reject naive — same policy as features module.
                result.gate_dump.append({
                    "scan_timestamp": _iso_utc(scan_ts),
                    "symbol": symbol,
                    "skipped": ScanSkipReason.STALE_BAR.value,
                    "reason": "naive_timestamp",
                })
                continue
            age_seconds = (scan_ts_obj - last_bar_ts).total_seconds()
            if age_seconds > max_bar_age_seconds:
                result.gate_dump.append({
                    "scan_timestamp": _iso_utc(scan_ts),
                    "symbol": symbol,
                    "skipped": ScanSkipReason.STALE_BAR.value,
                    "bar_age_seconds": float(age_seconds),
                    "max_bar_age_seconds": max_bar_age_seconds,
                })
                continue

        sess = aggregate_forming_session_bar(bars)
        feats = compute_forming_session_features(sess, baselines, vcf)
        ok, gates = apply_v2_gates(
            feats, signals_cfg,
            price=sess.get("last_price"),
            avg_dollar_volume_20d=adv,
            prior_atr_pct=prior_atr_pct,
            ema_slope_prior=ema_slope,
            instrument_class=meta.get("instrument_class"),
        )
        result.gate_dump.append({
            "scan_timestamp": _iso_utc(scan_ts),
            "symbol": symbol,
            "ok": bool(ok),
            "failing_gates": sorted(k for k, v in (gates or {}).items() if not v),
            "gate_results": gates,
            "features": feats,
            "baselines": {
                "prior_close": baselines.get("prior_close"),
                "prior_atr_pct": prior_atr_pct,
                "ema_slope_prior": ema_slope,
                "avg_dollar_volume_20d": adv,
            },
            "session_bar": sess,
            "volume_curve_fraction": vcf,
            "instrument_class": meta.get("instrument_class"),
        })
        if not ok:
            continue

        score = compute_signal_strength(feats, score_cfg, ema_slope_prior=ema_slope)
        ev = build_candidate_event(
            symbol=symbol,
            universe_meta=meta,
            cfg=cfg,
            universe_hash=universe_hash,
            config_hash_v=config_hash_v,
            session_bar=sess,
            prior_baselines=baselines,
            forming_feats=feats,
            volume_curve_fraction=vcf,
            gate_results=gates,
            candidate_rank=0,
            scan_ts=scan_ts_obj,
            signal_strength=score,
        )
        passing.append((score, ev))

    passing.sort(key=lambda x: -x[0])
    for rank, (_score, ev) in enumerate(passing[:effective_cap], start=1):
        ev["candidate_rank"] = rank
        result.emitted.append(ev)
        state.setdefault("in_play_pool", {})[ev["symbol"]] = {
            "last_signal_ts": ev["scan_timestamp"],
            "signal_expiry_ts": ev["signal_expiry_timestamp"],
            "last_signal_strength": ev["features"]["signal_strength"],
        }
    if len(passing) > effective_cap:
        # Record the capped overflow in the dump for visibility.
        for _score, ev in passing[effective_cap:]:
            result.gate_dump.append({
                "scan_timestamp": _iso_utc(scan_ts),
                "symbol": ev["symbol"],
                "ok": True,
                "skipped": ScanSkipReason.MAX_ENTRIES_CAP.value,
                "effective_cap": effective_cap,
            })
    state["scanner_last_run_ts"] = _iso_utc(scan_ts)
    return result
