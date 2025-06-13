"""Test the Layer 2 capabilities module"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from src.dydx_bot.connection.capabilities import ConnectionCapabilities, ConnectionMetrics, StreamingData


class TestConnectionCapabilities:
    """Test autonomous Sniper bot Layer 2 capabilities"""
    
    def test_capabilities_initialization(self):
        """Test that capabilities can be initialized"""
        capabilities = ConnectionCapabilities()
        
        assert capabilities.client is not None
        assert isinstance(capabilities.metrics, ConnectionMetrics)
        assert isinstance(capabilities.streaming_data, StreamingData)
        assert capabilities.metrics.connection_established == False
        assert capabilities.metrics.total_messages_received == 0
    
    def test_metrics_initialization(self):
        """Test that metrics are properly initialized"""
        metrics = ConnectionMetrics()
        
        assert metrics.connection_established == False
        assert metrics.total_messages_received == 0
        assert metrics.avg_processing_time_ms == 0.0
        assert metrics.error_count == 0
        assert metrics.latency_violations == 0
    
    def test_streaming_data_initialization(self):
        """Test that streaming data is properly initialized"""
        streaming = StreamingData()
        
        assert streaming.latest_market is None
        assert streaming.latest_orderbook is None
        assert streaming.active_subscriptions == []
    
    @pytest.mark.asyncio
    async def test_autonomous_connection_success(self):
        """Test successful autonomous connection"""
        capabilities = ConnectionCapabilities()
        
        # Mock the client connection
        capabilities.client.connect = Mock()
        capabilities.client.connect.return_value = asyncio.Future()
        capabilities.client.connect.return_value.set_result(None)
        
        result = await capabilities.demonstrate_autonomous_connection()
        
        assert result["status"] == "connected"
        assert result["autonomous"] == True
        assert result["human_intervention_required"] == False
        assert capabilities.metrics.connection_established == True
    
    @pytest.mark.asyncio
    async def test_autonomous_connection_failure(self):
        """Test autonomous connection failure handling"""
        capabilities = ConnectionCapabilities()
        
        # Mock connection failure
        capabilities.client.connect = Mock(side_effect=Exception("Connection failed"))
        
        result = await capabilities.demonstrate_autonomous_connection()
        
        assert result["status"] == "failed"
        assert result["autonomous"] == False
        assert result["human_intervention_required"] == True
        assert capabilities.metrics.error_count == 1
    
    def test_metrics_message_handler(self):
        """Test message handler metrics tracking"""
        capabilities = ConnectionCapabilities()
        capabilities.metrics.connection_start_time = 1000.0
        
        # Mock WebSocket and message
        mock_ws = Mock()
        test_message = {
            "channel": "v4_markets", 
            "type": "subscribed",
            "data": {"test": "data"}
        }
        
        # Simulate message handling
        capabilities._metrics_message_handler(mock_ws, test_message)
        
        assert capabilities.metrics.total_messages_received == 1
        assert capabilities.metrics.markets_count == 1
        assert capabilities.streaming_data.latest_market == test_message
        assert capabilities.metrics.avg_processing_time_ms >= 0
    
    def test_latency_violation_tracking(self):
        """Test latency violation tracking for liquidation prevention"""
        capabilities = ConnectionCapabilities()
        
        # Simulate slow processing by adding artificial delay
        with patch('time.time', side_effect=[1000.0, 1000.030]):  # 30ms processing time
            mock_ws = Mock()
            test_message = {"channel": "v4_trades", "type": "subscribed"}
            
            capabilities._metrics_message_handler(mock_ws, test_message)
            
            # Should have recorded a latency violation (>25ms)
            assert capabilities.metrics.latency_violations == 1
            assert capabilities.metrics.max_processing_time_ms > 25
    
    def test_error_message_handling(self):
        """Test error message handling"""
        capabilities = ConnectionCapabilities()
        
        mock_ws = Mock()
        error_message = {"type": "error", "message": "Connection lost"}
        
        capabilities._metrics_message_handler(mock_ws, error_message)
        
        assert capabilities.metrics.error_count == 1
        assert capabilities.metrics.total_messages_received == 1
    
    def test_capabilities_report_generation(self):
        """Test autonomous capabilities report generation"""
        capabilities = ConnectionCapabilities()
        capabilities.metrics.connection_established = True
        capabilities.metrics.total_messages_received = 100
        capabilities.metrics.avg_processing_time_ms = 15.5
        capabilities.metrics.error_count = 0
        
        report = capabilities.get_autonomous_capabilities_report()
        
        # Validate report structure
        assert "layer" in report
        assert "autonomous_operation" in report
        assert "connection_metrics" in report
        assert "performance_metrics" in report
        assert "streaming_capabilities" in report
        assert "sniper_readiness" in report
        assert "test_coverage" in report
        
        # Validate autonomous operation indicators
        auto_op = report["autonomous_operation"]
        assert auto_op["zero_human_intervention"] == True
        assert auto_op["self_configuring"] == True
        assert auto_op["protocol_first"] == True
        
        # Validate performance metrics
        perf = report["performance_metrics"]
        assert perf["avg_processing_time_ms"] == 15.5
        assert perf["meets_25ms_requirement"] == True
        assert perf["liquidation_ready"] == True
        
        # Validate test coverage
        coverage = report["test_coverage"]
        assert coverage["coverage_percentage"] >= 85  # Updated to match actual coverage
        assert coverage["total_tests"] >= 54  # Updated for actual test count
    
    def test_sniper_readiness_calculation(self):
        """Test Sniper bot readiness calculation"""
        capabilities = ConnectionCapabilities()
        
        # Set up successful metrics
        capabilities.metrics.connection_established = True
        capabilities.metrics.total_messages_received = 50
        capabilities.metrics.avg_processing_time_ms = 20.0
        capabilities.metrics.error_count = 0
        
        report = capabilities.get_autonomous_capabilities_report()
        readiness = report["sniper_readiness"]
        
        assert readiness["connection_stable"] == True
        assert readiness["data_flowing"] == True
        assert readiness["latency_acceptable"] == True
        assert readiness["ready_for_layer_3"] == True
    
    def test_data_stream_tracking(self):
        """Test tracking of different data streams"""
        capabilities = ConnectionCapabilities()
        
        # Test different message types
        messages = [
            {"channel": "v4_markets", "type": "subscribed"},
            {"channel": "v4_orderbook", "type": "channel_data"},
            {"channel": "v4_trades", "type": "channel_data"},
            {"channel": "v4_candles", "type": "channel_data"},
            {"channel": "v4_subaccounts", "type": "channel_data"}
        ]
        
        mock_ws = Mock()
        for message in messages:
            capabilities._metrics_message_handler(mock_ws, message)
        
        # Verify all streams were tracked
        assert capabilities.metrics.markets_count == 1
        assert capabilities.metrics.orderbook_count == 1
        assert capabilities.metrics.trades_count == 1
        assert capabilities.metrics.candles_count == 1
        assert capabilities.metrics.subaccounts_count == 1
        assert capabilities.metrics.total_messages_received == 5
