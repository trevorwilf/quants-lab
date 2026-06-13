I have comprehensive coverage across all sub-topics. I have enough to write a dense, well-cited report. Let me compile the findings now.

---

# Alpaca Market Data API v2 — Microstructure Realism Reference (mid-2026)

## 0. Feed taxonomy & core endpoints (baseline)

Alpaca's stock historical/real-time data is served under the `/v2/stocks/...` prefix on `data.alpaca.markets`, selectable via the `feed=` parameter ([about-market-data-api](https://docs.alpaca.markets/us/docs/about-market-data-api), [historical-stock-data](https://docs.alpaca.markets/docs/historical-stock-data-1)):

- **`feed=sip`** — consolidated CTA+UTP tape, 100% of US volume. Requires **Algo Trader Plus** subscription. This is the only feed adequate for a tape-replay backtester.
- **`feed=iex`** — IEX only, ~2.5% of volume; free. Not NBBO-representative.
- **`feed=boats`** — Blue Ocean ATS overnight session (8pm–4am ET); separate venue, not consolidated NBBO.
- **`feed=delayed_sip`** / 15-min-delayed SIP for free accounts.

Historical REST endpoints (all accept `feed`, `start`, `end`, `limit`, `page_token`, `sort`, plus `asof`/`currency` where relevant): **`/v2/stocks/trades`**, **`/v2/stocks/quotes`**, **`/v2/stocks/bars`** ([stockbars](https://docs.alpaca.markets/us/reference/stockbars)), **`/v2/stocks/auctions`** ([stockauctions](https://docs.alpaca.markets/reference/stockauctions-1)), plus `/snapshots`, `/{symbol}/trades/latest`, etc. Bars: timeframes 1Min→12Month; each bar has `t,o,h,l,c,v,n` (trade count), `vw` (VWAP).

---

## TOPIC 2 — Microstructure realism

### (a) Halts & LULD — **streaming-only; NO historical/REST equivalent**

The **`statuses`** and **`lulds`** channels exist **only on the WebSocket stream** (`wss://stream.data.alpaca.markets/v2/{feed}`) ([real-time-stock-pricing-data](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data)). There is **no historical or REST endpoint** for either. Confirmed by Alpaca staff in [forum: historical trade/quote statuses](https://forum.alpaca.markets/t/is-it-possible-to-query-for-historical-trade-quote-statuses/15067) and the [Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq), which explicitly tells users to "check the current halts or the historical halts on the **Nasdaq website**" — i.e. Alpaca does not store/serve halt history. **For a backtester, halt and LULD history must be sourced externally (Nasdaq Trader halt files / a third-party feed).**

WebSocket message shapes (for live capture, if you record your own history going forward):
- **Status message** (`T:"s"`): `S` (symbol), `sc` (status code, e.g. `"H"` halt, `"T"` trading/resume, `"Q"` quote-only, `"P"` pre-/post-trading), `sm` (status message text), `rc` (reason code, e.g. `"T12"`), `rm` (reason message, e.g. "Trading Halted; News Pending"), `t` (timestamp), `z` (tape).
- **LULD message** (`T:"l"`): `S`, `u` (upper band price), `d` (lower band price), `i` (indicator), `t`, `z`.

**Reconstructing halts from condition codes:** *partially possible but unreliable.* The trade tape carries auction-resume / halt-related sale conditions, but there is **no clean "halt began at T" trade print** — a halt is the *absence* of trades plus a status message you don't get historically. You can infer a *resume* from the post-halt **reopening auction print** (trade condition **`M`/`Q`** reopening, or the auction endpoint's reopening entry), but you cannot derive the halt **onset** or the LULD band from trades/quotes alone. Treat halt reconstruction as best-effort gap-detection (no trades + a subsequent auction print), not authoritative.

### (b) Trade condition codes — what to exclude from a tape-replay fill model

Mapping endpoint: **`GET /v2/stocks/meta/conditions/{ticktype}`** where `ticktype ∈ {trade, quote}`, `tape ∈ {A,B,C}` (A=NYSE/CTS, B=other CTS, C=Nasdaq/UTP) ([stockmetaconditions](https://docs.alpaca.markets/reference/stockmetaconditions-1)). Sources are **CTA/CTS** (NYSE-administered) and **UTP/UTDF** (Nasdaq-administered). A trade's `c` field is an **array**; multiple conditions can apply and **the strictest rule wins** ([trade conditions forum](https://forum.alpaca.markets/t/trade-conditions/5172)).

Key CTS/UTDF codes (per Alpaca's mapping + the community [trade-codes gist](https://gist.github.com/mdeatherage1992/087ef84ab7b5a5f61faefd842947dbd0)):

| Code | Meaning | Backtester treatment |
|---|---|---|
| `@` / `' '` (space) | Regular Sale | **Include** — primary fill tape, updates O/H/L/C + V |
| `I` | **Odd Lot** | **Exclude** from price; volume-only. Never updates bar price, never appears on `/latest`. |
| `O` | Market Center **Opening** print | Exclude from continuous tape; this *is* the official open (see (d)) |
| `M` | Market Center **Official Close** | Exclude from continuous tape; official close |
| `Q` | Market Center Official Open / reopening | Auction print, not continuous |
| `6` / `5` | Opening/Closing Prints (UTP) | Auction, handle as official O/C |
| `B` | **Average Price** Trade | **Exclude** — not an executable tape price |
| `W` | **Average Price** Trade (CTS) | **Exclude** |
| `L` | **Sold Last** / late reporting | **Exclude** for sequencing (out-of-time) |
| `Z` | **Sold (Out of Sequence)** | **Exclude** — late/out-of-sequence |
| `4` | **Derivatively Priced** | **Exclude** — not an independent print |
| `7` | Qualified Contingent Trade (QCT) | **Exclude** — multi-leg, not lit liquidity |
| `F` | Intermarket Sweep (ISO) | Include (real execution) but note aggressive |
| `H` | Price Variation Trade | Exclude (non-standard price) |
| `C` | Cash Trade | Exclude (settlement-special) |
| `N` | Next-Day Trade | Exclude |
| `P` | Prior Reference Price | **Exclude** — references an earlier time |
| `U` | Extended-hours (sold out of sequence) | Exclude from regular-session bars |
| `T`/`U` | Form-T / extended-hours trade | Session-tag, see (e) |

**Volume vs high/low:** Alpaca follows the **SIP guidance** for which conditions update which field — documented as "**page 64 of the CTS Specification and page 43 of the UTP Specification**" ([stock-minute-bars](https://alpaca.markets/learn/stock-minute-bars)). The Close field uses only a small set of "typical" trades; **Volume includes almost all trades** (incl. odd lots `I`); High/Low exclude the same out-of-sequence/derivative/average-price conditions that the consolidated high/low excludes. So a print with `[@,4,I]` updates **volume only**, no price — matching the SIP high/low/last rules.

### (c) Quote conditions, NBBO sizes, odd lots

Quote message/record fields: `bx,bp,bs` (bid exch/price/size), `ax,ap,as` (ask exch/price/size), `c` (**quote condition**, single char), `z` (tape), `t` ([real-time-stock-pricing-data](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data)). Quote-condition mapping via `meta/conditions/quote`. Relevant codes include `R` (Regular/open), `A` (Slow on bid), `B` (Slow on ask), `H` (slow both), `E` (Slow due to LRP/Gap), `O`/`6` (opening), `C`/`7` (closing), and crossed/locked indicators. **Crossed (ask<bid) and locked (ask=bid) NBBO states are surfaced via the quote condition** rather than a separate flag — your fill model should detect and skip crossed/locked NBBO ticks when modeling marketable fills.

**Sizes are in SHARES, not lots.** Despite CTA/UTP raw specs being round-lot-denominated, Alpaca's `bs`/`as` are emitted as **share counts**, and on the **SIP feed odd-lot quotes are visible** — you will routinely see `bs`/`as` < 100 ([is bid/ask in round lots](https://forum.alpaca.markets/t/is-the-ask-bid-size-represented-in-round-lots-or-as-individual-shares/11038), [why odd-lot quotes in SIP](https://forum.alpaca.markets/t/why-can-i-see-odd-lot-quotes-in-sip-feed/16000), [SIP odd-lot / BOLO](https://forum.alpaca.markets/t/sip-odd-lot-quotes-best-odd-lot-order-bolo-in-market-data/18561)). Implication: Alpaca's stock quote stream is **not a strict round-lot NBBO** — odd-lot and "Best Odd Lot Order (BOLO)" quotes are interleaved. A realistic fill model that assumes displayed size = accessible round-lot depth will **over-estimate liquidity**; you must treat sub-100 sizes as odd-lot (often non-NBBO-protected) and ideally filter to round-lot quotes for protected-NBBO logic. (This matches your prior finding that prevailing-NBBO ask_size is often ~100sh and that the sim "manufactures liquidity.")

### (d) Auction / official open & close

Three distinct sources — **do not conflate**:
1. **`GET /v2/stocks/auctions`** ([stockauctions](https://docs.alpaca.markets/reference/stockauctions-1)) — the authoritative one. Returns per-day arrays `o` (opening auctions) and `c` (closing auctions); each entry: `t` (timestamp), `x` (exchange), `p` (price), `s` (size), `c` (condition). These are the **official primary-listing opening/closing auction prints**.
2. **Trade-tape condition prints** — `O`/`6` (open) and `M`/`Q`/`5` (close) on `/v2/stocks/trades`. Same events, but you must filter by condition.
3. **Daily bars** `o`/`c` — the **first/last trade of the session, NOT the auction price**. The daily-bar open is the first eligible print (often a pre-open or first continuous trade), and close is the last trade, which **differs from the official closing-auction price** ([forum: daily bar O/C vs auction](https://forum.alpaca.markets/t/open-close-daily-bar-prices-vs-open-close-auction-prices-on-primary-exchange/14227)). **For official prints use the auctions endpoint, not daily bars.**

### (e) Extended-hours availability

Pre-market and after-hours trades **are aggregated into bars** and available in trades/quotes ([extended hours forum](https://forum.alpaca.markets/t/does-alpaca-have-extended-hours-for-market-data-api/15174), [Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)). Historical bars/trades/quotes/snapshots all carry extended-hours ticks; the SIP feed covers 4am–8pm ET regular+extended. The **overnight 8pm–4am session is a separate `feed=boats`** (Blue Ocean ATS), supporting Bars/Quotes/Trades/Snapshots for all NMS securities ([market-data-faq](https://docs.alpaca.markets/us/docs/market-data-faq)). Note: extended-hours prints carry their own sale conditions (e.g. `T`/`U` Form-T) and are **excluded from official high/low/volume** of the regular-session consolidated bar — your session-aware bar logic must distinguish them.

### (f) Corporate-actions timing — **NOT point-in-time safe**

Endpoint: **`GET /v1/corporate-actions`** (current, recommended) ([corporateactions](https://docs.alpaca.markets/reference/corporateactions-1)); the older `/v2/corporate_actions/announcements` is **deprecated**. Types include forward/reverse splits, cash/stock dividends, mergers, spinoffs; `cusips` filter supported; `old_cusip`/`new_cusip` added per the [CUSIP changelog](https://docs.alpaca.markets/changelog/cusip). **Critical caveat (Alpaca's own words):** "Alpaca has **no guarantees on the creation time** of corporate actions… there may be delays in receiving… and in processing." So the API gives the **effective/ex date**, not a reliable **announcement timestamp**, and entries can appear *after* the event. **This is a look-ahead/PIT hazard** — you cannot trust this feed to tell you what was *known* on a given historical date. For PIT-correct backtesting, snapshot the CA table daily yourself or use a vendor with announcement timestamps.

### (g) Short-sale data — **largely absent**

- **No SSR (Reg SHO short-sale-restriction / uptick-rule) flag** in the market-data API — not in trades, quotes, or any meta endpoint. There is **no historical SSR feed**. (Reconstruct from a 10% prior-close trigger externally if needed.)
- **Borrow status:** the **Trading API Assets endpoint** (`GET /v2/assets`) exposes `shortable` and `easy_to_borrow` booleans, refreshed each morning ([margin-and-short-selling](https://docs.alpaca.markets/us/docs/margin-and-short-selling)). This is **Trading-API, current-state only — not historical, not point-in-time**. Alpaca supports shorting **ETB only**; HTB is unsupported and **no HTB/borrow-rate data is exposed**. Borrow fees are $0 on ETB.

### (h) Bar-construction rules

Documented aggregation pipeline ([stock-minute-bars](https://alpaca.markets/learn/stock-minute-bars)): trades are **(1) bucketed by execution time → (2) filtered by trade condition (per-field) → (3) reduced** (first/max/min/last/sum). **Each OHLCV field filters by a different condition set**, following SIP guidance (CTS spec p.64 / UTP spec p.43):
- **Open/Close**: only "typical" price-eligible trades (excludes `I` odd lot, `B`/`W` avg-price, `4` derivatively-priced, `Z`/`L` out-of-sequence, `O`/`M` auction in continuous context).
- **High/Low**: same exclusion set as consolidated high/low.
- **Volume**: nearly all trades **including odd lots** `I`.
- Bars are **right-/left-labeled by start of interval**, UTC timestamps; `n`=trade count, `vw`=VWAP. Pre/post-market trades are aggregated into bars too, so a minute bar's eligibility depends on session + condition, not just timestamp.

---

## Quick availability matrix

| Data | SIP historical REST | IEX | Streaming-only | Broker/Trading-API only | Not available |
|---|---|---|---|---|---|
| Trades / Quotes / Bars / Auctions | ✅ | ✅ (IEX subset) | — | — | — |
| Trade & quote **condition mappings** | ✅ `meta/conditions` | ✅ | — | — | — |
| **Halt status / LULD bands** | ❌ | ❌ | ✅ `statuses`/`lulds` | — | ❌ historical |
| Official **open/close auctions** | ✅ `/auctions` | partial | — | — | — |
| Extended-hours bars/trades/quotes | ✅ | ✅ | — | — | — |
| Overnight session | ✅ `feed=boats` | — | — | — | — |
| **Corporate actions** | ✅ `/v1/corporate-actions` (not PIT-safe) | — | — | — | reliable announce-time ❌ |
| **SSR flag** | — | — | — | — | ❌ |
| **Borrow / ETB / shortable** | — | — | — | ✅ `/v2/assets` (current only) | historical/HTB-rate ❌ |

**Top realism risks for your sim:** (1) no historical halts/LULD — must import Nasdaq files; (2) corporate-actions feed is not PIT-safe (look-ahead); (3) quote sizes are share-denominated with odd-lot quotes mixed into SIP — filter to round-lot for protected-NBBO depth; (4) daily-bar O/C ≠ official auction price — use `/auctions`; (5) no SSR/HTB data at all.

**Sources:** [about-market-data-api](https://docs.alpaca.markets/us/docs/about-market-data-api) · [historical-stock-data](https://docs.alpaca.markets/docs/historical-stock-data-1) · [stockbars](https://docs.alpaca.markets/us/reference/stockbars) · [real-time-stock-pricing-data](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data) · [market-data-faq](https://docs.alpaca.markets/us/docs/market-data-faq) · [stockmetaconditions](https://docs.alpaca.markets/reference/stockmetaconditions-1) · [stockauctions](https://docs.alpaca.markets/reference/stockauctions-1) · [stock-minute-bars](https://alpaca.markets/learn/stock-minute-bars) · [corporateactions](https://docs.alpaca.markets/reference/corporateactions-1) · [CUSIP changelog](https://docs.alpaca.markets/changelog/cusip) · [margin-and-short-selling](https://docs.alpaca.markets/us/docs/margin-and-short-selling) · [forum: historical statuses](https://forum.alpaca.markets/t/is-it-possible-to-query-for-historical-trade-quote-statuses/15067) · [forum: daily bar O/C vs auction](https://forum.alpaca.markets/t/open-close-daily-bar-prices-vs-open-close-auction-prices-on-primary-exchange/14227) · [forum: odd-lot quotes in SIP](https://forum.alpaca.markets/t/why-can-i-see-odd-lot-quotes-in-sip-feed/16000) · [forum: bid/ask size shares vs lots](https://forum.alpaca.markets/t/is-the-ask-bid-size-represented-in-round-lots-or-as-individual-shares/11038) · [trade-codes gist](https://gist.github.com/mdeatherage1992/087ef84ab7b5a5f61faefd842947dbd0)

**Verification caveat:** No WebFetch tool was available in this environment, so exact field-name spellings and the full condition-code tables could not be read verbatim from the live OpenAPI pages — they are reconstructed from doc/forum search summaries and the community gist. Before hard-coding, confirm against `GET /v2/stocks/meta/conditions/{trade,quote}` live responses and the `/v2/stocks/auctions` schema, since Alpaca's exact JSON keys (e.g. auction `o`/`c` nesting, quote condition single-char values) should be validated against a live pull.