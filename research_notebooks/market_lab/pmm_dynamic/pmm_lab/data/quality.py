"""Data quality audit and reporting."""

import json
import sys
from dataclasses import asdict
from typing import Optional

import numpy as np

from pmm_lab.config.params import AuditResult
from pmm_lab.data.candles import validate_candles


def run_audit(
    candles: np.ndarray,
    interval: str,
    output_path: Optional[str] = None,
) -> AuditResult:
    """Run a comprehensive data quality audit and optionally write to JSON.

    Calls validate_candles() and enriches the result with additional statistics:
    - Percentiles for close price (5th, 25th, 50th, 75th, 95th)
    - Percentiles for volume
    - Percentiles for bar-to-bar returns
    - Volume=0 candle count and fraction

    Parameters
    ----------
    candles : np.ndarray
        Canonical structured candle array.
    interval : str
        Candle interval (e.g. '5m').
    output_path : str, optional
        If provided, writes the full audit as a JSON file.

    Returns
    -------
    AuditResult
    """
    audit = validate_candles(candles, interval, strict=True)

    # Additional statistics for reporting
    close_prices = candles["close"]
    volumes = candles["volume"]

    percentile_keys = [5, 25, 50, 75, 95]
    close_percentiles = {
        f"p{p}": float(np.percentile(close_prices, p)) for p in percentile_keys
    }
    volume_percentiles = {
        f"p{p}": float(np.percentile(volumes, p)) for p in percentile_keys
    }

    # Bar-to-bar returns
    if len(close_prices) > 1:
        returns = np.diff(close_prices) / close_prices[:-1]
        return_percentiles = {
            f"p{p}": float(np.percentile(returns, p)) for p in percentile_keys
        }
    else:
        return_percentiles = {f"p{p}": 0.0 for p in percentile_keys}

    if output_path is not None:
        audit_dict = asdict(audit)
        audit_dict["close_percentiles"] = close_percentiles
        audit_dict["volume_percentiles"] = volume_percentiles
        audit_dict["return_percentiles"] = return_percentiles
        with open(output_path, "w") as f:
            json.dump(audit_dict, f, indent=2, default=str)

    return audit


if __name__ == "__main__":
    import os
    from pathlib import Path

    # Ensure pmm_lab is importable
    project_root = str(Path(__file__).resolve().parent.parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from pmm_lab.data.mongo import MongoCandleLoader
    from pmm_lab.config.params import DataQuery

    loader = MongoCandleLoader()

    if not loader.ping():
        print("ERROR: Cannot connect to MongoDB. Check MONGO_URI env var.")
        sys.exit(1)

    combos = loader.list_combos(quote_asset="USDT")
    if not combos:
        print("No USDT candle combos found in MongoDB.")
        sys.exit(1)

    combo = combos[0]
    print(f"Auditing: {combo['connector']} {combo['trading_pair']} {combo['interval']}")
    print(f"  Range: {combo['first_ts']} - {combo['last_ts']} ({combo['count']} docs)")

    query = DataQuery(
        connector=combo["connector"],
        trading_pair=combo["trading_pair"],
        interval=combo["interval"],
    )
    candles = loader.load_range(query)

    # Take up to 1000 candles for a quick audit
    if len(candles) > 1000:
        candles = candles[:1000]

    audit = run_audit(candles, combo["interval"])

    print(f"\n{'='*50}")
    print(f"AUDIT RESULT")
    print(f"{'='*50}")
    print(f"  Total rows:     {audit.total_rows}")
    print(f"  Expected rows:  {audit.expected_rows}")
    print(f"  Missing rows:   {audit.missing_rows}")
    print(f"  Duplicates:     {audit.duplicate_count}")
    print(f"  OHLC violations:{audit.ohlc_violations}")
    print(f"  Volume=0:       {audit.volume_zero_count} ({audit.volume_zero_fraction:.4f})")
    print(f"  Longest gap:    {audit.longest_gap_seconds}s")
    print(f"  Dataset hash:   {audit.dataset_hash[:16]}...")
    print(f"  Passed strict:  {audit.passed_strict}")
    if audit.failure_reasons:
        print(f"  Failures:")
        for reason in audit.failure_reasons:
            print(f"    - {reason}")
