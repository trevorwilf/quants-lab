"""
Live performance tracker.

Connects to Hummingbot's PostgreSQL database and reads trade/order data
for a specific trading pair, computing live performance metrics that
can be compared against backtest predictions.

The Hummingbot database schema uses these key tables:
- TradeFill: completed trade fills with price, amount, fees
- Order: order lifecycle tracking

Hummingbot TradeFill schema (verified against Hummingbot source):
- timestamp: BigInteger — Unix MILLISECONDS
- exchange_trade_id: exchange-side trade ID (not "trade_id")
- trade_fee: TEXT/JSON — {"percent": str, "percent_token": str,
    "flat_fees": [{"token": str, "amount": str}]}
- trade_fee_in_quote: Float — pre-computed fee in quote currency

Usage:
    tracker = LivePerformanceTracker(db_url)
    live_metrics = tracker.get_performance("nonkyc", "XMR-USDT", hours=24)
"""

import json as _json
import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 2  # Bumped from implicit v1 (wrong column names) to v2 (correct schema)

# Hummingbot stores price/amount/trade_fee_in_quote as BIGINT with 1e6 scaling.
# The actual float value is column_value / BIGINT_SCALE.
# Timestamp is also BIGINT but stores Unix milliseconds — do NOT scale it.
# trade_fee JSON values are already human-readable strings — do NOT scale them.
BIGINT_SCALE = 1_000_000

# Columns we expect on the TradeFill table.
_EXPECTED_COLUMNS = frozenset({
    "exchange_trade_id", "symbol", "trade_type", "price", "amount",
    "trade_fee", "trade_fee_in_quote", "timestamp", "order_type", "market",
})


class TrackerHealth:
    """Health state for the last tracker query."""
    OK = "ok"
    NO_DATA = "no_data"
    DB_ERROR = "db_error"
    SCHEMA_ERROR = "schema_error"


@dataclass
class LiveTrade:
    """One trade from the Hummingbot database."""
    trade_id: str
    trading_pair: str
    side: str                  # "buy" or "sell"
    price: float
    amount: float
    fee_amount: float
    fee_currency: str
    timestamp: datetime
    order_type: str            # "LIMIT", "MARKET", etc.


@dataclass
class LivePerformanceMetrics:
    """Performance metrics computed from live trade data."""
    trading_pair: str
    period_hours: float
    trade_count: int
    buy_count: int
    sell_count: int
    total_volume_base: float
    total_volume_quote: float
    total_fees_quote: float
    avg_buy_price: float
    avg_sell_price: float
    net_base_flow: float        # positive = net bought, negative = net sold
    net_quote_flow: float       # positive = net received quote, negative = net spent
    estimated_pnl_quote: float  # rough PnL from avg sell - avg buy
    first_trade_at: Optional[datetime] = None
    last_trade_at: Optional[datetime] = None
    # Fee currency breakdown
    unresolved_fee_count: int = 0             # fees in neither base nor quote
    unresolved_fee_currencies: List[str] = None  # which currencies couldn't be converted
    # Raw trade list for downstream diagnostics (optional, not serialized)
    _trades: Optional[List['LiveTrade']] = None

    def __post_init__(self):
        if self.unresolved_fee_currencies is None:
            self.unresolved_fee_currencies = []


class LivePerformanceTracker:
    """Track live trading performance from Hummingbot's PostgreSQL.

    Parameters
    ----------
    db_url : str
        SQLAlchemy database URL for Hummingbot's PostgreSQL.
        Example: "postgresql+psycopg2://hbot:<password>@<host>:5432/hummingbot_api"
    """

    def __init__(self, db_url: Optional[str] = None):
        if db_url is None:
            db_url = self._build_db_url()
        self._db_url = db_url
        self._engine = None
        self._last_health: str = TrackerHealth.OK
        self._last_error: Optional[str] = None
        self._schema_checked: bool = False

    @staticmethod
    def _build_db_url() -> str:
        """Build DB URL from environment or .env file."""
        import os
        from pathlib import Path

        # Check env first
        url = os.environ.get("HBOT_DB_URL")
        if url:
            return url

        # Try .env file
        search_dir = Path(__file__).resolve().parent.parent.parent
        for _ in range(10):
            env_file = search_dir / ".env"
            if env_file.exists():
                dotenv = {}
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, _, v = line.partition("=")
                        dotenv[k.strip()] = v.strip()

                host = dotenv.get("TRUENAS_LAN_IP", "").strip()
                password = dotenv.get("POSTGRES_PASSWORD", "").strip()
                if host and password:
                    return f"postgresql+psycopg2://hbot:{password}@{host}:5432/hummingbot_api"
                break

            parent = search_dir.parent
            if parent == search_dir:
                break
            search_dir = parent

        return "postgresql+psycopg2://hbot:password@localhost:5432/hummingbot_api"

    def _get_engine(self):
        """Lazy-create SQLAlchemy engine."""
        if self._engine is None:
            from sqlalchemy import create_engine
            self._engine = create_engine(self._db_url, echo=False)
        return self._engine

    def ping(self) -> bool:
        """Check if the database is reachable."""
        try:
            from sqlalchemy import text
            engine = self._get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def _check_schema(self, conn) -> bool:
        """Verify expected columns exist on the TradeFill table.

        Sets health to SCHEMA_ERROR and returns False if columns are missing.
        """
        from sqlalchemy import text
        try:
            # Use information_schema to check columns (works on PostgreSQL and SQLite with pragma)
            result = conn.execute(text(
                """SELECT column_name FROM information_schema.columns
                   WHERE table_name = 'TradeFill'"""
            ))
            actual_columns = {row[0] for row in result}
        except Exception:
            # Fallback for SQLite (used in tests)
            try:
                result = conn.execute(text('PRAGMA table_info("TradeFill")'))
                actual_columns = {row[1] for row in result}
            except Exception as e:
                logger.warning("Cannot inspect TradeFill schema: %s", e)
                self._last_health = TrackerHealth.SCHEMA_ERROR
                self._last_error = f"Schema check failed: {e}"
                return False

        missing = _EXPECTED_COLUMNS - actual_columns
        if missing:
            msg = f"TradeFill table missing columns: {sorted(missing)}"
            logger.warning(msg)
            self._last_health = TrackerHealth.SCHEMA_ERROR
            self._last_error = msg
            return False
        return True

    @staticmethod
    def _parse_trade_fee(trade_fee_raw, trade_fee_in_quote) -> tuple:
        """Parse fee from TradeFill row.

        Returns (fee_amount, fee_currency).  Prefers trade_fee_in_quote
        when available; falls back to parsing the trade_fee JSON.
        """
        # Prefer the pre-computed quote fee
        if trade_fee_in_quote is not None and float(trade_fee_in_quote) > 0:
            return float(trade_fee_in_quote) / BIGINT_SCALE, ""

        # Fall back to JSON parsing
        if trade_fee_raw:
            try:
                fee_data = _json.loads(str(trade_fee_raw))
                flat_fees = fee_data.get("flat_fees", [])
                if flat_fees:
                    total = sum(float(f.get("amount", 0)) for f in flat_fees)
                    # Use the token from the first flat fee entry
                    currency = flat_fees[0].get("token", "") if flat_fees else ""
                    return total, currency
                # Percentage-only fee — cannot compute absolute amount without context
                pct = float(fee_data.get("percent", 0))
                if pct > 0:
                    currency = fee_data.get("percent_token", "")
                    return 0.0, currency  # caller needs trade notional to convert
            except (ValueError, TypeError, KeyError) as e:
                logger.debug("Could not parse trade_fee JSON: %s", e)

        return 0.0, ""

    def get_trades(
        self,
        connector: str,
        trading_pair: str,
        hours: float = 24.0,
        since: Optional[datetime] = None,
    ) -> List[LiveTrade]:
        """Fetch recent trades from the database.

        Parameters
        ----------
        connector : str
            Exchange connector name (e.g., "nonkyc").
        trading_pair : str
            Trading pair (e.g., "XMR-USDT").
        hours : float
            Look back this many hours from now.
        since : datetime, optional
            Override: fetch trades since this timestamp.

        Returns
        -------
        List[LiveTrade]
        """
        from sqlalchemy import text

        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Convert datetime to Unix milliseconds for the BigInteger timestamp column
        since_ms = int(since.timestamp() * 1000)

        engine = self._get_engine()
        query = text("""
            SELECT
                exchange_trade_id, symbol, trade_type, price, amount,
                trade_fee, trade_fee_in_quote, timestamp, order_type
            FROM "TradeFill"
            WHERE market = :connector
              AND symbol = :pair
              AND timestamp >= :since_ms
            ORDER BY timestamp ASC
        """)

        trades = []
        try:
            with engine.connect() as conn:
                if not self._schema_checked:
                    if not self._check_schema(conn):
                        return trades
                    self._schema_checked = True

                result = conn.execute(query, {
                    "connector": connector,
                    "pair": trading_pair,
                    "since_ms": since_ms,
                })
                for row in result:
                    fee_amount, fee_currency = self._parse_trade_fee(row[5], row[6])
                    # timestamp is Unix milliseconds — convert to datetime
                    ts_ms = int(row[7])
                    ts_dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
                    trades.append(LiveTrade(
                        trade_id=str(row[0]),
                        trading_pair=str(row[1]),
                        side=str(row[2]).lower(),
                        price=float(row[3]) / BIGINT_SCALE,
                        amount=float(row[4]) / BIGINT_SCALE,
                        fee_amount=fee_amount,
                        fee_currency=fee_currency,
                        timestamp=ts_dt,
                        order_type=str(row[8]) if row[8] else "LIMIT",
                    ))
            self._last_health = TrackerHealth.OK if trades else TrackerHealth.NO_DATA
            self._last_error = None
        except Exception as e:
            logger.warning("Failed to fetch trades: %s", e)
            self._last_health = TrackerHealth.DB_ERROR
            self._last_error = str(e)

        return trades

    @property
    def last_health(self) -> str:
        """Health state from the last get_trades() call."""
        return self._last_health

    @property
    def last_error(self) -> Optional[str]:
        """Error message from the last get_trades() call, or None."""
        return self._last_error

    def get_performance(
        self,
        connector: str,
        trading_pair: str,
        hours: float = 24.0,
        quote_currency: str = "USDT",
    ) -> LivePerformanceMetrics:
        """Compute live performance metrics from recent trades.

        Parameters
        ----------
        connector : str
            Exchange connector.
        trading_pair : str
            Trading pair.
        hours : float
            Look back period in hours.
        quote_currency : str
            Quote currency for fee conversion.

        Returns
        -------
        LivePerformanceMetrics
        """
        trades = self.get_trades(connector, trading_pair, hours)

        if not trades:
            return LivePerformanceMetrics(
                trading_pair=trading_pair,
                period_hours=hours,
                trade_count=0, buy_count=0, sell_count=0,
                total_volume_base=0.0, total_volume_quote=0.0,
                total_fees_quote=0.0,
                avg_buy_price=0.0, avg_sell_price=0.0,
                net_base_flow=0.0, net_quote_flow=0.0,
                estimated_pnl_quote=0.0,
            )

        buy_trades = [t for t in trades if t.side == "buy"]
        sell_trades = [t for t in trades if t.side == "sell"]

        total_buy_base = sum(t.amount for t in buy_trades)
        total_sell_base = sum(t.amount for t in sell_trades)
        total_buy_quote = sum(t.amount * t.price for t in buy_trades)
        total_sell_quote = sum(t.amount * t.price for t in sell_trades)

        avg_buy = total_buy_quote / total_buy_base if total_buy_base > 0 else 0.0
        avg_sell = total_sell_quote / total_sell_base if total_sell_base > 0 else 0.0

        # Fee estimation — branch by fee currency
        base_currency = trading_pair.split("-")[0] if "-" in trading_pair else ""
        total_fees = 0.0
        unresolved_count = 0
        unresolved_currencies = set()

        for t in trades:
            if not t.fee_currency or t.fee_currency == quote_currency:
                # Fee is already in quote currency
                total_fees += t.fee_amount
            elif t.fee_currency == base_currency:
                # Fee is in base currency — convert using trade price
                total_fees += t.fee_amount * t.price
            else:
                # Third-party fee asset — cannot safely convert
                unresolved_count += 1
                unresolved_currencies.add(t.fee_currency)
                logger.warning(
                    "Trade %s: fee in %s (not %s or %s) — cannot convert, excluded from totals",
                    t.trade_id, t.fee_currency, quote_currency, base_currency,
                )

        # Net flows
        net_base = total_buy_base - total_sell_base
        net_quote = total_sell_quote - total_buy_quote - total_fees

        # Rough PnL (only meaningful if roughly balanced)
        min_matched = min(total_buy_base, total_sell_base)
        if min_matched > 0 and avg_buy > 0:
            estimated_pnl = (avg_sell - avg_buy) * min_matched - total_fees
        else:
            estimated_pnl = -total_fees  # only fees spent, no round-trips

        return LivePerformanceMetrics(
            trading_pair=trading_pair,
            period_hours=hours,
            trade_count=len(trades),
            buy_count=len(buy_trades),
            sell_count=len(sell_trades),
            total_volume_base=total_buy_base + total_sell_base,
            total_volume_quote=total_buy_quote + total_sell_quote,
            total_fees_quote=total_fees,
            avg_buy_price=avg_buy,
            avg_sell_price=avg_sell,
            net_base_flow=net_base,
            net_quote_flow=net_quote,
            estimated_pnl_quote=estimated_pnl,
            first_trade_at=trades[0].timestamp if trades else None,
            last_trade_at=trades[-1].timestamp if trades else None,
            unresolved_fee_count=unresolved_count,
            unresolved_fee_currencies=sorted(unresolved_currencies),
            _trades=trades,
        )
