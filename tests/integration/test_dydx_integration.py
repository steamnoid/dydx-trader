"""
Integration Tests for Layer 2: Multi-component Interactions

These tests validate interactions between our components without external dependencies.
Tests the pipeline from WebSocket messages to processed data.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from src.dydx_bot.connection.client import DydxClient
from dydx_v4_client.indexer.candles_resolution import CandlesResolution


class TestDydxClientIntegration:
    """Integration tests for DydxClient component interactions"""
    
    @pytest.mark.asyncio
    async def test_websocket_to_rest_client_integration(self):
        """Test that WebSocket and REST clients work together"""
        client = DydxClient()
        
        with patch('src.dydx_bot.connection.client.IndexerClient') as mock_indexer, \
             patch('src.dydx_bot.connection.client.IndexerSocket') as mock_socket:
            
            # Mock REST client
            mock_indexer_instance = AsyncMock()
            mock_indexer.return_value = mock_indexer_instance
            
            # Mock WebSocket
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            
            await client.connect()
            
            # Verify both clients are created and accessible
            assert client.indexer_client == mock_indexer_instance
            assert client.indexer_socket == mock_socket_instance
            assert client.is_connected()
    
    @pytest.mark.asyncio
    async def test_message_handling_pipeline(self):
        """Test the complete message handling pipeline"""
        client = DydxClient()
        processed_messages = []
        
        def custom_message_handler(ws, message):
            processed_messages.append(("processed", message))
        
        client._on_message = custom_message_handler
        
        with patch('src.dydx_bot.connection.client.IndexerSocket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            
            await client.connect()
            
            # Simulate different message types
            test_messages = [
                {"type": "connected", "channel": None},
                {"type": "subscribed", "channel": "v4_markets"},
                {"type": "channel_data", "channel": "v4_orderbook", "contents": [{"bids": [], "asks": []}]},
                {"type": "channel_batch_data", "channel": "v4_trades", "contents": [{"trades": []}]}
            ]
            
            for message in test_messages:
                client.handle_websocket_message(mock_socket_instance, message)
            
            # Verify all messages were processed
            assert len(processed_messages) == len(test_messages)
            for i, (status, msg) in enumerate(processed_messages):
                assert status == "processed"
                assert msg == test_messages[i]
    
    @pytest.mark.asyncio
    async def test_subscription_management_integration(self):
        """Test subscription and unsubscription lifecycle"""
        client = DydxClient()
        
        with patch('src.dydx_bot.connection.client.IndexerSocket') as mock_socket:
            # Create mock socket with all subscription methods
            mock_socket_instance = Mock()
            mock_socket_instance.markets = Mock()
            mock_socket_instance.order_book = Mock()
            mock_socket_instance.trades = Mock()
            mock_socket_instance.candles = Mock()
            mock_socket_instance.subaccounts = Mock()
            mock_socket.return_value = mock_socket_instance
            
            await client.connect()
            
            # Test subscription lifecycle for markets
            await client.subscribe_to_markets()
            mock_socket_instance.markets.subscribe.assert_called_once()
            
            await client.unsubscribe_from_markets()
            mock_socket_instance.markets.unsubscribe.assert_called_once()
            
            # Test subscription lifecycle for orderbook
            market_id = "BTC-USD"
            await client.subscribe_to_orderbook(market_id)
            mock_socket_instance.order_book.subscribe.assert_called_with(market_id, batched=True)
            
            await client.unsubscribe_from_orderbook(market_id)
            mock_socket_instance.order_book.unsubscribe.assert_called_with(market_id)
    
    @pytest.mark.asyncio
    async def test_concurrent_subscription_handling(self):
        """Test handling multiple concurrent subscriptions"""
        client = DydxClient()
        
        with patch('src.dydx_bot.connection.client.IndexerSocket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket_instance.markets = Mock()
            mock_socket_instance.order_book = Mock()
            mock_socket_instance.trades = Mock()
            mock_socket.return_value = mock_socket_instance
            
            await client.connect()
            
            # Test concurrent subscriptions
            subscription_tasks = [
                client.subscribe_to_markets(),
                client.subscribe_to_orderbook("BTC-USD"),
                client.subscribe_to_orderbook("ETH-USD"),
                client.subscribe_to_trades("BTC-USD"),
                client.subscribe_to_trades("ETH-USD")
            ]
            
            # Execute all subscriptions concurrently
            await asyncio.gather(*subscription_tasks)
            
            # Verify all subscriptions were called
            mock_socket_instance.markets.subscribe.assert_called_once()
            assert mock_socket_instance.order_book.subscribe.call_count == 2
            assert mock_socket_instance.trades.subscribe.call_count == 2
    
    @pytest.mark.asyncio
    async def test_error_propagation_through_pipeline(self):
        """Test error handling propagation through the integration"""
        client = DydxClient()
        
        # Test connection error propagation
        with patch('src.dydx_bot.connection.client.IndexerClient') as mock_indexer:
            mock_indexer.side_effect = ConnectionError("Network failure")
            
            with pytest.raises(ConnectionError, match="Network failure"):
                await client.connect()
            
            assert not client.is_connected()
    
    @pytest.mark.asyncio
    async def test_websocket_message_filtering(self):
        """Test filtering and routing of different WebSocket message types"""
        client = DydxClient()
        received_by_type = {}
        
        def type_tracking_handler(ws, message):
            msg_type = message.get("type", "unknown")
            if msg_type not in received_by_type:
                received_by_type[msg_type] = []
            received_by_type[msg_type].append(message)
        
        client._on_message = type_tracking_handler
        
        with patch('src.dydx_bot.connection.client.IndexerSocket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            
            await client.connect()
            
            # Simulate various message types
            messages = [
                {"type": "connected"},
                {"type": "subscribed", "channel": "v4_markets"},
                {"type": "subscribed", "channel": "v4_orderbook"},
                {"type": "channel_data", "channel": "v4_markets", "contents": []},
                {"type": "channel_data", "channel": "v4_orderbook", "contents": []},
                {"type": "channel_batch_data", "channel": "v4_trades", "contents": []},
                {"type": "error", "message": "Test error"}
            ]
            
            for message in messages:
                client.handle_websocket_message(mock_socket_instance, message)
            
            # Verify messages were correctly categorized
            assert "connected" in received_by_type
            assert "subscribed" in received_by_type
            assert "channel_data" in received_by_type
            assert "channel_batch_data" in received_by_type
            assert "error" in received_by_type
            
            assert len(received_by_type["subscribed"]) == 2
            assert len(received_by_type["channel_data"]) == 2
    
    @pytest.mark.asyncio
    async def test_threading_integration(self):
        """Test threading integration with WebSocket"""
        client = DydxClient()
        
        with patch('src.dydx_bot.connection.client.IndexerSocket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket_instance.connect = AsyncMock()
            mock_socket.return_value = mock_socket_instance
            
            await client.connect()
            
            # Test that threading functionality is available
            thread = client.start_websocket_in_thread()
            assert thread is not None
            
            # Give thread a moment to start
            await asyncio.sleep(0.1)
    
    @pytest.mark.asyncio
    async def test_connection_state_management(self):
        """Test connection state management through the integration"""
        client = DydxClient()
        
        # Initial state
        assert not client.is_connected()
        
        with patch('src.dydx_bot.connection.client.IndexerClient') as mock_indexer, \
             patch('src.dydx_bot.connection.client.IndexerSocket') as mock_socket:
            
            mock_indexer.return_value = AsyncMock()
            mock_socket.return_value = Mock()
            
            # Connect
            await client.connect()
            assert client.is_connected()
            
            # Disconnect
            await client.disconnect()
            assert not client.is_connected()
            
            # Reconnect
            await client.connect()
            assert client.is_connected()
    
    @pytest.mark.asyncio
    async def test_candles_subscription_integration(self):
        """Test candles subscription with resolution parameter"""
        client = DydxClient()
        
        with patch('src.dydx_bot.connection.client.IndexerSocket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket_instance.candles = Mock()
            mock_socket.return_value = mock_socket_instance
            
            await client.connect()
            
            # Test different resolutions
            resolutions = [
                CandlesResolution.ONE_MINUTE,
                CandlesResolution.FIVE_MINUTES,
                CandlesResolution.FIFTEEN_MINUTES
            ]
            
            market_id = "BTC-USD"
            for resolution in resolutions:
                await client.subscribe_to_candles(market_id, resolution)
                mock_socket_instance.candles.subscribe.assert_called_with(
                    market_id, resolution, batched=True
                )
    
    @pytest.mark.asyncio
    async def test_subaccounts_subscription_integration(self):
        """Test subaccounts subscription integration"""
        client = DydxClient()
        
        with patch('src.dydx_bot.connection.client.IndexerSocket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket_instance.subaccounts = Mock()
            mock_socket.return_value = mock_socket_instance
            
            await client.connect()
            
            # Test subaccount subscription
            test_address = "dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art"
            subaccount_number = 0
            
            await client.subscribe_to_subaccounts(test_address, subaccount_number)
            mock_socket_instance.subaccounts.subscribe.assert_called_with(
                test_address, subaccount_number
            )
            
            await client.unsubscribe_from_subaccounts(test_address, subaccount_number)
            mock_socket_instance.subaccounts.unsubscribe.assert_called_with(
                test_address, subaccount_number
            )
    
    @pytest.mark.asyncio
    async def test_message_handler_chaining(self):
        """Test chaining multiple message handlers"""
        client = DydxClient()
        handler1_calls = []
        handler2_calls = []
        
        def handler1(ws, message):
            handler1_calls.append(message)
        
        def handler2(ws, message):
            handler2_calls.append(message)
            
        # Set initial handler
        client._on_message = handler1
        
        with patch('src.dydx_bot.connection.client.IndexerSocket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            
            await client.connect()
            
            # Send message with first handler
            test_message1 = {"type": "connected"}
            client.handle_websocket_message(mock_socket_instance, test_message1)
            
            # Change handler
            client._on_message = handler2
            
            # Send message with second handler
            test_message2 = {"type": "subscribed", "channel": "v4_markets"}
            client.handle_websocket_message(mock_socket_instance, test_message2)
            
            # Verify handlers received appropriate messages
            assert len(handler1_calls) == 1
            assert handler1_calls[0] == test_message1
            
            assert len(handler2_calls) == 1
            assert handler2_calls[0] == test_message2
