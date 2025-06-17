"""
E2E Test for Connection Status Panel

Tests the connection status panel with real dYdX API connection.
Uses Universal Rich E2E Testing Methodology for 100% operational guarantee.
"""

import pytest
import asyncio
import re
import time
from dydx_bot.dashboard.panels.layer3.connection_status_panel import ConnectionStatusPanel


class TestConnectionStatusPanelE2E:
    """E2E tests for Connection Status Panel with real API"""
    
    @pytest.mark.asyncio
    async def test_connection_status_static_data(self):
        """Test static configuration and connection data"""
        panel = ConnectionStatusPanel("BTC-USD")
        
        try:
            await panel.initialize()
            
            # Capture Rich output
            rendered_panel = panel.render()
            
            # Use Rich console to capture output
            with panel.console.capture() as capture:
                panel.console.print(rendered_panel)
            
            rich_output = capture.get()
            
            print(f"\n📊 Connection Status Static Data Check:")
            print("=" * 80)
            print(rich_output)
            print("=" * 80)
            
            # Static data validation - these should always be present
            static_fields = {
                'network_name': r'dYdX Mainnet',
                'market_id': r'Market ID.*BTC-USD',
                'connection_header': r'Connection Status',
                'component_column': r'Component',
                'status_column': r'Status',
                'details_column': r'Details',
                'metrics_column': r'Metrics'
            }
            
            missing_fields = []
            for field_name, pattern in static_fields.items():
                if not re.search(pattern, rich_output):
                    missing_fields.append(field_name)
            
            assert not missing_fields, f"Missing static fields: {missing_fields}"
            
            # Status indicators validation
            status_indicators = ["✅", "❌"]
            found_indicators = [ind for ind in status_indicators if ind in rich_output]
            assert len(found_indicators) > 0, "No status indicators found"
            
            print("✅ Static data validation passed")
            
        finally:
            await panel.shutdown()
    
    @pytest.mark.asyncio
    async def test_connection_status_streaming_data(self):
        """Test streaming metrics that update over time"""
        panel = ConnectionStatusPanel("BTC-USD")
        
        try:
            await panel.initialize()
            
            # Capture initial state
            panel.update_metrics()
            rendered_panel1 = panel.render()
            
            with panel.console.capture() as capture1:
                panel.console.print(rendered_panel1)
            initial_output = capture1.get()
            
            # Wait and update metrics
            await asyncio.sleep(2)
            panel.update_metrics()
            
            # Capture updated state
            rendered_panel2 = panel.render()
            
            with panel.console.capture() as capture2:
                panel.console.print(rendered_panel2)
            updated_output = capture2.get()
            
            print(f"\n📊 Connection Status Streaming Data Check:")
            print("=" * 80)
            print("INITIAL OUTPUT:")
            print(initial_output[:500])
            print("\nUPDATED OUTPUT:")
            print(updated_output[:500])
            print("=" * 80)
            
            # Verify data actually changed (streaming data must update)
            assert initial_output != updated_output, "Connection metrics not updating - streaming failed"
            
            # Extract uptime values to verify they increased
            uptime_pattern = r'Uptime: ([\d.]+)s'
            
            initial_uptime_match = re.search(uptime_pattern, initial_output)
            updated_uptime_match = re.search(uptime_pattern, updated_output)
            
            assert initial_uptime_match, "Initial uptime not found"
            assert updated_uptime_match, "Updated uptime not found"
            
            initial_uptime = float(initial_uptime_match.group(1))
            updated_uptime = float(updated_uptime_match.group(1))
            
            assert updated_uptime > initial_uptime, f"Uptime not increasing: {initial_uptime} -> {updated_uptime}"
            
            # Extract event count to verify it increased
            events_pattern = r'Events: (\d+)'
            
            initial_events_match = re.search(events_pattern, initial_output)
            updated_events_match = re.search(events_pattern, updated_output)
            
            assert initial_events_match, "Initial events count not found"
            assert updated_events_match, "Updated events count not found"
            
            initial_events = int(initial_events_match.group(1))
            updated_events = int(updated_events_match.group(1))
            
            assert updated_events > initial_events, f"Events not increasing: {initial_events} -> {updated_events}"
            
            print("✅ Streaming data validation passed")
            
        finally:
            await panel.shutdown()
    
    @pytest.mark.asyncio
    async def test_connection_status_component_details(self):
        """Test specific component status details"""
        panel = ConnectionStatusPanel("BTC-USD")
        
        try:
            await panel.initialize()
            
            # Capture Rich output
            rendered_panel = panel.render()
            
            with panel.console.capture() as capture:
                panel.console.print(rendered_panel)
            
            rich_output = capture.get()
            
            print(f"\n📊 Connection Status Component Details Check:")
            print("=" * 80)
            print(rich_output)
            print("=" * 80)
            
            # Component-specific validations - handle multiline Rich table cells
            component_patterns = {
                'network_connected': r'Network.*✅',
                'market_active': r'Market.*✅',
                'websocket_streaming': r'WebSocket.*✅',
                'rest_api_ready': r'REST API.*✅',
                'performance_limits': r'Performance.*✅'
            }
            
            missing_components = []
            for component_name, pattern in component_patterns.items():
                # Use DOTALL flag to match across line boundaries
                if not re.search(pattern, rich_output, re.DOTALL):
                    missing_components.append(component_name)
            
            assert not missing_components, f"Missing component status: {missing_components}"
            
            # Detailed field validation
            detail_patterns = {
                'indexer_socket': r'IndexerSocket active',
                'indexer_client': r'IndexerClient ready',
                'latency_target': r'< 25ms',
                'memory_cpu_limits': r'Memory < 512MB, CPU < 25%'
            }
            
            missing_details = []
            for detail_name, pattern in detail_patterns.items():
                if not re.search(pattern, rich_output):
                    missing_details.append(detail_name)
            
            assert not missing_details, f"Missing detail fields: {missing_details}"
            
            print("✅ Component details validation passed")
            
        finally:
            await panel.shutdown()
    
    @pytest.mark.asyncio 
    async def test_connection_status_performance_metrics(self):
        """Test performance and timing metrics"""
        panel = ConnectionStatusPanel("BTC-USD")
        
        try:
            await panel.initialize()
            
            # Update metrics multiple times to test performance
            for i in range(3):
                panel.update_metrics()
                await asyncio.sleep(0.5)
            
            # Capture Rich output
            rendered_panel = panel.render()
            
            with panel.console.capture() as capture:
                panel.console.print(rendered_panel)
            
            rich_output = capture.get()
            
            print(f"\n📊 Connection Status Performance Metrics Check:")
            print("=" * 80)
            print(rich_output)
            print("=" * 80)
            
            # Performance metrics validation
            perf_patterns = {
                'uptime_present': r'Uptime: [\d.]+s',
                'events_count': r'Events: \d+',
                'latency_metric': r'Latency: < 25ms',
                'rate_metric': r'Rate: ~\d+/sec',
                'target_metric': r'Target: < 25ms',
                'last_update': r'Last Update: \d{2}:\d{2}:\d{2} UTC'
            }
            
            missing_metrics = []
            for metric_name, pattern in perf_patterns.items():
                if not re.search(pattern, rich_output):
                    missing_metrics.append(metric_name)
            
            assert not missing_metrics, f"Missing performance metrics: {missing_metrics}"
            
            # Validate event count is reasonable (should be > 0 after updates)
            events_match = re.search(r'Events: (\d+)', rich_output)
            assert events_match, "Events count not found"
            
            events_count = int(events_match.group(1))
            assert events_count > 0, f"Events count should be > 0, got {events_count}"
            
            print("✅ Performance metrics validation passed")
            
        finally:
            await panel.shutdown()


if __name__ == "__main__":
    # Run individual tests for debugging
    import sys
    
    async def run_test():
        test_instance = TestConnectionStatusPanelE2E()
        
        print("🧪 Running Connection Status Panel E2E Tests...")
        
        try:
            print("\n1️⃣ Testing static data...")
            await test_instance.test_connection_status_static_data()
            
            print("\n2️⃣ Testing streaming data...")
            await test_instance.test_connection_status_streaming_data()
            
            print("\n3️⃣ Testing component details...")
            await test_instance.test_connection_status_component_details()
            
            print("\n4️⃣ Testing performance metrics...")
            await test_instance.test_connection_status_performance_metrics()
            
            print("\n🎉 All Connection Status Panel E2E tests passed!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            sys.exit(1)
    
    asyncio.run(run_test())
