export const meta = {
  name: 'fillmodel-t3-phase1',
  description: 'Phase 1: implement the T3_NBBO_DEPTH real-touch + participation-capped + sqrt-impact fill model (default-off, byte-identical) + unit tests',
  phases: [
    { title: 'Implement', detail: 'add T3 depth-impact fill helper + route T3 + market-path branch + config knobs + unit tests' },
    { title: 'Review', detail: 'adversarial review vs design + byte-identical guarantee' },
    { title: 'Test', detail: 'run ONLY the new + existing fills unit tests (no broad suites)' },
  ],
}

const ENV = `
ENVIRONMENT (you EDIT host source which the container mounts live; DO NOT touch live trading on the Windows host; DO NOT kill jupyter kernels):
- Host source to EDIT: E:/tradingsoftware/quants-lab/research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/sim/fills.py (+ a new/extended test under tests/). Read/Edit on host paths.
- Run pytest in ql-jupyter (mount is live, no reinstall):
    docker exec ql-jupyter bash -lc 'export MSYS_NO_PATHCONV=1; export PYTHONPATH=/quants-lab/research_notebooks/bowaka_v2_lab/src:/quants-lab/research_notebooks/bowaka_common/src; cd /quants-lab/research_notebooks/bowaka_v2_lab && /opt/conda/envs/quants-lab/bin/python -m pytest <PATHS> -q -p no:cacheprovider'
- HARD SCOPE GUARD (a prior implement agent over-ran ~30min by self-running the full integration suite): in the IMPLEMENT phase, run AT MOST a quick import check + the NEW test file. DO NOT run tests/integration, tests/reconcile, tests/scanner, or any broad suite. DO NOT recalibrate/re-approve any golden/snapshot/regression fixture (that is Phase 3, out of scope). Emit your structured summary and stop. The dedicated Test phase runs the fills tests.
`;

const DESIGN = `
LOCKED DESIGN (operator-approved; audit doc §10f). Implement the T3_NBBO_DEPTH real fill model in sim/fills.py. The tier system (ExecutionTier T0-T4, detect_execution_tier), simulate_market_fill (line ~394), simulate_marketable_limit_fill (line ~742), _t1_fill, _minute_dollar_volume, _scan_bar, _fees, _no_fill, FillResult, COST_STRESS_* already exist. The cost model sim/cost_model.py has get_cost_parameters(stress_level).half_spread_bps. QuoteSnapshot has .ask/.bid/.ask_size/.bid_size/.mid.

=== NEW HELPER: _t3_depth_impact_fill ===
Signature (keyword-only): side, requested_qty:int, quote:QuoteSnapshot, minute_bars, scan_ts, participation_cap:float, impact_coef_bps:float, impact_model:str ("sqrt"|"linear"), cost_stress:str, min_order_notional:float, commission_per_share:float, regulatory_fee_bps:float. Returns FillResult.
Logic (buy; mirror for sell using bid/bid_size):
  - touch_size = float(quote.ask_size or 0.0)   # the REAL displayed top-of-book size
  - minute_vol_shares: from the scan minute bar's 'volume' (shares). Use _scan_bar(minute_bars, scan_ts) -> bar['volume'] if present else 0.0. (If you only have dollar volume via _minute_dollar_volume, divide by quote.ask.)
  - cap_shares = participation_cap * minute_vol_shares
  - fillable = min(int(requested_qty), int(max(touch_size, cap_shares)))   # always get the displayed touch; beyond it up to the participation cap; NO fabricated depth
  - if fillable <= 0: return _no_fill("no_liquidity", order_style=..., execution_tier=T3)
  - participation = fillable / minute_vol_shares if minute_vol_shares > 0 else 0.0
  - frac = sqrt(participation) if impact_model=="sqrt" else participation     # math.sqrt
  - impact_bps = float(impact_coef_bps) * frac * COST_STRESS_SLIPPAGE_MULT[cost_stress]
  - half_spread_bps = get_cost_parameters(cost_stress).half_spread_bps   # real spread cost
  - total_bps = half_spread_bps + impact_bps
  - price = round(quote.ask * (1 + total_bps/1e4), 4) for buy (quote.bid*(1 - total_bps/1e4) for sell)
  - notional = fillable * price ; is_partial = fillable < requested_qty
  - if is_partial and notional < min_order_notional: return _no_fill("partial_below_min", order_style=..., execution_tier=T3)
  - commission, regulatory = _fees(notional, commission_per_share=..., qty=fillable, regulatory_bps=regulatory_fee_bps)
  - return FillResult(filled=True, filled_qty=fillable, avg_fill_price=price, slippage_bps_total=round(total_bps,4), notional=round(notional,4), commission, regulatory_fees, is_partial, reason="partial_fill" if is_partial else None, order_style=<caller's>, execution_tier=T3, liquidity_participation_frac=round(participation,6))

=== ROUTE T3 in simulate_marketable_limit_fill ===
Currently T3 falls back to T2 (T1 walk + participation cap). Change: when tier==ExecutionTier.T3_NBBO_DEPTH, use _t3_depth_impact_fill (order_style="marketable_limit") INSTEAD of _t1_fill + the T2 cap block. Thread new params market_impact_coef_bps + market_impact_model into the function signature (defaults: coef 10.0, model "sqrt"). T0/T1/T2/T4 paths UNCHANGED.

=== MARKET-PATH branch in simulate_market_fill ===
Add new optional kwargs: has_nbbo_depth:bool=False, minute_bars=None, scan_ts=None, participation_cap:float=0.10, market_impact_coef_bps:float=10.0, market_impact_model:str="sqrt". At the TOP of the function, if has_nbbo_depth is True: return _t3_depth_impact_fill(... order_style="market" ...) using the real touch + minute volume. When has_nbbo_depth is False (the default), the EXISTING body runs UNCHANGED (byte-identical: the 5%-ADV proxy path). Do NOT alter the existing body.

=== CONFIG KNOBS / DEFAULTS ===
New (read by the consumer in Phase 2, not Phase 1): execution.market_impact_coef_bps (10.0), execution.market_impact_model ("sqrt"), execution.minute_volume_participation_frac already exists (0.10). Phase 1 only adds the fills.py params with these defaults — do NOT change strategy_consumer.py wiring (that is Phase 2; default-off must keep the consumer byte-identical).

=== DEFAULT-OFF / BYTE-IDENTICAL (non-negotiable) ===
With has_nbbo_depth=False everywhere (the Phase-1 default, since the consumer is NOT rewired), simulate_market_fill and simulate_marketable_limit_fill T0/T1/T2/T4 behaviour is BYTE-IDENTICAL to today. The new code is reachable only via has_nbbo_depth=True (T3). Confirm with the existing fills unit tests.

=== TESTS ===
Add tests/unit/test_fills_t3_depth_impact.py covering: (1) touch-only fill when participation_cap*minute_vol < touch; (2) participation cap binds -> partial; (3) sqrt vs linear impact_bps; (4) partial below min_notional -> no_fill; (5) byte-identical: simulate_market_fill(has_nbbo_depth=False) == today for a representative case. Use small synthetic QuoteSnapshot + a 1-row minute_bars DataFrame.
`;

const IMPL_SCHEMA = {
  type: 'object',
  required: ['files_edited', 'helper_summary', 'routing_summary', 'market_path_summary', 'default_off_byte_identical', 'tests_added', 'quick_check_result', 'open_concerns'],
  properties: {
    files_edited: { type: 'array', items: { type: 'string' } },
    helper_summary: { type: 'string' },
    routing_summary: { type: 'string' },
    market_path_summary: { type: 'string' },
    default_off_byte_identical: { type: 'string', description: 'how the has_nbbo_depth=False path is kept byte-identical.' },
    tests_added: { type: 'array', items: { type: 'string' } },
    quick_check_result: { type: 'string', description: 'result of the NEW test file run ONLY (no broad suites).' },
    open_concerns: { type: 'string' },
  },
};

const REVIEW_SCHEMA = {
  type: 'object',
  required: ['verdict', 'matches_design', 'byte_identical_holds', 'sqrt_impact_correct', 'no_fabricated_depth', 'defects', 'must_fix'],
  properties: {
    verdict: { type: 'string', enum: ['sound', 'sound_with_nits', 'needs_fix'] },
    matches_design: { type: 'boolean' },
    byte_identical_holds: { type: 'boolean', description: 'independently verify has_nbbo_depth=False is byte-identical (read the diff; the existing market/T1/T2 bodies must be untouched).' },
    sqrt_impact_correct: { type: 'boolean', description: 'impact = coef*sqrt(filled/minute_vol)*stress; spread added; price = ask*(1+total_bps/1e4).' },
    no_fabricated_depth: { type: 'boolean', description: 'fillable capped at max(touch, cap*minute_vol) — no cent-stepping / ADV-proxy in the T3 path.' },
    defects: { type: 'string' },
    must_fix: { type: 'string' },
  },
};

const TEST_SCHEMA = {
  type: 'object',
  required: ['new_tests', 'existing_fills_tests', 'byte_identical_confirmed', 'regressions', 'verdict'],
  properties: {
    new_tests: { type: 'string', description: 'result of tests/unit/test_fills_t3_depth_impact.py' },
    existing_fills_tests: { type: 'string', description: 'result of the existing fills/cost unit tests (tests/unit -k "fill or cost or execution_tier") — confirm 0 new failures.' },
    byte_identical_confirmed: { type: 'boolean' },
    regressions: { type: 'string' },
    verdict: { type: 'string', enum: ['green', 'not_green'] },
  },
};

phase('Implement');
const impl = await agent(ENV + DESIGN + `\nTASK: Implement Phase 1 in sim/fills.py + add the unit test file. Read the existing functions first. Make surgical edits. Run ONLY a quick import check + the new test file. Return the structured summary. DO NOT run broad suites or touch goldens.`,
  { label: 'implement', phase: 'Implement', schema: IMPL_SCHEMA });

phase('Review');
const review = await agent(ENV + DESIGN + `\nIMPLEMENTER REPORT: ${JSON.stringify(impl)}\nTASK: Adversarially review the git diff of sim/fills.py + the new test vs the locked design. Verify byte-identical default-off (existing bodies untouched), the sqrt-impact math, no fabricated depth in T3, and the participation-cap formula. Cite file:line. Return verdict + must-fix.`,
  { label: 'review', phase: 'Review', schema: REVIEW_SCHEMA });

phase('Test');
const test = await agent(ENV + `\nIMPLEMENTER: ${JSON.stringify(impl)}\nREVIEW: ${JSON.stringify(review)}\nTASK: Run (1) tests/unit/test_fills_t3_depth_impact.py and (2) the existing fills/cost/tier unit tests: \`tests/unit -k "fill or cost or execution_tier or slippage"\`. Confirm the default-off path is byte-identical (0 new failures in the existing tests). DO NOT run integration/reconcile/scanner/broad suites. Report pass/fail counts + verdict.`,
  { label: 'test', phase: 'Test', schema: TEST_SCHEMA });

return { impl, review, test };
