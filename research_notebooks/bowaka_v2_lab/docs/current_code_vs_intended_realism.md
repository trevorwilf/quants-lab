# Current-code parity vs. intended realism

**Realism remediation — Phase 0.** Audit refs: §11 Phase 0, §16, P0-001.

The 2026-05-21 realism audit found four places where the **live Bowaka v2 code as
written** diverges from the **intended strategy**. The operator decision (prompt
§0) is *lab-only*: we do **not** edit the live code. Instead the lab supports
**two simulation contracts** so it can both (a) reconcile a run against live
Bowaka v2 and (b) model the intended strategy:

| `simulation.mode`     | Reproduces                                  |
|-----------------------|---------------------------------------------|
| `current_code_parity` | the live code *as written* (warts and all)  |
| `intended_realism`    | the *intended* strategy (audit §16 fixes)   |
| `smoke_fixture`       | deterministic synthetic data (plumbing only)|

Each of the four behaviors below is controlled by one field of
`SimulationConfig` (`src/bowaka_v2_lab/config/models.py`). The fields default to
`None` and are resolved from `mode` via `_SIMULATION_MODE_DEFAULTS`; a config can
also pin a single axis explicitly.

The line numbers below are into the **live, read-only** source under
`${BOWAKA_V2_SOURCE_ROOT}` and were verified on 2026-05-21.

---

## 1. Scanner intraday bar window

**Lab flag:** `simulation.intraday_window_policy`
**Live ref:** `bowaka_intraday_scanner.py:671-714`

The live scanner builds the forming-session bar window starting at
`session.scanner_start` (default **09:45 ET**), not the regular session open:

```python
session_start = pd.Timestamp(
    f"{today_et_date} {sess_cfg.get('scanner_start', '09:45')}",
    tz="America/New_York",
)
...
def live_bars_supplier(symbol, scan_ts):
    start_utc = session_start.tz_convert("UTC")   # 09:45 ET, not 09:30
    return oa.fetch_bars(..., start=start_utc, end=scan_ts_utc, ...)
```

The first 15 minutes of the session (09:30–09:44) are therefore **excluded**
from `rvol_so_far`, `range_expansion_so_far`, `close_location_so_far`, etc. The
intended strategy measures forming-session features from the **regular open
(09:30 ET)** so the opening range is represented.

| Mode                  | `intraday_window_policy`  | Window                       |
|-----------------------|---------------------------|------------------------------|
| `current_code_parity` | `scanner_start_to_scan`   | `session.scanner_start` → scan_ts |
| `intended_realism`    | `regular_open_to_scan`    | `session.start` (09:30) → scan_ts |
| `smoke_fixture`       | `regular_open_to_scan`    | `session.start` (09:30) → scan_ts |

`extended_hours_to_scan` (04:00 ET → scan_ts) is also available for research.
Phase 4 wires this into `data/suppliers.py` and `sim/schedule.py`.

---

## 2. Quote fallback when no quote is available

**Lab flag:** `simulation.quote_fallback_policy`
**Live ref:** `bowaka_v2_strategy.py:743-748`

When the quote supplier returns nothing, the live code fabricates a
**zero-spread quote at the signal price**:

```python
quote = (quote_supplier(symbol) if quote_supplier else None) or {
    "bid": signal_price, "ask": signal_price,
    "mid": signal_price, "spread_pct": 0.0,
    "quote_timestamp": _iso(now), "quote_age_seconds": 0,
}
```

A zero-spread, zero-age synthetic quote sails through the quote gate and implies
**free, frictionless fills** — materially optimistic. The intended strategy
should *fail closed* (reject the candidate) when no real quote exists.

| Mode                  | `quote_fallback_policy`  | Behavior when no historical quote                         |
|-----------------------|--------------------------|------------------------------------------------------------|
| `current_code_parity` | `zero_spread`            | synthetic quote, `bid=ask=mid=signal_price`, spread 0      |
| `intended_realism`    | `require_real`           | reject candidate with `missing_quote`; fail run below coverage threshold |
| `smoke_fixture`       | `synthetic_calibrated`   | calibrated synthetic spread + conservative slippage        |

Phase 6 wires the historical quote supplier and the calibrated fallback.

---

## 3. Acceptance event emitted before broker submit

**Lab flag:** `simulation.accepted_event_sequencing`
**Live ref:** `bowaka_v2_strategy.py:791-846`

The live code emits the `accepted` entry-decision **before** the order is
submitted to the broker:

```python
# Accepted. Build the entry-decision record + emit shadow risk.
accept = build_acceptance_record(ev, ...)
emit_entry_decision_v2(cfg, accept)          # <-- emitted here (line 804)
...
# Submit order (injection point).
if submit_supplier is not None:
    submit_resp = submit_supplier(symbol, qty)   # <-- broker submit (line 822)
    ...
    if not status_ok:
        summary["rejected"] += 1
        continue                                  # broker rejected -- but
                                                  # `accepted` was already emitted
```

So a broker reject still leaves an `accepted` event in the log with no
position — the candidate ends up counted both as accepted *and* rejected. The
intended sequencing emits `submitted_pending` after gates pass and only emits
`accepted` after broker accept/fill confirmation.

| Mode                  | `accepted_event_sequencing` | Event order on a broker reject                       |
|-----------------------|-----------------------------|-------------------------------------------------------|
| `current_code_parity` | `pre_submit`                | `accepted`, then `broker_reject` (no position)        |
| `intended_realism`    | `post_submit`               | `submitted_pending`, then `broker_reject` (no `accepted`) |
| `smoke_fixture`       | `pre_submit`                | `accepted`, then `broker_reject` (no position)        |

Phase 5 implements the terminal-decision schema and both sequencings.

---

## 4. Unknown instrument class fails open

**Lab flag:** `simulation.unknown_instrument_class_policy`
**Live ref:** `bowaka_v2_features.py:473-477`

The live instrument gate **passes** when `instrument_class is None`:

```python
# Instrument class.
gates["instrument_gate"] = (
    instrument_class is None
    or instrument_class == "operating_equity"
)
```

A symbol whose instrument class could not be resolved is therefore treated as
eligible — so an ETF/ETN/warrant/leveraged-ETP with a missing asset-master
class can slip into the universe. The intended strategy fails *closed*: an
unresolved instrument class is excluded.

| Mode                  | `unknown_instrument_class_policy` | `instrument_class is None` →     |
|-----------------------|-----------------------------------|-----------------------------------|
| `current_code_parity` | `fail_open`                       | gate **passes** (symbol eligible) |
| `intended_realism`    | `fail_closed`                     | gate **fails** (symbol excluded)  |
| `smoke_fixture`       | `fail_open`                       | gate **passes** (synthetic data has known classes) |

Phase 3 (PIT universe builder) and Phase 4 (scanner replay) honor this policy.

---

## 5. Early-close days — scan window truncation (Phase 4 deviation)

**Lab module:** `src/bowaka_v2_lab/sim/schedule.py`
**Live ref:** `bowaka_intraday_scanner.py:671-725` (`_run_live`)

The live scanner's loop bound `session_end` is built **purely from the
configured `scanner_end`** and the calendar is never consulted:

```python
session_end = pd.Timestamp(
    f"{today_et_date} {sess_cfg.get('scanner_end', '15:30')}",
    tz="America/New_York",
)
...
if now > session_end:
    LOG.info("past scanner_end (%s); scanner exiting", session_end)
    break
```

On an early-close day (e.g. the day after Thanksgiving or Christmas Eve, when
XNYS closes 13:00 ET) `scanner_end` is 15:30 ET — **after** the real market
close — so the live scanner would keep ticking against a shut market (it would
just receive no fresh bars and stale-skip every symbol).

**Lab deviation (intentional).** `scan_times_for_session` truncates the scan
window to `min(scanner_end, exchange early close)` using
`exchange_calendars.session_close`. A backtest therefore emits **no scan after
the market is closed** — the realistic behaviour. This is a deliberate
divergence from the live code as written; it is not gated by a
`simulation.mode` flag because emitting scans into a closed market is never
correct in any mode. On a normal day the exchange close (16:00 ET) is well past
`scanner_end` (15:30 ET) so the truncation is a no-op.

---

## Summary table

| # | Behavior                          | Lab flag / module                   | Live ref                          |
|---|-----------------------------------|-------------------------------------|-----------------------------------|
| 1 | Scanner bar window start          | `intraday_window_policy`            | `bowaka_intraday_scanner.py:671-714` |
| 2 | Quote fallback (no quote)         | `quote_fallback_policy`             | `bowaka_v2_strategy.py:743-748`   |
| 3 | Acceptance emitted pre/post submit| `accepted_event_sequencing`         | `bowaka_v2_strategy.py:791-846`   |
| 4 | Unknown instrument class          | `unknown_instrument_class_policy`   | `bowaka_v2_features.py:473-477`   |
| 5 | Early-close scan-window truncation| `sim/schedule.py` (always-on)       | `bowaka_intraday_scanner.py:671-725` |

Items 1-4 are recorded in `run_manifest.json` (`simulation` block) and the
backtest report header on every run. Item 5 is an unconditional correctness fix
in the Phase 4 scheduler.
