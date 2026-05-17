"""Phase 1: MongoStore tests using mongomock (no live Mongo needed)."""

from __future__ import annotations

import pytest
from mongomock import MongoClient as MockClient

from bowaka_lab.data.mongo_store import MongoStore


@pytest.fixture
def mongo_store():
    client = MockClient()
    return MongoStore(database="bowaka_lab_test", client=client)


def test_mongo_store_is_available_with_injected_client(mongo_store):
    assert mongo_store.is_available


def test_mongo_store_upsert_inserts_new(mongo_store):
    mongo_store.upsert("bowaka_assets", {"snapshot_id": "x", "symbol": "RILY"}, {"name": "B. Riley"})
    doc = mongo_store.collection("bowaka_assets").find_one({"symbol": "RILY"})
    assert doc["name"] == "B. Riley"


def test_mongo_store_upsert_updates_existing(mongo_store):
    mongo_store.upsert("bowaka_assets", {"snapshot_id": "x", "symbol": "RILY"}, {"name": "old"})
    mongo_store.upsert("bowaka_assets", {"snapshot_id": "x", "symbol": "RILY"}, {"name": "new"})
    docs = list(mongo_store.collection("bowaka_assets").find({"symbol": "RILY"}))
    assert len(docs) == 1
    assert docs[0]["name"] == "new"


def test_mongo_store_insert_many(mongo_store):
    docs = [{"k": i} for i in range(5)]
    n = mongo_store.insert_many("test", docs)
    assert n == 5
    assert mongo_store.collection("test").count_documents({}) == 5


def test_mongo_store_insert_many_empty_returns_zero(mongo_store):
    assert mongo_store.insert_many("test", []) == 0


def test_mongo_store_unavailable_without_uri(monkeypatch):
    monkeypatch.delenv("MONGO_URI", raising=False)
    store = MongoStore(uri=None)
    assert store.is_available is False
