"""
Layer 2 dYdX Trades Stream - Real WebSocket API Integration with Recording Capability
Following TDD methodology - implementing DydxTradesStream class step by step
"""
import asyncio
import json
import threading
from typing import Optional
from dydx_v4_client.indexer.socket.websocket import IndexerSocket
from dydx_v4_client.network import make_mainnet


class DydxTradesStream:
    """Manages dYdX WebSocket connection for trades data with recording capability"""
    
    def __init__(self):
        """Initialize the dYdX trades stream"""
        self._websocket: Optional[IndexerSocket] = None
        self._connection_id: Optional[str] = None
        self._is_connected = False
        self._trades_observers = {}  # Dict of market_id -> observer
        self._initial_trade_counts = {}  # Dict of market_id -> count
        self._subscribed_markets = set()  # Track subscribed markets
        self._unified_trades_observer = None  # Single observer for all markets
        
        # Orderbook stream support
        self._orderbook_observer = None  # Single observer for BTC orderbook
        self._current_orderbook = {"asks": [], "bids": []}  # Current orderbook state
    
    def connect(self):
        """Connect to dYdX WebSocket API"""
        try:
            # Create IndexerSocket with message handler (using mainnet for active trade data)
            self._websocket = IndexerSocket(
                "wss://indexer.dydx.trade/v4/ws",  # dYdX mainnet WebSocket
                on_message=self._handle_websocket_message
            )
            
            # Start WebSocket connection in separate thread (based on dYdX example)
            def _run_websocket():
                asyncio.run(self._websocket.connect())
            
            thread = threading.Thread(target=_run_websocket, daemon=True)
            thread.start()
            
            # Wait for connection to establish with timeout
            import time
            max_wait = 5  # 5 second timeout
            wait_time = 0
            while wait_time < max_wait and self._connection_id is None:
                time.sleep(0.1)
                wait_time += 0.1
            
            if self._connection_id is not None:
                self._is_connected = True
                return True
            else:
                self._is_connected = False
                return False
        except Exception:
            self._is_connected = False
            return False
    
    def _handle_websocket_message(self, ws: IndexerSocket, message):
        """Handle WebSocket messages from dYdX"""
        # Parse message if it's a string
        if isinstance(message, str):
            import json
            try:
                message = json.loads(message)
            except json.JSONDecodeError:
                return

        if message.get("type") == "connected":
            self._connection_id = message.get("connection_id")
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
                        
                        # Emit to individual market observer if present
                        if market_id in self._trades_observers:
                            self._trades_observers[market_id].on_next(enriched_trade)
                        
                        # Also emit to unified observer if present
                        if self._unified_trades_observer:
                            self._unified_trades_observer.on_next(enriched_trade)
        elif message.get("channel") == "v4_trades" and message.get("contents"):
            # Emit trade data to observer
            market_id = message.get("id", "unknown")
            trades_data = message.get("contents", {})
            if "trades" in trades_data:
                for trade in trades_data["trades"]:
                    enriched_trade = self._add_metadata_to_trade(trade, is_initial=False, market_id=market_id)
                    
                    # Emit to individual market observer if present
                    if market_id in self._trades_observers:
                        self._trades_observers[market_id].on_next(enriched_trade)
                    
                    # Also emit to unified observer if present
                    if self._unified_trades_observer:
                        self._unified_trades_observer.on_next(enriched_trade)
        elif message.get("channel") == "v4_orderbook":
            if message.get("type") == "subscribed":
                # Orderbook subscription confirmed - contains initial orderbook snapshot
                if message.get("contents"):
                    orderbook_data = message.get("contents", {})
                    # Replace current orderbook with initial snapshot
                    self._current_orderbook = {
                        "asks": orderbook_data.get("asks", []),
                        "bids": orderbook_data.get("bids", [])
                    }
                    # Emit to observer if present
                    if self._orderbook_observer:
                        self._orderbook_observer.on_next(self._current_orderbook.copy())
            elif message.get("contents"):
                # Orderbook update - apply incremental changes
                orderbook_data = message.get("contents", {})
                
                try:
                    self._apply_orderbook_update(orderbook_data)
                    
                    # Emit COMPLETE updated orderbook to observer
                    if self._orderbook_observer:
                        complete_orderbook = self._current_orderbook.copy()
                        self._orderbook_observer.on_next(complete_orderbook)
                except Exception as e:
                    print(f"❌ Error applying orderbook update: {e}")
                    import traceback
                    traceback.print_exc()
                    # In case of error, emit the raw update data to see what's happening
                    if self._orderbook_observer:
                        self._orderbook_observer.on_next(orderbook_data)
    
    def get_trades_observable(self, market_id: str = "BTC-USD"):
        """Get RxPY Observable stream of trades data for a specific market"""
        import reactivex as rx
        
        def create_trades_stream(observer, scheduler):
            """Create trades stream by subscribing to WebSocket trades channel"""
            try:
                if self._is_connected and self._websocket:
                    # Store observer for message handling
                    self._trades_observers[market_id] = observer
                    self._subscribed_markets.add(market_id)
                    
                    # Subscribe to trades channel for the specified market
                    subscription_message = {
                        "type": "subscribe",
                        "channel": "v4_trades",
                        "id": market_id
                    }
                    
                    # Send subscription message
                    import json
                    message_str = json.dumps(subscription_message)
                    self._websocket.send(message_str)
                    
                else:
                    observer.on_error(Exception("WebSocket not connected"))
            
            except Exception as e:
                observer.on_error(e)
            
            # Return disposable to unsubscribe
            def dispose():
                if self._websocket and market_id in self._subscribed_markets:
                    unsubscribe_message = {
                        "type": "unsubscribe", 
                        "channel": "v4_trades",
                        "id": market_id
                    }
                    try:
                        import json
                        message_str = json.dumps(unsubscribe_message)
                        self._websocket.send(message_str)
                    except:
                        pass
                    # Remove observer and market from tracking
                    if market_id in self._trades_observers:
                        del self._trades_observers[market_id]
                    self._subscribed_markets.discard(market_id)
            
            return dispose
        
        return rx.create(create_trades_stream)
    
    def get_all_trades_observable(self):
        """Get RxPY Observable stream of ALL trades data with market metadata for filtering
        
        This provides a single stream that emits trades from all subscribed markets.
        Use reactive operators to filter by market in higher layers:
        
        Example:
            all_trades = stream.get_all_trades_observable()
            btc_trades = all_trades.pipe(
                filter(lambda trade: trade["metadata"]["market_name"] == "BTC-USD")
            )
        """
        import reactivex as rx
        
        def create_all_trades_stream(observer, scheduler):
            """Create unified trades stream for all markets"""
            try:
                if self._is_connected and self._websocket:
                    # Store observer for ALL markets
                    self._unified_trades_observer = observer
                    
                    # Subscribe to all available markets
                    # For now, subscribe to major markets - can be made dynamic
                    major_markets = ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD", "AVAX-USD"]
                    
                    for market_id in major_markets:
                        subscription_message = {
                            "type": "subscribe",
                            "channel": "v4_trades", 
                            "id": market_id
                        }
                        message_str = json.dumps(subscription_message)
                        self._websocket.send(message_str)
                        self._subscribed_markets.add(market_id)
                    
                else:
                    observer.on_error(Exception("WebSocket not connected"))
            
            except Exception as e:
                observer.on_error(e)
            
            # Return disposable to unsubscribe from all markets
            def dispose():
                if self._websocket:
                    for market_id in list(self._subscribed_markets):
                        unsubscribe_message = {
                            "type": "unsubscribe",
                            "channel": "v4_trades", 
                            "id": market_id
                        }
                        try:
                            message_str = json.dumps(unsubscribe_message)
                            self._websocket.send(message_str)
                        except:
                            pass
                    
                    self._subscribed_markets.clear()
                    self._unified_trades_observer = None
            
            return dispose
        
        return rx.create(create_all_trades_stream)
    
    def get_orderbook_observable(self, market_id: str = "BTC-USD"):
        """Get RxPY Observable stream of orderbook data for BTC market"""
        import reactivex as rx
        
        def create_orderbook_stream(observer, scheduler):
            """Create orderbook stream by subscribing to WebSocket orderbook channel"""
            try:
                if self._is_connected and self._websocket:
                    # Store observer for message handling
                    self._orderbook_observer = observer
                    
                    # Subscribe to orderbook channel for BTC
                    subscription_message = {
                        "type": "subscribe",
                        "channel": "v4_orderbook",
                        "id": market_id
                    }
                    
                    # Send subscription message
                    import json
                    message_str = json.dumps(subscription_message)
                    self._websocket.send(message_str)
                    
                else:
                    observer.on_error(Exception("WebSocket not connected"))
            
            except Exception as e:
                observer.on_error(e)
            
            # Return disposable to unsubscribe
            def dispose():
                if self._websocket:
                    unsubscribe_message = {
                        "type": "unsubscribe", 
                        "channel": "v4_orderbook",
                        "id": market_id
                    }
                    try:
                        import json
                        message_str = json.dumps(unsubscribe_message)
                        self._websocket.send(message_str)
                    except:
                        pass
                    # Clear observer
                    self._orderbook_observer = None
            
            return dispose
        
        return rx.create(create_orderbook_stream)
    
    def _apply_orderbook_update(self, update_data: dict):
        """Apply incremental orderbook updates to current state"""
        # Update asks
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
                
                # Remove existing entry at this price
                self._current_orderbook["asks"] = [
                    ask for ask in self._current_orderbook["asks"] 
                    if ask["price"] != price
                ]
                
                # Add new entry if size > 0
                if float(size) > 0:
                    self._current_orderbook["asks"].append(ask_entry)
                    # Keep asks sorted by price (ascending)
                    self._current_orderbook["asks"].sort(key=lambda x: float(x["price"]))
        
        # Update bids
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
                
                # Remove existing entry at this price
                self._current_orderbook["bids"] = [
                    bid for bid in self._current_orderbook["bids"] 
                    if bid["price"] != price
                ]
                
                # Add new entry if size > 0
                if float(size) > 0:
                    self._current_orderbook["bids"].append(bid_entry)
                    # Keep bids sorted by price (descending)
                    self._current_orderbook["bids"].sort(key=lambda x: float(x["price"]), reverse=True)

    def is_connected(self):
        """Check if WebSocket connection is active"""
        return self._is_connected
    
    def get_connection_id(self):
        """Get the WebSocket connection ID from dYdX"""
        return self._connection_id
    
    def get_initial_trade_count(self, market_id: str = "BTC-USD"):
        """Get the number of trades received in the subscription confirmation for a specific market"""
        return self._initial_trade_counts.get(market_id, 0)
    
    def get_subscribed_markets(self):
        """Get the set of currently subscribed markets"""
        return self._subscribed_markets.copy()
    
    def _add_metadata_to_trade(self, trade: dict, is_initial: bool = False, market_id: str = "unknown") -> dict:
        """Add metadata to a trade message for tracking and performance monitoring."""
        import time
        
        # Create enriched trade with original data
        enriched_trade = trade.copy()
        
        # Add metadata
        metadata = {
            "market_name": market_id,  # Use provided market_id instead of ticker
            "ticker": trade.get("ticker", market_id),  # Keep original ticker as separate field
            "performance_metrics": {
                "timestamp_received": time.time(),  # When we received this trade
                "timestamp_processed": time.time(),  # When we processed this trade
                "is_initial_trade": is_initial,  # Whether this is from subscription confirmation
                "message_source": "subscription_confirmation" if is_initial else "real_time_update",
                "latency_ms": 0,  # Placeholder for latency calculation
            },
            "tracking_info": {
                "session_id": id(self),  # Unique session identifier
                "message_sequence": getattr(self, '_message_sequence', 0),  # Message sequence number
            }
        }
        
        # Increment message sequence counter
        if not hasattr(self, '_message_sequence'):
            self._message_sequence = 0
        self._message_sequence += 1
        metadata["tracking_info"]["message_sequence"] = self._message_sequence
        
        # Calculate latency if original timestamp is available
        if "createdAtHeight" in trade:
            try:
                # Estimate latency (simplified calculation)
                metadata["performance_metrics"]["latency_ms"] = round(
                    (time.time() - metadata["performance_metrics"]["timestamp_received"]) * 1000, 2
                )
            except:
                pass  # Keep default latency of 0
        
        # Add metadata to the trade
        enriched_trade["metadata"] = metadata
        
        return enriched_trade
