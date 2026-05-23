"""Phase 9 — the Phase-9 typed importer refuses to fabricate paper data.

The Phase-9 ``import_paper_event_logs`` reader is the strict-typed entry
point used by the slippage / OCO-latency calibrators (which can't operate on
a fabricated session). When no paper-logs root resolves it raises
:class:`PaperLogsNotFoundError` with a clear, non-zero message.

The CLI's ``reconcile`` subcommand has a SEPARATE contract: it writes a
``scaffolding_only`` report and exits 0 (proven by the existing Phase-10
``test_reconcile_cli_missing_paper_logs`` test). This test pins the strict
Phase-9 reader path so the calibrators never silently fabricate data.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_v2_lab.reconcile.importer import (
    PaperLogsNotFoundError,
    import_paper_event_logs,
    resolve_paper_logs_root,
)


def test_typed_reader_raises_when_no_path_and_no_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No path AND no env var → :class:`PaperLogsNotFoundError`."""
    monkeypatch.delenv("BOWAKA_V2_PAPER_LOGS_ROOT", raising=False)
    with pytest.raises(PaperLogsNotFoundError) as exc:
        import_paper_event_logs(None)
    assert "BOWAKA_V2_PAPER_LOGS_ROOT" in str(exc.value)


def test_typed_reader_raises_on_non_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pointing at a file (not a directory) raises with a clear message."""
    monkeypatch.delenv("BOWAKA_V2_PAPER_LOGS_ROOT", raising=False)
    f = tmp_path / "not-a-dir"
    f.write_text("hello", encoding="utf-8")
    with pytest.raises(PaperLogsNotFoundError) as exc:
        import_paper_event_logs(f)
    assert "not a directory" in str(exc.value).lower()


def test_resolve_helper_propagates_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """:func:`resolve_paper_logs_root` raises the same error class."""
    monkeypatch.delenv("BOWAKA_V2_PAPER_LOGS_ROOT", raising=False)
    with pytest.raises(PaperLogsNotFoundError):
        resolve_paper_logs_root(None)


def test_typed_reader_never_fabricates_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A completely empty directory yields an empty result, never fake data."""
    monkeypatch.delenv("BOWAKA_V2_PAPER_LOGS_ROOT", raising=False)
    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    result = import_paper_event_logs(empty_root)
    # Importer never fabricates rows — every event list is empty.
    assert result.n_events == 0
    for kind, evs in result.events_by_kind.items():
        assert evs == [], kind
    # And no spurious drift issues either.
    assert result.drift_issues == []
