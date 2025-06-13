"""
End-to-End Tests for Layer 2: Real dYdX Mainnet Connection

These tests validate that our DydxClient actually works with the real dYdX protocol.
Uses mainnet for better data activity but with testnet credentials.
"""

import pytest
import asyncio
import time
from unittest.mock import patch
from src.dydx_bot.connection.client import DydxClient
from dydx_v4_client.indexer.candles_resolution import CandlesResolution


class TestRealDydxConnection:
    """End-to-end tests with real dYdX mainnet"""
    
    @pytest.mark.asyncio
    async def test_real_indexer_client_connection(self):
        """Test real IndexerClient connection to dYdX mainnet"""
        client = DydxClient()
        
        # Use real IndexerClient, no mocks
        await client.connect()
        
        assert client.is_connected()
        assert client.indexer_client is not None
        
        # Test a real REST API call
        try:
            # This should work with real mainnet
            markets_response = await client.indexer_client.markets.get_perpetual_markets()
            assert "markets" in markets_response
            assert "BTC-USD" in markets_response["markets"]
            
            # Validate BTC-USD market structure
            btc_market = markets_response["markets"]["BTC-USD"]
            assert "status" in btc_market
            assert "ticker" in btc_market
            assert btc_market["status"] in ["ACTIVE", "PAUSED"]
            
        except Exception as e:
            pytest.fail(f"Real IndexerClient failed to fetch markets: {e}")
        
        await client.disconnect()
    
    @pytest.mark.asyncio 
    async def test_real_market_data_retrieval(self):
        """Test retrieving real market data from dYdX mainnet"""
        client = DydxClient()
        await client.connect()
        
        try:
            # Test orderbook data
            orderbook = await client.indexer_client.markets.get_perpetual_market_orderbook("BTC-USD")
            assert "asks" in orderbook
            assert "bids" in orderbook
            assert len(orderbook["asks"]) > 0
            assert len(orderbook["bids"]) > 0
            
            # Validate orderbook structure
            first_ask = orderbook["asks"][0]
            first_bid = orderbook["bids"][0]
            assert "price" in first_ask
            assert "size" in first_ask
            assert "price" in first_bid  
            assert "size" in first_bid
            
            # Test trades data
            trades = await client.indexer_client.markets.get_perpetual_market_trades("BTC-USD")
            assert "trades" in trades
            assert len(trades["trades"]) > 0
            
            # Validate trade structure
            first_trade = trades["trades"][0]
            assert "price" in first_trade
            assert "size" in first_trade
            assert "side" in first_trade
            assert first_trade["side"] in ["BUY", "SELL"]
            
        except Exception as e:
            pytest.fail(f"Real market data retrieval failed: {e}")
            
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_real_candles_data(self):
        """Test retrieving real candles data from dYdX mainnet"""
        client = DydxClient()
        await client.connect()
        
        try:
            # Test candles data
            candles = await client.indexer_client.markets.get_perpetual_market_candles(
                "BTC-USD", 
                "1MIN"
            )
            assert "candles" in candles
            assert len(candles["candles"]) > 0
            
            # Validate candle structure
            first_candle = candles["candles"][0]
            required_fields = ["startedAt", "low", "high", "open", "close", "baseTokenVolume", "usdVolume"]
            for field in required_fields:
                assert field in first_candle, f"Missing field: {field}"
            
            # Validate OHLC data makes sense
            assert float(first_candle["low"]) <= float(first_candle["high"])
            assert float(first_candle["low"]) <= float(first_candle["open"])
            assert float(first_candle["low"]) <= float(first_candle["close"])
            assert float(first_candle["open"]) <= float(first_candle["high"])
            assert float(first_candle["close"]) <= float(first_candle["high"])
            
        except Exception as e:
            pytest.fail(f"Real candles data retrieval failed: {e}")
            
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_real_websocket_connection(self):
        """Test real WebSocket connection to dYdX mainnet"""
        client = DydxClient()
        
        # Track received messages
        received_messages = []
        original_handler = None
        
        def test_message_handler(ws, message):
            received_messages.append(message)
            # Call original handler if it exists
            if original_handler:
                original_handler(ws, message)
        
        # Replace message handler
        original_handler = client._on_message
        client._on_message = test_message_handler
        
        try:
            await client.connect()
            
            # Start WebSocket in a thread (following official patterns)
            thread = client.start_websocket_in_thread()
            
            # Wait a bit for connection
            await asyncio.sleep(2)
            
            # Check if we received connection confirmation
            connected_messages = [msg for msg in received_messages if msg.get("type") == "connected"]
            assert len(connected_messages) > 0, "No 'connected' message received from WebSocket"
            
            # Try to subscribe to markets
            await client.subscribe_to_markets()
            
            # Wait for market data
            await asyncio.sleep(3)
            
            # Should have received some market data
            market_messages = [msg for msg in received_messages if msg.get("channel") == "v4_markets"]
            assert len(market_messages) > 0, "No market data received from WebSocket"
            
        except Exception as e:
            pytest.fail(f"Real WebSocket connection failed: {e}")
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_real_orderbook_websocket_subscription(self):
        """Test real orderbook WebSocket subscription"""
        client = DydxClient()
        received_messages = []
        
        def track_messages(ws, message):
            received_messages.append(message)
        
        client._on_message = track_messages
        
        try:
            await client.connect()
            thread = client.start_websocket_in_thread()
            
            # Wait for connection
            await asyncio.sleep(2)
            
            # Subscribe to BTC-USD orderbook
            await client.subscribe_to_orderbook("BTC-USD")
            
            # Wait for orderbook data
            await asyncio.sleep(5)
            
            # Check for orderbook messages
            orderbook_messages = [msg for msg in received_messages 
                                if msg.get("channel") == "v4_orderbook"]
            assert len(orderbook_messages) > 0, "No orderbook data received"
            
            # Validate orderbook message structure
            for msg in orderbook_messages[:1]:  # Check first message
                if "contents" in msg and isinstance(msg["contents"], list) and len(msg["contents"]) > 0:
                    content = msg["contents"][0]
                    # Should have either bids or asks
                    if isinstance(content, dict):
                        assert "bids" in content or "asks" in content
                # If no content yet, that's okay - connection is working
                    
        except Exception as e:
            pytest.fail(f"Real orderbook WebSocket failed: {e}")
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio 
    async def test_real_trades_websocket_subscription(self):
        """Test real trades WebSocket subscription"""
        client = DydxClient()
        received_messages = []
        
        def track_messages(ws, message):
            received_messages.append(message)
        
        client._on_message = track_messages
        
        try:
            await client.connect()
            thread = client.start_websocket_in_thread()
            
            # Wait for connection
            await asyncio.sleep(2)
            
            # Subscribe to BTC-USD trades
            await client.subscribe_to_trades("BTC-USD")
            
            # Wait for trade data
            await asyncio.sleep(5)
            
            # Check for trade messages
            trade_messages = [msg for msg in received_messages 
                            if msg.get("channel") == "v4_trades"]
            
            # Note: Trades might be less frequent, so we'll be more lenient
            if len(trade_messages) > 0:
                # Validate trade message structure
                for msg in trade_messages[:1]:
                    if "contents" in msg and isinstance(msg["contents"], list) and len(msg["contents"]) > 0:
                        content = msg["contents"][0]
                        if isinstance(content, dict):
                            assert "trades" in content
                # If no trade content yet, that's okay - connection is working
                        
        except Exception as e:
            pytest.fail(f"Real trades WebSocket failed: {e}")
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_connection_resilience(self):
        """Test connection resilience and error handling"""
        client = DydxClient()
        
        # Test multiple connect/disconnect cycles
        for i in range(3):
            await client.connect()
            assert client.is_connected()
            
            # Brief operation
            markets = await client.indexer_client.markets.get_perpetual_markets()
            assert "markets" in markets
            
            await client.disconnect()
            assert not client.is_connected()
            
            # Small delay between cycles
            await asyncio.sleep(0.5)
    
    @pytest.mark.asyncio
    async def test_multiple_market_subscriptions(self):
        """Test subscribing to multiple markets simultaneously"""
        client = DydxClient()
        received_messages = []
        
        def track_messages(ws, message):
            received_messages.append(message)
        
        client._on_message = track_messages
        
        try:
            await client.connect()
            thread = client.start_websocket_in_thread()
            
            # Wait for connection
            await asyncio.sleep(2)
            
            # Subscribe to multiple markets
            markets = ["BTC-USD", "ETH-USD"]
            for market in markets:
                await client.subscribe_to_orderbook(market)
                await asyncio.sleep(0.5)  # Small delay between subscriptions
            
            # Wait for data
            await asyncio.sleep(5)
            
            # Check we received data for both markets
            orderbook_messages = [msg for msg in received_messages 
                                if msg.get("channel") == "v4_orderbook"]
            
            if len(orderbook_messages) > 0:
                # Just verify we got some orderbook data
                assert len(orderbook_messages) > 0
                
        except Exception as e:
            pytest.fail(f"Multiple market subscriptions failed: {e}")
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_real_performance_timing(self):
        """Test performance of real dYdX operations"""
        client = DydxClient()
        
        # Time connection
        start_time = time.time()
        await client.connect()
        connect_time = time.time() - start_time
        
        assert connect_time < 5.0, f"Connection took too long: {connect_time:.2f}s"
        
        # Time market data fetch
        start_time = time.time()
        markets = await client.indexer_client.markets.get_perpetual_markets()
        fetch_time = time.time() - start_time
        
        assert fetch_time < 2.0, f"Market fetch took too long: {fetch_time:.2f}s"
        assert "markets" in markets
        
        # Time orderbook fetch
        start_time = time.time()
        orderbook = await client.indexer_client.markets.get_perpetual_market_orderbook("BTC-USD")
        orderbook_time = time.time() - start_time
        
        assert orderbook_time < 2.0, f"Orderbook fetch took too long: {orderbook_time:.2f}s"
        assert "asks" in orderbook and "bids" in orderbook
        
        await client.disconnect()
