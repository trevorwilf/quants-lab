"""Lightweight Optuna/objective profiling counters (speedup report §10.0, §11.1).

Phase 0 only adds counters; they are no-ops by default (zero cost) and exist so
later phases (cached suppliers, fold context, parallel workers, matrix
precompute) can be benchmarked against a fixed baseline.

The counters live behind a process-level boolean flag (default ``False``) and a
``ContextVar`` binding the currently-active :class:`ProfileCounters` instance.
Increment sites use the form::

    if _COUNTERS_ENABLED:
        try:
            current_profile_counters().inc(minute_supplier_calls=1)
        except LookupError:
            pass

The ``LookupError`` swallow keeps the increment fail-safe outside a context
(e.g. an ad-hoc Python REPL session).
"""
from __future__ import annotations

import contextlib
import contextvars
from dataclasses import asdict, dataclass, field, fields
from typing import Any, Iterator


_COUNTERS_ENABLED: bool = False


def set_counters_enabled(value: bool) -> None:
    """Toggle the process-level counters flag.

    Default ``False`` — increments are skipped without entering the
    ``ContextVar`` lookup. Returning to ``False`` does not delete the active
    instance; it only stops the cheap fast-path increments at call sites.
    """
    global _COUNTERS_ENABLED
    _COUNTERS_ENABLED = bool(value)


def counters_enabled() -> bool:
    return _COUNTERS_ENABLED


@dataclass
class ProfileCounters:
    """Mutable counter bag for one profiling pass (single thread / process).

    Integer-typed fields default to zero; float-typed timing fields default to
    0.0 (cumulative seconds across the bound context). Use :meth:`inc` to
    bump fields by keyword. :meth:`snapshot` returns a plain dict suitable for
    JSON dumps.
    """

    minute_supplier_calls: int = 0
    minute_parquet_reads: int = 0
    quote_supplier_calls: int = 0
    quote_parquet_reads: int = 0
    daily_cache_builds: int = 0
    event_count_processed: int = 0
    gate_dump_rows_constructed: int = 0
    artifact_bytes_written: int = 0
    # Speedup report v2 §5.3 / §5.8 / Phase 1 — batch-daily-cache counters.
    # Increments are gated by the existing ``_COUNTERS_ENABLED`` flag (no-op
    # when off); each parquet read of a symbol's full daily history under
    # the batch path bumps ``daily_parquet_reads`` exactly once vs.
    # ``unique_symbols * sessions`` under the legacy per-session path.
    daily_parquet_reads: int = 0
    daily_cache_symbols: int = 0
    daily_cache_sessions: int = 0
    daily_cache_batch_load_seconds: float = 0.0
    daily_cache_batch_slice_seconds: float = 0.0
    fold_context_build_seconds: float = 0.0
    worker_context_build_seconds: float = 0.0
    # Speedup report v2 §5.4 / Phase 2 — parallel preflight wall-clock.
    parallel_preflight_seconds: float = 0.0
    # Speedup report v2 §5.6 / Phase 3 — invariant startup DQ cache counters.
    startup_dq_builds: int = 0
    startup_dq_cached_hits: int = 0

    extra: dict[str, Any] = field(default_factory=dict)

    def inc(self, **kwargs: Any) -> None:
        for name, delta in kwargs.items():
            if hasattr(self, name) and name != "extra":
                current = getattr(self, name)
                if isinstance(current, float):
                    setattr(self, name, float(current) + float(delta))
                else:
                    setattr(self, name, int(current) + int(delta))
            else:
                cur = self.extra.get(name, 0)
                if isinstance(delta, float) or isinstance(cur, float):
                    self.extra[name] = float(cur) + float(delta)
                else:
                    self.extra[name] = int(cur) + int(delta)

    def reset(self) -> None:
        for f in fields(self):
            if f.name == "extra":
                self.extra.clear()
            elif f.type == "float" or isinstance(getattr(self, f.name), float):
                setattr(self, f.name, 0.0)
            else:
                setattr(self, f.name, 0)

    def snapshot(self) -> dict[str, Any]:
        out = {k: v for k, v in asdict(self).items() if k != "extra"}
        out.update(self.extra)
        return out


_CURRENT: contextvars.ContextVar[ProfileCounters] = contextvars.ContextVar(
    "bowaka_v2_lab.profile_counters.current",
)


def current_profile_counters() -> ProfileCounters:
    """Return the active :class:`ProfileCounters`.

    Raises :class:`LookupError` if no instance is bound — call sites guard this
    so cheap incrementing without an active context is a no-op.
    """
    return _CURRENT.get()


@contextlib.contextmanager
def profile_counters_context(
    counters: ProfileCounters | None = None,
    *,
    enable: bool = True,
) -> Iterator[ProfileCounters]:
    """Bind a fresh (or supplied) :class:`ProfileCounters` for the ``with``-block.

    ``enable`` flips :func:`set_counters_enabled` for the duration of the
    block. The previous flag value is restored on exit. The previously-bound
    counters instance (if any) is restored after the block too.
    """
    if counters is None:
        counters = ProfileCounters()
    token = _CURRENT.set(counters)
    prev_flag = counters_enabled()
    set_counters_enabled(enable)
    try:
        yield counters
    finally:
        set_counters_enabled(prev_flag)
        _CURRENT.reset(token)


__all__ = [
    "ProfileCounters",
    "counters_enabled",
    "current_profile_counters",
    "profile_counters_context",
    "set_counters_enabled",
]
