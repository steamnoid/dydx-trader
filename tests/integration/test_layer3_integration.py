"""
Layer 3 Integration Tests
========================

Integration tests for Layer 3 Market Data Processing
Testing the integration between Layer 2 (connection) and Layer 3 (data processing)
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from dydx_bot.data.processor import MarketDataProcessor
from dydx_bot.connection.client import DydxClient


class TestLayer3Integration:
    """Integration tests for Layer 3 with Layer 2 connection"""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock dYdX client for integration testing"""
        client = Mock(spec=DydxClient)
        client.indexer_client = Mock()
        client.indexer_client.markets = Mock()
        client.start_websocket_in_thread = AsyncMock()
        client.subscribe_to_trades = AsyncMock()
        client.subscribe_to_orderbook = AsyncMock()
        client.stop_websocket = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_processor_client_integration(self, mock_client):
        """Test processor initialization with client integration"""
        processor = MarketDataProcessor(market_id="BTC-USD")
        
        try:
            # Test initialization with provided client - this should call _setup_data_streams
            await processor.initialize(client=mock_client)
            
            # Verify client integration calls for subscription only (not websocket start)
            mock_client.subscribe_to_trades.assert_called_once_with(market_id="BTC-USD")
            mock_client.subscribe_to_orderbook.assert_called_once_with(market_id="BTC-USD")
            
            # Verify processor state
            assert processor.client is mock_client
            assert processor.is_running()
        finally:
            # GUARANTEED cleanup
            await processor.shutdown()
            mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio 
    async def test_processor_websocket_initialization(self):
        """Test processor initialization with WebSocket setup when no client provided"""
        processor = MarketDataProcessor(market_id="BTC-USD")
        
        # Mock the DydxClient creation to avoid real connections
        with patch('dydx_bot.data.processor.DydxClient') as mock_client_class:
            mock_client_instance = AsyncMock()
            # start_websocket_in_thread is not async in real implementation
            mock_client_instance.start_websocket_in_thread = Mock()
            mock_client_class.return_value = mock_client_instance
            
            try:
                # Test initialization without provided client - should create and setup WebSocket
                await processor.initialize()
                
                # Verify client was created with message handler
                mock_client_class.assert_called_once()
                call_args = mock_client_class.call_args
                assert 'on_message' in call_args.kwargs
                
                # Verify client setup calls
                mock_client_instance.connect.assert_called_once()
                mock_client_instance.start_websocket_in_thread.assert_called_once()
                mock_client_instance.subscribe_to_trades.assert_called_once_with(market_id="BTC-USD")
                mock_client_instance.subscribe_to_orderbook.assert_called_once_with(market_id="BTC-USD")
                
                # Verify processor state
                assert processor.client is mock_client_instance
                assert processor.is_running()
            finally:
                # GUARANTEED cleanup
                await processor.shutdown()
                mock_client_instance.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_to_end_message_processing_pipeline(self, mock_client):
        """Test complete message processing pipeline from WebSocket to data structures"""
        processor = MarketDataProcessor(market_id="BTC-USD")
        
        try:
            await processor.initialize(client=mock_client)
            
            # Simulate incoming trade message through WebSocket handler
            trade_message = {
                "type": "channel_data",
                "channel": "v4_trades",
                "id": "BTC-USD",
                "contents": {
                    "trades": [
                        {
                            "id": "test-trade-123",
                            "price": "45000.50",
                            "size": "0.1",
                            "side": "BUY",
                            "createdAt": "2024-01-15T12:30:45.123Z",
                            "resources": {"markets": {"BTC-USD": {"id": "BTC-USD"}}}
                        }
                    ]
                }
            }
            
            # Process through WebSocket handler (simulating real flow)
            processor._handle_websocket_message(mock_client, trade_message)
            
            # Verify data processed correctly
            assert processor.metrics.messages_processed == 1
            assert processor.current_candle is not None
            assert processor.current_candle['open'] == 45000.50
            assert processor.current_candle['volume'] == 0.1
            
            # Simulate orderbook message
            orderbook_message = {
                "type": "channel_data",
                "channel": "v4_orderbook",
                "id": "BTC-USD",
                "contents": {
                    "orderbook": {
                        "bids": [{"price": "45000.00", "size": "2.0"}],
                        "asks": [{"price": "45001.00", "size": "1.5"}]
                    }
                }
            }
            
            processor._handle_websocket_message(mock_client, orderbook_message)
            
            # Verify orderbook processing
            assert processor.metrics.messages_processed == 2
            latest_orderbook = processor.get_latest_orderbook()
            assert latest_orderbook is not None
            assert latest_orderbook.best_bid == 45000.00
            assert latest_orderbook.best_ask == 45001.00
            
        finally:
            await processor.shutdown()

    def test_multi_message_integration_performance(self, mock_client):
        """Test performance with multiple messages simulating real market load"""
        processor = MarketDataProcessor(market_id="BTC-USD")
        processor.client = mock_client
        
        # Process multiple trade messages rapidly
        start_time = time.time()
        message_count = 100
        
        for i in range(message_count):
            trade_message = {
                "type": "channel_data",
                "channel": "v4_trades",
                "contents": {
                    "trades": [
                        {
                            "price": str(45000.0 + i),  # Varying prices
                            "size": "0.1",
                            "side": "BUY" if i % 2 == 0 else "SELL",
                            "createdAt": "2024-01-15T12:30:45.123Z",
                            "resources": {"markets": {"BTC-USD": {"id": "BTC-USD"}}}
                        }
                    ]
                }
            }
            processor._handle_trade_message(trade_message)
            
        processing_time = time.time() - start_time
        
        # Performance assertions
        assert processor.metrics.messages_processed == message_count
        assert processing_time < 1.0  # Should process 100 messages in under 1 second
        assert processor.metrics.get_avg_latency_ms() < 10.0  # Low average latency
        
        # Verify data integrity after high-volume processing
        assert processor.current_candle is not None
        assert processor.current_candle['volume'] == pytest.approx(message_count * 0.1)
        
    def test_error_recovery_integration(self, mock_client):
        """Test error recovery in integration context"""
        processor = MarketDataProcessor(market_id="BTC-USD")
        processor.client = mock_client
        
        # Process valid message
        valid_message = {
            "type": "channel_data",
            "channel": "v4_trades",
            "contents": {
                "trades": [
                    {
                        "price": "45000.00",
                        "size": "0.1",
                        "side": "BUY",
                        "createdAt": "2024-01-15T12:30:45.123Z",
                        "resources": {"markets": {"BTC-USD": {"id": "BTC-USD"}}}
                    }
                ]
            }
        }
        
        processor._handle_websocket_message(mock_client, valid_message)
        assert processor.metrics.messages_processed == 1
        assert processor.metrics.error_count == 0
        
        # Process invalid message (should recover gracefully)
        invalid_message = {
            "type": "channel_data",
            "channel": "v4_trades",
            "contents": {
                "trades": [
                    {
                        "price": "invalid_price",  # Invalid format
                        "size": "0.1",
                        "side": "BUY"
                    }
                ]
            }
        }
        
        processor._handle_websocket_message(mock_client, invalid_message)
        
        # Verify error handling and recovery
        assert processor.metrics.messages_processed == 2  # Still counted
        assert processor.metrics.error_count > 0  # Error recorded
        
        # Process another valid message (should continue working)
        processor._handle_websocket_message(mock_client, valid_message)
        assert processor.metrics.messages_processed == 3
        
    @pytest.mark.asyncio
    async def test_funding_rate_integration(self, mock_client):
        """Test funding rate integration with client"""
        processor = MarketDataProcessor(market_id="BTC-USD")
        processor.client = mock_client
        await processor.initialize()
        
        try:
            # Test funding rate retrieval (using mock implementation)
            funding_rate = await processor.get_funding_rate()
            
            assert funding_rate is not None
            assert funding_rate.market_id == "BTC-USD"
            assert funding_rate.rate == 0.0001  # Mock rate
            assert len(processor.funding_rates) == 1
            
            # Test multiple funding rate calls
            funding_rate2 = await processor.get_funding_rate()
            assert len(processor.funding_rates) == 2
            
        finally:
            await processor.shutdown()

    def test_subscription_message_handling_integration(self, mock_client):
        """Test handling of subscription confirmation messages"""
        processor = MarketDataProcessor(market_id="BTC-USD")
        processor.client = mock_client
        
        # Simulate subscription confirmation messages
        trade_subscription = {
            "type": "subscribed",
            "channel": "v4_trades",
            "id": "BTC-USD"
        }
        
        orderbook_subscription = {
            "type": "subscribed", 
            "channel": "v4_orderbook",
            "id": "BTC-USD"
        }
        
        # Process subscription messages
        processor._handle_websocket_message(mock_client, trade_subscription)
        processor._handle_websocket_message(mock_client, orderbook_subscription)
        
        # Verify they're counted but not processed as data
        assert processor.metrics.messages_processed == 2
        assert processor.current_candle is None  # No trade data processed
        assert len(processor.orderbook_snapshots) == 0  # No orderbook data processed

    def test_concurrent_message_processing_integration(self, mock_client):
        """Test concurrent message processing in integration context"""
        import threading
        
        processor = MarketDataProcessor(market_id="BTC-USD")
        processor.client = mock_client
        
        def process_trades(count: int):
            """Process trade messages in thread"""
            for i in range(count):
                trade_message = {
                    "type": "channel_data",
                    "channel": "v4_trades",
                    "contents": {
                        "trades": [
                            {
                                "price": str(45000.0 + i),
                                "size": "0.1",
                                "side": "BUY",
                                "createdAt": "2024-01-15T12:30:45.123Z",
                                "resources": {"markets": {"BTC-USD": {"id": "BTC-USD"}}}
                            }
                        ]
                    }
                }
                processor._handle_websocket_message(mock_client, trade_message)
        
        def process_orderbooks(count: int):
            """Process orderbook messages in thread"""
            for i in range(count):
                orderbook_message = {
                    "type": "channel_data",
                    "channel": "v4_orderbook",
                    "contents": {
                        "orderbook": {
                            "bids": [{"price": str(45000.0 - i), "size": "1.0"}],
                            "asks": [{"price": str(45001.0 + i), "size": "1.0"}]
                        }
                    }
                }
                processor._handle_websocket_message(mock_client, orderbook_message)
        
        # Run concurrent processing
        trade_thread = threading.Thread(target=process_trades, args=(50,))
        orderbook_thread = threading.Thread(target=process_orderbooks, args=(50,))
        
        trade_thread.start()
        orderbook_thread.start()
        
        trade_thread.join()
        orderbook_thread.join()
        
        # Verify concurrent processing worked correctly
        assert processor.metrics.messages_processed == 100
        assert processor.current_candle is not None
        assert len(processor.orderbook_snapshots) == 50
        assert processor.current_candle['volume'] == pytest.approx(50 * 0.1)  # All trades processed

    def test_data_structure_integration_consistency(self, mock_client):
        """Test data structure consistency across integration points"""
        processor = MarketDataProcessor(market_id="BTC-USD")
        processor.client = mock_client
        
        # Process mixed message types
        messages = [
            # Trade message
            {
                "type": "channel_data",
                "channel": "v4_trades",
                "contents": {
                    "trades": [
                        {
                            "price": "45000.00",
                            "size": "0.5",
                            "side": "BUY",
                            "createdAt": "2024-01-15T12:30:45.123Z",
                            "resources": {"markets": {"BTC-USD": {"id": "BTC-USD"}}}
                        }
                    ]
                }
            },
            # Orderbook message
            {
                "type": "channel_data",
                "channel": "v4_orderbook",
                "contents": {
                    "orderbook": {
                        "bids": [{"price": "44999.00", "size": "2.0"}],
                        "asks": [{"price": "45001.00", "size": "1.5"}]
                    }
                }
            },
            # Subscription message
            {
                "type": "subscribed",
                "channel": "v4_trades"
            }
        ]
        
        for message in messages:
            processor._handle_websocket_message(mock_client, message)
            
        # Verify data structure consistency
        assert processor.metrics.messages_processed == 3
        
        # Check OHLCV data consistency
        assert processor.current_candle is not None
        assert processor.current_candle['market_id'] == "BTC-USD"
        
        # Check orderbook data consistency
        latest_orderbook = processor.get_latest_orderbook()
        assert latest_orderbook is not None
        assert latest_orderbook.market_id == "BTC-USD"
        assert latest_orderbook.best_bid == 44999.00
        assert latest_orderbook.best_ask == 45001.00
        
        # Check metrics consistency
        assert processor.metrics.error_count == 0
        assert len(processor.metrics.processing_latency_ms) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
