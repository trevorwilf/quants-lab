"""Preserved v2-archive single-file backtester — DEVELOPER USE ONLY.

Per [Report §9.1]: this is the v2 archive's ``bowaka_v2_backtest.py`` style of
backtester preserved as a regression / smoke harness. It is NOT the
comprehensive simulator. Every artifact written by this module carries
``performance_use="prohibited"`` so reviewers cannot accidentally cite its
output as a performance claim.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..config.paths import BowakaV2Paths
from ..utils.atomic_io import atomic_write_json, write_parquet
from ..utils.ids import generate_run_id


SMOKE_ARTIFACT_TAGS: dict[str, str] = {
    "strategy_id": "bowaka_v2",
    "artifact_class": "dev_smoke_or_regression",
    "performance_use": "prohibited",
}


def run_smoke_backtest(
    *,
    paths: BowakaV2Paths,
    n_synthetic_trades: int = 5,
    initial_bankroll: float = 50_000.0,
    seed: int = 1337,
) -> dict[str, Any]:
    """Generate a tiny synthetic backtest result under ``artifacts/smoke/<run_id>/``.

    Used by tests to verify the dev-tool artifact tag contract.
    """
    paths.assert_strategy_isolation()
    run_id = generate_run_id(kind="smoke", cfg_hash="cafe1234", dataset_hash="beef5678")
    out_dir = paths.artifact_root / "smoke" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Deterministic synthetic trades.
    trades = []
    bankroll = initial_bankroll
    for i in range(n_synthetic_trades):
        pnl = ((-1) ** i) * (50 + i * 5)
        bankroll += pnl
        trades.append({
            "trade_id": f"smoke_{i:03d}",
            "pnl": pnl,
            "bankroll_after": bankroll,
            **SMOKE_ARTIFACT_TAGS,
        })
    summary = {
        "run_id": run_id,
        "n_trades": n_synthetic_trades,
        "initial_bankroll": initial_bankroll,
        "final_bankroll": bankroll,
        **SMOKE_ARTIFACT_TAGS,
    }
    atomic_write_json(out_dir / "summary.json", summary)
    write_parquet(out_dir / "trades.parquet", pd.DataFrame(trades))
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="bowaka_v2 dev smoke backtester (NOT for performance claims)")
    p.add_argument("--synth", action="store_true", help="Run synthetic smoke; required.")
    p.add_argument("--n-trades", type=int, default=5)
    p.add_argument("--bankroll", type=float, default=50_000.0)
    args = p.parse_args(argv)
    if not args.synth:
        print(json.dumps({"error": "--synth required"}))
        return 2
    repo_root = Path(__file__).resolve().parents[5]
    paths = BowakaV2Paths.default(repo_root)
    summary = run_smoke_backtest(
        paths=paths, n_synthetic_trades=args.n_trades,
        initial_bankroll=args.bankroll,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
