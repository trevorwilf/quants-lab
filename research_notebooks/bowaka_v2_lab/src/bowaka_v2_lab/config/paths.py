"""Path resolution for bowaka_v2_lab.

Per [Report §6.2]: every v2 artifact must resolve under a path containing
``bowaka_v2_lab`` literally. Paths from a v1 lab (``bowaka_lab/`` without the
``v2`` suffix) or from the v2 source archive (``scripts/data/bowaka_v2``)
must be rejected — the strategy lab is the single point of truth for v2 outputs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


_FORBIDDEN_PATH_FRAGMENTS = (
    "scripts/data/bowaka_v2",
    "scripts\\data\\bowaka_v2",
)


def _contains_v1_lab_root(p: Path) -> bool:
    parts = [part.replace("\\", "/") for part in p.parts]
    joined = "/".join(parts).lower()
    # Reject paths under research_notebooks/bowaka_lab/ (v1) but allow
    # paths under research_notebooks/bowaka_v2_lab/ (v2).
    if "research_notebooks/bowaka_lab" in joined and "research_notebooks/bowaka_v2_lab" not in joined:
        return True
    return False


@dataclass(frozen=True)
class BowakaV2Paths:
    """Canonical path bundle for a v2 run.

    All four paths must resolve under a directory whose normalised string contains
    ``bowaka_v2_lab``. Construction does not enforce this; callers must call
    ``assert_strategy_isolation()`` (or rely on validators in higher-level code).
    """

    lab_root: Path
    data_root: Path
    artifact_root: Path
    config_path: Path

    def assert_strategy_isolation(self) -> None:
        """Raise ``ValueError`` if any path violates strategy isolation rules.

        Rules (per [Report §6.2]):
        1. ``data_root`` and ``artifact_root`` must contain ``bowaka_v2_lab``.
        2. No path may contain ``research_notebooks/bowaka_lab/`` (v1).
        3. No path may contain ``scripts/data/bowaka_v2`` (the source archive).
        """
        for name in ("lab_root", "data_root", "artifact_root"):
            p = getattr(self, name)
            normalised = str(p).replace("\\", "/").lower()
            if "bowaka_v2_lab" not in normalised:
                raise ValueError(
                    f"{name}={p!s} does not contain 'bowaka_v2_lab'; "
                    "v2 artifacts must live under the v2 lab root"
                )
            for frag in _FORBIDDEN_PATH_FRAGMENTS:
                if frag in normalised:
                    raise ValueError(
                        f"{name}={p!s} contains forbidden fragment {frag!r}; "
                        "v2 must not write into the v2 source archive's scripts/data/bowaka_v2 tree"
                    )
            if _contains_v1_lab_root(p):
                raise ValueError(
                    f"{name}={p!s} references the v1 lab root (research_notebooks/bowaka_lab/); "
                    "v2 must not write into v1 paths"
                )

    @classmethod
    def from_config(cls, cfg: "object", *, repo_root: Path | None = None) -> "BowakaV2Paths":
        """Construct from a parsed BowakaV2Config or a dict-like with ``paths``."""
        paths_section = getattr(cfg, "paths", None)
        if paths_section is None and isinstance(cfg, dict):
            paths_section = cfg.get("paths")
        if paths_section is None:
            raise ValueError("config has no 'paths' section")

        if hasattr(paths_section, "lab_root"):
            lab_root = Path(paths_section.lab_root)
            data_root = Path(paths_section.data_root)
            artifact_root = Path(paths_section.artifact_root)
        else:
            lab_root = Path(paths_section["lab_root"])
            data_root = Path(paths_section["data_root"])
            artifact_root = Path(paths_section["artifact_root"])

        config_path_attr = getattr(cfg, "_source_path", None) or (
            cfg.get("_source_path") if isinstance(cfg, dict) else None
        )
        config_path = Path(config_path_attr) if config_path_attr else Path("")

        if repo_root is not None:
            if not lab_root.is_absolute():
                lab_root = (repo_root / lab_root).resolve()
            if not data_root.is_absolute():
                data_root = (repo_root / data_root).resolve()
            if not artifact_root.is_absolute():
                artifact_root = (repo_root / artifact_root).resolve()
        return cls(
            lab_root=lab_root,
            data_root=data_root,
            artifact_root=artifact_root,
            config_path=config_path,
        )

    @classmethod
    def default(cls, repo_root: Path) -> "BowakaV2Paths":
        """Default location: ``research_notebooks/bowaka_v2_lab/{data,artifacts}``."""
        lab = (repo_root / "research_notebooks" / "bowaka_v2_lab").resolve()
        return cls(
            lab_root=lab,
            data_root=lab / "data",
            artifact_root=lab / "artifacts",
            config_path=Path(""),
        )
