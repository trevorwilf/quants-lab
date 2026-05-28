"""Phase 2 §3 — corruption helpers for ``verify_scan_matrix`` tests.

Each helper mutates one byte / one cell of a built matrix on disk so the
verifier's drift detection can be exercised end-to-end. Helpers return the
``store_root`` so callers can chain into ``verify_scan_matrix(...)``.

Mutation kinds (the prompt's required four, plus a parquet-byte mutator):
    * ``corrupt_dynamic_float_cell``        — one ``last_price`` cell
    * ``corrupt_validity_flag_cell``         — one ``has_bar`` flag
    * ``corrupt_static_float_column``        — one ``prior_close`` value
    * ``mutate_manifest_dataset_hash``       — flip the manifest's hash
    * ``corrupt_one_parquet_partition_byte`` — flip a byte in a parquet file
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np


def _open_dynamic_f64_memmap(session_dir: Path, column: str) -> np.ndarray:
    """Return a writeable memmap onto one dynamic_float64 column."""
    return np.lib.format.open_memmap(
        session_dir / f"dyn_f64__{column}.npy", mode="r+",
    )


def _open_dynamic_u8_memmap(session_dir: Path, column: str) -> np.ndarray:
    return np.lib.format.open_memmap(
        session_dir / f"dyn_u8__{column}.npy", mode="r+",
    )


def _open_static_f64_memmap(session_dir: Path, column: str) -> np.ndarray:
    return np.lib.format.open_memmap(
        session_dir / f"stat_f64__{column}.npy", mode="r+",
    )


def _first_session_dir(store_root: Path) -> Path:
    """Pick the first ``session=YYYY-MM-DD`` partition."""
    dirs = sorted(store_root.glob("session=*"))
    if not dirs:
        raise FileNotFoundError(f"no session partitions under {store_root}")
    return dirs[0]


def _all_session_dirs(store_root: Path) -> list[Path]:
    """Every ``session=YYYY-MM-DD`` partition under the store root."""
    dirs = sorted(store_root.glob("session=*"))
    if not dirs:
        raise FileNotFoundError(f"no session partitions under {store_root}")
    return dirs


def corrupt_dynamic_float_cell(
    store_root: Path, *, column: str = "last_price",
    scan_idx: int = 0, sym_idx: int = 0,
    value: float = -999999.0,
    all_sessions: bool = False,
) -> Path:
    """Overwrite one ``(scan_idx, sym_idx)`` cell in a dynamic_float64 column.

    When ``all_sessions=True`` the same mutation is applied to every session
    partition, so a random sub-sample of sessions still hits a corrupted
    cell.
    """
    sess_dirs = _all_session_dirs(store_root) if all_sessions else [_first_session_dir(store_root)]
    for sess_dir in sess_dirs:
        arr = _open_dynamic_f64_memmap(sess_dir, column)
        if arr.shape[0] > scan_idx and arr.shape[1] > sym_idx:
            arr[scan_idx, sym_idx] = value
            arr.flush()
    return store_root


def corrupt_validity_flag_cell(
    store_root: Path, *, column: str = "has_bar",
    scan_idx: int = 0, sym_idx: int = 0,
    value: int = 0,
    all_sessions: bool = False,
) -> Path:
    """Flip one ``(scan_idx, sym_idx)`` flag in a dynamic_uint8 column.

    Default: turn ``has_bar`` off at (0, 0). The verifier should detect that
    other columns (e.g. ``last_price``) still carry data, indicating drift.
    """
    sess_dirs = _all_session_dirs(store_root) if all_sessions else [_first_session_dir(store_root)]
    for sess_dir in sess_dirs:
        arr = _open_dynamic_u8_memmap(sess_dir, column)
        if arr.shape[0] > scan_idx and arr.shape[1] > sym_idx:
            arr[scan_idx, sym_idx] = int(value)
            arr.flush()
    return store_root


def corrupt_static_float_column(
    store_root: Path, *, column: str = "prior_close",
    sym_idx: int = 0,
    value: float = -1.0,
    all_sessions: bool = False,
) -> Path:
    """Overwrite one static_float64 column value."""
    sess_dirs = _all_session_dirs(store_root) if all_sessions else [_first_session_dir(store_root)]
    for sess_dir in sess_dirs:
        arr = _open_static_f64_memmap(sess_dir, column)
        if arr.shape[0] > sym_idx:
            arr[sym_idx] = value
            arr.flush()
    return store_root


def mutate_manifest_dataset_hash(
    store_root: Path,
    *,
    replacement: str = "sha256:0000000000000000000000000000000000000000000000000000000000000000",
) -> Path:
    """Rewrite the manifest's ``dataset_hash`` field to a known-bad value."""
    manifest_path = store_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["dataset_hash"] = replacement
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return store_root


def corrupt_one_parquet_partition_byte(store_root: Path) -> Path:
    """Flip a single byte inside the first ``*.parquet`` under store_root."""
    parquets = sorted(store_root.rglob("*.parquet"))
    if not parquets:
        raise FileNotFoundError(f"no *.parquet under {store_root}")
    target = parquets[0]
    raw = target.read_bytes()
    # Flip a byte in the middle of the file (avoid the magic header / footer).
    pos = max(1, len(raw) // 2)
    flipped = raw[:pos] + bytes([raw[pos] ^ 0xFF]) + raw[pos + 1:]
    target.write_bytes(flipped)
    return store_root
