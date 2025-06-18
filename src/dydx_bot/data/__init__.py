"""
Layer 3: Market Data Processing

This layer processes raw market data from Layer 2 (connection) into structured formats
for trading signals and autonomous decision making.

Key Components:
- Market data aggregation (OHLCV)
- Funding rate calculations
- Orderbook reconstruction
- Real-time performance metrics
"""

from .processor import MarketDataProcessor
from .types import MarketDataUpdate, OrderBookUpdate, TradeUpdate

__all__ = ['MarketDataProcessor', 'MarketDataUpdate', 'OrderBookUpdate', 'TradeUpdate']
