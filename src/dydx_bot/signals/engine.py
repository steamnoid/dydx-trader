"""
Signal Engine - MINIMAL code to pass ONE test only.
"""

from typing import Dict, Any
from src.dydx_bot.signals.types import SignalType
from src.dydx_bot.signals.connection_manager import ConnectionManager


class SignalEngine:
    """Minimal SignalEngine to pass the test."""
    
    def __init__(self, signal_type: SignalType):
        """Initialize with signal type."""
        self.signal_type = signal_type
        self.connection_manager = ConnectionManager.get_instance()
    
    def calculate_signal(self, market_data: Dict[str, Any]) -> float:
        """Calculate signal score from market data."""
        # Minimal implementation - return fixed score for now
        return 50.0


class MomentumEngine(SignalEngine):
    """Momentum signal engine."""
    
    def __init__(self):
        """Initialize with momentum signal type."""
        super().__init__(signal_type=SignalType.MOMENTUM)
    
    def calculate_signal(self, market_data: Dict[str, Any]) -> float:
        """Calculate momentum signal score from market data."""
        # Calculate momentum from 24h price change
        price_change_24h = market_data.get("price_change_24h", 0.0)
        current_price = market_data.get("price", 0.0)
        
        if current_price > 0:
            # Calculate percentage change
            price_change_percent = (price_change_24h / current_price) * 100
        else:
            price_change_percent = 0.0
        
        # Convert price change to 0-100 score (50 = neutral)
        # Positive change > 50, negative change < 50
        # Scale by 2 for sensitivity (1% change = 2 point move)
        score = 50.0 + (price_change_percent * 2.0)
        
        # Clamp to 0-100 range
        return max(0.0, min(100.0, score))


class VolumeEngine(SignalEngine):
    """Volume signal engine."""
    
    def __init__(self):
        """Initialize with volume signal type."""
        super().__init__(signal_type=SignalType.VOLUME)
    
    def calculate_signal(self, market_data: Dict[str, Any]) -> float:
        """Calculate volume signal score from market data."""
        # Calculate volume signal from 24h volume and trades
        volume_24h = market_data.get("volume_24h", 0.0)
        trades_count = market_data.get("trades_count", 0)
        
        # Normalize volume by trades to get average trade size
        if trades_count > 0:
            avg_trade_size = volume_24h / trades_count
        else:
            avg_trade_size = 0.0
        
        # Use log scale for volume score (large volumes get higher scores)
        if volume_24h > 0:
            # Convert to score: higher volume = higher score
            # Use logarithmic scaling to handle wide range of volumes
            import math
            volume_score = min(100.0, max(0.0, 30.0 + math.log10(volume_24h + 1) * 8.0))
        else:
            volume_score = 0.0
        
        return volume_score


class VolatilityEngine(SignalEngine):
    """Volatility signal engine."""
    
    def __init__(self):
        """Initialize with volatility signal type."""
        super().__init__(signal_type=SignalType.VOLATILITY)
    
    def calculate_signal(self, market_data: Dict[str, Any]) -> float:
        """Calculate volatility signal score from market data."""
        # Calculate volatility from bid-ask spread and volatility metric
        volatility = market_data.get("volatility", 0.0)
        bid_price = market_data.get("bid_price", 0.0)
        ask_price = market_data.get("ask_price", 0.0)
        current_price = market_data.get("price", 0.0)
        
        # Calculate bid-ask spread as percentage of mid price
        if current_price > 0 and bid_price > 0 and ask_price > 0:
            spread_percent = ((ask_price - bid_price) / current_price) * 100
        else:
            spread_percent = 0.0
        
        # Combine base volatility with spread (both indicate volatility)
        volatility_score = (volatility * 1000) + (spread_percent * 20)  # Scale factors
        
        # Normalize to 0-100 range
        # Higher volatility = higher score
        score = min(100.0, max(0.0, volatility_score * 100))
        
        return score


class OrderbookEngine(SignalEngine):
    """Orderbook signal engine."""
    
    def __init__(self):
        """Initialize with orderbook signal type."""
        super().__init__(signal_type=SignalType.ORDERBOOK)
    
    def calculate_signal(self, market_data: Dict[str, Any]) -> float:
        """Calculate orderbook signal score from market data."""
        # Calculate orderbook imbalance from bid/ask sizes
        bid_size = market_data.get("bid_size", 0.0)
        ask_size = market_data.get("ask_size", 0.0)
        
        # Calculate order book imbalance
        total_size = bid_size + ask_size
        if total_size > 0:
            # 0.5 = balanced, >0.5 = bid heavy, <0.5 = ask heavy
            bid_ratio = bid_size / total_size
        else:
            bid_ratio = 0.5  # Neutral if no data
        
        # Convert ratio to 0-100 score
        # 0.5 = 50 (neutral), 1.0 = 100 (all bids), 0.0 = 0 (all asks)
        score = bid_ratio * 100.0
        
        # Clamp to 0-100 range
        return max(0.0, min(100.0, score))
