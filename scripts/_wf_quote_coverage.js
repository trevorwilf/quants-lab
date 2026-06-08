export const meta = {
  name: 'quote-coverage-deepdive',
  description: 'Verify the quote_coverage mis-calibration (PIT over-inclusion + single-instant vs sim re-scan), confirm sim quote semantics, adversarially refute the fix, synthesize',
  phases: [
    { title: 'Verify', detail: 'independent measure + sim require_real/re-scan semantics' },
    { title: 'Refute', detail: 'adversary tries to break the eligible+anyscan fix' },
    { title: 'Synthesize', detail: 'recommended fix + open policy decision' },
  ],
}

const ENV = `
ENVIRONMENT (read-only; DO NOT edit code, DO NOT touch live trading on the Windows host, DO NOT kill jupyter kernels):
- Run python in ql-jupyter: docker exec ql-jupyter bash -lc 'export MSYS_NO_PATHCONV=1; export PYTHONPATH=/quants-lab/research_notebooks/bowaka_v2_lab/src:/quants-lab/research_notebooks/bowaka_common/src; /opt/conda/envs/quants-lab/bin/python /quants-lab/scripts/YOURFILE.py'. Scratch -> /quants-lab/scripts/ prefixed _wfqc_ . Host source: E:/tradingsoftware/quants-lab/research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/ (Read directly).
- Lake /opt/market_data_cache: quotes quotes/vendor=alpaca/feed=sip/symbol=X/year=Y/month=M/part.parquet (cols symbol,timestamp,bid,ask,bid_size,ask_size,conditions; ~per-minute prevailing NBBO at :59.99). minute bars bars/.../timeframe=1m/adjustment=raw. Config /tmp/ir2m.yml.
- SCOPE GUARD (CRITICAL — prior agents over-ran ~20min): work ONLY over the 5 study-start probe sessions [2025-08-27,28,29,2025-09-02,2025-09-03]. Build eligible_per_session_map(LAKE, those_5, cfg) ONCE and reuse. DO NOT build the full-study PIT union, DO NOT call plan_pit_symbol_union, DO NOT run broad pytest suites. Finish in a few minutes.

ESTABLISHED (your job is to VERIFY/REFUTE, not take on faith):
- quote_coverage gate: probe_quote_coverage (optuna/preflight.py:499) probes max_probe=200 (sym, scan) pairs; probe_ts = scan_times[len//2] (MIDDLE scan ~12:37); uses make_quote_supplier default max_age_seconds=60s; over the FULL union (2425 syms, so all 200 come from session-1). gate min_quote_coverage_pct=95% (_check_quote_coverage). Reproduced = 57.50%.
- intended_realism sets quote_fallback_policy=require_real (config/models.py:40); resolve_quote (sim/quote_model.py:216-254) returns missing_quote=True when require_real + no historical quote; the StrategyConsumer (strategy_consumer.py:264-303) rejects the candidate (reason quote stuff). config max_quote_age_seconds=15.
- MEASURED (scripts/_scout_quote_coverage.py, 5758 eligible pairs): middle_15s 56.06%, middle_60s 87.58%, any_session_quote 98.37%, anyscan_15s ("exists a scan t with a quote in [t-15s,t]") 98.33%, scan_density_15s mean 66.59%. probe_quote_coverage on ELIGIBLE union (still 200-cap,60s) = 89.00%. anyscan_15s misses are the SAME genuine flat-no-trade names (ANAB/AVBC/BACC, qrows=0, also zero minute bars).
`;

const VERIFY_SCHEMA = {
  type: 'object',
  required: ['anyscan_15s_pct', 'middle_instant_pct', 'eligible_vs_fullunion_gap', 'misses_are_genuine_flat', 'staleness_sensitivity', 'evidence', 'confidence'],
  properties: {
    anyscan_15s_pct: { type: 'number', description: 'independently re-measured: % of PIT-eligible (sym,session) pairs with a quote within 15s of SOME scan.' },
    middle_instant_pct: { type: 'number', description: 're-measured single middle-scan 60s % over eligible pairs.' },
    eligible_vs_fullunion_gap: { type: 'string', description: 'quantify the PIT-over-inclusion drag: full-union vs eligible at the same criterion.' },
    misses_are_genuine_flat: { type: 'boolean', description: 'Are the anyscan_15s misses genuine flat-no-trade sessions (zero quotes AND zero minute bars), NOT backfill gaps? Cross-check minute bars for >=6 named miss pairs.' },
    staleness_sensitivity: { type: 'string', description: 'anyscan coverage at 5s / 15s / 60s windows — how sensitive is it to the staleness bound.' },
    evidence: { type: 'string', description: 'the script you ran + key output.' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
};

const SIM_SCHEMA = {
  type: 'object',
  required: ['intended_realism_uses_require_real', 'missing_quote_rejects_candidate', 'quote_rejected_symbol_rescanned_later', 'sim_staleness_bound_seconds', 'realism_correct_quote_criterion', 'evidence', 'confidence'],
  properties: {
    intended_realism_uses_require_real: { type: 'boolean' },
    missing_quote_rejects_candidate: { type: 'boolean', description: 'Does a require_real missing quote actually reject the trade at that scan? cite strategy_consumer.py.' },
    quote_rejected_symbol_rescanned_later: { type: 'boolean', description: 'CRITICAL: is a symbol whose candidate was rejected for a missing quote at scan t re-evaluated at later scans (no per-symbol-per-day latch that disables it)? cite scan_loop.py / the consumer. This is the load-bearing assumption behind the anyscan metric.' },
    sim_staleness_bound_seconds: { type: 'number', description: 'the quote staleness bound the sim applies (execution.max_quote_age_seconds).' },
    realism_correct_quote_criterion: { type: 'string', description: 'Given the semantics, what SHOULD quote_coverage measure to match what the sim can actually trade?' },
    evidence: { type: 'string', description: 'file:line citations.' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
};

const REFUTE_SCHEMA = {
  type: 'object',
  required: ['strongest_objection', 'objection_is_fatal', 'masks_real_quote_gap', 'cap_or_sampling_concern', 'staleness_concern', 'recommended_guardrails', 'verdict'],
  properties: {
    strongest_objection: { type: 'string', description: 'Strongest case that "scope to eligible + anyscan_15s -> 98.33% PASS" is wrong/gaming.' },
    objection_is_fatal: { type: 'boolean' },
    masks_real_quote_gap: { type: 'string', description: 'Could it hide a genuine quote-backfill gap (missing quote partition for an eligible name)? How to keep that detectable.' },
    cap_or_sampling_concern: { type: 'string', description: 'Does removing the 200-cap / changing the sample matter? Is the eligible anyscan a fair estimator?' },
    staleness_concern: { type: 'string', description: 'The preflight probes 60s but the sim uses 15s — is using 15s (stricter, sim-faithful) correct, and does anyscan still pass at 15s?' },
    recommended_guardrails: { type: 'string' },
    verdict: { type: 'string', enum: ['fix_sound', 'fix_sound_with_guardrails', 'fix_unsafe'] },
  },
};

phase('Verify');
const [measure, sim] = await parallel([
  () => agent(ENV + `\nTASK: Independently re-measure quote coverage over the 5758 PIT-eligible (sym,session) probe pairs (read SIP quote parquets directly, cache per symbol-month): anyscan within 15s of some scan, single middle-scan 60s, any-session-quote. Quantify the full-union-vs-eligible PIT drag. CROSS-CHECK that the anyscan_15s misses are genuine flat-no-trade (also zero minute bars that session) — read the raw minute parquet for >=6 named miss pairs. Report anyscan coverage at 5s/15s/60s staleness.`,
    { label: 'measure', phase: 'Verify', schema: VERIFY_SCHEMA }),
  () => agent(ENV + `\nTASK: Confirm the sim quote semantics from source. (1) intended_realism -> quote_fallback_policy=require_real. (2) a require_real missing historical quote rejects the candidate at that scan (strategy_consumer.py:241-303). (3) CRITICAL: a symbol rejected for a missing quote at scan t IS re-evaluated at later scans — there is NO per-symbol-per-day latch disabling it (read scanner/scan_loop.py per-scan loop + the consumer; compare to the stale-bar skip which we know re-scans). (4) the staleness bound the sim uses (max_quote_age_seconds=15). Then state the realism-correct quote_coverage criterion. Cite file:line.`,
    { label: 'sim-quote-semantics', phase: 'Verify', schema: SIM_SCHEMA }),
]);

phase('Refute');
const refute = await agent(ENV + `\nPROPOSED FIX: (1) scope probe_quote_coverage to the per-session PIT-eligible symbols (not the full union); (2) replace the single-middle-scan probe with the sim-faithful "quote within max_quote_age_seconds (15s) of SOME scan" criterion; (3) remove/raise the 200-cap (measure all eligible pairs, reading each symbol's session quotes once). Result: 57.5% -> 98.33% -> PASS (95% gate). Optionally drop genuine flat-no-trade pairs from the denominator. Keep a structural quote-backfill-presence guardrail.\nVERIFY: ${JSON.stringify(measure)}\nSIM: ${JSON.stringify(sim)}\nTASK: Be the adversary. Argue the strongest case this is wrong/gaming, whether it masks a real quote-backfill gap, whether the 200-cap removal / eligible sampling is a fair estimator, and whether using 15s (sim) vs 60s (preflight default) is right. Then judge fatal-or-not + required guardrails.`,
  { label: 'refute', phase: 'Refute', schema: REFUTE_SCHEMA });

phase('Synthesize');
const synthesis = await agent(
  `Decision brief for the operator. Inputs:\nVERIFY: ${JSON.stringify(measure)}\nSIM: ${JSON.stringify(sim)}\nREFUTE: ${JSON.stringify(refute)}\n` +
  `TASK: Produce a concise Markdown section (to append to docs/audits/2026-06-07_intended_realism_coverage_findings.md as "## 10d. quote_coverage: evidence + recommended fix") covering: root cause (one line), the measured coverage table (full-union 57.5% / eligible 89% / single-instant / anyscan_15s 98.33%), why it mirrors coverage_missing, the recommended fix (eligibility scoping + sim-faithful anyscan criterion + cap removal + a quote-backfill-presence guardrail), the adversarial verdict + guardrails, and the explicit OPEN POLICY DECISION for the operator (e.g. drop flat-no-trade pairs from the denominator vs not; 15s vs 60s staleness; keep the 95% threshold). Be honest about confidence. Return ONLY the Markdown.`,
  { label: 'synthesize', phase: 'Synthesize' });

return { measure, sim, refute, synthesis };
