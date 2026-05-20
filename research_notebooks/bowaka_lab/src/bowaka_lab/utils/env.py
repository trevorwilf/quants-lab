"""Re-export shim: env.py now lives in bowaka_common.utils.env.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.utils.env import (  # noqa: F401
    load_project_dotenv,
)

__all__ = ['load_project_dotenv']
