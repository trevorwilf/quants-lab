export const meta = {
  name: 'emit-latch-fok-deepdive',
  description: 'Pressure-test the no-quote-loses-the-signal model against the operator FOK intent: characterize the sim execution model (walk-the-book vs FOK), measure FOK coverage incl. SIZE + staleness/stickiness, selection bias, recommend',
  phases: [
    { title: 'Investigate', detail: 'sim execution model + FOK size/staleness coverage + selection bias' },
    { title: 'Refute', detail: 'adversary challenges the FOK-coverage number + the model-gap claim' },
    { title: 'Synthesize', detail: 'execution-model decision + honest number + recommendation' },
  ],
}

const ENV = `
ENVIRONMENT (read-only; DO NOT edit code, DO NOT touch live trading on the Windows host, DO NOT kill jupyter kernels):
- Run python in ql-jupyter: docker exec ql-jupyter bash -lc 'export MSYS_NO_PATHCONV=1; export PYTHONPATH=/quants-lab/research_notebooks/bowaka_v2_lab/src:/quants-lab/research_notebooks/bowaka_common/src; /opt/conda/envs/quants-lab/bin/python /quants-lab/scripts/YOURFILE.py'. Scratch -> /quants-lab/scripts/ prefixed _wfef_ . Host source: E:/tradingsoftware/quants-lab/research_notebooks/bowaka_v2_lab/src/bowaka_v2_lab/ (Read directly).
- Lake /opt/market_data_cache: quotes quotes/vendor=alpaca/feed=sip/symbol=X/year=Y/month=M/part.parquet (cols symbol,timestamp,bid,ask,bid_size,ask_size,conditions; ~per-minute prevailing NBBO). minute bars bars/.../timeframe=1m/adjustment=raw. daily bars/.../timeframe=1d/adjustment=split_adjusted. Config /tmp/ir2m.yml.
- SCOPE GUARD (CRITICAL — prior agents over-ran ~20min): work ONLY over the 5 probe sessions [2025-08-27,28,29,2025-09-02,2025-09-03]. Build eligible_per_session_map(LAKE, those_5, cfg) ONCE and reuse. DO NOT build the full-study PIT union, DO NOT call plan_pit_symbol_union, DO NOT run broad pytest suites. Finish in a few minutes.

CONTEXT (operator decision): the operator's small-cap momentum strategy is the target; they want to keep as much of the small-cap universe as possible while being realistic. Their stated live intent for a signal whose spread/liquidity isn't there is "probably FILL-OR-KILL (FOK), not a resting limit." FOK = fill COMPLETELY at the touch immediately or cancel entirely (no resting, no walking the book).

ESTABLISHED:
- intended_realism uses quote_fallback_policy=require_real: a missing historical quote at the emit scan -> candidate REJECTED (sim/strategy_consumer.py). max_quote_age_seconds=15.
- The scanner EMIT-LATCHES: scan_loop.py:514-528 increments signal_emits_per_symbol UNCONDITIONALLY at emit, BEFORE the quote is fetched; same_symbol_entries_per_day=1, symbol_cooldown_minutes=390 -> ONE quote shot per (sym,session) at its first-emit scan; a missing quote there loses the signal (NOT re-scanned).
- Single-emit quote-PRESENCE coverage over 5758 PIT-eligible pairs: 77.84% at 15s (first-fresh-bar proxy), middle-scan 56.06% (15s) / 87.58% (60s); mean fresh-bar scan density 66.6% (15s). The 95% gate fails; genuine ~$50-100M ADV needed for 95% quote PRESENCE.
- The sim's FILL model is NOT FOK: fills.py _t1_fill (line 573-602) fills min(qty, ask_size) at the touch then WALKS THE BOOK one cent at a time for the remainder (detect_execution_tier T1_TOP_OF_BOOK). So the sim drops on no-quote but NEVER kills on insufficient size — it pays up. The operator's FOK intent would ALSO kill on insufficient size.
- Sizing (config /tmp/ir2m.yml): sizing_mode=equal_slice, equal_slice_bankroll_fraction=0.8, min_order_notional=500, max_position_as_adv_frac caps (~0.002-0.015). Derive the per-order share qty to test FOK size-sufficiency.
`;

const SIMMODEL_SCHEMA = {
  type: 'object',
  required: ['sim_execution_model', 'is_fok', 'drops_on_no_quote', 'kills_on_insufficient_size', 'size_slippage_model', 'gap_vs_fok', 'evidence', 'confidence'],
  properties: {
    sim_execution_model: { type: 'string', description: 'precise characterization of how the sim fills an accepted candidate (require_real gate, T1 walk-the-book, cent-stepping, fill_rate_cap, adverse selection). cite fills.py / strategy_consumer.py / orders.py file:line.' },
    is_fok: { type: 'boolean' },
    drops_on_no_quote: { type: 'boolean' },
    kills_on_insufficient_size: { type: 'boolean', description: 'does the sim kill (no fill) when NBBO size < order qty, or does it walk the book?' },
    size_slippage_model: { type: 'string', description: 'what price does the size beyond the touch fill at (cent-stepping? capped?), and is that realistic for thin small-caps?' },
    gap_vs_fok: { type: 'string', description: 'the precise realism gap between the sim model and the operator FOK intent (on no-quote AND on size).' },
    evidence: { type: 'string' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
};

const FOKCOV_SCHEMA = {
  type: 'object',
  required: ['order_qty_derivation', 'fok_coverage_pct', 'quote_presence_pct', 'size_binding_share', 'staleness_stickiness', 'evidence', 'confidence'],
  properties: {
    order_qty_derivation: { type: 'string', description: 'how you derived the per-order share qty per (sym,session) from the sizing config (equal_slice 0.8 bankroll, max_position_as_adv_frac, min_order_notional 500). state the bankroll assumption.' },
    fok_coverage_pct: { type: 'number', description: 'fraction of PIT-eligible first-emit scans that would FOK-FILL = quote present within 15s AND ask_size/bid_size >= order qty (complete fill at the touch).' },
    quote_presence_pct: { type: 'number', description: 're-confirmed quote-presence-only single-emit coverage (no size constraint) for comparison.' },
    size_binding_share: { type: 'string', description: 'of the quote-present emits, what fraction FAIL purely on size (NBBO size < order qty)? distribution of NBBO size vs order qty.' },
    staleness_stickiness: { type: 'string', description: 'NBBO stickiness: how often does the prevailing NBBO (bid/ask) change minute-to-minute for these illiquid names? Does a quote within 60s (or longer) reasonably represent the resting NBBO at the emit instant (FOK fillable)? FOK quote-presence at 15s vs 60s.' },
    evidence: { type: 'string', description: 'script + key output + named examples.' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
};

const BIAS_SCHEMA = {
  type: 'object',
  required: ['killed_signals_biased', 'bias_direction', 'dimensions_compared', 'evidence', 'confidence'],
  properties: {
    killed_signals_biased: { type: 'boolean', description: 'Are the (sym,session) emits that would be FOK-killed (no quote or insufficient size) systematically different from the filled ones?' },
    bias_direction: { type: 'string', description: 'On what dimensions (prior ADV, price, volatility/NATR, next-bar/forward return) do killed vs filled differ, and which way? Does dropping them flatter or penalise the backtest?' },
    dimensions_compared: { type: 'string', description: 'the dimensions you compared + the summary stats (killed vs filled).' },
    evidence: { type: 'string' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
};

const REFUTE_SCHEMA = {
  type: 'object',
  required: ['strongest_objection', 'fok_number_robust', 'model_gap_real', 'recommended_execution_model', 'verdict'],
  properties: {
    strongest_objection: { type: 'string', description: 'strongest challenge to the FOK-coverage number and the walk-the-book-vs-FOK gap claim.' },
    fok_number_robust: { type: 'boolean' },
    model_gap_real: { type: 'boolean', description: 'is the sim-walks-the-book vs operator-FOK gap a real realism defect, or is walk-the-book actually the better model for this strategy?' },
    recommended_execution_model: { type: 'string', enum: ['fok', 'walk_the_book', 'either_documented'], description: 'which execution model is most realistic for a small-cap momentum strategy, and why.' },
    verdict: { type: 'string', enum: ['sound', 'sound_with_caveats', 'needs_more_work'] },
  },
};

phase('Investigate');
const [simmodel, fokcov, bias] = await parallel([
  () => agent(ENV + `\nTASK: Characterize the sim's EXACT execution model for an accepted candidate and pinpoint the realism gap vs the operator's FOK intent. Read sim/strategy_consumer.py (resolve_quote/require_real reject), sim/fills.py (detect_execution_tier, _t1_fill walk-the-book + cent-stepping + fill_rate_cap + adverse selection), sim/orders.py / sim/portfolio.py (order qty + entry). State whether it is FOK, whether it drops on no-quote, whether it kills vs walks-the-book on insufficient size, and the size-slippage model. Cite file:line.`,
    { label: 'sim-model', phase: 'Investigate', schema: SIMMODEL_SCHEMA }),
  () => agent(ENV + `\nTASK: Measure the TRUE FOK executability over the 5758 PIT-eligible first-emit scans. (1) Derive the per-order share qty per (sym,session) from the sizing config (equal_slice 0.8 bankroll_fraction, max_position_as_adv_frac, min_order_notional=500; state your bankroll assumption, e.g. read it from the config or assume a representative value and report sensitivity). (2) FOK-fill = a quote present within 15s of the first-emit (first fresh-bar) scan AND the relevant NBBO size (ask_size for a buy) >= order qty. Report fok_coverage_pct, the quote-presence-only %, and what fraction of quote-present emits fail purely on size. (3) NBBO stickiness: how often does the prevailing bid/ask change minute-to-minute for these names; report FOK quote-presence at 15s vs 60s and whether a sticky-NBBO (longer effective staleness) is justified. SCOPE: 5 sessions, cached eligibility.`,
    { label: 'fok-coverage', phase: 'Investigate', schema: FOKCOV_SCHEMA }),
  () => agent(ENV + `\nTASK: Selection-bias check. For the PIT-eligible first-emit scans, split into FOK-killed (no quote within 15s, OR — if you can derive order qty cheaply — insufficient size) vs filled, and compare the two groups on prior ADV, prior close (price), volatility (NATR/ATR or intraday range), and a simple forward proxy (e.g. next-30min or close return from the emit bar). Are the killed signals systematically different, and does dropping them flatter or penalise a backtest? SCOPE: 5 sessions, cached eligibility; keep the forward proxy simple (read minute bars).`,
    { label: 'selection-bias', phase: 'Investigate', schema: BIAS_SCHEMA }),
]);

phase('Refute');
const refute = await agent(ENV + `\nFINDINGS:\nSIM MODEL: ${JSON.stringify(simmodel)}\nFOK COVERAGE: ${JSON.stringify(fokcov)}\nSELECTION BIAS: ${JSON.stringify(bias)}\nTASK: Adversarially challenge. Is the FOK-coverage number robust (order-qty/bankroll assumption, staleness choice, size-data reliability)? Is the sim-walks-the-book-vs-operator-FOK gap a REAL realism defect, or is walk-the-book the more realistic model for a small-cap momentum strategy (you CAN pay up for size; FOK may be too conservative and itself bias the backtest by dropping fillable-with-slippage trades)? Which execution model should the operator use? Give the verdict.`,
  { label: 'refute', phase: 'Refute', schema: REFUTE_SCHEMA });

phase('Synthesize');
const synthesis = await agent(
  `Decision brief for the operator (small-cap momentum; wants max small-cap inclusion + realism; live intent ~FOK). Inputs:\n` +
  `SIM MODEL: ${JSON.stringify(simmodel)}\nFOK COVERAGE: ${JSON.stringify(fokcov)}\nSELECTION BIAS: ${JSON.stringify(bias)}\nREFUTE: ${JSON.stringify(refute)}\n` +
  `TASK: Markdown section "## 10e. Emit-latch / FOK execution model: is 'lose the signal on no-quote' the right model?" covering: (1) is the no-quote-loses-the-signal model realism-faithful to FOK? (yes — FOK = drop, confirmed). (2) the sim models walk-the-book NOT FOK — the precise gap and which is more realistic for small-cap momentum. (3) the TRUE FOK executability number (quote AND size, at the right staleness) vs the quote-presence ~77%. (4) selection bias of killed signals (does the ~23% loss flatter/penalise the backtest). (5) the recommendation + the explicit OPEN POLICY DECISION (execution model FOK vs walk-the-book; the honest coverage number to set the gate to; whether small-cap intended_realism is now defensible). Be honest about confidence. Return ONLY the Markdown.`,
  { label: 'synthesize', phase: 'Synthesize' });

return { simmodel, fokcov, bias, refute, synthesis };
