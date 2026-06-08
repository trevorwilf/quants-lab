export const meta = {
  name: 'implement-remaining-ir-gate-fixes',
  description: 'Implement the coverage_missing combination fix + audit_missing_sessions per-session-eligibility scoping, adversarially review, and test (incl. live $2M gate re-run)',
  phases: [
    { title: 'Implement', detail: 'edit data_quality.py (+ tests) per the locked design' },
    { title: 'Review', detail: 'adversarial review of the diff vs the design + invariants' },
    { title: 'Test', detail: 'frozen DQ tests + unit suite + live $2M study-start gate re-run' },
  ],
}

const ENV = `
ENVIRONMENT (you EDIT host source which the container mounts live; DO NOT touch live trading on the Windows host; DO NOT kill jupyter kernels):
- Host source to EDIT: E:/tradingsoftware/quants-lab/research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/data/data_quality.py (and tests under research_notebooks/bowaka_v2_lab/tests/). Use Read/Edit on the host paths.
- Run python/pytest in the ql-jupyter container (the mount is live, no reinstall needed):
    docker exec ql-jupyter bash -lc 'export MSYS_NO_PATHCONV=1; export PYTHONPATH=/quants-lab/research_notebooks/bowaka_v2_lab/src:/quants-lab/research_notebooks/bowaka_common/src; cd /quants-lab/research_notebooks/bowaka_v2_lab && /opt/conda/envs/quants-lab/bin/python -m pytest ...'
- Container python: /opt/conda/envs/quants-lab/bin/python. Lake: /opt/market_data_cache. Config under test: /tmp/ir2m.yml.
`;

const DESIGN = `
LOCKED DESIGN (operator-approved; audit doc research_notebooks/bowaka_v2_lab/docs/audits/2026-06-07_intended_realism_coverage_findings.md §10c). All changes are in data/data_quality.py. The coverage gates already accept an optional eligible_per_session map (the §6.6 denominator fix). MEASURED facts: over 5758 PIT-eligible (sym,session) probe pairs, exact-09:45 miss=20.93%, "any regular-session bar" miss=1.63% (=94 genuine zero-bar flat sessions), "month-file+daily present" miss=0.78% (=45). The sim re-scans 346x/session (60s grid 09:45->15:30, no per-day disable latch) so probing only scan_times[0] is mis-calibrated.

=== FIX A — coverage_missing: sim-faithful criterion + drop genuine flat-session pairs from the gated denominator ===
In build_coverage_check (data/data_quality.py ~391-523):
- MINUTE-LEG CRITERION: change the minute probe from "bar at scan_times[0]" to "ANY real bar in the regular session [scan_times[0], scan_times[-1]]". Concretely, probe minute_bars_supplier(sym, scan_times[-1]) (the supplier window is [intraday_window_start(t), t] = [09:45, scan_times[-1]] under scanner_start_to_scan) and treat non-empty as session_minute_ok. (Keep probe_ts handling robust if scan_times is empty.)
- DENOMINATOR (gated only): a PIT-eligible pair that has a daily bar but NO regular-session minute bar is a genuine illiquid no-trade session -> NOT simulable -> EXCLUDE from the gated denominator expected_g AND do not count it in the gated missing. (The sim correctly never trades it.) i.e. for eligible pairs: if session_minute_ok is False AND day_ok is True -> skip from expected_g/missing_g entirely. If day_ok is False -> still counts as a gated miss (a real daily-leg gap). Result on the $2M probe: gated eligible_fraction -> 0 (all remaining eligible pairs have a session bar AND a daily bar).
- TELEMETRY: keep the FULL-UNION counters (expected, missing_daily, missing_minute, missing_fraction) BYTE-IDENTICAL to today for the §6.6 invariant — only the GATED counters (expected_g/missing_*_g/frac_g) and the gate status change. Record in evidence: keep existing keys; the full-union "missing_minute" now reflects the any-session-bar criterion too (document this in evidence with a "minute_leg_criterion":"any_regular_session_bar" note). Add evidence keys "dropped_flat_session_pairs" (count of eligible pairs excluded as no-trade) and "minute_leg_criterion".
- When eligible_per_session is None (legacy/no-eligibility): behaviour MUST stay BYTE-IDENTICAL to today (the criterion change applies to the probe, but with no gating the full-union exact-0945 vs any-session-bar difference WOULD change legacy numbers — therefore GATE THE CRITERION CHANGE on gated==True: when eligible_per_session is None keep the exact scan_times[0] probe; when gated, use the any-session-bar probe). This preserves all legacy/frozen behaviour.

=== FIX B — new guardrail check coverage_backfill_present (the strict structural-absence detector the tolerant gate must not mask) ===
Add a new check function build_backfill_presence_check(*, requested_symbols, sessions, eligible_per_session, lake_root, feed, daily_bars_supplier, source_file) returning a _check named "coverage_backfill_present":
- For every PIT-eligible (sym, session) pair (use eligible_per_session; if None, skip/pass as a no-op so legacy is unaffected), assert: (i) the minute MONTH parquet exists for that (sym, year, month) via bowaka_common.marketdata layout.minute_bars_path (or store path), AND (ii) a daily bar exists that session (daily_bars_supplier non-empty). Count pairs failing either leg.
- status: fail if fraction >= COVERAGE_MISSING_FAIL_FRACTION (1%); warn if any; else pass. (Measured 0.78% -> PASS, but a missing-month / wrong-feed catastrophe at 15-20% -> FAIL.) Evidence: expected, missing, fraction, examples, the two legs split.
- Wire it into build_data_quality_report / _build_multi_level_checks right after the coverage_missing check (it has lake_root, feed, daily_bars_supplier, eligible_per_session). Add "coverage_backfill_present" to the REQUIRED check set (_REQUIRED_CHECK_NAMES) so it gates intended_realism, and to dq_check_invariance map (classify like coverage_missing). When eligible_per_session is None it must be a no-op pass (legacy safe).

=== FIX C — audit_missing_sessions: per-session-eligibility scoping ===
The audit parquet (build_audit_checks, ~301-388) is SYMBOL-LEVEL (missing_sessions count over each ticker's full 2.5y calendar) — it cannot be split by session from the parquet alone. VERIFIED: all 1762 come from 6 ever-eligible de-SPAC/ticker-reuse names whose missing sessions are 100% PRE-first-eligible; 0 fall in any eligible window; 0 eligible sessions lack a daily bar.
- Change: pass eligible_per_session + daily_bars_supplier into build_audit_checks (thread from build_data_quality_report). When BOTH are provided, compute the audit_missing_sessions GATING count as the per-session-eligibility-scoped recomputation: the number of PIT-eligible (sym, session) pairs that LACK a daily bar (daily_bars_supplier empty) — i.e. missing sessions WITHIN eligible windows. Record the parquet symbol-level count as evidence "lake_audit_missing_sessions" (telemetry) + "gated":true + "eligible_missing_sessions": <recomputed>. Gate (status fail/pass) on the recomputed count (threshold 0, as today). On the $2M probe this -> 0 -> PASS.
- When eligible_per_session/daily_bars_supplier are None (legacy): byte-identical to today (parquet symbol-level count gates).
- Add an evidence note that ticker-reuse identity is flagged for the survivorship/PIT asset-master (separate work).

=== CONSTRAINTS ===
- Default/legacy path (eligible_per_session=None) BYTE-IDENTICAL to current behaviour for ALL three fixes. Confirm with the existing frozen tests.
- Preserve the §6.6 full-union telemetry invariant.
- Update/extend tests under tests/ for the new gated semantics + the new check; if any frozen golden changes, add a changelog comment explaining why (CLAUDE.md rule). Do NOT weaken unrelated tests.
- Do NOT change executor_refresh_time/cooldown_time typing or any unrelated code.
`;

const IMPL_SCHEMA = {
  type: 'object',
  required: ['files_edited', 'fix_a_summary', 'fix_b_summary', 'fix_c_summary', 'legacy_byte_identical', 'tests_added', 'open_concerns'],
  properties: {
    files_edited: { type: 'array', items: { type: 'string' } },
    fix_a_summary: { type: 'string' },
    fix_b_summary: { type: 'string' },
    fix_c_summary: { type: 'string' },
    legacy_byte_identical: { type: 'string', description: 'How you preserved the eligible_per_session=None byte-identical path for each fix.' },
    tests_added: { type: 'array', items: { type: 'string' } },
    open_concerns: { type: 'string' },
  },
};

const REVIEW_SCHEMA = {
  type: 'object',
  required: ['verdict', 'matches_design', 'legacy_byte_identical_holds', 's66_telemetry_preserved', 'guardrail_registered', 'defects', 'must_fix'],
  properties: {
    verdict: { type: 'string', enum: ['sound', 'sound_with_nits', 'needs_fix'] },
    matches_design: { type: 'boolean' },
    legacy_byte_identical_holds: { type: 'boolean', description: 'Independently verify the eligible_per_session=None path is unchanged (read the diff; reason about each branch).' },
    s66_telemetry_preserved: { type: 'boolean', description: 'Full-union expected/missing telemetry unchanged?' },
    guardrail_registered: { type: 'boolean', description: 'coverage_backfill_present added to _REQUIRED_CHECK_NAMES + dq_check_invariance, no-op when eligibility absent?' },
    defects: { type: 'string' },
    must_fix: { type: 'string', description: 'Concrete must-fix items, or "none".' },
  },
};

const TEST_SCHEMA = {
  type: 'object',
  required: ['frozen_dq_tests', 'unit_suite', 'gate_rerun', 'all_four_gates', 'regressions', 'verdict'],
  properties: {
    frozen_dq_tests: { type: 'string', description: 'result of the 3 frozen DQ tests (coverage_missing_fails_realism, dq_replay_level_missing_*).' },
    unit_suite: { type: 'string', description: 'tests/unit/data + tests/unit/optuna pass/fail counts; list any NEW failures vs the known 0-failure baseline.' },
    gate_rerun: { type: 'string', description: 'Re-run scripts/_verify_studystart_gate.py on /tmp/ir2m.yml; report the per-check table (coverage_missing_late_session, coverage_missing_exit_path, coverage_missing, coverage_backfill_present, audit_missing_sessions) with statuses.' },
    all_four_gates: { type: 'boolean', description: 'Do ALL previously-failing study-start gates now PASS (or are non-gating warns)?' },
    regressions: { type: 'string' },
    verdict: { type: 'string', enum: ['green', 'not_green'] },
  },
};

phase('Implement');
const impl = await agent(ENV + DESIGN + `\nTASK: Implement all three fixes in data/data_quality.py (+ wiring in build_data_quality_report/_build_multi_level_checks + registration constants) and add/extend tests. Read the functions first (build_coverage_check, build_audit_checks, _build_multi_level_checks, build_data_quality_report, _REQUIRED_CHECK_NAMES, dq_check_invariance). Make minimal, surgical edits. Return the structured summary.`,
  { label: 'implement', phase: 'Implement', schema: IMPL_SCHEMA });

phase('Review');
const review = await agent(ENV + DESIGN + `\nIMPLEMENTER REPORT: ${JSON.stringify(impl)}\nTASK: Adversarially review the actual diff (git diff on data_quality.py + tests) against the locked design. Independently verify: (1) the eligible_per_session=None path is byte-identical for all 3 fixes; (2) §6.6 full-union telemetry preserved; (3) coverage_backfill_present is registered as required + invariance + is a no-op when eligibility is absent; (4) FIX A actually drops gated->~0 and FIX C recomputes eligibility-scoped (not parquet) count; (5) no unrelated golden/test weakening. Be specific with file:line. Return the verdict + concrete must-fix items.`,
  { label: 'review', phase: 'Review', schema: REVIEW_SCHEMA });

phase('Test');
const test = await agent(ENV + `\nIMPLEMENTER: ${JSON.stringify(impl)}\nREVIEW: ${JSON.stringify(review)}\nTASK: Validate. (1) Run the 3 frozen DQ tests: tests/unit/test_coverage_missing_fails_realism.py tests/integration/test_dq_replay_level_missing_exit_path.py tests/integration/test_dq_replay_level_missing_late_minute.py. (2) Run tests/unit/data tests/unit/optuna and report pass/fail vs the known baseline of 0 failures (the 2 stale-mock failures were already fixed). (3) Re-run scripts/_verify_studystart_gate.py on /tmp/ir2m.yml (it spies run_preflight + build_data_quality_report and prints the per-level table) and report EVERY check's status — confirm coverage_missing, coverage_backfill_present, audit_missing_sessions, late_session, exit_path. Report whether ALL four originally-failing study-start gates now pass. Note: this re-run takes a few minutes (PIT build over 5 sessions); that is expected, let it finish. Return the structured result.`,
  { label: 'test', phase: 'Test', schema: TEST_SCHEMA });

return { impl, review, test };
