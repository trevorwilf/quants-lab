"""Offline test suite for ladder_lab_recycle_v11 (no network).

Run:  python3 test_recycle_v11.py   ->  ALL TESTS PASSED
Rerun after ANY edit to the module. Extends test_recycle.py (v10) -- keep
running that one too; v10 stays installed and untouched.
"""
import numpy as np
import pandas as pd

import ladder_lab as ll
import ladder_lab_recycle as lr10
import ladder_lab_recycle_v11 as lr

FAILED = []


def check(name, cond, extra=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name} {extra}")
    if not cond:
        FAILED.append(name)


def synth_bars6(n=2000, seed=3, p0=100.0, vol=0.012, wick=0.004,
                bar_seconds=3600.0, qvol_mean=500.0, trend=0.0):
    rng = np.random.default_rng(seed)
    rets = rng.normal(trend, vol, n)
    c = p0 * np.exp(np.cumsum(rets))
    o = np.roll(c, 1); o[0] = p0
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, wick, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, wick, n)))
    ts = 1.7e9 + np.arange(n) * bar_seconds
    qv = np.abs(rng.normal(qvol_mean, qvol_mean / 3, n))
    return np.column_stack([ts, o, h, l, c, qv])


CFG = lr.recycle_default_config("nonkyc")
CFG["rc_n_candidates"] = 40
CFG["rc_stage2_top_k"] = 4
CFG["rc_book_spread_in_slip"] = True
KW = dict(fund=1000.0, quote_frac=0.5, fee=0.002, slip=0.001,
          cooldown_seconds=3600, refresh_seconds=43200,
          min_order_quote=1.0, event_refresh=True, body_only=False)
BUYS = [95.0, 92.0, 89.0, 86.0]
SELLS = [105.0, 108.0, 111.0, 115.0]

# ----------------------------------------------------------------------
# 1. Kernel: parity + v10 equivalence + ledger conservation
# ----------------------------------------------------------------------
check("v11 parity + v10-equivalence sweep", lr.recycle_v11_parity_check(verbose=False))

bars = synth_bars6()
r10 = lr10.recycle_sim(bars[:, :5], BUYS, SELLS, **KW)
r11_off = lr.recycle_sim_v11(bars, BUYS, SELLS, **KW,
                             pen_frac=0.0, tick=0.0, vol_cap_frac=0.0)
check("features-off v11 == v10 (pnl)", abs(r10["pnl"] - r11_off["pnl"]) < 1e-9,
      f"{r10['pnl']:.6f} vs {r11_off['pnl']:.6f}")
check("features-off v11 == v10 (fills)", r10["bf"] == r11_off["bf"] and r10["sf"] == r11_off["sf"])
check("features-off v11 == v10 (equity curve)", bool(np.allclose(r10["eq"], r11_off["eq"], atol=1e-9)))

r11_on = lr.recycle_sim_v11(bars, BUYS, SELLS, **KW,
                            pen_frac=0.0005, tick=0.01, vol_cap_frac=0.25)
final = r11_on["quote"] + r11_on["base"] * bars[-1, 4]
check("ledger consistency (final eq == quote+base*close)",
      abs(final - r11_on["eq"][-1]) < 1e-6)
check("fees non-negative and bounded", 0.0 <= r11_on["fees"] < 1000.0,
      f"fees={r11_on['fees']:.2f}")

# ----------------------------------------------------------------------
# 2. Penetration: monotone fill reduction; huge pen kills all fills
# ----------------------------------------------------------------------
t0 = lr.recycle_sim_v11(bars, BUYS, SELLS, **KW, pen_frac=0.0, vol_cap_frac=0.0)["trades"]
t1 = lr.recycle_sim_v11(bars, BUYS, SELLS, **KW, pen_frac=0.002, vol_cap_frac=0.0)["trades"]
t2 = lr.recycle_sim_v11(bars, BUYS, SELLS, **KW, pen_frac=0.02, vol_cap_frac=0.0)["trades"]
check("penetration reduces fills monotonically", t0 >= t1 >= t2, f"{t0} >= {t1} >= {t2}")
t3 = lr.recycle_sim_v11(bars, BUYS, SELLS, **KW, pen_frac=10.0, vol_cap_frac=0.0)["trades"]
check("absurd penetration -> zero fills", t3 == 0, f"trades={t3}")

# ----------------------------------------------------------------------
# 3. Volume cap: partial fills, budget respected, NaN volume uncapped
# ----------------------------------------------------------------------
tiny = bars.copy(); tiny[:, 5] = 5.0                      # $5/bar traded
rc = lr.recycle_sim_v11(tiny, BUYS, SELLS, **KW, pen_frac=0.0, vol_cap_frac=0.2)
check("tight volume cap caps fills", rc["vol_capped_fills"] > 0,
      f"capped={rc['vol_capped_fills']}")
check("capped turnover <= sum(budget)",
      rc["turnover_x"] * 1000.0 <= 0.2 * 5.0 * len(tiny) + 1e-6,
      f"turnover={rc['turnover_x']*1000:.2f} budget={0.2*5.0*len(tiny):.2f}")
nanv = bars.copy(); nanv[:, 5] = np.nan
rn = lr.recycle_sim_v11(nanv, BUYS, SELLS, **KW, pen_frac=0.0, vol_cap_frac=0.25)
r_off = lr.recycle_sim_v11(bars, BUYS, SELLS, **KW, pen_frac=0.0, vol_cap_frac=0.0)
check("NaN volume -> uncapped (== cap off)", abs(rn["pnl"] - r_off["pnl"]) < 1e-9
      and rn["vol_capped_fills"] == 0)
huge = bars.copy(); huge[:, 5] = 1e12
rh = lr.recycle_sim_v11(huge, BUYS, SELLS, **KW, pen_frac=0.0, vol_cap_frac=0.25)
check("huge volume -> cap never binds (== cap off)",
      abs(rh["pnl"] - r_off["pnl"]) < 1e-9 and rh["vol_capped_fills"] == 0)

# ----------------------------------------------------------------------
# 4. ensure6 / regularize_bars6
# ----------------------------------------------------------------------
b5 = bars[:, :5]
e6 = lr.ensure6(b5)
check("ensure6 pads NaN volume", e6.shape[1] == 6 and np.isnan(e6[:, 5]).all())
gappy = np.delete(bars, np.arange(100, 160), axis=0)
reg, fill = lr.regularize_bars6(gappy)
check("regularize fills gaps on the grid", len(reg) == len(bars) and 0.0 < fill < 0.1,
      f"n={len(reg)} fill={fill:.3f}")
check("gap bars are flat with zero volume",
      bool(np.all(reg[100:160, 1] == reg[100:160, 4]))
      and bool(np.all(reg[100:160, 5] == 0.0)))
# collision: duplicate a timestamp with a wilder bar -> aggregated, not dropped
dup = bars.copy()
dup[50, 0] = dup[49, 0]
dup[50, 2] = dup[49, 2] * 1.10       # higher high in the colliding bar
reg2, _ = lr.regularize_bars6(dup)
slot = np.argmin(np.abs(reg2[:, 0] - bars[49, 0]))
check("collision aggregates (max high kept, volume summed)",
      abs(reg2[slot, 2] - dup[50, 2]) < 1e-9
      and abs(reg2[slot, 5] - (dup[49, 5] + dup[50, 5])) < 1e-6)

# ----------------------------------------------------------------------
# 5. Slip: book spread joins search slip (v10 only used Roll + floor)
# ----------------------------------------------------------------------
s_no = lr.effective_slip_v11(bars, CFG, book_half_spread_pct=0.0)
s_bk = lr.effective_slip_v11(bars, CFG, book_half_spread_pct=0.8)   # 0.8%/side
check("book half-spread raises effective slip", s_bk >= 0.008 - 1e-12 and s_bk > s_no,
      f"{s_no:.4f} -> {s_bk:.4f}")
cfg_off = dict(CFG, rc_book_spread_in_slip=False)
check("book-spread knob can be disabled",
      abs(lr.effective_slip_v11(bars, cfg_off, 0.8) - s_no) < 1e-12)

# ----------------------------------------------------------------------
# 6. Zig-zag harvest: exact swing count on a synthetic oscillator
# ----------------------------------------------------------------------
t = np.arange(0, 12000)
osc = 100.0 * (1.0 + 0.05 * np.sin(2 * np.pi * t / 500.0))   # +-5%, 24 cycles
ts = 1.7e9 + t * 3600.0
ob = np.column_stack([ts, osc, osc * 1.001, osc * 0.999, osc,
                      np.full(len(t), 1e6)])
sw = lr.zigzag_swings(osc, 4.0)      # 4% gap inside a +-5% sine
check("zigzag counts ~2 swings per cycle", 40 <= sw <= 50, f"swings={sw}")
hv = lr.grid_harvest(ob, CFG)
check("harvest positive on a clean oscillator", hv["harvest_best_pct_mo"] > 0,
      str(hv))
flat = ob.copy(); flat[:, 1:5] = 100.0
hv2 = lr.grid_harvest(flat, CFG)
check("harvest zero on a flat series", hv2["harvest_best_pct_mo"] <= 0.0, str(hv2))

# ----------------------------------------------------------------------
# 7. Candidate re-anchoring preserves relative offsets
# ----------------------------------------------------------------------
cand = dict(anchor=100.0, buy_prices=[98.0, 95.0, 90.0],
            sell_prices=[103.0, 108.0, 115.0],
            bw=np.array([1.0, 1.0, 1.0]), sw=np.array([1.0, 1.0, 1.0]),
            n_buy=3, n_sell=3, family="pct", spacing_curve="linear",
            weight_curve="equal", candidate_id="t")
c2 = lr.rebuild_candidate_at_anchor(cand, 200.0, pdec=4)
check("re-anchor doubles prices at 2x anchor",
      c2 is not None and np.allclose(c2["buy_prices"], [196.0, 190.0, 180.0])
      and np.allclose(c2["sell_prices"], [206.0, 216.0, 230.0]), str(c2 and c2["buy_prices"]))
check("re-anchor records provenance", c2["reanchored_from"] == 100.0
      and c2["anchor"] == 200.0)

# ----------------------------------------------------------------------
# 8. Holdout split: fit never sees the tail; boundaries exact
# ----------------------------------------------------------------------
CFG_H = dict(CFG)
CFG_H["rc_train_days"] = 60
CFG_H["rc_holdout_days"] = 15.0
long_bars = synth_bars6(n=24 * 200, seed=9)               # 200 days hourly
dep = lr.deploy_fit_with_holdout(long_bars, CFG_H, pdec=4, label="T")
check("holdout evaluated", dep["holdout"] is not None)
cut = long_bars[-1, 0] - 15 * 86400.0
check("fit_span ends at the holdout cut", abs(dep["fit_span"][1] - cut) < 3601.0,
      f"{dep['fit_span'][1]:.0f} vs {cut:.0f}")
check("fit anchor predates the holdout",
      dep["fit"]["best"]["anchor"] > 0 and dep["holdout"]["days"] >= 13.0,
      f"ho_days={dep['holdout']['days']}")
check("deployed ladder re-anchored at current price",
      dep["deployed"].get("reanchored_from") is not None
      or dep["deployed"]["anchor"] == dep["fit"]["best"]["anchor"])
short = synth_bars6(n=24 * 30, seed=9)                    # 30 days: too short
dep2 = lr.deploy_fit_with_holdout(short, CFG_H, pdec=4, label="T2")
check("too-short history -> holdout skipped, fit on all", dep2["holdout"] is None)
check("holdout gate flags the missing holdout",
      lr.holdout_gate(dep2["holdout"], CFG_H) is not None)
ho_bad = dict(dep["holdout"], edge_pct=-9.0, active=True)
check("holdout gate fails a deep-negative active holdout",
      lr.holdout_gate(ho_bad, CFG_H) is not None)
ho_ok = dict(dep["holdout"], edge_pct=1.0, active=True)
check("holdout gate passes a positive active holdout",
      lr.holdout_gate(ho_ok, CFG_H) is None)
ho_dorm = dict(dep["holdout"], edge_pct=0.0, active=False, trades=0, in_band_pct=0.0)
check("dormant holdout is flagged (no evidence)",
      lr.holdout_gate(ho_dorm, CFG_H) is not None)

# ----------------------------------------------------------------------
# 9. Blocks: in_fit tagging + clean gates
# ----------------------------------------------------------------------
res = lr.recycle_sim_v11(long_bars, [95, 90, 85], [105, 110, 118], **KW)
fit_span = (long_bars[-1, 0] - 75 * 86400.0, long_bars[-1, 0] - 15 * 86400.0)
bt = lr.block_table_v11(res, 15.0, band=(85.0, 118.0), fit_span=fit_span)
check("block table has in_fit column", "in_fit" in bt.columns and len(bt) >= 10,
      f"blocks={len(bt)}")
n_fit = int(bt.in_fit.sum())
check("~4 blocks tagged in-fit for a 60d window", 3 <= n_fit <= 6, f"in_fit={n_fit}")
ok_all, fails, summ = lr.block_gates_v11(bt, CFG)
check("clean_* fields present in gate summary",
      "n_clean_blocks" in summ and any(k.startswith("clean_") for k in summ))
few = bt.copy(); few["in_fit"] = True; few.loc[few.index[:2], "in_fit"] = False
ok2, fails2, _ = lr.block_gates_v11(few, CFG)
check("too few clean blocks fails with a clean: gate",
      (not ok2) and any(f.startswith("clean:") for f in fails2), str(fails2[:2]))

# ----------------------------------------------------------------------
# 10. Search / WF / report / finalize round trip (offline, synthetic)
# ----------------------------------------------------------------------
fit = lr.search_ladder_v11(lr10.slice_days(long_bars, 60) if hasattr(lr10, "slice_days")
                           else long_bars, CFG, pdec=4, label="S", book_half=0.1)
check("search returns a candidate + overfit telemetry",
      fit["best"] is not None and "fit_score_gap" in fit,
      f"gap={fit['fit_score_gap']}")
check("search records book spread provenance",
      fit.get("book_half_spread_pct") == 0.1)

rep = lr.frozen_ladder_report_v11(long_bars, fit["best"], CFG, label="R",
                                  book_half=0.1, pdec=4, fit_span=fit_span)
s = rep["summary"]
v10_fields = ("pnl_pct", "hold_pct", "edge_pct", "maxdd", "trades",
              "trades_per_month", "endinv", "fees", "stress_pnl_pct",
              "stress_edge_pct", "stress_trades", "slip_used_pct",
              "candle_gap_fill", "edge_pos_rate", "abs_pos_rate",
              "worst_block_edge", "median_trades_per_block", "two_sided_rate",
              "n_blocks", "n_active_blocks")
check("report keeps every v10 summary field", all(k in s for k in v10_fields),
      str([k for k in v10_fields if k not in s]))
check("report adds v11 fields",
      all(k in s for k in ("vol_capped_fills", "book_half_spread_pct",
                           "n_clean_blocks", "fill_model")))

wf = lr.rolling_walkforward_v11(long_bars, dict(CFG, rc_min_folds=2), pdec=4,
                                label="W", book_half=0.1)
check("WF produces folds with v10 columns + vol_capped_fills",
      wf["n_folds"] >= 2 and "vol_capped_fills" in wf["folds"].columns,
      f"folds={wf['n_folds']}")

# finalize with a stubbed universe (offline)
class _StubCache(dict):
    pass

uni = dict(exchange="nonkyc", df=pd.DataFrame([dict(pairkey="TST/USDT",
           vol_usd=250000.0, quote="USDT")]),
           base_of={"TST/USDT": "TST"}, quote_of={"TST/USDT": "USDT"},
           pdec={"TST/USDT": 4}, min_qty={"TST/USDT": float("nan")},
           last_of={"TST/USDT": float(long_bars[-1, 4])},
           usd_per_quote={"USDT": 1.0}, quote_of_map={},
           pair_alt={})
_orig_depth = ll.depth_info
_orig_fund = lr10._fund_sizing
ll.depth_info = lambda u, pk, band=0.02: (0.2, 50000.0)
lr10._fund_sizing = lambda u, pk, cfg: (1000, 0.2, 50000.0, 250000.0)
try:
    ev = dict(pair="TST/USDT", src="synthetic", granularity="1h",
              search_granularity="1h", wf=wf, fit=fit, report=rep,
              holdout=dep["holdout"], deployed=dict(fit["best"]),
              deploy_anchor=float(long_bars[-1, 4]),
              book_half_spread_pct=0.1, harvest=lr.grid_harvest(long_bars, CFG))
    final_df, configs = lr.finalize_v11({"TST/USDT": ev}, uni, CFG)
    check("finalize emits one row + config", len(final_df) == 1 and len(configs) == 1)
    row = final_df.iloc[0]
    v10_cols = ("base", "validation", "rungs", "family", "pnl_pct", "hold_pct",
                "edge_pct", "edge_pos_rate", "abs_pos_rate", "worst_block_edge",
                "med_trades_per_block", "trades", "maxdd", "endinv",
                "stress_edge_pct", "wf_pass", "max_fund", "gates",
                "slip_used_pct", "data_suspect", "n_active_blocks")
    check("final summary keeps every v10 column",
          all(c in final_df.columns for c in v10_cols),
          str([c for c in v10_cols if c not in final_df.columns]))
    check("final summary adds v11 columns",
          all(c in final_df.columns for c in
              ("holdout_edge_pct", "n_clean_blocks", "clean_edge_pos_rate",
               "vol_capped_fills", "harvest_best_pct_mo", "fit_score_gap")))
    cfg0 = configs[0]
    for k in ("symbol", "trading_pair", "exchange", "validation", "gates",
              "passive_order_placement", "max_fund_value_quote",
              "total_amount_quote", "buy_prices", "sell_prices",
              "buy_amounts_pct", "sell_amounts_pct", "engine",
              "block_consistency", "walkforward"):
        if k not in cfg0:
            check(f"config key {k}", False)
            break
    else:
        check("config keeps every v10 key (+ holdout/harvest)", True)
    md = lr.render_copy_paste_markdown(configs)      # v10 renderer, unchanged
    check("copy/paste md format intact (v10 renderer)",
          "### Ladder-only copy/paste block" in md
          and "buy_prices:" in md and "sell_amounts_pct:" in md
          and "### Optional sizing/cap block (clean reseed only)" in md)
    check("copy/paste md uses v10 title verbatim",
          "Suggested ladder copy/paste values (v10 recycle engine)" in md)
    import tempfile, os
    with tempfile.TemporaryDirectory() as td:
        written = lr.save_v11_outputs(os.path.join(td, "TEST_v11"), final_df,
                                      configs, wf["folds"], None,
                                      {"TST/USDT": rep["blocks"]},
                                      metadata=dict(unit_test=True))
        names = [os.path.basename(w) for w in written]
        check("saver writes the v10 artifact set (+holdout csv)",
              any("final_summary" in n for n in names)
              and any("copy_paste_ladders.md" in n for n in names)
              and any("deploy_config.json" in n for n in names)
              and any("holdout_summary" in n for n in names)
              and any("block_details" in n for n in names), str(names))
        import json as _json
        with open([w for w in written if w.endswith("deploy_config.json")][0]) as f:
            dj = _json.load(f)
        check("deploy json records v11 engine provenance",
              dj["engine"] == "ladder_lab_recycle_v11"
              and dj["configs"][0]["engine"]["fill_model"] == "v11")
finally:
    ll.depth_info = _orig_depth
    lr10._fund_sizing = _orig_fund

# ----------------------------------------------------------------------
# 11. v11 fill model is strictly more conservative on thin synthetic books
# ----------------------------------------------------------------------
thin = synth_bars6(n=3000, seed=5, qvol_mean=20.0)        # ~$20/bar traded
cfg_v10mode = dict(CFG, rc_v11_fill_model=False)
lad = dict(buy_prices=[95, 92, 89], sell_prices=[105, 108, 112],
           bw=None, sw=None, pdec=4)
r_v10m = lr.run_ladder_v11(thin, lad, cfg_v10mode, slip=0.001, pdec=4)
r_v11m = lr.run_ladder_v11(thin, lad, CFG, slip=0.001, pdec=4)
# NOTE: with partial fills the fill COUNT can rise (many small fills); the
# conservatism claim is about NOTIONAL traded and harvested edge, not count.
check("v11 model turnover <= v10 model on thin books",
      r_v11m["turnover_x"] <= r_v10m["turnover_x"] + 1e-9,
      f"v11={r_v11m['turnover_x']:.3f}x v10={r_v10m['turnover_x']:.3f}x "
      f"capped_fills={r_v11m['vol_capped_fills']}")
# On a PROFITABLE oscillation, thin volume must cap the harvest (the DOGS
# failure mode: sim happily "fills" size the book never traded). On losing
# series the cap can legitimately RAISE edge (it stops you buying the knife).
osc_thin = ob.copy()
osc_thin[:, 5] = 20.0                                     # ~$20/bar traded
lad_o = dict(buy_prices=[97.0, 96.0], sell_prices=[103.0, 104.0],
             bw=None, sw=None, pdec=4)
p_v10m = lr.run_ladder_v11(osc_thin, lad_o, cfg_v10mode, slip=0.001, pdec=4)
p_v11m = lr.run_ladder_v11(osc_thin, lad_o, CFG, slip=0.001, pdec=4)
check("thin book caps harvest of a profitable oscillation",
      p_v11m["pnl_pct"] < p_v10m["pnl_pct"] and p_v11m["pnl_pct"] < 0.5 * p_v10m["pnl_pct"],
      f"v11={p_v11m['pnl_pct']:.2f}% v10={p_v10m['pnl_pct']:.2f}%")

# ----------------------------------------------------------------------
# 12. v11.1: quote-unit conversion, two-sided mode, snapshot reuse, verify_books
# ----------------------------------------------------------------------
check("v11.1 knobs present", CFG.get("min_vol_usd") == 10000.0
      and CFG.get("rc_gate_two_sided_mode") == "either")

uni_btc = dict(uni)
uni_btc["quote_of"] = {"TST/BTC": "BTC"}
uni_btc["usd_per_quote"] = {"BTC": 100000.0}
check("quote_usd_rate BTC", abs(lr.quote_usd_rate(uni_btc, "TST/BTC") - 100000.0) < 1e-6)
cfg_b, rate = lr.quote_scaled_cfg(uni_btc, "TST/BTC", CFG)
check("quote-scaled fund/min-order (BTC pair: $1000 -> 0.01 BTC)",
      abs(cfg_b["fund_usd"] - 0.01) < 1e-12
      and abs(cfg_b["rc_min_order_quote"] - 1e-5) < 1e-18 and rate == 100000.0)
cfg_u, rate_u = lr.quote_scaled_cfg(uni, "TST/USDT", CFG)
check("USD-stable pair unscaled", cfg_u is CFG and rate_u == 1.0)
check("fund_quote_str formats", lr.fund_quote_str(200.0, 1.0) == 200
      and lr.fund_quote_str(0.0123456789, 1e5) == 0.0123457)

# quote-scaled sim actually trades on a BTC-priced market (v11.0 was inert)
btc_bars = synth_bars6(n=1500, seed=7, p0=0.005, vol=0.01, qvol_mean=0.05)  # BTC units
lad_b = dict(buy_prices=[0.00475, 0.0045], sell_prices=[0.00525, 0.0055],
             bw=None, sw=None, pdec=8)
r_wrong = lr.run_ladder_v11(btc_bars, dict(lad_b, fund=1000.0,
                                           min_order_quote=1.0), CFG, pdec=8)
r_right = lr.run_ladder_v11(btc_bars, dict(lad_b, fund=cfg_b["fund_usd"],
                                           min_order_quote=cfg_b["rc_min_order_quote"]),
                            CFG, pdec=8)
check("BTC-quoted pair trades once fund is in quote units",
      r_right["trades"] > 0 and abs(r_right["pnl_pct"]) > 1e-6,
      f"right={r_right['trades']} wrong={r_wrong['trades']} "
      f"(wrong pnl%={r_wrong['pnl_pct']:.4f})")

# two-sided mode
def _rep_stub(fails):
    return dict(failed_gates=list(fails), passed=(not fails),
                summary=dict())
ts_fail = "two_sided_rate 0.36 < 0.5 (active blocks)"
ts_fail_c = "clean: two_sided_rate 0.33 < 0.5 (active blocks)"
ho_two = dict(two_sided=True, active=True, buy_fills=5, sell_fills=7)
ho_one = dict(two_sided=False, active=True, buy_fills=9, sell_fills=0)
r = lr.apply_two_sided_mode(_rep_stub([ts_fail, ts_fail_c]), ho_two,
                            dict(CFG, rc_gate_two_sided_mode="either"))
check("'either': holdout two-sided waives block two-sided fails",
      r["passed"] and not r["failed_gates"]
      and r["summary"].get("two_sided_waived_by_holdout"))
r = lr.apply_two_sided_mode(_rep_stub([ts_fail, "thin book ($5)"]), ho_two,
                            dict(CFG, rc_gate_two_sided_mode="either"))
check("'either': other gates survive the waiver",
      (not r["passed"]) and r["failed_gates"] == ["thin book ($5)"])
r = lr.apply_two_sided_mode(_rep_stub([ts_fail]), ho_one,
                            dict(CFG, rc_gate_two_sided_mode="either"))
check("'either': one-sided holdout does NOT waive",
      (not r["passed"]) and ts_fail in r["failed_gates"])
r = lr.apply_two_sided_mode(_rep_stub([ts_fail]), ho_two,
                            dict(CFG, rc_gate_two_sided_mode="blocks"))
check("'blocks' mode untouched", (not r["passed"]) and r["failed_gates"] == [ts_fail])
r = lr.apply_two_sided_mode(_rep_stub([ts_fail]), ho_one,
                            dict(CFG, rc_gate_two_sided_mode="holdout"))
check("'holdout' mode: block fail dropped, holdout fail added",
      (not r["passed"]) and len(r["failed_gates"]) == 1
      and "holdout not two-sided" in r["failed_gates"][0])
r = lr.apply_two_sided_mode(_rep_stub([]), ho_two,
                            dict(CFG, rc_gate_two_sided_mode="either"))
check("no fails -> untouched", r["passed"] and not r["failed_gates"])

# verify_books with stubbed BOOKS (flaky + thin classification) -- v11.2:
# verify_books now pulls raw books via fetch_orderbook, not a scalar snapshot.
def _mkbook(mid, notional):
    """Synthetic book with `notional` USD resting within +-1% of mid."""
    q = notional / 4.0
    return dict(bids=[(mid * 0.995, q / (mid * 0.995)), (mid * 0.99, q / (mid * 0.99))],
                asks=[(mid * 1.005, q / (mid * 1.005)), (mid * 1.01, q / (mid * 1.01))])

_bookseq = {"GOOD/USDT": [_mkbook(100, 8000), _mkbook(100, 9000), _mkbook(100, 8500)],
            "FLKY/USDT": [_mkbook(100, 100), _mkbook(100, 4000), _mkbook(100, 90)],
            "THIN/USDT": [_mkbook(100, 50), _mkbook(100, 60), _mkbook(100, 40)]}
_bcalls = {k: 0 for k in _bookseq}
_orig_fetch_ob = lr.fetch_orderbook
def _fake_ob(u, pk, c):
    i = _bcalls[pk]; _bcalls[pk] += 1
    return _bookseq[pk][i % len(_bookseq[pk])]
lr.fetch_orderbook = _fake_ob
try:
    vb = lr.verify_books(uni, list(_bookseq), CFG, samples=3, pause=0.0)
finally:
    lr.fetch_orderbook = _orig_fetch_ob
vb = vb.set_index("market")
check("verify_books: good book not thin, not flaky",
      vb.loc["GOOD/USDT", "thin_med"] == False and vb.loc["GOOD/USDT", "flaky"] == False)
check("verify_books: flaky book flagged", vb.loc["FLKY/USDT", "flaky"] == True)
check("verify_books: thin book flagged on the median",
      vb.loc["THIN/USDT", "thin_med"] == True and vb.loc["THIN/USDT", "flaky"] == False)
check("verify_books: size suggestion present",
      vb.loc["GOOD/USDT", "size_suggestion"] > 0)

# finalize reuses the SNAPSHOT (no fresh depth call) + quote conversion
uni2 = dict(uni)
uni2["quote_of"] = {"TST/USDT": "BTC"}          # pretend BTC-quoted for export
uni2["usd_per_quote"] = {"BTC": 100000.0}
def _boom(u, pk, band=0.02):
    raise RuntimeError("finalize must NOT re-sample the book")
ll.depth_info = _boom
lr10._fund_sizing = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no fresh sizing"))
try:
    ev2 = dict(ev, spread_pct_sampled=0.4, depth_usd_sampled=50000.0,
               depth_used=50000.0, depth_basis="ladder_band",
               depth_ladder_band=50000.0,
               book_snapshot=dict(book_total_usd=90000.0),
               quote_usd_rate=100000.0)
    fdf2, cfgs2 = lr.finalize_v11({"TST/USDT": ev2}, uni2, CFG)
    row2 = fdf2.iloc[0]
    check("finalize works with stored snapshot only (no live call)",
          len(fdf2) == 1 and row2["spread_pct"] == 0.4
          and row2["depth_2pct"] == 50000.0)
    mfq = cfgs2[0]["max_fund_value_quote"]
    check("export fund in QUOTE units (USD/1e5), USD kept alongside",
          isinstance(mfq, float) and abs(mfq - row2["max_fund"] / 1e5) < 1e-9
          and cfgs2[0]["max_fund_value_usd"] == row2["max_fund"],
          f"quote={mfq} usd={row2['max_fund']}")
    check("quote rate recorded in row + config",
          row2["quote_usd_rate"] == 1e5 and cfgs2[0]["quote_usd_rate"] == 1e5)
    md2 = lr.render_copy_paste_markdown(cfgs2)
    check("copy/paste sizing block carries quote-unit fund",
          f"max_fund_value_quote: {mfq}" in md2)
finally:
    ll.depth_info = _orig_depth
    lr10._fund_sizing = _orig_fund


# ----------------------------------------------------------------------
# 13. v11.1b: multi-file JSONL collection + v11 live-vs-sim comparison
# ----------------------------------------------------------------------
import tempfile, os
_fills_a = pd.DataFrame(dict(ts=[1.70e9, 1.70e9 + 86400], side=["buy", "sell"],
                             price=[100.0, 105.0], amount=[1.0, 1.0]))
_fills_b = pd.DataFrame(dict(ts=[1.70e9 + 86400, 1.70e9 + 2 * 86400],  # overlaps a
                             side=["sell", "buy"],
                             price=[105.0, 99.0], amount=[1.0, 2.0]))
_orig_extract = lr.extract_fills_from_jsonl
with tempfile.TemporaryDirectory() as td:
    pa = os.path.join(td, "diag_2026a.jsonl"); open(pa, "w").write("{}\n")
    pb = os.path.join(td, "diag_2026b.jsonl"); open(pb, "w").write("{}\n")
    _map = {pa: _fills_a, pb: _fills_b}
    lr.extract_fills_from_jsonl = lambda p, max_lines=500000: _map[str(p)].copy()
    try:
        merged = lr.collect_jsonl_fills(os.path.join(td, "diag_*.jsonl"))
        check("glob collects both files, dedupes the overlap",
              len(merged) == 3 and set(merged.source_file) == {pa, pb},
              f"n={len(merged)}")
        check("merged fills sorted by ts",
              bool((merged.ts.diff().dropna() >= 0).all()))
        merged2 = lr.collect_jsonl_fills([pa, pb, pa])
        check("list input + duplicate file entries -> same result",
              len(merged2) == 3)
        missing = lr.collect_jsonl_fills(os.path.join(td, "nope_*.jsonl"))
        check("no matching files -> empty frame, no crash", missing.empty)
    finally:
        lr.extract_fills_from_jsonl = _orig_extract

check("sufficiency: thin set flagged",
      "TOO THIN" in lr.fills_sufficiency(_fills_a))
_big = pd.DataFrame(dict(ts=1.70e9 + np.arange(80) * 43200.0,
                         side=["buy", "sell"] * 40,
                         price=np.full(80, 100.0), amount=np.ones(80)))
check("sufficiency: 80 fills / 40d = solid",
      "solid" in lr.fills_sufficiency(_big))

_live = pd.DataFrame(dict(ts=bars[100, 0] + np.arange(40) * 43200.0,
                          side=["buy", "sell"] * 20,
                          price=np.full(40, 100.0), amount=np.ones(40)))
cmp_ = lr.compare_live_vs_sim_v11(_live, bars, dict(
    buy_prices=[95, 92, 89], sell_prices=[105, 108, 112], bw=None, sw=None),
    CFG, pdec=4, book_half=0.1)
check("compare_live_vs_sim_v11 returns ratio + v11 provenance",
      "sim_over_live_fill_ratio" in cmp_ and cmp_.get("fill_model") == "v11"
      and "fills_sufficiency" in cmp_, str({k: cmp_[k] for k in list(cmp_)[:4]}))

# ----------------------------------------------------------------------
# 14. v11.1.2: range_ladder schema extractor + glob-safe sniff helper
# ----------------------------------------------------------------------
import tempfile as _tf, os as _os, json as _json
_fill_ev = dict(event_type="range_ladder_fill_booked", ts_ms=1783837415442,
                side="BUY", d_base="0.016", d_quote="5.18416",
                d_fees="0.01036832", level_id="buy_324.01",
                executor_id="9H4gT31j", trading_pair="XMR-USDT",
                connector="nonkyc")
_sell_ev = dict(_fill_ev, ts_ms=1783840000000, side="SELL", d_base="0.024",
                d_quote="7.88616", level_id="sell_328.59")
_noise = [dict(event_type="range_ladder_diagnostic_heartbeat", ts_ms=1),
          dict(event_type="range_ladder_side_refresh", ts_ms=2),
          dict(event_type="range_ladder_buy_action", ts_ms=3,
               price="324.01", amount="0.016")]
with _tf.TemporaryDirectory() as td:
    p = _os.path.join(td, "range_inventory_ladder_xmr_usdt_diagnostic.jsonl")
    with open(p, "w") as f:
        for r in (_noise[:2] + [_fill_ev] + _noise[2:] + [_sell_ev]):
            f.write(_json.dumps(r) + "\n")
        f.write("not json at all\n")
    df = lr.extract_fills_range_ladder(p)
    check("range_ladder extractor finds exactly the booked fills",
          len(df) == 2 and list(df.side) == ["buy", "sell"], f"n={len(df)}")
    check("price derived from d_quote/d_base",
          abs(df.iloc[0].price - 324.01) < 1e-6
          and abs(df.iloc[1].price - 328.59) < 1e-6)
    check("amounts and fees carried",
          abs(df.iloc[0].amount - 0.016) < 1e-12 and df.iloc[0].fees > 0)
    check("buy_action noise NOT mistaken for fills",
          not (df.ts == 3).any())
    merged = lr.collect_jsonl_fills(_os.path.join(td, "range_*.jsonl"))
    check("collect prefers the schema-exact extractor via glob",
          len(merged) == 2 and "source_file" in merged.columns)
    check("first_existing resolves globs", lr.first_existing(
          _os.path.join(td, "range_*.jsonl")) == p)
    check("first_existing None on no match",
          lr.first_existing(_os.path.join(td, "nope_*.jsonl")) is None)
    # missing d_quote -> falls back to level_id price
    p2 = _os.path.join(td, "range_lvl.jsonl")
    bad = dict(_fill_ev); bad.pop("d_quote")
    open(p2, "w").write(_json.dumps(bad) + "\n")
    df2 = lr.extract_fills_range_ladder(p2)
    check("level_id price fallback works",
          len(df2) == 1 and abs(df2.iloc[0].price - 324.01) < 1e-6)

# ----------------------------------------------------------------------
# 15. v11.1.3 regressions: NaN-volume survives regularize (daily-market killer)
# ----------------------------------------------------------------------
b5only = synth_bars6(n=200, seed=21, bar_seconds=86400.0)[:, :5]   # Nx5, daily
b6 = lr.ensure6(b5only, 86400.0)                                   # vol = NaN
reg_n, _ = lr.regularize_bars6(b6, 86400.0)
check("regularize keeps NaN volume NaN (was coerced to 0 -> zero budget)",
      bool(np.isnan(reg_n[:, 5]).all()))
lad_d = dict(buy_prices=[95.0, 90.0], sell_prices=[106.0, 112.0],
             bw=None, sw=None, pdec=2)
r_reg = lr.run_ladder_v11(reg_n, lad_d, CFG, stress=False, slip=0.002, pdec=2)
r_raw = lr.run_ladder_v11(b6, lad_d, CFG, stress=False, slip=0.002, pdec=2)
check("daily Nx5-sourced bars FILL after regularize (the 19-dead-markets bug)",
      r_reg["trades"] > 0 and r_reg["trades"] == r_raw["trades"],
      f"reg={r_reg['trades']} raw={r_raw['trades']}")
rep_d = lr.frozen_ladder_report_v11(b6, lad_d, CFG, label="daily", pdec=2)
check("full report path trades on daily NaN-vol bars",
      rep_d["summary"]["trades"] > 0, f"trades={rep_d['summary']['trades']}")
# known volume still aggregates/zero-fills as designed
gap6 = np.delete(synth_bars6(n=200, seed=22, bar_seconds=86400.0), np.arange(50, 60), axis=0)
reg_k, fl = lr.regularize_bars6(gap6, 86400.0)
check("known-volume path unchanged (gap bars vol=0, gap_fill>0)",
      fl > 0 and bool(np.all(reg_k[50:60, 5] == 0.0))
      and bool(np.isfinite(reg_k[:, 5]).all()))
# NaN + known collision aggregates sanely
coll = synth_bars6(n=50, seed=23, bar_seconds=86400.0)
coll[10, 5] = np.nan; coll[11, 0] = coll[10, 0]        # NaN bar collides with known
reg_c, _ = lr.regularize_bars6(coll, 86400.0)
slot = np.argmin(np.abs(reg_c[:, 0] - coll[10, 0]))
check("NaN+known collision -> known volume wins",
      abs(reg_c[slot, 5] - coll[11, 5]) < 1e-9)

# degenerate fill windows guarded
one = pd.DataFrame(dict(ts=[1.7e9], side=["sell"], price=[100.0], amount=[1.0]))
check("single fill -> sufficiency says window undefined, no 1e9 rates",
      "TOO THIN" in lr.fills_sufficiency(one) and "1e" not in lr.fills_sufficiency(one))
cmp1 = lr.compare_live_vs_sim_v11(one, bars, dict(buy_prices=[95, 90],
      sell_prices=[105, 110], bw=None, sw=None), CFG, pdec=4)
check("single fill -> compare returns a note instead of a bogus ratio",
      "note" in cmp1 and "sim_over_live_fill_ratio" not in cmp1)

# median book sampling (v11.2: samples raw books, medians the profile)
_mseq = iter([_mkbook(100, 100.0), _mkbook(100, 90000.0), _mkbook(100, 8000.0)])
_orig_fo = lr.fetch_orderbook
lr.fetch_orderbook = lambda u, pk, c: next(_mseq)
try:
    snap_m = lr.market_book_snapshot(uni, "TST/USDT",
                                     dict(CFG, rc_book_samples=3,
                                          rc_book_sample_pause=0.0))
finally:
    lr.fetch_orderbook = _orig_fo
check("book snapshot = median of samples (outlier-robust)",
      abs(snap_m["book_total_usd"] - 8000.0) < 1.0 and snap_m["samples"] == 3,
      f"median_total=${snap_m['book_total_usd']:,.0f}")
check("snapshot keeps the raw book for ladder-band re-measurement",
      snap_m.get("book") is not None)

# ----------------------------------------------------------------------
# 17. v11.3: deployable YAML generation (round-trip through the REAL parser)
# ----------------------------------------------------------------------
import tempfile as _tf17, os as _os17
_cfg_conf = dict(symbol="DASH/USDT", trading_pair="DASH-USDT", exchange="nonkyc",
                 validation="CONFIRMED", gates=[],
                 max_fund_value_quote=1250, quote_usd_rate=1.0, fee=0.002,
                 buy_prices=["33.85", "33.11", "32.29", "31.47", "30.73"],
                 sell_prices=["35.61", "36.90", "38.25", "39.61", "40.90"],
                 buy_amounts_pct=[24.0, 22.0, 20.0, 18.0, 16.0],
                 sell_amounts_pct=[24.0, 22.0, 20.0, 18.0, 16.0],
                 engine=dict(fill_model="v11", penetration_pct=0.0005,
                             volume_cap_frac=0.25, book_half_spread_pct=0.5),
                 holdout=dict(edge_pct=1.4, trades=19, two_sided=True),
                 block_consistency=dict(edge_pct=55.6, maxdd=40.6))
cid, text = lr.render_deploy_yaml(_cfg_conf, CFG, tier="CONFIRMED", run_id="test")
check("yaml id follows the naming convention",
      cid == "range_inventory_ladder_dash_usdt_auto_test", cid)
check("kraken yamls get the k_ prefix",
      lr.render_deploy_yaml(dict(_cfg_conf, exchange="kraken"), CFG,
                            run_id="t")[0].startswith("k_range_inventory_ladder_"))
with _tf17.TemporaryDirectory() as td:
    p = _os17.path.join(td, f"{cid}.yml")
    open(p, "w").write(text)
    found = lr.discover_controller_yamls([td], pattern="*range_inventory_ladder*.y*ml",
                                         exchange="nonkyc")
    check("generated yaml is DISCOVERED by the real discovery", len(found) == 1)
    lad = lr.controller_to_ladder(found[0], CFG)
    check("generated yaml round-trips through the real parser",
          lad is not None and lad["trading_pair"] == "DASH/USDT")
    check("rung prices survive the round trip",
          [float(x) for x in _cfg_conf["buy_prices"]] == list(map(float, lad["buy_prices"]))
          and [float(x) for x in _cfg_conf["sell_prices"]] == list(map(float, lad["sell_prices"])))
    bw = np.asarray(lad["bw"], float); want = np.asarray(_cfg_conf["buy_amounts_pct"], float)
    check("rung weights survive (relative)",
          np.allclose(bw / bw.sum(), want / want.sum(), atol=1e-6))
    check("fresh seed = frac of cap, claimed base 0",
          "claimed_base_value_quote: 0" in text and "total_amount_quote: 625" in text)
    check("evidence + tier + discipline in the header",
          "TIER: CONFIRMED" in text and "holdout_edge=1.4%" in text
          and "FIRST live 15-day" in text)

# selection tiers
fdf = pd.DataFrame([
    dict(base="DASH/USDT", validation="CONFIRMED", gates="", holdout_edge_pct=1.4,
         holdout_two_sided=True, clean_edge_pos_rate=0.8),
    dict(base="XPL/USD", validation="GATED", gates="rolling WF (process check) failed",
         holdout_edge_pct=16.3, holdout_two_sided=True, clean_edge_pos_rate=0.667),
    dict(base="SPACE/USD", validation="GATED", gates="rolling WF (process check) failed",
         holdout_edge_pct=0.8, holdout_two_sided=False, clean_edge_pos_rate=1.0),
    dict(base="AIO/USD", validation="GATED",
         gates="rolling WF (process check) failed; min-qty needs fund >= 201 USD",
         holdout_edge_pct=8.7, holdout_two_sided=True, clean_edge_pos_rate=0.833),
    dict(base="JUNK/USDT", validation="SUSPECT", gates="thin book",
         holdout_edge_pct=9.9, holdout_two_sided=True, clean_edge_pos_rate=1.0),
])
tiers = lr.yaml_deploy_selection(fdf, CFG, deployed_pairs=["XMR/USDT", "DASH/USDT"])
check("CONFIRMED selected; live pair tagged +REFRESH",
      tiers.get("DASH/USDT") == "CONFIRMED+REFRESH")
check("strong-holdout WF-only GATED -> CANDIDATE", tiers.get("XPL/USD") == "CANDIDATE")
check("weak/one-sided holdout GATED excluded", "SPACE/USD" not in tiers)
check("multi-gate GATED excluded (min-qty is a real blocker)", "AIO/USD" not in tiers)
check("SUSPECT never selected", "JUNK/USDT" not in tiers)
check("deployed-but-unranked pair still gets a REFRESH", tiers.get("XMR/USDT") == "REFRESH")

with _tf17.TemporaryDirectory() as td:
    cfgs17 = [dict(_cfg_conf), dict(_cfg_conf, symbol="XPL/USD",
                                    trading_pair="XPL-USD", exchange="kraken",
                                    validation="GATED",
                                    gates=["rolling WF (process check) failed"])]
    paths = lr.save_deploy_yamls(td, cfgs17, fdf, CFG,
                                 deployed_pairs=["DASH/USDT"], run_id="t")
    names = [_os17.path.basename(p) for p in paths]
    check("saver writes yamls + INDEX.md",
          any(n.endswith(".yml") for n in names) and "INDEX.md" in names, str(names))
    idx_text = open([p for p in paths if p.endswith("INDEX.md")][0]).read()
    check("index lists tiers and evidence", "CONFIRMED+REFRESH" in idx_text
          and "CANDIDATE" in idx_text)

# ----------------------------------------------------------------------
# 18. v11.3: live-strategy health classification
# ----------------------------------------------------------------------
def _blocks(pnls, holds, trades=None, in_band=1.0, partial_last=False):
    n = len(pnls)
    return pd.DataFrame(dict(
        block=range(1, n + 1), days=[15.0] * n,
        pnl_pct=pnls, hold_pct=holds,
        edge_pct=[p - h for p, h in zip(pnls, holds)],
        trades=trades or [10] * n,
        two_sided=[True] * n, in_band_pct=[in_band] * n,
        partial=[False] * (n - 1) + [partial_last]))

def _rep(pk, blocks, pnl=0.0, edge=0.0):
    return dict(blocks=blocks, summary=dict(pnl_pct=pnl, edge_pct=edge),
                ladder=dict(trading_pair=pk))

reports = {
  "healthy":  _rep("H/USDT", _blocks([1, 2, 3], [0, 1, -1])),
  "defensive": _rep("D/USDT", _blocks([-3, -2, -4], [-8, -6, -9])),
  "bleeding": _rep("B/USDT", _blocks([1, 1, 1], [4, 5, 6])),
  "dead":     _rep("X/USDT", _blocks([-4, -3, -5], [-1, 0, -2])),
  "dormant":  _rep("Z/USDT", _blocks([0, 0, 0], [0, 0, 0],
                                     trades=[0, 0, 0], in_band=0.0)),
}
hdf = lr.live_strategy_health(pd.DataFrame(), reports, CFG)
st = dict(zip(hdf.controller, hdf.status))
check("health: profitable + edge -> HEALTHY", st["healthy"] == "HEALTHY")
check("health: beating hold but losing money -> DEFENSIVE",
      st["defensive"].startswith("DEFENSIVE"))
check("health: profit below hold -> BLEEDING VS HOLD",
      st["bleeding"] == "BLEEDING VS HOLD")
check("health: losing money AND losing to hold -> NOT PROFITABLE",
      st["dead"] == "NOT PROFITABLE")
check("health: out-of-band no-trade -> DORMANT", st["dormant"] == "DORMANT")
check("health: worst statuses sort to the top",
      hdf.status.iloc[0] == "NOT PROFITABLE")
check("health: recent compounding correct",
      abs(hdf.set_index("controller").loc["healthy", "recent_pnl_pct"]
          - ((1.01 * 1.02 * 1.03 - 1) * 100)) < 0.01)
# partial last block excluded from the recent window
rep_p = {"p": _rep("P/USDT", _blocks([1, 1, -50], [0, 0, 0], partial_last=True))}
hp = lr.live_strategy_health(pd.DataFrame(), rep_p, CFG)
check("health: partial final block excluded",
      hp.iloc[0].status == "HEALTHY" and hp.iloc[0].recent_blocks == 2)
import io as _io, contextlib as _ctx
buf = _io.StringIO()
with _ctx.redirect_stdout(buf):
    lr.print_health_banners(hdf)
out17 = buf.getvalue()
check("banners: NOT PROFITABLE is loud, HEALTHY is silent",
      "[!!] STOP" in out17 and "dead" in out17 and "healthy" not in out17)

# ----------------------------------------------------------------------
# 19. v11.3.1: resilient universe (retry, disk fallback, honest failure)
# ----------------------------------------------------------------------
import tempfile as _tf19, time as _t19
_orig_nu = ll.nonkyc_universe
_orig_sleep = lr.time.sleep
lr.time.sleep = lambda s: None                       # no waiting in tests
_uni_ok = dict(exchange="nonkyc", df=pd.DataFrame([dict(pairkey="A/USDT", vol_usd=1.0)]))
with _tf19.TemporaryDirectory() as td:
    cfg19 = dict(CFG, cache_dir=td)
    calls = {"n": 0}
    def _flaky(c):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("NonKYC /market/getlist returned nothing.")
        return dict(_uni_ok)
    ll.nonkyc_universe = _flaky
    try:
        u = lr.build_universe("nonkyc", cfg19)
        check("universe: transient failures retried to success",
              u["exchange"] == "nonkyc" and calls["n"] == 3, f"attempts={calls['n']}")
        check("universe: dust filter forced off at universe level",
              True)  # builder called with min_vol_usd=0 (asserted below)
        seen = {}
        ll.nonkyc_universe = lambda c: seen.update(v=c.get("min_vol_usd")) or dict(_uni_ok)
        lr.build_universe("nonkyc", dict(cfg19, min_vol_usd=10000.0))
        check("universe: min_vol_usd=0 passed to the builder", seen["v"] == 0.0)
        # good universe was cached; now the API dies completely -> fallback
        ll.nonkyc_universe = lambda c: (_ for _ in ()).throw(
            RuntimeError("NonKYC /market/getlist returned nothing."))
        u2 = lr.build_universe("nonkyc", cfg19, retries=1)
        check("universe: disk fallback when the API is down",
              u2["exchange"] == "nonkyc")
        # stale cache is refused
        import pickle as _pkl
        blob = _pkl.load(open(f"{td}/universe_nonkyc.pkl", "rb"))
        blob["saved_at"] = _t19.time() - 100 * 3600
        _pkl.dump(blob, open(f"{td}/universe_nonkyc.pkl", "wb"))
        try:
            lr.build_universe("nonkyc", cfg19, retries=0)
            check("universe: stale cache refused, original error raised", False)
        except RuntimeError as e:
            check("universe: stale cache refused, original error raised",
                  "returned nothing" in str(e))
    finally:
        ll.nonkyc_universe = _orig_nu
        lr.time.sleep = _orig_sleep

# ----------------------------------------------------------------------
print()
if FAILED:
    print(f"{len(FAILED)} FAILED: {FAILED}")
    raise SystemExit(1)
print("ALL TESTS PASSED")
