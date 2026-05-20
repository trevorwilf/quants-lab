"""Re-export shim: serialization.py now lives in bowaka_common.utils.serialization.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.utils.serialization import (  # noqa: F401
    BowakaJSONEncoder,
    dumps,
    loads,
)

__all__ = ['BowakaJSONEncoder', 'dumps', 'loads']
