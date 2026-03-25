"""Generate the public REST screener notebooks for NonKYC and MEXC."""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent
NOTEBOOK_DIR = ROOT / "notebooks"


def md(text: str):
    return nbf.v4.new_markdown_cell(text.strip() + "\n")


def code(text: str):
    return nbf.v4.new_code_cell(text.strip() + "\n")


SETUP_CELL = r'''
import os
import sys
import subprocess
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from IPython.display import display, Markdown

pd.set_option("display.max_columns", 200)
pd.set_option("display.width", 160)
pd.set_option("display.max_colwidth", 120)

CANDIDATE_DIRS = [
    Path("/quants-lab/research_notebooks/market_lab/pmm_dynamic"),
    Path.cwd(),
    Path.cwd().parent,
    Path.cwd().parent.parent,
]
PMM_DIR = next((p.resolve() for p in CANDIDATE_DIRS if (p / "pyproject.toml").exists() and (p / "pmm_lab").exists()), None)
if PMM_DIR is None:
    raise FileNotFoundError("Could not locate the pmm_dynamic project root. Open this notebook from inside the pmm_dynamic repo.")

if str(PMM_DIR) not in sys.path:
    sys.path.insert(0, str(PMM_DIR))
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "-e", str(PMM_DIR), "--quiet"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("pmm_lab").setLevel(logging.WARNING)

print(f"PMM project root: {PMM_DIR}")
'''


CONFIG_TEMPLATE = r'''
# ============================================================
# USER CONFIG — edit these, then Run All
# ============================================================
QUOTE_ASSET = "{quote_asset}"
INTERVAL = "{interval}"
UNIVERSE_TOP_K = {universe_top_k}
FINAL_TOP_N = {final_top_n}
CANDLE_LIMIT = {candle_limit}
DEPTH_LIMIT = {depth_limit}
RECENT_TRADE_LIMIT = {recent_trade_limit}

# Optional pair overrides.
# Keep INCLUDE_SYMBOLS empty to use the full eligible universe.
INCLUDE_SYMBOLS = []
EXCLUDE_SYMBOLS = []

OUTPUT_ROOT = (
    PMM_DIR / "artifacts" / "screener" / "{connector}" /
    datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
)

cfg = default_{connector}_config()
cfg.quote_asset = QUOTE_ASSET
cfg.interval = INTERVAL
cfg.universe_top_k = UNIVERSE_TOP_K
cfg.final_top_n = FINAL_TOP_N
cfg.candle_limit = CANDLE_LIMIT
cfg.depth_limit = DEPTH_LIMIT
cfg.recent_trade_limit = RECENT_TRADE_LIMIT
cfg.include_symbols = tuple(INCLUDE_SYMBOLS)
cfg.exclude_symbols = tuple(EXCLUDE_SYMBOLS)

# Conservative defaults. Loosen only if you explicitly want more exploratory coverage.
cfg.min_quote_volume_24h = {min_quote_volume_24h}
cfg.max_spread_bps = {max_spread_bps}
cfg.min_top_of_book_quote = {min_top_of_book_quote}
cfg.min_depth_10bps_quote = {min_depth_10bps_quote}
cfg.max_last_trade_age_sec = {max_last_trade_age_sec}
cfg.min_recent_trade_count = {min_recent_trade_count}
cfg.min_candle_count = {min_candle_count}
cfg.min_candle_coverage_ratio = {min_candle_coverage_ratio}
cfg.max_zero_volume_fraction = {max_zero_volume_fraction}
cfg.min_natr_bps = {min_natr_bps}
cfg.max_natr_bps = {max_natr_bps}

print("Screener config")
display(pd.Series(cfg.as_dict()).to_frame("value"))
print(f"Output root: {{OUTPUT_ROOT}}")
'''


UNIVERSE_CELL_TEMPLATE = r'''
screener = {screener_class}(cfg)

universe = screener.build_universe()
universe = compute_coarse_scores(universe)
shortlist = select_shortlist(universe, cfg)

summary = pd.DataFrame([
    {{
        "connector": cfg.connector,
        "quote_asset": cfg.quote_asset,
        "interval": cfg.interval,
        "universe_rows": len(universe),
        "shortlist_rows": len(shortlist),
    }}
])
display(summary)

preview_cols = [
    c for c in [
        "trading_pair",
        "exchange_symbol",
        "quote_volume_24h",
        "spread_bps",
        "coarse_score",
        "price_tick_estimate",
        "amount_step_estimate",
        "status_detail",
    ]
    if c in universe.columns
]

display(universe.loc[:, preview_cols].head(20))
print(f"Shortlist for detailed enrichment: {{len(shortlist)}}")
display(shortlist.loc[:, preview_cols].head(min(25, len(shortlist))))
'''


SCREEN_CELL = r'''
run = screener.screen_from_universe(universe)
final_df = run.final.copy()
selected_df = run.selected.copy()

status_counts = pd.DataFrame([
    {
        "enriched_rows": len(final_df),
        "selected_rows": len(selected_df),
        "pass_rate": float(selected_df.shape[0] / final_df.shape[0]) if len(final_df) else 0.0,
    }
])
display(status_counts)

final_cols = [
    c for c in [
        "trading_pair",
        "screen_score",
        "passed_filters",
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
        "rejection_reason",
    ]
    if c in final_df.columns
]
display(final_df.loc[:, final_cols].head(min(50, len(final_df))))
'''


DIAGNOSTICS_CELL = r'''
if final_df.empty:
    print("No enriched rows returned.")
else:
    passed = final_df[final_df["passed_filters"]].copy()
    rejected = final_df[~final_df["passed_filters"]].copy()

    print(f"Passed: {{len(passed)}} | Rejected: {{len(rejected)}}")

    if not passed.empty:
        display(
            passed.loc[:, [
                c for c in [
                    "trading_pair",
                    "screen_score",
                    "quote_volume_24h",
                    "spread_bps",
                    "top_of_book_quote",
                    "sym_depth_quote_10bps",
                    "recent_trade_count",
                    "last_trade_age_sec",
                    "natr_bps_mean",
                    "efficiency_ratio",
                ] if c in passed.columns
            ]].head(cfg.final_top_n)
        )

    if not rejected.empty:
        reject_counts = (
            rejected["rejection_reason"]
            .fillna("")
            .str.split("; ")
            .explode()
            .loc[lambda s: s.ne("")]
            .value_counts()
            .rename_axis("rejection_reason")
            .to_frame("count")
        )
        display(reject_counts.head(20))
'''


EXPORT_CELL_TEMPLATE = r'''
artifact_paths = export_screening_artifacts(
    run,
    output_dir=str(OUTPUT_ROOT),
    base_url={base_url_var},
    trade_limit=cfg.recent_trade_limit,
)

print("Artifacts written")
display(pd.Series(asdict(artifact_paths)).to_frame("path"))
'''


MERGE_CELL = r'''
from pathlib import Path

print("Selected Hummingbot pairs")
print("-" * 80)
print(Path(artifact_paths.selected_pairs_txt).read_text())

print("\nCandle ingestor manifest")
print("-" * 80)
print(Path(artifact_paths.candle_ingestor_manifest_yaml).read_text())

print("\nExchange rules patch (estimates only)")
print("-" * 80)
print(Path(artifact_paths.exchange_rules_patch_yaml).read_text())
'''


def build_notebook(*, connector: str, title: str, screener_class: str, import_line: str, base_url_var: str, public_note: str,
                   quote_asset: str, interval: str, universe_top_k: int, final_top_n: int, candle_limit: int,
                   depth_limit: int, recent_trade_limit: int, min_quote_volume_24h: float, max_spread_bps: float,
                   min_top_of_book_quote: float, min_depth_10bps_quote: float, max_last_trade_age_sec: float,
                   min_recent_trade_count: int, min_candle_count: int, min_candle_coverage_ratio: float,
                   max_zero_volume_fraction: float, min_natr_bps: float, max_natr_bps: float, path: Path) -> None:

    nb = nbf.v4.new_notebook()
    nb.cells = [
        md(f'''
# {title}

This notebook screens **{connector.upper()}** markets for **PMM Dynamic (Predictive Market Making)** using only public market-data endpoints. It is a **pre-ingestion gate**: the output is a ranked shortlist plus a candle-ingestor manifest, selected `BASE-QUOTE` pairs, and rule-estimate metadata.

{public_note}

Stop-ship stance: a pair passing this notebook is **fit for research and ingestion only** until it survives candle-quality checks, walk-forward validation, and live microstructure review.
        '''),
        code(SETUP_CELL + "\n" + import_line),
        md(f'''
## 1. Configuration

Edit the universe, thresholds, and output path here. Keep the defaults conservative unless you explicitly want a wider exploratory net.
        '''),
        code(CONFIG_TEMPLATE.format(
            connector=connector,
            quote_asset=quote_asset,
            interval=interval,
            universe_top_k=universe_top_k,
            final_top_n=final_top_n,
            candle_limit=candle_limit,
            depth_limit=depth_limit,
            recent_trade_limit=recent_trade_limit,
            min_quote_volume_24h=min_quote_volume_24h,
            max_spread_bps=max_spread_bps,
            min_top_of_book_quote=min_top_of_book_quote,
            min_depth_10bps_quote=min_depth_10bps_quote,
            max_last_trade_age_sec=max_last_trade_age_sec,
            min_recent_trade_count=min_recent_trade_count,
            min_candle_count=min_candle_count,
            min_candle_coverage_ratio=min_candle_coverage_ratio,
            max_zero_volume_fraction=max_zero_volume_fraction,
            min_natr_bps=min_natr_bps,
            max_natr_bps=max_natr_bps,
        )),
        md('''
## 2. Build the cheap universe snapshot

This step uses only batch endpoints to discover the broad market universe and assign a coarse score before any per-pair enrichment calls are made.
        '''),
        code(UNIVERSE_CELL_TEMPLATE.format(screener_class=screener_class)),
        md('''
## 3. Run the detailed screener

This step enriches the shortlist with order-book depth, recent trades, and candles, then applies hard gates plus the final PMM-oriented score.
        '''),
        code(SCREEN_CELL),
        md('''
## 4. Diagnostics

Inspect which pairs passed, which pairs failed, and why. Rejection counts are often more useful than raw rankings because they show whether you are liquidity-bound, spread-bound, or data-quality-bound.
        '''),
        code(DIAGNOSTICS_CELL),
        md('''
## 5. Export artifacts

This writes CSV, JSON, a Markdown report, a candle-ingestor manifest, and an exchange-rules patch for the selected pairs.
        '''),
        code(EXPORT_CELL_TEMPLATE.format(base_url_var=base_url_var)),
        md('''
## 6. Merge into candle ingestion

The manifest below follows the same `exchanges -> pairs -> intervals` structure already used by your candle-ingest and candle-gap-repair tooling, with slash-formatted exchange pairs and Hummingbot-normalized selected pair files alongside it.
        '''),
        code(MERGE_CELL),
    ]
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb.metadata["language_info"] = {
        "name": "python",
        "version": "3.12",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Wrote {path}")


if __name__ == "__main__":
    build_notebook(
        connector="nonkyc",
        title="PMM Dynamic Screener — NonKYC Public REST",
        screener_class="NonKYCPublicScreener",
        import_line='''
from pmm_lab.screener import NonKYCPublicScreener, default_nonkyc_config, export_screening_artifacts
from pmm_lab.screener.common import compute_coarse_scores, select_shortlist
from pmm_lab.screener.nonkyc_public import NONKYC_BASE_URL
''',
        base_url_var="NONKYC_BASE_URL",
        public_note="By default this notebook screens **all quote assets** available on NonKYC (USDT, XMR, BTC, USDC, etc.). To restrict to a single quote, set `QUOTE_ASSET` to e.g. `'USDT'`. To screen a specific set, use comma-separated values like `'USDT,XMR'`. The notebook uses the documented public REST endpoints for markets, tickers, order books, candles, and trades.",
        quote_asset="*",
        interval="5m",
        universe_top_k=80,
        final_top_n=15,
        candle_limit=288,
        depth_limit=200,
        recent_trade_limit=500,
        min_quote_volume_24h=50_000.0,
        max_spread_bps=120.0,
        min_top_of_book_quote=5.0,
        min_depth_10bps_quote=0.0,
        max_last_trade_age_sec=3600.0,
        min_recent_trade_count=40,
        min_candle_count=220,
        min_candle_coverage_ratio=0.90,
        max_zero_volume_fraction=0.30,
        min_natr_bps=12.0,
        max_natr_bps=400.0,
        path=NOTEBOOK_DIR / "pmm_dynamic_screener_nonkyc_public.ipynb",
    )

    build_notebook(
        connector="mexc",
        title="PMM Dynamic Screener — MEXC Public REST",
        screener_class="MEXCPublicScreener",
        import_line='''
from pmm_lab.screener import MEXCPublicScreener, default_mexc_config, export_screening_artifacts
from pmm_lab.screener.common import compute_coarse_scores, select_shortlist
from pmm_lab.screener.mexc_public import MEXC_BASE_URL
''',
        base_url_var="MEXC_BASE_URL",
        public_note="This notebook is **public-data only**. It uses unauthenticated MEXC spot market endpoints and does not require or send any account credentials.",
        quote_asset="USDT",
        interval="5m",
        universe_top_k=100,
        final_top_n=30,
        candle_limit=288,
        depth_limit=200,
        recent_trade_limit=500,
        min_quote_volume_24h=1_000_000.0,
        max_spread_bps=50.0,
        min_top_of_book_quote=250.0,
        min_depth_10bps_quote=1_000.0,
        max_last_trade_age_sec=1800.0,
        min_recent_trade_count=100,
        min_candle_count=240,
        min_candle_coverage_ratio=0.97,
        max_zero_volume_fraction=0.20,
        min_natr_bps=10.0,
        max_natr_bps=250.0,
        path=NOTEBOOK_DIR / "pmm_dynamic_screener_mexc_public.ipynb",
    )
''
