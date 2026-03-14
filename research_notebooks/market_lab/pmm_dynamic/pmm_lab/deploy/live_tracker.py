"""
Live performance tracker.

Connects to Hummingbot's PostgreSQL database and reads trade/order data
for a specific trading pair, computing live performance metrics that
can be compared against backtest predictions.

The Hummingbot database schema uses these key tables:
- TradeFill: completed trade fills with price, amount, fees
- Order: order lifecycle tracking

Usage:
    tracker = LivePerformanceTracker(db_url)
    live_metrics = tracker.get_performance("nonkyc", "XMR-USDT", hours=24)
"""

import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


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

        engine = self._get_engine()
        query = text("""
            SELECT
                trade_id, symbol, trade_type, price, amount,
                trade_fee_amount, trade_fee_currency, timestamp, order_type
            FROM "TradeFill"
            WHERE market = :connector
              AND symbol = :pair
              AND timestamp >= :since
            ORDER BY timestamp ASC
        """)

        trades = []
        try:
            with engine.connect() as conn:
                result = conn.execute(query, {
                    "connector": connector,
                    "pair": trading_pair,
                    "since": since.isoformat(),
                })
                for row in result:
                    trades.append(LiveTrade(
                        trade_id=str(row[0]),
                        trading_pair=str(row[1]),
                        side=str(row[2]).lower(),
                        price=float(row[3]),
                        amount=float(row[4]),
                        fee_amount=float(row[5]) if row[5] else 0.0,
                        fee_currency=str(row[6]) if row[6] else "",
                        timestamp=row[7] if isinstance(row[7], datetime) else datetime.fromisoformat(str(row[7])),
                        order_type=str(row[8]) if row[8] else "LIMIT",
                    ))
        except Exception as e:
            logger.warning("Failed to fetch trades: %s", e)
            # Table might not exist yet or have different schema
            # Return empty list rather than crashing

        return trades

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

        # Fee estimation (assume fees in quote currency)
        total_fees = sum(
            t.fee_amount * (t.price if t.fee_currency != quote_currency else 1.0)
            for t in trades
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
        )
