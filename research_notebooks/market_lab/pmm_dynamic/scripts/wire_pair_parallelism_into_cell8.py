"""Wire pair-level parallelism into _legacy/_build_cell8.py.

Transforms `_mr_body()` and `_ema_body()` raw-string literals:

1. `for pair_idx, pair_info in enumerate(candidates):` → `def _run_one_pair(pair_idx, pair_info):`
2. Every `_pair_bar.update(1)\\n<indent>continue` pair collapses to `<indent>return`
3. Trailing `_pair_bar.update(1)` at pair-body end (not followed by continue)
   collapses to `return`
4. Guards `_trial_bar = tqdm(...)` and the `callbacks=[...]` construction so
   per-trial progress is suppressed when PAIR_JOBS > 1
5. Adds a dispatcher right before `_pair_bar.close()` that runs pairs either
   serially (PAIR_JOBS=1) or via `ThreadPoolExecutor` (PAIR_JOBS>1)

Re-runnable: idempotent — detects whether transformation already applied.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


BUILD_CELL8 = (
    Path(__file__).resolve().parent.parent
    / "notebooks" / "direction-custom" / "_legacy" / "_build_cell8.py"
)


# NOTE: template is a plain Python string, written verbatim into the cell-8
# raw-string literal. Use SINGLE braces for runtime f-string interpolation.
# Doubling (`{{` / `}}`) would render LITERALLY in the notebook and break
# the f-strings.
_DISPATCHER_TEMPLATE = '''
if PAIR_JOBS <= 1:
    for pair_idx, pair_info in enumerate(candidates):
        try:
            _run_one_pair(pair_idx, pair_info)
        except Exception as _e:
            import traceback as _tb
            print(f"  [pair {pair_idx+1}] raised: {_e}")
            _tb.print_exc()
        _pair_bar.update(1)
else:
    from concurrent.futures import ThreadPoolExecutor as _TPE, as_completed as _as_completed
    print(f"[pair-level] Running with PAIR_JOBS={PAIR_JOBS} threads x N_JOBS={N_JOBS} Optuna subprocesses per pair.")
    with _TPE(max_workers=PAIR_JOBS) as _pool:
        _futs = {
            _pool.submit(_run_one_pair, _pidx, _pinfo): (_pidx, _pinfo)
            for _pidx, _pinfo in enumerate(candidates)
        }
        for _fut in _as_completed(_futs):
            _pidx, _pinfo = _futs[_fut]
            try:
                _fut.result()
            except Exception as _e:
                import traceback as _tb
                print(f"  [parallel] pair {_pidx+1} raised: {_e}")
                _tb.print_exc()
            _pair_bar.update(1)
'''


def _transform_body(body_src: str) -> tuple[str, dict]:
    """Apply the 5 transformations above. Returns (new_src, stats)."""
    stats = {
        "for_to_def": 0, "update_continue_pairs": 0,
        "trailing_update": 0, "trial_bar_guarded": 0,
        "callbacks_guarded": 0, "dispatcher_inserted": 0,
    }

    # 1) `for pair_idx, pair_info in enumerate(candidates):` → `def _run_one_pair(pair_idx, pair_info):`
    new = body_src
    pattern = "for pair_idx, pair_info in enumerate(candidates):"
    replacement = "def _run_one_pair(pair_idx, pair_info):"
    if pattern in new:
        count = new.count(pattern)
        new = new.replace(pattern, replacement)
        stats["for_to_def"] = count

    # 2) Every paired `_pair_bar.update(1)` + `continue` → `return`
    #    preserving indentation of the `continue`.
    new, n = re.subn(
        r"([ \t]+)_pair_bar\.update\(1\)\n[ \t]+continue\b",
        r"\1return",
        new,
    )
    stats["update_continue_pairs"] = n

    # 3) Remaining trailing `_pair_bar.update(1)` at pair-body end
    #    (after all continues removed). These are at indent 4 (one level inside
    #    the def). Replace with `return`.
    new, n = re.subn(
        r"^    _pair_bar\.update\(1\)\s*\n",
        "    return\n",
        new,
        flags=re.MULTILINE,
    )
    stats["trailing_update"] = n

    # 4) Guard the `_trial_bar = tqdm(...)` line and the `callbacks=[...]`
    #    construction so per-trial tqdm is suppressed when PAIR_JOBS > 1.
    old_trial_bar = (
        '    _trial_bar = tqdm(total=N_TRIALS, position=1, leave=False, desc="trials")\n'
        '    _trial_cb = TqdmProgressCallback(_trial_bar, show_best=True)\n'
    )
    new_trial_bar = (
        '    if PAIR_JOBS > 1:\n'
        '        _trial_bar = None\n'
        '        _trial_cb = None\n'
        '    else:\n'
        '        _trial_bar = tqdm(total=N_TRIALS, position=1, leave=False, desc="trials")\n'
        '        _trial_cb = TqdmProgressCallback(_trial_bar, show_best=True)\n'
    )
    if old_trial_bar in new:
        count = new.count(old_trial_bar)
        new = new.replace(old_trial_bar, new_trial_bar)
        stats["trial_bar_guarded"] = count

    # Callbacks list: inject conditional use of _trial_cb
    old_callbacks = "callbacks=[DegeneracyCheckCallback(), _trial_cb],"
    new_callbacks = (
        "callbacks=([DegeneracyCheckCallback(), _trial_cb] "
        "if _trial_cb is not None else [DegeneracyCheckCallback()]),"
    )
    if old_callbacks in new:
        count = new.count(old_callbacks)
        new = new.replace(old_callbacks, new_callbacks)
        stats["callbacks_guarded"] = count

    # Also guard the `_trial_bar.close()` finally-block to allow None
    old_close = "try:\n            _trial_bar.close()\n        except Exception:\n            pass"
    new_close = (
        "try:\n"
        "            if _trial_bar is not None:\n"
        "                _trial_bar.close()\n"
        "        except Exception:\n"
        "            pass"
    )
    if old_close in new:
        new = new.replace(old_close, new_close)

    # 5) Add the dispatcher just before `_pair_bar.close()`
    close_marker = "_pair_bar.close()"
    if close_marker in new and "_run_one_pair" in new and "if PAIR_JOBS <= 1:" not in new:
        new = new.replace(close_marker, _DISPATCHER_TEMPLATE.strip("\n") + "\n\n" + close_marker, 1)
        stats["dispatcher_inserted"] = 1

    return new, stats


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    src = BUILD_CELL8.read_text(encoding="utf-8")

    # Locate each raw-string body and transform it individually so the
    # helper-function boilerplate (def _mr_body(): return r'''...''')
    # remains untouched.
    total_stats = {
        "for_to_def": 0, "update_continue_pairs": 0,
        "trailing_update": 0, "trial_bar_guarded": 0,
        "callbacks_guarded": 0, "dispatcher_inserted": 0,
    }

    # Use a non-greedy match across the entire file, per body.
    pat = re.compile(
        r"(def (?:_mr_body|_ema_body)\(\):\n    return r'''\n?)(.*?)('''\n)",
        re.DOTALL,
    )
    matches = list(pat.finditer(src))
    if not matches:
        raise RuntimeError("Could not locate _mr_body / _ema_body raw-string blocks")

    # Build new src by replacing each match's body
    out_parts: list[str] = []
    last = 0
    for m in matches:
        out_parts.append(src[last:m.start()])
        head, body, tail = m.group(1), m.group(2), m.group(3)
        new_body, stats = _transform_body(body)
        for k, v in stats.items():
            total_stats[k] = total_stats[k] + v
        out_parts.append(head)
        out_parts.append(new_body)
        out_parts.append(tail)
        last = m.end()
    out_parts.append(src[last:])

    new_src = "".join(out_parts)
    BUILD_CELL8.write_text(new_src, encoding="utf-8")
    print(f"wrote {BUILD_CELL8}")
    for k, v in total_stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
