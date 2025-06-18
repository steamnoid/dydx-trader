"""
Data types for Layer 3 market data processing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class MarketDataUpdate:
    """
    Market data update from WebSocket or REST API.
    """
    market: str
    price: float
    volume_24h: float
    price_change_24h: float
    timestamp: datetime
    orderbook_spread: Optional[float] = None
    trade_count: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class OrderBookUpdate:
    """
    Order book update data.
    """
    market: str
    bids: list  # [(price, size), ...]
    asks: list  # [(price, size), ...]
    timestamp: datetime


@dataclass
class TradeUpdate:
    """
    Trade update data.
    """
    market: str
    price: float
    size: float
    side: str  # 'buy' or 'sell'
    timestamp: datetime
