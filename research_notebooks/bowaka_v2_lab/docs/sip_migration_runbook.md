# SIP migration runbook

Audit 2026-05-29 §9 Phase 7. The lab ships SIP-readiness scaffolding (the lake
quote layout, the NBBO coverage gate, the LULD/halt feed reader, and the
IEX-vs-SIP divergence report) BEFORE SIP access is available. When the operator
gains a SIP feed, switching the lab from `current_code_parity` (IEX) to
`intended_realism` (SIP) must be a **configuration change, not a code change**.
This runbook is the operator-facing procedure.

## Steps

1. **Ingest SIP data.** Land SIP daily + minute bars, NBBO quotes, and the
   halt feed under the lake's SIP partition paths
   (`bars/.../feed=sip/...`, `quotes/.../feed=sip/...`, `halt_events/...`).

2. **Confirm coverage.** Run the lake capability probe and the new
   `check_nbbo_quote_coverage` gate over the intended universe + fold windows;
   confirm mean per-fold NBBO coverage clears the configured
   `min_quote_coverage_pct`.

3. **Switch the config.** Flip the workstation config's `market_data.feed`
   from `iex` to `sip` and `simulation.mode` from `current_code_parity` to
   `intended_realism`. No code change is required — the readers and gates
   already understand the SIP slot.

4. **Run the feed-divergence report.** Run the IEX-vs-SIP feature-divergence
   report; review and document any feature whose median divergence exceeds 5%.

5. **Recalibrate RVOL thresholds.** Recalibrate the RVOL (and other
   feed-sensitive) thresholds in the search space using the divergence
   percentiles — moving from the current IEX-tightened thresholds to
   SIP-tightened thresholds.

6. **Re-run the full test matrix.** Re-run `make test-all`; the
   `intended_realism`-only gates (NBBO coverage, halt-data presence) may
   surface new failures that were dormant under `current_code_parity`. Resolve
   them before promoting any parameter recommendation.

## SIP cutover runbook (verified against the synthetic-SIP smoke 2026-05-29)

The commands below were exercised end-to-end against
`tests/fixtures/sip_synthetic_lake` (see
`tests/integration/test_sip_synthetic_end_to_end_smoke.py`), so the real
cutover is a config flip, not a debugging session.

Step 1 — re-ingest with the SIP feed:

    (edit) config/marketdata_backfill.yml: feed: sip
    cd <repo root>
    .\research_notebooks\bowaka_common\backfill_market_data.ps1

Step 2 — verify SIP partition presence:

    cd research_notebooks\bowaka_v2_lab
    py -3.12 -c "from bowaka_common.marketdata.catalog import available_symbols; print(len(available_symbols(None, timeframe='1d', vendor='alpaca', feed='sip', adjustment='split_adjusted')))"
    # expect >= 6000 once the full ingest completes; partial counts are fine for
    # a partial ingest as long as you narrow the workstation universe to match.

Step 3 — flip the workstation config:

    Use the shipped `configs/bowaka_v2_actual_sip_intended_realism.yml`
    (data.feed=sip, simulation.mode=intended_realism) in place of the IEX
    current_code_parity config. It is consistent with the smoke fixture config
    (same require_split_adjustment: true, quote_fallback_policy: require_real,
    simulation.mode: intended_realism).

Step 4 — run the verification CLIs:

    py -3.12 -m bowaka_v2_lab.cli verify-bayesian-fix     # Section 7 stays PASS
    py -3.12 -m bowaka_v2_lab.cli verify-realism-stress   # Section 13 'real SIP
    # partition present' flips DEFERRED -> PASS once SIP data is on disk.

Step 5 — start notebook 10 against the SIP config.

## Fill-realism data — trade tape + fine NBBO (PA.2 / PA.3)

The honest fill model (sell-side exits + the tape-replay oracle, see
`docs/fill_realism.md`) consumes two **opt-in** datasets, fetched with the same
incremental backfill. Both are SIP-only, sit on **sibling paths** (`trades/`,
`quotes_fine/`) that never drift the canonical `quote_partitions_hash`, and skip
the shared `_ingestion/manifest.json` write in `*-only` mode — so many month-range
workers can run in parallel and a running study is undisturbed.

    # raw trade tape (PB.4 oracle ground truth) — VERY sparse on a $1-$20 universe
    # (~2.7 MB/symbol-month; ~60-70 GB over ~11 months). Scope --start/--end.
    python scripts/backfill_market_data.py --feed sip --start 2025-08-01 --end auto \
        --trades-only --rpm 9000 --lake-root /opt/market_data_cache

    # fine NBBO (sub-minute + bid/ask exchange + tape). --quotes-fine-samples-per-minute
    # omitted = raw ticks; 4 = 4 prevailing snapshots/min (bounded, ~10 GB).
    python scripts/backfill_market_data.py --feed sip --start 2025-08-01 --end auto \
        --quotes-fine-only --quotes-fine-samples-per-minute 4 --rpm 9000 \
        --lake-root /opt/market_data_cache

Both are resume-skip incremental (per symbol/session) and heavy on the first run
(the full tape / NBBO tick stream is fetched). After a `*-only` run, do one normal
(non `*-only`) backfill to refresh the manifest. Enable the model per
`docs/fill_realism.md` (`exits.fill_model: tape_replay` and/or `execution.fill_model`).
