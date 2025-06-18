"""
Connection Manager - Layer 2 Singleton

Ensures single WebSocket connection shared across all signal engines and markets.
Critical for preventing multiple WebSocket connections per market.
"""

import asyncio
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field

from .client import DydxClient


@dataclass
class ConnectionConfig:
    """Configuration for shared connection management"""
    auto_subscribe_markets: bool = True
    default_message_handler: Optional[Callable] = None
    max_concurrent_subscriptions: int = 50
    connection_timeout_seconds: int = 30


class ConnectionManager:
    """
    Singleton connection manager ensuring single WebSocket connection
    
    Critical Architecture Feature:
    - ONE WebSocket connection for ALL signal engines
    - ALL markets share the same connection  
    - Message routing to multiple handlers
    - Connection state management for autonomous operation
    """
    
    _instance: Optional['ConnectionManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern - ensure only one connection manager exists"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        # Prevent re-initialization of singleton
        if hasattr(self, '_initialized'):
            return
            
        self.config = config or ConnectionConfig()
        self.client: Optional[DydxClient] = None
        self._connected = False
        self._websocket_thread: Optional[threading.Thread] = None
        
        # Message handler registry for routing to multiple consumers
        self._message_handlers: List[Callable[[Any, Dict[str, Any]], None]] = []
        
        # Active subscriptions tracking (prevent duplicates)
        self._active_subscriptions: Dict[str, set] = {
            'markets': set(),
            'orderbook': set(),
            'trades': set(), 
            'candles': set(),
            'subaccounts': set()
        }
        
        # Connection state
        self._connection_lock = asyncio.Lock()
        self._initialized = True
    
    async def initialize(self) -> bool:
        """
        Initialize single shared connection
        
        Returns:
            bool: True if connection established successfully
        """
        async with self._connection_lock:
            if self._connected and self.client and self.client.is_connected():
                return True
            
            try:
                # Create single client with message routing
                self.client = DydxClient(on_message=self._route_message)
                await self.client.connect()
                
                if self.client.is_connected():
                    # Start WebSocket in thread for real-time data
                    self._websocket_thread = self.client.start_websocket_in_thread()
                    
                    # Wait for connection to stabilize
                    await asyncio.sleep(3)
                    
                    self._connected = True
                    print(f"🔌 Single WebSocket connection established for all markets")
                    return True
                    
            except Exception as e:
                print(f"❌ Connection manager failed to initialize: {e}")
                self._connected = False
                
        return False
    
    def register_message_handler(self, handler: Callable[[Any, Dict[str, Any]], None]):
        """
        Register a message handler to receive WebSocket messages
        
        Args:
            handler: Function that accepts (ws, message) parameters
        """
        if handler not in self._message_handlers:
            self._message_handlers.append(handler)
    
    def unregister_message_handler(self, handler: Callable[[Any, Dict[str, Any]], None]):
        """Remove a message handler from the registry"""
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)
    
    def _route_message(self, ws: Any, message: Dict[str, Any]):
        """
        Route WebSocket messages to all registered handlers
        
        Critical: This ensures all signal engines receive the same data
        from the single WebSocket connection
        """
        for handler in self._message_handlers:
            try:
                handler(ws, message)
            except Exception as e:
                # Silent error handling to prevent one handler from breaking others
                pass
    
    async def subscribe_to_market_data(self, market_id: str, data_types: List[str] = None) -> bool:
        """
        Subscribe to market data for a specific market
        
        Args:
            market_id: Market to subscribe to (e.g., "BTC-USD")
            data_types: List of data types ["orderbook", "trades", "candles"]
        
        Returns:
            bool: True if subscriptions successful
        """
        if not self._connected or not self.client:
            return False
        
        if data_types is None:
            data_types = ["orderbook", "trades"]  # Default subscription set
        
        try:
            # Subscribe to orderbook if requested and not already subscribed
            if "orderbook" in data_types and market_id not in self._active_subscriptions['orderbook']:
                await self.client.subscribe_to_orderbook(market_id)
                self._active_subscriptions['orderbook'].add(market_id)
            
            # Subscribe to trades if requested and not already subscribed  
            if "trades" in data_types and market_id not in self._active_subscriptions['trades']:
                await self.client.subscribe_to_trades(market_id)
                self._active_subscriptions['trades'].add(market_id)
            
            # Subscribe to candles if requested and not already subscribed
            if "candles" in data_types and market_id not in self._active_subscriptions['candles']:
                from dydx_v4_client.indexer.candles_resolution import CandlesResolution
                await self.client.subscribe_to_candles(market_id, CandlesResolution.ONE_MINUTE)
                self._active_subscriptions['candles'].add(market_id)
            
            print(f"📊 Subscribed to {market_id} data: {data_types} (shared connection)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to subscribe to {market_id}: {e}")
            return False
    
    async def subscribe_to_markets(self) -> bool:
        """Subscribe to general markets data (if not already subscribed)"""
        if not self._connected or not self.client:
            return False
        
        if 'general' not in self._active_subscriptions['markets']:
            try:
                await self.client.subscribe_to_markets()
                self._active_subscriptions['markets'].add('general')
                return True
            except Exception as e:
                print(f"❌ Failed to subscribe to markets: {e}")
                return False
        
        return True  # Already subscribed
    
    def is_connected(self) -> bool:
        """Check if the shared connection is active"""
        return self._connected and self.client and self.client.is_connected()
    
    def get_client(self) -> Optional[DydxClient]:
        """Get the shared client instance"""
        return self.client
    
    def get_connection_metrics(self) -> Dict[str, Any]:
        """Get connection metrics and subscription status"""
        if not self.client:
            return {"connected": False, "subscriptions": {}}
        
        return {
            "connected": self.is_connected(),
            "active_subscriptions": {
                "markets": len(self._active_subscriptions['markets']),
                "orderbook": list(self._active_subscriptions['orderbook']),
                "trades": list(self._active_subscriptions['trades']),
                "candles": list(self._active_subscriptions['candles']),
                "subaccounts": len(self._active_subscriptions['subaccounts'])
            },
            "registered_handlers": len(self._message_handlers),
            "thread_active": self._websocket_thread and self._websocket_thread.is_alive() if self._websocket_thread else False,
            "throttle_metrics": self.client.get_throttle_metrics() if self.client else {}
        }
    
    async def disconnect(self):
        """Disconnect the shared connection"""
        async with self._connection_lock:
            if self.client:
                await self.client.disconnect()
            
            self._connected = False
            self._active_subscriptions = {
                'markets': set(),
                'orderbook': set(), 
                'trades': set(),
                'candles': set(),
                'subaccounts': set()
            }
            self._message_handlers.clear()
            print("🔌 Shared connection disconnected")


# Global singleton instance
connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """
    Get the global singleton connection manager
    
    Returns:
        ConnectionManager: The shared connection manager instance
    """
    return connection_manager
