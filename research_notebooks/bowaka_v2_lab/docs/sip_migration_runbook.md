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
