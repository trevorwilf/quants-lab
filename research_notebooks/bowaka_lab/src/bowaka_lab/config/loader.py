"""YAML config loader with `${VAR}` and `${VAR:-default}` substitution.

Rules:

- Unknown top-level keys are rejected by Pydantic `extra="forbid"`.
- `${VAR}` substitutes `os.environ["VAR"]`, raising `KeyError` if missing.
- `${VAR:-default}` substitutes `os.environ.get("VAR", "default")`.
- Substitution applies to all string leaves recursively.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from bowaka_lab.config.models import BowakaBacktestConfig

_PATTERN_DEFAULT = re.compile(r"\$\{([A-Za-z_][A-Za-z_0-9]*):-([^}]*)\}")
_PATTERN_REQUIRED = re.compile(r"\$\{([A-Za-z_][A-Za-z_0-9]*)\}")


def substitute_env(value: Any, env: dict[str, str] | None = None) -> Any:
    """Walk a nested config tree, substituting `${VAR}` placeholders."""
    if env is None:
        env = os.environ  # type: ignore[assignment]

    if isinstance(value, str):
        def replace_default(m: re.Match) -> str:
            return env.get(m.group(1), m.group(2))

        out = _PATTERN_DEFAULT.sub(replace_default, value)

        def replace_required(m: re.Match) -> str:
            var = m.group(1)
            if var not in env or env[var] == "":
                raise KeyError(f"Required env var {var!r} is not set")
            return env[var]

        out = _PATTERN_REQUIRED.sub(replace_required, out)
        return out

    if isinstance(value, dict):
        return {k: substitute_env(v, env) for k, v in value.items()}

    if isinstance(value, list):
        return [substitute_env(v, env) for v in value]

    return value


def load_yaml(path: Path | str) -> dict[str, Any]:
    """Parse a YAML file with env substitution applied."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    raw = yaml.safe_load(text) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"top-level YAML in {path} must be a mapping, got {type(raw).__name__}")
    return substitute_env(raw)


def load_config_file(path: Path | str) -> BowakaBacktestConfig:
    """Load and validate a Bowaka backtest config YAML.

    Raises ValidationError if any unknown top-level keys are present.
    """
    data = load_yaml(path)
    return BowakaBacktestConfig.model_validate(data)
