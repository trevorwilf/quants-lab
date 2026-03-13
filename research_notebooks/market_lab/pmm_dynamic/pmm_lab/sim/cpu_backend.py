"""NumPy implementation of the ArrayBackend protocol."""

import numpy as np


class NumpyBackend:
    """CPU array backend using NumPy."""

    def asarray(self, x, dtype=None):
        return np.asarray(x, dtype=dtype)

    def zeros(self, shape, dtype=None):
        return np.zeros(shape, dtype=dtype or np.float64)

    def ones(self, shape, dtype=None):
        return np.ones(shape, dtype=dtype or np.float64)

    def empty(self, shape, dtype=None):
        return np.empty(shape, dtype=dtype or np.float64)

    def maximum(self, a, b):
        return np.maximum(a, b)

    def minimum(self, a, b):
        return np.minimum(a, b)

    def where(self, cond, x, y):
        return np.where(cond, x, y)

    def sum(self, x, axis=None):
        return np.sum(x, axis=axis)

    def mean(self, x, axis=None):
        return np.mean(x, axis=axis)

    def abs(self, x):
        return np.abs(x)

    def clip(self, x, a_min, a_max):
        return np.clip(x, a_min, a_max)
