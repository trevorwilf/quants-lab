"""Re-export shim: mongo_store.py now lives in bowaka_common.storage.mongo_store.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.storage.mongo_store import (  # noqa: F401
    MongoStore,
)

__all__ = ['MongoStore']
