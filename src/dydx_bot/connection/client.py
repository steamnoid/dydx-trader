"""
Layer 2: dYdX v4 Client Integration

Protocol-first approach using official dydx-v4-client.
Includes WebSocket, async/await, threading patterns, and production throttling.
"""

import asyncio
import threading
import json
import time
from typing import Any, Dict, Optional, Callable
from collections import deque
from dataclasses import dataclass, field
from dydx_v4_client.indexer.rest.indexer_client import IndexerClient
from dydx_v4_client.node.client import NodeClient
from dydx_v4_client.indexer.socket.websocket import IndexerSocket
from dydx_v4_client.indexer.candles_resolution import CandlesResolution


@dataclass
class ThrottleConfig:
    """Production-grade throttling configuration for dYdX API limits"""
    # REST API limits (based on dYdX documentation)
    rest_requests_per_second: float = 10.0  # Conservative limit
    rest_burst_limit: int = 20  # Allow short bursts
    
    # WebSocket subscription limits
    ws_subscriptions_per_second: float = 5.0
    ws_max_concurrent_subscriptions: int = 50
    
    # Connection management
    reconnect_delay_seconds: float = 1.0
    max_reconnect_attempts: int = 5
    
    # Message processing
    max_message_queue_size: int = 1000
    message_processing_timeout_ms: int = 100


@dataclass
class ThrottleState:
    """Track throttling state for production stability"""
    rest_request_times: deque = field(default_factory=lambda: deque(maxlen=100))
    ws_subscription_times: deque = field(default_factory=lambda: deque(maxlen=50))
    last_rest_request: float = 0.0
    last_ws_subscription: float = 0.0
    active_subscriptions: int = 0
    reconnect_attempts: int = 0


class DydxClient:
    """
    Production-grade dYdX v4 client with throttling and rate limiting
    
    Protocol-first: Use official dydx-v4-client with production safeguards.
    Includes rate limiting, connection resilience, and autonomous operation.
    """
    
    def __init__(self, on_message: Optional[Callable] = None, throttle_config: Optional[ThrottleConfig] = None):
        self._indexer_client = None
        self._node_client = None  
        self._indexer_socket = None
        self._connected = False
        self._on_message = on_message or self._default_message_handler
        self._websocket_thread = None
        
        # Production throttling
        self._throttle_config = throttle_config or ThrottleConfig()
        self._throttle_state = ThrottleState()
        self._rest_semaphore = asyncio.Semaphore(self._throttle_config.rest_burst_limit)
        self._ws_semaphore = asyncio.Semaphore(self._throttle_config.ws_max_concurrent_subscriptions)
    
    async def connect(self):
        """Connect to dYdX v4 mainnet following official patterns"""
        try:
            # IndexerClient for REST API - takes host URL directly
            self._indexer_client = IndexerClient(
                host="https://indexer.dydx.trade"
            )
            
            # IndexerSocket for WebSocket with message handler
            self._indexer_socket = IndexerSocket(
                url="wss://indexer.dydx.trade/v4/ws",
                on_message=self.handle_websocket_message
            )
            
            self._connected = True
            
        except Exception as e:
            self._connected = False
            raise e
    
    async def disconnect(self):
        """Disconnect and cleanup resources"""
        if self._indexer_socket:
            self._indexer_socket.close()
        
        self._indexer_client = None
        self._indexer_socket = None
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected
    
    @property
    def indexer_client(self):
        """Get IndexerClient for REST operations"""
        return self._indexer_client
        
    @property 
    def indexer_socket(self):
        """Get IndexerSocket for WebSocket operations"""
        return self._indexer_socket
    
    def handle_websocket_message(self, ws: IndexerSocket, message: Dict[str, Any]):
        """
        Handle WebSocket messages following official patterns
        Based on websocket_example.py and test_websocket.py
        """
        if message.get("type") == "connected":
            # Auto-subscribe to basic channels on connection
            self._on_connected(ws)
        
        # Forward to custom message handler
        if self._on_message:
            self._on_message(ws, message)
    
    def _default_message_handler(self, ws: IndexerSocket, message: Dict[str, Any]):
        """Default message handler that prints messages"""
        print(f"WebSocket message: {message}")
    
    def _on_connected(self, ws: IndexerSocket):
        """Handle initial connection - can be overridden"""
        pass
    
    # Market Data Subscriptions following official patterns
    
    async def subscribe_to_markets(self):
        """Subscribe to markets channel (v4_markets) with throttling"""
        await self._throttle_ws_subscription()
        await self._ensure_connection_with_retry()
        
        if self._indexer_socket and hasattr(self._indexer_socket, 'markets'):
            self._indexer_socket.markets.subscribe()
            self._throttle_state.active_subscriptions += 1
    
    async def subscribe_to_orderbook(self, market_id: str, batched: bool = True):
        """Subscribe to orderbook channel (v4_orderbook) with throttling"""
        await self._throttle_ws_subscription()
        await self._ensure_connection_with_retry()
        
        if self._indexer_socket and hasattr(self._indexer_socket, 'order_book'):
            self._indexer_socket.order_book.subscribe(market_id, batched=batched)
            self._throttle_state.active_subscriptions += 1
    
    async def subscribe_to_trades(self, market_id: str, batched: bool = True):
        """Subscribe to trades channel (v4_trades) with throttling"""
        await self._throttle_ws_subscription()
        await self._ensure_connection_with_retry()
        
        if self._indexer_socket and hasattr(self._indexer_socket, 'trades'):
            self._indexer_socket.trades.subscribe(market_id, batched=batched)
            self._throttle_state.active_subscriptions += 1
    
    async def subscribe_to_candles(self, market_id: str, resolution: CandlesResolution, batched: bool = True):
        """Subscribe to candles channel (v4_candles) with throttling"""
        await self._throttle_ws_subscription()
        await self._ensure_connection_with_retry()
        
        if self._indexer_socket and hasattr(self._indexer_socket, 'candles'):
            self._indexer_socket.candles.subscribe(market_id, resolution, batched=batched)
            self._throttle_state.active_subscriptions += 1
    
    async def subscribe_to_subaccounts(self, address: str, subaccount_number: int):
        """Subscribe to subaccounts channel (v4_subaccounts) with throttling"""
        await self._throttle_ws_subscription()
        await self._ensure_connection_with_retry()
        
        if self._indexer_socket and hasattr(self._indexer_socket, 'subaccounts'):
            self._indexer_socket.subaccounts.subscribe(address, subaccount_number)
            self._throttle_state.active_subscriptions += 1
    
    # Threading patterns based on websoket_concurrency_example.py
    
    def start_websocket_in_thread(self):
        """
        Start WebSocket connection in a separate thread
        Based on websoket_concurrency_example.py threading pattern
        """
        def wrap_async_func():
            # NOTE: ._indexer_socket.connect() is a blocking async function call
            if self._indexer_socket:
                asyncio.run(self._indexer_socket.connect())
        
        self._websocket_thread = threading.Thread(target=wrap_async_func)
        self._websocket_thread.start()
        
        return self._websocket_thread
    
    # Unsubscribe methods following official patterns
    
    async def unsubscribe_from_markets(self):
        """Unsubscribe from markets channel"""
        if self._indexer_socket and hasattr(self._indexer_socket, 'markets'):
            self._indexer_socket.markets.unsubscribe()
    
    async def unsubscribe_from_orderbook(self, market_id: str):
        """Unsubscribe from orderbook channel"""
        if self._indexer_socket and hasattr(self._indexer_socket, 'order_book'):
            self._indexer_socket.order_book.unsubscribe(market_id)
    
    async def unsubscribe_from_trades(self, market_id: str):
        """Unsubscribe from trades channel"""
        if self._indexer_socket and hasattr(self._indexer_socket, 'trades'):
            self._indexer_socket.trades.unsubscribe(market_id)
    
    async def unsubscribe_from_candles(self, market_id: str, resolution: CandlesResolution):
        """Unsubscribe from candles channel"""
        if self._indexer_socket and hasattr(self._indexer_socket, 'candles'):
            self._indexer_socket.candles.unsubscribe(market_id, resolution)
    
    async def unsubscribe_from_subaccounts(self, address: str, subaccount_number: int):
        """Unsubscribe from subaccounts channel"""
        if self._indexer_socket and hasattr(self._indexer_socket, 'subaccounts'):
            self._indexer_socket.subaccounts.unsubscribe(address, subaccount_number)
    
    # Throttling methods for rate limiting and connection management
    
    async def _throttle_rest_request(self) -> None:
        """
        Throttle REST API requests to prevent hitting dYdX rate limits
        Critical for autonomous operation without human intervention
        """
        async with self._rest_semaphore:
            now = time.time()
            self._throttle_state.rest_request_times.append(now)
            
            # Calculate requests in the last second
            cutoff_time = now - 1.0
            recent_requests = [t for t in self._throttle_state.rest_request_times if t > cutoff_time]
            
            # If we're at the limit, wait
            if len(recent_requests) >= self._throttle_config.rest_requests_per_second:
                sleep_time = 1.0 / self._throttle_config.rest_requests_per_second
                await asyncio.sleep(sleep_time)
            
            self._throttle_state.last_rest_request = now
    
    async def _throttle_ws_subscription(self) -> None:
        """
        Throttle WebSocket subscriptions for stable operation
        Prevents overwhelming the WebSocket connection
        """
        async with self._ws_semaphore:
            now = time.time()
            self._throttle_state.ws_subscription_times.append(now)
            
            # Calculate subscriptions in the last second
            cutoff_time = now - 1.0
            recent_subs = [t for t in self._throttle_state.ws_subscription_times if t > cutoff_time]
            
            # If we're at the limit, wait
            if len(recent_subs) >= self._throttle_config.ws_subscriptions_per_second:
                sleep_time = 1.0 / self._throttle_config.ws_subscriptions_per_second
                await asyncio.sleep(sleep_time)
            
            self._throttle_state.last_ws_subscription = now
    
    async def _ensure_connection_with_retry(self) -> bool:
        """
        Ensure connection with exponential backoff retry
        Critical for autonomous 24/7 operation
        """
        if self._connected:
            return True
        
        for attempt in range(self._throttle_config.max_reconnect_attempts):
            try:
                await self.connect()
                self._throttle_state.reconnect_attempts = 0
                return True
                
            except Exception as e:
                self._throttle_state.reconnect_attempts += 1
                
                if attempt < self._throttle_config.max_reconnect_attempts - 1:
                    # Exponential backoff with jitter
                    delay = self._throttle_config.reconnect_delay_seconds * (2 ** attempt)
                    jitter = delay * 0.1 * (0.5 - asyncio.get_event_loop().time() % 1)
                    await asyncio.sleep(delay + jitter)
                else:
                    raise e
        
        return False
    
    # Throttling state accessors for dashboard and monitoring
    
    def get_throttle_metrics(self) -> Dict[str, Any]:
        """Get current throttling metrics for dashboard display"""
        now = time.time()
        
        # Calculate current rates
        rest_requests_last_second = len([
            t for t in self._throttle_state.rest_request_times 
            if t > now - 1.0
        ])
        
        ws_subs_last_second = len([
            t for t in self._throttle_state.ws_subscription_times 
            if t > now - 1.0
        ])
        
        return {
            "rest_api": {
                "requests_per_second_limit": self._throttle_config.rest_requests_per_second,
                "current_requests_per_second": rest_requests_last_second,
                "burst_limit": self._throttle_config.rest_burst_limit,
                "last_request_ago_ms": (now - self._throttle_state.last_rest_request) * 1000 if self._throttle_state.last_rest_request > 0 else None
            },
            "websocket": {
                "subscriptions_per_second_limit": self._throttle_config.ws_subscriptions_per_second,
                "current_subscriptions_per_second": ws_subs_last_second,
                "active_subscriptions": self._throttle_state.active_subscriptions,
                "max_concurrent_limit": self._throttle_config.ws_max_concurrent_subscriptions,
                "last_subscription_ago_ms": (now - self._throttle_state.last_ws_subscription) * 1000 if self._throttle_state.last_ws_subscription > 0 else None
            },
            "connection": {
                "reconnect_attempts": self._throttle_state.reconnect_attempts,
                "max_reconnect_attempts": self._throttle_config.max_reconnect_attempts,
                "reconnect_delay_seconds": self._throttle_config.reconnect_delay_seconds
            },
            "performance": {
                "message_queue_size_limit": self._throttle_config.max_message_queue_size,
                "message_timeout_ms": self._throttle_config.message_processing_timeout_ms
            }
        }
    
    async def throttled_rest_request(self, request_func, *args, **kwargs):
        """
        Execute a REST request with throttling
        Use this wrapper for all REST API calls in production
        """
        await self._throttle_rest_request()
        await self._ensure_connection_with_retry()
        
        if not self._indexer_client:
            raise Exception("REST client not connected")
        
        return await request_func(*args, **kwargs)
