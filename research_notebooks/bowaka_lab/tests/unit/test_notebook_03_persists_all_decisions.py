"""Phase fidelity-2: notebook 03 builder writes ``paths.all_decisions``."""

from __future__ import annotations

from pathlib import Path

BUILDER = (
    Path(__file__).resolve().parents[2]
    / "notebooks"
    / "_build_03_prefilter_replay.py"
)


def test_builder_imports_load_latest_asset_snapshot():
    src = BUILDER.read_text(encoding="utf-8")
    assert "load_latest_asset_snapshot" in src, (
        "Builder must import load_latest_asset_snapshot to populate the snapshot."
    )


def test_builder_passes_asset_snapshot_to_replay():
    src = BUILDER.read_text(encoding="utf-8")
    assert "asset_snapshot=asset_snapshot" in src, (
        "replay_prefilter_over_window must receive the asset snapshot."
    )


def test_builder_writes_all_decisions_artifact():
    src = BUILDER.read_text(encoding="utf-8")
    assert "paths.all_decisions" in src, "Builder must persist paths.all_decisions"
    # Must come from save_parquet, not bare pd.to_parquet
    assert "save_parquet(paths.all_decisions" in src


def test_builder_lineage_tags_candidates_and_decisions():
    src = BUILDER.read_text(encoding="utf-8")
    # Lineage columns added to BOTH candidates_df and all_decisions_df
    for col in ("config_hash", "data_feed", "asset_snapshot_id"):
        assert col in src, f"Builder must lineage-tag with {col!r}"


def test_artifact_paths_exposes_all_decisions(tmp_path):
    from bowaka_lab.utils import ArtifactPaths

    paths = ArtifactPaths.for_run("rid", tmp_path)
    assert paths.all_decisions.name == "all_decisions.parquet"
    assert paths.all_decisions.parent == paths.root
