"""Default constants for PMM Lab."""

# v1 scope: USDT-quote pairs only
SUPPORTED_QUOTE_ASSETS = ("USDT",)

# Connectors with candle data available
SUPPORTED_CONNECTORS = ("mexc", "nonkyc")

# Valid candle intervals and their duration in seconds
INTERVAL_SECONDS = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}

# Timestamp mode
DEFAULT_TIMESTAMP_MODE = "open"

# Dataset audit thresholds
MAX_OHLC_VIOLATION_FRACTION = 0.001  # fail audit if > 0.1% violations
MAX_DUPLICATE_FRACTION = 0.0         # zero tolerance for duplicates

# Forward-fill detection thresholds
MAX_FORWARD_FILL_FRACTION = 0.01     # fail audit if > 1% forward-filled bars

# Gap thresholds (strict mode)
MAX_MISSING_ROW_FRACTION = 0.05      # fail if > 5% of expected rows are missing
MAX_LONGEST_GAP_MULTIPLIER = 100     # fail if longest gap > 100 × interval_seconds
