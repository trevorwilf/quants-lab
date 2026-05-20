"""YAML loader for bowaka_v2_lab configs.

- Expands ``${VAR}`` and ``${VAR:-default}`` references from ``os.environ``.
- Rejects unknown top-level keys against an allow-list.
- Returns a plain ``dict`` (Pydantic validation happens separately in ``models``).
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Mapping

import yaml


# Allow-list of top-level keys. Anything else raises ``ValueError``.
ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {
        "strategy_id",
        "strategy_version",
        "market_data",
        "session",
        "universe",
        "scanner",
        "signals",
        "execution",
        "sizing",
        "risk",
        "exits",
        "backtest",
        "artifacts",
        "run",
        "paths",
        "optuna",
        "reconcile",
        "promotion",
    }
)


_VAR_PATTERN = re.compile(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::-(?P<default>[^}]*))?\}")


def _expand_env_in_str(value: str) -> str:
    def _sub(match: re.Match) -> str:
        name = match.group("name")
        default = match.group("default")
        env_value = os.environ.get(name)
        if env_value is not None:
            return env_value
        if default is not None:
            return default
        # Leave the placeholder verbatim so downstream validation catches the miss.
        return match.group(0)

    return _VAR_PATTERN.sub(_sub, value)


def _expand_env(node: Any) -> Any:
    if isinstance(node, str):
        return _expand_env_in_str(node)
    if isinstance(node, list):
        return [_expand_env(x) for x in node]
    if isinstance(node, dict):
        return {k: _expand_env(v) for k, v in node.items()}
    return node


def load_config(path: str | Path) -> dict[str, Any]:
    """Load and pre-process a v2 lab YAML config.

    Returns a plain ``dict`` with env vars expanded and unknown top-level keys rejected.
    Attaches the source path under ``_source_path`` for path-resolution and reporting.
    """
    cfg_path = Path(path)
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"config at {cfg_path} did not parse to a mapping (got {type(raw).__name__})")
    expanded = _expand_env(raw)
    unknown = set(expanded.keys()) - ALLOWED_TOP_LEVEL_KEYS
    if unknown:
        raise ValueError(
            f"unknown top-level keys in {cfg_path}: {sorted(unknown)}; "
            f"allowed: {sorted(ALLOWED_TOP_LEVEL_KEYS)}"
        )
    expanded["_source_path"] = str(cfg_path)
    return expanded
