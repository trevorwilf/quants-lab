# Data lake layout — feeds, paths, and SIP scaffolding

**Status:** scaffolding (realism remediation 2 Phase 10). The IEX-feed
partitions ship in the lake today; the SIP-feed partitions are documented
here and reserved by the layout helpers in `bowaka_common.marketdata.layout`,
but the SIP ingestion stage has not run. A `feed: sip` config that runs
against this lake will fail preflight with `sip_data_absent` and point back
at this document.

The canonical layout is owned by `bowaka_common.marketdata.layout`. Both
labs (`bowaka_lab`, `bowaka_v2_lab`) read through `MarketDataStore` and write
through `run_backfill`; nothing else constructs paths directly.

## Lake root

The lake root is resolved by `bowaka_common.marketdata.resolve_market_data_root`:

1. Explicit argument (e.g. `MarketDataStore(root="...")`).
2. The `MARKET_DATA_ROOT` environment variable.
3. The in-repo default: `<repo_root>/research_notebooks/market_data`.

## Partition hierarchy

Every dataset lives under `<root>/`:

```
bars/vendor=<v>/feed=<f>/timeframe=1d/adjustment=<a>/symbol=<SYM>/part.parquet
bars/vendor=<v>/feed=<f>/timeframe=1m/adjustment=<a>/symbol=<SYM>/year=<YYYY>/month=<MM>/part.parquet
quotes/vendor=<v>/feed=<f>/symbol=<SYM>/year=<YYYY>/month=<MM>/part.parquet
statuses/vendor=<v>/symbol=<SYM>/date=<YYYY-MM-DD>/part.parquet
corporate_actions/vendor=<v>/symbol=<SYM>/part.parquet
assets/vendor=<v>/snapshot_id=<id>/assets.parquet
_ingestion/manifest.json
_ingestion/runs/<run_id>.json
_ingestion/audits/<audit_run_id>.parquet
```

Daily bars are one file per symbol. Minute bars and quotes are grouped per
symbol/month — far fewer files than per-session, fast range scans. Status
partitions are per-symbol/date because halt / LULD / status data is session-
local.

## Feeds

The layout supports any `feed` value. Today two are in use:

| Feed | Tape coverage | Lab use today | Notes |
|------|---------------|---------------|-------|
| `iex` | Partial tape (IEX exchange only) | Lake has IEX bars; quotes not ingested yet | Capped at `suitability_tier: research_only` (audit §P1-010); IEX RVOL / range_expansion / ADV are IEX-specific and NOT consolidated |
| `sip` | Consolidated tape (NBBO) | Lake is empty for SIP | Required for any `simulation.mode: intended_realism` study that targets paper / live |

## IEX partition paths (in use today)

```
bars/vendor=alpaca/feed=iex/timeframe=1d/adjustment=raw/symbol=<SYM>/part.parquet
bars/vendor=alpaca/feed=iex/timeframe=1m/adjustment=raw/symbol=<SYM>/year=<YYYY>/month=<MM>/part.parquet
quotes/vendor=alpaca/feed=iex/symbol=<SYM>/year=<YYYY>/month=<MM>/part.parquet
statuses/vendor=alpaca/symbol=<SYM>/date=<YYYY-MM-DD>/part.parquet
```

IEX daily bars are raw (no split adjustment). A run that needs split-adjusted
daily bars on IEX must declare a parity sidecar; the DQ stack will fail closed
otherwise (audit §P0-005).

## SIP partition paths (reserved — scaffolding)

```
bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted/symbol=<SYM>/part.parquet
bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw/symbol=<SYM>/year=<YYYY>/month=<MM>/part.parquet
quotes/vendor=alpaca/feed=sip/symbol=<SYM>/year=<YYYY>/month=<MM>/part.parquet
statuses/vendor=alpaca/symbol=<SYM>/date=<YYYY-MM-DD>/part.parquet
corporate_actions/vendor=alpaca/symbol=<SYM>/part.parquet
```

SIP daily bars are split-adjusted by convention. SIP minute bars and SIP
quotes are raw (same shape as IEX) but sourced from the consolidated tape.

## Layout helpers

`bowaka_common.marketdata.layout` exports both generic builders
(`daily_bars_path`, `minute_bars_path`, `quotes_path`, ...) and SIP-specific
convenience wrappers:

| Helper | Returns |
|---|---|
| `sip_daily_bars_path(root, sym)` | `<root>/bars/vendor=alpaca/feed=sip/timeframe=1d/adjustment=split_adjusted/symbol=<SYM>/part.parquet` |
| `sip_minute_bars_path(root, sym, y, m)` | `<root>/bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw/symbol=<SYM>/year=<Y>/month=<M>/part.parquet` |
| `sip_quotes_path(root, sym, y, m)` | `<root>/quotes/vendor=alpaca/feed=sip/symbol=<SYM>/year=<Y>/month=<M>/part.parquet` |
| `sip_bars_root(root, "1d")` | The SIP daily-bars timeframe-adjustment root |
| `sip_quotes_root(root)` | The SIP quotes root |
| `statuses_path(root, sym, date)` | `<root>/statuses/vendor=alpaca/symbol=<SYM>/date=<YYYY-MM-DD>/part.parquet` |
| `sip_partitions_available(root)` | `True` iff the lake has *any* SIP bars or quotes parquet |

`MarketDataStore` exposes `sip_daily_bars` / `sip_minute_bars` / `sip_quotes`
/ `sip_quotes_at_or_before` / `has_sip_partitions` for SIP-aware reads.

## SIP preflight (Phase 10)

When a config sets `market_data.feed: sip`, two gates fire:

1. **`optuna/preflight.py`** — at study start, the preflight checks
   `MarketDataStore.has_sip_partitions()` (equivalently
   `bowaka_common.marketdata.layout.sip_partitions_available`). When the
   lake has no SIP data the preflight fails with `sip_data_absent` and a
   pointer to this document.
2. **`data/data_quality.py`** — the DQ stack emits a `sip_data_absent`
   required check for any `feed: sip` config against a SIP-less lake. The
   check is gated only on `intended_realism`; a `current_code_parity` run
   with `feed: sip` surfaces the warning but is not failed closed (parity
   mode reproduces the live code's behavior).

Neither gate fires for `feed: iex` — there is no regression.

## IEX caveat (P1-010)

Any artifact with `market_data.feed: iex` carries:

- `suitability_tier: research_only` (mechanical cap; see
  `bowaka_v2_lab.promotion.suitability`).
- `feed_caveat: partial_tape_features` (the new field added in Phase 10).

The run report opens with a banner that calls this out explicitly. Optuna
studies prefix the study name with `iex__` and tag `partial_tape=true` in
`study.user_attrs` so any downstream tool can immediately see the run was
tuned on IEX. Parameters tuned on IEX are NOT portable to SIP without
retraining — the audit (§P1-010) is explicit on this.

## See also

- `docs/audits/2026-05-22_realism_audit.md` §P1-010 (IEX-specific labeling).
- `docs/audits/2026-05-22_realism_audit.md` §11 Phase 9 (SIP migration plan).
- `bowaka_common.marketdata.layout` (the layout source of truth).
- `bowaka_v2_lab.optuna.preflight` (`sip_data_absent` gate).
- `bowaka_v2_lab.data.data_quality` (`sip_data_absent` required check).
- `bowaka_v2_lab.promotion.suitability` (`feed_caveat`, IEX promotion block).
- `bowaka_v2_lab.research.feature_divergence` (IEX-vs-SIP feature divergence
  report — runs once both feeds are ingested).
