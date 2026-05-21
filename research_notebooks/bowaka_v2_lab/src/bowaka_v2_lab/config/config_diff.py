"""Config-parity diff against the frozen live contract (realism Phase 1).

:func:`build_config_diff` compares a lab config to the frozen contract
(``reference/actual_bowaka_v2_contract.yaml``) and returns one row per leaf key:

    {"path": "signals.rvol_so_far_min",
     "actual_value": 0.7, "lab_value": 0.7, "parity_status": "match"}

``parity_status`` is one of:

- ``match``                — lab value equals the contract value.
- ``mismatch``             — lab value differs (or a contract key is unset).
- ``intentional_override`` — a deliberate divergence, declared in the optional
  sidecar ``<config>.parity.yml`` under key ``intentional_overrides``.

Sections ``signals`` / ``sizing`` / ``risk`` / ``exits`` / ``session`` share the
contract's schema, so every contract leaf is checked. Sections ``universe`` /
``scanner`` / ``execution`` use a *different* lab schema — only keys present on
**both** sides are diffed, and a key absent on one side is never a hard
``mismatch``.

In ``intended_realism`` mode a run must abort at startup when any *unannotated*
``mismatch`` exists — see :func:`unannotated_mismatches` and the backtester.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from ..utils.atomic_io import atomic_write_text

#: Sections whose lab schema matches the contract — every contract leaf checked.
_SCHEMA_MATCHING_SECTIONS: tuple[str, ...] = (
    "signals",
    "sizing",
    "risk",
    "exits",
    "session",
)
#: Sections whose lab schema diverges — diff only keys present on both sides.
_DIVERGENT_SECTIONS: tuple[str, ...] = (
    "universe",
    "scanner",
    "execution",
)


def _flatten(node: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten a nested mapping/list to ``{dotted.path: leaf_value}``."""
    out: dict[str, Any] = {}
    if isinstance(node, Mapping):
        for key, value in node.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten(value, child))
    elif isinstance(node, (list, tuple)):
        for idx, value in enumerate(node):
            child = f"{prefix}.{idx}" if prefix else str(idx)
            out.update(_flatten(value, child))
    else:
        out[prefix] = node
    return out


def _values_equal(a: Any, b: Any) -> bool:
    """Equality with int/float coercion (YAML may load 90000 as int or float)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b or a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return a == b


def load_parity_overrides(config_path: str | Path | None) -> set[str]:
    """Leaf paths declared as intentional overrides in the parity sidecar.

    The sidecar is ``<config-stem>.parity.yml`` next to the config; its
    ``intentional_overrides`` key is a list of dotted leaf paths. Absent sidecar
    -> empty set (no overrides).
    """
    if config_path is None:
        return set()
    cfg = Path(config_path)
    sidecar = cfg.with_name(f"{cfg.stem}.parity.yml")
    if not sidecar.is_file():
        return set()
    data = yaml.safe_load(sidecar.read_text(encoding="utf-8")) or {}
    overrides = data.get("intentional_overrides") or []
    return {str(p) for p in overrides}


def build_config_diff(
    lab_cfg: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    intentional_overrides: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Build the leaf-by-leaf parity diff rows (sorted by ``path``)."""
    overrides = {str(p) for p in intentional_overrides}
    rows: list[dict[str, Any]] = []

    for section in _SCHEMA_MATCHING_SECTIONS:
        c_flat = _flatten(contract.get(section) or {}, section)
        l_flat = _flatten(lab_cfg.get(section) or {}, section)
        # Check every contract leaf (the contract is the parity anchor). A
        # lab-only extra key (e.g. session.calendar) is not a contract leaf, so
        # it is not diffed.
        for path in sorted(c_flat):
            actual = c_flat[path]
            present = path in l_flat
            lab_value = l_flat.get(path)
            if present and _values_equal(actual, lab_value):
                status = "match"
            elif path in overrides:
                status = "intentional_override"
            else:
                status = "mismatch"
            rows.append({
                "path": path,
                "actual_value": actual,
                "lab_value": lab_value if present else None,
                "parity_status": status,
            })

    for section in _DIVERGENT_SECTIONS:
        c_flat = _flatten(contract.get(section) or {}, section)
        l_flat = _flatten(lab_cfg.get(section) or {}, section)
        # Schema diverges — only keys present on BOTH sides are comparable.
        for path in sorted(set(c_flat) & set(l_flat)):
            actual = c_flat[path]
            lab_value = l_flat[path]
            if _values_equal(actual, lab_value):
                status = "match"
            elif path in overrides:
                status = "intentional_override"
            else:
                status = "mismatch"
            rows.append({
                "path": path,
                "actual_value": actual,
                "lab_value": lab_value,
                "parity_status": status,
            })

    return rows


def unannotated_mismatches(diff_rows: Iterable[Mapping[str, Any]]) -> list[str]:
    """Paths whose ``parity_status`` is ``mismatch`` (not annotated as override)."""
    return [str(r["path"]) for r in diff_rows if r.get("parity_status") == "mismatch"]


def render_config_diff_yaml(diff_rows: list[dict[str, Any]]) -> str:
    """Deterministic YAML text for the ``config_diff_vs_actual_bowaka_v2.yaml`` artifact."""
    summary = {
        "match": sum(1 for r in diff_rows if r["parity_status"] == "match"),
        "mismatch": sum(1 for r in diff_rows if r["parity_status"] == "mismatch"),
        "intentional_override": sum(
            1 for r in diff_rows if r["parity_status"] == "intentional_override"
        ),
    }
    doc = {
        "schema_version": 1,
        "summary": summary,
        "rows": diff_rows,
    }
    return yaml.safe_dump(doc, sort_keys=True, default_flow_style=False, width=1000)


def write_config_diff(
    run_dir: str | Path,
    lab_cfg: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    config_path: str | Path | None = None,
) -> tuple[Path, list[dict[str, Any]]]:
    """Write ``config_diff_vs_actual_bowaka_v2.yaml`` into ``run_dir``.

    Returns ``(path, diff_rows)``. ``config_path`` locates the parity sidecar.
    """
    overrides = load_parity_overrides(config_path)
    diff_rows = build_config_diff(lab_cfg, contract, intentional_overrides=overrides)
    dest = Path(run_dir) / "config_diff_vs_actual_bowaka_v2.yaml"
    atomic_write_text(dest, render_config_diff_yaml(diff_rows))
    return dest, diff_rows


def write_empty_config_diff(run_dir: str | Path, *, note: str) -> Path:
    """Write a no-rows parity-diff artifact (used when the contract is absent).

    Keeps the run's artifact contract intact and records ``note`` rather than
    silently skipping the parity diff.
    """
    dest = Path(run_dir) / "config_diff_vs_actual_bowaka_v2.yaml"
    doc = {"schema_version": 1, "summary": {}, "rows": [], "note": note}
    atomic_write_text(dest, yaml.safe_dump(doc, sort_keys=True, default_flow_style=False))
    return dest


__all__ = [
    "build_config_diff",
    "unannotated_mismatches",
    "load_parity_overrides",
    "render_config_diff_yaml",
    "write_config_diff",
    "write_empty_config_diff",
]
