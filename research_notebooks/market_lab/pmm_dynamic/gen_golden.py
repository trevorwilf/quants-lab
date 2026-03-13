import numpy as np
import json
import sys

CANDLE_DTYPE = np.dtype([
    ('timestamp', 'int64'), ('open', 'float64'), ('high', 'float64'),
    ('low', 'float64'), ('close', 'float64'), ('volume', 'float64'),
    ('is_forward_fill', 'bool'),
])

rng = np.random.default_rng(seed=42)
n = 100
start_ts = 1756833000
interval = 300
timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype='int64')

price = 100000.0
rows = []
for i in range(n):
    change = rng.normal(0, 50)
    open_p = price
    close_p = open_p + change
    high_p = max(open_p, close_p) + abs(rng.normal(0, 20))
    low_p = min(open_p, close_p) - abs(rng.normal(0, 20))
    open_p = max(open_p, 1.0)
    close_p = max(close_p, 1.0)
    high_p = max(high_p, max(open_p, close_p))
    low_p = max(low_p, 0.01)
    low_p = min(low_p, min(open_p, close_p))
    vol = rng.uniform(0.05, 2.0)
    rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
    price = close_p

candles = np.array(rows, dtype=CANDLE_DTYPE)

# Save as JSON
candle_list = []
for r in candles:
    candle_list.append({
        'timestamp': int(r['timestamp']),
        'open': float(r['open']),
        'high': float(r['high']),
        'low': float(r['low']),
        'close': float(r['close']),
        'volume': float(r['volume']),
    })
with open('tests/fixtures/golden_candles_100.json', 'w') as f:
    json.dump(candle_list, f, indent=2)
print("Saved golden_candles_100.json")

from pmm_lab.features.pmm_dynamic_features import compute_pmm_dynamic_features
features = compute_pmm_dynamic_features(candles)
print(f'warmup_end = {features.warmup_end}')
for bar in [60, 70, 80, 90]:
    print(f'Bar {bar}:')
    print(f'  reference_price = {features.reference_price[bar]!r}')
    print(f'  spread_multiplier = {features.spread_multiplier[bar]!r}')
    print(f'  natr = {features.natr[bar]!r}')
    print(f'  price_multiplier = {features.price_multiplier[bar]!r}')
