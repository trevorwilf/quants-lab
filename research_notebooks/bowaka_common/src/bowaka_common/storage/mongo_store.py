"""Lazy pymongo wrapper with index application from a YAML spec."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database


class MongoStore:
    """Thin wrapper around pymongo with lazy connection."""

    def __init__(
        self,
        uri: str | None = None,
        database: str = "quants_lab",
        *,
        server_selection_timeout_ms: int = 5_000,
        client: MongoClient | None = None,
    ):
        self._uri = uri or os.environ.get("MONGO_URI")
        self._database_name = database
        self._timeout = server_selection_timeout_ms
        self._client: MongoClient | None = client
        self._db: Database | None = None

    @property
    def is_available(self) -> bool:
        if self._client is not None:
            return True
        return bool(self._uri)

    def _connect(self) -> MongoClient:
        if self._client is not None:
            return self._client
        if not self._uri:
            raise RuntimeError("MongoStore: no MONGO_URI provided")
        self._client = MongoClient(self._uri, serverSelectionTimeoutMS=self._timeout)
        return self._client

    def database(self) -> Database:
        if self._db is None:
            self._db = self._connect()[self._database_name]
        return self._db

    def collection(self, name: str) -> Collection:
        return self.database()[name]

    def ping(self) -> bool:
        try:
            self._connect().admin.command("ping")
            return True
        except Exception:
            return False

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None

    def upsert(self, collection: str, key: dict[str, Any], doc: dict[str, Any]) -> None:
        self.collection(collection).update_one(key, {"$set": doc}, upsert=True)

    def insert_many(self, collection: str, docs: list[dict[str, Any]]) -> int:
        if not docs:
            return 0
        res = self.collection(collection).insert_many(docs, ordered=False)
        return len(res.inserted_ids)

    def apply_indexes(self, spec_path: Path | str) -> dict[str, list[str]]:
        """Apply index definitions from a YAML spec.

        The YAML format mirrors ``[Report §8.6]``:

          ``collection_name``:
            - keys: [["field", 1], ["other", -1]]
              unique: true

        Returns a mapping ``collection -> list of created index names``.
        """
        spec = yaml.safe_load(Path(spec_path).read_text(encoding="utf-8")) or {}
        created: dict[str, list[str]] = {}

        for coll_name, idx_specs in spec.items():
            coll = self.collection(coll_name)
            names: list[str] = []
            for idx in idx_specs:
                raw_keys = idx["keys"]
                pymongo_keys = [(k[0], ASCENDING if int(k[1]) >= 1 else DESCENDING) for k in raw_keys]
                name = coll.create_index(pymongo_keys, unique=idx.get("unique", False))
                names.append(name)
            created[coll_name] = names
        return created
