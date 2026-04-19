"""Per-pair timing + heartbeat for candle_backfill_v3.ipynb.

Two edits:
  A) Cell 4 `ingest_nonkyc_range` — add heartbeat that prints every 30s when
     a single pair takes long (shows reqs / written / elapsed).
  B) Cell 11 `one_combo` — capture `combo_started`/`combo_elapsed` and
     include per-pair timing + running sweep wall-clock + ETA on the
     completion line (both the "no gaps" and "wrote" paths).

Idempotent: detects already-patched state via `combo_started = time.perf_counter()`
and `last_heartbeat = started` markers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

NB_PATH = (
    Path(__file__).resolve().parent.parent
    / "notebooks" / "mongo_tools" / "candle_backfill_v3.ipynb"
)


# ── Edit A: ingest_nonkyc_range (Cell 4) ──────────────────────────────────
_A_OLD = '''def ingest_nonkyc_range(coll, hbot_pair, interval, start_ts, end_ts):
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

_A_NEW = '''def ingest_nonkyc_range(coll, hbot_pair, interval, start_ts, end_ts):
    ex_cfg = EXCHANGES["nonkyc"]
    if ex_cfg["interval_map"].get(interval) is None:
        return 0
    step = INTERVAL_SECONDS[interval]
    now_ts = utc_now_ts()
    max_per = ex_cfg["max_per_request"]
    page_to = end_ts + step - 1
    total = 0
    safety = 0
    started = time.perf_counter()
    last_heartbeat = started
    requests_made = 0
    while page_to >= start_ts and safety < 100000:
        safety += 1
        requests_made += 1
        bars = fetch_nonkyc_candles(hbot_pair, interval, to_ts=page_to, count=max_per)
        # Heartbeat: show live progress when a single pair is taking a while
        now_pc = time.perf_counter()
        if now_pc - last_heartbeat >= 30.0:
            elapsed = now_pc - started
            print(f"    [nonkyc] {hbot_pair} {interval}: "
                  f"{requests_made} reqs, {total:,} written, {elapsed:.0f}s elapsed")
            last_heartbeat = now_pc
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


# ── Edit B: one_combo (Cell 11) ───────────────────────────────────────────
# Note: one_combo is nested inside exchange_worker — every line is indented
# 8 spaces. Preserve that indentation.
_B_OLD = '''        def one_combo(combo):
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
                print(f"[{done}/{total_series}] {exchange} {pair} {interval} ✓ no gaps")
                return 0, 0, []

            errors_here = []
            for gs, ge in gaps:
                try:
                    combo_written += ingester(coll, pair, interval, gs, ge)
                except Exception as e:
                    err = f"{exchange} {pair} {interval} [{fmt_ts(gs)}→{fmt_ts(ge)}]: {e}"
                    errors_here.append(err)
                    print(f"  ✗ {err}")

            with counter_lock:
                counter["done"] += 1
                done = counter["done"]
            print(f"[{done}/{total_series}] {exchange} {pair} {interval}: "
                  f"wrote {combo_written:,} across {len(gaps)} range(s)")
            return combo_written, len(gaps), errors_here'''

_B_NEW = '''        def one_combo(combo):
            combo_started = time.perf_counter()
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
                sweep_elapsed = time.time() - start_wall
                eta = (sweep_elapsed / done * (total_series - done)) if done > 0 else 0
                print(f"[{done}/{total_series}] {exchange} {pair} {interval} "
                      f"✓ no gaps  [sweep {sweep_elapsed/60:.1f}min, ETA {eta/60:.1f}min]")
                return 0, 0, []

            errors_here = []
            for gs, ge in gaps:
                try:
                    combo_written += ingester(coll, pair, interval, gs, ge)
                except Exception as e:
                    err = f"{exchange} {pair} {interval} [{fmt_ts(gs)}→{fmt_ts(ge)}]: {e}"
                    errors_here.append(err)
                    print(f"  ✗ {err}")

            combo_elapsed = time.perf_counter() - combo_started
            with counter_lock:
                counter["done"] += 1
                done = counter["done"]
            sweep_elapsed = time.time() - start_wall
            eta = (sweep_elapsed / done * (total_series - done)) if done > 0 else 0
            print(f"[{done}/{total_series}] {exchange} {pair} {interval}: "
                  f"wrote {combo_written:,} across {len(gaps)} range(s) "
                  f"in {combo_elapsed:.1f}s  "
                  f"[sweep {sweep_elapsed/60:.1f}min, ETA {eta/60:.1f}min]")
            return combo_written, len(gaps), errors_here'''


def _src(cell):
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else (s or "")


def _set(cell, new_src):
    cell["source"] = new_src.splitlines(keepends=True)
    cell["outputs"] = []
    cell["execution_count"] = None


def patch_cell4(cell):
    src = _src(cell)
    if "last_heartbeat = started" in src and "requests_made = 0" in src:
        return False
    if _A_OLD not in src:
        raise AssertionError("Cell 4: old ingest_nonkyc_range not found verbatim")
    _set(cell, src.replace(_A_OLD, _A_NEW, 1))
    return True


def patch_cell11(cell):
    src = _src(cell)
    if "combo_started = time.perf_counter()" in src:
        return False
    if _B_OLD not in src:
        raise AssertionError("Cell 11: old one_combo not found verbatim")
    _set(cell, src.replace(_B_OLD, _B_NEW, 1))
    return True


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    with open(NB_PATH, encoding="utf-8") as f:
        nb = json.load(f)

    cell4_idx = cell11_idx = None
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        s = _src(c)
        if cell4_idx is None and "def ingest_nonkyc_range(" in s:
            cell4_idx = i
        if cell11_idx is None and "def one_combo(combo):" in s:
            cell11_idx = i

    if cell4_idx is None:
        raise RuntimeError("ingest_nonkyc_range cell not found")
    if cell11_idx is None:
        raise RuntimeError("one_combo cell not found")

    did_A = patch_cell4(nb["cells"][cell4_idx])
    did_B = patch_cell11(nb["cells"][cell11_idx])

    with open(NB_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)

    print(f"A) ingest_nonkyc_range heartbeat (cell {cell4_idx}): "
          f"{'updated' if did_A else 'already patched'}")
    print(f"B) one_combo timing + ETA (cell {cell11_idx}):       "
          f"{'updated' if did_B else 'already patched'}")


if __name__ == "__main__":
    main()
