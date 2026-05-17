"""Environment-variable loading for bowaka_lab.

A single canonical .env discovery path is provided so every notebook,
script, and test in the project loads credentials the same way.

Discovery order (first match wins):

  1. <cwd>/.env
  2. each parent of <cwd>, walking up to the filesystem root, taking the
     first .env found

Rationale: when a notebook is opened from ``research_notebooks/bowaka_lab/``,
the closest .env is the bowaka_lab project's own .env. When run from the
repo root (e.g., via the QuantLab task runner), the repo-root .env is found
instead. Both are valid; we don't merge them — the closer one wins.

The companion ``db_tools/_backfill_lib.find_and_load_dotenv`` follows the
same discovery contract for the standalone backfill notebook. This module
centralises that logic into the installable package so any notebook,
script, or test can call ``load_project_dotenv()`` without duplicating it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def load_project_dotenv(
    start: Optional[Path] = None,
    override: bool = False,
) -> Optional[Path]:
    """Load the first .env file found walking up from ``start`` (or CWD).

    Args:
        start: Directory to begin the walk-up from. Defaults to ``Path.cwd()``.
        override: If True, .env values overwrite existing ``os.environ`` entries.
            Default False — existing process-env values win (so callers can set
            ad-hoc overrides without editing .env).

    Returns:
        The :class:`Path` of the .env file that was loaded, ``None`` if no
        .env was found, or ``None`` if ``python-dotenv`` is not installed.
        Never raises.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return None

    start_path = (start or Path.cwd()).resolve()
    for p in [start_path, *start_path.parents]:
        candidate = p / ".env"
        if candidate.is_file():
            load_dotenv(candidate, override=override)
            return candidate
    return None
