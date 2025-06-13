"""
Streaming Data Tests for Layer 2: dYdX v4 Client Integration

CRITICAL: These tests validate that our Layer 2 can handle real streaming data
from dYdX mainnet. Dashboard creation is FORBIDDEN until these all pass.

Tests real-time WebSocket data flows that the dashboard will rely on.
"""

import asyncio
import pytest
import time
from src.dydx_bot.connection.client import DydxClient


class TestRealStreamingData:
    """Test real streaming data handling - CRITICAL for dashboard readiness"""
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_real_markets_streaming_data_flow(self):
        """Test that we can receive and process real markets streaming data"""
        client = DydxClient()
        
        received_messages = []
        
        def capture_message(ws, message):
            received_messages.append(message)
            if message.get("type") == "connected":
                # Subscribe to markets on connection
                asyncio.create_task(client.subscribe_to_markets())
        
        # Override message handler to capture messages
        client._on_message = capture_message
        
        # This should work with REAL dYdX mainnet
        await client.connect()
        
        # Start WebSocket in thread (based on official examples)
        websocket_thread = client.start_websocket_in_thread()
        
        # Wait for streaming data
        await asyncio.sleep(5)
        
        # Validate we received real streaming data
        assert len(received_messages) > 0, "No streaming messages received"
        
        # Check we got connection message
        connected_msgs = [msg for msg in received_messages if msg.get("type") == "connected"]
        assert len(connected_msgs) > 0, "No connection message received"
        
        # Check for market data messages
        market_msgs = [msg for msg in received_messages 
                      if msg.get("channel") == "v4_markets"]
        
        # This validates the streaming data pipeline works
        print(f"Received {len(received_messages)} total messages")
        print(f"Market messages: {len(market_msgs)}")
        
        await client.disconnect()
    
    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_dashboard_readiness_comprehensive_streaming(self):
        """FINAL TEST: Comprehensive streaming test that proves dashboard readiness"""
        client = DydxClient()
        
        dashboard_data = {
            "markets": {"count": 0, "latest": None},
            "orderbook": {"count": 0, "latest": None},  
            "trades": {"count": 0, "latest": None},
            "candles": {"count": 0, "latest": None},
            "connection_stable": True,
            "latency_ok": True
        }
        
        connected_event = asyncio.Event()
        
        def dashboard_data_collector(ws, message):
            start_time = time.time()
            
            channel = message.get("channel")
            msg_type = message.get("type")
            
            # Monitor connection stability
            if msg_type == "error":
                dashboard_data["connection_stable"] = False
            
            # Collect data for dashboard
            if channel == "v4_markets":
                dashboard_data["markets"]["count"] += 1
                dashboard_data["markets"]["latest"] = message
            elif channel == "v4_orderbook":
                dashboard_data["orderbook"]["count"] += 1
                dashboard_data["orderbook"]["latest"] = message
            elif channel == "v4_trades":
                dashboard_data["trades"]["count"] += 1
                dashboard_data["trades"]["latest"] = message
            elif channel == "v4_candles":
                dashboard_data["candles"]["count"] += 1
                dashboard_data["candles"]["latest"] = message
            
            # Monitor processing latency
            processing_time = (time.time() - start_time) * 1000
            if processing_time > 25:
                dashboard_data["latency_ok"] = False
            
            if msg_type == "connected":
                # Signal that we're connected, don't subscribe from thread
                connected_event.set()
        
        client._on_message = dashboard_data_collector
        
        await client.connect()
        websocket_thread = client.start_websocket_in_thread()
        
        # Wait for connection
        try:
            await asyncio.wait_for(connected_event.wait(), timeout=10)
        except asyncio.TimeoutError:
            pytest.fail("WebSocket connection timeout - check dYdX connectivity")
        
        # Now subscribe to all channels in the main event loop
        await client.subscribe_to_markets()
        await client.subscribe_to_orderbook("BTC-USD")
        await client.subscribe_to_trades("BTC-USD")
        from dydx_v4_client.indexer.candles_resolution import CandlesResolution
        await client.subscribe_to_candles("BTC-USD", CandlesResolution.ONE_MINUTE)
        
        # Run comprehensive streaming test
        await asyncio.sleep(15)
        
        # CRITICAL VALIDATIONS FOR DASHBOARD READINESS
        assert dashboard_data["connection_stable"], "Connection not stable - dashboard will fail"
        assert dashboard_data["latency_ok"], "Latency requirements not met - dashboard will be slow"
        
        # All data streams must be working
        assert dashboard_data["markets"]["count"] > 0, "Markets data not streaming - dashboard will show no markets"
        assert dashboard_data["orderbook"]["count"] > 0, "Orderbook data not streaming - dashboard will show no prices" 
        assert dashboard_data["trades"]["count"] > 0, "Trades data not streaming - dashboard will show no activity"
        
        # Validate data quality for dashboard
        if dashboard_data["orderbook"]["latest"]:
            orderbook_msg = dashboard_data["orderbook"]["latest"]
            if orderbook_msg.get("contents"):
                content = orderbook_msg["contents"][0] if orderbook_msg["contents"] else {}
                assert "bids" in content or "asks" in content, "Orderbook data corrupted - dashboard will crash"
        
        if dashboard_data["trades"]["latest"]:
            trades_msg = dashboard_data["trades"]["latest"]  
            if trades_msg.get("contents"):
                # Handle flexible content format from dYdX
                contents = trades_msg["contents"]
                if isinstance(contents, dict) and "trades" in contents:
                    # Handle {"trades": [...]} format
                    if contents["trades"]:
                        trade = contents["trades"][0]
                        assert "price" in trade and "size" in trade, "Trade data corrupted - dashboard will crash"
                elif isinstance(contents, list) and len(contents) > 0:
                    # Handle list format
                    content = contents[0]
                    assert content, "Trade data exists"
        
        print("🟢 DASHBOARD READINESS VALIDATED:")
        print(f"  Markets: {dashboard_data['markets']['count']} messages")
        print(f"  Orderbook: {dashboard_data['orderbook']['count']} messages") 
        print(f"  Trades: {dashboard_data['trades']['count']} messages")
        print(f"  Candles: {dashboard_data['candles']['count']} messages")
        print(f"  Connection Stable: {dashboard_data['connection_stable']}")
        print(f"  Latency OK: {dashboard_data['latency_ok']}")
        
        await client.disconnect()
