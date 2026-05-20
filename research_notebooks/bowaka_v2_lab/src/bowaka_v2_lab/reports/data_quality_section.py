"""Render the data-quality section of the run report."""
from __future__ import annotations

import json
from pathlib import Path


def render_data_quality_section(run_dir: Path) -> str:
    out_lines = ["## Data Quality"]
    dq_path = Path(run_dir) / "data_quality_report.json"
    if dq_path.is_file():
        dq = json.loads(dq_path.read_text(encoding="utf-8"))
        out_lines.append(f"- schema_version: {dq.get('schema_version')}")
        out_lines.append(f"- notes: {dq.get('notes', '')}")
    else:
        out_lines.append("- (no data_quality_report.json found)")
    ds_path = Path(run_dir) / "dataset_manifest.json"
    if ds_path.is_file():
        ds = json.loads(ds_path.read_text(encoding="utf-8"))
        out_lines.append(f"- dataset.provider: {ds.get('provider')}")
        out_lines.append(f"- dataset.feed: {ds.get('feed')}")
        out_lines.append(f"- dataset.bar_count: {ds.get('bar_count')}")
        out_lines.append(f"- dataset.symbol_count: {len(ds.get('symbols', []))}")
    return "\n".join(out_lines)
