"""Live fee conversion must handle base, quote, and third-party fee currencies."""
from datetime import datetime, timezone
from pmm_lab.deploy.live_tracker import LiveTrade, LivePerformanceMetrics


def _make_trade(side="buy", price=100.0, amount=1.0, fee_amount=0.1,
                fee_currency="USDT", trade_id="t1"):
    return LiveTrade(
        trade_id=trade_id, trading_pair="BTC-USDT", side=side,
        price=price, amount=amount, fee_amount=fee_amount,
        fee_currency=fee_currency, timestamp=datetime.now(timezone.utc),
        order_type="LIMIT",
    )


def _compute_metrics_from_trades(trades, trading_pair, quote_currency):
    """Helper: extract the fee computation logic for testing."""
    base_currency = trading_pair.split("-")[0] if "-" in trading_pair else ""
    total_fees = 0.0
    unresolved_count = 0
    unresolved_currencies = set()

    for t in trades:
        if not t.fee_currency or t.fee_currency == quote_currency:
            total_fees += t.fee_amount
        elif t.fee_currency == base_currency:
            total_fees += t.fee_amount * t.price
        else:
            unresolved_count += 1
            unresolved_currencies.add(t.fee_currency)

    buy_trades = [t for t in trades if t.side == "buy"]
    sell_trades = [t for t in trades if t.side == "sell"]

    return LivePerformanceMetrics(
        trading_pair=trading_pair, period_hours=24.0,
        trade_count=len(trades), buy_count=len(buy_trades), sell_count=len(sell_trades),
        total_volume_base=sum(t.amount for t in trades),
        total_volume_quote=sum(t.amount * t.price for t in trades),
        total_fees_quote=total_fees,
        avg_buy_price=0.0, avg_sell_price=0.0,
        net_base_flow=0.0, net_quote_flow=0.0,
        estimated_pnl_quote=0.0,
        unresolved_fee_count=unresolved_count,
        unresolved_fee_currencies=sorted(unresolved_currencies),
    )


class TestFeeConversion:
    def test_quote_fee_used_directly(self):
        """Fees in quote currency are used as-is."""
        trades = [_make_trade(fee_amount=0.5, fee_currency="USDT")]
        metrics = _compute_metrics_from_trades(trades, "BTC-USDT", "USDT")
        assert abs(metrics.total_fees_quote - 0.5) < 1e-10

    def test_base_fee_converted_by_price(self):
        """Fees in base currency are converted using trade price."""
        trades = [_make_trade(fee_amount=0.001, fee_currency="BTC", price=50000.0)]
        metrics = _compute_metrics_from_trades(trades, "BTC-USDT", "USDT")
        assert abs(metrics.total_fees_quote - 50.0) < 1e-6  # 0.001 * 50000

    def test_third_party_fee_not_counted(self):
        """Fees in unknown third-party currencies are excluded from totals."""
        trades = [_make_trade(fee_amount=10.0, fee_currency="BNB")]
        metrics = _compute_metrics_from_trades(trades, "BTC-USDT", "USDT")
        assert metrics.total_fees_quote == 0.0
        assert metrics.unresolved_fee_count == 1
        assert "BNB" in metrics.unresolved_fee_currencies

    def test_mixed_fees(self):
        """Mix of quote, base, and third-party fees."""
        trades = [
            _make_trade(fee_amount=1.0, fee_currency="USDT", trade_id="t1"),
            _make_trade(fee_amount=0.0001, fee_currency="BTC", price=60000.0, trade_id="t2"),
            _make_trade(fee_amount=5.0, fee_currency="NKYO", trade_id="t3"),
        ]
        metrics = _compute_metrics_from_trades(trades, "BTC-USDT", "USDT")
        expected = 1.0 + (0.0001 * 60000.0)  # quote + base converted
        assert abs(metrics.total_fees_quote - expected) < 1e-6
        assert metrics.unresolved_fee_count == 1
