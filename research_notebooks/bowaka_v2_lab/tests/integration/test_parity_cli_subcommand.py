"""End-to-end: ``python -m bowaka_v2_lab.cli parity ...`` against the real lake.

Skip-guarded the same way as the runner test. Asserts the subcommand:
  - returns 0 or 1 (success / soft-fail; not 2 = error),
  - writes ``parity_report.md`` into the chosen ``--output-dir``,
  - prints a JSON line whose ``report_path`` matches that file.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_LAB = Path(__file__).resolve().parents[2]
_REPO_ROOT = _LAB.parents[1]
_PROD_SCRIPT = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_backtest.py"
_PROD_CONFIG = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_config.yaml"
_LAB_CONFIG = _LAB / "configs" / "bowaka_v2_actual_iex_current_code.yml"

pytestmark = pytest.mark.integration


@pytest.mark.timeout(900)
def test_parity_cli_subcommand_writes_report(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    if not _PROD_SCRIPT.is_file():
        pytest.skip(f"production script not at {_PROD_SCRIPT} (run mirror)")
    try:
        from bowaka_common.marketdata.catalog import available_symbols
        from bowaka_common.marketdata.store import resolve_market_data_root
    except ImportError:
        pytest.skip("bowaka_common not importable")
    lake_root = resolve_market_data_root(None, create=False)
    syms = available_symbols(
        lake_root, timeframe="1d", vendor="alpaca",
        feed="iex", adjustment="split_adjusted",
    )
    if "AAPL" not in syms:
        pytest.skip("real lake not present (AAPL not in available symbols)")

    out_dir = tmp_path / "parity_out"
    proc = subprocess.run(
        [sys.executable, "-m", "bowaka_v2_lab.cli", "parity",
         "--start-date", "2026-05-19",
         "--end-date", "2026-05-19",
         "--prod-config", str(_PROD_CONFIG),
         "--lab-config", str(_LAB_CONFIG),
         "--lake-root", str(lake_root),
         "--symbols", ",".join(syms[:5]),
         "--cost-stress", "conservative",
         "--output-dir", str(out_dir),
         "--python-exe", sys.executable],
        cwd=str(_REPO_ROOT),
        capture_output=True, text=True, timeout=720, check=False,
    )
    assert proc.returncode in (0, 1), (
        f"CLI failed with exit {proc.returncode}.\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    md_path = out_dir / "parity_report.md"
    assert md_path.is_file(), f"missing report at {md_path}"
    # The CLI emits a JSON payload on stdout naming the report path.
    payload_line = next(
        (line for line in proc.stdout.splitlines() if line.startswith("{") or line.startswith("[")),
        None,
    )
    if payload_line is None:
        # Argparse may print a multi-line JSON block via indent=2; load it all.
        payload = json.loads(proc.stdout[proc.stdout.index("{"):])
    else:
        payload = json.loads(proc.stdout[proc.stdout.index("{"):])
    assert payload["status"] == "ok"
    assert Path(payload["report_path"]) == md_path
