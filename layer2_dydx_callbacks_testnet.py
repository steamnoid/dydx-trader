"""
Layer 2 dYdX Trades Stream - Callback-Based Real WebSocket API Integration
Following TDD methodology - implementing DydxTradesStreamCallbacks class step by step
"""
import asyncio
import json
import threading
import time
from typing import Optional, Callable, Dict, Set
from dydx_v4_client.indexer.socket.websocket import IndexerSocket
from dydx_v4_client.network import make_mainnet

# Global configuration for orderbook depth optimization
ORDERBOOK_DEPTH = 100  # Number of price levels to maintain per side (bids/asks)


class DydxTradesStreamCallbacks:
    """Manages dYdX WebSocket connection for trades data with callback-based interface"""
    
    def __init__(self, websocket_url: str = "wss://indexer.v4testnet.dydx.exchange/v4/ws"):
        """Initialize the dYdX trades stream with callback support
        
        Args:
            websocket_url: WebSocket URL to connect to. 
                          Default: "wss://indexer.v4testnet.dydx.exchange/v4/ws" (testnet)
                          Mainnet: "wss://indexer.dydx.trade/v4/ws"
        """
        self._websocket: Optional[IndexerSocket] = None
        self._connection_id: Optional[str] = None
        self._is_connected = False
        self._trades_callbacks: Dict[str, Callable] = {}  # Dict of market_id -> callback
        self._initial_trade_counts: Dict[str, int] = {}  # Dict of market_id -> count
        self._subscribed_markets: Set[str] = set()  # Track subscribed markets
        self._unified_trades_callback: Optional[Callable] = None  # Single callback for all markets
        self.last_error: Optional[str] = None  # Store the last connection error
        self._websocket_url = websocket_url  # Store the WebSocket URL
        
        # Orderbook stream support
        self._orderbook_callbacks: Dict[str, Callable] = {}  # Dict of market_id -> callback
        self._current_orderbooks: Dict[str, dict] = {}  # Dict of market_id -> orderbook state
    
    def connect(self) -> bool:
        """Connect to dYdX WebSocket API"""
        try:
            # Create IndexerSocket with message handler (using configured WebSocket URL)
            self._websocket = IndexerSocket(
                self._websocket_url,  # Use the configured WebSocket URL
                on_message=self._handle_websocket_message
            )
            
            # Start WebSocket connection in separate thread (based on dYdX example)
            connection_error = None
            
            def _run_websocket():
                try:
                    asyncio.run(self._websocket.connect())
                except Exception as e:
                    nonlocal connection_error
                    connection_error = str(e)
            
            thread = threading.Thread(target=_run_websocket, daemon=True)
            thread.start()
            
            # Wait for connection to establish with timeout
            timeout = 10
            start_time = time.time()
            while not self._is_connected and time.time() - start_time < timeout:
                time.sleep(0.1)
                
                # Check if thread encountered an error
                if connection_error:
                    self.last_error = f"WebSocket connection error: {connection_error}"
                    return False
            
            if not self._is_connected:
                if connection_error:
                    self.last_error = f"WebSocket connection error: {connection_error}"
                else:
                    self.last_error = f"Connection timeout after {timeout} seconds"
            
            return self._is_connected
            
        except Exception as e:
            self._is_connected = False
            self.last_error = str(e)  # Store the actual error message
            return False
    
    def _handle_websocket_message(self, ws: IndexerSocket, message):
        """Handle WebSocket messages from dYdX"""
        # Parse message if it's a string
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except json.JSONDecodeError:
                return

        if message.get("type") == "connected":
            self._connection_id = message.get("connection_id")
            self._is_connected = True
            
        elif message.get("channel") == "v4_trades" and message.get("type") == "subscribed":
            # Trades subscription confirmed - may contain initial trade data
            market_id = message.get("id", "unknown")
            # Check if subscription confirmation contains trade data
            if message.get("contents"):
                trades_data = message.get("contents", {})
                if "trades" in trades_data:
                    trade_count = len(trades_data['trades'])
                    self._initial_trade_counts[market_id] = trade_count
                    for trade in trades_data["trades"]:
                        enriched_trade = self._add_metadata_to_trade(trade, is_initial=True, market_id=market_id)
                        
                        # Call individual market callback if present
                        # if market_id in self._trades_callbacks:
                            # self._trades_callbacks[market_id](enriched_trade)
                        
                        # Also call unified callback if present
                        # if self._unified_trades_callback:
                            # self._unified_trades_callback(enriched_trade)
                            
        elif message.get("channel") == "v4_trades" and message.get("contents"):
            # Emit trade data to callbacks
            market_id = message.get("id", "unknown")
            trades_data = message.get("contents", {})
            if "trades" in trades_data:
                for trade in trades_data["trades"]:
                    enriched_trade = self._add_metadata_to_trade(trade, is_initial=False, market_id=market_id)
                    
                    # Call individual market callback if present
                    if market_id in self._trades_callbacks:
                        self._trades_callbacks[market_id](enriched_trade)
                    
                    # Also call unified callback if present
                    if self._unified_trades_callback:
                        self._unified_trades_callback(enriched_trade)
                        
        elif message.get("channel") == "v4_orderbook":
            market_id = message.get("id", "unknown")
            
            if message.get("type") == "subscribed":
                # Orderbook subscription confirmed - contains initial orderbook snapshot
                if message.get("contents"):
                    orderbook_data = message.get("contents", {})
                    # Replace current orderbook with initial snapshot for this market (respecting depth limit)
                    asks = orderbook_data.get("asks", [])
                    bids = orderbook_data.get("bids", [])
                    
                    # Limit initial snapshot to configured depth
                    if len(asks) > ORDERBOOK_DEPTH:
                        asks = asks[:ORDERBOOK_DEPTH]
                    if len(bids) > ORDERBOOK_DEPTH:
                        bids = bids[:ORDERBOOK_DEPTH]
                    
                    self._current_orderbooks[market_id] = {
                        "asks": asks,
                        "bids": bids
                    }
                    # Call callback if present for this market
                    if market_id in self._orderbook_callbacks:
                        self._orderbook_callbacks[market_id](self._current_orderbooks[market_id].copy())
                        
            elif message.get("contents"):
                # Orderbook update - apply incremental changes
                orderbook_data = message.get("contents", {})
                
                try:
                    self._apply_orderbook_update(orderbook_data, market_id)
                    
                    # Call callback with COMPLETE updated orderbook for this market
                    if market_id in self._orderbook_callbacks:
                        complete_orderbook = self._current_orderbooks[market_id].copy()
                        self._orderbook_callbacks[market_id](complete_orderbook)
                except Exception as e:
                    print(f"❌ Error applying orderbook update for {market_id}: {e}")
                    # In case of error, call callback with raw update data to see what's happening
                    if market_id in self._orderbook_callbacks:
                        self._orderbook_callbacks[market_id](orderbook_data)
    
    def subscribe_to_trades(self, market_id: str, callback: Callable):
        """Subscribe to trades for a specific market with callback"""
        if not self._is_connected:
            raise RuntimeError("Must connect before subscribing to trades")
        
        # Store callback
        self._trades_callbacks[market_id] = callback
        
        # Subscribe to market if not already subscribed
        if market_id not in self._subscribed_markets:
            subscription_message = {
                "type": "subscribe",
                "channel": "v4_trades",
                "id": market_id
            }
            self._websocket.send(json.dumps(subscription_message))
            self._subscribed_markets.add(market_id)
    
    def subscribe_to_all_trades(self, callback: Callable):
        """Subscribe to all trades with unified callback"""
        if not self._is_connected:
            raise RuntimeError("Must connect before subscribing to trades")
        
        # Store unified callback
        self._unified_trades_callback = callback
    
    def subscribe_to_orderbook(self, market_id: str, callback: Callable):
        """Subscribe to orderbook for a specific market with callback"""
        if not self._is_connected:
            raise RuntimeError("Must connect before subscribing to orderbook")
        
        # Store callback
        self._orderbook_callbacks[market_id] = callback
        
        # Subscribe to orderbook
        subscription_message = {
            "type": "subscribe",
            "channel": "v4_orderbook",
            "id": market_id
        }
        self._websocket.send(json.dumps(subscription_message))
    
    def _apply_orderbook_update(self, update_data: dict, market_id: str):
        """Apply incremental orderbook updates to current state for specific market with depth optimization"""
        # Ensure we have an orderbook for this market
        if market_id not in self._current_orderbooks:
            self._current_orderbooks[market_id] = {"asks": [], "bids": []}
        
        current_orderbook = self._current_orderbooks[market_id]
        
        # Update asks with depth optimization
        if "asks" in update_data:
            for ask_update in update_data["asks"]:
                # Handle both list format [["price", "size"]] and dict format {"price": "...", "size": "..."}
                if isinstance(ask_update, list):
                    price = ask_update[0]
                    size = ask_update[1]
                    ask_entry = {"price": price, "size": size}
                else:
                    price = ask_update["price"]
                    size = ask_update["size"]
                    ask_entry = ask_update
                
                price_float = float(price)
                
                # OPTIMIZATION: Early filtering - skip updates for prices beyond our maintained depth
                if len(current_orderbook["asks"]) >= ORDERBOOK_DEPTH:
                    # If we already have max depth, check if this price would be relevant
                    worst_ask_price = float(current_orderbook["asks"][-1]["price"])  # Highest ask price
                    if price_float > worst_ask_price and float(size) > 0:
                        # This is a worse (higher) ask price than our worst maintained price, skip it
                        continue
                
                # Remove existing entry at this price (if any)
                current_orderbook["asks"] = [
                    ask for ask in current_orderbook["asks"] 
                    if ask["price"] != price
                ]
                
                # Add new entry if size > 0
                if float(size) > 0:
                    current_orderbook["asks"].append(ask_entry)
                    # Keep asks sorted by price (ascending) and limit depth
                    current_orderbook["asks"].sort(key=lambda x: float(x["price"]))
                    if len(current_orderbook["asks"]) > ORDERBOOK_DEPTH:
                        current_orderbook["asks"] = current_orderbook["asks"][:ORDERBOOK_DEPTH]
        
        # Update bids with depth optimization
        if "bids" in update_data:
            for bid_update in update_data["bids"]:
                # Handle both list format [["price", "size"]] and dict format {"price": "...", "size": "..."}
                if isinstance(bid_update, list):
                    price = bid_update[0]
                    size = bid_update[1]
                    bid_entry = {"price": price, "size": size}
                else:
                    price = bid_update["price"]
                    size = bid_update["size"]
                    bid_entry = bid_update
                
                price_float = float(price)
                
                # OPTIMIZATION: Early filtering - skip updates for prices beyond our maintained depth
                if len(current_orderbook["bids"]) >= ORDERBOOK_DEPTH:
                    # If we already have max depth, check if this price would be relevant
                    worst_bid_price = float(current_orderbook["bids"][-1]["price"])  # Lowest bid price
                    if price_float < worst_bid_price and float(size) > 0:
                        # This is a worse (lower) bid price than our worst maintained price, skip it
                        continue
                
                # Remove existing entry at this price (if any)
                current_orderbook["bids"] = [
                    bid for bid in current_orderbook["bids"] 
                    if bid["price"] != price
                ]
                
                # Add new entry if size > 0
                if float(size) > 0:
                    current_orderbook["bids"].append(bid_entry)
                    # Keep bids sorted by price (descending) and limit depth
                    current_orderbook["bids"].sort(key=lambda x: float(x["price"]), reverse=True)
                    if len(current_orderbook["bids"]) > ORDERBOOK_DEPTH:
                        current_orderbook["bids"] = current_orderbook["bids"][:ORDERBOOK_DEPTH]
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self._is_connected
    
    def get_connection_id(self) -> Optional[str]:
        """Get WebSocket connection ID"""
        return self._connection_id
    
    def get_initial_trade_count(self, market_id: str = "BTC-USD") -> int:
        """Get initial trade count for market"""
        return self._initial_trade_counts.get(market_id, 0)
    
    def get_subscribed_markets(self) -> Set[str]:
        """Get set of subscribed markets"""
        return self._subscribed_markets.copy()
    
    def get_last_error(self) -> Optional[str]:
        """Get the last connection error message"""
        return self.last_error

    def unsubscribe_from_trades(self, market_id: str):
        """Unsubscribe from trades for a specific market and clean up state"""
        if not self._is_connected:
            return
        
        # Send unsubscribe message
        unsubscribe_message = {
            "type": "unsubscribe",
            "channel": "v4_trades", 
            "id": market_id
        }
        try:
            self._websocket.send(json.dumps(unsubscribe_message))
        except Exception:
            pass  # Ignore send errors during cleanup
        
        # Clean up state
        self._trades_callbacks.pop(market_id, None)
        self._initial_trade_counts.pop(market_id, None)
        self._subscribed_markets.discard(market_id)
    
    def unsubscribe_from_orderbook(self, market_id: str):
        """Unsubscribe from orderbook for a specific market and clean up state"""
        if not self._is_connected:
            return
        
        # Send unsubscribe message
        unsubscribe_message = {
            "type": "unsubscribe",
            "channel": "v4_orderbook",
            "id": market_id
        }
        try:
            self._websocket.send(json.dumps(unsubscribe_message))
        except Exception:
            pass  # Ignore send errors during cleanup
        
        # Clean up state
        self._orderbook_callbacks.pop(market_id, None)
        self._current_orderbooks.pop(market_id, None)
    
    def cleanup_inactive_markets(self, active_markets: Set[str]):
        """Clean up state for markets that are no longer active"""
        # Find markets to clean up
        subscribed_markets = self._subscribed_markets.copy()
        markets_to_cleanup = subscribed_markets - active_markets
        
        for market_id in markets_to_cleanup:
            self.unsubscribe_from_trades(market_id)
            self.unsubscribe_from_orderbook(market_id)
    
    def reset_connection_state(self):
        """Reset all connection state - useful for reconnection scenarios"""
        self._is_connected = False
        self._connection_id = None
        self._trades_callbacks.clear()
        self._initial_trade_counts.clear()
        self._subscribed_markets.clear()
        self._orderbook_callbacks.clear()
        self._current_orderbooks.clear()
        self._unified_trades_callback = None
    
    def get_state_debug_info(self) -> Dict:
        """Get debug information about current state sizes"""
        return {
            'is_connected': self._is_connected,
            'subscribed_markets_count': len(self._subscribed_markets),
            'trades_callbacks_count': len(self._trades_callbacks),
            'orderbook_callbacks_count': len(self._orderbook_callbacks),
            'current_orderbooks_count': len(self._current_orderbooks),
            'initial_trade_counts_count': len(self._initial_trade_counts),
            'has_unified_trades_callback': self._unified_trades_callback is not None,
            'subscribed_markets': list(self._subscribed_markets)
        }
    
    def _add_metadata_to_trade(self, trade: dict, is_initial: bool = False, market_id: str = "unknown") -> dict:
        """Add metadata to trade data"""
        enriched_trade = trade.copy()
        enriched_trade["is_initial"] = is_initial
        enriched_trade["market_id"] = market_id
        enriched_trade["received_at"] = time.time()
        return enriched_trade
