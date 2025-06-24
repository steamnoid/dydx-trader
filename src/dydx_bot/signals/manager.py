"""
Signal Manager - Streaming architecture with single engine instances.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict
from src.dydx_bot.signals.engine import (
    MomentumEngine,
    VolumeEngine, 
    VolatilityEngine,
    OrderbookEngine
)
from src.dydx_bot.signals.types import SignalSet
from ..connection.manager import get_connection_manager


class StreamingSignalManager:
    """
    Streaming Signal Manager using single engine instances for all markets.
    Uses market_id as routing metadata, not processing state.
    """
    
    def __init__(self):
        """Initialize with single engine instances for ALL markets."""
        # SINGLE INSTANCES: 4 engines total, not 1040+
        self.momentum_engine = MomentumEngine()
        self.volume_engine = VolumeEngine()
        self.volatility_engine = VolatilityEngine()
        self.orderbook_engine = OrderbookEngine()
        
        # Signal cache indexed by market_id (metadata routing)
        self.signal_cache: Dict[str, SignalSet] = {}
        
        # Performance tracking
        self.last_update_times: Dict[str, float] = defaultdict(float)
        self.update_count = 0
        
        # Streaming state
        self._streaming = False
        self._connection_manager = None
    
    async def start_streaming(self):
        """Start streaming signal processing using shared WebSocket connection."""
        if self._streaming:
            return  # Already streaming
            
        # Connect to shared WebSocket connection
        self._connection_manager = get_connection_manager()
        
        # Register for market data messages
        self._connection_manager.register_message_handler(self._on_market_data)
        
        self._streaming = True
        print("🚀 StreamingSignalManager: Started streaming signal processing")
    
    async def stop_streaming(self):
        """Stop streaming signal processing."""
        if not self._streaming:
            return
            
        if self._connection_manager:
            self._connection_manager.unregister_message_handler(self._on_market_data)
            
        self._streaming = False
        print("🛑 StreamingSignalManager: Stopped streaming signal processing")
    
    def _on_market_data(self, ws, message: Dict[str, Any]):
        """
        Handle streaming market data and update signals in real-time.
        Uses single engines with market_id as routing metadata.
        """
        try:
            # Extract market_id from message (routing metadata)
            market_id = self._extract_market_id(message)
            if not market_id:
                return  # Skip if no market_id
            
            # Convert WebSocket message to market data format
            market_data = self._normalize_market_data(message, market_id)
            
            # Use SINGLE ENGINES with market_id as metadata parameter
            start_time = time.time()
            
            momentum_score = self.momentum_engine.calculate_signal(market_data, market_id)
            volume_score = self.volume_engine.calculate_signal(market_data, market_id)
            volatility_score = self.volatility_engine.calculate_signal(market_data, market_id)
            orderbook_score = self.orderbook_engine.calculate_signal(market_data, market_id)
            
            # Cache signals by market_id (metadata routing)
            self.signal_cache[market_id] = SignalSet(
                market=market_id,
                momentum=momentum_score,
                volume=volume_score,
                volatility=volatility_score,
                orderbook=orderbook_score,
                timestamp=datetime.now(),
                metadata={"processing_time_ms": (time.time() - start_time) * 1000}
            )
            
            # Track update performance
            self.last_update_times[market_id] = time.time()
            self.update_count += 1
            
        except Exception as e:
            # Silent error handling for streaming
            pass
    
    def _extract_market_id(self, message: Dict[str, Any]) -> Optional[str]:
        """Extract market_id from WebSocket message for routing."""
        # Handle different message formats
        if 'id' in message:
            return message['id']
        elif 'contents' in message and 'markets' in message['contents']:
            # Market list message - skip for now
            return None
        elif 'market' in message:
            return message['market']
        return None
    
    def _normalize_market_data(self, message: Dict[str, Any], market_id: str) -> Dict[str, Any]:
        """Convert WebSocket message to standardized market data format."""
        # Basic normalization - expand based on actual message formats
        return {
            "market_id": market_id,
            "price": message.get("price", 0.0),
            "price_change_24h": message.get("priceChange24H", 0.0),
            "volume_24h": message.get("volume24H", 0.0),
            "trades_count": message.get("trades24H", 0),
            "volatility": message.get("volatility", 0.0),
            "bid_price": message.get("bidPrice", 0.0),
            "ask_price": message.get("askPrice", 0.0),
            "bid_size": message.get("bidSize", 0.0),
            "ask_size": message.get("askSize", 0.0),
            "timestamp": time.time()
        }
    
    def get_latest_signals(self, market_id: str) -> Optional[SignalSet]:
        """Get cached signals for a market (no calculation needed - already streaming)."""
        return self.signal_cache.get(market_id)
    
    def get_all_cached_signals(self) -> Dict[str, SignalSet]:
        """Get all cached signals from streaming updates."""
        return self.signal_cache.copy()
    
    def calculate_signals(self, market: str, market_data: Dict[str, Any]) -> SignalSet:
        """
        Legacy method: Calculate signals on-demand using single engines.
        Used for backwards compatibility and non-streaming scenarios.
        """
        # Use SINGLE ENGINES with market as metadata parameter
        momentum_score = self.momentum_engine.calculate_signal(market_data, market)
        volume_score = self.volume_engine.calculate_signal(market_data, market)
        volatility_score = self.volatility_engine.calculate_signal(market_data, market)
        orderbook_score = self.orderbook_engine.calculate_signal(market_data, market)
        
        # Create and return SignalSet
        return SignalSet(
            market=market,
            momentum=momentum_score,
            volume=volume_score,
            volatility=volatility_score,
            orderbook=orderbook_score,
            timestamp=datetime.now(),
            metadata={"method": "on_demand"}
        )
