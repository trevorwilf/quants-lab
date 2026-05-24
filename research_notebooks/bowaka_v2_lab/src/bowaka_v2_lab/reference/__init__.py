"""Frozen contract for the live Bowaka v2 strategy.

``actual_bowaka_v2_contract.yaml`` (in the lab's ``reference/`` directory) is a
machine-readable snapshot of the live strategy config
(``${BOWAKA_V2_SOURCE_ROOT}/bowaka_v2_config.yaml``), pinned at the 2026-05-21
realism remediation. The lab simulator must reproduce this contract; Phase 1's
config-parity diff and the ``tests/parity/`` suite are checked against it.

Audit 2026-05-23 §P1-002 — the contract additionally hashes every authoritative
source file via ``source_manifest`` and the rolled-up ``source_manifest_hash``.
:func:`assert_source_manifest_unchanged` raises :class:`ConfigParityError` when
the live source tree drifts from the manifest the contract was generated against.

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

import ast
import hashlib
import json
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
#: v3: realism remediation 3 Phase 2 added the ``source_manifest`` block (audit §P1-002).
CONTRACT_SCHEMA_VERSION = 3

#: Basename of the live strategy config.
_LIVE_CONFIG_NAME = "bowaka_v2_config.yaml"

#: Authoritative source files the lab claims to replicate. Audit 2026-05-23
#: §P1-002 — the contract hashes every entry (not just bowaka_v2_config.yaml).
#: When ``bowaka_v2_strategy.py`` imports additional ``.py`` files via the
#: ``bowaka_*`` prefix, :func:`compute_source_manifest` adds them automatically
#: by static-analyzing the imports (never via execution).
AUTHORITATIVE_SOURCE_FILES: tuple[str, ...] = (
    "bowaka_v2_config.yaml",
    "bowaka_v2_strategy.py",
    "bowaka_intraday_scanner.py",
    "bowaka_v2_features.py",
    "bowaka_v2_schemas.py",
    "bowaka_v2_backtest.py",
    "bowaka_universe_builder.yaml",
)

#: Module-name prefix the scanner / strategy / backtest modules use; we walk
#: relative imports under this prefix when expanding the source manifest.
_BOWAKA_MODULE_PREFIX = "bowaka_"


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
    """Extract the pinned contract sections + the source manifest from a live config.

    Audit 2026-05-23 §P1-002 — the contract now includes a ``source_manifest``
    mapping every authoritative source file to its sha256 + bytes, plus a
    ``source_manifest_hash`` rollup that downstream code uses as the single
    "lab parity fingerprint."
    """
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
    # Audit 2026-05-23 §P1-002 — extend the contract with a source_manifest
    # hashing every authoritative source file (not just the YAML).
    source_root = src.parent
    manifest = compute_source_manifest(source_root)
    contract["source_manifest"] = manifest
    contract["source_manifest_hash"] = _hash_source_manifest(manifest)
    return contract


def _file_sha256(path: Path) -> tuple[str, int]:
    """Return ``(sha256_hex, byte_length)`` for one file."""
    raw = path.read_bytes()
    return hashlib.sha256(raw).hexdigest(), len(raw)


def _relative_python_imports(py_path: Path, *, prefix: str = _BOWAKA_MODULE_PREFIX) -> set[str]:
    """Statically extract relative ``bowaka_*`` module names imported from ``py_path``.

    Uses :mod:`ast` — no execution. Returns module *base* names (no path),
    e.g. ``{"bowaka_v2_paths", "bowaka_v2_event_stream_versioning"}``. Modules
    that don't start with ``prefix`` are ignored (stdlib / third-party).
    """
    if not py_path.is_file():
        return set()
    try:
        tree = ast.parse(py_path.read_bytes(), filename=str(py_path))
    except SyntaxError:
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(prefix):
                    found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "")
            if mod.startswith(prefix):
                found.add(mod.split(".")[0])
    return found


def compute_source_manifest(source_root: Path) -> dict[str, dict[str, Any]]:
    """Hash every authoritative source file under ``source_root``.

    Audit 2026-05-23 §P1-002. Returns ``{filename: {"sha256": hex, "bytes": int}}``
    for every entry in :data:`AUTHORITATIVE_SOURCE_FILES` plus every relative
    ``bowaka_*`` import statically discovered in ``bowaka_v2_strategy.py``.

    A missing required file raises :class:`FileNotFoundError` with a recovery
    hint pointing at ``mirror_bowaka_v2_source.ps1``.
    """
    source_root = Path(source_root)
    manifest: dict[str, dict[str, Any]] = {}
    candidate_dirs = [source_root, source_root / "scripts"]

    def _locate(name: str) -> Optional[Path]:
        for d in candidate_dirs:
            cand = d / name
            try:
                if cand.is_file():
                    return cand
            except OSError:
                continue
        return None

    missing: list[str] = []
    for filename in AUTHORITATIVE_SOURCE_FILES:
        path = _locate(filename)
        if path is None:
            missing.append(filename)
            continue
        sha, size = _file_sha256(path)
        manifest[filename] = {"sha256": sha, "bytes": size}

    if missing:
        raise FileNotFoundError(
            f"source manifest cannot be built: required file(s) missing under "
            f"{source_root}: {missing}. Run mirror_bowaka_v2_source.ps1 (repo "
            f"root) to repopulate the source mirror, or point "
            f"$BOWAKA_V2_SOURCE_ROOT at a tree that contains them."
        )

    # Static-analyze bowaka_v2_strategy.py for additional bowaka_* imports —
    # so a future refactor that splits out a new file still gets hashed.
    strategy_path = _locate("bowaka_v2_strategy.py")
    if strategy_path is not None:
        for module in _relative_python_imports(strategy_path):
            filename = f"{module}.py"
            if filename in manifest:
                continue
            path = _locate(filename)
            if path is None:
                continue  # silently ignore — the import may resolve to a package
            sha, size = _file_sha256(path)
            manifest[filename] = {"sha256": sha, "bytes": size}

    return manifest


def _hash_source_manifest(manifest: dict[str, dict[str, Any]]) -> str:
    """SHA-256 of the canonical-JSON-serialized manifest mapping."""
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def source_manifest_hash() -> str:
    """The contract's frozen ``source_manifest_hash`` (or ``""`` if no contract)."""
    if not ACTUAL_CONTRACT_PATH.is_file():
        return ""
    contract = load_actual_contract()
    return str(contract.get("source_manifest_hash", ""))


def assert_source_manifest_unchanged() -> None:
    """Raise :class:`ConfigParityError` when the live source drifts from the contract.

    Audit 2026-05-23 §P1-002. Compares the live source tree at
    :func:`resolve_source_root` to the contract's frozen ``source_manifest``;
    lists every file whose sha256 changed, was added, or is missing. When the
    contract has no ``source_manifest`` (legacy v2 contract), this is a no-op.
    When the live source tree cannot be located, raises with a recovery hint
    rather than passing silently.
    """
    from ..optuna.errors import ConfigParityError

    if not ACTUAL_CONTRACT_PATH.is_file():
        return  # nothing to compare against
    contract = load_actual_contract()
    frozen = contract.get("source_manifest")
    if not isinstance(frozen, dict):
        return  # legacy v2 contract — no source manifest to check
    source_root = resolve_source_root()
    if source_root is None:
        raise ConfigParityError(
            "live source tree not located: set $BOWAKA_V2_SOURCE_ROOT or "
            "populate reference/source_strategy/scripts/ via "
            "mirror_bowaka_v2_source.ps1. See "
            "docs/audits/2026-05-23_realism_audit.md §P1-002."
        )
    try:
        live = compute_source_manifest(source_root)
    except FileNotFoundError as exc:
        raise ConfigParityError(str(exc)) from exc
    drift: list[str] = []
    for filename, info in frozen.items():
        live_info = live.get(filename)
        if live_info is None:
            drift.append(f"{filename}: MISSING from live source")
            continue
        if live_info.get("sha256") != info.get("sha256"):
            drift.append(
                f"{filename}: sha256 {info.get('sha256', '?')[:12]}... -> "
                f"{live_info.get('sha256', '?')[:12]}..."
            )
    for filename in live:
        if filename not in frozen:
            drift.append(f"{filename}: ADDED to live source (not in contract)")
    if drift:
        raise ConfigParityError(
            "source_manifest drift detected — live source diverges from the "
            f"frozen contract on {len(drift)} file(s):\n  "
            + "\n  ".join(drift)
            + "\nRegenerate the contract deliberately via "
              "`python -m bowaka_v2_lab.reference` AFTER reviewing each diff. "
              "See docs/audits/2026-05-23_realism_audit.md §P1-002."
        )


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
    "AUTHORITATIVE_SOURCE_FILES",
    "resolve_source_root",
    "source_file",
    "source_config_path",
    "build_contract_dict",
    "render_contract_yaml",
    "write_contract_file",
    "contract_available",
    "load_actual_contract",
    "actual_contract_hash",
    "compute_source_manifest",
    "source_manifest_hash",
    "assert_source_manifest_unchanged",
    "build_config_from_contract",
    "render_config_yaml",
    "import_actual_config",
]
