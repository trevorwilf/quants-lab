"""Trace exactly what the worker sees when it resolves the lake root."""
import sys, os
sys.path.insert(0, '/quants-lab/research_notebooks/bowaka_v2_lab/src')
sys.path.insert(0, '/quants-lab/research_notebooks/bowaka_common/src')

from bowaka_v2_lab.config import load_config
from bowaka_v2_lab.data.lineage import resolve_lake_root, _coerce_lake_root

study = "iex__bowaka_v2_iex_walkforward_conservative_b44ea02b_20260530"
resolved_cfg_path = (
    f"/quants-lab/research_notebooks/bowaka_v2_lab/artifacts/"
    f"resolved_configs/{study}__resolved.yml"
)

print(f"--- env ---")
print(f"  MARKET_DATA_ROOT: {os.environ.get('MARKET_DATA_ROOT', '<unset>')}")
print(f"  CWD: {os.getcwd()}")
print(f"  __file__ of bowaka_common store:")
from bowaka_common.marketdata.store import store as _s
print(f"    {_s.__file__ if hasattr(_s, '__file__') else 'n/a'}")
from bowaka_common.marketdata import store as smod
print(f"    {smod.__file__}")
print()

cfg = load_config(resolved_cfg_path)
print(f"--- resolved config ---")
print(f"  market_data: {cfg.get('market_data')}")
print()

lake = resolve_lake_root(cfg)
print(f"--- resolver output ---")
print(f"  resolve_lake_root(cfg) -> {lake}")
print(f"  type: {type(lake).__name__}")
print(f"  .name: {lake.name}")
print(f"  is_dir: {lake.is_dir()}")
print(f"  resolved: {lake.resolve()}")
print()

p = lake / 'bars' / 'vendor=alpaca' / 'feed=iex' / 'timeframe=1d' / 'adjustment=split_adjusted'
print(f"--- partition check ---")
print(f"  expected partition: {p}")
print(f"  exists: {p.is_dir()}")
if p.is_dir():
    n = sum(1 for _ in p.iterdir())
    print(f"  symbol partitions: {n}")
else:
    print(f"  ** PARTITION DOES NOT EXIST AT RESOLVED PATH **")

print()
print(f"--- _coerce_lake_root check ---")
try:
    coerced = _coerce_lake_root(lake)
    print(f"  OK: {coerced}")
except RuntimeError as e:
    print(f"  REJECTED: {e}")

# Now mimic the worker even more closely: rebuild a tiny supplier and try
# to read one symbol's daily bars. If THIS returns empty, the bug is past
# the resolver — in the supplier.
print()
print(f"--- supplier read test ---")
from bowaka_common.marketdata.store import MarketDataStore
import datetime as dt
store = MarketDataStore(lake, vendor="alpaca")
test_sym = "AAPL"
try:
    df = store.daily_bars(
        test_sym,
        dt.datetime(2025, 7, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2025, 8, 27, tzinfo=dt.timezone.utc),
        feed="iex", adjustment="split_adjusted",
    )
    print(f"  store.daily_bars({test_sym}) -> rows={len(df)}")
    if len(df) > 0:
        print(f"  first row: {df.iloc[0].to_dict()}")
    else:
        print(f"  ** SUPPLIER RETURNED EMPTY despite path resolving correctly **")
except Exception as e:
    print(f"  EXCEPTION: {type(e).__name__}: {e}")
