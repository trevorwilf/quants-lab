"""Slow-loris fix patch for candle_backfill_v3.ipynb.

Applies four surgical edits:
  A) Cell 2 — rewrite `http_get_json` with tuple timeout (5, 15) + explicit
     ReadTimeout/ConnectionError handling that closes the pooled Session.
  B) Cell 3 — add `headers={"Connection": "close"}` to `fetch_nonkyc_candles`
     only (not other exchanges).
  C) Cell 2 — adjust `_EXCHANGE_TUNING["nonkyc"]` to
     `{"rate_per_sec": 6.0, "burst": 12.0, "parallel": 2}`.
  D) Final smoke-test cell — replace the 20-request serial smoke test with a
     100-request × 2-worker stress test that fails loud if any request
     approaches the 15s read timeout.

Idempotent: re-runs are safe — checks for existing patch markers before
mutating.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

NB_PATH = (
    Path(__file__).resolve().parent.parent
    / "notebooks" / "mongo_tools" / "candle_backfill_v3.ipynb"
)


# ── A) New http_get_json body ─────────────────────────────────────────────
_A_OLD = '''def http_get_json(url: str, params: dict = None, prefix: str = "",
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


_A_NEW = '''def http_get_json(url: str, params: dict = None, prefix: str = "",
                  exchange: Optional[str] = None,
                  headers: Optional[dict] = None) -> Any:
    """GET + JSON with retries, token-bucket pacing, and hung-connection recovery.

    Uses a (connect=5s, read=15s) tuple timeout. When a response hangs
    (ReadTimeout) or the connection drops (ConnectionError), the pooled
    Session is closed to force a fresh TCP connection on the next attempt.
    This is the specific countermeasure for Cloudflare's slow-loris
    soft-throttle behavior observed on NonKYC keep-alive connections during
    long backfills.
    """
    bucket = _get_exchange_bucket(exchange) if exchange else None
    last_err = None
    for attempt in range(1, HTTP_MAX_RETRIES + 1):
        if bucket is not None:
            bucket.acquire()
        try:
            resp = session.get(
                url, params=params, headers=headers,
                timeout=(5, 15),   # (connect, read) — NOT HTTP_TIMEOUT
            )
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
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            # Slow-loris / stalled-connection path: force-close all pooled
            # connections so the next attempt opens a fresh TCP socket.
            try:
                session.close()
            except Exception:
                pass
            last_err = e
            if attempt >= HTTP_MAX_RETRIES:
                break
            time.sleep(HTTP_RETRY_BACKOFF ** (attempt - 1))
        except Exception as e:
            last_err = e
            if attempt >= HTTP_MAX_RETRIES:
                break
            time.sleep(HTTP_RETRY_BACKOFF ** (attempt - 1))
    raise last_err'''


# ── C) _EXCHANGE_TUNING nonkyc entry ──────────────────────────────────────
_C_OLD = '"nonkyc":   {"rate_per_sec": 12.0, "burst": 24.0, "parallel": 4},'
_C_NEW = '"nonkyc":   {"rate_per_sec": 6.0, "burst": 12.0, "parallel": 2},'


# ── B) fetch_nonkyc_candles http_get_json call site ──────────────────────
_B_OLD = 'data = http_get_json(url, params, prefix="[nonkyc] ", exchange="nonkyc")'
_B_NEW = ('data = http_get_json(url, params, prefix="[nonkyc] ",\n'
          '                         exchange="nonkyc",\n'
          '                         headers={"Connection": "close"})')


# ── D) Stress smoke-test body (replaces the prior 20-request serial test) ──

_SMOKE_STRESS = '''# Stress smoke test — validates slow-loris mitigation.
# Expected outcome: 100 requests complete in 15-30 seconds with 2 pair-workers
# (6 req/s cap, plus TCP+TLS handshake per request). No single request should
# exceed the 15s read timeout.
import time as _t
from concurrent.futures import ThreadPoolExecutor, as_completed

N_REQUESTS = 100
N_WORKERS = 2

def _one(i):
    t0 = _t.perf_counter()
    try:
        bars = fetch_nonkyc_candles("BTC-USDT", "1h",
                                    to_ts=int(_t.time()) - i*3600, count=100)
        return ("ok", _t.perf_counter() - t0, len(bars))
    except Exception as e:
        return ("err", _t.perf_counter() - t0, str(e))

_start = _t.perf_counter()
with ThreadPoolExecutor(max_workers=N_WORKERS) as pool:
    results = [f.result() for f in as_completed(
        pool.submit(_one, i) for i in range(N_REQUESTS)
    )]
_wall = _t.perf_counter() - _start

ok = [r for r in results if r[0] == "ok"]
err = [r for r in results if r[0] == "err"]
latencies = sorted(r[1] for r in ok)

print(f"Stress smoke test: {N_REQUESTS} requests, {N_WORKERS} workers")
print(f"  Wall time: {_wall:.2f}s = {N_REQUESTS/_wall:.1f} req/s effective")
print(f"  OK: {len(ok)}  Errors: {len(err)}")
if latencies:
    p50 = latencies[len(latencies)//2]
    p95 = latencies[int(len(latencies)*0.95)]
    p99 = latencies[int(len(latencies)*0.99)]
    pmax = latencies[-1]
    print(f"  Latency p50={p50*1000:.0f}ms  p95={p95*1000:.0f}ms  "
          f"p99={p99*1000:.0f}ms  max={pmax*1000:.0f}ms")
print(f"  Bucket stats: {_get_exchange_bucket('nonkyc').stats()}")
print()
if len(err) > 0:
    print(f"  \u26a0  Errors occurred:")
    for e in err[:5]:
        print(f"      {e[2]}")
    print(f"      (showing first 5 of {len(err)})")
if latencies and latencies[-1] > 14.5:
    print(f"  \u2717 FAIL \u2014 at least one request hung near the 15s timeout.")
    print(f"    Slow-loris is still occurring. Do NOT run full backfill.")
elif len(err) > len(ok) * 0.05:
    print(f"  \u26a0  >5% errors. Consider lowering rate_per_sec or parallel.")
elif N_REQUESTS / _wall < 4.0:
    print(f"  \u26a0  Throughput below 4 req/s \u2014 slower than expected with 2 workers.")
    print(f"    May still be fine; try full backfill but watch for stalls.")
else:
    print(f"  \u2713 PASS \u2014 no stalls, no errors, sustained throughput looks healthy.")
    print(f"    Ready to run Cell 11 for full backfill.")'''


def _src(cell):
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else (s or "")


def _set(cell, new_src):
    cell["source"] = new_src.splitlines(keepends=True)
    cell["outputs"] = []
    cell["execution_count"] = None


def patch_cell2(cell):
    src = _src(cell)
    did_A = False
    did_C = False

    # A) http_get_json rewrite
    if "timeout=(5, 15)" in src and "session.close()" in src:
        # Already patched
        pass
    else:
        if _A_OLD not in src:
            raise AssertionError("Cell 2: old http_get_json body not found verbatim")
        src = src.replace(_A_OLD, _A_NEW, 1)
        did_A = True

    # C) _EXCHANGE_TUNING["nonkyc"]
    if _C_NEW in src:
        pass
    else:
        if _C_OLD not in src:
            raise AssertionError("Cell 2: old nonkyc tuning entry not found")
        src = src.replace(_C_OLD, _C_NEW, 1)
        did_C = True

    if did_A or did_C:
        _set(cell, src)
    return did_A, did_C


def patch_cell3(cell):
    src = _src(cell)
    if '"Connection": "close"' in src:
        return False  # already has the header somewhere
    if _B_OLD not in src:
        raise AssertionError(
            "Cell 3: fetch_nonkyc_candles http_get_json call not found in expected form"
        )
    src = src.replace(_B_OLD, _B_NEW, 1)
    _set(cell, src)
    return True


def patch_smoke_test(nb):
    """Find the last code cell whose body starts with 'Smoke test' or 'Stress
    smoke test' and replace it. Pre-existing tail cells from the earlier
    prompt begin with '# Smoke test'."""
    for cell in reversed(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        s = _src(cell)
        if s.startswith("# Smoke test") or s.startswith("# Stress smoke test"):
            if "N_REQUESTS = 100" in s and "slow-loris" in s.lower():
                return False  # already patched
            _set(cell, _SMOKE_STRESS)
            return True
    # Not found — append instead
    nb["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## Stress smoke test for NonKYC pacing\n",
                    "Delete after one successful run.\n"],
    })
    nb["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": _SMOKE_STRESS.splitlines(keepends=True),
    })
    return True


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    with open(NB_PATH, encoding="utf-8") as f:
        nb = json.load(f)

    did_A, did_C = patch_cell2(nb["cells"][2])
    did_B = patch_cell3(nb["cells"][3])
    did_smoke = patch_smoke_test(nb)

    with open(NB_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)

    print(f"A) http_get_json rewrite:             {'updated' if did_A else 'already patched'}")
    print(f"B) fetch_nonkyc_candles Connection:close: {'updated' if did_B else 'already patched'}")
    print(f"C) _EXCHANGE_TUNING nonkyc 6.0/12.0/2:   {'updated' if did_C else 'already patched'}")
    print(f"D) stress smoke-test cell:               {'updated' if did_smoke else 'already patched'}")


if __name__ == "__main__":
    main()
