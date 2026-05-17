# Bowaka Lab tests

## Fixtures

`tests/fixtures/` holds frozen regression data:

- `daily_bars_small.parquet` — 6 synthetic symbols × ~22 sessions of synthetic
  daily bars.
- `expected_features.json` — golden output of `compute_daily_features()` on the
  bars fixture with the canonical PrefilterConfig (see
  `tests/_generate_daily_fixture.py`).
- `expected_candidates.json` — golden output of `apply_prefilter()` on the
  features fixture.

Do **not** regenerate fixtures at test time. Regression tests compare against
the frozen JSON; if the math changes intentionally, regenerate via:

```bash
python tests/_generate_daily_fixture.py
```

and commit the regenerated `.parquet` + `.json` together with the code change.

## Markers

- `live_mongo` — requires a reachable MongoDB instance (via `MONGO_URI`).
- `live_alpaca` — requires `ALPACA_API_KEY_ID` and `ALPACA_API_SECRET_KEY`.
- `slow` — long-running.

Run the default suite (skip live_alpaca and slow):

```bash
python -m pytest tests -q --tb=short -m "not live_alpaca and not slow"
```

## Source-of-truth parity test

`tests/integration/test_prefilter_parity_with_source.py` compares the new
`compute_daily_features` to the legacy `bowaka_prefilter.compute_features`.
It is skipped unless `BOWAKA_SOURCE_STRATEGY_ROOT` is set, e.g.:

```bash
export BOWAKA_SOURCE_STRATEGY_ROOT=/path/to/openalgo
python -m pytest tests/integration/test_prefilter_parity_with_source.py -v
```

The env var must point to a directory containing `scripts/bowaka_prefilter.py`.
