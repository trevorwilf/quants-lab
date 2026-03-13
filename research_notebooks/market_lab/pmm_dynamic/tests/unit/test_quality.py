"""Tests for data quality audit."""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from pmm_lab.data.quality import run_audit
from tests.conftest import CANDLE_DTYPE


def test_run_audit_produces_all_fields(sample_candles_5m):
    """Audit result has all expected fields populated."""
    audit = run_audit(sample_candles_5m, "5m")
    assert audit.total_rows == 100
    assert audit.first_timestamp > 0
    assert audit.last_timestamp > audit.first_timestamp
    assert audit.expected_rows > 0
    assert isinstance(audit.missing_rows, int)
    assert isinstance(audit.duplicate_count, int)
    assert isinstance(audit.null_counts, dict)
    assert isinstance(audit.ohlc_violations, int)
    assert isinstance(audit.ohlc_violation_details, dict)
    assert isinstance(audit.volume_zero_count, int)
    assert isinstance(audit.volume_zero_fraction, float)
    assert isinstance(audit.dataset_hash, str)
    assert isinstance(audit.interval_seconds, int)
    assert isinstance(audit.gap_histogram, dict)
    assert isinstance(audit.longest_gap_seconds, int)
    assert isinstance(audit.passed_strict, bool)
    assert isinstance(audit.failure_reasons, list)


def test_run_audit_json_output(sample_candles_5m):
    """Audit writes valid JSON to output_path."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        tmp_path = f.name

    audit = run_audit(sample_candles_5m, "5m", output_path=tmp_path)

    with open(tmp_path, "r") as f:
        data = json.load(f)

    assert data["total_rows"] == audit.total_rows
    assert data["dataset_hash"] == audit.dataset_hash
    assert "close_percentiles" in data
    assert "volume_percentiles" in data

    Path(tmp_path).unlink(missing_ok=True)


def test_audit_includes_hash(sample_candles_5m):
    """Audit result includes a 64-char hex hash."""
    audit = run_audit(sample_candles_5m, "5m")
    assert len(audit.dataset_hash) == 64
    assert all(c in "0123456789abcdef" for c in audit.dataset_hash)


def test_audit_volume_zero_stats():
    """Audit correctly counts volume=0 candles."""
    rng = np.random.default_rng(seed=55)
    n = 20
    rows = []
    for i in range(n):
        ts = 1756833000 + i * 300
        o = 100000.0 + rng.normal(0, 10)
        c = 100000.0 + rng.normal(0, 10)
        h = max(o, c) + abs(rng.normal(0, 5))
        lo = min(o, c) - abs(rng.normal(0, 5))
        lo = max(lo, 0.01)
        vol = rng.uniform(0.1, 1.0)
        rows.append((ts, o, h, lo, c, vol, False))

    arr = np.array(rows, dtype=CANDLE_DTYPE)
    # Set 3 rows to volume=0
    arr["volume"][2] = 0.0
    arr["volume"][7] = 0.0
    arr["volume"][15] = 0.0

    audit = run_audit(arr, "5m")
    assert audit.volume_zero_count == 3
    assert abs(audit.volume_zero_fraction - 3 / 20) < 1e-9
