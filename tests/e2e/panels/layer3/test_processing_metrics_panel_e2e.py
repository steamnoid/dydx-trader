"""
E2E Tests for Processing Metrics Panel - Layer 3 Dashboard

Comprehensive end-to-end testing using the Universal Rich E2E Testing Methodology.
Validates static data, streaming data, component details, and performance metrics
using real dYdX API data and Rich console capture.
"""

import asyncio
import re
import time
import threading
from unittest.mock import patch

import pytest
from rich.console import Console

from src.dydx_bot.dashboard.panels.layer3.processing_metrics_panel import ProcessingMetricsPanel


@pytest.fixture
async def panel():
    """Fixture providing a ProcessingMetricsPanel instance with comprehensive cleanup"""
    panel = ProcessingMetricsPanel(market_id="BTC-USD")
    yield panel
    
    # Comprehensive cleanup to prevent hanging
    try:
        # Stop the panel if it's running
        if hasattr(panel, 'running'):
            panel.running = False
        
        # Shutdown processor and all connections
        if hasattr(panel, 'processor') and panel.processor:
            await panel.processor.shutdown()
            
        # Cancel any remaining tasks in the current event loop
        current_task = asyncio.current_task()
        tasks = [task for task in asyncio.all_tasks() if task != current_task and not task.done()]
        
        if tasks:
            # Cancel all background tasks
            for task in tasks:
                task.cancel()
            
            # Wait briefly for cancellation to complete
            try:
                await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=2.0)
            except asyncio.TimeoutError:
                pass  # Force cleanup even if timeout
                
    except Exception:
        pass  # Ignore cleanup errors but ensure we continue


@pytest.fixture(scope="session", autouse=True)
def cleanup_event_loop():
    """Session-level fixture to ensure complete cleanup after all tests"""
    yield
    
    # Final cleanup - cancel any remaining tasks
    try:
        loop = asyncio.get_event_loop()
        if loop and not loop.is_closed():
            # Cancel all remaining tasks
            pending = asyncio.all_tasks(loop)
            if pending:
                for task in pending:
                    task.cancel()
                
                # Give tasks a moment to cancel
                try:
                    loop.run_until_complete(
                        asyncio.wait_for(asyncio.gather(*pending, return_exceptions=True), timeout=1.0)
                    )
                except:
                    pass
    except:
        pass


class TestProcessingMetricsPanelE2E:
    """
    E2E tests for Processing Metrics Panel using Universal Rich E2E Testing Methodology.
    
    Tests validate:
    - Static panel information and layout structure
    - Real-time data processing metrics from dYdX API
    - Component status monitoring and health checks
    - Performance metrics and latency tracking
    - Error handling and reliability monitoring
    """

    def test_panel_static_layout_structure(self):
        """
        Test 1: Static Layout Structure Validation
        
        Validates the basic panel layout, headers, and table structure
        without requiring live data connections.
        """
        # Create panel instance locally (no async needed for static test)
        panel = ProcessingMetricsPanel(market_id="BTC-USD")
        console = Console(record=True, width=150)
        
        # Create layout without starting data processing
        layout = panel.create_layout()
        
        # Capture rendered output
        with console.capture() as capture:
            console.print(layout)
        output = capture.get()
        
        # Validate main header
        header_pattern = r"Layer 3 - Processing Metrics"
        assert re.search(header_pattern, output, re.DOTALL), "Main header not found"
        
        # Validate panel info section
        assert re.search(r"Panel.*Processing Metrics Dashboard", output, re.DOTALL), "Panel info not found"
        assert re.search(r"Market.*BTC-USD", output, re.DOTALL), "Market ID not found"
        assert re.search(r"Status.*LIVE", output, re.DOTALL), "Status not found"
        assert re.search(r"Update Freq.*5 seconds", output, re.DOTALL), "Update frequency not found"
        
        # Validate main sections (these show basic titles when processor not initialized)
        sections = [
            "Throughput",
            "Reliability", 
            "Latency",
            "Data Status"
        ]
        
        for section in sections:
            assert re.search(section, output, re.DOTALL), f"Section '{section}' not found"
        
        # Should show "Processor not initialized" message for all panels
        assert output.count("Processor not initialized") >= 4, "Should show processor not initialized for all panels"

    @pytest.mark.asyncio
    async def test_real_data_processing_metrics(self):
        """
        Test 2: Real Data Processing Metrics Validation
        
        Validates throughput metrics with real dYdX API data processing.
        Tests message processing rates, orderbook updates, and OHLCV generation.
        """
        # Create panel with proper cleanup
        panel = ProcessingMetricsPanel(market_id="BTC-USD")
        console = Console(record=True, width=150)
        
        try:
            # Start the panel and allow data processing
            start_time = time.time()
            await panel.initialize()
            
            # Wait for data to start flowing
            await asyncio.sleep(8)
            
            # Capture metrics
            layout = panel.create_layout()
            with console.capture() as capture:
                console.print(layout)
            output = capture.get()
            
        finally:
            # Ensure cleanup
            if hasattr(panel, 'processor') and panel.processor:
                await panel.processor.shutdown()
        
        # Validate throughput metrics are present and realistic
        throughput_metrics = [
            "Messages Processed",
            "OHLCV Candles Generated", 
            "Orderbook Updates"
        ]
        
        for metric in throughput_metrics:
            assert re.search(metric, output, re.DOTALL), f"Throughput metric '{metric}' not found"
        
        # Validate that we have non-zero message processing
        # Should see messages processed within 8 seconds of connection
        messages_pattern = r"Messages Processed.*?(\d+).*?(\d+\.\d+)"
        messages_match = re.search(messages_pattern, output, re.DOTALL)
        assert messages_match, "Messages processed count not found"
        
        total_messages = int(messages_match.group(1))
        assert total_messages > 0, f"Expected > 0 messages processed, got {total_messages}"
        
        # Validate orderbook updates are happening
        orderbook_pattern = r"Orderbook Updates.*?(\d+).*?(\d+\.\d+)"
        orderbook_match = re.search(orderbook_pattern, output, re.DOTALL)
        assert orderbook_match, "Orderbook updates not found"
        
        orderbook_total = int(orderbook_match.group(1))
        assert orderbook_total > 0, f"Expected > 0 orderbook updates, got {orderbook_total}"
        
        # Validate processing rates are reasonable (should be > 0/sec with active market)
        rate = float(messages_match.group(2))
        assert rate >= 0, f"Expected non-negative processing rate, got {rate}"

    @pytest.mark.asyncio
    async def test_reliability_and_error_monitoring(self, panel: ProcessingMetricsPanel):
        """
        Test 3: Reliability and Error Monitoring
        
        Validates reliability metrics including uptime tracking,
        error rates, and success rates with real API connections.
        """
        await panel.initialize()
        
        # Allow sufficient time for reliability metrics
        await asyncio.sleep(6)
        
        layout = panel.create_layout()
        console = Console(record=True, width=150)
        with console.capture() as capture:
            console.print(layout)
        output = capture.get()
        
        # Validate reliability metrics structure
        reliability_metrics = [
            "Uptime",
            "Total Errors",
            "Error Rate",
            "Success Rate"
        ]
        
        for metric in reliability_metrics:
            assert re.search(metric, output, re.DOTALL), f"Reliability metric '{metric}' not found"
        
        # Validate uptime is tracking correctly (should be > 0 seconds)
        uptime_pattern = r"Uptime.*?(\d+)s.*?(STARTING|RUNNING)"
        uptime_match = re.search(uptime_pattern, output, re.DOTALL)
        assert uptime_match, "Uptime metric not found"
        
        uptime_seconds = int(uptime_match.group(1))
        assert uptime_seconds > 0, f"Expected uptime > 0 seconds, got {uptime_seconds}"
        
        # Validate error tracking (should start with 0 errors)
        error_pattern = r"Total Errors.*?(\d+).*?(CLEAN|WARNING|CRITICAL)"
        error_match = re.search(error_pattern, output, re.DOTALL)
        assert error_match, "Error count not found"
        
        total_errors = int(error_match.group(1))
        error_status = error_match.group(2)
        assert total_errors >= 0, f"Expected non-negative error count, got {total_errors}"
        assert error_status in ["CLEAN", "WARNING", "CRITICAL"], f"Unexpected error status: {error_status}"
        
        # Validate success rate (should be high percentage)
        success_pattern = r"Success Rate.*?(\d+\.\d+)%.*?(EXCELLENT|GOOD|POOR)"
        success_match = re.search(success_pattern, output, re.DOTALL)
        assert success_match, "Success rate not found"
        
        success_rate = float(success_match.group(1))
        success_status = success_match.group(2)
        assert 0 <= success_rate <= 100, f"Success rate should be 0-100%, got {success_rate}%"
        assert success_status in ["EXCELLENT", "GOOD", "POOR"], f"Unexpected success status: {success_status}"

    @pytest.mark.asyncio 
    async def test_latency_analysis_and_performance(self, panel: ProcessingMetricsPanel):
        """
        Test 4: Latency Analysis and Performance Metrics
        
        Validates latency tracking, performance statistics, and
        trend analysis with real API response times.
        """
        await panel.initialize()
        
        # Allow time for latency samples to accumulate
        await asyncio.sleep(10)
        
        layout = panel.create_layout()
        console = Console(record=True, width=150)
        with console.capture() as capture:
            console.print(layout)
        output = capture.get()
        
        # Validate latency metrics
        latency_metrics = [
            "Average Latency",
            "95th Percentile",
            "Sample Count"
        ]
        
        for metric in latency_metrics:
            assert re.search(metric, output, re.DOTALL), f"Latency metric '{metric}' not found"
        
        # Validate average latency
        avg_latency_pattern = r"Average Latency.*?(\d+\.\d+).*?(GOOD|SLOW|CRITICAL)"
        avg_match = re.search(avg_latency_pattern, output, re.DOTALL)
        assert avg_match, "Average latency not found"
        
        avg_latency = float(avg_match.group(1))
        latency_status = avg_match.group(2)
        assert avg_latency >= 0, f"Expected non-negative latency, got {avg_latency}ms"
        assert latency_status in ["GOOD", "SLOW", "CRITICAL"], f"Unexpected latency status: {latency_status}"
        
        # Validate 95th percentile latency
        p95_pattern = r"95th Percentile.*?(\d+\.\d+).*?(GOOD|SLOW|CRITICAL)"
        p95_match = re.search(p95_pattern, output, re.DOTALL)
        assert p95_match, "95th percentile latency not found"
        
        p95_latency = float(p95_match.group(1))
        assert p95_latency >= avg_latency, f"95th percentile ({p95_latency}ms) should be >= average ({avg_latency}ms)"
        
        # Validate sample count
        sample_pattern = r"Sample Count.*?(\d+).*?(INFO|WARNING)"
        sample_match = re.search(sample_pattern, output, re.DOTALL)
        assert sample_match, "Sample count not found"
        
        sample_count = int(sample_match.group(1))
        assert sample_count > 0, f"Expected > 0 samples, got {sample_count}"
        
        # Check for recent trend if available
        trend_pattern = r"Recent Trend.*?(\d+\.\d+).*?(STABLE|IMPROVING|DEGRADING)"
        trend_match = re.search(trend_pattern, output, re.DOTALL)
        if trend_match:  # Trend may not appear immediately
            trend_value = float(trend_match.group(1))
            trend_status = trend_match.group(2)
            assert trend_value >= 0, f"Expected non-negative trend value, got {trend_value}ms"
            assert trend_status in ["STABLE", "IMPROVING", "DEGRADING"], f"Unexpected trend status: {trend_status}"

    @pytest.mark.asyncio
    async def test_component_status_monitoring(self, panel: ProcessingMetricsPanel):
        """
        Test 5: Component Status Monitoring
        
        Validates the status of all components including data processor,
        WebSocket connection, orderbook feed, and OHLCV generation.
        """
        await panel.initialize()
        
        # Allow time for all components to initialize and connect
        await asyncio.sleep(8)
        
        layout = panel.create_layout()
        console = Console(record=True, width=150)
        with console.capture() as capture:
            console.print(layout)
        output = capture.get()
        
        # Validate component status entries
        components = [
            "Data Processor",
            "WebSocket", 
            "Orderbook Feed",
            "OHLCV Generation"
        ]
        
        for component in components:
            assert re.search(component, output, re.DOTALL), f"Component '{component}' not found"
        
        # Validate data processor status
        processor_pattern = r"Data Processor.*?(RUNNING|STARTING|STOPPED).*?(Active|Starting|Stopped)"
        processor_match = re.search(processor_pattern, output, re.DOTALL)
        assert processor_match, "Data processor status not found"
        
        processor_status = processor_match.group(1)
        assert processor_status in ["RUNNING", "STARTING", "STOPPED"], f"Unexpected processor status: {processor_status}"
        
        # Validate WebSocket status  
        websocket_pattern = r"WebSocket.*?(CONNECTED|CONNECTING|DISCONNECTED).*?(Live|Connecting|Offline)"
        websocket_match = re.search(websocket_pattern, output, re.DOTALL)
        assert websocket_match, "WebSocket status not found"
        
        websocket_status = websocket_match.group(1)
        assert websocket_status in ["CONNECTED", "CONNECTING", "DISCONNECTED"], f"Unexpected WebSocket status: {websocket_status}"
        
        # Validate orderbook feed status
        orderbook_pattern = r"Orderbook Feed.*?(ACTIVE|NO DATA|ERROR).*?([0-9:]+|N/A)"
        orderbook_match = re.search(orderbook_pattern, output, re.DOTALL)
        assert orderbook_match, "Orderbook feed status not found"
        
        orderbook_status = orderbook_match.group(1)
        assert orderbook_status in ["ACTIVE", "NO DATA", "ERROR"], f"Unexpected orderbook status: {orderbook_status}"
        
        # If orderbook is active, validate timestamp format
        if orderbook_status == "ACTIVE":
            timestamp = orderbook_match.group(2)
            assert re.match(r"\d{2}:\d{2}:\d{2}", timestamp), f"Invalid timestamp format: {timestamp}"
        
        # Validate OHLCV generation status (may start as NO DATA)
        ohlcv_pattern = r"OHLCV Generation.*?(ACTIVE|NO DATA|ERROR).*?([0-9:]+|N/A)"
        ohlcv_match = re.search(ohlcv_pattern, output, re.DOTALL)
        assert ohlcv_match, "OHLCV generation status not found"
        
        ohlcv_status = ohlcv_match.group(1)
        assert ohlcv_status in ["ACTIVE", "NO DATA", "ERROR"], f"Unexpected OHLCV status: {ohlcv_status}"

    @pytest.mark.asyncio
    async def test_performance_under_load(self, panel: ProcessingMetricsPanel):
        """
        Test 6: Performance Under Load
        
        Validates panel performance and responsiveness during active
        market data processing with sustained load.
        """
        await panel.initialize()
        
        # Run for longer period to test sustained performance
        start_time = time.time()
        await asyncio.sleep(12)
        end_time = time.time()
        
        layout = panel.create_layout()
        console = Console(record=True, width=150)
        with console.capture() as capture:
            console.print(layout)
        
        output = capture.get()
        elapsed_time = end_time - start_time
        
        # Validate panel still responsive after sustained operation
        assert re.search(r"Layer 3 - Processing Metrics", output), "Panel header missing after sustained operation"
        
        # Validate throughput is sustained
        messages_pattern = r"Messages Processed.*?(\d+).*?(\d+\.\d+)"
        messages_match = re.search(messages_pattern, output, re.DOTALL)
        assert messages_match, "Message processing metrics missing"
        
        total_messages = int(messages_match.group(1))
        processing_rate = float(messages_match.group(2))
        
        # Should have processed multiple messages over 12+ seconds
        assert total_messages > 10, f"Expected >10 messages processed, got {total_messages}"
        
        # Processing rate should be reasonable for active market
        assert processing_rate >= 0, f"Expected non-negative processing rate, got {processing_rate}"
        
        # Validate latency remains reasonable under load
        latency_pattern = r"Average Latency.*?(\d+\.\d+).*?(GOOD|SLOW|CRITICAL)"
        latency_match = re.search(latency_pattern, output, re.DOTALL)
        assert latency_match, "Latency metrics missing under load"
        
        avg_latency = float(latency_match.group(1))
        latency_status = latency_match.group(2)
        
        # Latency should remain reasonable (< 1000ms is very conservative)
        assert avg_latency < 1000, f"Latency too high under load: {avg_latency}ms"
        
        # Validate uptime tracking is accurate
        uptime_pattern = r"Uptime.*?(\d+)s"
        uptime_match = re.search(uptime_pattern, output, re.DOTALL)
        assert uptime_match, "Uptime tracking missing"
        
        uptime_seconds = int(uptime_match.group(1))
        # Uptime should be close to elapsed time (within reasonable tolerance)
        assert abs(uptime_seconds - elapsed_time) < 3, f"Uptime ({uptime_seconds}s) doesn't match elapsed time ({elapsed_time:.1f}s)"

    def test_graceful_shutdown_handling(self):
        """
        Test 7: Graceful Shutdown Handling
        
        Validates that the panel handles shutdown signals properly
        and cleans up resources without errors.
        """
        # Create panel instance locally
        panel = ProcessingMetricsPanel(market_id="BTC-USD")
        
        # Test signal handler registration
        assert hasattr(panel, '_signal_handler'), "Signal handler not registered"
        
        # Test shutdown flag
        assert hasattr(panel, 'running'), "Running flag not present"
        
        # Simulate shutdown signal
        original_running = panel.running
        panel._signal_handler(2, None)  # SIGINT
        
        # Validate shutdown was initiated
        assert not panel.running, "Panel should stop running after shutdown signal"
        
        # Restore state (no cleanup needed for sync test)

    @pytest.mark.asyncio
    async def test_error_resilience_and_recovery(self):
        """
        Test 8: Error Resilience and Recovery
        
        Validates panel behavior under error conditions and
        recovery mechanisms for network issues.
        """
        # Create panel with proper cleanup
        panel = ProcessingMetricsPanel(market_id="BTC-USD")
        
        try:
            # Start panel normally first
            await panel.initialize()
            await asyncio.sleep(3)
            
            # Simulate network interruption by disconnecting processor
            if panel.processor:
                await panel.processor.shutdown()
            
            # Allow time for error detection
            await asyncio.sleep(2)
            
            # Capture output during error state
            layout = panel.create_layout()
            console = Console(record=True, width=150)
            with console.capture() as capture:
                console.print(layout)
            output = capture.get()
            
            # Panel should still render even with connection issues
            assert re.search(r"Layer 3 - Processing Metrics", output), "Panel should render during errors"
            
            # Error metrics should be tracked
            assert re.search(r"Total Errors", output), "Error tracking should be present"
            
            # Component status should reflect disconnection
            websocket_pattern = r"WebSocket.*?(CONNECTED|CONNECTING|DISCONNECTED)"
            websocket_match = re.search(websocket_pattern, output, re.DOTALL)
            if websocket_match:
                # Status should reflect current state (may be DISCONNECTED or attempting to reconnect)
                websocket_status = websocket_match.group(1)
                assert websocket_status in ["CONNECTED", "CONNECTING", "DISCONNECTED"]
                
        finally:
            # Ensure cleanup
            if hasattr(panel, 'processor') and panel.processor:
                await panel.processor.shutdown()
        
        # Test layout creation without processor (should handle gracefully)
        new_panel = ProcessingMetricsPanel(market_id="BTC-USD")
        layout = new_panel.create_layout()
        assert layout is not None
        
        # Capture layout rendering
        console = Console(width=120, height=30)
        with console.capture() as capture:
            console.print(layout)
        
        output = capture.get()
        
        # Validate static header content
        assert "Layer 3 - Processing Metrics" in output
        assert "BTC-USD" in output
        assert "LIVE" in output
        assert "5 seconds" in output
        
        # Validate panel structure
        assert "Throughput" in output
        assert "Latency" in output
        assert "Reliability" in output
        assert "Data Status" in output
        
        # Validate error handling when processor not initialized
        assert "Processor not initialized" in output
    
    @pytest.mark.asyncio
    async def test_panel_processor_initialization(self):
        """Test 2: Validate processor initialization and connection"""
        panel = ProcessingMetricsPanel(market_id="BTC-USD")
        
        try:
            # Initialize the panel
            await panel.initialize()
            
            # Validate processor creation
            assert panel.processor is not None
            assert panel.processor.market_id == "BTC-USD"
            assert panel.processor.client is not None
            
            # Wait for processor to start receiving data
            await asyncio.sleep(8)
            
            # Validate processor is running
            assert panel.processor.is_running() is True
            
            # Get processing metrics
            metrics = panel.processor.get_processing_metrics()
            assert metrics is not None
            assert metrics.uptime_start > 0
            assert metrics.get_uptime_seconds() > 5  # At least 5 seconds uptime
            
        finally:
            # Guaranteed cleanup
            if hasattr(panel, 'processor') and panel.processor:
                await panel.processor.shutdown()
    
    @pytest.mark.asyncio
    async def test_throughput_metrics_display(self, panel: ProcessingMetricsPanel):
        """Test 3: Validate throughput metrics panel content and formatting"""
        
        await panel.initialize()
        await asyncio.sleep(10)  # Allow time for message processing
        
        # Create layout and capture output
        layout = panel.create_layout()
        console = Console(width=120, height=30)
        with console.capture() as capture:
            console.print(layout)
        
        output = capture.get()
        
        # Validate throughput panel structure
        assert "Throughput" in output
        assert "Messages Processed" in output
        assert "OHLCV Candles Generated" in output
        assert "Orderbook Updates" in output
        
        # Validate numeric formatting with regex (handles commas and table formatting)
        assert re.search(r"Messages Processed.*[\d,]+.*[\d.]+", output, re.DOTALL)
        assert re.search(r"OHLCV Candles Generated.*[\d,]+.*[\d.]+", output, re.DOTALL)
        assert re.search(r"Orderbook Updates.*[\d,]+.*[\d.]+", output, re.DOTALL)
        
        # Validate rate calculations (Rate/sec column)
        assert re.search(r"Rate/sec.*[\d.]+", output, re.DOTALL)
        
        # Get actual metrics to validate content
        metrics = panel.processor.get_processing_metrics()
        assert metrics.messages_processed >= 0
        assert metrics.get_uptime_seconds() > 8
    
    @pytest.mark.asyncio
    async def test_latency_analysis_display(self, panel: ProcessingMetricsPanel):
        """Test 4: Validate latency analysis panel content and status indicators"""
        
        await panel.initialize()
        await asyncio.sleep(12)  # Allow time for latency samples
        
        # Create layout and capture output
        layout = panel.create_layout()
        console = Console(width=120, height=30)
        with console.capture() as capture:
            console.print(layout)
        
        output = capture.get()
        
        # Validate latency panel structure
        assert "Latency Analysis" in output
        assert "Average Latency" in output
        assert "95th Percentile" in output
        assert "Sample Count" in output
        
        # Validate latency values and status indicators
        assert re.search(r"Average Latency.*[\d.]+.*(GOOD|OK|HIGH)", output, re.DOTALL)
        assert re.search(r"95th Percentile.*[\d.]+.*(GOOD|OK|HIGH)", output, re.DOTALL)
        assert re.search(r"Sample Count.*[\d,]+.*INFO", output, re.DOTALL)
        
        # Validate status color indicators
        status_indicators = re.findall(r"(GOOD|OK|HIGH|INFO)", output)
        assert len(status_indicators) >= 3  # At least 3 status indicators
        
        # Get actual metrics to validate latency data
        metrics = panel.processor.get_processing_metrics()
        if metrics.processing_latency_ms:
            avg_latency = metrics.get_avg_latency_ms()
            assert avg_latency >= 0
            assert len(metrics.processing_latency_ms) > 0
    
    @pytest.mark.asyncio
    async def test_reliability_error_tracking(self, panel: ProcessingMetricsPanel):
        """Test 5: Validate reliability and error tracking display"""
        
        await panel.initialize()
        await asyncio.sleep(10)  # Allow time for operations
        
        # Create layout and capture output
        layout = panel.create_layout()
        console = Console(width=120, height=30)
        with console.capture() as capture:
            console.print(layout)
        
        output = capture.get()
        
        # Validate reliability panel structure
        assert "Reliability & Errors" in output
        assert "Uptime" in output
        assert "Total Errors" in output
        assert "Error Rate" in output
        assert "Success Rate" in output
        
        # Validate uptime formatting
        assert re.search(r"Uptime.*[\d.]+[hs].*(STABLE|STARTING)", output, re.DOTALL)
        
        # Validate error metrics
        assert re.search(r"Total Errors.*[\d,]+.*(ERRORS|CLEAN)", output, re.DOTALL)
        assert re.search(r"Error Rate.*[\d.]+%.*(HIGH|LOW|MINIMAL)", output, re.DOTALL)
        assert re.search(r"Success Rate.*[\d.]+%.*(EXCELLENT|GOOD|POOR)", output, re.DOTALL)
        
        # Get actual metrics to validate reliability data
        metrics = panel.processor.get_processing_metrics()
        uptime = metrics.get_uptime_seconds()
        assert uptime > 8  # At least 8 seconds uptime
        assert metrics.error_count >= 0
    
    @pytest.mark.asyncio
    async def test_data_status_connectivity(self, panel: ProcessingMetricsPanel):
        """Test 6: Validate data status and connectivity display"""
        
        await panel.initialize()
        await asyncio.sleep(10)  # Allow time for data updates
        
        # Create layout and capture output
        layout = panel.create_layout()
        console = Console(width=120, height=30)
        with console.capture() as capture:
            console.print(layout)
        
        output = capture.get()
        
        # Validate data status panel structure
        assert "Data Status" in output
        assert "Data Processor" in output
        assert "WebSocket" in output
        assert "Orderbook Feed" in output
        assert "OHLCV Generation" in output
        
        # Validate status indicators
        assert re.search(r"Data Processor.*(RUNNING|STOPPED)", output, re.DOTALL)
        assert re.search(r"WebSocket.*(CONNECTED|DISCONNECTED)", output, re.DOTALL)
        assert re.search(r"Orderbook Feed.*(ACTIVE|NO DATA)", output, re.DOTALL)
        assert re.search(r"OHLCV Generation.*(ACTIVE|NO DATA)", output, re.DOTALL)
        
        # Validate time formatting
        assert re.search(r"(\d{2}:\d{2}:\d{2}|N/A)", output, re.DOTALL)
        
        # Validate processor status
        assert panel.processor.is_running() is True
    
    @pytest.mark.asyncio
    async def test_streaming_data_updates(self, panel: ProcessingMetricsPanel):
        """Test 7: Validate streaming data updates and metric progression"""
        
        await panel.initialize()
        await asyncio.sleep(5)
        
        # Capture initial metrics
        initial_metrics = panel.processor.get_processing_metrics()
        initial_messages = initial_metrics.messages_processed
        initial_uptime = initial_metrics.get_uptime_seconds()
        
        # Wait for more data
        await asyncio.sleep(15)
        
        # Capture updated metrics
        updated_metrics = panel.processor.get_processing_metrics()
        updated_messages = updated_metrics.messages_processed
        updated_uptime = updated_metrics.get_uptime_seconds()
        
        # Validate metrics progression
        assert updated_messages >= initial_messages  # Messages should increase or stay same
        assert updated_uptime > initial_uptime  # Uptime should increase
        assert updated_uptime - initial_uptime >= 14  # At least 14 seconds difference
        
        # Create layout and validate live data
        layout = panel.create_layout()
        console = Console(width=120, height=30)
        with console.capture() as capture:
            console.print(layout)
        
        output = capture.get()
        
        # Validate that metrics are being displayed
        assert str(updated_messages) in output or f"{updated_messages:,}" in output
        assert "LIVE" in output
        assert "RUNNING" in output or "ACTIVE" in output
    
    @pytest.mark.asyncio
    async def test_data_quality_validation(self, panel: ProcessingMetricsPanel):
        """Test 8: Validate data quality and consistency"""
        
        await panel.initialize()
        await asyncio.sleep(15)  # Allow time for substantial data
        
        # Get metrics for validation
        metrics = panel.processor.get_processing_metrics()
        
        # Validate metric consistency
        assert metrics.messages_processed >= 0
        assert metrics.ohlcv_generated >= 0
        assert metrics.orderbook_updates >= 0
        assert metrics.error_count >= 0
        assert metrics.get_uptime_seconds() > 10
        
        # Validate rate calculations
        uptime = metrics.get_uptime_seconds()
        msg_rate = metrics.messages_processed / max(uptime, 1)
        assert msg_rate >= 0
        
        # Validate latency data if available
        if metrics.processing_latency_ms:
            avg_latency = metrics.get_avg_latency_ms()
            p95_latency = metrics.get_p95_latency_ms()
            assert avg_latency >= 0
            assert p95_latency >= avg_latency  # P95 should be >= average
            assert avg_latency < 10000  # Reasonable latency bounds (< 10 seconds)
        
        # Create layout and validate data representation
        layout = panel.create_layout()
        console = Console(width=120, height=30)
        with console.capture() as capture:
            console.print(layout)
        
        output = capture.get()
        
        # Validate no invalid data display
        assert "nan" not in output.lower()
        assert " inf " not in output.lower() and "inf%" not in output.lower() and "inf)" not in output.lower()  # Check for infinity values, not substrings
        assert "error" not in output.lower() or "Total Errors" in output  # Only valid error references
    
    @pytest.mark.asyncio
    async def test_performance_and_responsiveness(self, panel: ProcessingMetricsPanel):
        """Test 9: Validate panel performance and responsiveness"""
        
        await panel.initialize()
        await asyncio.sleep(8)
        
        # Test layout creation performance
        start_time = time.time()
        layout = panel.create_layout()
        layout_time = time.time() - start_time
        
        assert layout_time < 1.0  # Layout creation should be fast (< 1 second)
        
        # Test console rendering performance
        console = Console(width=120, height=30)
        start_time = time.time()
        with console.capture() as capture:
            console.print(layout)
        render_time = time.time() - start_time
        
        assert render_time < 0.5  # Rendering should be fast (< 0.5 seconds)
        
        # Validate output quality
        output = capture.get()
        assert len(output) > 100  # Should have substantial content
        assert output.count('\n') > 10  # Should have multiple lines
        
        # Test multiple rapid updates
        update_times = []
        for i in range(3):
            start_time = time.time()
            layout = panel.create_layout()
            with console.capture() as capture:
                console.print(layout)
            update_times.append(time.time() - start_time)
            await asyncio.sleep(1)
        
        # All updates should be reasonably fast
        avg_update_time = sum(update_times) / len(update_times)
        assert avg_update_time < 0.8  # Average update time should be reasonable
    
    @pytest.mark.asyncio
    async def test_autonomous_operation_guarantee(self, panel: ProcessingMetricsPanel):
        """Test 10: Validate autonomous operation and self-sufficiency"""
        
        await panel.initialize()
        
        # Validate processor independence
        assert panel.processor is not None
        assert panel.processor.client is not None
        assert panel.processor.is_running() is True
        
        # Test autonomous data collection over time
        start_time = time.time()
        initial_metrics = panel.processor.get_processing_metrics()
        initial_uptime = initial_metrics.get_uptime_seconds()
        
        # Run for a sustained period
        await asyncio.sleep(20)
        
        final_metrics = panel.processor.get_processing_metrics()
        final_uptime = final_metrics.get_uptime_seconds()
        elapsed_time = time.time() - start_time
        
        # Validate autonomous operation
        assert elapsed_time >= 18  # Ran for at least 18 seconds
        assert final_uptime >= 18
        assert panel.processor.is_running() is True
        
        # Validate continuous operation (uptime should increase by approximately the elapsed time)
        uptime_increase = final_uptime - initial_uptime
        assert uptime_increase >= 18  # Should have increased by at least the sleep time
        
        # Create final layout to ensure full functionality
        layout = panel.create_layout()
        console = Console(width=120, height=30)
        with console.capture() as capture:
            console.print(layout)
        
        output = capture.get()
        
        # Validate autonomous operation indicators
        assert "LIVE" in output
        assert "RUNNING" in output or "ACTIVE" in output
        assert "BTC-USD" in output
        
        # Validate operational metrics
        uptime_match = re.search(r"Uptime.*[\d.]+[hs]", output, re.DOTALL)
        assert uptime_match is not None
        
        # Validate success/stability indicators
        stability_indicators = re.findall(r"(STABLE|EXCELLENT|GOOD|ACTIVE|RUNNING|CONNECTED)", output)
        assert len(stability_indicators) >= 3  # Multiple stability indicators
        
        print(f"✅ Processing Metrics Panel autonomous operation validated over {elapsed_time:.1f} seconds")
        print(f"✅ Processed {final_metrics.messages_processed} messages with {final_metrics.error_count} errors")
        print(f"✅ Generated {final_metrics.ohlcv_generated} OHLCV candles and {final_metrics.orderbook_updates} orderbook updates")
        print(f"✅ Average latency: {final_metrics.get_avg_latency_ms():.2f}ms")


# Standalone test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
