"""JSON encoder for pd.Timestamp, date, Decimal, numpy types."""
from __future__ import annotations

import datetime as _dt
import json
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd


class BowakaV2JSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:  # noqa: D401
        if isinstance(obj, (pd.Timestamp, _dt.datetime)):
            return obj.isoformat()
        if isinstance(obj, _dt.date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, set):
            return sorted(obj)
        return super().default(obj)


def to_json(obj: Any, **kwargs: Any) -> str:
    kwargs.setdefault("sort_keys", True)
    kwargs.setdefault("separators", (",", ":"))
    return json.dumps(obj, cls=BowakaV2JSONEncoder, **kwargs)
