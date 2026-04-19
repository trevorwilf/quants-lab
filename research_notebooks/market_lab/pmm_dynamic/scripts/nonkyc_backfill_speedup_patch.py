"""One-shot patcher for `candle_backfill_v3.ipynb`.

Applies three in-place edits:
  B) Cell 2: replace lock-based HTTP pacing with a token-bucket rate limiter
             + per-exchange tuning + new `http_get_json`.
  C) Cell 4: rewrite `ingest_nonkyc_range` to drop the legacy `time.sleep(delay)`
             tail (pacing now handled by the token bucket in http_get_json).
  D) Cell 11: replace the parallel driver with outer-exchange + inner-pair pool.

Also appends:
  E) Smoke-test markdown + code cells at the end.

Idempotent: detects existing patches and skips them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

NB_PATH = (
    Path(__file__).resolve().parent.parent
    / "notebooks" / "mongo_tools" / "candle_backfill_v3.ipynb"
)


# ── Change B — Cell 2 HTTP pacing replacement ─────────────────────────────
# Replaces the lines from the `# One Session per exchange worker.` comment
# through the end of the old `http_get_json` function. We keep imports +
# helper functions (utc_now_ts, align_floor, to_*_symbol, compute_qc_flags,
# normalize_candle_doc, upsert_candles, etc.) exactly as-is.

_B_OLD = """# One Session per exchange worker. MongoClient is thread-safe; requests.Session
# is also thread-safe for simple GET use so we share a single session.
session = requests.Session()
# Per-exchange lock for polite request pacing — one in-flight request at a time
# per exchange, even when multiple exchanges run concurrently.
_exchange_locks: dict = {}
_locks_mutex = threading.Lock()


def _get_exchange_lock(exchange: str) -> threading.Lock:
    with _locks_mutex:
        if exchange not in _exchange_locks:
            _exchange_locks[exchange] = threading.Lock()
        return _exchange_locks[exchange]


def http_get_json(url: str, params: dict = None, prefix: str = "", exchange: Optional[str] = None) -> Any:
    \"\"\"GET + JSON with retries. When `exchange` is given, hold the per-exchange
    lock for the whole request so pairs on the same exchange serialize even if
    two different exchange workers are running concurrently.\"\"\"
    lock = _get_exchange_lock(exchange) if exchange else None
    if lock is not None:
        lock.acquire()
    try:
        last_err = None
        for attempt in range(1, HTTP_MAX_RETRIES + 1):
            try:
                resp = session.get(url, params=params, timeout=HTTP_TIMEOUT)
                if resp.status_code in (429, 418):
                    retry_after = resp.headers.get("Retry-After")
                    sleep_s = float(retry_after) if retry_after else HTTP_RETRY_BACKOFF ** attempt
                    print(f"  {prefix}Rate limited (HTTP {resp.status_code}), sleeping {sleep_s:.1f}s")
                    time.sleep(sleep_s)
                    continue
                if resp.status_code in (500, 502, 503, 504):
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_err = e
                if attempt >= HTTP_MAX_RETRIES:
                    break
                time.sleep(HTTP_RETRY_BACKOFF ** (attempt - 1))
        raise last_err
    finally:
        if lock is not None:
            lock.release()"""


_B_NEW = '''# Connection pooling for high-concurrency HTTP
from requests.adapters import HTTPAdapter

session = requests.Session()
_adapter = HTTPAdapter(pool_connections=16, pool_maxsize=32, max_retries=0)
session.mount("https://", _adapter)
session.mount("http://", _adapter)


class _TokenBucket:
    """Thread-safe token bucket with auto-decay on rate-limit signal.

    rate_per_sec   steady-state refill rate (tokens/s)
    burst_capacity max tokens in bucket (for burst tolerance)
    """

    def __init__(self, rate_per_sec: float, burst_capacity: float):
        self.rate = float(rate_per_sec)
        self.capacity = float(burst_capacity)
        self.tokens = float(burst_capacity)
        self.last = time.monotonic()
        self._cv = threading.Condition()
        self._min_rate = 0.5

    def acquire(self) -> None:
        with self._cv:
            while True:
                now = time.monotonic()
                elapsed = now - self.last
                self.last = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                wait = (1.0 - self.tokens) / self.rate
                self._cv.wait(timeout=wait)

    def on_rate_limited(self, retry_after_seconds):
        with self._cv:
            self.rate = max(self._min_rate, self.rate * 0.5)
            self.tokens = 0.0
            self._cv.notify_all()
        if retry_after_seconds:
            time.sleep(retry_after_seconds)

    def stats(self):
        with self._cv:
            return {"rate_per_sec": self.rate, "tokens": self.tokens,
                    "capacity": self.capacity}


# Per-exchange tuning. These values have been empirically validated for NonKYC.
# For other exchanges, values are conservative starting points close to the
# previous effective rates. If you need to reduce load, lower rate_per_sec.
_EXCHANGE_TUNING = {
    "nonkyc":   {"rate_per_sec": 12.0, "burst": 24.0, "parallel": 4},
    "binance":  {"rate_per_sec": 8.0,  "burst": 16.0, "parallel": 2},
    "mexc":     {"rate_per_sec": 5.0,  "burst": 10.0, "parallel": 2},
    "coinbase": {"rate_per_sec": 3.0,  "burst": 6.0,  "parallel": 2},
}

_exchange_buckets: dict = {}
_buckets_mutex = threading.Lock()


def _get_exchange_bucket(exchange: str) -> _TokenBucket:
    with _buckets_mutex:
        b = _exchange_buckets.get(exchange)
        if b is None:
            cfg = _EXCHANGE_TUNING.get(exchange, {"rate_per_sec": 2.0, "burst": 4.0})
            b = _TokenBucket(cfg["rate_per_sec"], cfg["burst"])
            _exchange_buckets[exchange] = b
        return b


def get_exchange_parallel_workers(exchange: str) -> int:
    return _EXCHANGE_TUNING.get(exchange, {}).get("parallel", 1)


def http_get_json(url: str, params: dict = None, prefix: str = "",
                  exchange: Optional[str] = None) -> Any:
    """GET + JSON with retries and token-bucket pacing per exchange.

    Multiple threads can make requests concurrently against the same exchange
    as long as there are tokens available. On 429/1015, the bucket halves
    its rate automatically (min floor: 0.5 req/s) so sustained runs self-tune.
    """
    bucket = _get_exchange_bucket(exchange) if exchange else None
    last_err = None
    for attempt in range(1, HTTP_MAX_RETRIES + 1):
        if bucket is not None:
            bucket.acquire()
        try:
            resp = session.get(url, params=params, timeout=HTTP_TIMEOUT)
            if resp.status_code in (429, 418, 1015):
                retry_after = resp.headers.get("Retry-After")
                sleep_s = float(retry_after) if retry_after else HTTP_RETRY_BACKOFF ** attempt
                print(f"  {prefix}Rate limited (HTTP {resp.status_code}), "
                      f"sleeping {sleep_s:.1f}s and halving rate")
                if bucket is not None:
                    bucket.on_rate_limited(sleep_s)
                else:
                    time.sleep(sleep_s)
                continue
            if resp.status_code in (500, 502, 503, 504):
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            if attempt >= HTTP_MAX_RETRIES:
                break
            time.sleep(HTTP_RETRY_BACKOFF ** (attempt - 1))
    raise last_err'''


# ── Change C — ingest_nonkyc_range rewrite ────────────────────────────────

_C_OLD = '''def ingest_nonkyc_range(coll, hbot_pair, interval, start_ts, end_ts):
    ex_cfg = EXCHANGES["nonkyc"]
    if ex_cfg["interval_map"].get(interval) is None:
        return 0
    step = INTERVAL_SECONDS[interval]
    now_ts = utc_now_ts()
    max_per = ex_cfg["max_per_request"]
    delay = ex_cfg["request_delay_seconds"]
    page_to = end_ts + step - 1
    total = 0
    safety = 0
    while page_to >= start_ts and safety < 100000:
        safety += 1
        bars = fetch_nonkyc_candles(hbot_pair, interval, to_ts=page_to, count=max_per)
        if not bars:
            break
        docs = []
        oldest = None
        for b in bars:
            ts_open = int(b["timestamp"])
            if ts_open < start_ts or ts_open > end_ts:
                continue
            oldest = ts_open if oldest is None else min(oldest, ts_open)
            docs.append(normalize_candle_doc(
                connector="nonkyc", hbot_pair=hbot_pair, interval=interval,
                ts_open=ts_open, open_=b["open"], high=b["high"], low=b["low"],
                close=b["close"], base_volume=b["volume"],
                interval_seconds=step, now_ts=now_ts,
            ))
        if docs:
            total += upsert_candles(coll, docs, is_backfill=True)
        if oldest is None or oldest <= start_ts or oldest >= page_to:
            break
        page_to = oldest - 1
        time.sleep(delay)
    return total'''


_C_NEW = '''def ingest_nonkyc_range(coll, hbot_pair, interval, start_ts, end_ts):
    ex_cfg = EXCHANGES["nonkyc"]
    if ex_cfg["interval_map"].get(interval) is None:
        return 0
    step = INTERVAL_SECONDS[interval]
    now_ts = utc_now_ts()
    max_per = ex_cfg["max_per_request"]
    page_to = end_ts + step - 1
    total = 0
    safety = 0
    while page_to >= start_ts and safety < 100000:
        safety += 1
        bars = fetch_nonkyc_candles(hbot_pair, interval, to_ts=page_to, count=max_per)
        if not bars:
            break
        docs = []
        oldest = None
        for b in bars:
            ts_open = int(b["timestamp"])
            if ts_open < start_ts or ts_open > end_ts:
                continue
            oldest = ts_open if oldest is None else min(oldest, ts_open)
            docs.append(normalize_candle_doc(
                connector="nonkyc", hbot_pair=hbot_pair, interval=interval,
                ts_open=ts_open, open_=b["open"], high=b["high"], low=b["low"],
                close=b["close"], base_volume=b["volume"],
                interval_seconds=step, now_ts=now_ts,
            ))
        if docs:
            total += upsert_candles(coll, docs, is_backfill=True)
        if oldest is None or oldest <= start_ts or oldest >= page_to:
            break
        page_to = oldest - 1
        # No explicit sleep — the token bucket inside http_get_json paces requests
    return total'''


# ── Change D — entire Cell 11 replacement ─────────────────────────────────
# This is the whole new cell-11 body (from the prompt §3.4).

_D_NEW = '''# Cell 11: Run the backfill
#
# Layered parallelism:
#   - Outer: one thread per exchange.
#   - Inner: per-exchange parallel pair-workers (from _EXCHANGE_TUNING).
#   - Pacing: shared per-exchange token bucket enforces sustained rate caps.
# All pair-workers within an exchange share the same bucket, so adding
# workers raises parallelism without exceeding the rate-per-second cap.

if not selected_combos:
    print("Nothing to backfill.")
else:
    per_exchange = {}
    for c in selected_combos:
        per_exchange.setdefault(c["connector"], []).append(c)

    results = {}
    results_lock = threading.Lock()
    counter_lock = threading.Lock()
    total_series = len(selected_combos)
    counter = {"done": 0}

    def exchange_worker(exchange: str, combos_for_ex: list):
        ingester = INGESTERS.get(exchange)
        if ingester is None:
            with results_lock:
                results[exchange] = {"written": 0,
                                     "errors": [f"{exchange}: no ingester"],
                                     "gap_ranges": 0}
            return

        parallel_workers = get_exchange_parallel_workers(exchange)
        rate_cap = _EXCHANGE_TUNING.get(exchange, {}).get("rate_per_sec", "?")
        print(f"[{exchange}] {len(combos_for_ex)} series, "
              f"{parallel_workers} parallel pair-workers, rate cap = {rate_cap} req/s")

        local_written = 0
        local_errors: list = []
        local_gaps = 0
        local_lock = threading.Lock()

        def one_combo(combo):
            combo_written = 0
            pair = combo["pair"]
            interval = combo["interval"]
            step = combo["step"]
            is_new = combo.get("is_new_pair", False)
            win_start = combo["window_start"]

            if is_new:
                eff_start = align_floor(win_start, step)
                eff_end = last_closed_open_ts(utc_now_ts(), step)
                gaps = [(eff_start, eff_end)] if eff_end >= eff_start else []
            else:
                gaps = find_gaps_in_window(coll, exchange, pair, interval, step,
                                            win_start, utc_now_ts())

            if not gaps:
                with counter_lock:
                    counter["done"] += 1
                    done = counter["done"]
                print(f"[{done}/{total_series}] {exchange} {pair} {interval} \u2713 no gaps")
                return 0, 0, []

            errors_here = []
            for gs, ge in gaps:
                try:
                    combo_written += ingester(coll, pair, interval, gs, ge)
                except Exception as e:
                    err = f"{exchange} {pair} {interval} [{fmt_ts(gs)}\u2192{fmt_ts(ge)}]: {e}"
                    errors_here.append(err)
                    print(f"  \u2717 {err}")

            with counter_lock:
                counter["done"] += 1
                done = counter["done"]
            print(f"[{done}/{total_series}] {exchange} {pair} {interval}: "
                  f"wrote {combo_written:,} across {len(gaps)} range(s)")
            return combo_written, len(gaps), errors_here

        with ThreadPoolExecutor(max_workers=parallel_workers) as pair_pool:
            futs = {pair_pool.submit(one_combo, c): c for c in combos_for_ex}
            for fut in as_completed(futs):
                try:
                    w, g, errs = fut.result()
                    with local_lock:
                        local_written += w
                        local_gaps += g
                        local_errors.extend(errs)
                except Exception as e:
                    c = futs[fut]
                    with local_lock:
                        local_errors.append(
                            f"{exchange} {c['pair']} {c['interval']}: worker crashed: {e}"
                        )

        with results_lock:
            results[exchange] = {"written": local_written,
                                 "errors": local_errors,
                                 "gap_ranges": local_gaps}

    start_wall = time.time()
    n_exchange_workers = max(1, len(per_exchange))
    print(f"Running {n_exchange_workers} exchange(s) in parallel, "
          f"with per-exchange parallel pair-workers as configured.\\n")

    with ThreadPoolExecutor(max_workers=n_exchange_workers) as pool:
        futures = {pool.submit(exchange_worker, ex, cs): ex
                   for ex, cs in per_exchange.items()}
        for fut in as_completed(futures):
            ex = futures[fut]
            try:
                fut.result()
            except Exception as e:
                print(f"  \u2717 Worker for {ex} crashed: {e}")

    elapsed = time.time() - start_wall

    print(f"\\n{'\u2550' * 70}")
    print("BACKFILL COMPLETE")
    print(f"  Wall clock: {elapsed/60:.1f} min")
    total_written = sum(r["written"] for r in results.values())
    total_errors = sum(len(r["errors"]) for r in results.values())
    total_gaps = sum(r["gap_ranges"] for r in results.values())
    print(f"  Gap ranges processed: {total_gaps:,}")
    print(f"  Total candles written: {total_written:,}")
    print(f"  Errors: {total_errors}")
    for ex in sorted(results.keys()):
        r = results[ex]
        print(f"    {ex:12s} wrote {r['written']:>10,d} across "
              f"{r['gap_ranges']:>4} ranges, {len(r['errors'])} error(s)")
        try:
            s = _get_exchange_bucket(ex).stats()
            initial = _EXCHANGE_TUNING.get(ex, {}).get("rate_per_sec", "?")
            print(f"      final bucket rate: {s['rate_per_sec']:.2f} req/s "
                  f"(initial: {initial})")
            if isinstance(initial, (int, float)) and s["rate_per_sec"] < initial:
                print(f"      \u21aa rate was auto-decayed \u2014 {ex} returned 429s during the run")
        except Exception:
            pass
        for e in r["errors"][:5]:
            print(f"      \u2717 {e}")
        if len(r["errors"]) > 5:
            print(f"      ... and {len(r['errors']) - 5} more")
    print(f"{'\u2550' * 70}")'''


# ── Smoke-test cells ──────────────────────────────────────────────────────

_SMOKE_MD = (
    "## Smoke test for NonKYC pacing\n"
    "\n"
    "Delete this cell + the code cell below after one successful run.\n"
    "The code cell issues 20 NonKYC requests and prints the observed throughput.\n"
    "Expected: 1.5-3.0 seconds for 20 requests (rate cap 12 req/s + ~300ms RTT).\n"
    "If > 10s, pacing is still serialized somewhere — do NOT run Cell 11 yet.\n"
)

_SMOKE_CODE = '''# Smoke test — confirms token bucket pacing works against live NonKYC.
# Expected outcome: 20 serial requests complete in ~1.5-2.0 seconds wall
# time (bucket rate-cap of 12 req/s means min possible wall = 20/12 ~ 1.7s).
# If this takes 10+ seconds, something is still serialized.
import time as _t
_t0 = _t.perf_counter()
for _i in range(20):
    _ = fetch_nonkyc_candles("BTC-USDT", "1h", to_ts=int(_t.time()) - _i*3600, count=100)
_wall = _t.perf_counter() - _t0
print(f"Smoke test: 20 serial nonkyc requests in {_wall:.2f}s "
      f"= {20/_wall:.1f} req/s")
print(f"  Expected: 1.5-3.0s (rate-cap is 12 req/s + ~300ms RTT)")
print(f"  If > 10s, pacing is still serialized \u2014 do NOT run a full backfill.")
print(f"  Bucket stats: {_get_exchange_bucket('nonkyc').stats()}")'''


def _src_of(cell):
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else (s or "")


def _set_src(cell, new_src):
    cell["source"] = new_src.splitlines(keepends=True)
    cell["outputs"] = []
    cell["execution_count"] = None


def patch_cell2(cell):
    """Replace the lock-based pacing block with the new token-bucket block."""
    src = _src_of(cell)
    # Idempotence check
    if "_TokenBucket" in src and "_exchange_locks" not in src:
        return False  # already patched
    if _B_OLD not in src:
        raise AssertionError("Cell 2: old lock-based pacing block not found verbatim")
    new_src = src.replace(_B_OLD, _B_NEW, 1)
    _set_src(cell, new_src)
    return True


def patch_cell4(cell):
    src = _src_of(cell)
    if "# No explicit sleep" in src and 'delay = ex_cfg["request_delay_seconds"]' not in src:
        return False
    if _C_OLD not in src:
        raise AssertionError("Cell 4: old ingest_nonkyc_range body not found verbatim")
    new_src = src.replace(_C_OLD, _C_NEW, 1)
    _set_src(cell, new_src)
    return True


def patch_cell11(cell):
    src = _src_of(cell)
    if "get_exchange_parallel_workers" in src and "# Cell 11: Run the backfill" in src:
        return False
    _set_src(cell, _D_NEW)
    return True


def append_smoke_test_cells(nb):
    """Append markdown + code smoke-test cells at the end (idempotent)."""
    # Check whether already appended
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            if "Smoke test: 20 serial nonkyc requests" in _src_of(cell):
                return False
    nb["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": _SMOKE_MD.splitlines(keepends=True),
    })
    nb["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": _SMOKE_CODE.splitlines(keepends=True),
    })
    return True


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    with open(NB_PATH, encoding="utf-8") as f:
        nb = json.load(f)

    changed_b = patch_cell2(nb["cells"][2])
    changed_c = patch_cell4(nb["cells"][4])
    changed_d = patch_cell11(nb["cells"][11])
    changed_smoke = append_smoke_test_cells(nb)

    with open(NB_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)

    print(f"cell 2 (token-bucket HTTP pacing): {'updated' if changed_b else 'already patched'}")
    print(f"cell 4 (ingest_nonkyc_range):     {'updated' if changed_c else 'already patched'}")
    print(f"cell 11 (parallel driver):         {'updated' if changed_d else 'already patched'}")
    print(f"smoke-test cells appended:         {'yes' if changed_smoke else 'already present'}")


if __name__ == "__main__":
    main()
