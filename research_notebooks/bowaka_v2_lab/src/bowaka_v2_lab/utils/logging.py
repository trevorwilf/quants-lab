"""structlog-style logger factory. No secrets are ever logged."""
from __future__ import annotations

import logging
from typing import Any


_SENSITIVE_KEYS = ("api_key", "secret", "password", "token", "mongo_uri", "uri", "postgres_uri")


def _scrub(record: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in record.items():
        if any(s in k.lower() for s in _SENSITIVE_KEYS):
            out[k] = "<redacted>"
        else:
            out[k] = v
    return out


def get_logger(name: str = "bowaka_v2_lab") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger


def log_event(logger: logging.Logger, level: str, event: str, **kwargs: Any) -> None:
    payload = _scrub({"event": event, **kwargs})
    msg = " ".join(f"{k}={v}" for k, v in payload.items())
    getattr(logger, level)(msg)
