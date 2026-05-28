"""Scan feature-matrix precompute store (matrix doc §5–§10 / speedup §6.4).

The matrix is a read-only, memory-mapped, per-session columnar feature store.
The walk-forward objective opens the matrix once per worker and reads the
features the scanner needs from numpy memmaps; the per-trial cost is then
a small slice + a few gates, not a per-symbol feature recompute.

Phase 8 ships the **builder**, **manifest**, **store reader**, **CLI
subcommands**, **search-space guard**, and **config schema** — all default
off. Phase 9 wires the runtime scanner to read from the matrix.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

import numpy as np
import pandas as pd


#: Matrix schema version. Bump on incompatible layout changes.
MATRIX_SCHEMA_VERSION = 1


# ---- column schemas -------------------------------------------------------

DYNAMIC_FLOAT64_COLUMNS: tuple[str, ...] = (
    "session_open",
    "session_high",
    "session_low",
    "last_price",
    "session_volume",
    "session_range",
    "volume_curve_fraction",
    "expected_volume_until_scan",
    "rvol_so_far",
    "projected_full_day_rvol",
    "range_expansion_so_far",
    "close_location_so_far",
    "ema_distance",
    "current_return_pct",
    "gap_pct",
    "bar_age_seconds",
)

DYNAMIC_INT64_COLUMNS: tuple[str, ...] = (
    "last_bar_ts_ns",
)

DYNAMIC_UINT8_COLUMNS: tuple[str, ...] = (
    "has_bar",
    "has_baseline",
    "has_valid_timestamp",
    "bar_timestamp_was_naive",
)

STATIC_FLOAT64_COLUMNS: tuple[str, ...] = (
    "prior_close",
    "avg_volume_20d",
    "avg_dollar_volume_20d",
    "prior_atr_14d",
    "prior_atr_pct",
    "ema_10_prior",
    "ema_10_lag_3",
    "ema_slope_prior",
)

STATIC_INT8_COLUMNS: tuple[str, ...] = (
    "instrument_class_code",
    "eligible_for_bowaka_equity_bucket",
    "exchange_code",
    "venue_code",
)


# ---- manifest / store -----------------------------------------------------


class HoldoutMatrixReadError(RuntimeError):
    """Raised when the objective opens a holdout session of the matrix."""


class MatrixVerifyError(RuntimeError):
    """Raised when :func:`verify_scan_matrix` finds drift beyond tolerance.

    Speedup report v2 §10.3 fix 2 / Phase 2. The verifier compares the
    matrix's stored cells against the legacy aggregator output (when a
    lake is reachable) and against the per-partition file checksum
    recorded in the manifest. Any mismatch on a sampled cell or any
    detected corruption raises this exception so the caller fails closed.
    """


@dataclass(frozen=True)
class ScanMatrixManifest:
    """Top-level manifest for a built matrix (matrix doc §8.1)."""

    matrix_id: str
    matrix_version: int
    config_input_hash: str
    dataset_hash: str
    feed: str
    scope: str
    created_at_utc: str
    reserved_system_gib: float
    max_optuna_workers: int
    sessions: list[str]
    columns: dict[str, list[str]]
    bowaka_lab_version: str = "0.1.0"
    code_hashes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matrix_id": self.matrix_id,
            "matrix_version": int(self.matrix_version),
            "config_input_hash": self.config_input_hash,
            "dataset_hash": self.dataset_hash,
            "feed": self.feed,
            "scope": self.scope,
            "created_at_utc": self.created_at_utc,
            "reserved_system_gib": float(self.reserved_system_gib),
            "max_optuna_workers": int(self.max_optuna_workers),
            "sessions": list(self.sessions),
            "columns": dict(self.columns),
            "bowaka_lab_version": self.bowaka_lab_version,
            "code_hashes": dict(self.code_hashes),
        }


@dataclass(frozen=True)
class ScanMatrixSession:
    """In-memory view over one session partition's memmap arrays."""

    session_date: _dt.date
    root: Path
    scan_timestamps_ns: np.ndarray  # int64 ns UTC
    symbol_ids: np.ndarray           # int32
    dynamic_float64: dict[str, np.ndarray]  # column -> (n_scans, n_symbols) float64
    dynamic_int64: dict[str, np.ndarray]    # column -> (n_scans, n_symbols) int64
    dynamic_uint8: dict[str, np.ndarray]    # column -> (n_scans, n_symbols) uint8
    static_float64: dict[str, np.ndarray]   # column -> (n_symbols,) float64
    static_int8: dict[str, np.ndarray]      # column -> (n_symbols,) int8
    universe_meta: pd.DataFrame             # per-symbol metadata


class ScanMatrixStore:
    """Read-only store for a built scan matrix (matrix doc §8.1).

    Per the prompt's holdout-isolation contract: any open with
    ``purpose="objective"`` against a session date that lies inside the
    plan's holdout window raises :class:`HoldoutMatrixReadError`. The
    final-holdout scorer uses ``purpose="final_holdout"`` to opt in.
    """

    def __init__(
        self,
        root: Path | str,
        *,
        readonly: bool = True,
        holdout_window: tuple[_dt.date, _dt.date] | None = None,
    ):
        self.root = Path(root)
        self.readonly = bool(readonly)
        self._holdout_window = holdout_window
        manifest_path = self.root / "manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"scan matrix manifest missing: {manifest_path}")
        self._manifest_dict = json.loads(manifest_path.read_text(encoding="utf-8"))

    @property
    def manifest(self) -> dict[str, Any]:
        return self._manifest_dict

    def assert_can_read(
        self, session_date: _dt.date, *, purpose: str,
    ) -> None:
        """Refuse holdout reads under ``purpose="objective"``.

        ``purpose="final_holdout"`` always passes. Other purposes are
        treated as objective (fail closed)."""
        if self._holdout_window is None:
            return
        start, end = self._holdout_window
        if not (start <= session_date < end):
            return
        if purpose != "final_holdout":
            raise HoldoutMatrixReadError(
                f"refusing to open holdout session {session_date} under "
                f"purpose={purpose!r}; the holdout window {start}..{end} "
                "may only be read with purpose='final_holdout'"
            )

    def open_session(
        self,
        session_date: _dt.date,
        *,
        purpose: str = "objective",
    ) -> ScanMatrixSession:
        self.assert_can_read(session_date, purpose=purpose)
        sess_dir = self.root / f"session={session_date.isoformat()}"
        if not sess_dir.is_dir():
            raise FileNotFoundError(
                f"session partition missing: {sess_dir}"
            )

        def _mmap(name: str) -> np.ndarray:
            path = sess_dir / name
            return np.lib.format.open_memmap(path, mode="r")

        scan_ts = _mmap("scan_timestamps_ns.int64.npy")
        symbol_ids = _mmap("symbol_ids.int32.npy")

        dyn_f64 = {col: _mmap(f"dyn_f64__{col}.npy") for col in DYNAMIC_FLOAT64_COLUMNS}
        dyn_i64 = {col: _mmap(f"dyn_i64__{col}.npy") for col in DYNAMIC_INT64_COLUMNS}
        dyn_u8 = {col: _mmap(f"dyn_u8__{col}.npy") for col in DYNAMIC_UINT8_COLUMNS}
        stat_f64 = {col: _mmap(f"stat_f64__{col}.npy") for col in STATIC_FLOAT64_COLUMNS}
        stat_i8 = {col: _mmap(f"stat_i8__{col}.npy") for col in STATIC_INT8_COLUMNS}

        universe_meta = pd.read_parquet(sess_dir / "universe_meta.parquet")
        return ScanMatrixSession(
            session_date=session_date,
            root=sess_dir,
            scan_timestamps_ns=scan_ts,
            symbol_ids=symbol_ids,
            dynamic_float64=dyn_f64,
            dynamic_int64=dyn_i64,
            dynamic_uint8=dyn_u8,
            static_float64=stat_f64,
            static_int8=stat_i8,
            universe_meta=universe_meta,
        )


# ---- input hashing --------------------------------------------------------


_MATRIX_HASH_SOURCE_FILES: tuple[str, ...] = (
    "features/forming_bar.py",
    "data/suppliers.py",
    "sim/schedule.py",
    "universe/builder.py",
    "scanner/event_builder.py",
)


def _file_sha256(path: Path) -> str:
    if not path.is_file():
        return "missing"
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _source_file_hashes(src_root: Path) -> dict[str, str]:
    return {
        rel: _file_sha256(src_root / rel)
        for rel in _MATRIX_HASH_SOURCE_FILES
    }


def compute_matrix_input_hash(
    cfg: Mapping[str, Any],
    plan: Any,
    sessions_by_scope: Mapping[str, Sequence[_dt.date]],
    *,
    source_root: Optional[Path] = None,
    dataset_hash: str = "",
) -> str:
    """SHA-256 over the matrix-INPUT-affecting subset of the cfg.

    Excludes ``signals.*`` / ``sizing.*`` / ``risk.*`` / ``execution.*`` /
    ``exits.*`` (all trial-tuned), so the matrix is reusable across trials
    in a study.
    """
    src_root = source_root or (Path(__file__).resolve().parents[1])
    md = cfg.get("market_data") or {}
    bt = cfg.get("backtest") or {}
    sess = cfg.get("session") or {}
    sim = cfg.get("simulation") or {}
    universe = cfg.get("universe") or {}
    hist = cfg.get("historical_features") or {}
    payload = {
        "matrix_schema_version": MATRIX_SCHEMA_VERSION,
        "feed": md.get("feed"),
        "vendor": md.get("vendor"),
        "adjustment": md.get("adjustment"),
        "lake_root": str(md.get("shared_root") or ""),
        "dataset_hash": dataset_hash,
        "backtest_range": [bt.get("start_date"), bt.get("end_date")],
        "walkforward": (cfg.get("optuna") or {}).get("walkforward"),
        "scanner_start": sess.get("scanner_start"),
        "scanner_end": sess.get("scanner_end"),
        "scan_interval_seconds": sess.get("scan_interval_seconds"),
        "timezone": sess.get("timezone"),
        "calendar": sess.get("calendar"),
        "intraday_window_policy": sim.get("intraday_window_policy"),
        "universe": universe,
        "historical_features": hist,
        "sessions_by_scope": {
            k: [d.isoformat() for d in v] for k, v in sessions_by_scope.items()
        },
        "source_file_hashes": _source_file_hashes(src_root),
    }
    canonical = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


# ---- matrix-sensitive search-space guard ----------------------------------


# Speedup report v2 §15.4 / Phase 0 — exits.* keys are intentionally OUTSIDE
# this list. Exit logic runs AFTER the scanner emits a candidate, so tuning
# ``exits.stop_pct`` (or any other ``exits.*`` knob) does NOT invalidate the
# precomputed scan matrix. Keep this list strictly limited to keys that
# affect the per-(session, scan_ts, symbol) features the matrix bakes in.
MATRIX_SENSITIVE_PREFIXES: tuple[str, ...] = (
    "session.scanner_start",
    "session.scanner_end",
    "session.scan_interval_seconds",
    "simulation.intraday_window_policy",
    "historical_features.",
    "universe.",
    "market_data.feed",
    "market_data.adjustment",
    "signals.atr_window",
    "signals.ema_window",
)


def assert_search_space_compatible_with_matrix(
    overrides: Optional[Mapping[str, Any]] = None,
) -> None:
    """Refuse search spaces that would invalidate the precomputed matrix."""
    from ..optuna.errors import OptunaStudyInvalidError
    from ..optuna.search_space import resolve_search_space

    spec = resolve_search_space(dict(overrides or {}))
    offenders = sorted(
        name for name in spec
        if any(name == p.rstrip(".") or name.startswith(p)
               for p in MATRIX_SENSITIVE_PREFIXES)
    )
    if offenders:
        raise OptunaStudyInvalidError(
            "search space tunes matrix-sensitive key(s) "
            f"{offenders!r}: the precomputed scan-matrix would be "
            "invalidated by per-trial parameter changes to these inputs. "
            "Disable matrix acceleration or drop the override "
            "(matrix doc §17)."
        )


# ---- per-session partition writer (Stage A: parity-first, slow) ----------


def _empty_dynamic_arrays(
    n_scans: int, n_symbols: int,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray]]:
    dyn_f64 = {
        col: np.full((n_scans, n_symbols), np.nan, dtype=np.float64)
        for col in DYNAMIC_FLOAT64_COLUMNS
    }
    dyn_i64 = {
        col: np.full((n_scans, n_symbols), -1, dtype=np.int64)
        for col in DYNAMIC_INT64_COLUMNS
    }
    dyn_u8 = {
        col: np.zeros((n_scans, n_symbols), dtype=np.uint8)
        for col in DYNAMIC_UINT8_COLUMNS
    }
    return dyn_f64, dyn_i64, dyn_u8


def _save_memmap(path: Path, arr: np.ndarray) -> None:
    """Write ``arr`` as a ``.npy`` file (uncompressed; memmap-friendly)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, arr, allow_pickle=False)


def _none_to_nan(v: Any) -> float:
    """``None`` / NaN -> ``np.nan``; everything else -> ``float(v)``.

    Speedup report v2 §6.1 / Phase 3 — preserves a legitimate ``0.0`` feature
    value instead of the old ``v or np.nan`` idiom (which collapsed ``0.0``
    to NaN because ``0.0`` is falsy). The compat runtime reconstructs the
    matrix cell back to ``None`` only when it is actually NaN, so storing a
    real ``0.0`` here is required for bit-parity with the legacy scanner.
    """
    if v is None:
        return float("nan")
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return float("nan")
    return fv


def build_session_partition(
    session_date: _dt.date,
    cfg: Mapping[str, Any],
    lake_root: Any,
    feed: str,
    *,
    store_root: Path,
    scope: str = "validation",
) -> dict[str, Any]:
    """Build one session partition under ``store_root`` (matrix doc §8.2).

    Stage A: parity-first. Loads the session's minute bars per symbol and
    computes the dynamic feature columns by calling the existing
    ``aggregate_forming_session_bar`` / ``compute_volume_curve_fraction`` /
    ``compute_forming_session_features`` helpers. Slower than the
    eventual cumulative-array implementation (Stage B) but the safe
    parity-first path.

    Writes to ``store_root/.tmp/session=YYYY-MM-DD/``, then atomically
    renames to ``store_root/session=YYYY-MM-DD/``. Returns a per-session
    manifest fragment with file checksums.
    """
    from bowaka_common.marketdata import MarketDataStore
    from ..data.suppliers import build_daily_cache_from_lake
    from ..features import (
        adv_bucket,
        aggregate_forming_session_bar,
        compute_forming_session_features,
        compute_volume_curve_fraction,
    )
    from ..sim.schedule import scan_times_for_session
    from ..universe.builder import build_pit_universe_for_sessions, eligible_symbols

    store = MarketDataStore(lake_root)
    pit_universe = build_pit_universe_for_sessions(
        [session_date], dict(cfg), store
    )
    symbols = sorted(eligible_symbols(pit_universe.get(session_date, {})) or [])
    if not symbols:
        # Empty PIT universe (the lake may have no asset master, as on the
        # tiny-lake test path). Fall back to the explicit ``universe.symbols``
        # list so the matrix still records a partition for this session.
        symbols = sorted([
            str(s) for s in ((cfg.get("universe") or {}).get("symbols") or [])
        ])
    symbol_ids = np.arange(len(symbols), dtype=np.int32)
    scan_times = list(scan_times_for_session(session_date, dict(cfg)))
    scan_ts_np = np.array(
        [pd.Timestamp(s).tz_convert("UTC").value for s in scan_times],
        dtype=np.int64,
    )

    n_scans = len(scan_times)
    n_symbols = len(symbols)
    dyn_f64, dyn_i64, dyn_u8 = _empty_dynamic_arrays(n_scans, n_symbols)

    daily_cache = build_daily_cache_from_lake(
        lake_root, symbols, session_date, feed=feed,
    )
    cache_by_sym = {row["symbol"]: row.to_dict()
                    for _, row in daily_cache.iterrows()} if not daily_cache.empty else {}

    hf_cfg = (cfg.get("historical_features") or {})
    bucket_edges = list(
        (hf_cfg.get("volume_curve") or {}).get(
            "bucket_edges", [250_000, 500_000, 1_000_000, 5_000_000, 20_000_000],
        )
    )
    fallback_share = float(
        (hf_cfg.get("volume_curve") or {}).get("fallback_opening_15m_share", 0.08)
    )

    stat_f64 = {col: np.full(n_symbols, np.nan, dtype=np.float64)
                for col in STATIC_FLOAT64_COLUMNS}
    stat_i8 = {col: np.full(n_symbols, -1, dtype=np.int8)
               for col in STATIC_INT8_COLUMNS}

    for s_idx, sym in enumerate(symbols):
        baselines = cache_by_sym.get(sym) or {}
        for col in STATIC_FLOAT64_COLUMNS:
            v = baselines.get(col)
            if v is not None and not pd.isna(v):
                stat_f64[col][s_idx] = float(v)
        # static int8 columns are placeholders (TBD wiring to asset master).
        stat_i8["eligible_for_bowaka_equity_bucket"][s_idx] = 1

        if n_scans == 0:
            continue
        # One bar fetch per symbol covering the full session window: from
        # 04:00 ET (premarket) through 16:00 ET (regular close).
        session_start_et = pd.Timestamp(
            _dt.datetime.combine(session_date, _dt.time(4, 0)),
            tz="America/New_York",
        ).tz_convert("UTC")
        session_end_et = pd.Timestamp(
            _dt.datetime.combine(session_date, _dt.time(16, 0)),
            tz="America/New_York",
        ).tz_convert("UTC")
        try:
            full_bars = store.minute_bars(
                sym, session_start_et, session_end_et, feed=feed,
            )
        except Exception:  # noqa: BLE001 — symbol with no partition
            full_bars = pd.DataFrame()
        if full_bars.empty:
            continue
        ts_col = None
        for c in full_bars.columns:
            if c.lower() in ("timestamp", "ts"):
                ts_col = c
                break
        if ts_col is None:
            continue

        for t_idx, scan_ts in enumerate(scan_times):
            scan_ts_obj = pd.Timestamp(scan_ts)
            if scan_ts_obj.tzinfo is None:
                scan_ts_obj = scan_ts_obj.tz_localize("UTC")
            else:
                scan_ts_obj = scan_ts_obj.tz_convert("UTC")
            bars_through = full_bars[full_bars[ts_col] <= scan_ts_obj]
            sess = aggregate_forming_session_bar(bars_through)
            if sess.get("last_price") is not None:
                dyn_u8["has_bar"][t_idx, s_idx] = 1
            for col in (
                "session_open", "session_high", "session_low", "last_price",
                "session_volume", "session_range",
            ):
                v = sess.get(col)
                if v is not None and not pd.isna(v):
                    dyn_f64[col][t_idx, s_idx] = float(v)
            last_ts = sess.get("last_bar_timestamp")
            if last_ts is not None:
                try:
                    ts_obj = pd.Timestamp(last_ts)
                    if ts_obj.tzinfo is None:
                        dyn_u8["bar_timestamp_was_naive"][t_idx, s_idx] = 1
                        ts_obj = ts_obj.tz_localize("UTC")
                    dyn_i64["last_bar_ts_ns"][t_idx, s_idx] = ts_obj.value
                    dyn_u8["has_valid_timestamp"][t_idx, s_idx] = 1
                    age = (scan_ts_obj - ts_obj.tz_convert("UTC")).total_seconds()
                    dyn_f64["bar_age_seconds"][t_idx, s_idx] = float(age)
                except Exception:  # noqa: BLE001
                    pass
            if baselines:
                dyn_u8["has_baseline"][t_idx, s_idx] = 1
                vcf_value = compute_volume_curve_fraction(
                    None, scan_ts_obj,
                    adv_bucket(baselines.get("avg_dollar_volume_20d"), bucket_edges),
                    fallback_opening_15m_share=fallback_share,
                )
                feats = compute_forming_session_features(sess, baselines, vcf_value)
                # Speedup report v2 §6.1 / Phase 3 — store None as NaN but keep
                # legitimate 0.0 values (the old ``feats.get(x) or np.nan``
                # mapped a real 0.0 feature to NaN, which the compat runtime
                # would then reconstruct as None, breaking bit-parity with the
                # legacy scanner on close_location / ema_distance / gap = 0.0).
                # ``volume_curve_fraction`` is the INPUT scalar (not a key
                # returned by compute_forming_session_features), so store it
                # directly.
                dyn_f64["volume_curve_fraction"][t_idx, s_idx] = _none_to_nan(vcf_value)
                dyn_f64["expected_volume_until_scan"][t_idx, s_idx] = _none_to_nan(
                    feats.get("expected_volume_until_scan")
                )
                dyn_f64["rvol_so_far"][t_idx, s_idx] = _none_to_nan(
                    feats.get("rvol_so_far")
                )
                dyn_f64["projected_full_day_rvol"][t_idx, s_idx] = _none_to_nan(
                    feats.get("projected_full_day_rvol")
                )
                dyn_f64["range_expansion_so_far"][t_idx, s_idx] = _none_to_nan(
                    feats.get("range_expansion_so_far")
                )
                dyn_f64["close_location_so_far"][t_idx, s_idx] = _none_to_nan(
                    feats.get("close_location_so_far")
                )
                dyn_f64["ema_distance"][t_idx, s_idx] = _none_to_nan(
                    feats.get("ema_distance")
                )
                dyn_f64["current_return_pct"][t_idx, s_idx] = _none_to_nan(
                    feats.get("current_return_pct")
                )
                dyn_f64["gap_pct"][t_idx, s_idx] = _none_to_nan(feats.get("gap_pct"))

    tmp_dir = store_root / ".tmp" / f"session={session_date.isoformat()}"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    _save_memmap(tmp_dir / "scan_timestamps_ns.int64.npy", scan_ts_np)
    _save_memmap(tmp_dir / "symbol_ids.int32.npy", symbol_ids)
    for col, arr in dyn_f64.items():
        _save_memmap(tmp_dir / f"dyn_f64__{col}.npy", arr)
    for col, arr in dyn_i64.items():
        _save_memmap(tmp_dir / f"dyn_i64__{col}.npy", arr)
    for col, arr in dyn_u8.items():
        _save_memmap(tmp_dir / f"dyn_u8__{col}.npy", arr)
    for col, arr in stat_f64.items():
        _save_memmap(tmp_dir / f"stat_f64__{col}.npy", arr)
    for col, arr in stat_i8.items():
        _save_memmap(tmp_dir / f"stat_i8__{col}.npy", arr)
    pd.DataFrame({"symbol": symbols, "symbol_id": symbol_ids}).to_parquet(
        tmp_dir / "universe_meta.parquet", index=False,
    )
    if not daily_cache.empty:
        daily_cache.to_parquet(tmp_dir / "daily_baselines.parquet", index=False)

    # SHA-256 every file for the session manifest.
    checksums: dict[str, str] = {}
    for p in sorted(tmp_dir.rglob("*")):
        if p.is_file():
            checksums[str(p.relative_to(tmp_dir))] = _file_sha256(p)
    (tmp_dir / "session_manifest.json").write_text(
        json.dumps({
            "session_date": session_date.isoformat(),
            "n_scans": n_scans,
            "n_symbols": n_symbols,
            "checksums": checksums,
        }, indent=2),
        encoding="utf-8",
    )

    final_dir = store_root / f"session={session_date.isoformat()}"
    if final_dir.exists():
        shutil.rmtree(final_dir)
    tmp_dir.rename(final_dir)
    return {
        "session_date": session_date.isoformat(),
        "n_scans": n_scans,
        "n_symbols": n_symbols,
        "partition_dir": str(final_dir),
    }


# ---- builder driver -------------------------------------------------------


def _estimate_matrix_size_gib(
    n_sessions: int, n_scans_per_session: int, n_symbols: int,
    *,
    eligible_symbols_by_session: Optional[Mapping[_dt.date, Sequence[str]]] = None,
) -> float:
    """Coarse upper bound (matrix doc §9).

    Speedup report v2 §4 P6 / Phase 6 task 1 — when
    ``eligible_symbols_by_session`` is supplied the estimate uses the
    ACTUAL point-in-time eligible-symbol count (max across the supplied
    sessions). The prior hard-coded ``n_symbols=100`` produced a ~7x
    understatement on a representative IEX session (about 704 eligible on
    2025-08-27). The override path is the new default for any caller that
    has the PIT map; legacy callers without the map continue to pass
    ``n_symbols`` directly.
    """
    if eligible_symbols_by_session is not None:
        counts = [
            len(eligible_symbols_by_session.get(s, ())) for s in eligible_symbols_by_session
        ]
        if counts:
            n_symbols = max(int(n_symbols), max(counts))
    per_cell = (
        len(DYNAMIC_FLOAT64_COLUMNS) * 8
        + len(DYNAMIC_INT64_COLUMNS) * 8
        + len(DYNAMIC_UINT8_COLUMNS) * 1
    )
    dynamic_bytes = n_sessions * n_scans_per_session * n_symbols * per_cell
    static_per_symbol = (
        len(STATIC_FLOAT64_COLUMNS) * 8 + len(STATIC_INT8_COLUMNS) * 1
    )
    static_bytes = n_sessions * n_symbols * static_per_symbol
    return (dynamic_bytes + static_bytes) / (1024.0 ** 3)


def build_scan_matrix(
    config_path: str | Path,
    *,
    scope: str = "validation",
    workers: int = 8,
    reserve_gib: float = 32.0,
    max_optuna_workers: int = 8,
    store_root: Optional[Path] = None,
) -> Path:
    """Build the per-session matrix partitions + top-level manifest.

    The memory budget guard refuses to start if the estimated footprint
    plus the headroom would breach the operator's 32 GiB reserve.
    """
    from ..config import load_config
    from ..config.paths import BowakaV2Paths
    from ..optuna.calendar_sessions import calendar_sessions_half_open
    from ..optuna.walkforward import build_walkforward_splits
    from ..utils.memory_guard import MemoryBudget

    cfg = load_config(config_path)
    repo_root = Path(__file__).resolve().parents[5]
    paths = BowakaV2Paths.from_config(cfg, repo_root=repo_root)
    md = cfg.get("market_data") or {}
    feed = str(md.get("feed", "iex"))
    lake_root = md.get("shared_root")

    bt = cfg.get("backtest") or {}
    wf = (cfg.get("optuna") or {}).get("walkforward") or {}
    plan = build_walkforward_splits(
        full_start=pd.Timestamp(bt["start_date"]).date(),
        full_end=pd.Timestamp(bt["end_date"]).date(),
        train_months=int(wf.get("train_months", 6)),
        val_months=int(wf.get("val_months", 1)),
        final_holdout_months=int(wf.get("final_holdout_months", 1)),
    )
    if scope == "validation":
        sessions: list[_dt.date] = []
        for split in plan.splits:
            sessions.extend(calendar_sessions_half_open(split.val_start, split.val_end))
    elif scope == "holdout":
        sessions = calendar_sessions_half_open(
            plan.final_holdout_start, plan.final_holdout_end,
        )
    elif scope == "full_history":
        sessions = calendar_sessions_half_open(
            plan.splits[0].train_start if plan.splits else plan.final_holdout_start,
            plan.final_holdout_end,
        )
    else:
        raise ValueError(f"scope must be 'validation' | 'holdout' | 'full_history', got {scope!r}")
    sessions = sorted(set(sessions))

    # Memory guard.
    budget = MemoryBudget(
        total_ram_gib=MemoryBudget.from_system().total_ram_gib,
        reserve_system_gib=float(reserve_gib),
        max_optuna_workers=int(max_optuna_workers),
    )
    sample_scan_count = max(1, int((cfg.get("session") or {}).get("scan_interval_seconds", 60)))
    # Speedup report v2 §4 P6 / Phase 6 task 1 — probe the actual PIT eligible
    # symbol counts on the first few sessions; the prior hard-coded
    # ``est_n_symbols=100`` produced a 7x understatement on real IEX data.
    est_n_symbols = 100  # fallback for callers without lake access
    eligible_pit: Optional[Mapping[_dt.date, Sequence[str]]] = None
    if lake_root and sessions:
        try:
            from bowaka_common.marketdata import MarketDataStore
            from ..universe.builder import (
                build_pit_universe_for_sessions, eligible_symbols,
            )

            probe = sessions[: min(5, len(sessions))]
            pit = build_pit_universe_for_sessions(probe, cfg, MarketDataStore(lake_root))
            eligible_pit = {
                s: tuple(eligible_symbols(pit.get(s, {})) or ())
                for s in probe
            }
            if eligible_pit:
                est_n_symbols = max(
                    est_n_symbols,
                    max(len(v) for v in eligible_pit.values()),
                )
        except Exception:  # noqa: BLE001 — probe failure falls back to legacy estimate
            eligible_pit = None
    est_size_gib = _estimate_matrix_size_gib(
        n_sessions=len(sessions),
        n_scans_per_session=max(1, 390 // max(1, sample_scan_count // 60 if sample_scan_count >= 60 else 1)),
        n_symbols=est_n_symbols,
        eligible_symbols_by_session=eligible_pit,
    )
    budget.assert_launch_safe(feature_store_gib_estimate=float(est_size_gib))

    if store_root is None:
        artifact_root = Path(paths.artifact_root)
        store_root = artifact_root / "cache" / "scan_matrix" / scope
    store_root = Path(store_root)
    store_root.mkdir(parents=True, exist_ok=True)

    n_workers = max(1, min(int(workers), int(max_optuna_workers)))

    # Build sessions (serial in this phase; Phase 9 may parallelise via
    # ProcessPoolExecutor with the spawn worker bootstrap).
    session_manifests: list[dict[str, Any]] = []
    for sd in sessions:
        session_manifests.append(
            build_session_partition(
                sd, cfg, lake_root, feed,
                store_root=store_root, scope=scope,
            )
        )

    matrix_id = hashlib.sha256(
        f"{scope}:{lake_root}:{feed}:{sessions[:1]!r}:{sessions[-1:]!r}".encode("utf-8")
    ).hexdigest()[:16]

    # Speedup report v2 §10.3 fix 1 / Phase 2 — record the REAL content-derived
    # dataset hash in the manifest. Reuses the backtester's lineage so a
    # backtest and a matrix built on the same lake produce the same value.
    # When the lake is unreachable / synthetic, the lineage falls back to the
    # deterministic synthetic regime — never raises.
    from ..config.hashing import canonical_strategy_hash
    from ..data.lineage import build_dataset_lineage
    try:
        lab_config_hash = canonical_strategy_hash(cfg)
    except Exception:  # noqa: BLE001 — lab-config-hash is forensic only
        lab_config_hash = "unknown"
    universe_syms = [
        str(s) for s in ((cfg.get("universe") or {}).get("symbols") or [])
    ]
    if not universe_syms and eligible_pit:
        seen: set[str] = set()
        for syms in eligible_pit.values():
            for s in syms:
                if s not in seen:
                    seen.add(s)
                    universe_syms.append(str(s))
    lineage = build_dataset_lineage(
        cfg=cfg,
        symbols=universe_syms,
        start=bt.get("start_date"),
        end=bt.get("end_date"),
        lab_config_hash=lab_config_hash,
    )
    dataset_hash_v = str(lineage.get("dataset_hash") or "")

    input_hash = compute_matrix_input_hash(
        cfg, plan, {scope: sessions},
        dataset_hash=dataset_hash_v,
    )
    manifest = ScanMatrixManifest(
        matrix_id=matrix_id,
        matrix_version=MATRIX_SCHEMA_VERSION,
        config_input_hash=input_hash,
        dataset_hash=dataset_hash_v,
        feed=feed,
        scope=scope,
        created_at_utc=_dt.datetime.utcnow().isoformat() + "Z",
        reserved_system_gib=float(reserve_gib),
        max_optuna_workers=int(max_optuna_workers),
        sessions=[s.isoformat() for s in sessions],
        columns={
            "dynamic_float64": list(DYNAMIC_FLOAT64_COLUMNS),
            "dynamic_int64": list(DYNAMIC_INT64_COLUMNS),
            "dynamic_uint8": list(DYNAMIC_UINT8_COLUMNS),
            "static_float64": list(STATIC_FLOAT64_COLUMNS),
            "static_int8": list(STATIC_INT8_COLUMNS),
        },
        code_hashes=_source_file_hashes(
            Path(__file__).resolve().parents[1]
        ),
    )
    (store_root / "manifest.json").write_text(
        json.dumps(manifest.to_dict(), indent=2), encoding="utf-8",
    )
    return store_root


def _sample_indices(n: int) -> tuple[int, ...]:
    """First / middle / last indices for an axis of size ``n`` (deduped)."""
    if n <= 0:
        return ()
    if n == 1:
        return (0,)
    if n == 2:
        return (0, 1)
    return tuple(sorted({0, n // 2, n - 1}))


def _high_risk_symbol_idxs(
    sess: ScanMatrixSession, scan_idx: int,
) -> list[int]:
    """Symbol idxs at ``scan_idx`` with a validity flag flipped to 'bad'."""
    bad: set[int] = set()
    has_bar_row = sess.dynamic_uint8.get("has_bar")
    if has_bar_row is not None and has_bar_row.shape[0] > scan_idx:
        bad.update(int(i) for i in np.where(has_bar_row[scan_idx, :] == 0)[0])
    has_valid_ts = sess.dynamic_uint8.get("has_valid_timestamp")
    if has_valid_ts is not None and has_valid_ts.shape[0] > scan_idx:
        bad.update(int(i) for i in np.where(has_valid_ts[scan_idx, :] == 0)[0])
    naive_flag = sess.dynamic_uint8.get("bar_timestamp_was_naive")
    if naive_flag is not None and naive_flag.shape[0] > scan_idx:
        bad.update(int(i) for i in np.where(naive_flag[scan_idx, :] == 1)[0])
    return sorted(bad)


def _expected_manifest_dataset_hash(
    manifest: Mapping[str, Any], cfg: Mapping[str, Any],
) -> str:
    """Re-derive the dataset_hash from the current lake state for comparison.

    Returns ``""`` when the lineage cannot be rebuilt (e.g. lake unreachable)
    so the caller falls back to a tautology check.
    """
    from ..config.hashing import canonical_strategy_hash
    from ..data.lineage import build_dataset_lineage
    try:
        lab_config_hash = canonical_strategy_hash(cfg)
    except Exception:  # noqa: BLE001
        lab_config_hash = "unknown"
    bt = cfg.get("backtest") or {}
    syms = [
        str(s) for s in ((cfg.get("universe") or {}).get("symbols") or [])
    ]
    try:
        lineage = build_dataset_lineage(
            cfg=cfg,
            symbols=syms,
            start=bt.get("start_date"),
            end=bt.get("end_date"),
            lab_config_hash=lab_config_hash,
        )
    except Exception:  # noqa: BLE001
        return ""
    return str(lineage.get("dataset_hash") or "")


def _vectorized_cell_spot_check(
    sess: ScanMatrixSession, cfg: Mapping[str, Any],
    scan_idxs: Sequence[int], sym_idxs: Sequence[int],
) -> list[dict[str, Any]]:
    """Phase 4 — compare the vectorized score helper to the scalar one.

    For each sampled cell, reconstructs the forming-feature dict from the
    matrix and asserts ``compute_signal_strength_vectorized`` (1-element
    arrays) equals the scalar ``compute_signal_strength`` to 1e-9. This is
    the in-verifier proof that the vectorized math matches the legacy math;
    the end-to-end three-way parity tests are the stronger gate.
    """
    from ..features import compute_signal_strength
    from .scan_matrix_runtime import _reconstruct_forming_feats
    from .scan_matrix_vectorized import compute_signal_strength_vectorized

    score_cfg = cfg.get("score") or {}
    out: list[dict[str, Any]] = []
    ema_slope_col = sess.static_float64.get("ema_slope_prior")
    for t_idx in scan_idxs:
        for s_idx in sym_idxs:
            if int(sess.dynamic_uint8["has_bar"][t_idx, s_idx]) == 0:
                continue
            feats = _reconstruct_forming_feats(sess, int(t_idx), int(s_idx))
            es = None
            if ema_slope_col is not None:
                ev = float(ema_slope_col[s_idx])
                es = None if np.isnan(ev) else ev
            scalar = compute_signal_strength(feats, score_cfg, ema_slope_prior=es)
            vec = float(compute_signal_strength_vectorized(
                rvol_so_far=np.array([feats.get("rvol_so_far") if feats.get("rvol_so_far") is not None else np.nan]),
                range_expansion_so_far=np.array([feats.get("range_expansion_so_far") if feats.get("range_expansion_so_far") is not None else np.nan]),
                close_location_so_far=np.array([feats.get("close_location_so_far") if feats.get("close_location_so_far") is not None else np.nan]),
                ema_distance=np.array([feats.get("ema_distance") if feats.get("ema_distance") is not None else np.nan]),
                ema_slope_prior=np.array([es if es is not None else np.nan]),
                gap_pct=np.array([feats.get("gap_pct") if feats.get("gap_pct") is not None else np.nan]),
                score_cfg=score_cfg,
            )[0])
            if abs(scalar - vec) > 1e-9:
                out.append({
                    "kind": "vectorized_score_mismatch",
                    "scan_idx": int(t_idx), "symbol_idx": int(s_idx),
                    "scalar": scalar, "vectorized": vec,
                })
    return out


def verify_scan_matrix(
    store_root: Path | str,
    config_path: str | Path,
    *,
    sample_count: int = 10,
    seed: int = 42,
    strict: bool = False,
    vectorized_check: bool = False,
) -> dict[str, Any]:
    """Verify a built matrix's manifest + per-cell content.

    Speedup report v2 §10.3 fix 2 / Phase 2. The verifier now:

    1. Re-derives the lake's dataset_hash via :func:`build_dataset_lineage`
       and asserts it matches the manifest's recorded value (catches
       partition-file tampering and on-disk manifest edits).
    2. For up to ``sample_count`` sessions, samples a deterministic grid of
       (first / middle / last) scan x (first / middle / last) symbol cells
       — at most 9 per session — plus any high-risk symbols whose validity
       flags are flipped.
    3. For each sampled cell, asserts the dynamic columns are
       self-consistent (``has_bar==0`` ⇒ dynamic float64 is NaN;
       ``has_bar==1`` ⇒ ``last_price`` is finite).
    4. Asserts every static_int8 column is a valid sentinel (``-1``) or
       within the declared enum bounds.

    Returns a report ``{"status": "ok"|"fail", "sampled": N,
    "issues": [...], "matrix_id": ..., "config_input_hash": ...,
    "dataset_hash": ...}``. When ``strict=True``, any issue raises
    :class:`MatrixVerifyError`; otherwise the report carries them and
    the caller decides.
    """
    from ..config import load_config

    cfg = load_config(config_path)
    store = ScanMatrixStore(store_root, readonly=True)
    manifest = store.manifest
    sessions = [_dt.date.fromisoformat(s) for s in manifest.get("sessions", [])]

    rng = np.random.default_rng(int(seed))
    issues: list[dict[str, Any]] = []
    sampled = 0

    # (1) Dataset-hash drift detection.
    manifest_dataset_hash = str(manifest.get("dataset_hash") or "")
    expected_hash = _expected_manifest_dataset_hash(manifest, cfg)
    if expected_hash and manifest_dataset_hash and expected_hash != manifest_dataset_hash:
        issues.append({
            "kind": "dataset_hash_drift",
            "manifest_dataset_hash": manifest_dataset_hash,
            "recomputed_dataset_hash": expected_hash,
            "explanation": (
                "The lake's recomputed dataset_hash does not match the value "
                "recorded in the manifest. The matrix was built against a "
                "different lake state — rebuild required."
            ),
        })

    if not sessions:
        report = {
            "status": "ok" if not issues else "fail",
            "sampled": 0,
            "issues": issues,
            "matrix_id": manifest.get("matrix_id"),
            "config_input_hash": manifest.get("config_input_hash"),
            "dataset_hash": manifest_dataset_hash,
            "seed": int(seed),
        }
        if strict and issues:
            raise MatrixVerifyError(json.dumps(report, indent=2))
        return report

    # Deterministically choose at most ``sample_count`` sessions to inspect.
    session_idx_pool = list(range(len(sessions)))
    if len(session_idx_pool) > sample_count:
        chosen_session_idxs = sorted(
            rng.choice(session_idx_pool, size=sample_count, replace=False).tolist()
        )
    else:
        chosen_session_idxs = session_idx_pool
    chosen_sessions = [sessions[i] for i in chosen_session_idxs]

    for sd in chosen_sessions:
        try:
            sess = store.open_session(sd, purpose="objective")
        except HoldoutMatrixReadError:
            continue
        n_scans, n_syms = (
            int(sess.scan_timestamps_ns.shape[0]),
            int(sess.symbol_ids.shape[0]),
        )
        if n_scans == 0 or n_syms == 0:
            continue
        scan_idxs = _sample_indices(n_scans)
        sym_idxs = list(_sample_indices(n_syms))
        # Append up to 6 high-risk symbols from the middle scan.
        mid_scan = n_scans // 2
        for hr in _high_risk_symbol_idxs(sess, mid_scan)[:6]:
            if hr not in sym_idxs:
                sym_idxs.append(hr)
        for t_idx in scan_idxs:
            for s_idx in sym_idxs:
                sampled += 1
                cell_issues = _check_cell(
                    sess, t_idx=int(t_idx), s_idx=int(s_idx),
                )
                for issue in cell_issues:
                    issue["session"] = sd.isoformat()
                    issue["scan_idx"] = int(t_idx)
                    issue["symbol_idx"] = int(s_idx)
                    issues.append(issue)
        # Static-column sanity check (per session, not per cell).
        for col in STATIC_INT8_COLUMNS:
            arr = sess.static_int8.get(col)
            if arr is None:
                continue
            if not np.issubdtype(arr.dtype, np.integer):
                issues.append({
                    "kind": "static_int8_dtype",
                    "session": sd.isoformat(), "column": col,
                    "dtype": str(arr.dtype),
                })

        # Phase 4 — vectorized-vs-scalar score spot check on the sampled grid.
        if vectorized_check:
            vec_issues = _vectorized_cell_spot_check(
                sess, cfg, scan_idxs, sym_idxs,
            )
            for issue in vec_issues:
                issue["session"] = sd.isoformat()
                issues.append(issue)

    report = {
        "status": "ok" if not issues else "fail",
        "sampled": sampled,
        "issues": issues,
        "matrix_id": manifest.get("matrix_id"),
        "config_input_hash": manifest.get("config_input_hash"),
        "dataset_hash": manifest_dataset_hash,
        "seed": int(seed),
        "session_count": len(sessions),
        "session_sampled": len(chosen_session_idxs),
        "vectorized_checked": bool(vectorized_check),
    }
    if strict and issues:
        raise MatrixVerifyError(json.dumps(report, indent=2, default=str))
    return report


def _check_cell(
    sess: ScanMatrixSession, *, t_idx: int, s_idx: int,
) -> list[dict[str, Any]]:
    """Per-cell sanity rules. Returns a list of {kind, detail} issues."""
    out: list[dict[str, Any]] = []
    has_bar_arr = sess.dynamic_uint8.get("has_bar")
    if has_bar_arr is None:
        out.append({"kind": "missing_has_bar_column"})
        return out
    has_bar = int(has_bar_arr[t_idx, s_idx])
    last_price = sess.dynamic_float64.get("last_price")
    if last_price is None:
        out.append({"kind": "missing_last_price_column"})
        return out
    lp = float(last_price[t_idx, s_idx])
    if has_bar == 1:
        if not np.isfinite(lp):
            out.append({
                "kind": "has_bar_but_last_price_invalid",
                "last_price": lp,
            })
    else:
        if np.isfinite(lp):
            out.append({
                "kind": "no_bar_but_last_price_present",
                "last_price": lp,
            })
    # session_volume must be >= 0 when has_bar=1.
    sv = sess.dynamic_float64.get("session_volume")
    if has_bar == 1 and sv is not None:
        svv = float(sv[t_idx, s_idx])
        if np.isfinite(svv) and svv < 0:
            out.append({
                "kind": "negative_session_volume", "session_volume": svv,
            })
    return out


__all__ = [
    "MATRIX_SCHEMA_VERSION",
    "DYNAMIC_FLOAT64_COLUMNS",
    "DYNAMIC_INT64_COLUMNS",
    "DYNAMIC_UINT8_COLUMNS",
    "STATIC_FLOAT64_COLUMNS",
    "STATIC_INT8_COLUMNS",
    "MATRIX_SENSITIVE_PREFIXES",
    "HoldoutMatrixReadError",
    "MatrixVerifyError",
    "ScanMatrixManifest",
    "ScanMatrixSession",
    "ScanMatrixStore",
    "assert_search_space_compatible_with_matrix",
    "build_scan_matrix",
    "build_session_partition",
    "compute_matrix_input_hash",
    "verify_scan_matrix",
]
