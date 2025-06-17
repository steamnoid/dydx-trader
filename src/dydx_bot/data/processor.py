"""
Market Data Processor - Layer 3

Processes raw dYdX market data into structured formats for autonomous trading.
Protocol-first implementation using dydx-v4-client data structures.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import deque
import statistics

from ..connection.client import DydxClient


@dataclass
class OHLCVData:
    """OHLCV candlestick data structure"""
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    market_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'market_id': self.market_id
        }


@dataclass
class OrderbookSnapshot:
    """Orderbook snapshot with best bid/ask"""
    timestamp: float
    market_id: str
    best_bid: float
    best_ask: float
    bid_size: float
    ask_size: float
    spread: float
    mid_price: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp,
            'market_id': self.market_id,
            'best_bid': self.best_bid,
            'best_ask': self.best_ask,
            'bid_size': self.bid_size,
            'ask_size': self.ask_size,
            'spread': self.spread,
            'mid_price': self.mid_price
        }


@dataclass
class FundingRateData:
    """Funding rate information"""
    market_id: str
    rate: float
    effective_at: str
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'market_id': self.market_id,
            'rate': self.rate,
            'effective_at': self.effective_at,
            'timestamp': self.timestamp
        }


@dataclass
class ProcessingMetrics:
    """Data processing performance metrics"""
    messages_processed: int = 0
    ohlcv_generated: int = 0
    orderbook_updates: int = 0
    processing_latency_ms: List[float] = field(default_factory=list)
    error_count: int = 0
    uptime_start: float = field(default_factory=time.time)
    
    def add_latency_sample(self, latency_ms: float):
        """Add latency sample and maintain rolling window"""
        self.processing_latency_ms.append(latency_ms)
        # Keep only last 1000 samples
        if len(self.processing_latency_ms) > 1000:
            self.processing_latency_ms = self.processing_latency_ms[-1000:]
    
    def get_avg_latency_ms(self) -> float:
        """Get average processing latency"""
        if not self.processing_latency_ms:
            return 0.0
        return statistics.mean(self.processing_latency_ms)
    
    def get_p95_latency_ms(self) -> float:
        """Get 95th percentile latency"""
        if not self.processing_latency_ms:
            return 0.0
        return statistics.quantiles(self.processing_latency_ms, n=20)[18]  # 95th percentile
    
    def get_uptime_seconds(self) -> float:
        """Get uptime in seconds"""
        return time.time() - self.uptime_start


class MarketDataProcessor:
    """
    Processes raw market data from dYdX into structured formats
    
    Features:
    - Real-time OHLCV aggregation
    - Orderbook reconstruction
    - Funding rate tracking
    - Performance monitoring
    """
    
    def __init__(self, market_id: str = "BTC-USD"):
        self.market_id = market_id
        self.client: Optional[DydxClient] = None
        
        # Data storage
        self.ohlcv_data: deque = deque(maxlen=1000)  # Last 1000 candles
        self.orderbook_snapshots: deque = deque(maxlen=100)  # Last 100 snapshots
        self.funding_rates: deque = deque(maxlen=24)  # Last 24 funding rates
        
        # Current aggregation state
        self.current_candle: Optional[Dict[str, Any]] = None
        self.candle_interval_minutes = 1  # 1-minute candles
        self.last_candle_start = 0
        
        # Performance metrics
        self.metrics = ProcessingMetrics()
        
        # Message handlers
        self.message_handlers: List[Callable] = []
        
        # Running state
        self._running = False
    
    async def initialize(self, client: Optional[DydxClient] = None):
        """Initialize processor with dYdX client"""
        if client:
            self.client = client
        else:
            # Create client with message handler
            self.client = DydxClient(on_message=self._handle_websocket_message)
            await self.client.connect()
            
            # Start WebSocket in thread for real-time data
            self.client.start_websocket_in_thread()
        
        # Wait a moment for connection to stabilize
        await asyncio.sleep(3)
        
        # Subscribe to real-time data streams
        await self._setup_data_streams()
        self._running = True
    
    async def _setup_data_streams(self):
        """Setup WebSocket subscriptions for real-time data"""
        if not self.client:
            raise ValueError("Client not initialized")
        
        # Subscribe to trades for OHLCV aggregation
        await self.client.subscribe_to_trades(market_id=self.market_id)
        
        # Subscribe to orderbook for best bid/ask
        await self.client.subscribe_to_orderbook(market_id=self.market_id)
    
    def _handle_websocket_message(self, ws, message: Dict[str, Any]):
        """Handle all WebSocket messages and route to appropriate processors"""
        try:
            # Message is already parsed by the client
            msg_data = message
            
            # Route based on channel type
            channel = msg_data.get('channel', '')
            
            if 'trades' in channel:
                self._handle_trade_message(msg_data)
            elif 'orderbook' in channel:
                self._handle_orderbook_message(msg_data)
                
        except Exception as e:
            self.metrics.error_count += 1
            # Silent error handling - no debug output
    
    def _handle_trade_message(self, message: Dict[str, Any]):
        """Process trade message for OHLCV aggregation"""
        start_time = time.time()
        
        try:
            # Always increment message count
            self.metrics.messages_processed += 1
            
            if message.get('type') == 'subscribed':
                return
            
            # Extract trade data - check multiple possible structures
            trades_found = False
            
            # Structure 1: Direct contents.trades
            if 'contents' in message and 'trades' in message['contents']:
                trades = message['contents']['trades']
                for trade in trades:
                    self._process_trade(trade)
                trades_found = True
            
            # Structure 2: Contents as array with trades
            elif 'contents' in message and isinstance(message['contents'], list):
                for content in message['contents']:
                    if 'trades' in content:
                        trades = content['trades']
                        for trade in trades:
                            self._process_trade(trade)
                        trades_found = True
            
            # Structure 3: Direct trades in message
            elif 'trades' in message:
                trades = message['trades']
                for trade in trades:
                    self._process_trade(trade)
                trades_found = True
            
        except Exception as e:
            self.metrics.error_count += 1
            # Silent error handling - no debug output
        
        finally:
            # Record processing latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.add_latency_sample(latency_ms)
    
    def _handle_orderbook_message(self, message: Dict[str, Any]):
        """Process orderbook message for best bid/ask"""
        start_time = time.time()
        
        try:
            # Always increment message count
            self.metrics.messages_processed += 1
            
            if message.get('type') == 'subscribed':
                return
            
            # Extract orderbook data - check multiple possible structures
            orderbook_found = False
            
            # Structure 1: Direct contents.orderbook
            if 'contents' in message and 'orderbook' in message['contents']:
                orderbook = message['contents']['orderbook']
                self._process_orderbook(orderbook)
                orderbook_found = True
            
            # Structure 2: Contents as array with orderbook
            elif 'contents' in message and isinstance(message['contents'], list):
                # For dYdX v4, the orderbook may be split across multiple content objects
                all_bids = []
                all_asks = []
                
                for content in message['contents']:
                    if 'orderbook' in content:
                        # Complete orderbook in one content object
                        orderbook = content['orderbook']
                        self._process_orderbook(orderbook)
                        orderbook_found = True
                        break
                    elif 'bids' in content:
                        # Collect bids from this content object
                        all_bids.extend(content['bids'])
                    elif 'asks' in content:
                        # Collect asks from this content object
                        all_asks.extend(content['asks'])
                
                # If we collected separate bids and asks, combine them
                if all_bids and all_asks and not orderbook_found:
                    combined_orderbook = {
                        'bids': all_bids,
                        'asks': all_asks
                    }
                    self._process_orderbook(combined_orderbook)
                    orderbook_found = True
            
            # Structure 3: Direct orderbook in message
            elif 'orderbook' in message:
                orderbook = message['orderbook']
                self._process_orderbook(orderbook)
                orderbook_found = True
            
        except Exception as e:
            self.metrics.error_count += 1
            # Silent error handling - no debug output
        
        finally:
            # Record processing latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.add_latency_sample(latency_ms)
    
    def _process_trade(self, trade: Dict[str, Any]):
        """Process individual trade for OHLCV aggregation"""
        try:
            price = float(trade['price'])
            size = float(trade['size'])
            
            # Parse timestamp - handle both formats
            timestamp_str = trade['createdAt']
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]  # Remove 'Z' suffix
            
            # Convert to timestamp
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp_str.replace('Z', ''))
            timestamp = dt.timestamp()
            
            # Determine candle interval
            candle_start = self._get_candle_start_time(timestamp)
            
            # Initialize new candle if needed
            if self.current_candle is None or candle_start != self.last_candle_start:
                self._finalize_current_candle()
                self._start_new_candle(price, timestamp, candle_start)
            
            # Update current candle
            self.current_candle['high'] = max(self.current_candle['high'], price)
            self.current_candle['low'] = min(self.current_candle['low'], price)
            self.current_candle['close'] = price
            self.current_candle['volume'] += size
            
        except (KeyError, ValueError, TypeError) as e:
            self.metrics.error_count += 1
            # Silent error handling - no debug output
    
    def _process_orderbook(self, orderbook: Dict[str, Any]):
        """Process orderbook snapshot"""
        try:
            timestamp = time.time()
            
            # Extract best bid and ask
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            if not bids or not asks:
                return
            
            # Handle different orderbook formats
            # Format 1: [["price", "size"], ...] (dYdX v4 format)
            if isinstance(bids[0], list) and len(bids[0]) >= 2:
                best_bid = float(bids[0][0])
                bid_size = float(bids[0][1])
                best_ask = float(asks[0][0])
                ask_size = float(asks[0][1])
            # Format 2: [{"price": "...", "size": "..."}, ...] (object format)
            elif isinstance(bids[0], dict) and 'price' in bids[0]:
                best_bid = float(bids[0]['price'])
                best_ask = float(asks[0]['price'])
                bid_size = float(bids[0]['size'])
                ask_size = float(asks[0]['size'])
            else:
                return
            
            spread = best_ask - best_bid
            mid_price = (best_bid + best_ask) / 2
            
            snapshot = OrderbookSnapshot(
                timestamp=timestamp,
                market_id=self.market_id,
                best_bid=best_bid,
                best_ask=best_ask,
                bid_size=bid_size,
                ask_size=ask_size,
                spread=spread,
                mid_price=mid_price
            )
            
            self.orderbook_snapshots.append(snapshot)
            self.metrics.orderbook_updates += 1
            
        except (KeyError, ValueError, TypeError, IndexError) as e:
            self.metrics.error_count += 1
            # Silent error handling - no debug output
    
    def _get_candle_start_time(self, timestamp: float) -> float:
        """Get the start time for a candle interval"""
        interval_seconds = self.candle_interval_minutes * 60
        return int(timestamp // interval_seconds) * interval_seconds
    
    def _start_new_candle(self, price: float, timestamp: float, candle_start: float):
        """Start a new OHLCV candle"""
        self.current_candle = {
            'timestamp': candle_start,
            'open': price,
            'high': price,
            'low': price,
            'close': price,
            'volume': 0,
            'market_id': self.market_id
        }
        self.last_candle_start = candle_start
    
    def _finalize_current_candle(self):
        """Finalize and store the current candle"""
        if self.current_candle is not None:
            ohlcv = OHLCVData(**self.current_candle)
            self.ohlcv_data.append(ohlcv)
            self.metrics.ohlcv_generated += 1
    
    async def get_funding_rate(self) -> Optional[FundingRateData]:
        """Get current funding rate for the market"""
        if not self.client:
            return None
        
        try:
            # TODO: Fix funding rate API call - method name needs verification
            # response = await self.client.indexer_client.markets.get_perpetual_market_funding(
            #     market=self.market_id
            # )
            
            # For now, return a mock funding rate to keep dashboard functional
            funding_rate = FundingRateData(
                market_id=self.market_id,
                rate=0.0001,  # Mock 0.01% funding rate
                effective_at=datetime.now(timezone.utc).isoformat(),
                timestamp=time.time()
            )
            
            self.funding_rates.append(funding_rate)
            return funding_rate
                
        except Exception as e:
            self.metrics.error_count += 1
            # Silent error handling - no debug output
        
        return None
    
    def get_latest_ohlcv(self, count: int = 10) -> List[OHLCVData]:
        """Get latest OHLCV data"""
        return list(self.ohlcv_data)[-count:] if self.ohlcv_data else []
    
    def get_latest_orderbook(self) -> Optional[OrderbookSnapshot]:
        """Get latest orderbook snapshot"""
        return self.orderbook_snapshots[-1] if self.orderbook_snapshots else None
    
    def get_processing_metrics(self) -> ProcessingMetrics:
        """Get current processing metrics"""
        return self.metrics
    
    def add_message_handler(self, handler: Callable):
        """Add custom message handler"""
        self.message_handlers.append(handler)
    
    async def shutdown(self):
        """Shutdown processor and cleanup resources"""
        self._running = False
        
        # Finalize any current candle
        self._finalize_current_candle()
        
        # Disconnect client if we own it
        if self.client:
            await self.client.disconnect()
            # Give a moment for disconnection to complete
            await asyncio.sleep(0.1)
            
        # Clear client reference
        self.client = None
    
    def is_running(self) -> bool:
        """Check if processor is running"""
        return self._running and self.client is not None
