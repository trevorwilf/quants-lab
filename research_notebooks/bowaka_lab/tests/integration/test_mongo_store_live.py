"""Phase 1: live Mongo connectivity + index application.

This test runs only when `MONGO_URI` is set in the environment (per the
implementation prompt: "live_mongo runs (Mongo reachable via MONGO_URI)").
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

from bowaka_lab.data.mongo_store import MongoStore


pytestmark = pytest.mark.live_mongo


@pytest.fixture(scope="module")
def live_mongo_store():
    uri = os.environ.get("MONGO_URI")
    if not uri:
        pytest.skip("MONGO_URI not set")
    db_name = f"bowaka_lab_test_{uuid.uuid4().hex[:8]}"
    store = MongoStore(uri=uri, database=db_name)
    if not store.ping():
        pytest.skip("Mongo not reachable")
    yield store
    store.database().client.drop_database(db_name)
    store.close()


def test_live_mongo_ping(live_mongo_store):
    assert live_mongo_store.ping()


def test_live_mongo_index_apply(live_mongo_store, bowaka_root):
    spec_path: Path = bowaka_root / "configs" / "mongo_indexes.yml"
    created = live_mongo_store.apply_indexes(spec_path)
    assert "bowaka_assets" in created
    assert "bowaka_prefilter_runs" in created
    assert "bowaka_candidates" in created
    assert "bowaka_backtest_runs" in created
    assert "bowaka_backtest_trades" in created
    assert "bowaka_counterfactuals" in created
    assert "bowaka_paper_reconciliation" in created

    asset_indexes = live_mongo_store.collection("bowaka_assets").index_information()
    unique_indexes = [name for name, info in asset_indexes.items() if info.get("unique")]
    assert len(unique_indexes) >= 1
