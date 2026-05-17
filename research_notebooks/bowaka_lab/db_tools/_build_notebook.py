"""Build db_tools/bowaka_backfill.ipynb programmatically.

This file is intentionally separate from the notebook itself so the notebook
content lives in a single editable source. Re-run after changes.
"""

from __future__ import annotations

from pathlib import Path

import nbformat

HERE = Path(__file__).resolve().parent
NB_PATH = HERE / "bowaka_backfill.ipynb"


TITLE_OVERVIEW = """# Bowaka Backfill (standalone)

This notebook backfills Alpaca equities data (asset universe, daily bars, 1-minute
bars) into the storage layout that Bowaka Lab Phase 2 will consume *without
re-fetching*. It is intentionally standalone: it does not import from
`bowaka_lab.*` — all helpers live in `db_tools/_backfill_lib.py`.

What it produces:

- `{out_dir}/parquet/assets/...` — asset snapshot per `[Report §8.5]`
- `{out_dir}/parquet/bars/feed=.../timeframe=1d/...` — daily bars per `[Report §8.3]`
- `{out_dir}/parquet/bars/feed=.../timeframe=1m/...` — minute bars per `[Report §8.3]`
- `{out_dir}/scope/...` — Scope 3 (universe-gate-passers per session) with
  no-lookahead ADV per `[Report §11.4]`
- `{out_dir}/manifest.json` — counts + dataset hashes
- Mongo: `bowaka_asset_snapshots`, `bowaka_assets`, `bowaka_data_ingestion_runs`,
  `bowaka_daily_bar_audits` per `[Report §8.5]` with indexes per `[Report §8.6]`

Daily audits follow `[Report §16.1]`. IEX vs SIP volume warnings: `[Report §27.1]`.
"""


PREREQS = """## Prerequisites

`.env` (at `research_notebooks/bowaka_lab/.env` preferred, repo root accepted):

```
ALPACA_API_KEY_ID=...
ALPACA_API_SECRET_KEY=...
MONGO_URI=mongodb://...
# optional:
MONGO_DATABASE=bowaka_lab
ALPACA_PAPER=true
```

Mongo must be reachable. The default `make run-db` from the quants-lab root counts.
"""


IMPORTS = '''import os, sys, json, logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Make db_tools importable when the notebook runs from research_notebooks/bowaka_lab
# without an editable install yet.
_HERE = Path.cwd().resolve()
_BOWAKA_ROOT = _HERE
while _BOWAKA_ROOT != _BOWAKA_ROOT.parent and not (_BOWAKA_ROOT / "db_tools" / "_backfill_lib.py").exists():
    _BOWAKA_ROOT = _BOWAKA_ROOT.parent
if str(_BOWAKA_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOWAKA_ROOT))

from db_tools import _backfill_lib as lib
print("db_tools loaded from", _BOWAKA_ROOT / "db_tools")
'''


PARAMETERS = '''# --- Time window ----------------------------------------
START_DATE = "2024-12-01"           # first session_date in scope 3
END_DATE   = "2026-05-15"           # last session_date

# --- Feed -----------------------------------------------
FEED = "iex"                        # "iex" (free, single-exchange) or "sip" (subscription)

# --- Universe gates (Scope 3) ---------------------------
PRICE_MIN          = 1.0
PRICE_MAX          = 20.0
ADV_MIN            = 200_000.0      # LOWER for IEX (~10-20x lower volume than SIP)
ADV_WINDOW_DAYS    = 20

# --- Universe filters -----------------------------------
ALLOWED_EXCHANGES  = ["NASDAQ", "NYSE", "ARCA", "AMEX", "BATS"]

# --- Storage --------------------------------------------
OUTPUT_DIR         = "./bowaka_data"  # relative or absolute; can be a 100 GB volume mount

# --- Rate limiting / batching ---------------------------
RATE_LIMIT_RPM     = 180              # Alpaca Basic plan caps at 200
SYMBOL_BATCH_SIZE  = 200

# --- Mongo ----------------------------------------------
WRITE_TO_MONGO     = True
MONGO_DATABASE     = None             # None -> use $MONGO_DATABASE env (default "bowaka_lab")

# --- Behavior -------------------------------------------
RESUME             = True             # skip files that already exist

# --- Stage control --------------------------------------
RUN_SMOKE          = True
RUN_ESTIMATE       = True
RUN_ASSETS         = True
RUN_DAILY          = True
RUN_SCOPE          = True
RUN_MINUTE         = True
RUN_AUDITS         = True
RUN_MANIFEST       = True
'''


LOAD_CONFIG = '''loaded = lib.find_and_load_dotenv()
env = lib.resolve_env()
cfg = lib.BackfillConfig(
    api_key=env["ALPACA_API_KEY_ID"],
    api_secret=env["ALPACA_API_SECRET_KEY"],
    paper=env["ALPACA_PAPER"],
    feed=FEED,
    start_date=date.fromisoformat(START_DATE),
    end_date=date.fromisoformat(END_DATE),
    out_dir=Path(OUTPUT_DIR).expanduser().resolve(),
    mongo_uri=env["MONGO_URI"] if WRITE_TO_MONGO else None,
    mongo_database=MONGO_DATABASE or env["MONGO_DATABASE"],
    write_to_mongo=WRITE_TO_MONGO,
    price_min=PRICE_MIN, price_max=PRICE_MAX,
    adv_min=ADV_MIN, adv_window_days=ADV_WINDOW_DAYS,
    rate_limit_rpm=RATE_LIMIT_RPM,
    allowed_exchanges=tuple(ALLOWED_EXCHANGES),
    exclude_name_pattern=lib.DEFAULT_EXCLUDE_NAME_PATTERN,
    batch_size_symbols=SYMBOL_BATCH_SIZE,
    resume=RESUME,
)
print(f".env loaded from: {loaded}")
print(f"out_dir:          {cfg.out_dir}")
print(f"feed:             {cfg.feed} (paper={cfg.paper})")
print(f"window:           {cfg.start_date} -> {cfg.end_date}")
print(f"daily fetch:      from {cfg.daily_fetch_start} (ADV warmup pad)")
print(f"mongo:            {'enabled (' + cfg.mongo_database + ')' if cfg.write_to_mongo else 'disabled'}")
'''


LOGGER_AND_MONGO = '''cfg.out_dir.mkdir(parents=True, exist_ok=True)
log_path = cfg.out_dir / "backfill.log"

log = logging.getLogger("bowaka_backfill")
log.setLevel(logging.INFO)
for h in list(log.handlers):
    log.removeHandler(h)
log.addHandler(logging.StreamHandler())
log.addHandler(logging.FileHandler(log_path, encoding="utf-8"))
log.propagate = False
log.info("bowaka backfill started; feed=%s window=%s..%s", cfg.feed, cfg.start_date, cfg.end_date)

limiter = lib.RateLimiter(rpm=cfg.rate_limit_rpm)

mongo_client = None
db = None
if cfg.write_to_mongo:
    mongo_client = lib.get_mongo_client(cfg.mongo_uri)
    db = mongo_client[cfg.mongo_database]
    lib.apply_indexes(db)
    print(f"Mongo connected; indexes applied to {cfg.mongo_database}.")
else:
    print("Mongo writes disabled.")
'''


SMOKE = '''if RUN_SMOKE:
    result = lib.run_smoke_test(cfg, log)
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        if result.get("feed_403"):
            print()
            print("WARNING: SIP feed not authorized on this account. Re-run with FEED = 'iex'.")
        else:
            print()
            print("WARNING: Smoke test failed; resolve before running stages.")
else:
    print("RUN_SMOKE is False; skipping.")
'''


ESTIMATE = '''if RUN_ESTIMATE:
    proj = lib.estimate_storage_and_time(cfg)
    df_est = pd.DataFrame([{"metric": k, "value": v} for k, v in proj.items()])
    try:
        from IPython.display import display
        display(df_est)
    except Exception:
        print(df_est.to_string(index=False))
else:
    print("RUN_ESTIMATE is False; skipping.")
'''


STAGE_ASSETS = '''snapshot_id = None
kept_df = None
if RUN_ASSETS:
    snapshot_id, kept_df = lib.fetch_assets(cfg, log)
    print(f"snapshot_id: {snapshot_id}")
    print(f"kept assets: {kept_df.shape[0]}")
    try:
        from IPython.display import display
        display(kept_df.head())
    except Exception:
        print(kept_df.head().to_string(index=False))
    if cfg.write_to_mongo:
        lib.write_asset_snapshot_to_mongo(db, snapshot_id, kept_df, cfg)
        print(f"Wrote snapshot + {kept_df.shape[0]} assets to Mongo.")
else:
    print("RUN_ASSETS is False; skipping.")
'''


STAGE_DAILY = '''if RUN_DAILY:
    if kept_df is None or kept_df.empty:
        raise RuntimeError("kept_df not loaded; rerun Stage 1 or set RUN_ASSETS=True.")
    ingest_run_id = f"ingest_{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}_{cfg.feed}_1d_{cfg.adjustment}"
    stats = lib.fetch_daily_bars(cfg, kept_df, log, limiter)
    dataset_hash = lib.compute_dataset_hash(lib.daily_root(cfg))
    record = {
        "ingestion_run_id": ingest_run_id,
        "vendor": "alpaca",
        "feed": cfg.feed,
        "timeframe": "1d",
        "adjustment": cfg.adjustment,
        "start": cfg.daily_fetch_start.isoformat(),
        "end": cfg.end_date.isoformat(),
        "symbol_count_requested": stats["symbols_requested"],
        "symbol_count_success": stats["symbols_written"],
        "symbol_count_failed": stats["symbols_failed"],
        "api_call_count": stats["api_call_count_est"],
        "rate_limit_policy": f"{cfg.rate_limit_rpm}_rpm_basic_safe",
        "dataset_hash": dataset_hash,
        "parquet_root": str(lib.daily_root(cfg)),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if cfg.write_to_mongo:
        lib.write_ingestion_run_to_mongo(db, record)
    print(json.dumps(stats, indent=2))
    print(f"dataset_hash: {dataset_hash}")
else:
    print("RUN_DAILY is False; skipping.")
'''


STAGE_SCOPE = '''scope_df = None
if RUN_SCOPE:
    scope_df = lib.compute_scope_3(cfg, log)
    n_sessions = scope_df["session_date"].nunique() if not scope_df.empty else 0
    n_pairs = scope_df.shape[0]
    avg_per_session = n_pairs / max(1, n_sessions)
    print(f"sessions: {n_sessions}")
    print(f"pairs:    {n_pairs}")
    print(f"avg sym/session: {avg_per_session:.1f}")
    if not scope_df.empty:
        # No-lookahead invariant: smallest session_date must be >= start_date.
        assert scope_df["session_date"].min() >= cfg.start_date, "scope leaked sessions before start_date"
        try:
            from IPython.display import display
            counts = scope_df.groupby("session_date").size().describe()
            display(counts.to_frame("symbols_per_session"))
        except Exception:
            pass
else:
    print("RUN_SCOPE is False; skipping.")
'''


STAGE_MINUTE = '''if RUN_MINUTE:
    if scope_df is None or scope_df.empty:
        raise RuntimeError("scope_df not loaded; rerun Stage 3.")
    ingest_run_id = f"ingest_{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}_{cfg.feed}_1m_{cfg.adjustment}"
    stats = lib.fetch_minute_bars(cfg, scope_df, log, limiter)
    dataset_hash = lib.compute_dataset_hash(lib.minute_root(cfg))
    record = {
        "ingestion_run_id": ingest_run_id,
        "vendor": "alpaca",
        "feed": cfg.feed,
        "timeframe": "1m",
        "adjustment": cfg.adjustment,
        "start": cfg.start_date.isoformat(),
        "end": cfg.end_date.isoformat(),
        "symbol_count_requested": stats["pairs_requested"],
        "symbol_count_success": stats["pairs_written"],
        "symbol_count_failed": stats["batches_failed"],
        "api_call_count": stats["pairs_requested"] // max(1, cfg.batch_size_symbols),
        "rate_limit_policy": f"{cfg.rate_limit_rpm}_rpm_basic_safe",
        "dataset_hash": dataset_hash,
        "parquet_root": str(lib.minute_root(cfg)),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if cfg.write_to_mongo:
        lib.write_ingestion_run_to_mongo(db, record)
    print(json.dumps(stats, indent=2))
    print(f"dataset_hash: {dataset_hash}")
else:
    print("RUN_MINUTE is False; skipping.")
'''


STAGE_AUDITS = '''if RUN_AUDITS:
    audits_df = lib.audit_daily_bars(cfg, log)
    if audits_df.empty:
        print("no audits produced (empty daily root)")
    else:
        print(audits_df["passed_research_audit"].value_counts())
        print("total ohlc_violations:", int(audits_df["ohlc_violations"].sum()))
        print("total duplicate_sessions:", int(audits_df["duplicate_sessions"].sum()))
        worst_missing = audits_df.sort_values("missing_sessions", ascending=False).head(10)
        try:
            from IPython.display import display
            display(worst_missing[["symbol", "expected_sessions", "observed_sessions", "missing_sessions"]])
        except Exception:
            print(worst_missing[["symbol", "expected_sessions", "observed_sessions", "missing_sessions"]].to_string(index=False))
        if cfg.write_to_mongo:
            lib.write_daily_audits_to_mongo(db, audits_df, cfg)
            print(f"wrote {audits_df.shape[0]} audit rows to Mongo")
else:
    print("RUN_AUDITS is False; skipping.")
'''


STAGE_MANIFEST = '''if RUN_MANIFEST:
    counts = {
        "snapshot_id": snapshot_id,
        "kept_assets": int(kept_df.shape[0]) if kept_df is not None else 0,
        "scope_pairs": int(scope_df.shape[0]) if scope_df is not None else 0,
    }
    dataset_hashes = {
        "daily_bars": lib.compute_dataset_hash(lib.daily_root(cfg)),
        "minute_bars": lib.compute_dataset_hash(lib.minute_root(cfg)),
    }
    manifest_path = lib.write_manifest_json(cfg, counts, dataset_hashes)
    print(f"manifest: {manifest_path}")
    print(manifest_path.read_text())
else:
    print("RUN_MANIFEST is False; skipping.")
'''


SUMMARY = '''manifest_path = lib.manifest_file(cfg)
summary_rows = []
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    summary_rows.append({"item": "manifest", "value": str(manifest_path)})
    for k, v in manifest.get("counts", {}).items():
        summary_rows.append({"item": f"count.{k}", "value": v})
    for k, v in manifest.get("dataset_hashes", {}).items():
        summary_rows.append({"item": f"hash.{k}", "value": v})

daily_count = len(list(lib.daily_root(cfg).rglob("part.parquet"))) if lib.daily_root(cfg).exists() else 0
minute_count = len(list(lib.minute_root(cfg).rglob("*.parquet"))) if lib.minute_root(cfg).exists() else 0
summary_rows.append({"item": "files.daily", "value": daily_count})
summary_rows.append({"item": "files.minute", "value": minute_count})

if cfg.write_to_mongo and db is not None:
    for coll in ("bowaka_asset_snapshots", "bowaka_assets", "bowaka_data_ingestion_runs", "bowaka_daily_bar_audits"):
        summary_rows.append({"item": f"mongo.{coll}", "value": int(db[coll].count_documents({}))})

summary_df = pd.DataFrame(summary_rows)
try:
    from IPython.display import display
    display(summary_df)
except Exception:
    print(summary_df.to_string(index=False))

if daily_count == 0:
    print("WARNING: zero daily files on disk")
if minute_count == 0 and 'scope_df' in dir() and scope_df is not None and not scope_df.empty:
    print("WARNING: zero minute files but scope_df is non-empty")

if mongo_client is not None:
    mongo_client.close()
'''


def _code(source: str, tag: str | None = None) -> nbformat.NotebookNode:
    cell = nbformat.v4.new_code_cell(source)
    if tag is not None:
        cell.metadata["tags"] = [tag]
    return cell


def main() -> None:
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_markdown_cell(TITLE_OVERVIEW),
        nbformat.v4.new_markdown_cell(PREREQS),
        _code(IMPORTS),
        _code(PARAMETERS, tag="parameters"),
        _code(LOAD_CONFIG),
        _code(LOGGER_AND_MONGO),
        nbformat.v4.new_markdown_cell("## Smoke test (run this first)"),
        _code(SMOKE, tag="smoke"),
        nbformat.v4.new_markdown_cell("## Estimate before running stages"),
        _code(ESTIMATE, tag="estimate"),
        nbformat.v4.new_markdown_cell("## Stage 1: Asset snapshot"),
        _code(STAGE_ASSETS, tag="stage_assets"),
        nbformat.v4.new_markdown_cell("## Stage 2: Daily bars (full kept universe)"),
        _code(STAGE_DAILY, tag="stage_daily"),
        nbformat.v4.new_markdown_cell("## Stage 3: Scope 3 (universe-gate-passers per session)"),
        _code(STAGE_SCOPE, tag="stage_scope"),
        nbformat.v4.new_markdown_cell("## Stage 4: Minute bars for scope-3 pairs"),
        _code(STAGE_MINUTE, tag="stage_minute"),
        nbformat.v4.new_markdown_cell("## Stage 5: Daily-bar quality audits (Report 16.1)"),
        _code(STAGE_AUDITS, tag="stage_audits"),
        nbformat.v4.new_markdown_cell("## Stage 6: Manifest"),
        _code(STAGE_MANIFEST, tag="stage_manifest"),
        nbformat.v4.new_markdown_cell("## Summary & verification"),
        _code(SUMMARY, tag="summary"),
    ]
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.metadata["language_info"] = {"name": "python", "version": "3.12"}
    nbformat.write(nb, NB_PATH)
    print(f"wrote {NB_PATH}")


if __name__ == "__main__":
    main()
