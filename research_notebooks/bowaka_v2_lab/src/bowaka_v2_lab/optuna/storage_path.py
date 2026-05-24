"""Optuna storage-URI resolution (audit 2026-05-23 §P1-006).

Pre-remediation ``optuna.storage: sqlite:///research_notebooks/bowaka_v2_lab/artifacts/optuna/local.db``
was CWD-sensitive: launching the runner from the lab directory (where the
notebooks live) made the path resolve to
``research_notebooks/bowaka_v2_lab/research_notebooks/bowaka_v2_lab/artifacts/``.

:func:`resolve_storage_uri` repoints a relative SQLite URI at an absolute path
under ``paths.lab_root``, creates the parent directory, and returns a normalised
``sqlite:////absolute/path`` URI. PostgreSQL URIs are returned unchanged.
"""
from __future__ import annotations

import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover — import-time only
    from ..config.paths import BowakaV2Paths


def resolve_storage_uri(raw: str, *, paths: "BowakaV2Paths") -> str:
    """Resolve a possibly-relative ``sqlite:///`` URI against ``paths.lab_root``.

    - PostgreSQL URIs (``postgresql+...``) are returned unchanged.
    - Relative SQLite URIs are repointed at an absolute path under
      ``paths.lab_root``. The parent directory is created.
    - Absolute SQLite URIs are returned unchanged (no relocation).

    Audit 2026-05-23 §P1-006.
    """
    if raw.startswith("postgresql"):
        return raw
    if not raw.startswith("sqlite"):
        raise ValueError(f"unsupported optuna storage URI: {raw!r}")
    parsed = urllib.parse.urlparse(raw)
    # ``sqlite:///rel/path`` -> ``parsed.path == "/rel/path"``.
    # ``sqlite:////abs/path`` -> ``parsed.path == "//abs/path"`` (already absolute).
    path_text = parsed.path
    if path_text.startswith("//"):
        # Already absolute (``sqlite:////abs/path``).
        return raw
    db_path = Path(path_text.lstrip("/"))
    if not db_path.is_absolute():
        # If the relative path begins with a segment that matches the lab root's
        # last segment (e.g. ``research_notebooks/bowaka_v2_lab/artifacts/...``)
        # and the lab root itself ends in ``bowaka_v2_lab``, strip the lab-root
        # prefix so we don't double up — the user's intent is the path RELATIVE
        # TO the lab root.
        try:
            lab_str = str(paths.lab_root).replace("\\", "/")
        except AttributeError:
            lab_str = ""
        db_str = db_path.as_posix()
        if lab_str and db_str.startswith(lab_str.split("/")[-2] + "/"):
            # e.g. lab=/foo/research_notebooks/bowaka_v2_lab,
            #      db=research_notebooks/bowaka_v2_lab/artifacts/...
            # → strip 'research_notebooks/bowaka_v2_lab/' prefix
            parts = db_str.split("/", 2)
            if len(parts) >= 3 and "bowaka_v2_lab" in parts[1]:
                db_path = Path(parts[2])
        db_path = (paths.lab_root / db_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


__all__ = ["resolve_storage_uri"]
