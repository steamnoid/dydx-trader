#!/usr/bin/env python3
"""
Integration test to verify dashboard → live trader queue communication
"""

import asyncio
import pytest
import time
import json
from unittest.mock import patch
from dataclasses import dataclass

from live_trader import LiveTrader, LiveTraderConfig


@dataclass
class MockPosition:
    """Mock position for testing dashboard publishing"""
    market: str = "BTC-USD"
    signal_type: str = "BUY"
    size: float = 0.01
    entry_price: float = 50000.0
    status: str = "PENDING"
    pnl_usd: float = 0.0


class MockDashboard:
    """Mock dashboard that can publish trade opportunities"""
    
    def __init__(self):
        self.zmq_context = None
        self.trade_publisher = None
        self._setup_trade_publisher()
    
    def _setup_trade_publisher(self):
        """Initialize pyzmq publisher for testing"""
        try:
            import zmq
            self.zmq_context = zmq.Context()
            self.trade_publisher = self.zmq_context.socket(zmq.PUB)
            self.trade_publisher.bind("tcp://127.0.0.1:5557")  # Different port for testing
            print("Mock dashboard publisher initialized on tcp://127.0.0.1:5557")
        except Exception as e:
            print(f"Failed to setup mock publisher: {e}")
            self.trade_publisher = None
    
    def publish_trade_opportunity(self, position: MockPosition):
        """Publish a trade opportunity like the real dashboard would"""
        if not self.trade_publisher:
            return
        
        try:
            trade_message = {
                "timestamp": time.time(),
                "datetime": "2025-07-02T10:00:00",
                "action": "ENTRY",
                "market": position.market,
                "side": position.signal_type,
                "size": position.size,
                "price": position.entry_price,
                "status": position.status,
                "pnl_usd": position.pnl_usd,
                "details": {"test": True},
                "source": "mock_dashboard"
            }
            
            topic = "TRADE_OPPORTUNITY"
            message = json.dumps(trade_message)
            self.trade_publisher.send_multipart([topic.encode('utf-8'), message.encode('utf-8')])
            print(f"Published mock trade: {trade_message['action']} {trade_message['market']}")
            
        except Exception as e:
            print(f"Failed to publish mock trade: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.trade_publisher:
                self.trade_publisher.close()
            if self.zmq_context:
                self.zmq_context.term()
        except Exception as e:
            print(f"Mock dashboard cleanup error: {e}")


@pytest.mark.asyncio
async def test_dashboard_to_live_trader_communication():
    """Test that dashboard can send trade opportunities to live trader"""
    
    # Create mock dashboard
    dashboard = MockDashboard()
    
    # Give publisher time to bind
    await asyncio.sleep(0.5)
    
    # Create live trader with test configuration
    config = LiveTraderConfig(
        network_type="testnet",
        enable_live_trading=False  # Disable actual trading for test
    )
    
    trader = LiveTrader(config)
    
    # Patch the trader's consumer to use test port
    with patch.object(trader, 'setup_trade_consumer') as mock_setup:
        async def mock_setup_consumer():
            try:
                import zmq.asyncio
                trader.zmq_context = zmq.asyncio.Context()
                trader.trade_subscriber = trader.zmq_context.socket(zmq.SUB)
                trader.trade_subscriber.connect("tcp://127.0.0.1:5557")  # Connect to mock dashboard
                trader.trade_subscriber.setsockopt(zmq.SUBSCRIBE, b"TRADE_OPPORTUNITY")
                print("Mock trade consumer connected to tcp://127.0.0.1:5557")
                return True
            except Exception as e:
                print(f"Mock consumer setup failed: {e}")
                return False
        
        mock_setup.side_effect = mock_setup_consumer
        
        # Set up the trade consumer
        consumer_ready = await trader.setup_trade_consumer()
        assert consumer_ready is True
        
        # Track received trades
        received_trades = []
        
        # Patch the trade processing to capture trades instead of executing them
        async def mock_process_trade(trade_data):
            received_trades.append(trade_data)
            print(f"Mock received trade: {trade_data.get('action')} {trade_data.get('market')}")
        
        with patch.object(trader, '_process_trade_opportunity', side_effect=mock_process_trade):
            
            # Start consumer in background
            consumer_task = asyncio.create_task(trader.consume_trade_opportunities())
            
            # Give consumer time to start
            await asyncio.sleep(0.5)
            
            # Publish a trade opportunity from dashboard
            test_position = MockPosition(
                market="BTC-USD",
                signal_type="BUY",
                size=0.01,
                entry_price=50000.0
            )
            
            dashboard.publish_trade_opportunity(test_position)
            
            # Give time for message to be received and processed
            await asyncio.sleep(1.0)
            
            # Stop consumer
            await trader.stop_consuming()
            
            # Wait for consumer task to finish
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
            
            # Verify trade was received
            assert len(received_trades) == 1
            
            trade = received_trades[0]
            assert trade['action'] == 'ENTRY'
            assert trade['market'] == 'BTC-USD'
            assert trade['side'] == 'BUY'
            assert trade['size'] == 0.01
            assert trade['price'] == 50000.0
            assert trade['source'] == 'mock_dashboard'
            
            print("✅ Dashboard → Live Trader communication test passed!")
    
    # Cleanup
    dashboard.cleanup()


if __name__ == "__main__":
    asyncio.run(test_dashboard_to_live_trader_communication())
