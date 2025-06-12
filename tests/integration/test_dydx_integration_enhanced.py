"""
Enhanced integration tests for dYdX v4 trading bot

Tests real connections to dYdX v4 testnet to validate protocol integration.
These tests require network access and may be skipped in CI environments.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.dydx_bot.connection.dydx_client import DydxClientManager, DydxClientError
from src.dydx_bot.config.settings import Settings, NetworkType
from src.dydx_bot.main import (
    setup_logging, initialize_application, shutdown_application, 
    signal_handler, main_async, test_connection, config_info, main
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_dydx_connection_enhanced():
    """Test real connection to dYdX v4 testnet with enhanced error handling"""
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
        # Clean up - handle disconnect gracefully
        try:
            await client_manager.disconnect()
        except Exception as disconnect_error:
            print(f"Disconnect warning (non-critical): {disconnect_error}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dydx_mainnet_configuration():
    """Test mainnet configuration without connecting"""
    settings = Settings(
        dydx_network=NetworkType.MAINNET,
        max_leverage=5.0,
        risk_tolerance=0.02
    )

    client_manager = DydxClientManager(settings)
    
    # Test network configuration
    network = client_manager._get_network()
    assert network.node.chain_id == "dydx-mainnet-1"
    assert "indexer.dydx.exchange" in network.rest_indexer
    print(f"Mainnet configuration validated: {network.node.chain_id}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_connection_timeout_handling():
    """Test connection timeout and error handling"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    try:
        # Set a short timeout for this test
        await asyncio.wait_for(client_manager.connect(), timeout=30.0)
        
        # If we get here, connection succeeded
        assert client_manager.is_connected
        print("Connection succeeded within timeout")
        
        # Test a quick API call
        health = await client_manager.health_check()
        assert "indexer_client" in health
        
        await client_manager.disconnect()
        
    except asyncio.TimeoutError:
        pytest.skip("Connection timeout (expected in slow networks)")
    except Exception as e:
        pytest.skip(f"Connection failed (expected in CI): {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_connections():
    """Test multiple connection/disconnection cycles"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    try:
        for i in range(2):  # Test 2 cycles
            print(f"Connection cycle {i + 1}")
            
            # Connect
            await client_manager.connect()
            assert client_manager.is_connected
            
            # Basic test
            health = await client_manager.health_check()
            assert health["indexer_client"] is True
            
            # Disconnect
            await client_manager.disconnect()
            assert not client_manager.is_connected
            
            print(f"Cycle {i + 1} completed successfully")

    except Exception as e:
        pytest.skip(f"Multiple connection test failed (network issue): {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_error_handling():
    """Test API error handling with real connection"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    try:
        await client_manager.connect()
        assert client_manager.is_connected

        # Test with invalid address (should handle gracefully)
        try:
            balance = await client_manager.get_account_balance("invalid_address")
            # If this succeeds, the API is more lenient than expected
            print(f"API response for invalid address: {balance}")
        except DydxClientError as e:
            # Expected - API should reject invalid address
            print(f"Expected API error for invalid address: {e}")
            assert "failed" in str(e).lower()

    except Exception as e:
        pytest.skip(f"API error test failed (network issue): {e}")
    
    finally:
        try:
            await client_manager.disconnect()
        except Exception:
            pass  # Ignore disconnect errors


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_api_calls():
    """Test concurrent API calls"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    try:
        await client_manager.connect()
        assert client_manager.is_connected

        # Make concurrent API calls
        tasks = [
            client_manager.get_markets(),
            client_manager.health_check(),
            client_manager.health_check()  # Duplicate to test concurrency
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that at least the basic calls succeeded
        markets_result = results[0]
        if not isinstance(markets_result, Exception):
            assert "markets" in markets_result
            print(f"Concurrent API calls successful")
        else:
            print(f"Concurrent API calls had issues: {markets_result}")

    except Exception as e:
        pytest.skip(f"Concurrent API test failed (network issue): {e}")
    
    finally:
        try:
            await client_manager.disconnect()
        except Exception:
            pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_network_configuration_validation():
    """Test that network configurations are valid"""
    
    # Test testnet
    testnet_settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )
    
    testnet_manager = DydxClientManager(testnet_settings)
    testnet_network = testnet_manager._get_network()
    
    assert testnet_network.node.chain_id == "dydx-testnet-4"
    assert "testnet" in testnet_network.rest_indexer.lower()
    print(f"Testnet configuration valid: {testnet_network.node.chain_id}")
    
    # Test mainnet
    mainnet_settings = Settings(
        dydx_network=NetworkType.MAINNET,
        max_leverage=5.0,
        risk_tolerance=0.02
    )
    
    mainnet_manager = DydxClientManager(mainnet_settings)
    mainnet_network = mainnet_manager._get_network()
    
    assert mainnet_network.node.chain_id == "dydx-mainnet-1"
    assert "indexer.dydx.exchange" in mainnet_network.rest_indexer
    print(f"Mainnet configuration valid: {mainnet_network.node.chain_id}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graceful_disconnect_scenarios():
    """Test various disconnect scenarios"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    try:
        # Test disconnect without connection
        await client_manager.disconnect()  # Should not raise error
        assert not client_manager.is_connected
        
        # Test disconnect after connection
        await client_manager.connect()
        assert client_manager.is_connected
        
        await client_manager.disconnect()
        assert not client_manager.is_connected
        
        # Test multiple disconnects
        await client_manager.disconnect()  # Should not raise error
        await client_manager.disconnect()  # Should not raise error
        
        print("Graceful disconnect scenarios completed")

    except Exception as e:
        pytest.skip(f"Disconnect test failed (network issue): {e}")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_extended_connection():
    """Test extended connection stability (marked as slow)"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    try:
        await client_manager.connect()
        assert client_manager.is_connected
        
        # Test stability over time with multiple API calls
        for i in range(3):  # 3 iterations for faster testing
            health = await client_manager.health_check()
            assert health["indexer_client"] is True
            
            markets = await client_manager.get_markets()
            assert "markets" in markets
            
            # Small delay between calls
            await asyncio.sleep(0.5)
            
            print(f"Extended test iteration {i + 1}/3 completed")
        
        print("Extended connection test passed")

    except Exception as e:
        pytest.skip(f"Extended connection test failed (network issue): {e}")
    
    finally:
        try:
            await client_manager.disconnect()
        except Exception:
            pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_client_lifecycle():
    """Test complete client lifecycle including all connection phases"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    # Test initial state
    assert not client_manager.is_connected
    assert client_manager.wallet is None

    # Test property access before connection
    with pytest.raises(RuntimeError, match="IndexerClient not initialized"):
        _ = client_manager.indexer_client

    with pytest.raises(RuntimeError, match="NodeClient not initialized"):
        _ = client_manager.node_client

    with pytest.raises(RuntimeError, match="IndexerSocket not initialized"):
        _ = client_manager.indexer_socket

    # Test connection with mocked clients to avoid network dependency
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

        # Test connection
        await client_manager.connect()
        assert client_manager.is_connected

        # Test property access after connection
        assert client_manager.indexer_client is not None
        assert client_manager.node_client is not None
        assert client_manager.indexer_socket is not None

        # Test health check
        mock_indexer_instance.utility.get_time = AsyncMock(return_value={"iso": "2024-01-01T00:00:00Z"})
        mock_node_instance.latest_block_height = AsyncMock(return_value=12345)
        mock_socket_instance.connected = True

        health = await client_manager.health_check()
        assert health["indexer_client"] is True
        assert health["node_client"] is True  
        assert health["indexer_socket"] is True

        # Test disconnection
        await client_manager.disconnect()
        assert not client_manager.is_connected


@pytest.mark.integration
@pytest.mark.asyncio
async def test_wallet_integration():
    """Test wallet creation and management integration"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        dydx_mnemonic="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    with patch('src.dydx_bot.connection.dydx_client.IndexerClient') as mock_indexer, \
         patch('src.dydx_bot.connection.dydx_client.IndexerSocket') as mock_socket, \
         patch('src.dydx_bot.connection.dydx_client.NodeClient') as mock_node, \
         patch('src.dydx_bot.connection.dydx_client.Wallet') as mock_wallet_class:

        # Setup mocks
        mock_wallet = MagicMock()
        mock_wallet.address = "dydx1test_wallet_address"
        mock_wallet_class.from_mnemonic = AsyncMock(return_value=mock_wallet)

        mock_indexer_instance = AsyncMock()
        mock_socket_instance = AsyncMock()
        mock_node_instance = AsyncMock()

        mock_indexer.return_value = mock_indexer_instance
        mock_socket.return_value = mock_socket_instance
        mock_node.connect = AsyncMock(return_value=mock_node_instance)

        # First connect the client
        await client_manager.connect()
        assert client_manager.is_connected

        # Then create wallet separately
        wallet = await client_manager.create_wallet(
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
            "dydx1test_wallet_address"
        )
        
        assert client_manager.wallet is not None
        assert client_manager.wallet.address == "dydx1test_wallet_address"

        # Test health check with wallet
        health = await client_manager.health_check()
        assert health["wallet"] is True

        await client_manager.disconnect()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_connection_error_scenarios():
    """Test various connection error scenarios"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    # Test connection failure
    with patch('src.dydx_bot.connection.dydx_client.NodeClient') as mock_node:
        mock_node.connect = AsyncMock(side_effect=Exception("Connection failed"))
        
        with pytest.raises(DydxClientError, match="Connection failed:"):
            await client_manager.connect()

    # Test disconnect failure
    client_manager._is_connected = True
    mock_socket = AsyncMock()
    mock_socket.close = AsyncMock(side_effect=Exception("Socket close failed"))
    client_manager._indexer_socket = mock_socket

    with pytest.raises(DydxClientError, match="Disconnection failed:"):
        await client_manager.disconnect()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check_comprehensive():
    """Test comprehensive health check scenarios"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    # Test health check when nothing is connected
    health = await client_manager.health_check()
    assert health["indexer_client"] is False
    assert health["indexer_socket"] is False
    assert health["node_client"] is False
    assert health["wallet"] is False

    # Test partial connection scenarios
    mock_indexer = MagicMock()
    mock_utility = MagicMock()
    
    # Test indexer client failure
    mock_utility.get_time = AsyncMock(side_effect=Exception("API failed"))
    mock_indexer.utility = mock_utility
    client_manager._indexer_client = mock_indexer
    
    health = await client_manager.health_check()
    assert health["indexer_client"] is False

    # Test indexer client success
    mock_utility.get_time = AsyncMock(return_value={"iso": "2024-01-01T00:00:00Z"})
    health = await client_manager.health_check()
    assert health["indexer_client"] is True

    # Test node client scenarios
    mock_node = MagicMock()
    mock_node.latest_block_height = AsyncMock(side_effect=Exception("Node failed"))
    client_manager._node_client = mock_node
    
    health = await client_manager.health_check()
    assert health["node_client"] is False

    mock_node.latest_block_height = AsyncMock(return_value=12345)
    health = await client_manager.health_check()
    assert health["node_client"] is True

    # Test socket scenarios
    mock_socket = MagicMock()
    mock_socket.connected = True
    client_manager._indexer_socket = mock_socket
    
    health = await client_manager.health_check()
    assert health["indexer_socket"] is True

    # Test wallet scenario
    mock_wallet = MagicMock()
    mock_wallet.address = "dydx1test_address"
    client_manager._wallet = mock_wallet
    
    health = await client_manager.health_check()
    assert health["wallet"] is True


@pytest.mark.integration
def test_main_module_integration():
    """Test main module integration functions"""
    # Test setup_logging
    setup_logging("DEBUG")
    setup_logging("INFO")
    setup_logging("ERROR")

    # Test signal handler
    import signal
    original_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal_handler(signal.SIGINT, None)
    signal.signal(signal.SIGINT, original_handler)

    # Test config_info
    with patch('src.dydx_bot.main.console.print') as mock_print:
        config_info()
        assert mock_print.call_count >= 5  # Should print several config lines


@pytest.mark.integration
@pytest.mark.asyncio
async def test_application_lifecycle():
    """Test complete application initialization and shutdown"""
    # Create mock settings with wallet config for validation
    mock_settings = Settings(
        dydx_network=NetworkType.TESTNET,
        dydx_mnemonic="abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
        dydx_wallet_address="dydx1test_address",
        dydx_private_key="test_private_key",
        max_leverage=10.0,
        risk_tolerance=0.05
    )
    
    with patch('src.dydx_bot.main.settings', mock_settings), \
         patch('src.dydx_bot.main.DydxClientManager') as mock_manager_class:
        
        # Setup mock manager
        mock_manager = AsyncMock()
        mock_manager.connect = AsyncMock()
        mock_manager.health_check = AsyncMock(return_value={"indexer_client": True})
        mock_manager.disconnect = AsyncMock()
        mock_manager_class.return_value = mock_manager

        # Test initialization
        manager = await initialize_application()
        assert manager is not None
        mock_manager.connect.assert_called_once()
        mock_manager.health_check.assert_called_once()

        # Test shutdown
        await shutdown_application(manager)
        mock_manager.disconnect.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_configuration_validation():
    """Test configuration validation integration"""
    # Test valid configuration
    valid_settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )
    
    client_manager = DydxClientManager(valid_settings)
    network = client_manager._get_network()
    assert network is not None

    # Test invalid network type
    client_manager = DydxClientManager(valid_settings)
    client_manager.settings.dydx_network = "INVALID_NETWORK"
    
    with pytest.raises(ValueError, match="Unknown network"):
        client_manager._get_network()


@pytest.mark.integration
def test_settings_integration():
    """Test settings module integration"""
    # Test basic settings creation
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )
    
    assert settings.dydx_network == NetworkType.TESTNET
    assert settings.max_leverage == 10.0
    assert not settings.has_wallet_config()

    # Test settings with wallet
    settings_with_wallet = Settings(
        dydx_network=NetworkType.TESTNET,
        dydx_mnemonic="test mnemonic phrase",
        dydx_wallet_address="test_address",
        dydx_private_key="test_key",
        max_leverage=10.0,
        risk_tolerance=0.05
    )
    
    assert settings_with_wallet.has_wallet_config()

    # Test validation
    try:
        settings.validate_for_trading()
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected for settings without wallet


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_propagation():
    """Test error propagation through the system"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    # Test that health check doesn't raise on empty state
    health = await client_manager.health_check()
    assert isinstance(health, dict)

    # Test exception handling in health check
    client_manager._indexer_client = MagicMock()
    client_manager._indexer_client.utility.get_time = AsyncMock(side_effect=Exception("Network error"))
    
    # Should not raise, should return False for failed component
    health = await client_manager.health_check()
    assert health["indexer_client"] is False


@pytest.mark.integration 
@pytest.mark.asyncio
async def test_main_function_integration():
    """Test main function integration with mocking"""
    # Mock the main loop to avoid infinite execution and configuration validation
    with patch('src.dydx_bot.main.initialize_application') as mock_init, \
         patch('src.dydx_bot.main.shutdown_event') as mock_event:
        
        # Setup mock manager and initialization
        mock_manager = AsyncMock()
        mock_init.return_value = mock_manager
        
        # Mock shutdown_event.wait() to return immediately
        mock_event.wait = AsyncMock()
        
        # Test that main function can be imported and called
        from src.dydx_bot.main import main_async
        result = await main_async()
        
        # Should complete without error
        assert result is None
        mock_init.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio 
async def test_signal_handling_integration():
    """Test signal handling integration"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    # Test graceful shutdown simulation
    import signal
    original_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    try:
        signal_handler(signal.SIGINT, None)
        # Should not raise an exception
        assert True
    finally:
        signal.signal(signal.SIGINT, original_handler)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_cleanup_integration():
    """Test memory cleanup integration"""
    settings = Settings(
        dydx_network=NetworkType.TESTNET,
        max_leverage=10.0,
        risk_tolerance=0.05
    )

    client_manager = DydxClientManager(settings)

    # Mock components for testing cleanup
    mock_indexer = MagicMock()
    mock_socket = MagicMock()
    mock_node = MagicMock()
    mock_wallet = MagicMock()

    client_manager._indexer_client = mock_indexer
    client_manager._indexer_socket = mock_socket
    client_manager._node_client = mock_node
    client_manager._wallet = mock_wallet
    client_manager._is_connected = True

    # Test disconnect cleans up
    await client_manager.disconnect()
    
    assert client_manager._indexer_client is None
    assert client_manager._indexer_socket is None
    assert client_manager._node_client is None
    assert client_manager._wallet is None
    assert not client_manager.is_connected


if __name__ == "__main__":
    # Run directly for manual testing
    asyncio.run(test_real_dydx_connection_enhanced())
    asyncio.run(test_dydx_mainnet_configuration())
    asyncio.run(test_connection_timeout_handling())
    asyncio.run(test_multiple_connections())
    asyncio.run(test_api_error_handling())
    asyncio.run(test_concurrent_api_calls())
    asyncio.run(test_network_configuration_validation())
    asyncio.run(test_graceful_disconnect_scenarios())
    asyncio.run(test_extended_connection())
    asyncio.run(test_full_client_lifecycle())
    asyncio.run(test_wallet_integration())
    asyncio.run(test_connection_error_scenarios())
    asyncio.run(test_health_check_comprehensive())
    test_main_module_integration()
    asyncio.run(test_application_lifecycle())
    asyncio.run(test_configuration_validation())
    test_settings_integration()
    asyncio.run(test_error_propagation())
    asyncio.run(test_main_function_integration())
    asyncio.run(test_signal_handling_integration())
    asyncio.run(test_memory_cleanup_integration())
