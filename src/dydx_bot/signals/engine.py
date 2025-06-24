"""
Signal Engine - Streaming real-time signal processing.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime
from src.dydx_bot.signals.types import SignalType
from src.dydx_bot.connection.manager import get_connection_manager


class StreamingSignalEngine:
    """Streaming signal engine that updates signals in real-time from WebSocket data."""
    
    def __init__(self, signal_type: SignalType, market_id: str):
        """Initialize streaming signal engine for a specific market."""
        self.signal_type = signal_type
        self.market_id = market_id
        self.latest_score = 50.0  # Start with neutral score
        self.last_update = time.time()
        self._market_data_cache = {}
        
        # Register with connection manager for streaming updates
        self.connection_manager = get_connection_manager()
        self.connection_manager.register_message_handler(self._on_websocket_message)
    
    def _on_websocket_message(self, ws, message: Dict[str, Any]):
        """Handle WebSocket messages and update signals in real-time."""
        try:
            # Filter messages for this market
            if not self._is_relevant_message(message):
                return
            
            # Update market data cache
            self._update_market_data_cache(message)
            
            # Calculate new signal score from streaming data
            new_score = self._calculate_streaming_signal(self._market_data_cache)
            
            # Update latest score if changed
            if abs(new_score - self.latest_score) > 0.1:  # Threshold to avoid noise
                self.latest_score = new_score
                self.last_update = time.time()
                
        except Exception as e:
            # Silent error handling for production stability
            pass
    
    def _is_relevant_message(self, message: Dict[str, Any]) -> bool:
        """Check if message is relevant to this market and signal type."""
        channel = message.get('channel', '')
        market = message.get('id', '')
        
        # Match market ID and relevant channels
        if market != self.market_id:
            return False
            
        # Different signal types care about different channels
        if self.signal_type == SignalType.MOMENTUM and 'trades' in channel:
            return True
        elif self.signal_type == SignalType.VOLUME and 'trades' in channel:
            return True
        elif self.signal_type == SignalType.VOLATILITY and ('trades' in channel or 'orderbook' in channel):
            return True
        elif self.signal_type == SignalType.ORDERBOOK and 'orderbook' in channel:
            return True
            
        return False
    
    def _update_market_data_cache(self, message: Dict[str, Any]):
        """Update market data cache with new WebSocket data."""
        channel = message.get('channel', '')
        contents = message.get('contents', {})
        
        if 'trades' in channel:
            # Update trade data for momentum/volume calculations
            trades = contents.get('trades', [])
            if trades:
                latest_trade = trades[-1]
                self._market_data_cache.update({
                    'latest_price': float(latest_trade.get('price', 0)),
                    'latest_size': float(latest_trade.get('size', 0)),
                    'trade_timestamp': latest_trade.get('createdAt', ''),
                })
                
        elif 'orderbook' in channel:
            # Update orderbook data for volatility/orderbook calculations
            asks = contents.get('asks', [])
            bids = contents.get('bids', [])
            
            if asks and bids:
                best_ask = asks[0] if asks else {'price': '0', 'size': '0'}
                best_bid = bids[0] if bids else {'price': '0', 'size': '0'}
                
                self._market_data_cache.update({
                    'ask_price': float(best_ask.get('price', 0)),
                    'ask_size': float(best_ask.get('size', 0)),
                    'bid_price': float(best_bid.get('price', 0)),
                    'bid_size': float(best_bid.get('size', 0)),
                })
    
    def _calculate_streaming_signal(self, market_data: Dict[str, Any]) -> float:
        """Calculate signal score from streaming market data - to be overridden by subclasses."""
        return 50.0
    
    def get_latest_signal(self) -> float:
        """Get the latest signal score (no calculation needed - already updated from stream)."""
        return self.latest_score
    
    def calculate_signal(self, market_data: Dict[str, Any], market_id: Optional[str] = None) -> float:
        """
        Calculate signal score for any market using market_id as metadata.
        Legacy method for backward compatibility - supports both streaming and on-demand calculation.
        """
        # For on-demand calculation, use the provided market_data
        if market_id:
            # Use market_id as metadata for logging/debugging
            return self._calculate_streaming_signal(market_data)
        else:
            # Legacy behavior - return cached streaming signal
            return self.latest_score
    
    def shutdown(self):
        """Clean shutdown - unregister from connection manager."""
        try:
            self.connection_manager.unregister_message_handler(self._on_websocket_message)
        except:
            pass


class SignalEngine:
    """Legacy SignalEngine for backward compatibility."""
    
    def __init__(self, signal_type: SignalType):
        """Initialize with signal type."""
        self.signal_type = signal_type
    
    def calculate_signal(self, market_data: Dict[str, Any]) -> float:
        """Calculate signal score from market data."""
        # Minimal implementation - return fixed score for now
        return 50.0


class MomentumEngine(StreamingSignalEngine):
    """Streaming momentum signal engine."""
    
    def __init__(self, market_id: str = "BTC-USD"):
        """Initialize streaming momentum engine for a specific market."""
        super().__init__(signal_type=SignalType.MOMENTUM, market_id=market_id)
        self._price_history = []  # Store recent prices for momentum calculation
        
    def _calculate_streaming_signal(self, market_data: Dict[str, Any]) -> float:
        """Calculate momentum signal from streaming trade data."""
        latest_price = market_data.get("latest_price", 0.0)
        
        if latest_price > 0:
            # Add to price history
            self._price_history.append(latest_price)
            
            # Keep only last 20 prices for momentum calculation
            if len(self._price_history) > 20:
                self._price_history.pop(0)
            
            # Calculate momentum from price trend
            if len(self._price_history) >= 2:
                old_price = self._price_history[0]
                price_change_percent = ((latest_price - old_price) / old_price) * 100
                
                # Convert to 0-100 score (50 = neutral)
                score = 50.0 + (price_change_percent * 2.0)
                return max(0.0, min(100.0, score))
        
        return 50.0  # Neutral if no data
    
    def calculate_signal(self, market_data: Dict[str, Any]) -> float:
        """Legacy method - calculate momentum from batch data."""
        price_change_24h = market_data.get("price_change_24h", 0.0)
        current_price = market_data.get("price", 0.0)
        
        if current_price > 0:
            price_change_percent = (price_change_24h / current_price) * 100
            score = 50.0 + (price_change_percent * 2.0)
            return max(0.0, min(100.0, score))
        
        return 50.0


class VolumeEngine(StreamingSignalEngine):
    """Streaming volume signal engine."""
    
    def __init__(self, market_id: str = "BTC-USD"):
        """Initialize streaming volume engine for a specific market."""
        super().__init__(signal_type=SignalType.VOLUME, market_id=market_id)
        self._volume_window = []  # Store recent trade sizes
        
    def _calculate_streaming_signal(self, market_data: Dict[str, Any]) -> float:
        """Calculate volume signal from streaming trade data."""
        latest_size = market_data.get("latest_size", 0.0)
        
        if latest_size > 0:
            # Add to volume window
            self._volume_window.append(latest_size)
            
            # Keep only last 50 trades for volume analysis
            if len(self._volume_window) > 50:
                self._volume_window.pop(0)
            
            # Calculate average volume and score
            if self._volume_window:
                avg_volume = sum(self._volume_window) / len(self._volume_window)
                recent_volume = sum(self._volume_window[-10:]) / min(10, len(self._volume_window))
                
                # Score based on recent vs average volume
                if avg_volume > 0:
                    volume_ratio = recent_volume / avg_volume
                    score = 50.0 + ((volume_ratio - 1.0) * 25.0)  # Scale around 50
                    return max(0.0, min(100.0, score))
        
        return 50.0  # Neutral if no data
    
    def calculate_signal(self, market_data: Dict[str, Any]) -> float:
        """Legacy method - calculate volume from batch data."""
        volume_24h = market_data.get("volume_24h", 0.0)
        trades_count = market_data.get("trades_count", 0)
        
        if volume_24h > 0:
            import math
            volume_score = min(100.0, max(0.0, 30.0 + math.log10(volume_24h + 1) * 8.0))
            return volume_score
        
        return 0.0


class VolatilityEngine(StreamingSignalEngine):
    """Streaming volatility signal engine."""
    
    def __init__(self, market_id: str = "BTC-USD"):
        """Initialize streaming volatility engine for a specific market."""
        super().__init__(signal_type=SignalType.VOLATILITY, market_id=market_id)
        
    def _calculate_streaming_signal(self, market_data: Dict[str, Any]) -> float:
        """Calculate volatility signal from streaming orderbook and trade data."""
        bid_price = market_data.get("bid_price", 0.0)
        ask_price = market_data.get("ask_price", 0.0)
        latest_price = market_data.get("latest_price", 0.0)
        
        # Use mid price if available, otherwise latest trade price
        mid_price = (bid_price + ask_price) / 2.0 if (bid_price > 0 and ask_price > 0) else latest_price
        
        if mid_price > 0 and bid_price > 0 and ask_price > 0:
            # Calculate bid-ask spread as percentage
            spread_percent = ((ask_price - bid_price) / mid_price) * 100
            
            # Higher spread = higher volatility score
            score = min(100.0, spread_percent * 1000)  # Scale spread to 0-100
            return max(0.0, score)
        
        return 50.0  # Neutral if no data
    
    def calculate_signal(self, market_data: Dict[str, Any]) -> float:
        """Legacy method - calculate volatility from batch data."""
        volatility = market_data.get("volatility", 0.0)
        bid_price = market_data.get("bid_price", 0.0)
        ask_price = market_data.get("ask_price", 0.0)
        current_price = market_data.get("price", 0.0)
        
        if current_price > 0 and bid_price > 0 and ask_price > 0:
            spread_percent = ((ask_price - bid_price) / current_price) * 100
            volatility_score = (volatility * 1000) + (spread_percent * 20)
            score = min(100.0, max(0.0, volatility_score * 100))
            return score
        
        return 0.0


class OrderbookEngine(StreamingSignalEngine):
    """Streaming orderbook signal engine."""
    
    def __init__(self, market_id: str = "BTC-USD"):
        """Initialize streaming orderbook engine for a specific market."""
        super().__init__(signal_type=SignalType.ORDERBOOK, market_id=market_id)
        
    def _calculate_streaming_signal(self, market_data: Dict[str, Any]) -> float:
        """Calculate orderbook signal from streaming orderbook data."""
        bid_size = market_data.get("bid_size", 0.0)
        ask_size = market_data.get("ask_size", 0.0)
        
        # Calculate order book imbalance
        total_size = bid_size + ask_size
        if total_size > 0:
            bid_ratio = bid_size / total_size
            score = bid_ratio * 100.0
            return max(0.0, min(100.0, score))
        
        return 50.0  # Neutral if no data
    
    def calculate_signal(self, market_data: Dict[str, Any]) -> float:
        """Legacy method - calculate orderbook from batch data."""
        bid_size = market_data.get("bid_size", 0.0)
        ask_size = market_data.get("ask_size", 0.0)
        
        total_size = bid_size + ask_size
        if total_size > 0:
            bid_ratio = bid_size / total_size
            score = bid_ratio * 100.0
            return max(0.0, min(100.0, score))
        
        return 50.0
