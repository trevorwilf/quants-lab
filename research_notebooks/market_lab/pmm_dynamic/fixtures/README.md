# Frozen Test Fixtures

This directory contains frozen candle data + expected feature values
for regression testing.

Generate fixtures with:
```python
from pmm_lab.parity.fixtures import generate_frozen_fixture
generate_frozen_fixture(candles, config_params, name="btc_usdt_5m")
```

Fixtures are used by the parity harness to verify that code changes
don't alter feature computation or export format.
