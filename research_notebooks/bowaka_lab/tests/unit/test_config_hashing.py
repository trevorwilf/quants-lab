"""Phase 1: stable hash tests."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from bowaka_lab.config.hashing import short, stable_hash


def test_hash_is_key_order_invariant():
    a = {"a": 1, "b": 2, "c": 3}
    b = {"c": 3, "a": 1, "b": 2}
    assert stable_hash(a) == stable_hash(b)


def test_hash_changes_on_substantive_change():
    a = {"a": 1, "b": 2}
    b = {"a": 1, "b": 3}
    assert stable_hash(a) != stable_hash(b)


def test_hash_handles_date_and_decimal_consistently():
    a = {"d": date(2026, 5, 15), "dec": Decimal("3.14")}
    b = {"d": date(2026, 5, 15), "dec": Decimal("3.14")}
    assert stable_hash(a) == stable_hash(b)


def test_hash_handles_numpy_scalars():
    h_int = stable_hash({"v": 1})
    h_np = stable_hash({"v": np.int64(1)})
    assert h_int == h_np


def test_hash_handles_pandas_timestamp():
    a = {"t": pd.Timestamp("2026-05-15 10:00:00")}
    b = {"t": pd.Timestamp("2026-05-15 10:00:00")}
    assert stable_hash(a) == stable_hash(b)


def test_hash_prefix_default():
    h = stable_hash({"x": 1})
    assert h.startswith("sha256:")


def test_hash_prefix_custom():
    h = stable_hash({"x": 1}, prefix="custom:")
    assert h.startswith("custom:")


def test_short_truncates_with_or_without_prefix():
    h = "sha256:0123456789abcdef0123456789"
    assert short(h, 8) == "01234567"
    assert short(h.split(":", 1)[1], 8) == "01234567"


def test_hash_handles_nested_structures():
    a = {"a": [1, 2, {"b": 3, "c": [4, 5]}], "z": True}
    b = {"z": True, "a": [1, 2, {"c": [4, 5], "b": 3}]}
    assert stable_hash(a) == stable_hash(b)


def test_hash_handles_pydantic_model():
    from bowaka_lab.config.models import ExitConfig

    c = ExitConfig()
    h1 = stable_hash(c)
    h2 = stable_hash(c.model_dump())
    assert h1 == h2


def test_hash_distinguishes_different_dates():
    a = {"d": date(2026, 5, 15)}
    b = {"d": date(2026, 5, 16)}
    assert stable_hash(a) != stable_hash(b)


def test_hash_handles_datetimes():
    a = {"t": datetime(2026, 5, 15, 10, 30)}
    b = {"t": datetime(2026, 5, 15, 10, 30)}
    assert stable_hash(a) == stable_hash(b)
