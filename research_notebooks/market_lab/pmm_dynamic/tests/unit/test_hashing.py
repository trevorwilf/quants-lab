"""Tests for deterministic dataset hashing."""

import numpy as np
import pytest

from pmm_lab.data.hashing import hash_candles


def test_hash_deterministic(sample_candles_5m):
    """Same data produces identical hash."""
    h1 = hash_candles(sample_candles_5m)
    h2 = hash_candles(sample_candles_5m)
    assert h1 == h2


def test_hash_changes_with_data(sample_candles_5m):
    """Modifying a close price changes the hash."""
    h1 = hash_candles(sample_candles_5m)
    modified = sample_candles_5m.copy()
    modified["close"][0] += 1.0
    h2 = hash_candles(modified)
    assert h1 != h2


def test_hash_ignores_forward_fill_column(sample_candles_5m):
    """is_forward_fill column is excluded from hash."""
    h1 = hash_candles(sample_candles_5m)
    modified = sample_candles_5m.copy()
    modified["is_forward_fill"][0] = True
    h2 = hash_candles(modified)
    assert h1 == h2


def test_hash_different_for_different_slices(sample_candles_5m):
    """Different slices produce different hashes."""
    h1 = hash_candles(sample_candles_5m[:50])
    h2 = hash_candles(sample_candles_5m[:60])
    assert h1 != h2


def test_hash_is_64_char_hex(sample_candles_5m):
    """Hash is exactly 64 hex characters (SHA-256)."""
    h = hash_candles(sample_candles_5m)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)
