"""Bundler writes every required file; missing inputs → raises."""
from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_v2_lab.promotion.bundler import REQUIRED_BUNDLE_FILES, bundle_review_package


def _make_full_run_dir(rd: Path) -> None:
    rd.mkdir(parents=True, exist_ok=True)
    for fname in REQUIRED_BUNDLE_FILES:
        (rd / fname).write_text("stub content", encoding="utf-8")


def test_bundle_copies_required_files(tmp_path: Path) -> None:
    src = tmp_path / "src_run"
    _make_full_run_dir(src)
    out = bundle_review_package(
        source_run_dir=src,
        promotion_root=tmp_path / "promo",
        run_id="test_rid",
    )
    for fname in REQUIRED_BUNDLE_FILES:
        assert (out / fname).is_file()


def test_bundle_raises_on_missing_required(tmp_path: Path) -> None:
    src = tmp_path / "src_run"
    src.mkdir()
    (src / "summary.json").write_text("{}")  # only one file
    with pytest.raises(FileNotFoundError):
        bundle_review_package(source_run_dir=src, promotion_root=tmp_path / "promo")


def test_bundle_copies_optional_when_present(tmp_path: Path) -> None:
    src = tmp_path / "src_run"
    _make_full_run_dir(src)
    (src / "optuna_report.md").write_text("# opt", encoding="utf-8")
    out = bundle_review_package(source_run_dir=src, promotion_root=tmp_path / "promo")
    assert (out / "optuna_report.md").is_file()
