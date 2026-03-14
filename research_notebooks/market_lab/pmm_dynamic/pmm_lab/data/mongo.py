"""MongoDB candle data loader."""

import logging
import os
from typing import Optional

import numpy as np

from pmm_lab.config.defaults import INTERVAL_SECONDS
from pmm_lab.config.params import DataQuery

logger = logging.getLogger(__name__)

CANDLE_DTYPE = np.dtype([
    ("timestamp", "int64"),
    ("open", "float64"),
    ("high", "float64"),
    ("low", "float64"),
    ("close", "float64"),
    ("volume", "float64"),
    ("is_forward_fill", "bool"),
])


class MongoCandleLoader:
    """Loads candle data from MongoDB candles collection."""

    def __init__(self, client=None, db_name: Optional[str] = None):
        """Initialize the loader.

        If client is None, creates a MongoClient from MONGO_URI env var.
        If db_name is None, reads MONGO_DATABASE env var (default: "quants_lab").

        Parameters
        ----------
        client : pymongo.MongoClient or mongomock.MongoClient, optional
            MongoDB client instance. If None, creates one from env.
        db_name : str, optional
            Database name. Defaults to MONGO_DATABASE env var or "quants_lab".
        """
        if client is None:
            from pymongo import MongoClient
            uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
            client = MongoClient(uri)

        self._client = client
        self._db_name = db_name or os.environ.get("MONGO_DATABASE", "quants_lab")
        self._db = client[self._db_name]
        self._collection = self._db["candles"]

    def ensure_indexes(self) -> None:
        """Create compound index on (connector, trading_pair, interval, timestamp).

        Idempotent — safe to call multiple times.
        """
        self._collection.create_index(
            [
                ("connector", 1),
                ("trading_pair", 1),
                ("interval", 1),
                ("timestamp", 1),
            ],
            name="connector_pair_interval_ts",
        )

    def list_combos(
        self,
        connector: Optional[str] = None,
        quote_asset: Optional[str] = "USDT",
    ) -> list[dict]:
        """Return distinct (connector, trading_pair, interval) combinations with stats.

        Parameters
        ----------
        connector : str, optional
            Filter to a specific connector.
        quote_asset : str, optional
            Filter to pairs ending with f"-{quote_asset}". Default "USDT".

        Returns
        -------
        list[dict]
            Each dict has: connector, trading_pair, interval, count, first_ts, last_ts.
        """
        match_stage: dict = {}
        if connector:
            match_stage["connector"] = connector
        if quote_asset:
            match_stage["trading_pair"] = {"$regex": f"-{quote_asset}$"}

        pipeline = []
        if match_stage:
            pipeline.append({"$match": match_stage})

        pipeline.extend([
            {
                "$group": {
                    "_id": {
                        "connector": "$connector",
                        "trading_pair": "$trading_pair",
                        "interval": "$interval",
                    },
                    "count": {"$sum": 1},
                    "first_ts": {"$min": "$timestamp"},
                    "last_ts": {"$max": "$timestamp"},
                }
            },
            {
                "$sort": {
                    "_id.connector": 1,
                    "_id.trading_pair": 1,
                    "_id.interval": 1,
                }
            },
        ])

        results = []
        for doc in self._collection.aggregate(pipeline):
            results.append({
                "connector": doc["_id"]["connector"],
                "trading_pair": doc["_id"]["trading_pair"],
                "interval": doc["_id"]["interval"],
                "count": doc["count"],
                "first_ts": doc["first_ts"],
                "last_ts": doc["last_ts"],
            })
        return results

    def load_range(self, query: DataQuery) -> np.ndarray:
        """Load candles matching query, return as canonical structured NumPy array.

        Parameters
        ----------
        query : DataQuery
            Query parameters.

        Returns
        -------
        np.ndarray
            Structured array with canonical CANDLE_DTYPE.

        Raises
        ------
        ValueError
            If query.interval is not valid or no documents match.
        """
        if query.interval not in INTERVAL_SECONDS:
            raise ValueError(
                f"Invalid interval '{query.interval}'. "
                f"Valid intervals: {list(INTERVAL_SECONDS.keys())}"
            )

        mongo_filter: dict = {
            "connector": query.connector,
            "trading_pair": query.trading_pair,
            "interval": query.interval,
        }

        if query.start_ts is not None or query.end_ts is not None:
            ts_filter: dict = {}
            if query.start_ts is not None:
                ts_filter["$gte"] = query.start_ts
            if query.end_ts is not None:
                ts_filter["$lte"] = query.end_ts
            mongo_filter["timestamp"] = ts_filter

        cursor = self._collection.find(mongo_filter).sort("timestamp", 1)
        docs = list(cursor)

        if not docs:
            raise ValueError(
                f"No candles found for {query.connector} {query.trading_pair} "
                f"{query.interval}"
            )

        # Build array
        rows = []
        for doc in docs:
            rows.append((
                int(doc["timestamp"]),
                float(doc["open"]),
                float(doc["high"]),
                float(doc["low"]),
                float(doc["close"]),
                float(doc["volume"]),
                False,  # is_forward_fill always False in v1
            ))

        arr = np.array(rows, dtype=CANDLE_DTYPE)

        # Deduplicate by timestamp deterministically.
        # When duplicates exist, keep the row with the highest volume
        # (most likely the "real" candle vs a placeholder/forward-fill).
        # Ties broken by keeping the first occurrence in sort order.
        _, unique_indices = np.unique(arr["timestamp"], return_index=True)
        if len(unique_indices) < len(arr):
            dup_count = len(arr) - len(unique_indices)
            logger.warning(
                "Removed %d duplicate timestamps from %s %s %s",
                dup_count, query.connector, query.trading_pair, query.interval,
            )

            # For each unique timestamp, pick the row with max volume
            ts_vals = arr["timestamp"]
            vol_vals = arr["volume"]
            keep_indices = []
            seen_ts = set()
            # Sort by (timestamp ASC, volume DESC) for deterministic pick
            sort_order = np.lexsort((-vol_vals, ts_vals))
            for idx in sort_order:
                t = ts_vals[idx]
                if t not in seen_ts:
                    seen_ts.add(t)
                    keep_indices.append(idx)

            keep_indices.sort()  # restore chronological order
            arr = arr[np.array(keep_indices)]
        else:
            # No duplicates — just ensure sorted
            unique_indices.sort()
            arr = arr[unique_indices]

        return arr

    def ping(self) -> bool:
        """Return True if MongoDB is reachable.

        Returns
        -------
        bool
        """
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False
