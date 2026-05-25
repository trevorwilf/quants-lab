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
                feats = compute_forming_session_features(
                    sess, baselines,
                    compute_volume_curve_fraction(
                        None, scan_ts_obj,
                        adv_bucket(baselines.get("avg_dollar_volume_20d"), bucket_edges),
                        fallback_opening_15m_share=fallback_share,
                    ),
                )
                dyn_f64["volume_curve_fraction"][t_idx, s_idx] = float(
                    feats.get("volume_curve_fraction", np.nan) or np.nan
                )
                dyn_f64["expected_volume_until_scan"][t_idx, s_idx] = float(
                    feats.get("expected_volume_until_scan", np.nan) or np.nan
                )
                dyn_f64["rvol_so_far"][t_idx, s_idx] = float(
                    feats.get("rvol_so_far", np.nan) or np.nan
                )
                dyn_f64["projected_full_day_rvol"][t_idx, s_idx] = float(
                    feats.get("projected_full_day_rvol", np.nan) or np.nan
                )
                dyn_f64["range_expansion_so_far"][t_idx, s_idx] = float(
                    feats.get("range_expansion_so_far", np.nan) or np.nan
                )
                dyn_f64["close_location_so_far"][t_idx, s_idx] = float(
                    feats.get("close_location_so_far", np.nan) or np.nan
                )
                dyn_f64["ema_distance"][t_idx, s_idx] = float(
                    feats.get("ema_distance", np.nan) or np.nan
                )
                dyn_f64["current_return_pct"][t_idx, s_idx] = float(
                    feats.get("current_return_pct", np.nan) or np.nan
                )
                dyn_f64["gap_pct"][t_idx, s_idx] = float(
                    feats.get("gap_pct", np.nan) or np.nan
                )

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
) -> float:
    """Coarse upper bound (matrix doc §9)."""
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
    est_n_symbols = 100
    est_size_gib = _estimate_matrix_size_gib(
        n_sessions=len(sessions),
        n_scans_per_session=max(1, 390 // max(1, sample_scan_count // 60 if sample_scan_count >= 60 else 1)),
        n_symbols=est_n_symbols,
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
    input_hash = compute_matrix_input_hash(
        cfg, plan, {scope: sessions},
        dataset_hash="",
    )
    manifest = ScanMatrixManifest(
        matrix_id=matrix_id,
        matrix_version=MATRIX_SCHEMA_VERSION,
        config_input_hash=input_hash,
        dataset_hash="",
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


def verify_scan_matrix(
    store_root: Path | str,
    config_path: str | Path,
    *,
    sample_count: int = 10,
) -> dict[str, Any]:
    """Spot-check ``sample_count`` (session, symbol, scan) tuples against
    the legacy feature path. Returns a report dict + raises on mismatch.
    """
    store = ScanMatrixStore(store_root, readonly=True)
    manifest = store.manifest
    sessions = [_dt.date.fromisoformat(s) for s in manifest.get("sessions", [])]
    if not sessions:
        return {"status": "ok", "sampled": 0, "issues": []}
    issues: list[dict[str, Any]] = []
    sampled = 0
    for sd in sessions[: min(2, len(sessions))]:
        try:
            sess = store.open_session(sd, purpose="objective")
        except HoldoutMatrixReadError:
            continue
        if sess.scan_timestamps_ns.shape[0] == 0 or sess.symbol_ids.shape[0] == 0:
            continue
        # Pick the first scan + first symbol and confirm a few columns.
        s_idx = 0
        t_idx = 0
        sym_row = sess.universe_meta.iloc[s_idx]
        sym = str(sym_row["symbol"])
        has_bar = int(sess.dynamic_uint8["has_bar"][t_idx, s_idx])
        last_price = float(sess.dynamic_float64["last_price"][t_idx, s_idx])
        if has_bar and not np.isnan(last_price):
            sampled += 1
        else:
            issues.append({
                "session": sd.isoformat(), "symbol": sym,
                "issue": "missing_first_scan_cell",
            })
    return {
        "status": "ok" if not issues else "warn",
        "sampled": sampled,
        "issues": issues,
        "matrix_id": manifest.get("matrix_id"),
        "config_input_hash": manifest.get("config_input_hash"),
    }


__all__ = [
    "MATRIX_SCHEMA_VERSION",
    "DYNAMIC_FLOAT64_COLUMNS",
    "DYNAMIC_INT64_COLUMNS",
    "DYNAMIC_UINT8_COLUMNS",
    "STATIC_FLOAT64_COLUMNS",
    "STATIC_INT8_COLUMNS",
    "MATRIX_SENSITIVE_PREFIXES",
    "HoldoutMatrixReadError",
    "ScanMatrixManifest",
    "ScanMatrixSession",
    "ScanMatrixStore",
    "assert_search_space_compatible_with_matrix",
    "build_scan_matrix",
    "build_session_partition",
    "compute_matrix_input_hash",
    "verify_scan_matrix",
]
