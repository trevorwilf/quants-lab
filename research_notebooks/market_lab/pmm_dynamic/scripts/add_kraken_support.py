"""Add Kraken exchange support (shallow-mode) to candle_backfill_v3.ipynb.

Four edits:
  A) candle_backfill_config.yaml — comment out the active `kraken:` block.
  B) Cell 2 — fix _EXCHANGE_TUNING kraken line spacing, add
     _KRAKEN_BASE_TRANSLATIONS + to_kraken_symbol helpers.
  C) Cell 3 — replace the stub fetch_kraken_candles with a full
     OHLC-endpoint implementation.
  D) Cell 4 — add ingest_kraken_range and register it in INGESTERS.

Kraken is shallow-mode only: most-recent 720 bars per interval via
/0/public/OHLC. Deep-history via Trades aggregation is NOT implemented.

Idempotent: detects already-patched state via marker strings.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB_PATH = ROOT / "notebooks" / "mongo_tools" / "candle_backfill_v3.ipynb"
YAML_PATH = ROOT / "notebooks" / "mongo_tools" / "candle_backfill_config.yaml"


# ── A) YAML ───────────────────────────────────────────────────────────────
_YAML_OLD_BLOCK = """  # Example: uncomment and fill in when you're ready to add Kraken.
  # You'll also need to add fetch_kraken_candles / ingest_kraken_range in
  # the notebook. Kraken OHLC endpoint: /0/public/OHLC?pair=XBTUSD&interval=5
  kraken:
    base_url: "https://api.kraken.com"
    request_delay_seconds: 1.0    # Kraken rate limit is stricter than most
    max_per_request: 720           # Kraken caps at 720 OHLC per request
    interval_map:
      "1m": 1
      "5m": 5
      "15m": 15
      "30m": 30
      "1h": 60
      "4h": 240
      "8h": 480
      "12h": 720
      "1d": 1440
"""

_YAML_NEW_BLOCK = """  # Kraken — uncomment when ready to enable.
  # Constraints: 1 req/s per IP (strict), 720 bars per response cap,
  # cannot page older than ~720 bars of history via OHLC endpoint.
  # For deep history, use Trades-aggregation mode (not yet implemented).
  # kraken:
  #   base_url: "https://api.kraken.com"
  #   request_delay_seconds: 0.0    # ignored — token bucket handles pacing
  #   max_per_request: 720           # Kraken OHLC hard cap
  #   interval_map:
  #     "1m": 1
  #     "5m": 5
  #     "15m": 15
  #     "30m": 30
  #     "1h": 60
  #     "4h": 240
  #     "1d": 1440
  #     # Kraken does not support 3m, 8h, or 12h spot OHLC.
"""


# ── B) Cell 2 ─────────────────────────────────────────────────────────────
# Current line has ONE space before "parallel"; target has TWO.
_C2_TUNING_OLD = '"kraken":   {"rate_per_sec": 1.0, "burst": 2.0, "parallel": 1},'
_C2_TUNING_NEW = '"kraken":   {"rate_per_sec": 1.0, "burst": 2.0,  "parallel": 1},'

_C2_COINBASE_ANCHOR = '''def to_coinbase_product_id(hbot_pair: str) -> str:
    return hbot_pair  # already BASE-QUOTE'''

_C2_KRAKEN_HELPERS = '''def to_coinbase_product_id(hbot_pair: str) -> str:
    return hbot_pair  # already BASE-QUOTE


# Kraken uses "XBT" instead of "BTC", and "XDG" instead of "DOGE", in some
# contexts. This translation is applied to the request symbol; the response
# key returned by Kraken is NOT guaranteed to match and must be discovered
# at parse time (see fetch_kraken_candles).
_KRAKEN_BASE_TRANSLATIONS = {
    "BTC": "XBT",
    "DOGE": "XDG",
}


def to_kraken_symbol(hbot_pair: str) -> str:
    base, quote = split_hbot_pair(hbot_pair)
    kb = _KRAKEN_BASE_TRANSLATIONS.get(base, base)
    return f"{kb}{quote}"'''


# ── C) Cell 3: replace stub fetch_kraken_candles ──────────────────────────
_C3_STUB = '''def fetch_kraken_candles(hbot_pair, interval, since_ts, count):
    ex_cfg = EXCHANGES["kraken"]
    api_interval = ex_cfg["interval_map"].get(interval)
    if api_interval is None:
        return []
    url = ex_cfg["base_url"].rstrip("/") + "/0/public/OHLC"
    # Kraken uses "XBT" not "BTC" in some pairs — you may need a pair translation table.
    params = {"pair": hbot_pair.replace("-", ""), "interval": int(api_interval), "since": int(since_ts)}
    data = http_get_json(url, params, prefix="[kraken] ", exchange="kraken")
    # parse data["result"][<pair_key>] into [{timestamp, open, high, low, close, volume}] ...
#     ...'''

_C3_NEW_FETCHER = '''def fetch_kraken_candles(hbot_pair, interval, since_ts=None):
    """Fetch OHLC candles from Kraken's public /0/public/OHLC endpoint.

    Kraken caps this endpoint at 720 bars per response and does NOT support
    paging further back. For deep history, /0/public/Trades + local
    aggregation would be required (not implemented here).

    Parameters
    ----------
    hbot_pair : str
        Hummingbot-style BASE-QUOTE, e.g. "BTC-USDT".
    interval : str
        Hummingbot-style interval key (e.g. "5m", "1h").
    since_ts : int or None
        Optional lower timestamp bound (seconds). Kraken interprets as
        "return bars with timestamp > since_ts". If None, returns the
        most recent 720 bars.

    Returns
    -------
    list[dict] where each dict has {timestamp, open, high, low, close, volume}.
    Timestamps are seconds (Kraken returns seconds already).
    """
    ex_cfg = EXCHANGES["kraken"]
    api_interval = ex_cfg["interval_map"].get(interval)
    if api_interval is None:
        return []
    url = ex_cfg["base_url"].rstrip("/") + "/0/public/OHLC"
    params = {
        "pair": to_kraken_symbol(hbot_pair),
        "interval": int(api_interval),
    }
    if since_ts is not None:
        params["since"] = int(since_ts)
    data = http_get_json(url, params, prefix="[kraken] ", exchange="kraken")

    # Kraken response shape:
    #   {"error": [...], "result": {"<pair_key>": [[ts,o,h,l,c,vwap,vol,count], ...], "last": <ts>}}
    if not isinstance(data, dict):
        return []
    if data.get("error"):
        # Kraken surfaces errors as a list of strings in "error"
        print(f"  [kraken] API error for {hbot_pair}: {data[\'error\']}")
        return []
    result = data.get("result", {})
    if not isinstance(result, dict):
        return []
    # The response dict has one key that's the pair (not always matching our
    # request symbol) and a "last" key. Find the pair's OHLC list.
    pair_key = None
    for k in result.keys():
        if k != "last":
            pair_key = k
            break
    if pair_key is None:
        return []
    rows = result.get(pair_key, [])
    if not isinstance(rows, list):
        return []

    candles = []
    for r in rows:
        if not isinstance(r, (list, tuple)) or len(r) < 7:
            continue
        ts_open = int(r[0])   # Kraken returns seconds already
        candles.append({
            "timestamp": ts_open,
            "open":   safe_float(r[1]),
            "high":   safe_float(r[2]),
            "low":    safe_float(r[3]),
            "close":  safe_float(r[4]),
            "volume": safe_float(r[6]),   # r[5] is vwap, r[6] is base volume
        })
    return candles'''


# ── D) Cell 4: add ingest_kraken_range and register it ─────────────────────
_C4_INGESTER = '''def ingest_kraken_range(coll, hbot_pair, interval, start_ts, end_ts):
    """Shallow-mode ingester for Kraken.

    Kraken's OHLC endpoint does NOT support historical pagination. It
    always returns the most recent 720 bars (or bars newer than `since`
    if specified). For gap-filling of historical data older than ~720 bars
    of the requested interval, a Trades-aggregation path is needed — not
    implemented here.

    Strategy: call OHLC with `since = start_ts - step` and hope the gap
    is within the most recent 720 bars. If the gap predates that window,
    we log a warning and skip. This is sufficient for routine catch-up
    runs against a pre-populated database but NOT for initial deep-history
    backfills.
    """
    ex_cfg = EXCHANGES["kraken"]
    if ex_cfg["interval_map"].get(interval) is None:
        return 0
    step = INTERVAL_SECONDS[interval]
    now_ts = utc_now_ts()
    max_per = ex_cfg["max_per_request"]  # 720

    # If the requested range extends further back than Kraken's hard limit,
    # warn and clamp forward.
    earliest_fetchable = now_ts - (max_per * step)
    if start_ts < earliest_fetchable:
        print(f"  [kraken] {hbot_pair} {interval}: requested range starts "
              f"{(now_ts - start_ts)/86400:.0f}d ago, but Kraken OHLC only "
              f"returns most-recent {max_per} bars "
              f"({max_per*step/86400:.0f}d). Clamping to fetchable window.")
        start_ts = earliest_fetchable

    # Fetch with `since = start_ts - step` so we include the start boundary.
    bars = fetch_kraken_candles(hbot_pair, interval,
                                 since_ts=max(0, start_ts - step))
    if not bars:
        return 0

    docs = []
    for b in bars:
        ts_open = int(b["timestamp"])
        if ts_open < start_ts or ts_open > end_ts:
            continue
        docs.append(normalize_candle_doc(
            connector="kraken", hbot_pair=hbot_pair, interval=interval,
            ts_open=ts_open, open_=b["open"], high=b["high"], low=b["low"],
            close=b["close"], base_volume=b["volume"],
            interval_seconds=step, now_ts=now_ts,
        ))
    if docs:
        return upsert_candles(coll, docs, is_backfill=True)
    return 0


'''


# ─────────────────────────────────────────────────────────────────────────

def _src(cell):
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else (s or "")


def _set(cell, new_src):
    cell["source"] = new_src.splitlines(keepends=True)
    cell["outputs"] = []
    cell["execution_count"] = None


def patch_yaml():
    text = YAML_PATH.read_text(encoding="utf-8")
    # Idempotent: if `# kraken:` line exists (comment form) and the live
    # block `  kraken:` is absent, skip.
    if "# kraken:" in text and re.search(r"^\s{2}kraken:", text, re.MULTILINE) is None:
        return False
    if _YAML_OLD_BLOCK not in text:
        raise AssertionError("YAML: pre-existing kraken block not found verbatim")
    YAML_PATH.write_text(text.replace(_YAML_OLD_BLOCK, _YAML_NEW_BLOCK, 1), encoding="utf-8")
    return True


def patch_cell2(cell):
    src = _src(cell)
    changed = False

    # B.1 — tuning line spacing
    if _C2_TUNING_NEW not in src:
        if _C2_TUNING_OLD not in src:
            raise AssertionError("Cell 2: kraken tuning line not found with expected shape")
        src = src.replace(_C2_TUNING_OLD, _C2_TUNING_NEW, 1)
        changed = True

    # B.2 — add _KRAKEN_BASE_TRANSLATIONS + to_kraken_symbol
    if "_KRAKEN_BASE_TRANSLATIONS" not in src:
        if _C2_COINBASE_ANCHOR not in src:
            raise AssertionError("Cell 2: to_coinbase_product_id anchor not found")
        src = src.replace(_C2_COINBASE_ANCHOR, _C2_KRAKEN_HELPERS, 1)
        changed = True

    if changed:
        _set(cell, src)
    return changed


def patch_cell3(cell):
    src = _src(cell)
    if "def to_kraken_symbol" in src:
        pass  # we didn't add it here — but let that be
    # Idempotent: skip if full fetcher signature + response-dict iteration present
    if "fetch_kraken_candles(hbot_pair, interval, since_ts=None)" in src \
            and 'if k != "last"' in src:
        return False
    if _C3_STUB not in src:
        raise AssertionError("Cell 3: stub fetch_kraken_candles not found verbatim")
    src = src.replace(_C3_STUB, _C3_NEW_FETCHER, 1)
    _set(cell, src)
    return True


def patch_cell4(cell):
    src = _src(cell)
    changed = False

    # D.1 — insert ingest_kraken_range before INGESTERS
    if "def ingest_kraken_range(" not in src:
        anchor = "INGESTERS = {"
        idx = src.find(anchor)
        if idx == -1:
            raise AssertionError("Cell 4: INGESTERS dict not found")
        src = src[:idx] + _C4_INGESTER + src[idx:]
        changed = True

    # D.2 — add kraken entry to INGESTERS dict
    if '"kraken":' not in src.split("INGESTERS = {")[1].split("}")[0]:
        old_ing = '    "coinbase": ingest_coinbase_range,\n}'
        new_ing = '    "coinbase": ingest_coinbase_range,\n    "kraken": ingest_kraken_range,\n}'
        if old_ing not in src:
            raise AssertionError("Cell 4: INGESTERS closing pattern not found")
        src = src.replace(old_ing, new_ing, 1)
        changed = True

    if changed:
        _set(cell, src)
    return changed


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    did_yaml = patch_yaml()

    with open(NB_PATH, encoding="utf-8") as f:
        nb = json.load(f)

    cell_idx = {}
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        s = _src(c)
        if "class _TokenBucket" in s:
            cell_idx["c2"] = i
        elif "FETCHERS = {" in s:
            cell_idx["c3"] = i
        elif "INGESTERS = {" in s:
            cell_idx["c4"] = i

    for key in ("c2", "c3", "c4"):
        if key not in cell_idx:
            raise RuntimeError(f"{key} cell not found")

    did_c2 = patch_cell2(nb["cells"][cell_idx["c2"]])
    did_c3 = patch_cell3(nb["cells"][cell_idx["c3"]])
    did_c4 = patch_cell4(nb["cells"][cell_idx["c4"]])

    with open(NB_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)

    print(f"A) YAML kraken block commented:                  {'updated' if did_yaml else 'already patched'}")
    print(f"B) Cell {cell_idx['c2']} tuning spacing + helpers:         {'updated' if did_c2 else 'already patched'}")
    print(f"C) Cell {cell_idx['c3']} fetch_kraken_candles full impl:    {'updated' if did_c3 else 'already patched'}")
    print(f"D) Cell {cell_idx['c4']} ingest_kraken_range + INGESTERS:  {'updated' if did_c4 else 'already patched'}")


if __name__ == "__main__":
    main()
