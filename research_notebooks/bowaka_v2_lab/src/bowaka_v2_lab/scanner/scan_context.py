"""Per-session scan context precompute (speedup report §5.4 / §10.4 / §11.2 Phase 4).

The legacy :func:`scanner.scan_loop.evaluate_one_scan` rebuilt three pieces
of state on EVERY scan call:

1. ``universe_meta_by_sym = {s["symbol"]: s for s in universe_snapshot["symbols"]}``
2. ``cache_by_sym = {row["symbol"]: row.to_dict() for _, row in daily_cache.iterrows()}``
3. ``config_hash_v = _config_hash(cfg)`` (deep-hashes the cfg dict)

Plus, the per-symbol volume-curve fraction lookup recomputed bucket /
fraction logic every scan even though it depends only on
``(scan_ts, adv_bucket)`` — which is stable across symbols sharing the
same bucket.

``ScanSessionContext`` precomputes all four ONCE per session (the cfg /
universe / daily cache do not change inside a backtester run) and exposes
them to the scanner. ``evaluate_one_scan`` accepts an optional
``scan_context`` and reads from it when present.

Forensic gate dump: per-symbol nested dumps are still constructed when
``collect_gate_dump=True`` (the default for full artifact mode). For
``artifact_mode="objective_minimal"`` the backtester passes
``collect_gate_dump=False`` and the scanner records bounded rejection
counters on ``ScanResult.rejection_counts`` instead. Promotion-relevant
funnel counters remain computable from those counters.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

import pandas as pd

from ..features import adv_bucket, compute_volume_curve_fraction


@dataclass(frozen=True)
class ScanSessionContext:
    """Precomputed per-session inputs for :func:`evaluate_one_scan`."""

    universe_meta_by_sym: Mapping[str, dict]
    cache_by_sym: Mapping[str, dict]
    config_hash_v: str
    #: ``(scan_ts, adv_bucket) -> volume_curve_fraction`` lookup. Bucket is a
    #: stable string from :func:`adv_bucket`. Missing keys fall back to the
    #: ``fallback_opening_15m_share`` configured in ``historical_features``.
    volume_curve_fraction_by_scan_bucket: Mapping[tuple[pd.Timestamp, str], float]
    collect_gate_dump: bool = True
    #: §10h Opt A — mutable per-session memo for the matrix evaluator's
    #: session-constant baseline arrays (adv / prior_atr_pct / ema_slope /
    #: has_baseline / instrument_pass), keyed by ``allow_unknown``. Built ONCE per
    #: session instead of every scan (~346x). Excluded from eq/hash (compare=False)
    #: so it never affects the frozen-dataclass identity semantics.
    _matrix_baseline_cache: dict = field(default_factory=dict, compare=False)
    #: c18 — mutable per-session memo for the matrix evaluator's symbol-order
    #: arrays (sym_to_idx, order_idxs), keyed by the matrix-session identity with a
    #: length guard. These depend only on matrix_session.universe_meta + the
    #: session-constant symbol list, but were rebuilt every scan (~346x). Same
    #: compare=False semantics as the baseline memo above.
    _matrix_order_cache: dict = field(default_factory=dict, compare=False)


def _config_hash(cfg: Mapping[str, Any]) -> str:
    """Deep, stable hash over the cfg — mirrors ``scan_loop._config_hash``."""
    payload = json.dumps(cfg, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()[:16]


def build_scan_session_context(
    cfg: Mapping[str, Any],
    daily_cache: pd.DataFrame | None,
    universe_snapshot: Mapping[str, Any],
    scan_times: list[Any] | tuple[Any, ...],
    volume_curve: pd.DataFrame | None = None,
    *,
    collect_gate_dump: bool = True,
) -> ScanSessionContext:
    """Build the per-session context once for an entire session of scans."""
    universe_meta_by_sym: dict[str, dict] = {
        s["symbol"]: dict(s) for s in (universe_snapshot.get("symbols") or [])
    }
    cache_by_sym: dict[str, dict] = {}
    if daily_cache is not None and not daily_cache.empty:
        for _, row in daily_cache.iterrows():
            cache_by_sym[row["symbol"]] = row.to_dict()

    hf_cfg = cfg.get("historical_features") or {}
    bucket_edges = list(
        (hf_cfg.get("volume_curve") or {}).get(
            "bucket_edges", [250_000, 500_000, 1_000_000, 5_000_000, 20_000_000],
        )
    )
    fallback_share = float(
        (hf_cfg.get("volume_curve") or {}).get("fallback_opening_15m_share", 0.08)
    )

    # Distinct ADV buckets in this session's universe.
    buckets_in_play: set[str] = set()
    for meta in cache_by_sym.values():
        adv = meta.get("avg_dollar_volume_20d")
        buckets_in_play.add(adv_bucket(adv, bucket_edges))

    # Precompute (scan_ts, bucket) -> fraction once per session.
    vcf_map: dict[tuple[pd.Timestamp, str], float] = {}
    for raw_ts in scan_times:
        ts = pd.Timestamp(raw_ts)
        for bucket in buckets_in_play:
            vcf_map[(ts, bucket)] = compute_volume_curve_fraction(
                volume_curve, ts, bucket,
                fallback_opening_15m_share=fallback_share,
            )

    return ScanSessionContext(
        universe_meta_by_sym=universe_meta_by_sym,
        cache_by_sym=cache_by_sym,
        config_hash_v=_config_hash(cfg),
        volume_curve_fraction_by_scan_bucket=vcf_map,
        collect_gate_dump=bool(collect_gate_dump),
    )


__all__ = [
    "ScanSessionContext",
    "build_scan_session_context",
]
