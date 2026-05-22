"""Frozen contract for the live Bowaka v2 strategy.

``actual_bowaka_v2_contract.yaml`` (in the lab's ``reference/`` directory) is a
machine-readable snapshot of the live strategy config
(``${BOWAKA_V2_SOURCE_ROOT}/bowaka_v2_config.yaml``), pinned at the 2026-05-21
realism remediation. The lab simulator must reproduce this contract; Phase 1's
config-parity diff and the ``tests/parity/`` suite are checked against it.

The live source is **read-only** and is never edited by the lab. Resolution
order for its location (see :func:`resolve_source_root`):

1. ``$BOWAKA_V2_SOURCE_ROOT`` — may point either *at* the ``scripts/`` directory
   or at its parent;
2. the in-repo fallback ``reference/source_strategy/scripts`` (a local,
   git-ignored mirror — populate it with ``mirror_bowaka_v2_source.ps1``).

When neither resolves, parity tests xfail with a clear reason rather than
fabricate values.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Optional

import yaml

#: The lab's ``reference/`` directory (sibling of ``src/``).
REFERENCE_DIR = Path(__file__).resolve().parents[3] / "reference"
#: The frozen machine-readable contract (committed; the durable parity anchor).
ACTUAL_CONTRACT_PATH = REFERENCE_DIR / "actual_bowaka_v2_contract.yaml"

#: Live-config sections pinned verbatim into the contract (audit §11 Phase 0).
#: ``data`` added in realism remediation 2 Phase 1 (audit §P0-005): the live
#: ``data:`` block carries ``require_adjusted_daily_bars`` /
#: ``require_split_adjustment`` / ``max_bar_age_seconds`` / ``max_quote_age_seconds``,
#: which the contract->config mapper threads into ``market_data.*``.
CONTRACT_SECTIONS: tuple[str, ...] = (
    "data",
    "session",
    "universe",
    "historical_features",
    "scanner",
    "signals",
    "score",
    "execution",
    "sizing",
    "risk",
    "exits",
)
#: Contract schema version — bump whenever :data:`CONTRACT_SECTIONS` changes.
#: v2: realism remediation 2 Phase 1 added the ``data`` section.
CONTRACT_SCHEMA_VERSION = 2

#: Basename of the live strategy config.
_LIVE_CONFIG_NAME = "bowaka_v2_config.yaml"


def resolve_source_root() -> Optional[Path]:
    """Resolve the live-strategy source directory, or ``None`` if unavailable.

    Tolerates a ``$BOWAKA_V2_SOURCE_ROOT`` that points at a path which does not
    exist on the current host (e.g. a Windows path seen from inside a Linux
    container) — such candidates are skipped and the in-repo mirror is used.
    """
    candidates: list[Path] = []
    env = os.environ.get("BOWAKA_V2_SOURCE_ROOT")
    if env:
        candidates.append(Path(env))
    candidates.append(REFERENCE_DIR / "source_strategy" / "scripts")
    for cand in candidates:
        try:
            if cand.is_dir():
                return cand
        except OSError:
            continue
    return None


def source_file(name: str) -> Optional[Path]:
    """Absolute path to a named live source file, or ``None`` if unavailable.

    Looks under the resolved source root and, defensively, a ``scripts/``
    subdirectory of it (covers ``$BOWAKA_V2_SOURCE_ROOT`` pointing at the parent
    of ``scripts/``).
    """
    root = resolve_source_root()
    if root is None:
        return None
    for cand in (root / name, root / "scripts" / name):
        try:
            if cand.is_file():
                return cand
        except OSError:
            continue
    return None


def source_config_path() -> Optional[Path]:
    """Absolute path to the live ``bowaka_v2_config.yaml``, or ``None``."""
    return source_file(_LIVE_CONFIG_NAME)


def build_contract_dict(live_config_path: str | Path) -> dict[str, Any]:
    """Extract the pinned contract sections + the source SHA-256 from a live config."""
    src = Path(live_config_path)
    raw = src.read_bytes()
    live = yaml.safe_load(raw.decode("utf-8"))
    if not isinstance(live, dict):
        raise ValueError(f"live config {src} did not parse to a mapping")
    contract: dict[str, Any] = {
        "contract_schema_version": CONTRACT_SCHEMA_VERSION,
        "source_filename": src.name,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
    }
    for section in CONTRACT_SECTIONS:
        if section in live:
            contract[section] = live[section]
    return contract


_CONTRACT_HEADER = """\
# ------------------------------------------------------------------
# actual_bowaka_v2_contract.yaml -- FROZEN live-strategy contract.
#
# Machine-readable snapshot of the live Bowaka v2 config
# (${BOWAKA_V2_SOURCE_ROOT}/bowaka_v2_config.yaml), pinned at the
# 2026-05-21 realism remediation. The lab simulator must reproduce
# this contract; Phase 1's config-parity diff is checked against it.
#
# DO NOT hand-edit. Regenerate with:
#   python -m bowaka_v2_lab.reference
# (Phase 1 also adds the `bowaka-v2-lab import-actual-config` command.)
#
# source_sha256 is the SHA-256 of the live config file bytes; the
# tests/parity/ suite flags drift between this snapshot and live.
# ------------------------------------------------------------------
"""


def render_contract_yaml(contract: dict[str, Any]) -> str:
    """Deterministic YAML text for a contract dict (header + sorted body)."""
    body = yaml.safe_dump(
        contract,
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
        width=1000,
    )
    return _CONTRACT_HEADER + body


def write_contract_file(
    live_config_path: str | Path, *, out_path: str | Path | None = None
) -> Path:
    """Generate the frozen contract file from a live config. Returns its path."""
    contract = build_contract_dict(live_config_path)
    dest = Path(out_path) if out_path is not None else ACTUAL_CONTRACT_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_contract_yaml(contract), encoding="utf-8")
    return dest


def contract_available() -> bool:
    """True when the frozen contract file is present."""
    return ACTUAL_CONTRACT_PATH.is_file()


def load_actual_contract() -> dict[str, Any]:
    """Load the frozen contract dict. Raises :class:`FileNotFoundError` if absent."""
    if not ACTUAL_CONTRACT_PATH.is_file():
        raise FileNotFoundError(
            f"frozen contract not found: {ACTUAL_CONTRACT_PATH} -- "
            f"generate it with `python -m bowaka_v2_lab.reference`"
        )
    data = yaml.safe_load(ACTUAL_CONTRACT_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"contract {ACTUAL_CONTRACT_PATH} did not parse to a mapping")
    return data


def actual_contract_hash() -> str:
    """SHA-256 of the frozen contract file bytes — the ``strategy_config_hash_actual``.

    Returns an empty string when the contract file is absent, so callers that
    only want lineage metadata never crash on a missing contract.
    """
    if not ACTUAL_CONTRACT_PATH.is_file():
        return ""
    return hashlib.sha256(ACTUAL_CONTRACT_PATH.read_bytes()).hexdigest()


def __getattr__(name: str) -> Any:
    """Lazily expose the Phase 1 contract->config mapper.

    Kept lazy so importing :mod:`bowaka_v2_lab.reference` for lineage hashes
    never pulls in the Pydantic config models.
    """
    if name in ("build_config_from_contract", "render_config_yaml", "import_actual_config"):
        from . import import_config

        return getattr(import_config, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "REFERENCE_DIR",
    "ACTUAL_CONTRACT_PATH",
    "CONTRACT_SECTIONS",
    "CONTRACT_SCHEMA_VERSION",
    "resolve_source_root",
    "source_file",
    "source_config_path",
    "build_contract_dict",
    "render_contract_yaml",
    "write_contract_file",
    "contract_available",
    "load_actual_contract",
    "actual_contract_hash",
    "build_config_from_contract",
    "render_config_yaml",
    "import_actual_config",
]
