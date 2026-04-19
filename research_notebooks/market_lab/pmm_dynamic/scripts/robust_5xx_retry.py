"""Add robust 5xx retry handling to http_get_json in candle_backfill_v3.ipynb.

Single edit to Cell 2: replace http_get_json body so that transient 5xx
errors (500, 502, 503, 504) get a separate 6-retry budget with exponential
backoff capped at 30s + ±30% jitter + visible retry logging. Non-5xx paths
(ReadTimeout, ConnectionError, generic exceptions) keep the existing
HTTP_MAX_RETRIES budget. Watchdog, local_session-per-attempt, token
bucket, and 429/418/1015 handling are preserved.

Idempotent: detects already-patched state via `RETRY_BUDGET_5XX = 6`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

NB_PATH = (
    Path(__file__).resolve().parent.parent
    / "notebooks" / "mongo_tools" / "candle_backfill_v3.ipynb"
)


_OLD = '''def http_get_json(url: str, params: dict = None, prefix: str = "",
                  exchange: Optional[str] = None,
                  headers: Optional[dict] = None) -> Any:
    """GET + JSON with per-request session (no shared-state issues).

    Each attempt creates its own requests.Session, uses it, and closes it in
    a finally block. This avoids the footgun where session.close() on a
    shared session leaves the session in an undefined state for subsequent
    callers — the likely cause of indefinite hangs in long-running backfills.

    Watchdog thread enforces HARD_DEADLINE_SECONDS wall-clock ceiling.
    """
    HARD_DEADLINE_SECONDS = 20.0

    bucket = _get_exchange_bucket(exchange) if exchange else None
    last_err = None

    for attempt in range(1, HTTP_MAX_RETRIES + 1):
        if bucket is not None:
            bucket.acquire()

        # Fresh session per attempt — closing it only affects this attempt
        local_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=1, pool_maxsize=1, max_retries=0,
        )
        local_session.mount("https://", adapter)
        local_session.mount("http://", adapter)

        done = threading.Event()

        def _watchdog():
            if not done.wait(HARD_DEADLINE_SECONDS):
                try:
                    local_session.close()
                    print(f"  {prefix}Watchdog: killed hung connection after "
                          f"{HARD_DEADLINE_SECONDS:.0f}s")
                except Exception:
                    pass

        watchdog = threading.Thread(target=_watchdog, daemon=True)
        watchdog.start()

        try:
            resp = local_session.get(
                url, params=params, headers=headers,
                timeout=(5, 15),
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
                done.set()
                continue
            if resp.status_code in (500, 502, 503, 504):
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            resp.raise_for_status()
            result = resp.json()
            done.set()
            return result
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            last_err = e
            done.set()
            if attempt >= HTTP_MAX_RETRIES:
                break
            time.sleep(HTTP_RETRY_BACKOFF ** (attempt - 1))
        except Exception as e:
            last_err = e
            done.set()
            if attempt >= HTTP_MAX_RETRIES:
                break
            time.sleep(HTTP_RETRY_BACKOFF ** (attempt - 1))
        finally:
            try:
                local_session.close()
            except Exception:
                pass

    raise last_err'''


_NEW = '''def http_get_json(url: str, params: dict = None, prefix: str = "",
                  exchange: Optional[str] = None,
                  headers: Optional[dict] = None) -> Any:
    """GET + JSON with per-request session, watchdog, and robust 5xx retries.

    Behavior:
    - Watchdog thread enforces HARD_DEADLINE_SECONDS wall-clock ceiling.
    - 5xx errors (500, 502, 503, 504) are retried up to RETRY_BUDGET_5XX
      times with exponential backoff + random jitter. These are treated
      as transient backend hiccups.
    - Non-5xx errors (connection errors, timeouts, other exceptions)
      retry up to HTTP_MAX_RETRIES times using the standard backoff.
    - Rate limits (429, 418, 1015) use the token bucket's auto-decay.
    - Each attempt gets a fresh requests.Session so closing it on
      timeout doesn't affect other attempts.
    """
    import random  # stdlib

    HARD_DEADLINE_SECONDS = 20.0
    RETRY_BUDGET_5XX = 6            # More aggressive than HTTP_MAX_RETRIES for 5xx
    MAX_BACKOFF_5XX = 30.0          # Cap backoff so a single retry doesn't sleep forever

    bucket = _get_exchange_bucket(exchange) if exchange else None
    last_err = None
    attempt = 0
    attempt_5xx = 0

    # Use a looser attempt cap that accommodates either budget.
    max_attempts = max(HTTP_MAX_RETRIES, RETRY_BUDGET_5XX)

    while attempt < max_attempts:
        attempt += 1
        if bucket is not None:
            bucket.acquire()

        local_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=1, pool_maxsize=1, max_retries=0,
        )
        local_session.mount("https://", adapter)
        local_session.mount("http://", adapter)

        done = threading.Event()

        def _watchdog():
            if not done.wait(HARD_DEADLINE_SECONDS):
                try:
                    local_session.close()
                    print(f"  {prefix}Watchdog: killed hung connection after "
                          f"{HARD_DEADLINE_SECONDS:.0f}s")
                except Exception:
                    pass

        watchdog = threading.Thread(target=_watchdog, daemon=True)
        watchdog.start()

        try:
            resp = local_session.get(
                url, params=params, headers=headers,
                timeout=(5, 15),
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
                done.set()
                continue
            if resp.status_code in (500, 502, 503, 504):
                # Transient backend error — treat with the 5xx-specific budget
                attempt_5xx += 1
                last_err = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                done.set()
                if attempt_5xx >= RETRY_BUDGET_5XX:
                    break
                # Exponential backoff with jitter (0.7x - 1.3x multiplier)
                raw_backoff = min(MAX_BACKOFF_5XX,
                                   HTTP_RETRY_BACKOFF ** attempt_5xx)
                sleep_s = raw_backoff * (0.7 + 0.6 * random.random())
                print(f"  {prefix}HTTP {resp.status_code} transient, "
                      f"retrying in {sleep_s:.1f}s "
                      f"(attempt {attempt_5xx}/{RETRY_BUDGET_5XX})")
                time.sleep(sleep_s)
                continue
            resp.raise_for_status()
            result = resp.json()
            done.set()
            return result
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            last_err = e
            done.set()
            if attempt >= HTTP_MAX_RETRIES:
                break
            time.sleep(HTTP_RETRY_BACKOFF ** (attempt - 1))
        except Exception as e:
            last_err = e
            done.set()
            if attempt >= HTTP_MAX_RETRIES:
                break
            time.sleep(HTTP_RETRY_BACKOFF ** (attempt - 1))
        finally:
            try:
                local_session.close()
            except Exception:
                pass

    raise last_err'''


def _src(cell):
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else (s or "")


def _set(cell, new_src):
    cell["source"] = new_src.splitlines(keepends=True)
    cell["outputs"] = []
    cell["execution_count"] = None


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    with open(NB_PATH, encoding="utf-8") as f:
        nb = json.load(f)

    idx = None
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        s = _src(c)
        if "def http_get_json" in s and "class _TokenBucket" in s:
            idx = i
            break
    if idx is None:
        raise RuntimeError("Cell 2 (http_get_json + _TokenBucket) not found")

    src = _src(nb["cells"][idx])

    if "RETRY_BUDGET_5XX = 6" in src and "MAX_BACKOFF_5XX = 30.0" in src:
        print(f"Cell {idx}: already patched")
        return

    if _OLD not in src:
        raise AssertionError(
            "Cell 2: current http_get_json body does not match expected pre-state verbatim"
        )

    new_src = src.replace(_OLD, _NEW, 1)
    _set(nb["cells"][idx], new_src)

    with open(NB_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)

    print(f"Cell {idx}: http_get_json updated with 5xx retry + jitter + logging")


if __name__ == "__main__":
    main()
