"""Skip last N days for existing pairs in candle_backfill_v3.ipynb.

Five edits:
  A) candle_backfill_config.yaml — add recent_days_owned_by_other_process: 30
  B) Cell 1 — load RECENT_DAYS_OWNED, print the new setting
  C) Cell 8 — reorder so effective_end is computed before the count query,
     clamp effective_end by recent_cutoff, add "$lte" to count query, add
     "window_end" field to combos.append
  D) Cell 9 — add "window_end" field to NEW_PAIRS combo (full window)
  E) Cell 11 — retrieve win_end from combo, use it in both is_new and
     existing-pair branches

Idempotent: each step checks for its own marker before mutating.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB_PATH = ROOT / "notebooks" / "mongo_tools" / "candle_backfill_v3.ipynb"
YAML_PATH = ROOT / "notebooks" / "mongo_tools" / "candle_backfill_config.yaml"


# ── A) YAML ────────────────────────────────────────────────────────────────
_YAML_OLD = """# Absolute ceiling regardless of any per-interval target. 10 years in days.
absolute_max_days: 3650

# Exchange definitions."""

_YAML_NEW = """# Absolute ceiling regardless of any per-interval target. 10 years in days.
absolute_max_days: 3650

# Skip the most-recent N days when backfilling pairs that already
# exist in the database. Intended for coordination with a separate
# "live" backfill process that handles the recent window. Set to 0
# to disable (backfill all the way to now, which is the legacy behavior).
# New pairs (via Cell 9's NEW_PAIRS list) always backfill fully to now
# regardless of this value.
recent_days_owned_by_other_process: 30

# Exchange definitions."""


# ── B) Cell 1 ──────────────────────────────────────────────────────────────
_C1_LOAD_OLD = 'ABSOLUTE_MAX_DAYS     = CFG["absolute_max_days"]'
_C1_LOAD_NEW = ('ABSOLUTE_MAX_DAYS     = CFG["absolute_max_days"]\n'
                'RECENT_DAYS_OWNED = int(CFG.get("recent_days_owned_by_other_process", 0))')

_C1_PRINT_OLD = 'print(f"Absolute max lookback: {ABSOLUTE_MAX_DAYS} days ({ABSOLUTE_MAX_DAYS / 365:.1f} years)")'
_C1_PRINT_NEW = ('print(f"Absolute max lookback: {ABSOLUTE_MAX_DAYS} days ({ABSOLUTE_MAX_DAYS / 365:.1f} years)")\n'
                 'print(f"Skipping last {RECENT_DAYS_OWNED} days for existing pairs (0 = disabled)")')


# ── C) Cell 8 ──────────────────────────────────────────────────────────────
# Full reorder: move effective_start/effective_end/recent_cutoff ahead of
# the count_documents query so the query can clamp with $lte.
_C8_BLOCK_OLD = '''    candles_in_window = coll.count_documents({
        "connector": connector, "trading_pair": pair, "interval": interval,
        "timestamp": {"$gte": window_start},
    })

    effective_start = align_floor(window_start, step)
    effective_end   = last_closed_open_ts(now_ts, step)
    expected = ((effective_end - effective_start) // step) + 1 if effective_end >= effective_start else 0
    missing  = max(0, expected - candles_in_window)
    pct      = (candles_in_window / expected * 100) if expected > 0 else 100.0'''

_C8_BLOCK_NEW = '''    effective_start = align_floor(window_start, step)
    # Skip the recent window if configured — another process owns it.
    # Existing pairs get this clamp; new pairs (Cell 9) do not.
    recent_cutoff = now_ts - (RECENT_DAYS_OWNED * 86400) if RECENT_DAYS_OWNED > 0 else now_ts
    effective_end   = min(last_closed_open_ts(now_ts, step),
                           last_closed_open_ts(recent_cutoff, step))
    expected = ((effective_end - effective_start) // step) + 1 if effective_end >= effective_start else 0

    candles_in_window = coll.count_documents({
        "connector": connector, "trading_pair": pair, "interval": interval,
        "timestamp": {"$gte": window_start, "$lte": effective_end},
    })

    missing  = max(0, expected - candles_in_window)
    pct      = (candles_in_window / expected * 100) if expected > 0 else 100.0'''

_C8_APPEND_OLD = '''    combos.append({
        "connector": connector,
        "pair": pair,
        "interval": interval,
        "total_docs": int(doc["count"]),
        "in_window": candles_in_window,
        "expected": expected,
        "missing": missing,
        "pct": pct,
        "step": step,
        "window_start": window_start,
    })'''

_C8_APPEND_NEW = '''    combos.append({
        "connector": connector,
        "pair": pair,
        "interval": interval,
        "total_docs": int(doc["count"]),
        "in_window": candles_in_window,
        "expected": expected,
        "missing": missing,
        "pct": pct,
        "step": step,
        "window_start": window_start,
        "window_end": effective_end,
    })'''


# ── D) Cell 9 ──────────────────────────────────────────────────────────────
_C9_APPEND_OLD = '''selected_combos.append({
            "connector": nconn, "pair": npair, "interval": interval,
            "total_docs": 0, "in_window": 0, "expected": expected,
            "missing": expected, "pct": 0.0, "step": step,
            "window_start": window_start, "is_new_pair": True,
        })'''

_C9_APPEND_NEW = '''selected_combos.append({
            "connector": nconn, "pair": npair, "interval": interval,
            "total_docs": 0, "in_window": 0, "expected": expected,
            "missing": expected, "pct": 0.0, "step": step,
            "window_start": window_start,
            "window_end": effective_end,
            "is_new_pair": True,
        })'''


# ── E) Cell 11 ─────────────────────────────────────────────────────────────
_C11_WINSTART_OLD = '            win_start = combo["window_start"]\n'
_C11_WINSTART_NEW = (
    '            win_start = combo["window_start"]\n'
    '            win_end = combo.get("window_end", last_closed_open_ts(utc_now_ts(), step))\n'
)

_C11_ISNEW_OLD = '                eff_end = last_closed_open_ts(utc_now_ts(), step)\n'
_C11_ISNEW_NEW = '                eff_end = win_end\n'

_C11_FINDGAPS_OLD = (
    '                gaps = find_gaps_in_window(coll, exchange, pair, interval, step,\n'
    '                                            win_start, utc_now_ts())\n'
)
_C11_FINDGAPS_NEW = (
    '                gaps = find_gaps_in_window(coll, exchange, pair, interval, step,\n'
    '                                            win_start, win_end)\n'
)


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
    if "recent_days_owned_by_other_process" in text:
        return False
    if _YAML_OLD not in text:
        raise AssertionError("YAML: expected anchor (absolute_max_days → Exchange definitions) not found")
    YAML_PATH.write_text(text.replace(_YAML_OLD, _YAML_NEW, 1), encoding="utf-8")
    return True


def patch_cell1(cell):
    src = _src(cell)
    changed = False

    if "RECENT_DAYS_OWNED = int(CFG.get" not in src:
        if _C1_LOAD_OLD not in src:
            raise AssertionError("Cell 1: ABSOLUTE_MAX_DAYS anchor not found")
        src = src.replace(_C1_LOAD_OLD, _C1_LOAD_NEW, 1)
        changed = True

    if "Skipping last" not in src:
        if _C1_PRINT_OLD not in src:
            raise AssertionError("Cell 1: 'Absolute max lookback' print anchor not found")
        src = src.replace(_C1_PRINT_OLD, _C1_PRINT_NEW, 1)
        changed = True

    if changed:
        _set(cell, src)
    return changed


def patch_cell8(cell):
    src = _src(cell)
    changed = False

    if "recent_cutoff = now_ts - (RECENT_DAYS_OWNED" not in src:
        if _C8_BLOCK_OLD not in src:
            raise AssertionError("Cell 8: effective_start/end block not found verbatim")
        src = src.replace(_C8_BLOCK_OLD, _C8_BLOCK_NEW, 1)
        changed = True

    if '"window_end": effective_end,\n    })' not in src:
        if _C8_APPEND_OLD not in src:
            raise AssertionError("Cell 8: combos.append block not found verbatim")
        src = src.replace(_C8_APPEND_OLD, _C8_APPEND_NEW, 1)
        changed = True

    if changed:
        _set(cell, src)
    return changed


def patch_cell9(cell):
    src = _src(cell)
    if '"window_end": effective_end,' in src:
        return False
    if _C9_APPEND_OLD not in src:
        raise AssertionError("Cell 9: selected_combos.append block not found verbatim")
    _set(cell, src.replace(_C9_APPEND_OLD, _C9_APPEND_NEW, 1))
    return True


def patch_cell11(cell):
    src = _src(cell)
    changed = False

    if 'win_end = combo.get("window_end"' not in src:
        if _C11_WINSTART_OLD not in src:
            raise AssertionError("Cell 11: win_start anchor not found")
        src = src.replace(_C11_WINSTART_OLD, _C11_WINSTART_NEW, 1)
        changed = True

    if "eff_end = win_end\n" not in src:
        if _C11_ISNEW_OLD not in src:
            raise AssertionError("Cell 11: is_new eff_end anchor not found")
        src = src.replace(_C11_ISNEW_OLD, _C11_ISNEW_NEW, 1)
        changed = True

    if "win_start, win_end)" not in src:
        if _C11_FINDGAPS_OLD not in src:
            raise AssertionError("Cell 11: find_gaps_in_window anchor not found")
        src = src.replace(_C11_FINDGAPS_OLD, _C11_FINDGAPS_NEW, 1)
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

    # Locate cells by distinctive content
    idx = {"c1": None, "c8": None, "c9": None, "c11": None}
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        s = _src(c)
        if idx["c1"] is None and "ABSOLUTE_MAX_DAYS" in s and "CFG[" in s:
            idx["c1"] = i
        if idx["c8"] is None and "# ── Cell 8:" in s:
            idx["c8"] = i
        if idx["c9"] is None and "# ── Cell 9:" in s:
            idx["c9"] = i
        if idx["c11"] is None and "def one_combo(combo):" in s:
            idx["c11"] = i

    for k, v in idx.items():
        if v is None:
            raise RuntimeError(f"{k} cell not found")

    did = {}
    did["c1"] = patch_cell1(nb["cells"][idx["c1"]])
    did["c8"] = patch_cell8(nb["cells"][idx["c8"]])
    did["c9"] = patch_cell9(nb["cells"][idx["c9"]])
    did["c11"] = patch_cell11(nb["cells"][idx["c11"]])

    with open(NB_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)

    print(f"A) YAML recent_days_owned_by_other_process:          "
          f"{'updated' if did_yaml else 'already patched'}")
    print(f"B) Cell {idx['c1']} RECENT_DAYS_OWNED + print:                    "
          f"{'updated' if did['c1'] else 'already patched'}")
    print(f"C) Cell {idx['c8']} reorder + $lte + window_end:                  "
          f"{'updated' if did['c8'] else 'already patched'}")
    print(f"D) Cell {idx['c9']} new-pair window_end:                          "
          f"{'updated' if did['c9'] else 'already patched'}")
    print(f"E) Cell {idx['c11']} win_end retrieval + replace utc_now_ts:       "
          f"{'updated' if did['c11'] else 'already patched'}")


if __name__ == "__main__":
    main()
