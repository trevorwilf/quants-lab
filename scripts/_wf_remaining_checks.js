export const meta = {
  name: 'ir-remaining-checks-deepdive',
  description: 'Deep-dive the 2 remaining intended_realism gates (coverage_missing + audit_missing_sessions): verify root cause + sim semantics, adversarially refute the proposed fixes, synthesize a recommendation',
  phases: [
    { title: 'Investigate', detail: 'sim carry-forward/staleness semantics + independent verification of both checks' },
    { title: 'Refute', detail: 'adversarial skeptics try to break each proposed fix' },
    { title: 'Synthesize', detail: 'recommended fix per check + draft audit-doc section' },
  ],
}

// Shared container recipe every agent needs (read-only; lake + host code).
const RECIPE = `
ENVIRONMENT (read-only investigation; DO NOT edit code, DO NOT touch live trading on the Windows host, DO NOT kill jupyter kernels):
- Run python in the ql-jupyter container. Recipe (MSYS path-mangling guard is REQUIRED):
    docker exec ql-jupyter bash -lc 'export MSYS_NO_PATHCONV=1; export PYTHONPATH=/quants-lab/research_notebooks/bowaka_v2_lab/src:/quants-lab/research_notebooks/bowaka_common/src; /opt/conda/envs/quants-lab/bin/python /quants-lab/scripts/YOURFILE.py'
  Write scratch scripts to /quants-lab/scripts/ (host: E:/tradingsoftware/quants-lab/scripts/). Prefix names with _wfagent_ to avoid clashes.
- Host source lives at E:/tradingsoftware/quants-lab/research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/ (Read it directly).
- Lake (container, native FS): /opt/market_data_cache. minute bars: bars/vendor=alpaca/feed=sip/timeframe=1m/adjustment=raw/symbol=X/year=Y/month=M/part.parquet ; daily: timeframe=1d/adjustment=split_adjusted/symbol=X/part.parquet ; audit parquet: _ingestion/audits/audit_*_sip.parquet.
- Config under test: /tmp/ir2m.yml (intended_realism, feed=sip, universe.max_price=20, min_adv_dollars=2000000). Container local time is MDT.

EVIDENCE ALREADY ESTABLISHED (your job is to VERIFY/REFUTE, not take on faith):
- The $2M intended_realism study-start preflight (walkforward_runner.py:1972) probes 5 sessions [2025-08-27,28,29, 09-02, 09-03] x ~1148-1162 PIT-eligible symbols/session (eligible union 1207). A §6.6 denominator fix already landed: coverage replay checks now gate on per-session PIT-eligible pairs.
- TWO checks still FAIL the study-start gate:
  (A) coverage_missing: gated 1205/5758 = 20.93% (gate = COVERAGE_MISSING_FAIL_FRACTION = 1%). Instrumented split of the 1205 eligible misses: minute_leg only (NO daily-leg miss at all = 0); of those, 1111 (92.2%) "traded_later" (no bar in the EXACT [09:45,09:45] window but >=1 bar in [09:45, close]), 94 (7.8%) "no_trade_today" (no bar 09:45->close). build_coverage_check (data/data_quality.py:391-560) marks a pair missing if no daily bar OR no minute bar at scan_times[0]=09:45; window policy scanner_start_to_scan makes the minute probe a 1-minute [09:45,09:45] window (data/suppliers.py:74 resolve_intraday_window_policy + intraday_window_start).
  (B) audit_missing_sessions: count=1762 over the 2425-symbol requested union (gate=0). build_audit_checks (data/data_quality.py:301-365) sums the per-symbol missing_sessions column of the latest audit parquet, restricted to requested_symbols. Decomposed: ever-eligible symbols contribute 0; never-eligible symbols contribute 1762 (100%). Restricting the sum to the ever-eligible union (1207 syms) -> 0.
`;

const SIM_SCHEMA = {
  type: 'object',
  required: ['carry_forward_exists', 'staleness_bounded', 'staleness_policy', 'realism_correct_coverage_criterion', 'coverage_check_is_miscalibrated', 'evidence', 'confidence'],
  properties: {
    carry_forward_exists: { type: 'boolean', description: 'Does the sim carry forward a last/prior price when no trade prints at a scan minute (forming_session_bar.last_price etc.)?' },
    staleness_bounded: { type: 'boolean', description: 'Is carry-forward bounded by a staleness limit (quote_stale path / max age) rather than carried forever?' },
    staleness_policy: { type: 'string', description: 'Exact staleness rule the sim applies at a scan with no fresh bar (max bar/quote age, what triggers quote_stale, what the scan does when stale). Cite file:line.' },
    realism_correct_coverage_criterion: { type: 'string', description: 'Given the sim semantics, what SHOULD "coverable at 09:45" mean for a DQ preflight, so the check matches what the sim can actually simulate? (e.g. "has daily bar OR a minute bar within N min of 09:45")' },
    coverage_check_is_miscalibrated: { type: 'boolean', description: 'Is the current literal-bar-at-09:45 requirement mis-calibrated for an illiquid universe given the sim carries forward?' },
    evidence: { type: 'string', description: 'file:line citations for every claim (strategy_consumer.py, quote_model.py, protection.py, exits.py, backtester.py as relevant).' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
};

const AUDIT_SCHEMA = {
  type: 'object',
  required: ['full_study_union_missing_sessions', 'restricting_to_eligible_union_yields_zero', 'builder_legs_omitted_by_proxy', 'residual_eligible_with_missing', 'fix_is_safe', 'evidence', 'confidence'],
  properties: {
    full_study_union_missing_sessions: { type: 'integer', description: 'missing_sessions summed over the FULL-STUDY PIT-eligible union (ALL folds + holdout, not just the 5 probe sessions) — build the plan from /tmp/ir2m.yml and union per-fold eligibility (optuna/pit_universe.py plan_pit_symbol_union).' },
    restricting_to_eligible_union_yields_zero: { type: 'boolean', description: 'Does restricting the audit_missing_sessions sum to the full-study eligible union drive it to 0?' },
    builder_legs_omitted_by_proxy: { type: 'string', description: 'Which eligibility legs (instrument-class, blocklist, status_active, etc.) does the daily_eligible CSV proxy omit vs the real builder.eligible_symbols? Do they change the conclusion?' },
    residual_eligible_with_missing: { type: 'string', description: 'Any symbol that IS ever PIT-eligible (full study) yet has missing_sessions>0 — list them, or state none. This is the load-bearing safety check.' },
    fix_is_safe: { type: 'boolean', description: 'Is restricting the audit check to the PIT-eligible union safe (does not hide a real data gap for any tradeable symbol)?' },
    evidence: { type: 'string', description: 'file:line + the script you ran + its output.' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
};

const COVERAGE_DATA_SCHEMA = {
  type: 'object',
  required: ['sparsity_claim_holds', 'staleness_at_0945_distribution', 'is_supplier_window_bug', 'no_trade_today_have_prior_close', 'evidence', 'confidence'],
  properties: {
    sparsity_claim_holds: { type: 'boolean', description: 'Spot-checking raw lake minute files for a sample of the 1111 "traded_later" pairs: do they genuinely lack a 09:45 bar but have later bars (NOT a supplier-window/off-by-one artifact)?' },
    staleness_at_0945_distribution: { type: 'string', description: 'For the 1111 traded_later pairs: how stale is the last available price AT 09:45 (last pre-09:45 bar this session, or prior close)? Distribution of the gap to first post-09:45 trade. Are most within a plausible staleness bound?' },
    is_supplier_window_bug: { type: 'boolean', description: 'Is any part of the 20.93% actually a supplier window / timezone / off-by-one bug rather than genuine no-trade?' },
    no_trade_today_have_prior_close: { type: 'boolean', description: 'Do the 94 no_trade_today pairs have a valid prior close (a price to carry / they are real but flat that session)?' },
    evidence: { type: 'string', description: 'the script you ran + raw-lake spot-check output for >=6 named pairs.' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
};

const REFUTE_SCHEMA = {
  type: 'object',
  required: ['fix_under_test', 'strongest_objection', 'objection_is_fatal', 'masks_real_problem', 'recommended_guardrails', 'verdict'],
  properties: {
    fix_under_test: { type: 'string' },
    strongest_objection: { type: 'string', description: 'The single strongest reason this fix is WRONG or unsafe — argue it as hard as you can.' },
    objection_is_fatal: { type: 'boolean', description: 'After arguing it, is the objection actually fatal, or does it survive?' },
    masks_real_problem: { type: 'string', description: 'Does the fix risk masking a genuine data defect / halt / survivorship issue? Be concrete.' },
    recommended_guardrails: { type: 'string', description: 'If the fix proceeds, what guardrail/telemetry must accompany it so it cannot silently hide a real gap?' },
    verdict: { type: 'string', enum: ['fix_sound', 'fix_sound_with_guardrails', 'fix_unsafe'] },
  },
};

phase('Investigate');
const [sim, audit, covdata] = await parallel([
  () => agent(RECIPE + `\nTASK: Read the sim engine and determine the EXACT carry-forward + staleness semantics at a scan minute with no fresh trade. Start at sim/strategy_consumer.py (forming_session_bar, last_price, the quote_stale reason ~line 300), sim/quote_model.py (synthesize_quote), sim/protection.py (stale handling), and how backtester.py drives scans. Then state the realism-correct definition of "coverable at 09:45" for the coverage_missing DQ preflight so it matches what the sim can actually simulate. Cite file:line for everything.`,
    { label: 'sim-semantics', phase: 'Investigate', schema: SIM_SCHEMA }),
  () => agent(RECIPE + `\nTASK: Independently verify the audit_missing_sessions root cause AND the safety of the eligible-union fix. (1) Build the FULL-STUDY PIT-eligible union (all validation folds + final holdout) for /tmp/ir2m.yml using optuna/pit_universe.py::plan_pit_symbol_union (build the plan via the walkforward planner the runner uses), NOT just the 5 probe sessions. (2) Sum the audit parquet missing_sessions over that union. (3) Cross-check the real universe/builder.py::eligible_symbols (instrument-class / blocklist / status_active legs) against the CSV daily_eligible proxy. (4) CRITICAL: find any symbol that is ever PIT-eligible across the full study yet has missing_sessions>0 — that would make the fix unsafe. Report counts + named residuals.`,
    { label: 'audit-verify', phase: 'Investigate', schema: AUDIT_SCHEMA }),
  () => agent(RECIPE + `\nTASK: Verify the coverage_missing sparsity claim against the RAW lake (not the supplier abstraction). For a sample of >=8 of the 1111 "traded_later" eligible pairs (e.g. AACI,ABEO,ABX,ACCO,ACEL,ACIC @2025-08-27) read the raw minute parquet and confirm: no bar timestamped in [09:45:00,09:46:00) ET, but >=1 bar later in the session. Quantify how stale the last price is AT 09:45 (gap from last pre-09:45 bar — or prior close — to first post-09:45 trade). Confirm it is NOT a timezone/off-by-one/window artifact. Separately confirm the 94 no_trade_today pairs have a valid prior daily close.`,
    { label: 'coverage-data', phase: 'Investigate', schema: COVERAGE_DATA_SCHEMA }),
]);

phase('Refute');
const [refuteCov, refuteAudit] = await parallel([
  () => agent(RECIPE + `\nPROPOSED FIX for coverage_missing: make the minute-leg coverage criterion carry-forward/staleness-aware (a pair is "covered" at 09:45 if a non-stale price can be established per the sim's own staleness policy — given 0 daily-leg misses and 92% trade later, this passes nearly all eligible pairs), instead of requiring a literal bar in the exact 09:45 minute. Sim-semantics finding: ${JSON.stringify(sim)}. Coverage-data finding: ${JSON.stringify(covdata)}.\nTASK: Be the adversary. Argue the STRONGEST case that this fix is wrong or unsafe — e.g. it masks genuine halts/illiquidity that should disqualify a symbol, it diverges from the sim's actual staleness gate, it lets a non-tradeable name into the study, or the 20.93% hides a real defect. Then judge whether the objection is fatal and what guardrail must accompany the fix.`,
    { label: 'refute-coverage', phase: 'Refute', schema: REFUTE_SCHEMA }),
  () => agent(RECIPE + `\nPROPOSED FIX for audit_missing_sessions: restrict the audit-check denominator (requested_symbols) to the full-study PIT-eligible union before summing missing_sessions — the same §6.6-compatible pattern already applied to the coverage replay checks. Audit-verify finding: ${JSON.stringify(audit)}.\nTASK: Be the adversary. Argue the STRONGEST case that this is wrong or unsafe — e.g. a symbol eligible in one fold but with missing sessions in another window, survivorship/PIT leakage, the audit parquet being stale vs the SIP backfill, or the eligible-union scope being computed inconsistently with how the check would compute it at runtime. Then judge whether the objection is fatal and what guardrail must accompany the fix.`,
    { label: 'refute-audit', phase: 'Refute', schema: REFUTE_SCHEMA }),
]);

phase('Synthesize');
const synthesis = await agent(
  RECIPE +
  `\nTASK: Synthesize a RECOMMENDED FIX PER CHECK for the user to decide on. You have:\n` +
  `SIM SEMANTICS: ${JSON.stringify(sim)}\n` +
  `AUDIT VERIFY: ${JSON.stringify(audit)}\n` +
  `COVERAGE DATA: ${JSON.stringify(covdata)}\n` +
  `REFUTE COVERAGE: ${JSON.stringify(refuteCov)}\n` +
  `REFUTE AUDIT: ${JSON.stringify(refuteAudit)}\n` +
  `Produce a concise Markdown section (suitable to append to docs/audits/2026-06-07_intended_realism_coverage_findings.md) titled "## 10c. Remaining gates: evidence + recommended fix per check". For EACH check give: root cause (one line), the evidence (numbers + file:line), the recommended fix, the adversarial verdict + required guardrails, and an explicit OPEN POLICY DECISION the user must make (for coverage_missing: carry-forward-aware coverage vs exclude-illiquid-pairs vs lower the gate; for audit_missing_sessions: restrict-to-eligible-union vs regenerate-audit). Do NOT overstate: if a finding is medium/low confidence or a refutation demands a guardrail, say so. Return ONLY the Markdown.`,
  { label: 'synthesize', phase: 'Synthesize' });

return { sim, audit, covdata, refuteCov, refuteAudit, synthesis };
