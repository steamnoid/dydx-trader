"""Integration tests for Layer 4: SignalManager and ConnectionManager."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import pytest
from src.dydx_bot.signals.manager import SignalManager
from src.dydx_bot.signals.connection_manager import ConnectionManager

class TestLayer4Integration:
    """Integration tests for Layer 4 components."""

    def test_signal_manager_uses_connection_manager(self):
        """Test that SignalManager interacts correctly with ConnectionManager."""
        # Get ConnectionManager instance
        connection_manager = ConnectionManager.get_instance()

        # Create SignalManager instance
        signal_manager = SignalManager()

        # Verify SignalManager uses the same ConnectionManager instance
        assert signal_manager.momentum_engine.connection_manager is connection_manager
        assert signal_manager.volume_engine.connection_manager is connection_manager
        assert signal_manager.volatility_engine.connection_manager is connection_manager
        assert signal_manager.orderbook_engine.connection_manager is connection_manager
