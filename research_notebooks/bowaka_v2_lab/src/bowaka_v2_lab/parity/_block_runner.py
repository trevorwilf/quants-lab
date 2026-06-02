"""Phase 3 — parallel parity block runner (subprocess entrypoint).

Run as ``python -m bowaka_v2_lab.parity._block_runner <spec.pkl> <out.pkl>``.

The parallel parity launcher runs ONE of these per contiguous session block.
Using a real importable module launched as a subprocess (rather than a
``multiprocessing`` spawn worker) sidesteps the Windows/Jupyter spawn limitation
where the child cannot re-import an interactive / ``<stdin>`` ``__main__`` — so
``run_parity(parallel_workers=N)`` works from a notebook kernel, papermill, the
CLI, and plain scripts alike.

BLAS threads are pinned to 1 BEFORE any numpy import (also set in the parent's
env; belt-and-suspenders here).
"""
from __future__ import annotations

import os

for _v in (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_v, "1")

import pickle  # noqa: E402
import sys  # noqa: E402
import traceback  # noqa: E402


def main() -> int:
    spec_path, out_path = sys.argv[1], sys.argv[2]
    with open(spec_path, "rb") as fh:
        spec = pickle.load(fh)
    from bowaka_v2_lab.parity.runner import _run_parity_session_block

    try:
        results = _run_parity_session_block(spec)
        payload = {"ok": True, "results": results, "error": None}
    except Exception as exc:  # noqa: BLE001 — reported back to the parent
        payload = {
            "ok": False, "results": None,
            "error": f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
        }
    with open(out_path, "wb") as fh:
        pickle.dump(payload, fh)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
