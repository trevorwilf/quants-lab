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
        "simulation",
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
        # Speedup report v2 §1.4 / Phase 5 — staged finalist evaluation knobs.
        "finalist_evaluation",
        # Audit 2026-05-29 §5.4 / Phase 1 — full-fold preflight knobs
        # (e.g. ``preflight.min_pit_universe_per_fold``).
        "preflight",
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


def _assert_not_quarantined(cfg_path: Path) -> None:
    """Refuse a config that lives under a ``quarantined/`` directory.

    Quarantined configs (realism audit §P0-001) are unsafe to run — they claim a
    ``simulation.mode`` they do not honor or diverge from the frozen contract.
    The standard loader is the hard gate: a quarantined path can never reach the
    backtester / Optuna runner / CLI. See ``configs/quarantined/README.md``.
    """
    parts = {p.lower() for p in cfg_path.resolve().parts}
    if "quarantined" in parts:
        raise ValueError(
            f"refusing to load quarantined config {cfg_path}: it lives under a "
            f"`quarantined/` directory. Quarantined configs are not valid for any "
            f"backtest / optimization / promotion run — see "
            f"configs/quarantined/README.md and "
            f"docs/audits/2026-05-22_realism_audit.md §P0-001."
        )


def load_config(path: str | Path) -> dict[str, Any]:
    """Load and pre-process a v2 lab YAML config.

    Returns a plain ``dict`` with env vars expanded and unknown top-level keys rejected.
    Attaches the source path under ``_source_path`` for path-resolution and reporting.

    Raises ``ValueError`` if the config lives under a ``quarantined/`` directory.
    """
    cfg_path = Path(path)
    _assert_not_quarantined(cfg_path)
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
    # Audit 2026-05-23 §P1-003 — ``same_symbol_entries_per_day`` lives under
    # ``scanner:`` (it is a candidate-gating field per the live contract).
    # A config that sets it under both ``scanner`` and ``risk`` is ambiguous
    # — the runtime would otherwise honor whichever the consumer happens to
    # read; reject up-front instead of letting the mismatch silently shape a
    # trial's behavior.
    _assert_same_symbol_entries_unambiguous(expanded, cfg_path=cfg_path)
    expanded["_source_path"] = str(cfg_path)
    return expanded


def _assert_same_symbol_entries_unambiguous(
    cfg: Mapping[str, Any], *, cfg_path: Path
) -> None:
    """Refuse a config that sets ``same_symbol_entries_per_day`` in both blocks.

    Audit 2026-05-23 §P1-003. The live contract treats this as a scanner
    field; the lab schema now models it on :class:`ScannerConfig`. A legacy
    config that still sets it under ``risk`` is rejected with a clear
    pointer to the canonical location.
    """
    from ..optuna.errors import ConfigParityError

    scanner = cfg.get("scanner") or {}
    risk = cfg.get("risk") or {}
    if (
        isinstance(scanner, dict)
        and isinstance(risk, dict)
        and "same_symbol_entries_per_day" in scanner
        and "same_symbol_entries_per_day" in risk
    ):
        raise ConfigParityError(
            f"config {cfg_path} sets ``same_symbol_entries_per_day`` under BOTH "
            f"``scanner`` and ``risk``. The live contract treats this as a "
            f"scanner field — drop the risk entry. See "
            f"docs/audits/2026-05-23_realism_audit.md §P1-003."
        )
