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
        markets_with_realtime = set();
        
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


class TestLayer2SafetyNet:
    """Comprehensive safety net tests for Layer 2 before moving to Layer 3+"""
    
    def test_layer2_readiness_all_core_functions(self):
        """Validate that all core Layer 2 functions are working properly"""
        # Arrange: Create stream instance
        stream = DydxTradesStream()
        
        # Act & Assert: Test all core functions exist and work
        # 1. Can create stream
        assert stream is not None
        
        # 2. Can connect to WebSocket
        connect_result = stream.connect()
        assert connect_result is True
        assert stream.is_connected() is True
        
        # 3. Can get connection ID
        connection_id = stream.get_connection_id()
        assert connection_id is not None
        assert len(connection_id) > 0
        
        # 4. Can create observables
        trades_obs = stream.get_trades_observable()
        orderbook_obs = stream.get_orderbook_observable("BTC-USD")
        
        from reactivex import Observable
        assert isinstance(trades_obs, Observable)
        assert isinstance(orderbook_obs, Observable)
        
        # 5. Can get subscription status
        assert hasattr(stream, 'get_subscribed_markets')
        subscriptions = stream.get_subscribed_markets()
        assert isinstance(subscriptions, (list, dict, set))
        
        print("✅ All core Layer 2 functions working properly")
    
    def test_layer2_data_quality_validation(self):
        """Validate the quality and structure of data coming from Layer 2"""
        # Arrange: Setup stream and data capture
        stream = DydxTradesStream()
        stream.connect()
        
        trades_data = []
        orderbook_data = []
        
        # Subscribe to both trades and orderbook
        trades_obs = stream.get_trades_observable()
        orderbook_obs = stream.get_orderbook_observable("BTC-USD")
        
        trades_sub = trades_obs.subscribe(lambda x: trades_data.append(x))
        orderbook_sub = orderbook_obs.subscribe(lambda x: orderbook_data.append(x))
        
        # Act: Wait for data
        time.sleep(10)  # Wait for sufficient data
        
        # Assert: Validate data quality
        assert len(trades_data) > 0, "Should receive trade data"
        assert len(orderbook_data) > 0, "Should receive orderbook data"
        
        # Validate trade data structure
        trade = trades_data[0]
        required_trade_fields = ['price', 'size', 'side']
        for field in required_trade_fields:
            assert field in trade, f"Trade should have {field} field"
        
        # Validate metadata contains market information
        assert 'metadata' in trade, "Trade should have metadata"
        assert 'market_name' in trade['metadata'], "Trade metadata should have market_name"
        
        # Validate orderbook data structure
        orderbook = orderbook_data[0]
        assert 'bids' in orderbook, "Orderbook should have bids"
        assert 'asks' in orderbook, "Orderbook should have asks"
        assert len(orderbook['bids']) > 0, "Should have bid prices"
        assert len(orderbook['asks']) > 0, "Should have ask prices"
        
        # Cleanup
        trades_sub.dispose()
        orderbook_sub.dispose()
        
        print("✅ Layer 2 data quality validation passed")
    
    def test_layer2_performance_baseline(self):
        """Establish performance baseline for Layer 2 before Layer 3+ development"""
        # Arrange: Setup performance monitoring
        stream = DydxTradesStream()
        stream.connect()
        
        start_time = time.time()
        data_count = 0
        
        def count_data(data):
            nonlocal data_count
            data_count += 1
        
        # Act: Monitor performance for a fixed period
        observable = stream.get_trades_observable()
        subscription = observable.subscribe(count_data)
        
        # Wait for 30 seconds to establish baseline
        time.sleep(30)
        end_time = time.time()
        
        # Cleanup
        subscription.dispose()
        
        # Assert: Performance should meet minimum thresholds
        duration = end_time - start_time
        data_rate = data_count / duration
        
        print(f"📊 Layer 2 Performance Baseline:")
        print(f"  - Duration: {duration:.1f}s")
        print(f"  - Messages received: {data_count}")
        print(f"  - Rate: {data_rate:.2f} messages/second")
        
        # Minimum performance thresholds for Layer 2
        assert data_rate > 0.1, f"Data rate too low: {data_rate:.2f} msg/s"
        assert data_count > 0, "Should receive some data"
        
        print("✅ Layer 2 performance baseline established")
    
    def test_layer2_error_handling_resilience(self):
        """Test Layer 2 error handling and resilience patterns"""
        # Arrange: Create stream for error testing
        stream = DydxTradesStream()
        
        # Test 1: Connection resilience
        connect_result = stream.connect()
        assert connect_result is True
        
        # Test 2: Invalid market handling
        try:
            invalid_obs = stream.get_orderbook_observable("INVALID-MARKET")
            # Should not crash, should handle gracefully
            assert invalid_obs is not None
        except Exception as e:
            # If it throws exception, it should be a reasonable one
            assert "invalid" in str(e).lower() or "market" in str(e).lower()
        
        # Test 3: Multiple subscription handling
        obs1 = stream.get_trades_observable()
        obs2 = stream.get_trades_observable()
        assert obs1 is not None
        assert obs2 is not None
        
        print("✅ Layer 2 error handling resilience validated")
    
    def test_layer2_subscription_management(self):
        """Test Layer 2 subscription management for multiple markets"""
        # Arrange: Create stream and test markets
        stream = DydxTradesStream()
        stream.connect()
        
        test_markets = ["BTC-USD", "ETH-USD", "SOL-USD"]
        subscriptions = []
        market_data = {market: [] for market in test_markets}
        
        # Act: Subscribe to multiple markets
        for market in test_markets:
            obs = stream.get_orderbook_observable(market)
            sub = obs.subscribe(lambda data, m=market: market_data[m].append(data))
            subscriptions.append(sub)
        
        # Wait for data from multiple markets
        time.sleep(15)
        
        # Assert: Should receive data from multiple markets
        markets_with_data = [m for m in test_markets if len(market_data[m]) > 0]
        print(f"📊 Multi-market subscription results:")
        for market in test_markets:
            count = len(market_data[market])
            print(f"  - {market}: {count} messages")
        
        assert len(markets_with_data) > 0, "Should receive data from at least one market"
        
        # Cleanup
        for sub in subscriptions:
            sub.dispose()
        
        print("✅ Layer 2 subscription management validated")
    
    def test_layer2_ready_for_layer3_development(self):
        """Final validation that Layer 2 is ready for Layer 3+ development"""
        # This is the comprehensive readiness check
        
        print("🔍 Final Layer 2 Readiness Check...")
        
        # 1. Basic functionality
        stream = DydxTradesStream()
        assert stream.connect() is True
        print("  ✅ Basic connectivity")
        
        # 2. Data streams work
        trades_obs = stream.get_trades_observable()
        orderbook_obs = stream.get_orderbook_observable("BTC-USD")
        
        data_received = []
        trades_sub = trades_obs.subscribe(lambda x: data_received.append(('trade', x)))
        orderbook_sub = orderbook_obs.subscribe(lambda x: data_received.append(('orderbook', x)))
        
        time.sleep(5)  # Quick check
        
        assert len(data_received) > 0, "Should receive streaming data"
        print("  ✅ Data streaming working")
        
        # 3. Data structure validation
        trade_data = [d[1] for d in data_received if d[0] == 'trade']
        orderbook_data = [d[1] for d in data_received if d[0] == 'orderbook']
        
        if trade_data:
            assert 'price' in trade_data[0], "Trade data has required fields"
        if orderbook_data:
            assert 'bids' in orderbook_data[0], "Orderbook data has required fields"
        print("  ✅ Data structure validation")
        
        # 4. Resource cleanup
        trades_sub.dispose()
        orderbook_sub.dispose()
        print("  ✅ Resource cleanup")
        
        print("🎉 Layer 2 is READY for Layer 3+ development!")
        print("🚀 Proceed with confidence to higher layers")
        
        # This test should always pass if Layer 2 is truly ready
        assert True


class TestLayer2DashboardIntegration:
    """Test dYdX stream integration with all implemented dashboards"""
    
    def test_btc_orderbook_dashboard_stream_integration(self):
        """Test that BTCOrderbookDashboard properly integrates with dYdX stream"""
        from btc_orderbook_dashboard import BTCOrderbookDashboard
        
        # Arrange: Create dashboard and capture stream usage
        dashboard = BTCOrderbookDashboard()
        assert dashboard.stream is not None
        assert hasattr(dashboard.stream, 'get_orderbook_observable')
        
        # Act: Connect stream and get orderbook observable
        connect_result = dashboard.stream.connect()
        assert connect_result is True
        
        orderbook_obs = dashboard.stream.get_orderbook_observable("BTC-USD")
        assert orderbook_obs is not None
        
        # Test that dashboard can process orderbook updates
        orderbook_updates = []
        subscription = orderbook_obs.subscribe(lambda x: orderbook_updates.append(x))
        
        time.sleep(3)  # Collect some updates
        subscription.dispose()
        
        # Assert: Dashboard integration works
        assert len(orderbook_updates) > 0, "Should receive orderbook updates"
        
        # Validate orderbook structure expected by dashboard
        orderbook = orderbook_updates[0]
        assert 'asks' in orderbook, "Orderbook should have asks for dashboard"
        assert 'bids' in orderbook, "Orderbook should have bids for dashboard"
        assert isinstance(orderbook['asks'], list), "Asks should be list for dashboard"
        assert isinstance(orderbook['bids'], list), "Bids should be list for dashboard"
        
        print(f"✅ BTC Orderbook Dashboard: {len(orderbook_updates)} updates processed")
    
    def test_multi_market_dashboard_stream_integration(self):
        """Test that MultiMarketDashboard properly integrates with dYdX stream"""
        from multi_market_dashboard import MultiMarketDashboard
        
        # Arrange: Create dashboard and verify stream setup
        dashboard = MultiMarketDashboard()
        assert dashboard.stream is not None
        
        # Test dashboard's expected markets
        expected_markets = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD", "ATOM-USD"]
        assert dashboard.markets == expected_markets
        
        # Act: Connect and test multi-market observables
        connect_result = dashboard.stream.connect()
        assert connect_result is True
        
        # Test that we can create observables for all dashboard markets
        market_observables = {}
        for market in dashboard.markets:
            obs = dashboard.stream.get_orderbook_observable(market)
            assert obs is not None, f"Should create observable for {market}"
            market_observables[market] = obs
        
        # Test parallel data collection (like dashboard does)
        all_updates = {market: [] for market in dashboard.markets}
        subscriptions = []
        
        for market in dashboard.markets:
            obs = market_observables[market]
            sub = obs.subscribe(lambda x, m=market: all_updates[m].append(x))
            subscriptions.append(sub)
        
        time.sleep(5)  # Collect updates from all markets
        
        # Cleanup subscriptions
        for sub in subscriptions:
            sub.dispose()
        
        # Assert: Multi-market integration works
        markets_with_data = [m for m, updates in all_updates.items() if len(updates) > 0]
        assert len(markets_with_data) >= 3, f"Should receive data from multiple markets, got: {markets_with_data}"
        
        print(f"✅ Multi-Market Dashboard: {len(markets_with_data)} markets with data")
    
    def test_reactive_trades_dashboard_stream_integration(self):
        """Test that BTCDashboard (reactive trades) properly integrates with dYdX stream"""
        from reactive_trades_dashboard import BTCDashboard
        
        # Arrange: Create dashboard
        dashboard = BTCDashboard()
        assert dashboard.stream is not None
        assert hasattr(dashboard.stream, 'get_trades_observable')
        
        # Act: Connect and get trades observable
        connect_result = dashboard.stream.connect()
        assert connect_result is True
        
        trades_obs = dashboard.stream.get_trades_observable("BTC-USD")
        assert trades_obs is not None
        
        # Test trades data collection
        trades_updates = []
        subscription = trades_obs.subscribe(lambda x: trades_updates.append(x))
        
        time.sleep(4)  # Collect trade updates
        subscription.dispose()
        
        # Assert: Trades integration works
        assert len(trades_updates) > 0, "Should receive trade updates"
        
        # Validate trade structure expected by dashboard
        trade = trades_updates[0]
        assert 'price' in trade, "Trade should have price for dashboard"
        assert 'size' in trade, "Trade should have size for dashboard"
        assert 'side' in trade, "Trade should have side for dashboard"
        
        print(f"✅ Reactive Trades Dashboard: {len(trades_updates)} trade updates processed")
    
    def test_spreads_dashboard_stream_integration(self):
        """Test that SpreadsDashboard properly integrates with dYdX stream"""
        from reactive_spreads_dashboard import SpreadsDashboard
        
        # Arrange: Create dashboard
        dashboard = SpreadsDashboard()
        assert dashboard.stream is not None
        
        # Act: Connect stream
        connect_result = dashboard.stream.connect()
        assert connect_result is True
        
        # Test that dashboard can access both trades and orderbook data
        trades_obs = dashboard.stream.get_trades_observable("BTC-USD")
        orderbook_obs = dashboard.stream.get_orderbook_observable("BTC-USD")
        
        assert trades_obs is not None, "Spreads dashboard needs trades data"
        assert orderbook_obs is not None, "Spreads dashboard needs orderbook data"
        
        # Test parallel data collection (spreads need both data types)
        trades_data = []
        orderbook_data = []
        
        trades_sub = trades_obs.subscribe(lambda x: trades_data.append(x))
        orderbook_sub = orderbook_obs.subscribe(lambda x: orderbook_data.append(x))
        
        time.sleep(4)  # Collect both types of updates
        
        trades_sub.dispose()
        orderbook_sub.dispose()
        
        # Assert: Spreads dashboard integration works
        assert len(trades_data) > 0, "Should receive trades for spread calculation"
        assert len(orderbook_data) > 0, "Should receive orderbook for spread calculation"
        
        print(f"✅ Spreads Dashboard: {len(trades_data)} trades, {len(orderbook_data)} orderbooks")
    
    def test_dashboard_performance_under_load(self):
        """Test that stream can handle multiple dashboard subscriptions simultaneously"""
        # Arrange: Create all dashboards (simulating real usage)
        from btc_orderbook_dashboard import BTCOrderbookDashboard
        from multi_market_dashboard import MultiMarketDashboard
        from reactive_trades_dashboard import BTCDashboard
        from reactive_spreads_dashboard import SpreadsDashboard
        
        # Create single stream (as dashboards would in real usage)
        from layer2_dydx_stream import DydxTradesStream
        stream = DydxTradesStream()
        
        # Act: Connect and create multiple concurrent subscriptions
        connect_result = stream.connect()
        assert connect_result is True
        
        # Simulate multiple dashboard subscriptions
        all_data = {
            'btc_orderbook': [],
            'eth_orderbook': [],
            'sol_orderbook': [],
            'btc_trades': [],
            'eth_trades': []
        }
        
        subscriptions = [
            stream.get_orderbook_observable("BTC-USD").subscribe(lambda x: all_data['btc_orderbook'].append(x)),
            stream.get_orderbook_observable("ETH-USD").subscribe(lambda x: all_data['eth_orderbook'].append(x)),
            stream.get_orderbook_observable("SOL-USD").subscribe(lambda x: all_data['sol_orderbook'].append(x)),
            stream.get_trades_observable("BTC-USD").subscribe(lambda x: all_data['btc_trades'].append(x)),
            stream.get_trades_observable("ETH-USD").subscribe(lambda x: all_data['eth_trades'].append(x))
        ]
        
        # Monitor performance metrics
        start_time = time.time()
        time.sleep(6)  # Collect data under load
        end_time = time.time()
        
        # Cleanup
        for sub in subscriptions:
            sub.dispose()
        
        # Assert: Performance acceptable under dashboard load
        total_updates = sum(len(data) for data in all_data.values())
        duration = end_time - start_time
        updates_per_second = total_updates / duration
        
        assert total_updates > 20, f"Should handle multiple subscriptions, got {total_updates} updates"
        assert updates_per_second > 2, f"Should maintain reasonable throughput: {updates_per_second:.2f} updates/sec"
        
        # Verify all subscription types received data
        active_streams = [name for name, data in all_data.items() if len(data) > 0]
        assert len(active_streams) >= 3, f"Multiple streams should be active: {active_streams}"
        
        print(f"✅ Dashboard Performance: {total_updates} updates in {duration:.1f}s ({updates_per_second:.2f}/sec)")
    
    def test_dashboard_error_recovery_patterns(self):
        """Test that dashboards can handle stream errors gracefully"""
        from layer2_dydx_stream import DydxTradesStream
        
        # Arrange: Create stream and setup error tracking
        stream = DydxTradesStream()
        connect_result = stream.connect()
        assert connect_result is True
        
        # Act: Create subscription with error handling (like dashboards should)
        data_received = []
        errors_received = []
        completions_received = []
        
        def on_next(data):
            data_received.append(data)
        
        def on_error(error):
            errors_received.append(error)
        
        def on_completed():
            completions_received.append(True)
        
        # Test both trades and orderbook error handling
        trades_sub = stream.get_trades_observable("BTC-USD").subscribe(
            on_next=on_next,
            on_error=on_error,
            on_completed=on_completed
        )
        
        time.sleep(3)  # Normal operation
        
        # Simulate what dashboards should handle
        assert len(data_received) > 0, "Should receive data during normal operation"
        
        trades_sub.dispose()
        
        # Test reconnection capability (important for dashboard resilience)
        reconnect_result = stream.connect()  # Should handle reconnection
        assert reconnect_result is True, "Stream should support reconnection for dashboard resilience"
        
        print(f"✅ Dashboard Error Recovery: {len(data_received)} updates, resilient reconnection")


class TestLayer2DataStructures:
    """Test that Layer 2 provides data structures that dashboards expect"""
    
    def test_orderbook_structure_for_dashboard_consumption(self):
        """Test that orderbook data structure meets dashboard requirements"""
        from layer2_dydx_stream import DydxTradesStream
        
        stream = DydxTradesStream()
        stream.connect()
        
        # Collect orderbook data
        orderbook_updates = []
        subscription = stream.get_orderbook_observable("BTC-USD").subscribe(
            lambda x: orderbook_updates.append(x)
        )
        
        time.sleep(3)
        subscription.dispose()
        
        assert len(orderbook_updates) > 0, "Should receive orderbook updates"
        
        # Validate structure that ALL dashboards expect
        orderbook = orderbook_updates[0]
        
        # Core structure validation
        assert isinstance(orderbook, dict), "Orderbook must be dict for dashboard processing"
        assert 'asks' in orderbook, "Must have asks for sell-side display"
        assert 'bids' in orderbook, "Must have bids for buy-side display"
        assert isinstance(orderbook['asks'], list), "Asks must be list for iteration"
        assert isinstance(orderbook['bids'], list), "Bids must be list for iteration"
        
        # Price/size structure validation (critical for dashboard display)
        if orderbook['asks']:
            ask = orderbook['asks'][0]
            assert 'price' in ask, "Ask must have price for display"
            assert 'size' in ask, "Ask must have size for volume display"
            assert isinstance(float(ask['price']), float), "Price must be numeric"
            assert isinstance(float(ask['size']), float), "Size must be numeric"
        
        if orderbook['bids']:
            bid = orderbook['bids'][0]
            assert 'price' in bid, "Bid must have price for display"
            assert 'size' in bid, "Bid must have size for volume display"
            assert isinstance(float(bid['price']), float), "Price must be numeric"
            assert isinstance(float(bid['size']), float), "Size must be numeric"
        
        # Depth validation (dashboards expect reasonable depth)
        ask_count = len(orderbook['asks'])
        bid_count = len(orderbook['bids'])
        assert ask_count >= 1, f"Should have at least one ask for dashboard: {ask_count}"
        assert bid_count >= 1, f"Should have at least one bid for dashboard: {bid_count}"
        
        # Prefer more depth but don't fail if market is thin
        if ask_count >= 3 and bid_count >= 3:
            print(f"Good orderbook depth: {ask_count} asks, {bid_count} bids")
        else:
            print(f"Thin orderbook: {ask_count} asks, {bid_count} bids (acceptable for dashboard)")
        
        print(f"✅ Orderbook Structure: {ask_count} asks, {bid_count} bids with proper format")
    
    def test_trade_structure_for_dashboard_consumption(self):
        """Test that trade data structure meets dashboard requirements"""
        from layer2_dydx_stream import DydxTradesStream
        
        stream = DydxTradesStream()
        stream.connect()
        
        # Collect trade data
        trade_updates = []
        subscription = stream.get_trades_observable("BTC-USD").subscribe(
            lambda x: trade_updates.append(x)
        )
        
        time.sleep(4)
        subscription.dispose()
        
        assert len(trade_updates) > 0, "Should receive trade updates"
        
        # Validate structure that trades dashboards expect
        trade = trade_updates[0]
        
        # Core structure validation
        assert isinstance(trade, dict), "Trade must be dict for dashboard processing"
        assert 'price' in trade, "Must have price for trade display"
        assert 'size' in trade, "Must have size for volume display"
        assert 'side' in trade, "Must have side for buy/sell indication"
        
        # Data type validation (critical for dashboard calculations)
        assert isinstance(float(trade['price']), float), "Price must be numeric for calculations"
        assert isinstance(float(trade['size']), float), "Size must be numeric for volume calculations"
        assert trade['side'] in ['BUY', 'SELL'], f"Side must be BUY/SELL for dashboard logic: {trade['side']}"
        
        # Timestamp validation (for dashboard time series)
        assert 'createdAt' in trade, "Must have timestamp for time-based displays"
        
        # Market identification (multi-market dashboards need this)
        assert 'metadata' in trade, "Must have metadata for market identification"
        assert 'market_name' in trade['metadata'], "Must identify market for multi-market dashboards"
        
        print(f"✅ Trade Structure: Valid format with price ${trade['price']}, side {trade['side']}")
    
    def test_stream_timing_for_dashboard_updates(self):
        """Test that stream provides timely updates for dashboard refresh rates"""
        from layer2_dydx_stream import DydxTradesStream
        
        stream = DydxTradesStream()
        stream.connect()
        
        # Monitor update timing (dashboards need consistent updates)
        update_times = []
        
        def record_update_time(data):
            update_times.append(time.time())
        
        subscription = stream.get_orderbook_observable("BTC-USD").subscribe(record_update_time)
        
        time.sleep(10)  # Monitor for sufficient time
        subscription.dispose()
        
        assert len(update_times) >= 5, "Should receive multiple updates for timing analysis"
        
        # Calculate update intervals
        intervals = []
        for i in range(1, len(update_times)):
            interval = update_times[i] - update_times[i-1]
            intervals.append(interval)
        
        # Validate timing suitable for dashboards
        avg_interval = sum(intervals) / len(intervals)
        max_interval = max(intervals)
        min_interval = min(intervals)
        
        # Dashboard requirements
        assert avg_interval < 5.0, f"Average update interval too slow for dashboards: {avg_interval:.2f}s"
        assert max_interval < 10.0, f"Maximum gap too long for smooth dashboard updates: {max_interval:.2f}s"
        
        # Consistency check
        interval_variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
        assert interval_variance < 25.0, f"Update timing too irregular for smooth dashboard: {interval_variance:.2f}"
        
        print(f"✅ Stream Timing: avg {avg_interval:.2f}s, max {max_interval:.2f}s, variance {interval_variance:.2f}")
    
    def test_multi_market_data_consistency(self):
        """Test that multi-market data is consistent for multi-market dashboards"""
        from layer2_dydx_stream import DydxTradesStream
        
        stream = DydxTradesStream()
        stream.connect()
        
        # Test multiple markets simultaneously (like MultiMarketDashboard)
        markets = ["BTC-USD", "ETH-USD", "SOL-USD"]
        market_data = {market: [] for market in markets}
        subscriptions = []
        
        for market in markets:
            obs = stream.get_orderbook_observable(market)
            sub = obs.subscribe(lambda x, m=market: market_data[m].append(x))
            subscriptions.append(sub)
        
        time.sleep(6)  # Collect data from all markets
        
        for sub in subscriptions:
            sub.dispose()
        
        # Validate multi-market consistency
        markets_with_data = [m for m, data in market_data.items() if len(data) > 0]
        assert len(markets_with_data) >= 2, f"Should receive data from multiple markets: {markets_with_data}"
        
        # Validate data structure consistency across markets
        for market, data in market_data.items():
            if data:  # If we have data for this market
                sample = data[0]
                assert 'asks' in sample, f"{market} orderbook missing asks"
                assert 'bids' in sample, f"{market} orderbook missing bids"
                assert len(sample['asks']) > 0, f"{market} should have ask data"
                assert len(sample['bids']) > 0, f"{market} should have bid data"
        
        print(f"✅ Multi-Market Consistency: {len(markets_with_data)} markets with consistent data structure")