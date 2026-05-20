"""OpenAlgo client adapter (paper/live only).

Skeleton port of ``bowaka_v2_openalgo_client.py``. The simulator does not
import this module; Phase 7+ paper trading wires it.
"""
from __future__ import annotations


class OpenAlgoClient:
    """Thin REST adapter for the OpenAlgo paper-trading server.

    Phase 7+ deliverable.
    """

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self.base_url = base_url
        self.api_key = api_key

    def submit_order(self, payload: dict) -> dict:
        raise NotImplementedError("Phase 7+ wires OpenAlgoClient.submit_order")

    def get_position(self, symbol: str) -> dict | None:
        raise NotImplementedError("Phase 7+ wires OpenAlgoClient.get_position")
