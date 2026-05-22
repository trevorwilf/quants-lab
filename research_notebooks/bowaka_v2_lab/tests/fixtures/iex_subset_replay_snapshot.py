"""Build / re-build the approved IEX-subset replay snapshot (Phase 3).

This is a *developer tool*, not a test. It runs the full multi-level DQ stack
against the committed IEX subset under a fixed configuration (deterministic by
construction — committed parquet payloads + fixed window + fixed symbol list)
and emits the normalised snapshot JSON the byte-comparison test reads.

Run once when the Phase-3 baseline is being established, OR when a downstream
phase legitimately changes the DQ surface (the snapshot then needs to be
re-approved and recommitted along with the code change that caused the diff).

Usage::

    cd /quants-lab/research_notebooks/bowaka_v2_lab
    PYTHONPATH=.:src:../bowaka_common/src \\
      /opt/conda/envs/quants-lab/bin/python tests/fixtures/iex_subset_replay_snapshot.py

Writes ``tests/fixtures/iex_subset_replay/approved/dq_report_snapshot.json``.

Normalisation strips fields that are environment-dependent (absolute paths,
mtimes) so two CI runs against the same committed subset produce byte-identical
snapshots.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import yaml

# When invoked as a script the tests/ dir is on sys.path so tests.fixtures.* resolves.
_LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_LAB_ROOT))

from tests.fixtures.loader import IexSubset, load_iex_subset  # noqa: E402

from bowaka_v2_lab.cli_runners import dq_report_command  # noqa: E402
from bowaka_v2_lab.config.loader import load_config  # noqa: E402


#: Fixed window into the committed subset for the deterministic replay.
#: The committed parquet covers 25 daily sessions; sessions [5:8] gives a
#: 3-session window in the middle of the fixture (insulated from any future
#: trimming of the subset's edges).
WINDOW_SLICE = slice(5, 8)


def build_run_config(subset: IexSubset, lab_root: Path) -> Path:
    """The frozen config the snapshot is built against."""
    cfg = load_config(lab_root / "configs" / "bowaka_v2_actual_iex_current_code.yml")
    cfg.pop("_source_path", None)
    cfg["market_data"]["shared_root"] = str(subset.root)
    # The subset is a raw IEX lake — disable the adjustment gates so the DQ
    # stack runs the full multi-level surface instead of aborting early.
    cfg["market_data"]["require_adjusted_daily_bars"] = False
    cfg["market_data"]["require_split_adjustment"] = False
    cfg["simulation"] = {"mode": "current_code_parity"}
    cfg["universe"] = {
        **cfg.get("universe", {}),
        "symbols": list(subset.symbols),
        "min_adv_dollars": 0,
        "min_price": 0.5,
        "max_price": 1_000.0,
    }
    sessions = sorted(subset.sessions)
    window = sessions[WINDOW_SLICE]
    cfg["backtest"] = {
        "start_date": window[0].isoformat(),
        "end_date": window[-1].isoformat(),
        "cost_stress": "base",
    }
    tmp = Path(tempfile.gettempdir()) / "iex_subset_replay_cfg.yml"
    tmp.write_text(yaml.safe_dump(cfg, sort_keys=True), encoding="utf-8")
    return tmp


def normalise_report(report: dict) -> dict:
    """Strip environment-dependent fields from a DQ report.

    The committed parquet payload is deterministic, but the absolute lake root
    (it changes per CI host / tmp_path) is not. We retain the check semantics
    (name, status, count, threshold, every evidence field that is content-
    addressed by the lake's *contents*) and drop the host-specific paths.
    """

    def _clean_evidence(ev: dict) -> dict:
        out: dict = {}
        for k, v in ev.items():
            if k in ("source_file", "shared_root", "lake_root"):
                continue  # absolute paths — host-dependent
            out[k] = v
        return out

    checks_out = []
    for c in sorted(report.get("checks", []), key=lambda x: x["name"]):
        checks_out.append(
            {
                "name": c["name"],
                "status": c["status"],
                "count": c["count"],
                "threshold": c.get("threshold"),
                "source_file": _normalise_source(c.get("source_file", "")),
                "evidence": _clean_evidence(c.get("evidence") or {}),
            }
        )
    return {
        "schema_version": report.get("schema_version"),
        "regime": report.get("regime"),
        "feed": report.get("feed"),
        "passed": report.get("passed"),
        "failed": report.get("failed"),
        "warned": report.get("warned"),
        "required_failures": sorted(report.get("required_failures") or []),
        "adjustment_gating_failures": sorted(report.get("adjustment_gating_failures") or []),
        "per_symbol_failures": {
            k: sorted(v) for k, v in (report.get("per_symbol_failures") or {}).items()
        },
        "notes": report.get("notes", ""),
        "checks": checks_out,
    }


def _normalise_source(s: str) -> str:
    """Strip absolute-path components from a ``source_file`` evidence value."""
    if not s:
        return s
    if "/" in s or "\\" in s:
        return Path(s).name
    return s


def build_snapshot() -> dict:
    subset = load_iex_subset(lake_source="committed")
    assert not subset.synthetic_fallback, (
        "the deterministic-replay baseline requires the real IEX subset; "
        "synthetic_fallback was loaded — regenerate the subset with "
        "tests/fixtures/build_iex_subset.py against the real lake first"
    )
    cfg_path = build_run_config(subset, _LAB_ROOT)
    with tempfile.TemporaryDirectory() as outdir:
        out = Path(outdir) / "dq.json"
        dq_report_command(str(cfg_path), out_path=out)
        report = json.loads(out.read_text(encoding="utf-8"))
    return normalise_report(report)


def main() -> int:
    snapshot = build_snapshot()
    target_dir = _LAB_ROOT / "tests" / "fixtures" / "iex_subset_replay" / "approved"
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / "dq_report_snapshot.json"
    out_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"[iex_subset_replay_snapshot] wrote {out_path} ({out_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
