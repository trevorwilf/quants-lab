"""Realism remediation 2 Phase 3 — content-addressed hash reproducibility (§P1-005).

Two separate Python processes hashing the same lake + config + code-manifest
must produce byte-identical dataset hashes. The footer-hash cache is
process-local; the resulting hash is not.
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import layout


def _build_lake(root: Path) -> None:
    df = pd.DataFrame(
        {
            "symbol": ["AAA"] * 5,
            "timestamp": pd.date_range("2024-09-01", periods=5, tz="UTC"),
            "open": [10.0, 10.1, 10.2, 10.3, 10.4],
            "high": [10.2, 10.3, 10.4, 10.5, 10.6],
            "low": [9.9, 10.0, 10.1, 10.2, 10.3],
            "close": [10.1, 10.2, 10.3, 10.4, 10.5],
            "volume": [1_000.0, 1_100.0, 1_200.0, 1_300.0, 1_400.0],
            "session_date": pd.date_range("2024-09-01", periods=5).date,
        }
    )
    p = layout.daily_bars_path(root, "AAA", feed="iex", adjustment="raw")
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p, index=False)
    mp = layout.ingestion_manifest_path(root)
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(
        '{"feed":"iex","adjustment":"raw","dataset_hashes":{"lake":"sha256:stable"}}',
        encoding="utf-8",
    )


_PROBE = """
import json, sys
from bowaka_v2_lab.data.lineage import content_addressed_dataset_hash
res = content_addressed_dataset_hash(
    lake_root=__import__("pathlib").Path(sys.argv[1]),
    config_hash="cfg_xyz",
    code_manifest_hash="code_xyz",
)
print(json.dumps({"dataset_hash": res["dataset_hash"]}))
"""


def test_dataset_hash_stable_across_processes(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    _build_lake(lake)
    script = tmp_path / "probe.py"
    script.write_text(textwrap.dedent(_PROBE), encoding="utf-8")

    def _run() -> str:
        out = subprocess.check_output(
            [sys.executable, str(script), str(lake)],
            stderr=subprocess.STDOUT, text=True,
        )
        return json.loads(out.strip().splitlines()[-1])["dataset_hash"]

    h1, h2 = _run(), _run()
    assert h1 == h2, "the same inputs must produce identical hashes across processes"


def test_dataset_hash_stable_in_same_process(tmp_path: Path) -> None:
    """Re-hashing the same lake in one process is also stable (cache hit path)."""
    from bowaka_v2_lab.data.lineage import (
        _FOOTER_HASH_CACHE,
        content_addressed_dataset_hash,
    )

    lake = tmp_path / "lake"
    _build_lake(lake)
    _FOOTER_HASH_CACHE.clear()

    h1 = content_addressed_dataset_hash(
        lake_root=lake, config_hash="x", code_manifest_hash="y"
    )["dataset_hash"]
    h2 = content_addressed_dataset_hash(
        lake_root=lake, config_hash="x", code_manifest_hash="y"
    )["dataset_hash"]
    assert h1 == h2
