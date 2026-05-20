"""Dataset hashing determinism (moved from v1)."""
from __future__ import annotations

import pandas as pd

from bowaka_common.storage.dataset_hash import hash_dataframe


def test_hash_dataframe_stable_for_same_content() -> None:
    df1 = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
    df2 = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
    assert hash_dataframe(df1) == hash_dataframe(df2)


def test_hash_dataframe_changes_for_different_content() -> None:
    df1 = pd.DataFrame({"a": [1, 2, 3]})
    df2 = pd.DataFrame({"a": [1, 2, 4]})
    assert hash_dataframe(df1) != hash_dataframe(df2)


def test_hash_starts_with_sha256_prefix() -> None:
    df = pd.DataFrame({"x": [1]})
    h = hash_dataframe(df)
    assert h.startswith("sha256:")
