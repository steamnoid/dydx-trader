"""Test configuration and utilities for dYdX v4 trading bot tests"""

import pytest
import asyncio
from typing import Generator, Dict, Any
from unittest.mock import MagicMock

from dydx_bot.config.settings import Settings, NetworkType


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with safe defaults"""
    return Settings(
        dydx_network=NetworkType.TESTNET,
        dydx_mnemonic="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
        dydx_wallet_address="dydx1test123456789",
        dydx_private_key="test_private_key_safe_for_testing",
        paper_trading=True,
        initial_capital=1000.0,
        max_leverage=5.0,
        risk_tolerance=0.01,
        debug=True
    )


@pytest.fixture
def mock_dydx_network_config() -> Dict[str, Any]:
    """Mock dYdX network configuration"""
    return {
        "chain_id": "dydx-testnet-4",
        "node_endpoint": "https://test-dydx.kingnodes.com",
        "indexer_rest_endpoint": "https://indexer.v4testnet.dydx.exchange",
        "indexer_ws_endpoint": "wss://indexer.v4testnet.dydx.exchange/v4/ws",
    }


@pytest.fixture
def mock_wallet():
    """Mock dYdX wallet for testing"""
    wallet = MagicMock()
    wallet.address = "dydx1test123456789"
    wallet.public_key = "test_public_key"
    return wallet


@pytest.fixture
def mock_indexer_client():
    """Mock IndexerClient for testing"""
    client = MagicMock()
    client.utility.get_time.return_value = {"time": "2023-01-01T00:00:00Z"}
    return client


@pytest.fixture  
def mock_indexer_socket():
    """Mock IndexerSocket for testing"""
    socket = MagicMock()
    socket.connected = True
    socket.close = MagicMock()
    return socket


@pytest.fixture
def mock_node_client():
    """Mock NodeClient for testing"""
    client = MagicMock()
    return client
