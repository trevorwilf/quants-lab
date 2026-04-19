"""Watchdog timeout + gentler NonKYC pacing for candle_backfill_v3.ipynb.

Two surgical edits to Cell 2 only:
  A) Replace `http_get_json` body with a watchdog-thread version that
     enforces a hard 20s wall-clock deadline via `session.close()` when the
     watchdog fires. Required because Cloudflare's slow-loris trickle can
     defeat urllib3's per-recv `(5, 15)` read timeout.
  B) Lower `_EXCHANGE_TUNING["nonkyc"]` to
     `{"rate_per_sec": 2.0, "burst": 4.0, "parallel": 1}`.

Idempotent: re-runs detect an already-patched cell via
`HARD_DEADLINE_SECONDS` marker and skip Edit A.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

NB_PATH = (
    Path(__file__).resolve().parent.parent
    / "notebooks" / "mongo_tools" / "candle_backfill_v3.ipynb"
)


_NEW_HTTP_GET_JSON = '''def http_get_json(url: str, params: dict = None, prefix: str = "",
                  exchange: Optional[str] = None,
                  headers: Optional[dict] = None) -> Any:
    """GET + JSON with hard wall-clock deadline via watchdog thread.

    The primary timeout mechanism is a watchdog thread that force-closes
    the session's connection pool after HARD_DEADLINE_SECONDS regardless
    of whether urllib3's internal timeout fired. This is required because
    Cloudflare's slow-loris behavior can defeat urllib3's per-recv timeout
    by sending a single byte periodically.
    """
    HARD_DEADLINE_SECONDS = 20.0

    bucket = _get_exchange_bucket(exchange) if exchange else None
    last_err = None

    for attempt in range(1, HTTP_MAX_RETRIES + 1):
        if bucket is not None:
            bucket.acquire()

        done = threading.Event()

        def _watchdog():
            if not done.wait(HARD_DEADLINE_SECONDS):
                try:
                    session.close()
                    print(f"  {prefix}Watchdog: killed hung connection after "
                          f"{HARD_DEADLINE_SECONDS:.0f}s")
                except Exception:
                    pass

        watchdog = threading.Thread(target=_watchdog, daemon=True)
        watchdog.start()

        try:
            resp = session.get(
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
            done.set()
            return resp.json()
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            try:
                session.close()
            except Exception:
                pass
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

    raise last_err


'''


_OLD_NONKYC = '"nonkyc":   {"rate_per_sec": 6.0, "burst": 12.0, "parallel": 2},'
_NEW_NONKYC = '"nonkyc":   {"rate_per_sec": 2.0, "burst": 4.0, "parallel": 1},'


def _find_cell2(nb):
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
        if "class _TokenBucket" in src and "_EXCHANGE_TUNING" in src:
            return i, src
    raise RuntimeError("Could not find Cell 2 by content match")


def patch_http_get_json(src: str) -> tuple[str, bool]:
    """Edit A: replace http_get_json body. Idempotent."""
    if "HARD_DEADLINE_SECONDS = 20.0" in src and "def _watchdog():" in src:
        return src, False

    old_fn_start = src.find("def http_get_json(")
    if old_fn_start == -1:
        raise RuntimeError("http_get_json function not found in Cell 2")

    end_marker = "def normalize_candle_doc("
    old_fn_end = src.find(end_marker, old_fn_start)
    if old_fn_end == -1:
        raise RuntimeError(
            "Could not locate end of http_get_json "
            "(expected 'def normalize_candle_doc(' downstream)"
        )

    src_new = src[:old_fn_start] + _NEW_HTTP_GET_JSON + src[old_fn_end:]
    return src_new, True


def patch_nonkyc_tuning(src: str) -> tuple[str, bool]:
    """Edit B: replace nonkyc tuning. Idempotent."""
    if _NEW_NONKYC in src:
        return src, False

    if _OLD_NONKYC in src:
        return src.replace(_OLD_NONKYC, _NEW_NONKYC, 1), True

    pattern = re.compile(
        r'"nonkyc":\s*\{"rate_per_sec":\s*[\d.]+,\s*'
        r'"burst":\s*[\d.]+,\s*"parallel":\s*\d+\}\s*,'
    )
    if pattern.search(src):
        return pattern.sub(_NEW_NONKYC, src, count=1), True

    raise RuntimeError("Could not find nonkyc tuning line to replace")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    with open(NB_PATH, encoding="utf-8") as f:
        nb = json.load(f)

    idx, src = _find_cell2(nb)
    src, did_A = patch_http_get_json(src)
    src, did_B = patch_nonkyc_tuning(src)

    nb["cells"][idx]["source"] = src.splitlines(keepends=True)
    nb["cells"][idx]["outputs"] = []
    nb["cells"][idx]["execution_count"] = None

    with open(NB_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)

    print(f"A) http_get_json watchdog:           {'updated' if did_A else 'already patched'}")
    print(f"B) nonkyc tuning 2.0/4.0/1:          {'updated' if did_B else 'already patched'}")


if __name__ == "__main__":
    main()
