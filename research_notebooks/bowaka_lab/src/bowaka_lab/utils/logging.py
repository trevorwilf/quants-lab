"""Lightweight structured logger.

Avoids external `structlog` to keep deps minimal. Emits JSON lines so logs are
machine-readable. Never logs secrets — credentials are masked when their
keys match the SECRET_KEYS pattern.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

SECRET_KEYS = frozenset(
    {
        "alpaca_api_key_id",
        "alpaca_api_secret_key",
        "mongo_uri",
        "mongo_password",
        "postgres_uri",
        "postgres_password",
        "jupyter_token",
    }
)


def _mask(d: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in d.items():
        if k.lower() in SECRET_KEYS:
            out[k] = "***"
        elif isinstance(v, dict):
            out[k] = _mask(v)
        else:
            out[k] = v
    return out


class StructuredLogger:
    def __init__(self, name: str = "bowaka_lab", *, level: int = logging.INFO):
        self._name = name
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
        self._logger.setLevel(level)

    def _emit(self, level: int, event: str, **fields: Any) -> None:
        record = {"event": event, **_mask(fields)}
        self._logger.log(level, json.dumps(record, default=str, sort_keys=True))

    def debug(self, event: str, **fields: Any) -> None:
        self._emit(logging.DEBUG, event, **fields)

    def info(self, event: str, **fields: Any) -> None:
        self._emit(logging.INFO, event, **fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._emit(logging.WARNING, event, **fields)

    def error(self, event: str, **fields: Any) -> None:
        self._emit(logging.ERROR, event, **fields)


def get_logger(name: str = "bowaka_lab") -> StructuredLogger:
    return StructuredLogger(name)
