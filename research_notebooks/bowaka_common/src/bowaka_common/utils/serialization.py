"""JSON encoding for Bowaka domain types."""

from __future__ import annotations

import datetime as _dt
import json
from decimal import Decimal
from typing import Any

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore[assignment]

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None  # type: ignore[assignment]


class BowakaJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, (_dt.date, _dt.datetime)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return str(o)
        if np is not None and isinstance(o, np.generic):
            return o.item()
        if np is not None and isinstance(o, np.ndarray):
            return o.tolist()
        if pd is not None and isinstance(o, pd.Timestamp):
            return o.isoformat()
        if pd is not None and isinstance(o, pd.Timedelta):
            return o.total_seconds()
        if hasattr(o, "model_dump"):
            return o.model_dump(mode="json")
        if hasattr(o, "__dict__"):
            return o.__dict__
        return super().default(o)


def dumps(obj: Any, **kw: Any) -> str:
    kw.setdefault("cls", BowakaJSONEncoder)
    kw.setdefault("sort_keys", True)
    return json.dumps(obj, **kw)


def loads(text: str, **kw: Any) -> Any:
    return json.loads(text, **kw)
