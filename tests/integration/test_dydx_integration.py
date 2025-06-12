"""
Integration test for dYdX v4 Client Manager

Test real connection to dYdX v4 testnet to validate protocol integration.
This test is optional and requires network access.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.dydx_bot.connection.dydx_client import DydxClientManager, DydxClientError
from src.dydx_bot.config.settings import Settings, NetworkType


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_dydx_connection():
    """Test real connection to dYdX v4 testnet"""
    # Create settings for testnet (no wallet needed for basic connection)
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )
    
    client_manager = DydxClientManager(settings)
    
    try:
        # Test connection to testnet
        await client_manager.connect()
        assert client_manager.is_connected
        
        # Test basic API calls
        markets = await client_manager.get_markets()
        assert "markets" in markets
        print(f"Found {len(markets['markets'])} perpetual markets")
        
        # Test health check
        health = await client_manager.health_check()
        assert health["indexer_client"] is True
        print("Health check passed")
        
    except Exception as e:
        # Skip if network issues, but log for debugging
        pytest.skip(f"Network connection failed (expected in CI): {e}")
    
    finally:
        # Clean up
        await client_manager.disconnect()


@pytest.mark.integration 
@pytest.mark.asyncio
async def test_network_configuration():
    """Test network configuration without connection"""
    # Test testnet config
    testnet_settings = Settings(dydx_network=NetworkType.TESTNET)
    testnet_manager = DydxClientManager(testnet_settings)
    
    assert testnet_manager.network.node.chain_id == "dydx-testnet-4"
    assert "testnet" in testnet_manager.network.rest_indexer
    
    # Test mainnet config
    mainnet_settings = Settings(dydx_network=NetworkType.MAINNET)
    mainnet_manager = DydxClientManager(mainnet_settings)
    
    # Should have different endpoints
    assert mainnet_manager.network.rest_indexer != testnet_manager.network.rest_indexer
    print("Network configurations are properly different")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_settings_network_configurations():
    """Test different network configuration integrations"""
    # Test testnet configuration
    testnet_settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )
    
    testnet_client = DydxClientManager(testnet_settings)
    testnet_network = testnet_client._get_network()
    assert testnet_network.node.chain_id == "dydx-testnet-4"
    assert "testnet" in testnet_network.rest_indexer.lower()

    # Test mainnet configuration  
    mainnet_settings = Settings(
        dydx_network=NetworkType.MAINNET,
        max_leverage=5.0,
        risk_tolerance=0.02
    )
    
    mainnet_client = DydxClientManager(mainnet_settings)
    mainnet_network = mainnet_client._get_network()
    assert mainnet_network.node.chain_id == "dydx-mainnet-1"
    assert "indexer.dydx.exchange" in mainnet_network.rest_indexer


@pytest.mark.integration  
@pytest.mark.asyncio
async def test_client_state_management():
    """Test client state management across operations"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    # Test initial state
    assert not client_manager.is_connected
    assert client_manager.wallet is None

    # Mock the network components to avoid real connections
    with patch('src.dydx_bot.connection.dydx_client.IndexerClient') as mock_indexer, \
         patch('src.dydx_bot.connection.dydx_client.IndexerSocket') as mock_socket, \
         patch('src.dydx_bot.connection.dydx_client.NodeClient') as mock_node:

        # Setup mocks with proper async handling
        mock_indexer_instance = AsyncMock()
        mock_socket_instance = AsyncMock()
        mock_node_instance = AsyncMock()

        mock_indexer.return_value = mock_indexer_instance
        mock_socket.return_value = mock_socket_instance
        mock_node.connect = AsyncMock(return_value=mock_node_instance)

        # Test connection state change
        await client_manager.connect()
        assert client_manager.is_connected

        # Test that components are accessible after connection
        assert client_manager.indexer_client is mock_indexer_instance
        assert client_manager.node_client is mock_node_instance
        assert client_manager.indexer_socket is mock_socket_instance

        # Test disconnect state change
        await client_manager.disconnect()
        assert not client_manager.is_connected

        # Test that components are cleaned up
        assert client_manager._indexer_client is None
        assert client_manager._node_client is None
        assert client_manager._indexer_socket is None


@pytest.mark.integration
@pytest.mark.asyncio  
async def test_error_handling_integration():
    """Test integrated error handling across components"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )
    
    client_manager = DydxClientManager(settings)
    
    # Test property access before connection
    with pytest.raises(RuntimeError, match="IndexerClient not initialized"):
        _ = client_manager.indexer_client
        
    with pytest.raises(RuntimeError, match="NodeClient not initialized"):
        _ = client_manager.node_client
        
    with pytest.raises(RuntimeError, match="IndexerSocket not initialized"):
        _ = client_manager.indexer_socket

    # Test wallet property (should return None, not raise)
    assert client_manager.wallet is None


@pytest.mark.integration
def test_import_integration():
    """Test that all necessary imports work correctly"""
    from src.dydx_bot.connection.dydx_client import DydxClientManager, DydxClientError
    from src.dydx_bot.config.settings import Settings, NetworkType
    from src.dydx_bot.main import setup_logging, config_info
    
    # Test that classes can be instantiated
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )
    
    client_manager = DydxClientManager(settings)
    assert client_manager is not None
    
    # Test that functions can be called
    setup_logging("INFO")
    
    with patch('src.dydx_bot.main.console.print'):
        config_info()


if __name__ == "__main__":
    # Run directly for manual testing
    asyncio.run(test_real_dydx_connection())
    asyncio.run(test_network_configuration())
    asyncio.run(test_settings_network_configurations())
    asyncio.run(test_client_state_management())
    asyncio.run(test_error_handling_integration())
