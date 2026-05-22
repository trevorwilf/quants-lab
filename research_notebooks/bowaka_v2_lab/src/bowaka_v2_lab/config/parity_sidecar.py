"""Structured parity sidecar — declared diffs vs the frozen contract.

Realism remediation 2 Phase 0 (audit §P0-001). A *parity sidecar* is the
auditable record of every deliberate divergence between a lab config and the
frozen live-strategy contract (``reference/actual_bowaka_v2_contract.yaml``).

The sidecar file is ``<config-stem>.parity_sidecar.yaml``, next to the config::

    schema_version: 1
    declared_diffs:
      - field_path: exits.stop_pct
        actual_value: 0.08
        lab_value: 0.05
        reason: "SIP-tightened stop for the sip_tightened variant"
        risk_classification: scoped

Each declared diff is a :class:`ParitySidecar` row. ``risk_classification`` is
one of ``benign`` / ``scoped`` / ``dangerous``.

This module *builds on* :mod:`bowaka_v2_lab.config.config_diff` — the leaf-level
diff is computed there; this module only layers the structured declaration +
classification on top. :func:`classify_config_parity` returns the merged view a
CLI / refusal-gate consumes; :func:`undeclared_diff_paths` is the hard gate
(non-empty -> the config diverges from the contract without a sidecar entry).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from .config_diff import build_config_diff, unannotated_mismatches

#: Allowed values for ``ParitySidecar.risk_classification``.
RISK_CLASSIFICATIONS: tuple[str, ...] = ("benign", "scoped", "dangerous")

#: Basename suffix of the structured parity sidecar for a config.
SIDECAR_SUFFIX = ".parity_sidecar.yaml"


@dataclass(frozen=True)
class ParitySidecar:
    """One declared divergence of a lab config from the frozen contract.

    A sidecar *file* is a list of these. Each row pins the contract value
    (``actual_value``), the config value (``lab_value``), a human ``reason``,
    and a ``risk_classification`` ∈ :data:`RISK_CLASSIFICATIONS`.
    """

    field_path: str
    actual_value: Any
    lab_value: Any
    reason: str
    risk_classification: str

    def __post_init__(self) -> None:
        if not self.field_path:
            raise ValueError("ParitySidecar.field_path must be a non-empty dotted path")
        if not str(self.reason).strip():
            raise ValueError(
                f"ParitySidecar({self.field_path}): reason must be a non-empty string"
            )
        if self.risk_classification not in RISK_CLASSIFICATIONS:
            raise ValueError(
                f"ParitySidecar({self.field_path}): risk_classification="
                f"{self.risk_classification!r} invalid; expected one of "
                f"{RISK_CLASSIFICATIONS}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Plain-dict form for YAML serialisation."""
        return {
            "field_path": self.field_path,
            "actual_value": self.actual_value,
            "lab_value": self.lab_value,
            "reason": self.reason,
            "risk_classification": self.risk_classification,
        }

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "ParitySidecar":
        """Build a :class:`ParitySidecar` from a sidecar-file row.

        Raises ``ValueError`` (via ``__post_init__``) on a missing/invalid field.
        """
        missing = {"field_path", "reason", "risk_classification"} - set(row)
        if missing:
            raise ValueError(
                f"parity sidecar row missing required key(s): {sorted(missing)}"
            )
        return cls(
            field_path=str(row["field_path"]),
            actual_value=row.get("actual_value"),
            lab_value=row.get("lab_value"),
            reason=str(row["reason"]),
            risk_classification=str(row["risk_classification"]),
        )


def sidecar_path_for(config_path: str | Path) -> Path:
    """Return the ``<config-stem>.parity_sidecar.yaml`` path for a config."""
    cfg = Path(config_path)
    return cfg.with_name(f"{cfg.stem}{SIDECAR_SUFFIX}")


def load_parity_sidecar(config_path: str | Path) -> list[ParitySidecar]:
    """Load the structured parity sidecar for a config, or ``[]`` if absent.

    Raises ``ValueError`` if the sidecar file exists but is malformed (so a
    typo'd sidecar fails loudly rather than silently declaring nothing).
    """
    sidecar = sidecar_path_for(config_path)
    if not sidecar.is_file():
        return []
    data = yaml.safe_load(sidecar.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"parity sidecar {sidecar} did not parse to a mapping")
    rows = data.get("declared_diffs")
    if rows is None:
        return []
    if not isinstance(rows, list):
        raise ValueError(
            f"parity sidecar {sidecar}: 'declared_diffs' must be a list"
        )
    return [ParitySidecar.from_dict(r) for r in rows]


def render_parity_sidecar(rows: Iterable[ParitySidecar]) -> str:
    """Deterministic YAML text for a parity-sidecar file."""
    doc = {
        "schema_version": 1,
        "declared_diffs": [r.to_dict() for r in rows],
    }
    return yaml.safe_dump(doc, sort_keys=True, default_flow_style=False, width=1000)


def write_parity_sidecar(config_path: str | Path, rows: Iterable[ParitySidecar]) -> Path:
    """Write the structured parity sidecar next to ``config_path``. Returns its path."""
    dest = sidecar_path_for(config_path)
    dest.write_text(render_parity_sidecar(rows), encoding="utf-8")
    return dest


def classify_config_parity(
    lab_cfg: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    sidecar: Iterable[ParitySidecar] = (),
) -> dict[str, Any]:
    """Merge the leaf diff with the structured sidecar declarations.

    Builds the contract diff via :func:`config_diff.build_config_diff`, then for
    every leaf that diverges decides whether the sidecar declares it. Returns::

        {
          "rows": [ {path, actual_value, lab_value, status, ...}, ... ],
          "summary": {"match", "declared", "undeclared", "total_diffs"},
          "undeclared": ["exits.stop_pct", ...],   # diverging, NO sidecar entry
          "declared":   [{path, risk_classification, reason}, ...],
        }

    ``status`` is ``match`` / ``declared`` / ``undeclared``.
    """
    declared_by_path = {s.field_path: s for s in sidecar}
    # The leaf diff treats any sidecar-declared path as an intentional override
    # (so build_config_diff's own status is consistent), but the authoritative
    # declared/undeclared split is computed here from the structured sidecar.
    diff_rows = build_config_diff(
        lab_cfg, contract, intentional_overrides=declared_by_path.keys()
    )

    rows: list[dict[str, Any]] = []
    undeclared: list[str] = []
    declared: list[dict[str, Any]] = []
    n_match = 0
    for row in diff_rows:
        path = str(row["path"])
        diverges = row["parity_status"] != "match"
        out_row = {
            "path": path,
            "actual_value": row["actual_value"],
            "lab_value": row["lab_value"],
        }
        if not diverges:
            n_match += 1
            out_row["status"] = "match"
            rows.append(out_row)
            continue
        sc = declared_by_path.get(path)
        if sc is None:
            out_row["status"] = "undeclared"
            undeclared.append(path)
        else:
            out_row["status"] = "declared"
            out_row["risk_classification"] = sc.risk_classification
            out_row["reason"] = sc.reason
            declared.append(
                {
                    "path": path,
                    "risk_classification": sc.risk_classification,
                    "reason": sc.reason,
                }
            )
        rows.append(out_row)

    return {
        "rows": rows,
        "summary": {
            "match": n_match,
            "declared": len(declared),
            "undeclared": len(undeclared),
            "total_diffs": len(declared) + len(undeclared),
        },
        "undeclared": sorted(undeclared),
        "declared": declared,
    }


def undeclared_diff_paths(
    lab_cfg: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    sidecar: Iterable[ParitySidecar] = (),
) -> list[str]:
    """Leaf paths that diverge from the contract with NO sidecar declaration.

    Empty -> the config is contract-parity-clean (every diff is declared). This
    is the hard gate the Optuna refusal check and the ``config-parity`` CLI use.
    """
    return classify_config_parity(lab_cfg, contract, sidecar=sidecar)["undeclared"]


__all__ = [
    "RISK_CLASSIFICATIONS",
    "SIDECAR_SUFFIX",
    "ParitySidecar",
    "sidecar_path_for",
    "load_parity_sidecar",
    "render_parity_sidecar",
    "write_parity_sidecar",
    "classify_config_parity",
    "undeclared_diff_paths",
    # re-exported from config_diff for the refusal gate's convenience.
    "unannotated_mismatches",
]
