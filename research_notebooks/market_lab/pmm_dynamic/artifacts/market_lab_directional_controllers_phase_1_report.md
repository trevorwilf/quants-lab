# Phase 1 Report — Platform Additions (3 surgical edits)

**Date**: 2026-04-17
**Objective**: Add 12h interval, XMR-USDT rules, and strategy factory registrations.

## Files Modified

1. `pmm_lab/config/defaults.py` — added `"12h": 43200,` between `"4h": 14400,` and `"1d": 86400,` in `INTERVAL_SECONDS`.
2. `configs/exchange_rules.yaml` — added `XMR-USDT` entry to both `mexc.pairs` and `nonkyc.pairs` with `price_tick: 0.01`, `amount_step: 0.001`, `min_notional_quote: 1.0`.
3. `pmm_lab/strategies/factory.py` — added imports and registrations for `MeanReversionBBRSIStrategy` and `EMARegimeHoldStrategy`.

## XMR-USDT Rules Audit Note

XMR-USDT rules verified against live MEXC exchangeInfo (`quotePrecision=2`,
`baseAssetPrecision=3`, `baseSizePrecision="0.001"`, `quoteAmountPrecision="1"`)
and NonKYC `/market/getlist` (`priceDecimals=2`, `quantityDecimals=3`,
`minQuote=1` with `isMinQuoteActive=true`). price_tick=0.01,
amount_step=0.001, min_notional_quote=1.0 on both connectors. Per-pair
override required because both connector `default:` blocks specify
`min_notional_quote: 5.0`, which would silently over-reject small orders.
Values pre-verified in the prompt; no runtime re-verification required.

## Files Created (Phase 1 tests)

- `tests/unit/test_interval_registry_12h.py`
- `tests/unit/test_exchange_rules_xmr_usdt.py`

## Test Results

New tests: **12 passed, 0 failed** (registry + XMR-USDT rules).

The strategy factory import now fails with `ModuleNotFoundError` for
`pmm_lab.strategies.mean_reversion_bb_rsi` — this is expected until Phase 3
creates the strategy modules. Per the prompt's Phase 1 guidance: "the factory
self-test after this edit... will fail until Phase 4."

**Contained failure check**: the factory import error cascades to any test
that transitively imports `pmm_lab.strategies`. We are intentionally proceeding
directly to Phase 2/3 to restore the factory.

## Escalations

None.

## Phase 1 — Complete
