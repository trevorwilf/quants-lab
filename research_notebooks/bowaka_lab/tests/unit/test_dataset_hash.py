"""Phase 1: dataset hash tests."""

from __future__ import annotations

import pandas as pd
import pytest

from bowaka_lab.data.dataset_hash import hash_dataframe, hash_documents, hash_parquet_files


def test_hash_dataframe_stable_under_row_reorder():
    df1 = pd.DataFrame({"k": [1, 2, 3], "v": [10, 20, 30]})
    df2 = pd.DataFrame({"k": [3, 1, 2], "v": [30, 10, 20]})
    h1 = hash_dataframe(df1, sort_by=["k"])
    h2 = hash_dataframe(df2, sort_by=["k"])
    assert h1 == h2


def test_hash_dataframe_changes_on_real_diff():
    df1 = pd.DataFrame({"k": [1, 2], "v": [10, 20]})
    df2 = pd.DataFrame({"k": [1, 2], "v": [10, 99]})
    assert hash_dataframe(df1, sort_by=["k"]) != hash_dataframe(df2, sort_by=["k"])


def test_hash_dataframe_empty():
    h = hash_dataframe(pd.DataFrame())
    assert h.startswith("sha256:")


def test_hash_documents_stable_under_reorder():
    docs1 = [{"k": 1, "v": "a"}, {"k": 2, "v": "b"}]
    docs2 = [{"k": 2, "v": "b"}, {"k": 1, "v": "a"}]
    assert hash_documents(docs1, sort_keys=["k"]) == hash_documents(docs2, sort_keys=["k"])


def test_hash_documents_changes_on_diff():
    a = [{"k": 1, "v": "a"}]
    b = [{"k": 1, "v": "z"}]
    assert hash_documents(a, sort_keys=["k"]) != hash_documents(b, sort_keys=["k"])


def test_hash_parquet_files(tmp_path):
    f1 = tmp_path / "a.parquet"
    f2 = tmp_path / "b.parquet"
    pd.DataFrame({"x": [1, 2]}).to_parquet(f1, index=False)
    pd.DataFrame({"x": [3, 4]}).to_parquet(f2, index=False)
    h = hash_parquet_files([f1, f2])
    assert h.startswith("sha256:")
    # Order of paths should not matter, since sorting is internal.
    h2 = hash_parquet_files([f2, f1])
    assert h == h2
