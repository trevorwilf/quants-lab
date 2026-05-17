"""Phase backfill-notebook: live-mongo integration tests for the helper lib."""

from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timezone

import pandas as pd
import pytest

from db_tools import _backfill_lib as lib


pytestmark = pytest.mark.live_mongo


@pytest.fixture
def live_db():
    uri = os.environ.get("MONGO_URI")
    if not uri:
        pytest.skip("MONGO_URI not set")
    client = lib.get_mongo_client(uri)
    try:
        client.admin.command("ping")
    except Exception:
        pytest.skip("Mongo not reachable")
    db_name = f"bowaka_lab_test_{uuid.uuid4().hex[:8]}"
    db = client[db_name]
    try:
        yield db
    finally:
        client.drop_database(db_name)
        client.close()


def _cfg(tmp_path) -> lib.BackfillConfig:
    return lib.BackfillConfig(
        api_key="k",
        api_secret="s",
        paper=True,
        feed="iex",
        start_date=date(2025, 1, 2),
        end_date=date(2026, 5, 15),
        out_dir=tmp_path,
        mongo_uri=None,
        write_to_mongo=False,
    )


def test_apply_indexes_creates_section_8_6_indexes(live_db):
    lib.apply_indexes(live_db)
    for coll_name, spec_entries in lib.SECTION_8_6_INDEXES.items():
        info = live_db[coll_name].index_information()
        # At least one unique index should exist per collection.
        unique_indexes = [n for n, meta in info.items() if meta.get("unique")]
        assert unique_indexes, f"{coll_name} has no unique index"


def test_apply_indexes_is_idempotent(live_db):
    lib.apply_indexes(live_db)
    lib.apply_indexes(live_db)  # must not raise
    info = live_db["bowaka_assets"].index_information()
    unique_indexes = [n for n, meta in info.items() if meta.get("unique")]
    assert unique_indexes


def test_write_asset_snapshot_inserts_snapshot_and_assets(live_db, tmp_path):
    cfg = _cfg(tmp_path)
    lib.apply_indexes(live_db)
    df = pd.DataFrame(
        [
            {"symbol": "AAA", "name": "Alpha", "exchange": "NASDAQ"},
            {"symbol": "BBB", "name": "Beta", "exchange": "NYSE"},
        ]
    )
    snapshot_id = "snap-test-1"
    lib.write_asset_snapshot_to_mongo(live_db, snapshot_id, df, cfg)
    snap_count = live_db["bowaka_asset_snapshots"].count_documents({"snapshot_id": snapshot_id})
    asset_count = live_db["bowaka_assets"].count_documents({"snapshot_id": snapshot_id})
    assert snap_count == 1
    assert asset_count == 2


def test_write_asset_snapshot_upsert_semantics(live_db, tmp_path):
    cfg = _cfg(tmp_path)
    lib.apply_indexes(live_db)
    df = pd.DataFrame([{"symbol": "AAA", "name": "Alpha", "exchange": "NASDAQ"}])
    snapshot_id = "snap-test-upsert"
    lib.write_asset_snapshot_to_mongo(live_db, snapshot_id, df, cfg)
    lib.write_asset_snapshot_to_mongo(live_db, snapshot_id, df, cfg)
    asset_count = live_db["bowaka_assets"].count_documents({"snapshot_id": snapshot_id})
    assert asset_count == 1


def test_write_ingestion_run_inserts(live_db):
    lib.apply_indexes(live_db)
    record = {
        "ingestion_run_id": "ingest-1",
        "vendor": "alpaca",
        "feed": "iex",
        "timeframe": "1d",
        "adjustment": "raw",
        "start": "2025-01-01",
        "end": "2026-05-15",
        "symbol_count_requested": 100,
        "symbol_count_success": 95,
        "symbol_count_failed": 5,
        "api_call_count": 1,
        "rate_limit_policy": "180_rpm",
        "dataset_hash": "sha256:abc",
        "parquet_root": "/tmp/bowaka",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    lib.write_ingestion_run_to_mongo(live_db, record)
    assert live_db["bowaka_data_ingestion_runs"].count_documents({"ingestion_run_id": "ingest-1"}) == 1


def test_write_daily_audits_upserts_by_symbol_and_feed(live_db, tmp_path):
    cfg = _cfg(tmp_path)
    lib.apply_indexes(live_db)
    df = pd.DataFrame(
        [
            {"symbol": "AAA", "timeframe": "1d", "passed_research_audit": True, "expected_sessions": 100, "observed_sessions": 100},
            {"symbol": "BBB", "timeframe": "1d", "passed_research_audit": False, "expected_sessions": 100, "observed_sessions": 80},
        ]
    )
    lib.write_daily_audits_to_mongo(live_db, df, cfg)
    lib.write_daily_audits_to_mongo(live_db, df, cfg)  # idempotent
    assert live_db["bowaka_daily_bar_audits"].count_documents({"symbol": "AAA"}) == 1
    assert live_db["bowaka_daily_bar_audits"].count_documents({"symbol": "BBB"}) == 1


def _cfg_with_history_mode(tmp_path, mode: str) -> lib.BackfillConfig:
    return lib.BackfillConfig(
        api_key="k",
        api_secret="s",
        paper=True,
        feed="iex",
        start_date=date(2025, 1, 2),
        end_date=date(2026, 5, 15),
        out_dir=tmp_path,
        mongo_uri=None,
        write_to_mongo=False,
        audit_history_mode=mode,
    )


def test_audit_history_mode_latest_upserts_by_symbol(live_db, tmp_path):
    cfg = _cfg_with_history_mode(tmp_path, "latest")
    lib.apply_indexes(live_db)
    df1 = pd.DataFrame(
        [{"symbol": "AAA", "timeframe": "1d", "passed_research_audit": True, "audit_run_id": "audit_run_1"}]
    )
    df2 = pd.DataFrame(
        [{"symbol": "AAA", "timeframe": "1d", "passed_research_audit": False, "audit_run_id": "audit_run_2"}]
    )
    lib.write_daily_audits_to_mongo(live_db, df1, cfg)
    lib.write_daily_audits_to_mongo(live_db, df2, cfg)
    docs = list(live_db["bowaka_daily_bar_audits"].find({"symbol": "AAA"}))
    assert len(docs) == 1
    assert docs[0]["audit_run_id"] == "audit_run_2"
    assert docs[0]["passed_research_audit"] is False


def test_audit_history_mode_append_creates_new_records(live_db, tmp_path):
    cfg = _cfg_with_history_mode(tmp_path, "append")
    lib.apply_indexes(live_db)
    df1 = pd.DataFrame(
        [{"symbol": "AAA", "timeframe": "1d", "passed_research_audit": True, "audit_run_id": "audit_run_1"}]
    )
    df2 = pd.DataFrame(
        [{"symbol": "AAA", "timeframe": "1d", "passed_research_audit": False, "audit_run_id": "audit_run_2"}]
    )
    lib.write_daily_audits_to_mongo(live_db, df1, cfg)
    lib.write_daily_audits_to_mongo(live_db, df2, cfg)
    docs = sorted(live_db["bowaka_daily_bar_audits"].find({"symbol": "AAA"}), key=lambda d: d["audit_run_id"])
    assert len(docs) == 2
    assert {d["audit_run_id"] for d in docs} == {"audit_run_1", "audit_run_2"}


def test_apply_indexes_creates_both_audit_index_variants(live_db):
    lib.apply_indexes(live_db)
    info = live_db["bowaka_daily_bar_audits"].index_information()
    key_sets = {tuple(field for field, _ in meta["key"]) for meta in info.values()}
    # Both index variants must exist so latest-mode and append-mode writers
    # have their lookup keys covered. The latest-mode index is non-unique —
    # uniqueness is enforced by the writer's upsert, not the index, so the
    # append-mode index can layer on top of it.
    assert ("symbol", "feed", "timeframe") in key_sets
    assert ("symbol", "feed", "timeframe", "audit_run_id") in key_sets
    # The append-mode index must be unique so two appends in the same
    # audit_run_id can't duplicate.
    unique_key_sets = {
        tuple(field for field, _ in meta["key"])
        for meta in info.values()
        if meta.get("unique")
    }
    assert ("symbol", "feed", "timeframe", "audit_run_id") in unique_key_sets
    # Idempotency.
    lib.apply_indexes(live_db)
    info2 = live_db["bowaka_daily_bar_audits"].index_information()
    assert set(info.keys()) == set(info2.keys())
