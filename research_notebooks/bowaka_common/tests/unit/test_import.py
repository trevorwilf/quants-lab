"""Smoke import + version test for bowaka_common."""
from __future__ import annotations


def test_package_imports_and_has_version() -> None:
    import bowaka_common

    assert bowaka_common.__version__ == "0.1.0"


def test_calendar_module_imports() -> None:
    from bowaka_common.calendar.exchange import USEquityCalendar  # noqa: F401


def test_data_modules_import() -> None:
    from bowaka_common.data.alpaca_client import AlpacaClient  # noqa: F401
    from bowaka_common.data.schemas import build_candidate_v3  # noqa: F401
    from bowaka_common.data.bars import fetch_daily_bars  # noqa: F401


def test_storage_modules_import() -> None:
    from bowaka_common.storage.mongo_store import MongoStore  # noqa: F401
    from bowaka_common.storage.dataset_hash import hash_dataframe  # noqa: F401


def test_artifacts_modules_import() -> None:
    from bowaka_common.artifacts import (  # noqa: F401
        build_run_manifest,
        build_dataset_manifest,
        build_code_manifest,
        write_run_dir,
    )


def test_research_modules_import() -> None:
    from bowaka_common.research.splits import WalkForwardPlan  # noqa: F401
    from bowaka_common.research.walkforward import run_walkforward  # noqa: F401


def test_metrics_modules_import() -> None:
    import bowaka_common.metrics.trade_metrics  # noqa: F401
    import bowaka_common.metrics.diagnostics  # noqa: F401
    import bowaka_common.metrics.mfe_mae  # noqa: F401
    import bowaka_common.metrics.bucket_analysis  # noqa: F401
    import bowaka_common.metrics.portfolio_metrics  # noqa: F401
