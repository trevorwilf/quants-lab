"""Is a bowaka_v2 study / finalist-sweep actively computing in this container?

Used by scheduled_weekly_refresh.ps1 as the GUARD: a lake refresh OR a scan-matrix
rebuild while a walk-forward study (or the Top-N finalist sweep) is running can
corrupt it -- the study reads the lake directly per-fold and reads the matrix
store, and the whole-lake dataset_hash drifts on any lake change. So the whole
weekly run is deferred while one is active.

Detection is PROCESS-BASED and timezone-independent (a wall-clock "recent trial"
approach had a TZ bug and missed the context-build + finalist-sweep phases). A
study/sweep always has heavy python worker processes:
  - process_parallel optimization workers (spawned fresh; each climbs to ~7-9 GB),
  - the per-fold context build,
  - the Top-N finalist-sweep workers (scripts/topn_robustness_sweep.py).
Idle, the only python is the ~0.2-0.8 GB Jupyter kernel / lab. Detection uses TWO
RSS bands so the brief sub-1.5 GB worker STARTUP ramp is still caught:
  - any python proc > 1.5 GB                        (steady-state worker), OR
  - >= 4 python procs each > 0.5 GB                 (16-worker startup ramp), OR
  - a topn_robustness_sweep process                 (finalist sweep, by name).

Erring toward ACTIVE is the safe direction: a false ACTIVE only defers a refresh
(next week re-covers via -LookbackDays); a false IDLE could clobber a live study.
On ANY inspection failure we return ACTIVE (0) so the wrapper defers.

Exit codes:  0 = ACTIVE (defer / skip)    1 = IDLE (safe to refresh+rebuild)
The wrapper requires BOTH rc==1 AND the literal '-> IDLE' line before proceeding.
"""
from __future__ import annotations

import subprocess
import sys

BIG_KB = 1_572_864   # 1.5 GB -> a single one means a worker at steady state
MID_KB = 524_288     # 0.5 GB -> >=4 of these means a multi-worker startup ramp
MID_COUNT = 4
_SELF = "check_study_active"


def main() -> int:
    try:
        out = subprocess.run(
            ["ps", "-eo", "rss,args"], capture_output=True, text=True, check=True
        ).stdout
    except Exception as exc:  # noqa: BLE001 — cannot inspect -> assume ACTIVE (safe)
        print(f"PS_ERROR: {exc} -> ACTIVE (fail-safe)")
        return 0

    big = 0
    mid = 0
    sweep = False
    for line in out.splitlines()[1:]:
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        try:
            rss = int(parts[0])
        except ValueError:
            continue
        args = parts[1]
        if _SELF in args:  # never count this probe itself
            continue
        if "python" in args.lower():
            if rss > BIG_KB:
                big += 1
            if rss > MID_KB:
                mid += 1
        if "topn_robustness_sweep" in args:
            sweep = True

    active = big >= 1 or mid >= MID_COUNT or sweep
    print(f"big_gt1.5gb={big} mid_gt0.5gb={mid} topn_sweep={sweep} -> "
          f"{'ACTIVE' if active else 'IDLE'}")
    return 0 if active else 1


if __name__ == "__main__":
    sys.exit(main())
