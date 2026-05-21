"""The migrated backfill is Parquet-only — no Mongo client, no Mongo config."""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from bowaka_common.marketdata import backfill


def test_backfill_config_has_no_mongo_fields():
    names = {f.name for f in fields(backfill.BackfillConfig)}
    mongo_fields = [n for n in names if "mongo" in n.lower()]
    assert not mongo_fields, f"BackfillConfig still carries Mongo fields: {mongo_fields}"


def test_backfill_source_constructs_no_mongo_client():
    src = Path(backfill.__file__).read_text(encoding="utf-8")
    assert "pymongo" not in src
    assert "MongoClient" not in src
    assert "import mongo" not in src.lower()


def test_no_mongo_callables_remain():
    for name in (
        "get_mongo_client",
        "apply_indexes",
        "write_asset_snapshot_to_mongo",
        "write_ingestion_run_to_mongo",
        "write_daily_audits_to_mongo",
    ):
        assert not hasattr(backfill, name), f"stale Mongo callable: {name}"


def test_scope3_stage_removed():
    # Scope-3 / ADV universe is strategy-specific — it lives in bowaka_lab now.
    assert not hasattr(backfill, "compute_scope_3")
