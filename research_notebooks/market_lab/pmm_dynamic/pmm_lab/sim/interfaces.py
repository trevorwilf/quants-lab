"""
Backend abstraction for GPU-ready simulation.

The ArrayBackend protocol defines the array operations used in the simulation
inner loop. The CPU backend (NumPy) is the source of truth. A future GPU
backend (CuPy/Numba) can be swapped in by implementing this protocol.
"""

from typing import Protocol, Any, Optional
import numpy as np


class ArrayBackend(Protocol):
    """Protocol for array computation backends."""
    def asarray(self, x: Any, dtype: Optional[np.dtype] = None) -> Any: ...
    def zeros(self, shape: Any, dtype: Optional[np.dtype] = None) -> Any: ...
    def ones(self, shape: Any, dtype: Optional[np.dtype] = None) -> Any: ...
    def empty(self, shape: Any, dtype: Optional[np.dtype] = None) -> Any: ...
    def maximum(self, a: Any, b: Any) -> Any: ...
    def minimum(self, a: Any, b: Any) -> Any: ...
    def where(self, cond: Any, x: Any, y: Any) -> Any: ...
    def sum(self, x: Any, axis: Optional[int] = None) -> Any: ...
    def mean(self, x: Any, axis: Optional[int] = None) -> Any: ...
    def abs(self, x: Any) -> Any: ...
    def clip(self, x: Any, a_min: Any, a_max: Any) -> Any: ...


def get_backend(name: str = "cpu") -> ArrayBackend:
    """Return the requested backend.

    Parameters
    ----------
    name : str
        "cpu" for NumPy backend, "gpu" for CuPy/Numba (future).

    Returns
    -------
    ArrayBackend

    Raises
    ------
    NotImplementedError
        If name == "gpu" (not yet implemented).
    ValueError
        If name is not recognized.
    """
    if name == "cpu":
        from pmm_lab.sim.cpu_backend import NumpyBackend
        return NumpyBackend()
    elif name == "gpu":
        raise NotImplementedError("GPU backend is not implemented in v1. Use 'cpu' backend.")
    else:
        raise ValueError(f"Unknown backend: '{name}'. Valid options: 'cpu', 'gpu'.")
