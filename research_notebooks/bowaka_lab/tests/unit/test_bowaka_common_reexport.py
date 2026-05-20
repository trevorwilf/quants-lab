"""Assert v1 shims re-export the *same* objects as bowaka_common (id() identity).

After Phase 2, many v1 modules became thin re-export shims pointing at
``bowaka_common.<new_path>``. v1 imports must continue to resolve and the
imported objects must be byte-identical (``id()`` match) to the canonical
``bowaka_common`` versions — otherwise downstream subclass / isinstance / patching
behavior would silently diverge between v1 and v2 callers.
"""
from __future__ import annotations

import pytest


_SHIMS_TO_CHECK = [
    # (v1_module, v1_attr, common_module, common_attr)
    ("bowaka_lab.data.calendar", "USEquityCalendar", "bowaka_common.calendar.exchange", "USEquityCalendar"),
    ("bowaka_lab.data.calendar", "SessionTimes", "bowaka_common.calendar.exchange", "SessionTimes"),
    ("bowaka_lab.data.alpaca_client", "AlpacaClient", "bowaka_common.data.alpaca_client", "AlpacaClient"),
    ("bowaka_lab.data.rate_limit", "TokenBucket", "bowaka_common.data.rate_limit", "TokenBucket"),
    ("bowaka_lab.data.assets", "classify_instrument", "bowaka_common.data.assets", "classify_instrument"),
    ("bowaka_lab.data.assets", "build_asset_snapshot", "bowaka_common.data.assets", "build_asset_snapshot"),
    ("bowaka_lab.data.bars", "fetch_daily_bars", "bowaka_common.data.bars", "fetch_daily_bars"),
    ("bowaka_lab.data.bars", "fetch_minute_bars", "bowaka_common.data.bars", "fetch_minute_bars"),
    ("bowaka_lab.data.corporate_actions", "detect_split_anomalies", "bowaka_common.data.corporate_actions", "detect_split_anomalies"),
    ("bowaka_lab.data.quote_loader", "QuoteLoader", "bowaka_common.data.quote_loader", "QuoteLoader"),
    ("bowaka_lab.data.quotes", "fetch_quotes", "bowaka_common.data.quotes", "fetch_quotes"),
    ("bowaka_lab.data.schemas", "build_candidate_v3", "bowaka_common.data.schemas", "build_candidate_v3"),
    ("bowaka_lab.data.mongo_store", "MongoStore", "bowaka_common.storage.mongo_store", "MongoStore"),
    ("bowaka_lab.data.parquet_io", "MinuteBarLoader", "bowaka_common.storage.parquet_io", "MinuteBarLoader"),
    ("bowaka_lab.data.parquet_store", "ParquetStore", "bowaka_common.storage.parquet_store", "ParquetStore"),
    ("bowaka_lab.data.dataset_hash", "hash_dataframe", "bowaka_common.storage.dataset_hash", "hash_dataframe"),
    ("bowaka_lab.data.quality", "audit_daily_bars", "bowaka_common.quality.reports", "audit_daily_bars"),
    ("bowaka_lab.research.splits", "WalkForwardPlan", "bowaka_common.research.splits", "WalkForwardPlan"),
    ("bowaka_lab.research.walkforward", "run_walkforward", "bowaka_common.research.walkforward", "run_walkforward"),
    ("bowaka_lab.research.robustness", "topk_convergence", "bowaka_common.research.robustness", "topk_convergence"),
    ("bowaka_lab.research.sensitivity", "one_at_a_time", "bowaka_common.research.sensitivity", "one_at_a_time"),
    ("bowaka_lab.research.stress", "high_vol_sessions", "bowaka_common.research.stress", "high_vol_sessions"),
    ("bowaka_lab.sim.ambiguity", "resolve", "bowaka_common.sim.ambiguity", "resolve"),
    ("bowaka_lab.utils.ids", "run_id", "bowaka_common.utils.ids", "run_id"),
    ("bowaka_lab.utils.ids", "trade_id", "bowaka_common.utils.ids", "trade_id"),
    ("bowaka_lab.config.hashing", "stable_hash", "bowaka_common.utils.hashing", "stable_hash"),
    ("bowaka_lab.config.hashing", "short", "bowaka_common.utils.hashing", "short"),
]


@pytest.mark.parametrize("v1_mod,v1_attr,common_mod,common_attr", _SHIMS_TO_CHECK)
def test_shim_reexports_identical_object(
    v1_mod: str, v1_attr: str, common_mod: str, common_attr: str
) -> None:
    import importlib

    v1 = importlib.import_module(v1_mod)
    common = importlib.import_module(common_mod)
    v1_obj = getattr(v1, v1_attr, None)
    common_obj = getattr(common, common_attr, None)
    assert v1_obj is not None, f"{v1_mod}.{v1_attr} missing after shim"
    assert common_obj is not None, f"{common_mod}.{common_attr} missing"
    assert v1_obj is common_obj, (
        f"{v1_mod}.{v1_attr} is not the same object as {common_mod}.{common_attr} "
        f"(ids {id(v1_obj)} vs {id(common_obj)})"
    )
