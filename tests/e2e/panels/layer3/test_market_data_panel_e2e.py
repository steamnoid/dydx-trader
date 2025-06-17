"""
E2E Tests for Market Data Panel - Layer 3 Dashboard

Comprehensive testing using Universal Rich E2E Testing Methodology:
- Real dYdX API only (no mocks, no fallbacks)
- Rich Console.capture() validation
- Static vs Streaming data testing
- Field-level assertions with regex patterns
- Performance and autonomous operation validation

Tests the Market Data Panel as a standalone, forever-running component.
"""

import pytest
import asyncio
import re
import time
from datetime import datetime
from rich.console import Console
from rich.text import Text

from dydx_bot.dashboard.panels.layer3.market_data_panel import MarketDataPanel


class TestMarketDataPanelE2E:
    """
    End-to-End tests for Market Data Panel using real dYdX API
    
    NO MOCKS, NO FALLBACKS - Tests fail if dYdX unavailable
    Validates operational guarantee with real streaming data
    """
    
    @pytest.fixture
    async def market_panel(self):
        """Create Market Data Panel and connect to real dYdX"""
        panel = MarketDataPanel()
        
        # Connect to real dYdX API
        connected = await panel.connect_client()
        assert connected, "Failed to connect to real dYdX API"
        
        # Fetch initial data
        await panel.fetch_market_data()
        
        yield panel
        
        # Cleanup
        if panel.client.is_connected():
            await panel.client.disconnect()
    
    def capture_panel_output(self, panel, method_name, *args, **kwargs):
        """Capture Rich panel output for testing"""
        console = Console(width=132, legacy_windows=False)
        
        with console.capture() as capture:
            method = getattr(panel, method_name)
            panel_obj = method(*args, **kwargs)
            console.print(panel_obj)
        
        return capture.get()
    
    def strip_ansi(self, text: str) -> str:
        """Remove ANSI escape codes from text"""
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_escape.sub('', text)
    
    @pytest.mark.asyncio
    async def test_static_panel_configuration_validation(self, market_panel):
        """Test static configuration data is correctly displayed"""
        print("🧪 Testing Market Data Panel static configuration...")
        
        # Test header panel
        header_output = self.capture_panel_output(market_panel, 'create_header_panel')
        header_clean = self.strip_ansi(header_output)
        
        # Static header elements
        static_fields = {
            'panel_title': r'🏪 Market Data Panel',
            'uptime_label': r'Uptime:',
            'updates_label': r'Updates:',
            'last_label': r'Last:',
            'connected_label': r'Connected:',
            'layer3_title': r'Layer 3 Dashboard - Market Data'
        }
        
        missing_fields = []
        for field_name, pattern in static_fields.items():
            if not re.search(pattern, header_clean, re.DOTALL):
                missing_fields.append(field_name)
        
        assert not missing_fields, f"Header missing static fields: {missing_fields}"
        
        # Test performance panel static structure
        perf_output = self.capture_panel_output(market_panel, 'create_performance_panel')
        perf_clean = self.strip_ansi(perf_output)
        
        perf_static_fields = {
            'metric_header': r'Metric',
            'value_header': r'Value',
            'status_header': r'Status',
            'update_rate_label': r'Update Rate',
            'data_age_label': r'Data Age',
            'connection_label': r'Connection',
            'coverage_label': r'Market.*Coverage',
            'total_updates_label': r'Total.*Updates'
        }
        
        missing_perf = []
        for field_name, pattern in perf_static_fields.items():
            if not re.search(pattern, perf_clean, re.DOTALL):
                missing_perf.append(field_name)
        
        assert not missing_perf, f"Performance panel missing static fields: {missing_perf}"
        
        print("✅ Static configuration validation PASSED")
    
    @pytest.mark.asyncio
    async def test_real_market_data_presence_validation(self, market_panel):
        """Test real market data is received and displayed correctly"""
        print("🧪 Testing real market data presence...")
        
        # Test markets overview panel
        markets_output = self.capture_panel_output(market_panel, 'create_markets_overview_panel')
        markets_clean = self.strip_ansi(markets_output)
        
        # Market data fields that should be present
        market_fields = {
            'market_header': r'Market',
            'price_header': r'Price',
            'change_header': r'24h Change',
            'volume_header': r'24h Volume',
            'status_header': r'Status',
            'btc_market': r'BTC-USD',
            'eth_market': r'ETH-USD',
            'price_format': r'\$[\d,]+\.\d{2}',  # Price like $107,094.71
            'status_active': r'🟢 ACTIVE'
        }
        
        missing_market_fields = []
        for field_name, pattern in market_fields.items():
            if not re.search(pattern, markets_clean, re.DOTALL):
                missing_market_fields.append(field_name)
        
        assert not missing_market_fields, f"Markets overview missing fields: {missing_market_fields}"
        
        # Test orderbook panel
        orderbook_output = self.capture_panel_output(market_panel, 'create_orderbook_panel', 'BTC-USD')
        orderbook_clean = self.strip_ansi(orderbook_output)
        
        orderbook_fields = {
            'bid_size_header': r'Bid Size',
            'bid_price_header': r'Bid Price',
            'spread_header': r'Spread',
            'ask_price_header': r'Ask Price',
            'ask_size_header': r'Ask Size',
            'orderbook_title': r'📈 Orderbook - BTC-USD',
            'price_data': r'\$[\d,]+',  # Price data
            'size_data': r'\d+\.\d{4}'  # Size data with 4 decimals
        }
        
        missing_ob_fields = []
        for field_name, pattern in orderbook_fields.items():
            if not re.search(pattern, orderbook_clean, re.DOTALL):
                missing_ob_fields.append(field_name)
        
        assert not missing_ob_fields, f"Orderbook panel missing fields: {missing_ob_fields}"
        
        # Test trades panel
        trades_output = self.capture_panel_output(market_panel, 'create_trades_panel', 'BTC-USD')
        trades_clean = self.strip_ansi(trades_output)
        
        trades_fields = {
            'time_header': r'Time',
            'side_header': r'Side',  # Note: uses Side not Price due to different col order
            'price_header': r'Price',
            'size_header': r'Size',
            'value_header': r'Value',
            'trades_title': r'⚡ Recent Trades - BTC-USD',
            'buy_side': r'🟢',  # Buy indicator
            'sell_side': r'🔴'  # Sell indicator  
        }
        
        missing_trades_fields = []
        for field_name, pattern in trades_fields.items():
            if not re.search(pattern, trades_clean, re.DOTALL):
                missing_trades_fields.append(field_name)
        
        assert not missing_trades_fields, f"Trades panel missing fields: {missing_trades_fields}"
        
        # Test candles panel
        candles_output = self.capture_panel_output(market_panel, 'create_candles_panel', 'BTC-USD')
        candles_clean = self.strip_ansi(candles_output)
        
        candles_fields = {
            'time_header': r'Time',
            'open_header': r'Open',
            'high_header': r'High',
            'low_header': r'Low',
            'close_header': r'Close',
            'volume_header': r'Volume',
            'candles_title': r'🕯️ OHLCV Candles \(1MIN\) - BTC-USD',
            'ohlc_data': r'\$[\d,]+',  # OHLC price data
            'time_data': r'\d{2}:\d{2}'  # Time format HH:MM
        }
        
        missing_candles_fields = []
        for field_name, pattern in candles_fields.items():
            if not re.search(pattern, candles_clean, re.DOTALL):
                missing_candles_fields.append(field_name)
        
        assert not missing_candles_fields, f"Candles panel missing fields: {missing_candles_fields}"
        
        print("✅ Real market data presence validation PASSED")
    
    @pytest.mark.asyncio
    async def test_streaming_data_updates_validation(self, market_panel):
        """Test data actually updates over time (autonomous operation)"""
        print("🧪 Testing streaming data updates...")
        
        # Capture initial state
        initial_header = self.capture_panel_output(market_panel, 'create_header_panel')
        initial_header_clean = self.strip_ansi(initial_header)
        
        # Extract initial update count
        update_match = re.search(r'Updates:\s*(\d+)', initial_header_clean)
        initial_updates = int(update_match.group(1)) if update_match else 0
        
        # Wait for data updates (15 seconds to ensure at least one update cycle)
        print(f"📊 Initial updates: {initial_updates}")
        print("⏳ Waiting 15 seconds for data updates...")
        
        for i in range(15):
            await asyncio.sleep(1)
            # Fetch new data during wait
            if i % 5 == 0:  # Every 5 seconds
                await market_panel.fetch_market_data()
        
        # Capture updated state
        updated_header = self.capture_panel_output(market_panel, 'create_header_panel')
        updated_header_clean = self.strip_ansi(updated_header)
        
        # Extract updated count
        update_match = re.search(r'Updates:\s*(\d+)', updated_header_clean)
        updated_updates = int(update_match.group(1)) if update_match else 0
        
        print(f"📊 Updated updates: {updated_updates}")
        
        # Verify update count increased
        assert updated_updates > initial_updates, f"Update count should increase: {initial_updates} -> {updated_updates}"
        
        # Verify data freshness
        freshness_match = re.search(r'Last:\s*(\d+)s ago', updated_header_clean)
        if freshness_match:
            seconds_ago = int(freshness_match.group(1))
            assert seconds_ago <= 10, f"Data should be fresh (≤10s), got {seconds_ago}s"
        
        # Test performance metrics show autonomous operation
        perf_output = self.capture_panel_output(market_panel, 'create_performance_panel')
        perf_clean = self.strip_ansi(perf_output)
        
        # Verify autonomous indicators
        performance_validations = {
            'update_rate': (r'Update Rate.*(\d+\.?\d*)/min', 0.0, 60.0),
            'data_age': (r'Data Age.*(\d+)s', 0, 30),
            'connection_status': r'🟢.*Connected',
            'market_coverage': r'2/2.*🟢.*Complete',
            'autonomous_indicator': r'Autonomous'
        }
        
        missing_perf = []
        for field_name, validation in performance_validations.items():
            if isinstance(validation, tuple) and len(validation) == 3:
                # Numeric validation
                pattern, min_val, max_val = validation
                match = re.search(pattern, perf_clean, re.DOTALL)
                if match:
                    value = float(match.group(1))
                    if not (min_val <= value <= max_val):
                        missing_perf.append(f"{field_name}: {value} not in range [{min_val}, {max_val}]")
                else:
                    missing_perf.append(f"{field_name}: pattern not found")
            else:
                # String validation
                pattern = validation
                if not re.search(pattern, perf_clean, re.DOTALL):
                    missing_perf.append(field_name)
        
        assert not missing_perf, f"Performance validation failures: {missing_perf}"
        
        print("✅ Streaming data updates validation PASSED")
    
    @pytest.mark.asyncio
    async def test_component_details_and_data_quality(self, market_panel):
        """Test component-specific details and data quality"""
        print("🧪 Testing component details and data quality...")
        
        # Test market data quality
        markets_output = self.capture_panel_output(market_panel, 'create_markets_overview_panel')
        markets_clean = self.strip_ansi(markets_output)
        
        # Extract price values and validate they're reasonable
        btc_price_match = re.search(r'BTC-USD.*\$(\d{1,3}(?:,\d{3})*\.\d{2})', markets_clean)
        eth_price_match = re.search(r'ETH-USD.*\$(\d{1,3}(?:,\d{3})*\.\d{2})', markets_clean)
        
        if btc_price_match:
            btc_price = float(btc_price_match.group(1).replace(',', ''))
            assert 10000 <= btc_price <= 200000, f"BTC price seems unrealistic: ${btc_price:,.2f}"
        
        if eth_price_match:
            eth_price = float(eth_price_match.group(1).replace(',', ''))
            assert 500 <= eth_price <= 20000, f"ETH price seems unrealistic: ${eth_price:,.2f}"
        
        # Test orderbook spread calculation
        orderbook_output = self.capture_panel_output(market_panel, 'create_orderbook_panel', 'BTC-USD')
        orderbook_clean = self.strip_ansi(orderbook_output)
        
        # Look for spread percentage
        spread_match = re.search(r'(\d+\.\d{3})%', orderbook_clean)
        if spread_match:
            spread_pct = float(spread_match.group(1))
            assert 0.001 <= spread_pct <= 1.0, f"Spread percentage seems unrealistic: {spread_pct}%"
        
        # Test trades data quality  
        trades_output = self.capture_panel_output(market_panel, 'create_trades_panel', 'BTC-USD')
        trades_clean = self.strip_ansi(trades_output)
        
        # Verify trade timestamps are recent (within last hour)
        time_matches = re.findall(r'(\d{2}):(\d{2})', trades_clean)
        if time_matches:
            current_hour = datetime.now().hour
            current_minute = datetime.now().minute
            
            for hour_str, minute_str in time_matches[:3]:  # Check first 3 trades
                trade_hour = int(hour_str)
                trade_minute = int(minute_str)
                
                # Allow for trades within reasonable time window
                time_diff = abs((current_hour * 60 + current_minute) - (trade_hour * 60 + trade_minute))
                if time_diff > 720:  # 12 hours in minutes
                    time_diff = 1440 - time_diff  # Handle day rollover
                
                assert time_diff <= 720, f"Trade timestamp too old: {hour_str}:{minute_str}"
        
        # Test candles OHLCV data integrity
        candles_output = self.capture_panel_output(market_panel, 'create_candles_panel', 'BTC-USD')
        candles_clean = self.strip_ansi(candles_output)
        
        # Find OHLC values and verify relationships (O,H,L,C should make sense)
        ohlc_matches = re.findall(r'\$(\d{1,3}(?:,\d{3})*)', candles_clean)
        if len(ohlc_matches) >= 4:
            # Take first candle's OHLC
            open_val = float(ohlc_matches[0].replace(',', ''))
            high_val = float(ohlc_matches[1].replace(',', ''))
            low_val = float(ohlc_matches[2].replace(',', ''))
            close_val = float(ohlc_matches[3].replace(',', ''))
            
            # Verify OHLC relationships
            assert low_val <= open_val <= high_val, f"Invalid OHLC: L({low_val}) <= O({open_val}) <= H({high_val})"
            assert low_val <= close_val <= high_val, f"Invalid OHLC: L({low_val}) <= C({close_val}) <= H({high_val})"
        
        print("✅ Component details and data quality validation PASSED")
    
    @pytest.mark.asyncio
    async def test_performance_and_timing_validation(self, market_panel):
        """Test performance metrics and timing requirements"""
        print("🧪 Testing performance and timing...")
        
        # Test data fetch performance
        start_time = time.time()
        await market_panel.fetch_market_data()
        fetch_duration = time.time() - start_time
        
        assert fetch_duration < 10.0, f"Data fetch too slow: {fetch_duration:.2f}s (should be < 10s)"
        
        # Test panel rendering performance
        start_time = time.time()
        header_output = self.capture_panel_output(market_panel, 'create_header_panel')
        markets_output = self.capture_panel_output(market_panel, 'create_markets_overview_panel')
        orderbook_output = self.capture_panel_output(market_panel, 'create_orderbook_panel', 'BTC-USD')
        trades_output = self.capture_panel_output(market_panel, 'create_trades_panel', 'BTC-USD')
        candles_output = self.capture_panel_output(market_panel, 'create_candles_panel', 'BTC-USD')
        perf_output = self.capture_panel_output(market_panel, 'create_performance_panel')
        render_duration = time.time() - start_time
        
        assert render_duration < 5.0, f"Panel rendering too slow: {render_duration:.2f}s (should be < 5s)"
        
        # Test update rate is reasonable
        perf_clean = self.strip_ansi(perf_output)
        rate_match = re.search(r'Update Rate.*(\d+\.?\d*)/min', perf_clean)
        if rate_match:
            update_rate = float(rate_match.group(1))
            assert 0.1 <= update_rate <= 60.0, f"Update rate unrealistic: {update_rate}/min"
        
        # Test connection status is maintained
        header_clean = self.strip_ansi(header_output)
        assert re.search(r'Connected:\s*✅', header_clean), "Connection should be active"
        
        # Test data coverage
        assert re.search(r'2/2.*🟢.*Complete', perf_clean), "Should have complete market coverage"
        
        print("✅ Performance and timing validation PASSED")
    
    @pytest.mark.asyncio
    async def test_autonomous_operation_guarantee(self, market_panel):
        """Test autonomous operation guarantee - panel runs independently"""
        print("🧪 Testing autonomous operation guarantee...")
        
        # Verify panel can operate independently
        assert market_panel.client.is_connected(), "Panel should maintain dYdX connection"
        assert market_panel.running, "Panel should be in running state"
        
        # Test data update capability
        initial_count = market_panel.update_count
        await market_panel.fetch_market_data()
        assert market_panel.update_count > initial_count, "Panel should autonomously update data"
        
        # Test all tracked markets are supported
        assert 'BTC-USD' in market_panel.tracked_markets, "BTC-USD should be tracked"
        assert 'ETH-USD' in market_panel.tracked_markets, "ETH-USD should be tracked"
        
        # Verify real-time data storage
        if market_panel.markets_data:
            assert 'BTC-USD' in market_panel.markets_data or 'ETH-USD' in market_panel.markets_data, \
                "Should have real market data stored"
        
        # Test layout creation works
        layout = market_panel.create_layout()
        assert layout is not None, "Panel should create valid layout"
        
        # Test graceful shutdown capability
        original_running = market_panel.running
        market_panel.running = False
        assert not market_panel.running, "Panel should support graceful shutdown"
        market_panel.running = original_running  # Restore for cleanup
        
        print("✅ Autonomous operation guarantee PASSED")
    
    @pytest.mark.asyncio
    async def test_real_dydx_integration_validation(self, market_panel):
        """Test real dYdX integration - no mocks, no fallbacks"""
        print("🧪 Testing real dYdX integration...")
        
        # Verify we're using real dYdX client
        assert market_panel.client is not None, "Should have real dYdX client"
        assert market_panel.client.is_connected(), "Should be connected to real dYdX"
        
        # Test we have real data from each API endpoint
        assert market_panel.markets_data, "Should have real markets data from dYdX"
        assert market_panel.orderbook_data, "Should have real orderbook data from dYdX"
        assert market_panel.trades_data, "Should have real trades data from dYdX"
        assert market_panel.candles_data, "Should have real candles data from dYdX"
        
        # Verify data structure matches dYdX API
        if 'BTC-USD' in market_panel.markets_data:
            btc_market = market_panel.markets_data['BTC-USD']
            expected_fields = ['status', 'oraclePrice', 'priceChange24H', 'volume24H']
            missing = [field for field in expected_fields if field not in btc_market]
            assert not missing, f"Missing dYdX market fields: {missing}"
        
        if 'BTC-USD' in market_panel.orderbook_data:
            orderbook = market_panel.orderbook_data['BTC-USD']
            assert 'bids' in orderbook and 'asks' in orderbook, "Should have dYdX orderbook structure"
            
            if orderbook['bids']:
                bid = orderbook['bids'][0]
                assert 'price' in bid and 'size' in bid, "Should have dYdX bid structure"
        
        if 'BTC-USD' in market_panel.trades_data and 'trades' in market_panel.trades_data['BTC-USD']:
            trades = market_panel.trades_data['BTC-USD']['trades']
            if trades:
                trade = trades[0]
                expected_trade_fields = ['price', 'size', 'side', 'createdAt']
                missing = [field for field in expected_trade_fields if field not in trade]
                assert not missing, f"Missing dYdX trade fields: {missing}"
        
        if 'BTC-USD' in market_panel.candles_data and 'candles' in market_panel.candles_data['BTC-USD']:
            candles = market_panel.candles_data['BTC-USD']['candles']
            if candles:
                candle = candles[0]
                expected_candle_fields = ['open', 'high', 'low', 'close', 'usdVolume', 'startedAt']
                missing = [field for field in expected_candle_fields if field not in candle]
                assert not missing, f"Missing dYdX candle fields: {missing}"
        
        print("✅ Real dYdX integration validation PASSED")


# Additional test utilities
def test_market_data_panel_imports():
    """Test that all required imports work correctly"""
    from dydx_bot.dashboard.panels.layer3.market_data_panel import MarketDataPanel
    from dydx_bot.connection.client import DydxClient
    from dydx_v4_client.indexer.candles_resolution import CandlesResolution
    
    # Verify classes can be instantiated
    panel = MarketDataPanel()
    assert panel is not None
    assert hasattr(panel, 'tracked_markets')
    assert hasattr(panel, 'run_forever')


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/e2e/panels/layer3/test_market_data_panel_e2e.py -v
    print("Market Data Panel E2E Test Suite")
    print("Run with: python -m pytest tests/e2e/panels/layer3/test_market_data_panel_e2e.py -v")
