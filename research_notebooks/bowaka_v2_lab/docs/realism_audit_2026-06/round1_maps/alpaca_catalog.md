I have enough verified detail across all sub-topics to synthesize. I'll note where exact field schemas (auctions, corrections) come from SDK/docs knowledge versus where search confirmed them. Let me write the dense report.

# Alpaca Market Data API v2 — Stock Data Catalog (mid-2026)

Base host: `https://data.alpaca.markets`. Stock REST endpoints are under `/v2/stocks/...`; newer products (screener, news, corporate actions) live under `/v1beta1/...`. Auth via `APCA-API-KEY-ID` / `APCA-API-SECRET-KEY` headers (or Broker basic auth). **Feed legend below:** SIP = paid consolidated tape (Algo Trader Plus), IEX = free single-exchange (~2.5% volume), BOATS = Blue Ocean overnight ATS, DELAYED_SIP = 15-min-delayed SIP. Note: all feeds serve data ≥15 min old; only SIP/real-time-IEX serve the most recent 15 min.

## TOPIC 1 — Data-Product Catalog

### Historical Bars — `GET /v2/stocks/bars` (multi) and `GET /v2/stocks/{symbol}/bars` (single)
- **Timeframes** (`timeframe` param): `1Min`…`59Min`, `1Hour`…`23Hour`, `1Day`, `1Week`, `1Month`…`12Month` (one-minute through 12-month). Multipliers allowed within the minute/hour/day/week/month units.
- **`adjustment`** (stocks only): `raw` (default), `split`, `dividend`, `all`. Adjustments are applied only relative to the request's start date.
- **`feed`**: `sip` | `iex` | `boats` | `otc` | `delayed_sip`. `feed=boats` returns overnight-session bars/quotes/trades.
- **Bar fields**: `t` (RFC-3339 timestamp), `o`, `h`, `l`, `c`, `v` (volume), `n` (trade count), `vw` (VWAP).
- Other params: `start`, `end`, `limit` (≤10000), `asof`, `currency`, `sort` (asc/desc), `page_token`.
- Docs: https://docs.alpaca.markets/reference/stockbars · single: https://docs.alpaca.markets/reference/stockbarsingle-1
- **Feed availability:** SIP / IEX / BOATS / DELAYED_SIP historical. ✅ Core backtest product.

### Historical Trades — `GET /v2/stocks/trades` (multi) and `/v2/stocks/{symbol}/trades` (single)
- **Trade fields**: `t` (RFC-3339, ns precision), `x` (exchange code), `p` (price), `s` (size), `c` (array of condition codes), `i` (trade ID), `z` (tape: `A`=NYSE, `B`=NASDAQ, `C`=other), `u` (update flag — e.g. `canceled`/`corrected`, present when applicable).
- **Update/correction handling**: in the *historical* tape, corrected/canceled prints carry the `u` field; the corrected value is reflected as a separate record. Real-time corrections come via the streaming `corrections`/`cancelErrors` channels (below), not via a separate historical endpoint.
- Example: `{"t":"...Z","x":"V","p":411.115,"s":500,"c":[" "],"i":53297330284354,"z":"B"}`
- **Feed availability:** SIP (full tape) / IEX (IEX prints only) / BOATS historical. Decode `c` and `x` via the metadata endpoints below.
- Docs: https://docs.alpaca.markets/reference/stocktrades-1

### Historical Quotes (NBBO) — `GET /v2/stocks/quotes` (multi) and `/v2/stocks/{symbol}/quotes` (single)
- **Quote fields**: `t` (timestamp), `bx` (bid exchange), `bp` (bid price), `bs` (bid size, round lots), `ax` (ask exchange), `ap` (ask price), `as` (ask size), `c` (array of quote condition codes), `z` (tape).
- On **SIP**, quotes are true consolidated NBBO across all exchanges; on **IEX** they are IEX-only best bid/offer (not NBBO). This is the key distinction for spread/liquidity backtesting — only SIP gives real NBBO.
- Docs: https://docs.alpaca.markets/reference/stockquotes-1
- **Feed availability:** SIP (NBBO) / IEX (IEX top-of-book) / BOATS historical.

### Auctions — `GET /v2/stocks/auctions` (multi) and `/v2/stocks/{symbol}/auctions` (single)
- Returns daily opening and closing **auction** prints. Response groups per symbol by date `d`, with `o` = array of **opening** auction prints and `c` = array of **closing** auction prints. Each auction print contains `t` (timestamp), `x` (exchange), `p` (price), `s` (size), `c` (condition: e.g. `Q`/`O` open, `M`/`6` close). These are the *primary-listing-exchange* official auction prices (distinct from the daily bar's open/close, which are first/last consolidated trades). Useful for MOO/MOC fill modeling.
- **Feed availability:** **SIP only** (auction data is not on IEX). ✅ Available, paid.
- Docs: https://docs.alpaca.markets/reference/stockauctions-1 · single: https://docs.alpaca.markets/reference/stockauctionsingle-1

### Snapshots — `GET /v2/stocks/snapshots` (multi) and `/v2/stocks/{symbol}/snapshot` (single)
- Per symbol returns: `latestTrade`, `latestQuote`, `minuteBar`, `dailyBar`, `prevDailyBar` (each using the field schemas above). One call for a current-state composite.
- **Feed availability:** SIP / IEX (real-time-ish, subject to 15-min rule on free SIP).
- Docs: https://docs.alpaca.markets/reference/stocksnapshots-1 · single: https://docs.alpaca.markets/reference/stocksnapshotsingle

### Latest endpoints (point-in-time, not historical ranges)
- `/v2/stocks/trades/latest`, `/v2/stocks/quotes/latest`, `/v2/stocks/bars/latest` (plural multi-symbol) — latest single record per symbol. SIP/IEX.

### Exchange & Condition-Code Metadata
- **Exchange codes**: `GET /v2/stocks/meta/exchanges` → map of single-char exchange code → name. Docs: https://docs.alpaca.markets/reference/stockmetaexchanges-1
- **Condition codes**: `GET /v2/stocks/meta/conditions/{ticktype}` where `ticktype` ∈ `trade` | `quote` → map of CTA/UTP condition code → meaning. Docs: https://docs.alpaca.markets/reference/stockmetaconditions-1
- **Feed availability:** REST, available to all (reference data). ✅

### Corporate Actions — TWO distinct products
1. **Market-Data Corporate Actions** — `GET /v1beta1/corporate-actions` (the one relevant to a backtester). Query by `symbols`, `types`, `start`, `end`. Types include `forward_split`, `reverse_split`, `unit_split`, `stock_dividend`, `cash_dividend`, `cash_merger`, `stock_merger`, `stock_and_cash_merger`, `redemption`, `name_change`, `worthless_removal`, `rights_distribution`, `spin_off`. Returns ex-date/payable-date/record-date, ratios, cash amounts, old/new symbols. This is the canonical source for **split & dividend adjustment factors** and **symbol changes**. Docs: https://docs.alpaca.markets/reference/corporateactions-1
2. **Broker-API Announcements** — `GET /v2/corporate_actions/announcements` (Broker/Trading API). Covers `dividend`, `merger`, `spinoff`, `split` only; symbol changes/redemptions/delistings/tender offers **not** exposed here. Data back to **April 2020**. This is **Broker-/Trading-API-only**, not the market-data product. Docs/blog: https://alpaca.markets/blog/introducing-corporate-actions-api-announcements/
- **Net for a backtester:** use `/v1beta1/corporate-actions` (market data) — it has the broader type list incl. `name_change`/`worthless_removal`.

### News — `GET /v1beta1/news`
- Fields: `id`, `author`, `created_at`, `updated_at`, `headline`, `summary`, `content`, `images` (array w/ sizes), `url`, `symbols` (array, stocks+crypto), `source` (Benzinga). History back to **2015**, ~130+ articles/day. Default 10, paginated.
- **Feed availability:** REST historical + WebSocket real-time (separate news stream). Free with any data plan.
- Docs: https://docs.alpaca.markets/reference/news-3 · streaming: https://docs.alpaca.markets/us/docs/streaming-real-time-news

### Options Data — `/v1beta1/options/...`
- Endpoints: `bars`, `trades`, `quotes` (latest + historical), `snapshots`, `meta/exchanges`, `meta/conditions`. **Historical option trades limited to last 7 days** in some calls; full history only since **February 2024**.
- **Feeds**: `indicative` (free, 15-min-delayed OPRA derivative) vs `opra` (paid consolidated options tape, requires Algo Trader Plus / options data subscription).
- Docs: https://docs.alpaca.markets/reference/optionbars · https://docs.alpaca.markets/us/docs/historical-option-data

### Crypto (skipped per scope)
- `/v1beta3/crypto/{loc}/...` bars/trades/quotes/orderbooks/snapshots; no feed subscription required.

### Screener / Most-Actives — `/v1beta1/screener/...`
- **Most actives**: `GET /v1beta1/screener/stocks/most-actives` — top N by `volume` or `trade_count` (default top 10), from real-time SIP. Docs: https://docs.alpaca.markets/reference/mostactives-1
- **Movers**: `GET /v1beta1/screener/{market_type}/movers` (`market_type`=`stocks`|`crypto`) — top gainers & losers vs previous close; split-adjusted; resets at market open (shows prior day pre-open); tradable symbols only. Docs: https://docs.alpaca.markets/reference/movers-1
- **Feed availability:** Built on **real-time SIP** — effectively requires the paid feed for live values.

### WebSocket Streams — ALL channels
- **Stock URL**: `wss://stream.data.alpaca.markets/v2/{feed}` where `{feed}` ∈ `sip` | `iex` | `delayed_sip` | `boats` | `test`. Subscribe with `{"action":"subscribe", ...}`. **All stock stream channels** (subscription keys):
  - `trades` (msg type `t`)
  - `quotes` (`q`)
  - `bars` — minute bars (`b`)
  - `updatedBars` — minute-bar late-correction updates (`u`)
  - `dailyBars` (`d`)
  - `statuses` — trading status / halts & resumes (`s`)
  - `lulds` — Limit-Up/Limit-Down price bands (`l`)
  - `corrections` — corrected trade prints (`c`)
  - `cancelErrors` — trade cancel/error messages (`x`)
  - plus control messages: `success`, `error`, `subscription`.
- **News stream**: `wss://stream.data.alpaca.markets/v1beta1/news` — channel `news` (`n`).
- **Options stream**: `wss://stream.data.alpaca.markets/v1beta1/{indicative|opra}` — `trades`, `quotes`.
- **Channel limits (stocks):** `trades`+`quotes` capped at 30 symbols on the free/basic plan; **`bars`/`dailyBars`/`updatedBars`/`statuses`/`lulds` are unlimited**. Algo Trader Plus / Elite removes the 30-symbol cap.
- **Streaming-only (no historical equivalent):** `statuses` (halt/resume), `lulds` (price bands), `cancelErrors`. `corrections`/`updatedBars` are streaming-only as live channels (historical equivalent = the `u` field on trades/bars). 
- Docs: https://docs.alpaca.markets/docs/streaming-market-data · https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data

### Coverage Start Dates
- **SIP stocks**: ~**7+ years** of history (effectively since ~2016 via the v2 API; Alpaca markets it as "7+ years"). Minute bars available across that range.
- **IEX**: from when IEX feed coverage began (~2018–2019 in practice; thinner).
- **News**: 2015. **Options**: Feb 2024. **Broker announcements**: Apr 2020. **Market-data corporate-actions**: aligned with SIP history.
- Note: docs state "7+ years" rather than a hard date — treat the exact SIP start as ~2016 but verify per-symbol via earliest returned bar.

### Rate Limits per Subscription Tier
- **Free / Basic**: **200 API calls/min**; SIP restricted (only ≥15-min-old SIP data; real-time = IEX only); 30-symbol stream cap on trades/quotes.
- **Algo Trader Plus** (~$99/mo, free for Elite/funded brokerage): full real-time **SIP**, **10,000 API calls/min**, OPRA options add-on, unlimited stream symbols.
- (Historically a ~$9 "Unlimited" intermediate tier offered 1,000 calls/min — superseded by the 200 vs 10,000 split.)
- Docs: https://docs.alpaca.markets/us/docs/about-market-data-api · https://alpaca.markets/data

### Pagination / Latency Characteristics
- **Pagination**: token cursor — responses include `next_page_token`; pass back as `page_token`. `limit` ≤ **10000** records/page (bars/trades/quotes). Multi-symbol responses key results by symbol. `sort=asc|desc`.
- **`asof`** param enables point-in-time symbology (handles ticker renames) on bars.
- **Latency**: REST historical is batch/aggregated (not low-latency); free SIP enforces the **15-minute embargo** on the `end` boundary (`end` must be ≥15 min in the past) — paid removes this. Real-time path is the WebSocket, not REST.

## Quick availability matrix
| Product | SIP hist | IEX hist | Streaming-only | Broker-API-only | N/A |
|---|---|---|---|---|---|
| Bars/Trades/Quotes | ✅ | ✅ (limited) | — | — | — |
| Auctions | ✅ | ❌ | — | — | — |
| NBBO quotes | ✅ (true NBBO) | ❌ (IEX top only) | — | — | — |
| Snapshots/Most-actives/Movers | ✅ | partial | — | — | — |
| `statuses`/`lulds`/`cancelErrors` | — | — | ✅ | — | — |
| Corp-actions announcements | — | — | — | ✅ (`/v2/corporate_actions`) | — |
| Corp-actions (market data `/v1beta1`) | ✅ | ✅ | — | — | — |
| News | ✅ (2015+) | ✅ | + stream | — | — |
| Options | ✅ OPRA (2024+) | indicative(delayed) | + stream | — | — |
| Tick-by-tick L2 / full order book (equities) | — | — | — | — | ❌ not offered |

**Caveat:** No general WebFetch was available in this environment, so the exact `auctions` and `corrections`/`cancelErrors` JSON field keys above are drawn from Alpaca SDK/doc knowledge cross-checked against search snippets rather than a live fetch of the reference page — verify field-letter exactness against https://docs.alpaca.markets/reference/stockauctions-1 before hardcoding parsers. All other field lists (bars/trades/quotes/snapshots/news/corporate-actions/streams) were confirmed in the search results.

Sources:
- [Historical bars](https://docs.alpaca.markets/reference/stockbars) · [single](https://docs.alpaca.markets/reference/stockbarsingle-1)
- [Historical trades](https://docs.alpaca.markets/reference/stocktrades-1) · [Historical quotes](https://docs.alpaca.markets/reference/stockquotes-1)
- [Historical auctions](https://docs.alpaca.markets/reference/stockauctions-1) · [single](https://docs.alpaca.markets/reference/stockauctionsingle-1)
- [Snapshots](https://docs.alpaca.markets/reference/stocksnapshots-1) · [single](https://docs.alpaca.markets/reference/stocksnapshotsingle)
- [Exchange codes](https://docs.alpaca.markets/reference/stockmetaexchanges-1) · [Condition codes](https://docs.alpaca.markets/reference/stockmetaconditions-1)
- [Corporate actions (market data)](https://docs.alpaca.markets/reference/corporateactions-1) · [Announcements (Broker) blog](https://alpaca.markets/blog/introducing-corporate-actions-api-announcements/)
- [News articles](https://docs.alpaca.markets/reference/news-3) · [Historical news data](https://docs.alpaca.markets/us/docs/historical-news-data) · [Real-time news](https://docs.alpaca.markets/us/docs/streaming-real-time-news)
- [Most actives](https://docs.alpaca.markets/reference/mostactives-1) · [Top movers](https://docs.alpaca.markets/reference/movers-1)
- [Options bars](https://docs.alpaca.markets/reference/optionbars) · [Historical option data](https://docs.alpaca.markets/us/docs/historical-option-data)
- [WebSocket stream](https://docs.alpaca.markets/docs/streaming-market-data) · [Real-time stock data](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data)
- [About Market Data API](https://docs.alpaca.markets/us/docs/about-market-data-api) · [Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) · [Data plans/pricing](https://alpaca.markets/data)