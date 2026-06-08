export const meta = {
  name: 'coverage-criteria-measure',
  description: 'Measure exact coverage_missing miss-fraction under each candidate criterion + verify sim first-scan/multi-scan behavior, to ground the Option-1-vs-Option-2 decision',
  phases: [
    { title: 'Measure', detail: 'exact miss-fraction per criterion + sim scan-window/cadence from source' },
    { title: 'Judge', detail: 'adversarial: which option is most honest given the measured numbers' },
    { title: 'Synthesize', detail: 'grounded Option 1 vs Option 2 pros/cons' },
  ],
}

const RECIPE = `
ENVIRONMENT (read-only; DO NOT edit code, DO NOT touch live trading on the Windows host, DO NOT kill jupyter kernels):
- Run python in the ql-jupyter container:
    docker exec ql-jupyter bash -lc 'export MSYS_NO_PATHCONV=1; export PYTHONPATH=/quants-lab/research_notebooks/bowaka_v2_lab/src:/quants-lab/research_notebooks/bowaka_common/src; /opt/conda/envs/quants-lab/bin/python /quants-lab/scripts/YOURFILE.py'
  Write scratch to /quants-lab/scripts/ prefixed _wfcc_ . Host source: E:/tradingsoftware/quants-lab/research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/ (Read directly).
- Lake: /opt/market_data_cache. minute: bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw/symbol=X/year=Y/month=M/part.parquet. Config: /tmp/ir2m.yml.
- SCOPE GUARD (CRITICAL — a prior agent over-ran by 20min): work ONLY over the 5 study-start probe sessions [2025-08-27,28,29,2025-09-02,2025-09-03]. Build eligible_per_session_map(LAKE, those_5_sessions, cfg) ONCE and reuse it. DO NOT build the full-study PIT union, DO NOT call plan_pit_symbol_union, DO NOT iterate folds. Your whole script must finish in a few minutes.

ESTABLISHED FACTS (verified):
- The $2M intended_realism study-start gate probes scan_times_for_session(sd,cfg)[0] = 09:45 ET. build_coverage_check (data/data_quality.py:391-523) marks a (sym,session) missing if no daily bar OR no minute bar at scan_times[0]. minute_bars_supplier under policy scanner_start_to_scan (data/suppliers.py:47-90) => window [intraday_window_start(t), t].
- Over the 5758 PIT-eligible (sym,session) pairs: 1205 eligible misses = 20.93% (gate COVERAGE_MISSING_FAIL_FRACTION=1%). 100% minute-leg (0 daily-leg). 1111 (92.2%) have a bar LATER in [09:45,close] but NOT at exactly 09:45; 94 (7.8%) have no bar 09:45->close. Raw-verified: misses have bars at 09:44 and 09:46 but none at exactly 13:45:00 UTC (=09:45 ET) -> NOT a tz/offset bug.
- Sim carries forward last real bar bounded by max_bar_age_seconds=90s; scanner skips STALE_BAR if last bar age > 90s (scanner/scan_loop.py:369-399). No quote partitions -> zero-spread synth quote age 0 -> quote_stale(15s) never trips.
`;

const MEASURE_SCHEMA = {
  type: 'object',
  required: ['n_eligible', 'criteria', 'sim_first_scan_window', 'sim_scans_per_session', 'stale_symbol_reevaluated_later', 'evidence', 'confidence'],
  properties: {
    n_eligible: { type: 'integer', description: 'total eligible (sym,session) pairs (expect 5758)' },
    criteria: {
      type: 'array',
      description: 'miss count + fraction + gate(1%) pass/fail under each candidate coverage criterion',
      items: {
        type: 'object',
        required: ['key', 'definition', 'miss', 'fraction_pct', 'passes_1pct_gate'],
        properties: {
          key: { type: 'string', enum: ['exact_0945', 'asof90_at_0945', 'fresh_at_any_scan_90s', 'any_regular_session_bar', 'monthfile_and_daily_present'] },
          definition: { type: 'string', description: 'exact rule measured (windows/timestamps)' },
          miss: { type: 'integer' },
          fraction_pct: { type: 'number' },
          passes_1pct_gate: { type: 'boolean' },
        },
      },
    },
    sim_first_scan_window: { type: 'string', description: 'At the FIRST scan (09:45) what window does the sim actually read — [09:45,09:45] (no lookback) or wider? Cite suppliers.py intraday_window_start + the value of session_start/scanner_start passed. Resolve whether a 09:44 bar is visible to the sim at the 09:45 scan.' },
    sim_scans_per_session: { type: 'integer', description: 'how many scan times per session does scan_times_for_session(sd,cfg) return for /tmp/ir2m.yml' },
    stale_symbol_reevaluated_later: { type: 'boolean', description: 'Is a symbol skipped STALE_BAR / empty-window at 09:45 re-evaluated at later scan times (no per-symbol per-day latch disabling it)? Cite scan_loop.py.' },
    evidence: { type: 'string', description: 'the script you ran (path) + key output + file:line citations.' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
};

const JUDGE_SCHEMA = {
  type: 'object',
  required: ['most_realism_faithful_criterion', 'is_changing_criterion_gaming_the_gate', 'does_option1_pass', 'gate_change_also_needed', 'strongest_objection_to_each', 'recommendation'],
  properties: {
    most_realism_faithful_criterion: { type: 'string', description: 'Which measured criterion most faithfully reflects "the lake can simulate this (sym,session)" given the sim probes MANY scans, not just 09:45? Justify.' },
    is_changing_criterion_gaming_the_gate: { type: 'string', description: 'Is moving off exact_0945 a legitimate mis-calibration fix or is it loosening a real check? Argue both sides, then conclude.' },
    does_option1_pass: { type: 'boolean', description: 'Does the Option-1 criterion (asof/fresh-aware) actually drop below the 1% gate per the measured numbers, or not?' },
    gate_change_also_needed: { type: 'boolean', description: 'Given the measured residual (genuine flat-session pairs), is a gate-threshold change ALSO required to pass, or does a criterion change alone suffice?' },
    strongest_objection_to_each: { type: 'string', description: 'Strongest objection to Option 1 (change criterion) AND to Option 2 (raise gate).' },
    recommendation: { type: 'string', description: 'The most defensible path (may be a combination), with the guardrail that keeps backfill-gap detection intact.' },
  },
};

phase('Measure');
const measure = await agent(
  RECIPE + `\nTASK: Write ONE bounded script over the 5758 eligible pairs (cache eligible_per_session_map over the 5 probe sessions) and measure the miss count + fraction + 1%-gate pass/fail under EACH criterion:\n` +
  `  exact_0945: bar timestamped exactly at scan_times[0] (the current check).\n` +
  `  asof90_at_0945: >=1 real minute bar in [scan_times[0]-90s, scan_times[0]] (hypothetical pre-open lookback).\n` +
  `  fresh_at_any_scan_90s: EXISTS a scan time t in scan_times_for_session(sd,cfg) such that >=1 bar in [t-90s, t] AND that bar is within the session (>= scanner_start) — i.e. the sim would trade the symbol at SOME scan.\n` +
  `  any_regular_session_bar: >=1 bar in [scan_times[0], scan_times[-1]].\n` +
  `  monthfile_and_daily_present: the symbol's minute month parquet exists for the session AND a daily bar exists that session.\n` +
  `Use store.minute_bars(sym, start, end) directly for the asof windows (the supplier has a fixed window-start). Report per-criterion totals + per-session + 3 named examples of each criterion's residual misses. ALSO resolve from source (suppliers.py, scan_loop.py, schedule.py): the FIRST-scan window the sim actually reads, the number of scans/session, and whether a 09:45-skipped symbol is re-scanned later. Keep it to a few minutes.`,
  { label: 'measure-criteria', phase: 'Measure', schema: MEASURE_SCHEMA });

phase('Judge');
const judge = await agent(
  RECIPE + `\nMEASURED RESULT: ${JSON.stringify(measure)}\n` +
  `TASK: Adversarially decide between Option 1 (change the coverage criterion off exact_0945 to a sim-faithful one) and Option 2 (keep exact_0945, raise the 1% gate). Use ONLY the measured numbers. Is changing the criterion a legitimate mis-calibration fix (the sim re-scans through the day, so first-scan-only coverage is unrepresentative) or is it gaming the gate? Does Option 1 actually pass, or is a gate change also needed for the genuine flat-session residual? Give the strongest objection to each and a final recommendation that keeps backfill-gap (no-month-file) detection intact.`,
  { label: 'judge', phase: 'Judge', schema: JUDGE_SCHEMA });

phase('Synthesize');
const synthesis = await agent(
  `You are writing a decision brief for the operator. Inputs:\n` +
  `MEASURED: ${JSON.stringify(measure)}\nADVERSARIAL JUDGE: ${JSON.stringify(judge)}\n` +
  `TASK: Produce a concise Markdown answer to "why Option 1 (sim-faithful coverage criterion) over Option 2 (raise the 1% gate)? pros/cons of each", grounded ENTIRELY in the measured miss-fractions. Include: a one-line statement of what each option actually does to the numbers (cite the measured fraction), a short pros/cons table for each, whether either alone passes the gate, the recommended path (and whether it is a combination), and the guardrail that preserves real-gap detection. Be honest if Option 1 does not fully pass on its own. Return ONLY the Markdown.`,
  { label: 'synthesize', phase: 'Synthesize' });

return { measure, judge, synthesis };
