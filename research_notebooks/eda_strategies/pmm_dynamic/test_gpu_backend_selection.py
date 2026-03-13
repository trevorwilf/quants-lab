"""Minimal regression test: GPU backend selection should default to Numba.

Why this exists
---------------
We observed CPU/GPU parity failures on some machines when CuPy is installed but
its CUDA context is not compatible with Numba's CUDA context. The safest default
is to use Numba device arrays for allocation/transfer, and only use CuPy when
explicitly requested.

This test:
  1) Injects a lightweight dummy 'cupy' module so that 'import cupy as cp' succeeds
     even on machines without CuPy installed.
  2) Forces NUMBA_ENABLE_CUDASIM=1 so the GPU module can import and report a backend.
  3) Verifies:
       - default backend is 'numba' (even though cupy import succeeded)
       - backend switches to 'cupy' when PMM_DYNAMIC_GPU_BACKEND='cupy'

Run:
  NUMBA_ENABLE_CUDASIM=1 python pmm_dynamic/test_gpu_backend_selection.py
"""

from __future__ import annotations

import importlib
import os
import sys
import types

import numpy as np


def _install_dummy_cupy():
    if "cupy" in sys.modules:
        return

    dummy = types.ModuleType("cupy")

    # Minimal subset used by pmm_dynamic_optimizer_gpu.py
    dummy.ndarray = np.ndarray
    dummy.asarray = lambda x: np.asarray(x)
    dummy.asnumpy = lambda x: np.asarray(x)
    dummy.zeros = lambda shape, dtype=None: np.zeros(shape, dtype=dtype)
    dummy.full = lambda shape, fill_value, dtype=None: np.full(shape, fill_value, dtype=dtype)

    sys.modules["cupy"] = dummy


def main() -> int:
    # Force CUDASIM so cuda.is_available() is True without a real GPU.
    os.environ["NUMBA_ENABLE_CUDASIM"] = "1"

    # Ensure importing cupy succeeds (real CuPy or dummy).
    _install_dummy_cupy()

    # Import from repo-local module path.
    sys.path.insert(0, os.path.dirname(__file__))

    # Case 1: default backend should be numba (even with cupy importable)
    os.environ.pop("PMM_DYNAMIC_GPU_BACKEND", None)

    import pmm_dynamic_optimizer_gpu as m  # type: ignore

    backend = m.get_gpu_backend()
    assert backend == "numba", f"Expected default backend 'numba', got {backend!r}"

    # Case 2: explicit cupy backend should be honored
    os.environ["PMM_DYNAMIC_GPU_BACKEND"] = "cupy"
    m = importlib.reload(m)

    backend2 = m.get_gpu_backend()
    assert backend2 == "cupy", f"Expected backend 'cupy' when requested, got {backend2!r}"

    print("OK: backend selection works (default=numba, requested=cupy)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
