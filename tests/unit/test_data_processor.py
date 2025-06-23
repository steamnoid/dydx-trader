"""
Layer 3: Market Data Processor Unit Tests

Tests for the MarketDataProcessor class covering OHLCV aggregation,
orderbook processing, and performance metrics.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from src.dydx_bot.data.processor import (
    MarketDataProcessor, 
    OHLCVData, 
    OrderbookSnapshot, 
    FundingRateData,
    ProcessingMetrics
)


class TestMarketDataProcessor:
    """Test MarketDataProcessor functionality"""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance for testing"""
        return MarketDataProcessor("BTC-USD")
    
    @pytest.fixture
    def mock_client(self):
        """Create mock dYdX client"""
        client = AsyncMock()
        client.indexer_client = AsyncMock()
        client.markets = AsyncMock()
        return client
    
    def test_processor_initialization(self, processor):
        """Test processor initializes correctly"""
        assert processor.market_id == "BTC-USD"
        assert processor.client is None
        assert len(processor.ohlcv_data) == 0
        assert len(processor.orderbook_snapshots) == 0
        assert len(processor.funding_rates) == 0
        assert processor.metrics.messages_processed == 0
        assert not processor._running
    
    @pytest.mark.asyncio
    async def test_initialize_with_external_client(self, processor, mock_client):
        """Test initialization with external client"""
        with patch.object(processor, '_setup_data_streams') as mock_setup:
            await processor.initialize(client=mock_client)
            
            assert processor.client == mock_client
            assert processor._running
            mock_setup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_creates_internal_client(self, processor):
        """Test initialization uses connection manager when no client provided"""
        with patch('src.dydx_bot.data.processor.get_connection_manager') as mock_get_conn:
            mock_connection_manager = Mock()
            mock_client_instance = AsyncMock()
            
            # Setup connection manager mocks
            mock_connection_manager.is_connected.return_value = False
            mock_connection_manager.initialize = AsyncMock()
            mock_connection_manager.get_client.return_value = mock_client_instance
            mock_connection_manager.register_message_handler = Mock()
            mock_connection_manager.subscribe_to_market_data = AsyncMock(return_value=True)
            mock_get_conn.return_value = mock_connection_manager
            
            await processor.initialize()
            
            # Verify connection manager was used instead of direct client creation
            mock_connection_manager.is_connected.assert_called_once()
            mock_connection_manager.initialize.assert_called_once()
            mock_connection_manager.get_client.assert_called_once()
            mock_connection_manager.register_message_handler.assert_called_once_with(processor._handle_websocket_message)
            mock_connection_manager.subscribe_to_market_data.assert_called_once_with(
                market_id="BTC-USD",
                data_types=["orderbook", "trades"]
            )
            assert processor._running
    
    def test_ohlcv_data_creation(self):
        """Test OHLCV data structure"""
        ohlcv = OHLCVData(
            timestamp=1640995200.0,
            open=50000.0,
            high=51000.0,
            low=49500.0,
            close=50500.0,
            volume=100.5,
            market_id="BTC-USD"
        )
        
        assert ohlcv.timestamp == 1640995200.0
        assert ohlcv.open == 50000.0
        assert ohlcv.high == 51000.0
        assert ohlcv.low == 49500.0
        assert ohlcv.close == 50500.0
        assert ohlcv.volume == 100.5
        assert ohlcv.market_id == "BTC-USD"
        
        # Test serialization
        data_dict = ohlcv.to_dict()
        assert data_dict['timestamp'] == 1640995200.0
        assert data_dict['market_id'] == "BTC-USD"
    
    def test_orderbook_snapshot_creation(self):
        """Test orderbook snapshot structure"""
        snapshot = OrderbookSnapshot(
            timestamp=time.time(),
            market_id="BTC-USD",
            best_bid=50000.0,
            best_ask=50010.0,
            bid_size=1.5,
            ask_size=2.0,
            spread=10.0,
            mid_price=50005.0
        )
        
        assert snapshot.market_id == "BTC-USD"
        assert snapshot.best_bid == 50000.0
        assert snapshot.best_ask == 50010.0
        assert snapshot.spread == 10.0
        assert snapshot.mid_price == 50005.0
        
        # Test serialization
        data_dict = snapshot.to_dict()
        assert data_dict['best_bid'] == 50000.0
        assert data_dict['spread'] == 10.0
    
    def test_funding_rate_data_creation(self):
        """Test funding rate data structure"""
        funding = FundingRateData(
            market_id="BTC-USD",
            rate=0.0001,
            effective_at="2024-01-01T00:00:00Z",
            timestamp=time.time()
        )
        
        assert funding.market_id == "BTC-USD"
        assert funding.rate == 0.0001
        assert funding.effective_at == "2024-01-01T00:00:00Z"
        
        # Test serialization
        data_dict = funding.to_dict()
        assert data_dict['rate'] == 0.0001
        assert data_dict['effective_at'] == "2024-01-01T00:00:00Z"
    
    def test_processing_metrics(self):
        """Test processing metrics functionality"""
        metrics = ProcessingMetrics()
        
        # Test initial state
        assert metrics.messages_processed == 0
        assert metrics.error_count == 0
        assert len(metrics.processing_latency_ms) == 0
        
        # Test latency tracking
        metrics.add_latency_sample(10.5)
        metrics.add_latency_sample(15.2)
        metrics.add_latency_sample(8.7)
        
        assert len(metrics.processing_latency_ms) == 3
        assert metrics.get_avg_latency_ms() == pytest.approx(11.47, rel=1e-2)
        
        # Test uptime calculation
        uptime = metrics.get_uptime_seconds()
        assert uptime > 0
    
    def test_processing_metrics_rolling_window(self):
        """Test metrics maintain rolling window"""
        metrics = ProcessingMetrics()
        
        # Add more than 1000 samples
        for i in range(1200):
            metrics.add_latency_sample(float(i))
        
        # Should only keep last 1000
        assert len(metrics.processing_latency_ms) == 1000
        assert metrics.processing_latency_ms[0] == 200.0  # First kept sample
        assert metrics.processing_latency_ms[-1] == 1199.0  # Last sample
    
    def test_process_trade_message(self, processor):
        """Test trade message processing for OHLCV"""
        # Mock trade message
        trade_data = {
            'price': '50000.50',
            'size': '1.5',
            'createdAt': '2024-01-01T12:00:00Z'
        }
        
        processor._process_trade(trade_data)
        
        # Should create new candle
        assert processor.current_candle is not None
        assert processor.current_candle['open'] == 50000.50
        assert processor.current_candle['close'] == 50000.50
        assert processor.current_candle['volume'] == 1.5
        assert processor.current_candle['market_id'] == "BTC-USD"
    
    def test_process_multiple_trades_same_candle(self, processor):
        """Test multiple trades in same candle interval"""
        # First trade
        trade1 = {
            'price': '50000.00',
            'size': '1.0',
            'createdAt': '2024-01-01T12:00:00Z'
        }
        processor._process_trade(trade1)
        
        # Second trade in same minute
        trade2 = {
            'price': '50500.00',
            'size': '0.5',
            'createdAt': '2024-01-01T12:00:30Z'
        }
        processor._process_trade(trade2)
        
        # Third trade - lower price
        trade3 = {
            'price': '49800.00',
            'size': '0.75',
            'createdAt': '2024-01-01T12:00:45Z'
        }
        processor._process_trade(trade3)
        
        # Check OHLCV aggregation
        candle = processor.current_candle
        assert candle['open'] == 50000.00  # First trade price
        assert candle['high'] == 50500.00  # Highest price
        assert candle['low'] == 49800.00   # Lowest price
        assert candle['close'] == 49800.00 # Last trade price
        assert candle['volume'] == 2.25    # Sum of volumes
    
    def test_process_orderbook_message(self, processor):
        """Test orderbook message processing"""
        orderbook_data = {
            'bids': [
                {'price': '50000.00', 'size': '1.5'},
                {'price': '49995.00', 'size': '2.0'}
            ],
            'asks': [
                {'price': '50010.00', 'size': '1.0'},
                {'price': '50015.00', 'size': '1.5'}
            ]
        }
        
        processor._process_orderbook(orderbook_data)
        
        # Should have one snapshot
        assert len(processor.orderbook_snapshots) == 1
        
        snapshot = processor.orderbook_snapshots[0]
        assert snapshot.best_bid == 50000.00
        assert snapshot.best_ask == 50010.00
        assert snapshot.bid_size == 1.5
        assert snapshot.ask_size == 1.0
        assert snapshot.spread == 10.0
        assert snapshot.mid_price == 50005.00
        assert snapshot.market_id == "BTC-USD"
        
        # Check metrics
        assert processor.metrics.orderbook_updates == 1
    
    def test_websocket_message_handler(self, processor):
        """Test WebSocket message routing"""
        with patch.object(processor, '_handle_trade_message') as mock_trade, \
             patch.object(processor, '_handle_orderbook_message') as mock_orderbook:
            
            # Test trades channel
            trade_msg = {"channel": "v4_trades", "type": "subscribed"}
            processor._handle_websocket_message(None, trade_msg)
            mock_trade.assert_called_once()
            
            # Reset mocks
            mock_trade.reset_mock()
            mock_orderbook.reset_mock()
            
            # Test orderbook channel
            orderbook_msg = {"channel": "v4_orderbook", "type": "subscribed"}
            processor._handle_websocket_message(None, orderbook_msg)
            mock_orderbook.assert_called_once()
    
    def test_handle_trade_message_with_contents(self, processor):
        """Test trade message handling with trade contents"""
        message = {
            'type': 'channel_data',
            'contents': {
                'trades': [
                    {
                        'price': '50000.00',
                        'size': '1.0',
                        'createdAt': '2024-01-01T12:00:00Z'
                    },
                    {
                        'price': '50050.00',
                        'size': '0.5',
                        'createdAt': '2024-01-01T12:00:15Z'
                    }
                ]
            }
        }
        
        processor._handle_trade_message(message)
        
        # Should process both trades
        assert processor.current_candle is not None
        assert processor.current_candle['volume'] == 1.5
        assert processor.metrics.messages_processed == 1
    
    def test_handle_orderbook_message_with_contents(self, processor):
        """Test orderbook message handling with orderbook contents"""
        message = {
            'type': 'channel_data',
            'contents': {
                'orderbook': {
                    'bids': [{'price': '50000.00', 'size': '1.5'}],
                    'asks': [{'price': '50010.00', 'size': '1.0'}]
                }
            }
        }
        
        processor._handle_orderbook_message(message)
        
        # Should create orderbook snapshot
        assert len(processor.orderbook_snapshots) == 1
        assert processor.metrics.messages_processed == 1
        assert processor.metrics.orderbook_updates == 1
    
    def test_candle_interval_timing(self, processor):
        """Test candle start time calculation"""
        # Test 1-minute intervals
        timestamp1 = 1640995200.0  # 2022-01-01 00:00:00
        timestamp2 = 1640995230.0  # 2022-01-01 00:00:30
        timestamp3 = 1640995260.0  # 2022-01-01 00:01:00
        
        start1 = processor._get_candle_start_time(timestamp1)
        start2 = processor._get_candle_start_time(timestamp2)
        start3 = processor._get_candle_start_time(timestamp3)
        
        # Same minute should have same start time
        assert start1 == start2 == 1640995200.0
        # Next minute should have different start time
        assert start3 == 1640995260.0
    
    def test_finalize_candle(self, processor):
        """Test candle finalization"""
        # Create a test candle
        processor.current_candle = {
            'timestamp': time.time(),
            'open': 50000.0,
            'high': 50100.0,
            'low': 49900.0,
            'close': 50050.0,
            'volume': 10.5,
            'market_id': 'BTC-USD'
        }
        
        initial_count = processor.metrics.ohlcv_generated
        processor._finalize_current_candle()
        
        # Should add to OHLCV data
        assert len(processor.ohlcv_data) == 1
        assert processor.metrics.ohlcv_generated == initial_count + 1
        
        ohlcv = processor.ohlcv_data[0]
        assert ohlcv.open == 50000.0
        assert ohlcv.volume == 10.5
        assert ohlcv.market_id == 'BTC-USD'
    
    def test_get_latest_ohlcv(self, processor):
        """Test getting latest OHLCV data"""
        # Add test data
        for i in range(15):
            ohlcv = OHLCVData(
                timestamp=time.time() + i,
                open=50000.0 + i,
                high=50100.0 + i,
                low=49900.0 + i,
                close=50050.0 + i,
                volume=10.5,
                market_id="BTC-USD"
            )
            processor.ohlcv_data.append(ohlcv)
        
        # Test getting last 5
        latest_5 = processor.get_latest_ohlcv(count=5)
        assert len(latest_5) == 5
        assert latest_5[0].open == 50010.0  # 15-5 = 10
        assert latest_5[-1].open == 50014.0  # Last one
        
        # Test getting more than available
        latest_20 = processor.get_latest_ohlcv(count=20)
        assert len(latest_20) == 15  # All available
    
    def test_get_latest_orderbook(self, processor):
        """Test getting latest orderbook snapshot"""
        # No snapshots initially
        assert processor.get_latest_orderbook() is None
        
        # Add snapshot
        snapshot = OrderbookSnapshot(
            timestamp=time.time(),
            market_id="BTC-USD",
            best_bid=50000.0,
            best_ask=50010.0,
            bid_size=1.5,
            ask_size=1.0,
            spread=10.0,
            mid_price=50005.0
        )
        processor.orderbook_snapshots.append(snapshot)
        
        latest = processor.get_latest_orderbook()
        assert latest == snapshot
        assert latest.best_bid == 50000.0
    
    def test_error_handling_in_message_processing(self, processor):
        """Test error handling in message processing"""
        # Test invalid trade data
        invalid_trade = {
            'price': 'invalid',  # Non-numeric price
            'size': '1.0',
            'createdAt': '2024-01-01T12:00:00Z'
        }
        
        initial_errors = processor.metrics.error_count
        processor._process_trade(invalid_trade)
        
        # Should increment error count
        assert processor.metrics.error_count == initial_errors + 1
        
        # Test invalid orderbook data
        invalid_orderbook = {
            'bids': [],  # Empty bids
            'asks': []   # Empty asks
        }
        
        processor._process_orderbook(invalid_orderbook)
        # Should handle gracefully (no new snapshot created)
        assert len(processor.orderbook_snapshots) == 0
    
    @pytest.mark.asyncio
    async def test_shutdown(self, processor, mock_client):
        """Test processor shutdown"""
        # Mock the connection manager to avoid real WebSocket operations
        with patch('src.dydx_bot.data.processor.get_connection_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.subscribe_to_market_data = AsyncMock(return_value=True)
            mock_get_manager.return_value = mock_manager
            
            # Initialize processor
            await processor.initialize(client=mock_client)
            assert processor._running
        
        # Add some current candle data
        processor.current_candle = {
            'timestamp': time.time(),
            'open': 50000.0,
            'high': 50000.0,
            'low': 50000.0,
            'close': 50000.0,
            'volume': 1.0,
            'market_id': 'BTC-USD'
        }
        
        initial_ohlcv_count = len(processor.ohlcv_data)
        
        await processor.shutdown()
        
        # Should finalize current candle and cleanup
        assert not processor._running
        assert len(processor.ohlcv_data) == initial_ohlcv_count + 1
        mock_client.disconnect.assert_called_once()
    
    def test_is_running(self, processor):
        """Test running status check"""
        # Initially not running
        assert not processor.is_running()
        
        # Set running state
        processor._running = True
        processor.client = Mock()
        assert processor.is_running()
        
        # No client
        processor.client = None
        assert not processor.is_running()
    
    def test_latency_measurement(self, processor):
        """Test latency measurement in message handlers"""
        # Test trade message latency
        message = {
            'type': 'channel_data',
            'contents': {
                'trades': [
                    {
                        'price': '50000.00',
                        'size': '1.0',
                        'createdAt': '2024-01-01T12:00:00Z'
                    }
                ]
            }
        }
        
        processor._handle_trade_message(message)
        
        # Should record latency
        assert len(processor.metrics.processing_latency_ms) > 0
        assert processor.metrics.processing_latency_ms[0] >= 0
    
    def test_message_handler_subscription_types(self, processor):
        """Test handling of subscription messages"""
        # Subscription messages should not be processed as data
        subscription_message = {
            'type': 'subscribed',
            'channel': 'v4_trades'
        }
        
        initial_count = processor.metrics.messages_processed
        processor._handle_trade_message(subscription_message)
        
        # Should not process as trade data
        assert processor.current_candle is None
        # But should still count as processed message
        assert processor.metrics.messages_processed == initial_count + 1

    def test_p95_latency_calculation(self, processor):
        """Test P95 latency percentile calculation"""
        # Test with no latency samples
        assert processor.metrics.get_p95_latency_ms() == 0.0
        
        # Add multiple latency samples
        latency_samples = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0,
                          11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0]
        
        for latency in latency_samples:
            processor.metrics.add_latency_sample(latency)
            
        # P95 should be near the 95th percentile (19.0 for this dataset)
        p95_latency = processor.metrics.get_p95_latency_ms()
        assert 18.0 <= p95_latency <= 20.0  # Should be around 19.0
