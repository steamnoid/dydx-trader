"""
Layer 2 dYdX Trades Stream Tests
Following STRICT TDD methodology - testing real dYdX WebSocket integration with recording capability
"""
import pytest
import time
from layer2_dydx_stream import DydxTradesStream


class TestDydxTradesStream:
    """Test Layer 2 dYdX trades streaming functionality with WebSocket and recording"""
    
    def test_can_create_dydx_trades_stream(self):
        """Test that we can create a DydxTradesStream instance"""
        # Arrange: No setup needed for this basic test
        
        # Act: Create the stream instance
        stream = DydxTradesStream()
        
        # Assert: Should create valid instance
        assert stream is not None
        assert hasattr(stream, 'connect')
        assert hasattr(stream, 'get_trades_observable')
    
    def test_connect_initializes_websocket_connection(self):
        """Test that connect() initializes WebSocket connection to dYdX"""
        # Arrange: Create stream instance
        stream = DydxTradesStream()
        
        # Act: Connect to dYdX WebSocket
        result = stream.connect()
        
        # Assert: Connection should be established
        assert result is True
        assert stream.is_connected() is True
    
    def test_get_trades_observable_returns_rxpy_observable(self):
        """Test that get_trades_observable() returns a valid RxPY Observable"""
        # Arrange: Create and connect stream
        stream = DydxTradesStream()
        stream.connect()
        
        # Act: Get the trades Observable (defaults to BTC-USD)
        observable = stream.get_trades_observable()
        
        # Assert: Should return a valid RxPY Observable
        from reactivex import Observable
        assert isinstance(observable, Observable)
    
    def test_connect_establishes_real_dydx_websocket_connection(self):
        """Test that connect() establishes a real connection to dYdX testnet WebSocket"""
        # Arrange: Create stream instance
        stream = DydxTradesStream()
        
        # Act: Connect to dYdX WebSocket
        result = stream.connect()
        
        # Assert: Connection should be established and connection_id should be set
        assert result is True
        assert stream.is_connected() is True
        assert stream.get_connection_id() is not None  # This will require real WebSocket connection
        assert len(stream.get_connection_id()) > 0
    
    def test_trades_observable_emits_real_trade_data(self):
        """Test that the trades observable emits real trade data from dYdX when subscribed to"""
        # Arrange: Create and connect stream
        stream = DydxTradesStream()
        connect_result = stream.connect()
        assert connect_result is True
        
        observable = stream.get_trades_observable()
        
        # Arrange: Setup to capture emitted data
        received_data = []
        completed = []
        errors = []
        
        def on_next(data):
            received_data.append(data)
        
        def on_error(error):
            errors.append(error)
        
        def on_completed():
            completed.append(True)
        
        # Act: Subscribe to the observable for a short period
        subscription = observable.subscribe(
            on_next=on_next,
            on_error=on_error,
            on_completed=on_completed
        )
        
        # Wait for some data to arrive (timeout after 15 seconds for trades)
        import time
        max_wait = 15
        wait_time = 0
        while len(received_data) == 0 and len(errors) == 0 and wait_time < max_wait:
            time.sleep(0.1)
            wait_time += 0.1
        
        # Cleanup
        subscription.dispose()
        
        # Assert: Should have received at least one trade data point
        assert len(errors) == 0, f"Observable emitted error: {errors}"
        assert len(received_data) > 0, "Observable should emit at least one trade data point"
        
        # Assert: Validate structure of emitted trade data
        trade_data = received_data[0]
        assert isinstance(trade_data, dict), "Emitted data should be a dictionary"
        
        # Expected fields for trade data (based on dYdX v4 trades API documentation)
        expected_fields = ['id', 'side', 'size', 'price', 'createdAt']
        
        for field in expected_fields:
            assert field in trade_data, f"Trade data should contain '{field}' field"
        
        # Verify that trade includes metadata
        assert "metadata" in trade_data, "Trade should include metadata"
        metadata = trade_data["metadata"]
        
        # Verify metadata structure
        assert "market_name" in metadata, "Metadata should include market_name"
        assert "performance_metrics" in metadata, "Metadata should include performance_metrics"
        assert "tracking_info" in metadata, "Metadata should include tracking_info"
        
        # Verify performance metrics
        perf_metrics = metadata["performance_metrics"]
        assert "timestamp_received" in perf_metrics, "Performance metrics should include timestamp_received"
        assert "timestamp_processed" in perf_metrics, "Performance metrics should include timestamp_processed"
        assert "is_initial_trade" in perf_metrics, "Performance metrics should include is_initial_trade"
        assert "message_source" in perf_metrics, "Performance metrics should include message_source"
        assert "latency_ms" in perf_metrics, "Performance metrics should include latency_ms"
        
        # Verify tracking info
        tracking_info = metadata["tracking_info"]
        assert "session_id" in tracking_info, "Tracking info should include session_id"
        assert "message_sequence" in tracking_info, "Tracking info should include message_sequence"
        
        print(f"Successfully verified metadata in trade: {metadata['market_name']}")
        print(f"Message source: {perf_metrics['message_source']}")
        print(f"Message sequence: {tracking_info['message_sequence']}")

    def test_trades_observable_emits_more_than_initial_count(self):
        """Test that the trades observable emits more trades than the initial subscription confirmation count"""
        # Arrange: Create and connect stream
        stream = DydxTradesStream()
        connect_result = stream.connect()
        assert connect_result is True
        
        observable = stream.get_trades_observable()
        
        # Arrange: Setup to capture emitted data
        received_data = []
        errors = []
        
        def on_next(data):
            received_data.append(data)
        
        def on_error(error):
            errors.append(error)
        
        # Act: Subscribe to the observable for longer to capture both initial and new trades
        subscription = observable.subscribe(
            on_next=on_next,
            on_error=on_error
        )
        
        # Wait for initial subscription confirmation and some additional data
        import time
        max_wait = 30  # Wait up to 30 seconds for trades (longer than basic test)
        wait_time = 0
        initial_count_captured = False
        
        while len(errors) == 0 and wait_time < max_wait:
            time.sleep(0.5)
            wait_time += 0.5
            
            # Check if we have the initial trade count
            if not initial_count_captured and stream.get_initial_trade_count() > 0:
                initial_count_captured = True
                print(f"DEBUG: Initial trade count from subscription: {stream.get_initial_trade_count()}")
            
            # If we have initial count and more trades than that, we can stop
            if initial_count_captured and len(received_data) > stream.get_initial_trade_count():
                print(f"DEBUG: Received {len(received_data)} trades, more than initial {stream.get_initial_trade_count()}")
                break
        
        # Cleanup
        subscription.dispose()
        
        # Assert: Should have received at least the initial trade count
        assert len(errors) == 0, f"Observable emitted error: {errors}"
        initial_trade_count = stream.get_initial_trade_count("BTC-USD")  # Specify market
        assert initial_trade_count > 0, "Should have received trades in subscription confirmation"
        
        # Assert: Should have received more trades than the initial count (proving real-time data)
        assert len(received_data) > initial_trade_count, (
            f"Should emit more than {initial_trade_count} initial trades, "
            f"but only received {len(received_data)} total trades"
        )
        
        # Verify that all trades include metadata
        for i, trade in enumerate(received_data[:3]):  # Check first 3 trades
            assert "metadata" in trade, f"Trade {i} should include metadata"
            metadata = trade["metadata"]
            assert "market_name" in metadata, f"Trade {i} metadata should include market_name"
            assert "performance_metrics" in metadata, f"Trade {i} metadata should include performance_metrics"
            assert "tracking_info" in metadata, f"Trade {i} metadata should include tracking_info"
        
        # Verify initial vs real-time message sources
        initial_trades = [t for t in received_data if t["metadata"]["performance_metrics"]["is_initial_trade"]]
        realtime_trades = [t for t in received_data if not t["metadata"]["performance_metrics"]["is_initial_trade"]]
        
        print(f"Received {len(initial_trades)} initial trades and {len(realtime_trades)} real-time trades")
        assert len(initial_trades) == initial_trade_count, "Initial trade count should match metadata"
        assert len(realtime_trades) > 0, "Should have received some real-time trades"
    
    def test_can_subscribe_to_multiple_markets_simultaneously(self):
        """Test that we can subscribe to multiple markets through the same WebSocket connection"""
        # Arrange: Create and connect stream
        stream = DydxTradesStream()
        connect_result = stream.connect()
        assert connect_result is True
        
        # Arrange: Setup to capture data from multiple markets
        btc_data = []
        eth_data = []
        errors = []
        
        def on_btc_next(data):
            btc_data.append(data)
        
        def on_eth_next(data):
            eth_data.append(data)
        
        def on_error(error):
            errors.append(error)
        
        # Act: Subscribe to both BTC-USD and ETH-USD
        btc_observable = stream.get_trades_observable("BTC-USD")
        eth_observable = stream.get_trades_observable("ETH-USD")
        
        btc_subscription = btc_observable.subscribe(
            on_next=on_btc_next,
            on_error=on_error
        )
        
        eth_subscription = eth_observable.subscribe(
            on_next=on_eth_next, 
            on_error=on_error
        )
        
        # Wait for data to arrive from both markets
        import time
        max_wait = 20  # Wait up to 20 seconds for both markets
        wait_time = 0
        
        while (len(btc_data) == 0 or len(eth_data) == 0) and len(errors) == 0 and wait_time < max_wait:
            time.sleep(0.5)
            wait_time += 0.5
        
        # Cleanup
        btc_subscription.dispose()
        eth_subscription.dispose()
        
        # Assert: Should have received data from both markets
        assert len(errors) == 0, f"Observable emitted errors: {errors}"
        assert len(btc_data) > 0, "Should have received BTC-USD trade data"
        assert len(eth_data) > 0, "Should have received ETH-USD trade data"
        
        # Assert: Verify market metadata is correct
        btc_trade = btc_data[0]
        eth_trade = eth_data[0]
        
        assert btc_trade["metadata"]["market_name"] == "BTC-USD", "BTC trade should have correct market name"
        assert eth_trade["metadata"]["market_name"] == "ETH-USD", "ETH trade should have correct market name"
        
        # Assert: Verify subscribed markets tracking
        subscribed_markets = stream.get_subscribed_markets()
        # Note: Markets might be unsubscribed due to dispose(), so we check that subscription worked
        assert len(btc_data) > 0 and len(eth_data) > 0, "Both markets should have provided data"
        
        print(f"Successfully received {len(btc_data)} BTC trades and {len(eth_data)} ETH trades")

    def test_all_trades_observable_emits_unified_stream(self):
        """Test that get_all_trades_observable() emits trades from all markets in one stream"""
        # Arrange: Create and connect stream
        stream = DydxTradesStream()
        connect_result = stream.connect()
        assert connect_result is True
        
        # Arrange: Setup to capture unified data
        all_trades_data = []
        errors = []
        
        def on_next(data):
            all_trades_data.append(data)
        
        def on_error(error):
            errors.append(error)
        
        # Act: Subscribe to unified observable for all markets
        all_trades_observable = stream.get_all_trades_observable()
        subscription = all_trades_observable.subscribe(
            on_next=on_next,
            on_error=on_error
        )
        
        # Wait for data from multiple markets
        import time
        max_wait = 25  # Wait up to 25 seconds for multiple markets
        wait_time = 0
        
        # Collect unique market names to verify we get multiple markets
        unique_markets = set()
        
        while len(errors) == 0 and wait_time < max_wait:
            time.sleep(0.5)
            wait_time += 0.5
            
            # Track unique markets we've received
            for trade in all_trades_data:
                if "metadata" in trade and "market_name" in trade["metadata"]:
                    unique_markets.add(trade["metadata"]["market_name"])
            
            # If we have trades from at least 2 different markets, we can stop
            if len(unique_markets) >= 2 and len(all_trades_data) >= 5:
                break
        
        # Cleanup
        subscription.dispose()
        
        # Assert: Should have received trades from multiple markets
        assert len(errors) == 0, f"Observable emitted errors: {errors}"
        assert len(all_trades_data) > 0, "Should have received trade data from unified stream"
        assert len(unique_markets) >= 2, f"Should receive trades from multiple markets, got: {unique_markets}"
        
        # Assert: All trades should have correct metadata structure
        for trade in all_trades_data[:3]:  # Check first 3 trades
            assert "metadata" in trade, "All trades should include metadata"
            assert "market_name" in trade["metadata"], "All trades should include market_name"
            assert trade["metadata"]["market_name"] in ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD", "AVAX-USD"], \
                f"Market name should be one of expected markets: {trade['metadata']['market_name']}"
        
        print(f"Successfully received {len(all_trades_data)} total trades from {len(unique_markets)} markets: {unique_markets}")

    def test_receives_subscription_confirmation_for_each_market(self):
        """Test that for each subscribed market, we receive both initial trades (from subscription confirmation) and real-time trades (from channel updates)"""
        # Arrange: Create and connect stream
        stream = DydxTradesStream()
        connect_result = stream.connect()
        assert connect_result is True
        
        # Arrange: Markets to subscribe to (3 high-volume markets for comprehensive testing)
        markets = ["BTC-USD", "ETH-USD", "SOL-USD"]
        all_trades = []
        errors = []
        
        def on_next(data):
            # Capture all trade data (from both confirmation and real-time updates)
            all_trades.append(data)
            print(f"DEBUG: Received trade for {data.get('metadata', {}).get('market_name', 'unknown')} - "
                  f"Initial: {data.get('metadata', {}).get('performance_metrics', {}).get('is_initial_trade', False)}")
        
        def on_error(error):
            errors.append(error)
        
        # Act: Subscribe to multiple markets individually
        subscriptions = []
        for market in markets:
            observable = stream.get_trades_observable(market)
            subscription = observable.subscribe(
                on_next=on_next,
                on_error=on_error
            )
            subscriptions.append(subscription)
        
        # Wait for trade data from all markets (both initial and real-time)
        # Run until all markets have both types or pytest timeout hits
        wait_time = 0
        
        markets_with_initial = set()
        markets_with_realtime = set()
        
        while len(errors) == 0:
            time.sleep(0.5)
            wait_time += 0.5
            
            # Track which markets have provided initial and real-time trade data
            for trade in all_trades:
                if "metadata" in trade and "market_name" in trade["metadata"]:
                    market = trade["metadata"]["market_name"]
                    is_initial = trade["metadata"]["performance_metrics"]["is_initial_trade"]
                    
                    if is_initial:
                        markets_with_initial.add(market)
                    else:
                        markets_with_realtime.add(market)
            
            # Check if all markets have both types of trades
            all_markets_have_both = True
            for market in markets:
                if market not in markets_with_initial or market not in markets_with_realtime:
                    all_markets_have_both = False
                    break
            
            if all_markets_have_both:
                print(f"DEBUG: All {len(markets)} markets have both initial and real-time trades, stopping at {wait_time}s")
                break
            
            # Log progress every 10 seconds
            if wait_time % 10 == 0:
                print(f"DEBUG: Wait time: {wait_time}s - Initial: {markets_with_initial}, Real-time: {markets_with_realtime}")
        
        # Cleanup
        for subscription in subscriptions:
            subscription.dispose()
        
        # Assert: Should have received trade data without errors
        assert len(errors) == 0, f"Observable emitted errors: {errors}"
        assert len(all_trades) > 0, "Should have received trade data"
        
        # Organize trades by market and type for detailed analysis
        market_trades = {}
        for trade in all_trades:
            if "metadata" in trade and "market_name" in trade["metadata"]:
                market = trade["metadata"]["market_name"]
                if market not in market_trades:
                    market_trades[market] = {"initial": [], "realtime": []}
                
                if trade["metadata"]["performance_metrics"]["is_initial_trade"]:
                    market_trades[market]["initial"].append(trade)
                else:
                    market_trades[market]["realtime"].append(trade)
        
        # Detailed logging for debugging
        print(f"\n=== TRADE BREAKDOWN BY MARKET ===")
        for market in markets:
            initial_count = len(market_trades.get(market, {}).get("initial", []))
            realtime_count = len(market_trades.get(market, {}).get("realtime", []))
            print(f"{market}: {initial_count} initial trades, {realtime_count} real-time trades")
        
        # Assert: All subscribed markets should have provided trade data
        for market in markets:
            assert market in market_trades, f"Should receive trade data for {market}"
            
            # Assert: Each market should have initial trades (from subscription confirmation)
            initial_trades = market_trades[market]["initial"]
            assert len(initial_trades) > 0, \
                f"Market {market} should have initial trades from subscription confirmation, got {len(initial_trades)}"
            
            # Verify initial trades have correct metadata
            for trade in initial_trades:
                metadata = trade["metadata"]
                assert metadata["performance_metrics"]["is_initial_trade"] is True, \
                    f"Initial trade for {market} should have is_initial_trade=True"
                assert metadata["performance_metrics"]["message_source"] == "subscription_confirmation", \
                    f"Initial trade for {market} should have message_source='subscription_confirmation'"
        
        # Assert: All markets should have real-time trades (proving comprehensive live data flow)
        markets_with_realtime_trades = [
            market for market in markets 
            if len(market_trades.get(market, {}).get("realtime", [])) > 0
        ]
        
        assert len(markets_with_realtime_trades) == len(markets), \
            f"All {len(markets)} markets should have real-time trades. Got real-time trades from {len(markets_with_realtime_trades)}/{len(markets)} markets: {markets_with_realtime_trades}"
        
        # For markets that have real-time trades, verify their metadata
        for market in markets_with_realtime_trades:
            realtime_trades = market_trades[market]["realtime"]
            for trade in realtime_trades[:3]:  # Check first 3 real-time trades
                metadata = trade["metadata"]
                assert metadata["performance_metrics"]["is_initial_trade"] is False, \
                    f"Real-time trade for {market} should have is_initial_trade=False"
                assert metadata["performance_metrics"]["message_source"] == "real_time_update", \
                    f"Real-time trade for {market} should have message_source='real_time_update'"
        
        # Assert: Verify that we have sufficient total trade volume across all markets
        total_initial_trades = sum(len(market_trades.get(market, {}).get("initial", [])) for market in markets)
        total_realtime_trades = sum(len(market_trades.get(market, {}).get("realtime", [])) for market in markets)
        
        print(f"\n=== SUMMARY ===")
        print(f"Total markets subscribed: {len(markets)}")
        print(f"Markets with data: {len(market_trades)}")
        print(f"Markets with initial trades: {len([m for m in markets if len(market_trades.get(m, {}).get('initial', [])) > 0])}")
        print(f"Markets with real-time trades: {len(markets_with_realtime_trades)}")
        print(f"Total initial trades: {total_initial_trades}")
        print(f"Total real-time trades: {total_realtime_trades}")
        
        assert total_initial_trades > 0, "Should have received initial trades from subscription confirmations"
        assert total_realtime_trades > 0, "Should have received real-time trades proving live data stream"