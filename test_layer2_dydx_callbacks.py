"""
Layer 2 dYdX Trades Stream Callbacks Tests
Following STRICT TDD methodology - testing real dYdX WebSocket integration with callback interface
"""
import pytest
import time
import threading
from layer2_dydx_callbacks import DydxTradesStreamCallbacks


class TestDydxTradesStreamCallbacks:
    """Test Layer 2 dYdX trades streaming functionality with WebSocket and callbacks"""
    
    def test_can_create_dydx_trades_stream_callbacks(self):
        """Test that we can create a DydxTradesStreamCallbacks instance"""
        # Arrange: No setup needed for this basic test
        
        # Act: Create the stream instance
        stream = DydxTradesStreamCallbacks()
        
        # Assert: Should create valid instance
        assert stream is not None
        assert hasattr(stream, 'connect')
        assert hasattr(stream, 'subscribe_to_trades')
        assert hasattr(stream, 'subscribe_to_orderbook')
    
    def test_connect_initializes_websocket_connection(self):
        """Test that connect() initializes WebSocket connection to dYdX"""
        # Arrange: Create stream instance
        stream = DydxTradesStreamCallbacks()
        
        # Act: Connect to dYdX WebSocket
        result = stream.connect()
        
        # Assert: Connection should be established
        assert result is True
        assert stream.is_connected() is True
    
    def test_subscribe_to_trades_requires_connection(self):
        """Test that subscribe_to_trades() requires active connection"""
        # Arrange: Create stream instance without connecting
        stream = DydxTradesStreamCallbacks()
        
        def dummy_callback(trade):
            pass
        
        # Act & Assert: Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Must connect before subscribing"):
            stream.subscribe_to_trades("BTC-USD", dummy_callback)
    
    def test_subscribe_to_trades_with_callback(self):
        """Test that subscribe_to_trades() works with callback function"""
        # Arrange: Create and connect stream
        stream = DydxTradesStreamCallbacks()
        stream.connect()
        
        received_trades = []
        def trade_callback(trade):
            received_trades.append(trade)
        
        # Act: Subscribe to trades
        stream.subscribe_to_trades("BTC-USD", trade_callback)
        
        # Assert: Should be subscribed
        assert "BTC-USD" in stream.get_subscribed_markets()
        
        # Wait for some trade data (allow up to 30 seconds)
        timeout = 30
        start_time = time.time()
        while len(received_trades) == 0 and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # Should have received at least one trade
        assert len(received_trades) > 0
        
        # Verify trade structure
        trade = received_trades[0]
        assert "market_id" in trade
        assert "received_at" in trade
        assert "is_initial" in trade
        assert trade["market_id"] == "BTC-USD"
    
    def test_subscribe_to_orderbook_with_callback(self):
        """Test that subscribe_to_orderbook() works with callback function"""
        # Arrange: Create and connect stream
        stream = DydxTradesStreamCallbacks()
        stream.connect()
        
        received_orderbooks = []
        def orderbook_callback(orderbook):
            received_orderbooks.append(orderbook)
        
        # Act: Subscribe to orderbook
        stream.subscribe_to_orderbook("BTC-USD", orderbook_callback)
        
        # Wait for orderbook data (allow up to 30 seconds)
        timeout = 30
        start_time = time.time()
        while len(received_orderbooks) == 0 and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # Should have received at least one orderbook
        assert len(received_orderbooks) > 0
        
        # Verify orderbook structure
        orderbook = received_orderbooks[0]
        assert "bids" in orderbook
        assert "asks" in orderbook
        assert isinstance(orderbook["bids"], list)
        assert isinstance(orderbook["asks"], list)
    
    def test_subscribe_to_all_trades_with_unified_callback(self):
        """Test that subscribe_to_all_trades() works with unified callback"""
        # Arrange: Create and connect stream
        stream = DydxTradesStreamCallbacks()
        stream.connect()
        
        received_trades = []
        def unified_callback(trade):
            received_trades.append(trade)
        
        # Act: Subscribe to all trades
        stream.subscribe_to_all_trades(unified_callback)
        
        # Also subscribe to specific markets to generate traffic
        stream.subscribe_to_trades("BTC-USD", lambda t: None)
        stream.subscribe_to_trades("ETH-USD", lambda t: None)
        
        # Wait for trade data (allow up to 30 seconds)
        timeout = 30
        start_time = time.time()
        while len(received_trades) == 0 and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # Should have received trades from multiple markets
        assert len(received_trades) > 0
        
        # Check that we have trades from different markets
        markets = set(trade.get("market_id") for trade in received_trades)
        assert len(markets) > 0  # At least one market should be present
    
    def test_connect_establishes_real_dydx_websocket_connection(self):
        """Test that connect() establishes a real connection to dYdX mainnet WebSocket"""
        # Arrange: Create stream instance
        stream = DydxTradesStreamCallbacks()
        
        # Act: Connect to dYdX WebSocket
        result = stream.connect()
        
        # Assert: Connection should be established with real connection ID
        assert result is True
        assert stream.is_connected() is True
        assert stream.get_connection_id() is not None
        assert isinstance(stream.get_connection_id(), str)
        assert len(stream.get_connection_id()) > 0
    
    def test_multiple_market_subscriptions_work_independently(self):
        """Test that multiple market subscriptions work independently with separate callbacks"""
        # Arrange: Create and connect stream
        stream = DydxTradesStreamCallbacks()
        stream.connect()
        
        btc_trades = []
        eth_trades = []
        
        def btc_callback(trade):
            btc_trades.append(trade)
        
        def eth_callback(trade):
            eth_trades.append(trade)
        
        # Act: Subscribe to multiple markets
        stream.subscribe_to_trades("BTC-USD", btc_callback)
        stream.subscribe_to_trades("ETH-USD", eth_callback)
        
        # Wait for trade data from both markets
        timeout = 45
        start_time = time.time()
        while (len(btc_trades) == 0 or len(eth_trades) == 0) and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # Should have received trades for both markets
        assert len(btc_trades) > 0
        assert len(eth_trades) > 0
        
        # Verify trades are correctly routed
        for trade in btc_trades:
            assert trade["market_id"] == "BTC-USD"
        
        for trade in eth_trades:
            assert trade["market_id"] == "ETH-USD"
    
    def test_callback_receives_enriched_trade_data(self):
        """Test that callback receives enriched trade data with metadata"""
        # Arrange: Create and connect stream
        stream = DydxTradesStreamCallbacks()
        stream.connect()
        
        received_trades = []
        def trade_callback(trade):
            received_trades.append(trade)
        
        # Act: Subscribe and wait for trades
        stream.subscribe_to_trades("BTC-USD", trade_callback)
        
        timeout = 30
        start_time = time.time()
        while len(received_trades) == 0 and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # Assert: Trade should have enriched metadata
        assert len(received_trades) > 0
        trade = received_trades[0]
        
        # Check metadata fields
        assert "market_id" in trade
        assert "received_at" in trade
        assert "is_initial" in trade
        assert trade["market_id"] == "BTC-USD"
        assert isinstance(trade["received_at"], float)
        assert isinstance(trade["is_initial"], bool)
        
        # Check original trade fields are preserved
        assert "price" in trade
        assert "size" in trade
        assert "side" in trade
    
    def test_orderbook_callback_receives_complete_orderbook_state(self):
        """Test that orderbook callback receives complete orderbook state"""
        # Arrange: Create and connect stream
        stream = DydxTradesStreamCallbacks()
        stream.connect()
        
        received_orderbooks = []
        def orderbook_callback(orderbook):
            received_orderbooks.append(orderbook)
        
        # Act: Subscribe to orderbook
        stream.subscribe_to_orderbook("BTC-USD", orderbook_callback)
        
        # Wait for multiple orderbook updates
        timeout = 45
        start_time = time.time()
        while len(received_orderbooks) < 3 and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # Assert: Should have received multiple orderbook updates
        assert len(received_orderbooks) >= 1
        
        # Verify orderbook structure and content
        for orderbook in received_orderbooks:
            assert "bids" in orderbook
            assert "asks" in orderbook
            
            # Should have bids and asks
            assert len(orderbook["bids"]) > 0
            assert len(orderbook["asks"]) > 0
            
            # Check bid/ask structure
            for bid in orderbook["bids"]:
                assert "price" in bid
                assert "size" in bid
                assert float(bid["price"]) > 0
                assert float(bid["size"]) > 0
            
            for ask in orderbook["asks"]:
                assert "price" in ask
                assert "size" in ask
                assert float(ask["price"]) > 0
                assert float(ask["size"]) > 0
            
            # Bids should be sorted highest to lowest
            bid_prices = [float(bid["price"]) for bid in orderbook["bids"]]
            assert bid_prices == sorted(bid_prices, reverse=True)
            
            # Asks should be sorted lowest to highest
            ask_prices = [float(ask["price"]) for ask in orderbook["asks"]]
            assert ask_prices == sorted(ask_prices)
    
    def test_stream_handles_high_frequency_data_without_blocking(self):
        """Test that stream handles high-frequency data without blocking callbacks"""
        # Arrange: Create and connect stream
        stream = DydxTradesStreamCallbacks()
        stream.connect()
        
        trade_count = 0
        callback_times = []
        
        def fast_callback(trade):
            nonlocal trade_count
            trade_count += 1
            callback_times.append(time.time())
        
        # Act: Subscribe to high-frequency market
        stream.subscribe_to_trades("BTC-USD", fast_callback)
        
        # Wait for a significant number of trades
        timeout = 60
        start_time = time.time()
        while trade_count < 10 and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # Assert: Should have received multiple trades quickly
        assert trade_count >= 10
        
        # Verify callbacks are not blocking each other
        if len(callback_times) >= 2:
            # Most callbacks should happen within quick succession
            time_diffs = [callback_times[i+1] - callback_times[i] for i in range(len(callback_times)-1)]
            avg_time_diff = sum(time_diffs) / len(time_diffs)
            # Average time between callbacks should be reasonable (< 1 second)
            assert avg_time_diff < 1.0


# Additional integration tests for real-world scenarios
class TestDydxCallbacksIntegration:
    """Integration tests for callback-based dYdX stream with real market conditions"""
    
    def test_real_market_data_flow_with_callbacks(self):
        """Test complete real market data flow using callbacks"""
        # Arrange: Create stream and data collectors
        stream = DydxTradesStreamCallbacks()
        
        trades_data = []
        orderbook_data = []
        
        def collect_trades(trade):
            trades_data.append(trade)
        
        def collect_orderbook(orderbook):
            orderbook_data.append(orderbook)
        
        # Act: Connect and subscribe
        assert stream.connect() is True
        
        stream.subscribe_to_trades("BTC-USD", collect_trades)
        stream.subscribe_to_orderbook("BTC-USD", collect_orderbook)
        
        # Wait for substantial data
        timeout = 60
        start_time = time.time()
        while (len(trades_data) < 5 or len(orderbook_data) < 3) and time.time() - start_time < timeout:
            time.sleep(0.5)
        
        # Assert: Should have collected real market data
        assert len(trades_data) >= 5
        assert len(orderbook_data) >= 3
        
        # Verify data quality
        for trade in trades_data:
            assert float(trade["price"]) > 0
            assert float(trade["size"]) > 0
            assert trade["side"] in ["BUY", "SELL"]
        
        for orderbook in orderbook_data:
            assert len(orderbook["bids"]) > 0
            assert len(orderbook["asks"]) > 0
            
            # Market should be reasonable (ask > bid)
            best_bid = float(orderbook["bids"][0]["price"])
            best_ask = float(orderbook["asks"][0]["price"])
            assert best_ask > best_bid
    
    def test_callback_error_handling_doesnt_break_stream(self):
        """Test that callback errors don't break the stream"""
        # Arrange: Create stream with error-prone callback
        stream = DydxTradesStreamCallbacks()
        
        good_trades = []
        error_count = 0
        
        def error_callback(trade):
            nonlocal error_count
            error_count += 1
            if error_count <= 3:
                raise Exception("Simulated callback error")
            # After 3 errors, start working normally
            good_trades.append(trade)
        
        # Act: Connect and subscribe with error-prone callback
        assert stream.connect() is True
        stream.subscribe_to_trades("BTC-USD", error_callback)
        
        # Wait for errors to occur and then recovery
        timeout = 60
        start_time = time.time()
        while len(good_trades) < 1 and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # Assert: Stream should recover after callback errors
        assert error_count > 3  # Errors occurred
        assert len(good_trades) >= 1  # But stream recovered
        assert stream.is_connected()  # Connection still active
