#!/usr/bin/env python3
"""
sample_mongo_candles.py — Pull and display sample candle data from MongoDB.

Run from your Trading Pod environment (where pymongo is installed):
    python sample_mongo_candles.py

Edit the CONFIG section below, or set environment variables:
    MONGO_URI, MONGO_DATABASE, TRUENAS_LAN_IP, MONGO_ROOT_PASSWORD
"""

import os
import sys
import json
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG — edit these or rely on environment variables
# ─────────────────────────────────────────────────────────────────────────────
TRUENAS_IP = os.environ.get("TRUENAS_LAN_IP", "192.168.1.54")
TRUENAS_DB_PASS = os.environ.get("MONGO_ROOT_PASSWORD", "mypass")
MONGO_URI = os.environ.get(
    "MONGO_URI",
    f"mongodb://admin:{TRUENAS_DB_PASS}@{TRUENAS_IP}:27017/quants_lab?authSource=admin",
)
MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "quants_lab")

# Which pair to sample (set to None to auto-discover)
CONNECTOR = "nonkyc"
TRADING_PAIR = "BTC-USDT"   # MongoDB format (hyphen)
INTERVAL = "5m"

# How many sample rows to pull
N_SAMPLES = 10
# ─────────────────────────────────────────────────────────────────────────────


def main():
    try:
        from pymongo import MongoClient
    except ImportError:
        print("ERROR: pymongo not installed. Run: pip install pymongo")
        sys.exit(1)

    try:
        import pandas as pd
    except ImportError:
        pd = None

    # ── Connect ──
    print("=" * 70)
    print("MongoDB Candle Data Sampler")
    print("=" * 70)
    safe_uri = MONGO_URI.split("@")[-1] if "@" in MONGO_URI else MONGO_URI
    print(f"  URI:      ...@{safe_uri}")
    print(f"  Database: {MONGO_DATABASE}")
    print()

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("  ✓ Connected successfully\n")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        sys.exit(1)

    db = client[MONGO_DATABASE]

    # ── 1. List collections ──
    print("─" * 70)
    print("COLLECTIONS IN DATABASE")
    print("─" * 70)
    for coll_name in sorted(db.list_collection_names()):
        count = db[coll_name].estimated_document_count()
        print(f"  {coll_name:30s}  ~{count:,} docs")
    print()

    # ── 2. Discover available connectors / pairs / intervals ──
    print("─" * 70)
    print("AVAILABLE CONNECTOR / PAIR / INTERVAL COMBOS (candles collection)")
    print("─" * 70)
    if "candles" not in db.list_collection_names():
        print("  No 'candles' collection found!")
        client.close()
        return

    pipeline = [
        {"$group": {
            "_id": {
                "connector": "$connector",
                "trading_pair": "$trading_pair",
                "interval": "$interval",
            },
            "count": {"$sum": 1},
            "min_ts": {"$min": "$timestamp"},
            "max_ts": {"$max": "$timestamp"},
        }},
        {"$sort": {"_id.connector": 1, "_id.trading_pair": 1, "_id.interval": 1}},
    ]
    combos = list(db.candles.aggregate(pipeline))
    for c in combos:
        cid = c["_id"]
        min_dt = _ts_to_str(c["min_ts"])
        max_dt = _ts_to_str(c["max_ts"])
        print(f"  {cid['connector']:12s} {cid['trading_pair']:15s} {cid['interval']:5s} "
              f" {c['count']:>8,} candles   {min_dt} → {max_dt}")
    print()

    # ── 3. Raw document samples ──
    print("─" * 70)
    print(f"RAW MONGODB DOCUMENTS (first {N_SAMPLES} for {CONNECTOR} {TRADING_PAIR} {INTERVAL})")
    print("─" * 70)
    query = {
        "connector": CONNECTOR,
        "trading_pair": TRADING_PAIR,
        "interval": INTERVAL,
    }
    # First N (by timestamp ascending)
    first_docs = list(db.candles.find(query, {"_id": 0}).sort("timestamp", 1).limit(N_SAMPLES))
    if not first_docs:
        print(f"  No documents found for {CONNECTOR} {TRADING_PAIR} {INTERVAL}")
        print("  Check the combos listed above and update CONFIG.")
        client.close()
        return

    print(f"\n  FIRST {len(first_docs)} documents (ascending timestamp):\n")
    for i, doc in enumerate(first_docs):
        print(f"  [{i}] {json.dumps(_serialize(doc), indent=6, default=str)}")

    # Last N
    last_docs = list(db.candles.find(query, {"_id": 0}).sort("timestamp", -1).limit(N_SAMPLES))
    last_docs.reverse()
    print(f"\n  LAST {len(last_docs)} documents (most recent):\n")
    for i, doc in enumerate(last_docs):
        print(f"  [{i}] {json.dumps(_serialize(doc), indent=6, default=str)}")

    # ── 4. Schema analysis ──
    print("\n" + "─" * 70)
    print("SCHEMA ANALYSIS")
    print("─" * 70)
    sample_doc = first_docs[0]
    print("  Fields and types in first document:")
    for key, val in sample_doc.items():
        print(f"    {key:20s}  type={type(val).__name__:10s}  value={val!r}")

    # Check timestamp format
    ts_val = sample_doc.get("timestamp")
    print(f"\n  Timestamp field value: {ts_val!r}")
    if isinstance(ts_val, (int, float)):
        if ts_val > 1e12:
            print(f"    → Looks like MILLISECONDS (÷1000 → {datetime.fromtimestamp(ts_val/1000, tz=timezone.utc)})")
        elif ts_val > 1e9:
            print(f"    → Looks like SECONDS (→ {datetime.fromtimestamp(ts_val, tz=timezone.utc)})")
        else:
            print(f"    → Unexpected magnitude: {ts_val}")
    elif isinstance(ts_val, datetime):
        print(f"    → Native datetime object: {ts_val}")
    else:
        print(f"    → Unexpected type: {type(ts_val)}")

    # ── 5. Sort order check ──
    print("\n" + "─" * 70)
    print("SORT ORDER CHECK")
    print("─" * 70)
    all_ts = [d["timestamp"] for d in first_docs]
    sorted_asc = all(all_ts[i] <= all_ts[i + 1] for i in range(len(all_ts) - 1))
    print(f"  First {len(all_ts)} timestamps ascending? {sorted_asc}")
    if len(all_ts) >= 2:
        gaps = [all_ts[i + 1] - all_ts[i] for i in range(len(all_ts) - 1)]
        print(f"  Gaps between consecutive timestamps: {gaps}")
        if all(isinstance(g, (int, float)) for g in gaps):
            print(f"  Min gap: {min(gaps)}, Max gap: {max(gaps)}, Median: {sorted(gaps)[len(gaps)//2]}")

    # ── 6. Aggregate stats ──
    total_count = db.candles.count_documents(query)
    print(f"\n  Total documents matching query: {total_count:,}")

    # Check for duplicates
    dup_pipeline = [
        {"$match": query},
        {"$group": {"_id": "$timestamp", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$count": "n_duplicates"},
    ]
    dup_result = list(db.candles.aggregate(dup_pipeline))
    n_dups = dup_result[0]["n_duplicates"] if dup_result else 0
    print(f"  Duplicate timestamps: {n_dups}")

    # Check for any null/missing OHLCV
    for col in ["open", "high", "low", "close", "volume"]:
        null_q = {**query, col: {"$in": [None, float("nan")]}}
        n_null = db.candles.count_documents(null_q)
        missing_q = {**query, col: {"$exists": False}}
        n_missing = db.candles.count_documents(missing_q)
        if n_null > 0 or n_missing > 0:
            print(f"  ⚠ {col}: {n_null} null + {n_missing} missing")

    # ── 7. Pandas DataFrame preview (if available) ──
    if pd is not None:
        print("\n" + "─" * 70)
        print("PANDAS DATAFRAME PREVIEW (first 20 rows after load_candles-style processing)")
        print("─" * 70)
        cursor = db.candles.find(query, {"_id": 0}).sort("timestamp", 1).limit(20)
        rows = list(cursor)
        df = pd.DataFrame(rows)
        if "timestamp" in df.columns:
            ts_col = df["timestamp"]
            if ts_col.dtype in ("int64", "float64") and ts_col.iloc[0] > 1e9:
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
        for col in ("open", "high", "low", "close", "volume"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        # Drop metadata columns for display
        drop_cols = [c for c in ("connector", "trading_pair", "interval") if c in df.columns]
        df_display = df.drop(columns=drop_cols)
        print(f"\n  Shape: {df_display.shape}")
        print(f"  Dtypes:\n{df_display.dtypes.to_string()}\n")
        print(df_display.to_string(index=True))
        print(f"\n  Describe:\n{df_display.describe().to_string()}")

    # ── 8. Random mid-section sample ──
    print("\n" + "─" * 70)
    print(f"RANDOM MID-SECTION SAMPLE ({N_SAMPLES} docs from ~middle of dataset)")
    print("─" * 70)
    skip_count = max(0, total_count // 2 - N_SAMPLES // 2)
    mid_docs = list(
        db.candles.find(query, {"_id": 0})
        .sort("timestamp", 1)
        .skip(skip_count)
        .limit(N_SAMPLES)
    )
    for i, doc in enumerate(mid_docs):
        print(f"  [{i}] {json.dumps(_serialize(doc), indent=6, default=str)}")

    client.close()
    print("\n" + "=" * 70)
    print("Done. Copy/paste this output to share with Claude for analysis.")
    print("=" * 70)


def _ts_to_str(ts_val):
    """Convert a timestamp value to human-readable string."""
    try:
        if isinstance(ts_val, (int, float)):
            if ts_val > 1e12:
                return datetime.fromtimestamp(ts_val / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            return datetime.fromtimestamp(ts_val, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        return str(ts_val)
    except Exception:
        return str(ts_val)


def _serialize(doc):
    """Make a Mongo document JSON-serializable."""
    out = {}
    for k, v in doc.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, bytes):
            out[k] = v.hex()
        else:
            out[k] = v
    return out


if __name__ == "__main__":
    main()
