"""Walk-forward terminates with ``OptunaStudyInvalidError`` BEFORE
``build_fold_contexts`` is called when the preflight DQ check fails closed on
adjustment-gating failures.

Speedup report §4 P0-A / §5.1 / Phase 0 task 3 + task 6. The pre-remediation
flow either (a) raised ``PreflightError`` without writing a failed-status
artifact, or (b) classified ``adjustment_mismatch`` as a parity-mode ``warn``
and silently ran the study to completion against a raw lake. The new
short-circuit writes a failed artifact AND raises ``OptunaStudyInvalidError``
before any fold context is built.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

import bowaka_v2_lab.optuna.walkforward_runner as runner
from bowaka_common.marketdata import layout
from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
from tests.fixtures.universe_fixture import write_lake_asset_master


def _write_parquet(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _build_raw_iex_lake(root: Path, symbol: str, months: int = 4) -> tuple[dt.date, dt.date]:
    """Build an IEX lake whose manifest declares ``adjustment: raw`` (no _adjusted
    partition, no split metadata).

    The ``adjustment_mismatch`` and ``split_adjustment_mismatch`` checks both fire
    against this lake when the config requires adjusted daily bars + split
    adjustment.
    """
    start = dt.date(2024, 1, 1)
    end = start + dt.timedelta(days=months * 30)
    days = [d.date() for d in pd.bdate_range(start, end)]
    _write_parquet(
        layout.daily_bars_path(root, symbol, feed="iex"),
        pd.DataFrame(
            {
                "symbol": [symbol] * len(days),
                "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
                "open": [10.0] * len(days), "high": [10.1] * len(days),
                "low": [9.9] * len(days), "close": [10.0] * len(days),
                "volume": [1_000_000] * len(days), "session_date": days,
            }
        ),
    )
    # Per-month minute bars per symbol.
    by_month: dict[tuple[int, int], list] = {}
    for d in days:
        for i in range(60):
            ts = pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=13, minutes=30 + i)
            by_month.setdefault((d.year, d.month), []).append(
                {"symbol": symbol, "timestamp": ts, "open": 10.0, "high": 10.1,
                 "low": 9.9, "close": 10.05, "volume": 5000.0}
            )
    for (year, month), rows in by_month.items():
        _write_parquet(
            layout.minute_bars_path(root, symbol, year, month, feed="iex"),
            pd.DataFrame(rows),
        )
    # Ingestion manifest with adjustment: raw (no split metadata).
    mpath = layout.ingestion_manifest_path(root)
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(
        json.dumps({"feed": "iex", "adjustment": "raw", "dataset_hashes": {"lake": "sha256:raw"}}),
        encoding="utf-8",
    )
    audit_dir = layout.ingestion_dir(root) / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [{
            "symbol": symbol, "feed": "iex", "timeframe": "1d",
            "start": start.isoformat(), "end": end.isoformat(),
            "expected_sessions": len(days), "observed_sessions": len(days),
            "missing_sessions": 0, "duplicate_sessions": 0, "ohlc_violations": 0,
            "zero_volume_sessions": 0, "large_gap_flags": 0,
            "passed_research_audit": True, "warnings": [],
            "audit_run_id": "audit_phase0_test",
        }]
    ).to_parquet(audit_dir / "audit_phase0_test.parquet", index=False)
    write_lake_asset_master(root, [symbol])
    return start, end


_LAB_ROOT = Path(__file__).resolve().parents[2]


def _write_parity_walkforward_config(
    out_path: Path, *, lake: Path, symbol: str, start: dt.date, end: dt.date,
) -> Path:
    """Copy the shipping ``bowaka_v2_actual_iex_current_code_optuna.yml``,
    redirect the lake / symbols / date range so it lands on the test's fixture.

    Mirrors :func:`bowaka_v2_lab.devtools.wf_lake.write_walkforward_test_config`
    EXCEPT it preserves ``simulation.mode = current_code_parity`` and the
    adjustment-required flags so the preflight DQ short-circuit fires.
    """
    base = _LAB_ROOT / "configs" / "bowaka_v2_actual_iex_current_code_optuna.yml"
    raw = yaml.safe_load(Path(base).read_text(encoding="utf-8"))
    raw["backtest"]["start_date"] = start.isoformat()
    raw["backtest"]["end_date"] = end.isoformat()
    raw["market_data"]["shared_root"] = str(lake)
    raw["market_data"]["feed"] = "iex"
    # PRESERVE simulation.mode = current_code_parity + the adjustment-required
    # flags (Phase 0 test goal) — do NOT downgrade to smoke_fixture.
    raw.setdefault("universe", {})["symbols"] = [symbol]
    raw["universe"].setdefault("min_adv_dollars", 0)
    raw["universe"].setdefault("min_price", 1.0)
    raw["universe"].setdefault("max_price", 1_000.0)
    raw["optuna"]["n_trials"] = 1
    raw["optuna"]["n_jobs"] = 1
    raw["optuna"]["walkforward"] = {
        "train_months": 1, "val_months": 1, "final_holdout_months": 1,
    }
    raw["optuna"].pop("storage", None)
    tmp_lab = Path(out_path).parent / "bowaka_v2_lab"
    raw["paths"] = {
        "lab_root": str(tmp_lab),
        "data_root": str(tmp_lab / "data"),
        "artifact_root": str(tmp_lab / "artifacts"),
    }
    Path(out_path).write_text(yaml.safe_dump(raw), encoding="utf-8")
    return Path(out_path)


def test_walkforward_fails_before_context_build_on_raw_lake(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    symbol = "AAA"
    lake = tmp_path / "lake"
    start, end = _build_raw_iex_lake(lake, symbol, months=4)
    cfg_path = _write_parity_walkforward_config(
        tmp_path / "wf.yml", lake=lake, symbol=symbol, start=start, end=end,
    )

    # Patch ``build_fold_contexts`` (as imported by the runner) to raise an
    # AssertionError so the test proves the short-circuit happens BEFORE the
    # parent-side context build.
    def _must_not_be_called(*_args, **_kwargs):
        raise AssertionError(
            "build_fold_contexts must not be called when preflight fails closed"
        )

    monkeypatch.setattr(runner, "build_fold_contexts", _must_not_be_called)

    # Opt into current_code_parity (the suitability gate refuses parity studies
    # without this; we want to land on the preflight DQ gate, not that one).
    with pytest.raises(OptunaStudyInvalidError) as exc_info:
        runner.run_walkforward_study(
            cfg_path,
            allow_smoke=False,
            allow_current_code_parity_study=True,
            tier="research_only",
        )

    assert "adjustment_mismatch" in str(exc_info.value), (
        f"failure reason should mention adjustment_mismatch: {exc_info.value}"
    )

    # The failed-status artifact landed on disk before the exception propagated.
    # The config writer points the lab root at ``tmp_path / bowaka_v2_lab`` so
    # ``BowakaV2Paths.assert_strategy_isolation()`` permits the artifact write.
    artifact_root = tmp_path / "bowaka_v2_lab" / "artifacts"
    optuna_dir = artifact_root / "optuna"
    assert optuna_dir.is_dir(), f"failed-study artifact dir not created: {optuna_dir}"
    artifacts = sorted(optuna_dir.glob("*.json"))
    assert artifacts, f"no failed-study artifact JSON in {optuna_dir}"
    payload = json.loads(artifacts[0].read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert "adjustment_mismatch" in payload["failure_reason"]
