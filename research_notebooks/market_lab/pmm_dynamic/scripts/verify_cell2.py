"""Verify Cell 2 of candle_backfill_v3.ipynb defines the expected symbols.

Executes ONLY the replacement-block portion of Cell 2 (the part containing
`_TokenBucket`) in a minimal namespace, to confirm parseability and correct
initialization of per-exchange bucket tuning. Does NOT hit the network.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

NB_PATH = (
    Path(__file__).resolve().parent.parent
    / "notebooks" / "mongo_tools" / "candle_backfill_v3.ipynb"
)


def _cell_source(cell):
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else (s or "")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    nb = json.load(open(NB_PATH, encoding="utf-8"))
    cell2 = None
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = _cell_source(cell)
        if "_TokenBucket" in src:
            cell2 = cell
            break
    if cell2 is None:
        print("FAIL: Cell 2 (containing _TokenBucket) not found")
        sys.exit(1)

    cell2_src = _cell_source(cell2)

    # Minimal execution environment — just what the replacement block needs.
    # The cell imports these at the top of its source, so we pre-provide them
    # in ns so exec() doesn't need to resolve module-level imports.
    import threading, time, requests
    from typing import Any, Optional
    ns = {
        "HTTP_MAX_RETRIES": 3,
        "HTTP_TIMEOUT": 30,
        "HTTP_RETRY_BACKOFF": 1.8,
        "threading": threading,
        "time": time,
        "requests": requests,
        "Optional": Optional,
        "Any": Any,
        "__builtins__": __builtins__,
    }

    exec(cell2_src, ns)

    for name in ("_TokenBucket", "http_get_json", "_get_exchange_bucket",
                 "get_exchange_parallel_workers", "_EXCHANGE_TUNING",
                 "session", "normalize_candle_doc", "upsert_candles"):
        assert name in ns, f"expected symbol {name!r} missing after exec"

    b = ns["_get_exchange_bucket"]("nonkyc")
    s = b.stats()
    assert s["rate_per_sec"] == 12.0, f"nonkyc rate: expected 12.0, got {s['rate_per_sec']}"
    assert s["capacity"] == 24.0, f"nonkyc capacity: expected 24.0, got {s['capacity']}"

    # Confirm parallelism helper returns expected value for nonkyc
    parallel = ns["get_exchange_parallel_workers"]("nonkyc")
    assert parallel == 4, f"nonkyc parallel workers: expected 4, got {parallel}"

    # Confirm old symbols are GONE
    assert "_exchange_locks" not in ns, "old _exchange_locks should be removed"
    assert "_get_exchange_lock" not in ns, "old _get_exchange_lock should be removed"

    print("OK: Cell 2 replacement parses and defines the expected symbols.")
    print(f"    nonkyc bucket: rate={s['rate_per_sec']} req/s, capacity={s['capacity']} tokens")
    print(f"    nonkyc parallel pair-workers: {parallel}")


if __name__ == "__main__":
    main()
