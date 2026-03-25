"""Artifact export helpers for public market screeners."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import pandas as pd
import yaml

from pmm_lab.screener.common import ScreeningRun, hb_to_slash_pair, json_ready_records, now_utc_iso


@dataclass(frozen=True)
class ScreenerArtifactPaths:
    root_dir: str
    universe_csv: str
    shortlist_csv: str
    final_csv: str
    selected_csv: str
    selected_pairs_txt: str
    selected_pairs_json: str
    symbol_metadata_json: str
    candle_ingestor_manifest_yaml: str
    exchange_rules_patch_yaml: str
    screening_report_md: str
    run_metadata_json: str



def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)



def _write_json(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=False)



def _selected_pairs(run: ScreeningRun) -> list[str]:
    if run.selected is None or run.selected.empty:
        return []
    return [str(v) for v in run.selected["trading_pair"].tolist()]



def build_candle_ingestor_manifest(
    run: ScreeningRun,
    base_url: str,
    trade_limit: int,
    recent_window_minutes: int = 120,
    include_open_candle: bool = False,
    backfill_days: int = 180,
    request_delay: float = 0.5,
    overlap_candles: int = 2,
) -> dict[str, Any]:
    pairs = [hb_to_slash_pair(p) for p in _selected_pairs(run)]
    return {
        "backfill_days": int(backfill_days),
        "request_delay": float(request_delay),
        "overlap_candles": int(overlap_candles),
        "include_open_candle": bool(include_open_candle),
        "http": {
            "timeout_seconds": float(run.config.timeout_seconds),
            "max_retries": int(run.config.max_retries),
            "retry_backoff": float(run.config.retry_backoff),
            "user_agent": run.config.user_agent,
        },
        "exchanges": {
            run.connector: {
                "enabled": True,
                "base_url": base_url,
                "pairs": pairs,
                "intervals": [run.config.interval],
                "trades": {
                    "enabled": True,
                    "limit": int(trade_limit),
                    "update_recent_candles": False,
                    "recent_window_minutes": int(recent_window_minutes),
                },
            }
        },
    }



def build_exchange_rules_patch(run: ScreeningRun) -> dict[str, Any]:
    pairs: dict[str, Any] = {}
    if run.selected is None or run.selected.empty:
        return {"connectors": {run.connector: {"pairs": pairs}}}

    for _, row in run.selected.iterrows():
        pair = str(row["trading_pair"])
        payload: dict[str, Any] = {}
        for src, dest in (
            ("price_tick_estimate", "price_tick"),
            ("amount_step_estimate", "amount_step"),
            ("min_notional_quote_estimate", "min_notional_quote"),
            ("min_order_size_base_estimate", "min_order_size_base"),
        ):
            value = row.get(src)
            if pd.notna(value):
                payload[dest] = float(value)
        if payload:
            pairs[pair] = payload
    return {"connectors": {run.connector: {"pairs": pairs}}}



def build_symbol_metadata(run: ScreeningRun) -> list[dict[str, Any]]:
    if run.selected is None or run.selected.empty:
        return []

    keep_cols = [
        "connector",
        "exchange_symbol",
        "trading_pair",
        "base_asset",
        "quote_asset",
        "quote_volume_24h",
        "spread_bps",
        "top_of_book_quote",
        "sym_depth_quote_10bps",
        "recent_trade_count",
        "last_trade_age_sec",
        "n_candles",
        "coverage_ratio",
        "zero_volume_fraction",
        "natr_bps_mean",
        "efficiency_ratio",
        "screen_score",
        "price_tick_estimate",
        "amount_step_estimate",
        "min_notional_quote_estimate",
        "min_order_size_base_estimate",
        "rule_estimate_source",
        "status_detail",
    ]
    cols = [c for c in keep_cols if c in run.selected.columns]
    return json_ready_records(run.selected.loc[:, cols])



def build_screening_report(run: ScreeningRun) -> str:
    lines: list[str] = []
    lines.append(f"# {run.connector.upper()} Public Screener Report")
    lines.append("")
    lines.append(f"Generated: {run.finished_at}")
    lines.append("")
    lines.append("## Objective")
    lines.append("")
    lines.append(
        "Shortlist markets for PMM Dynamic research and candle ingestion using public market-data endpoints only."
    )
    lines.append("")
    lines.append("## Stop-Ship Notes")
    lines.append("")
    lines.append("- This is an ingestion/research gate, not a live-trading approval.")
    lines.append("- Passing markets still need post-ingestion audit, walk-forward validation, and live microstructure checks.")
    lines.append("- Exchange rule fields are exported as estimates when the API does not expose exact tick/step filters.")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- Universe: {len(run.universe)}")
    lines.append(f"- Shortlist: {len(run.shortlist)}")
    lines.append(f"- Enriched: {len(run.final)}")
    lines.append(f"- Selected: {len(run.selected)}")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append("```yaml")
    lines.append(yaml.safe_dump(run.config.as_dict(), sort_keys=True).rstrip())
    lines.append("```")
    lines.append("")
    lines.append("## Top Selected Pairs")
    lines.append("")
    if run.selected is None or run.selected.empty:
        lines.append("No markets passed the configured gates.")
    else:
        cols = [c for c in ["trading_pair", "screen_score", "quote_volume_24h", "spread_bps", "sym_depth_quote_10bps", "natr_bps_mean"] if c in run.selected.columns]
        preview = run.selected.loc[:, cols].copy()
        lines.append(preview.to_markdown(index=False))
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    for note in run.notes:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)



def export_screening_artifacts(
    run: ScreeningRun,
    output_dir: str,
    base_url: str,
    trade_limit: int,
    recent_window_minutes: int = 120,
) -> ScreenerArtifactPaths:
    root = Path(output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    paths = {
        "universe_csv": root / "universe.csv",
        "shortlist_csv": root / "shortlist.csv",
        "final_csv": root / "final_screen.csv",
        "selected_csv": root / "selected_pairs.csv",
        "selected_pairs_txt": root / "selected_pairs.txt",
        "selected_pairs_json": root / "selected_pairs.json",
        "symbol_metadata_json": root / "symbol_metadata.json",
        "candle_ingestor_manifest_yaml": root / "candle_ingestor_manifest.yaml",
        "exchange_rules_patch_yaml": root / "exchange_rules_patch.yaml",
        "screening_report_md": root / "screening_report.md",
        "run_metadata_json": root / "run_metadata.json",
    }

    _write_csv(run.universe, paths["universe_csv"])
    _write_csv(run.shortlist, paths["shortlist_csv"])
    _write_csv(run.final, paths["final_csv"])
    _write_csv(run.selected, paths["selected_csv"])

    selected_pairs = _selected_pairs(run)
    paths["selected_pairs_txt"].write_text("\n".join(selected_pairs) + ("\n" if selected_pairs else ""), encoding="utf-8")
    _write_json(selected_pairs, paths["selected_pairs_json"])
    _write_json(build_symbol_metadata(run), paths["symbol_metadata_json"])

    manifest = build_candle_ingestor_manifest(
        run,
        base_url=base_url,
        trade_limit=trade_limit,
        recent_window_minutes=recent_window_minutes,
    )
    paths["candle_ingestor_manifest_yaml"].write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )

    rules_patch = build_exchange_rules_patch(run)
    paths["exchange_rules_patch_yaml"].write_text(
        yaml.safe_dump(rules_patch, sort_keys=False), encoding="utf-8"
    )

    report_text = build_screening_report(run)
    paths["screening_report_md"].write_text(report_text, encoding="utf-8")

    metadata = run.metadata()
    metadata["exported_at"] = now_utc_iso()
    metadata["artifact_paths"] = {k: str(v) for k, v in paths.items()}
    _write_json(metadata, paths["run_metadata_json"])

    return ScreenerArtifactPaths(
        root_dir=str(root),
        universe_csv=str(paths["universe_csv"]),
        shortlist_csv=str(paths["shortlist_csv"]),
        final_csv=str(paths["final_csv"]),
        selected_csv=str(paths["selected_csv"]),
        selected_pairs_txt=str(paths["selected_pairs_txt"]),
        selected_pairs_json=str(paths["selected_pairs_json"]),
        symbol_metadata_json=str(paths["symbol_metadata_json"]),
        candle_ingestor_manifest_yaml=str(paths["candle_ingestor_manifest_yaml"]),
        exchange_rules_patch_yaml=str(paths["exchange_rules_patch_yaml"]),
        screening_report_md=str(paths["screening_report_md"]),
        run_metadata_json=str(paths["run_metadata_json"]),
    )
