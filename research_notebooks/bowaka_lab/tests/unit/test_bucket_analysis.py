"""Unit tests for ``bowaka_lab.metrics.bucket_analysis``.

Covers the dict + JSON-string variant cases so the weekly report keeps working
after counterfactual frames have been round-tripped through parquet (which
serializes dict columns to JSON strings via ``utils.io.to_parquet_safe``).
"""

from __future__ import annotations

import json

import pandas as pd

from bowaka_lab.metrics.bucket_analysis import (
    summarize_by_entry_rule,
    summarize_by_exit_geometry,
    summarize_by_signal_fade_threshold,
)


def _rows_dict_variants():
    return [
        {"symbol": "AAA", "would_enter": True, "pnl_pct": 0.10, "first_touch": "target",
         "variant": {"entry_rule": "fixed_time_0935", "stop_pct": 0.08, "target_pct": 0.15}},
        {"symbol": "BBB", "would_enter": True, "pnl_pct": -0.08, "first_touch": "stop",
         "variant": {"entry_rule": "fixed_time_0935", "stop_pct": 0.08, "target_pct": 0.15}},
        {"symbol": "CCC", "would_enter": True, "pnl_pct": 0.02, "first_touch": "target",
         "variant": {"entry_rule": "fixed_time_0945", "stop_pct": 0.08, "target_pct": 0.15}},
    ]


def _rows_json_string_variants():
    """Same data as _rows_dict_variants but with variant pre-serialized to JSON
    strings, matching what comes back from parquet via to_parquet_safe."""
    rows = _rows_dict_variants()
    for r in rows:
        r["variant"] = json.dumps(r["variant"])
    return rows


def test_summarize_by_entry_rule_dict_variants():
    out = summarize_by_entry_rule(pd.DataFrame(_rows_dict_variants()))
    assert sorted(out["entry_rule"].tolist()) == ["fixed_time_0935", "fixed_time_0945"]
    rule_n = dict(zip(out["entry_rule"], out["n"]))
    assert rule_n["fixed_time_0935"] == 2
    assert rule_n["fixed_time_0945"] == 1


def test_summarize_by_entry_rule_json_string_variants():
    """Regression: variant column round-tripped through parquet is a JSON
    string, not a dict. The function must flatten it just the same."""
    out = summarize_by_entry_rule(pd.DataFrame(_rows_json_string_variants()))
    assert sorted(out["entry_rule"].tolist()) == ["fixed_time_0935", "fixed_time_0945"]
    rule_n = dict(zip(out["entry_rule"], out["n"]))
    assert rule_n["fixed_time_0935"] == 2
    assert rule_n["fixed_time_0945"] == 1


def test_summarize_by_entry_rule_returns_empty_schema_when_column_missing():
    """A counterfactuals frame from cf_exit alone (no entry_rule) must not raise."""
    df = pd.DataFrame(
        [{"symbol": "AAA", "would_enter": True, "pnl_pct": 0.1, "stop_pct": 0.08, "target_pct": 0.15}]
    )
    out = summarize_by_entry_rule(df)
    assert out.empty
    assert "entry_rule" in out.columns


def test_summarize_by_exit_geometry_json_string_variants():
    out = summarize_by_exit_geometry(pd.DataFrame(_rows_json_string_variants()))
    assert not out.empty
    assert {"stop_pct", "target_pct", "n"}.issubset(out.columns)
    assert int(out["n"].sum()) == 3


def test_summarize_by_exit_geometry_returns_empty_when_columns_missing():
    df = pd.DataFrame(
        [{"symbol": "AAA", "would_enter": True, "pnl_pct": 0.1, "entry_rule": "x"}]
    )
    out = summarize_by_exit_geometry(df)
    assert out.empty


def test_summarize_by_signal_fade_threshold_json_string_variants():
    rows = _rows_json_string_variants()
    # add a signal_fade_threshold field
    rows = [
        {**r, "variant": json.dumps({**json.loads(r["variant"]), "signal_fade_threshold": 7})}
        for r in rows
    ]
    out = summarize_by_signal_fade_threshold(pd.DataFrame(rows))
    assert not out.empty
    assert "signal_fade_threshold" in out.columns
    assert int(out["n"].sum()) == 3
