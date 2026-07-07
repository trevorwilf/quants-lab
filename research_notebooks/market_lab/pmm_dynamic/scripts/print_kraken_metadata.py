"""Print exchange metadata from quants_lab.symbol_metadata for the ladder pairs.

The candle ingester stores Kraken AssetPairs metadata (tick_size,
quantity_step, ordermin, costmin, maker/taker fees) in the
`quants_lab.symbol_metadata` MongoDB collection. This helper prints the
values used to populate `configs/exchange_rules.yaml` so they can be
re-verified after any ingester refresh.

Usage (from the pmm_dynamic subproject root, .env discovered upward):
    python scripts/print_kraken_metadata.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

KRAKEN_PAIRS = ["XMR-USDT", "XMR-USD"]
NONKYC_LADDER_PAIRS = ["XMR-USDT", "DASH-USDT", "SUN-USDT", "ZANO-USDT"]

FIELDS = [
    "tick_size", "price_decimals", "quantity_step", "quantity_decimals",
    "min_order_qty", "min_notional", "maker_fee", "taker_fee",
    "status", "source", "updated_at",
]


def _load_env() -> None:
    """Walk upward from this file looking for a .env with MONGO_URI."""
    if os.environ.get("MONGO_URI"):
        return
    d = Path(__file__).resolve().parent
    for _ in range(10):
        env = d / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
            return
        d = d.parent


def main() -> int:
    _load_env()
    if not os.environ.get("MONGO_URI"):
        print("MONGO_URI not set and no .env found — cannot reach the lake.")
        return 1

    from pymongo import MongoClient

    client = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=8000)
    coll = client[os.environ.get("MONGO_DATABASE", "quants_lab")]["symbol_metadata"]

    for connector, pairs in (("kraken", KRAKEN_PAIRS), ("nonkyc", NONKYC_LADDER_PAIRS)):
        print(f"\n=== {connector} ===")
        for pair in pairs:
            doc = coll.find_one({"connector": connector, "trading_pair": pair})
            if doc is None:
                print(f"{pair:12s}  <NOT IN symbol_metadata — use REST or placeholder>")
                continue
            vals = ", ".join(f"{f}={doc.get(f)}" for f in FIELDS if f in doc)
            print(f"{pair:12s}  {vals}")

    print(
        "\nNote: nonkyc docs carry priceDecimals-derived tick_size (1e-8) and "
        "null fees — the curated values in configs/exchange_rules.yaml come "
        "from live prices / account trades instead."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
