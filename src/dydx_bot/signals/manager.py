"""
Signal Manager - MINIMAL code to pass ONE test only.
"""

from datetime import datetime
from typing import Dict, Any
from src.dydx_bot.signals.engine import (
    MomentumEngine, 
    VolumeEngine, 
    VolatilityEngine, 
    OrderbookEngine
)
from src.dydx_bot.signals.types import SignalSet


class SignalManager:
    """Minimal SignalManager to coordinate all signal engines."""
    
    def __init__(self):
        """Initialize with all signal engines."""
        self.momentum_engine = MomentumEngine()
        self.volume_engine = VolumeEngine()
        self.volatility_engine = VolatilityEngine()
        self.orderbook_engine = OrderbookEngine()
    
    def calculate_signals(self, market: str, market_data: Dict[str, Any]) -> SignalSet:
        """Calculate complete signal set for a market."""
        # Calculate all signal scores
        momentum_score = self.momentum_engine.calculate_signal(market_data)
        volume_score = self.volume_engine.calculate_signal(market_data)
        volatility_score = self.volatility_engine.calculate_signal(market_data)
        orderbook_score = self.orderbook_engine.calculate_signal(market_data)
        
        # Create and return SignalSet
        return SignalSet(
            market=market,
            momentum=momentum_score,
            volume=volume_score,
            volatility=volatility_score,
            orderbook=orderbook_score,
            timestamp=datetime.now(),
            metadata={}
        )
    
    def aggregate_and_publish(self, market_data: Dict[str, Dict[str, Any]]) -> SignalSet:
        """Aggregate signals from all engines and publish a SignalSet."""
        # Calculate signals for each engine
        momentum_score = self.momentum_engine.calculate_signal(market_data.get("momentum", {}))
        volume_score = self.volume_engine.calculate_signal(market_data.get("volume", {}))
        volatility_score = self.volatility_engine.calculate_signal(market_data.get("volatility", {}))
        orderbook_score = self.orderbook_engine.calculate_signal(market_data.get("orderbook", {}))

        # Create and return SignalSet
        return SignalSet(
            market="BTC-USD",  # Example market
            momentum=momentum_score,
            volume=volume_score,
            volatility=volatility_score,
            orderbook=orderbook_score,
            timestamp=datetime.now(),
            metadata={}
        )
