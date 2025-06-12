"""
Enhanced unit tests for dYdX v4 Client Manager - Coverage improvement

Tests specifically targeting the uncovered lines in the dydx_client.py module.
Focus on edge cases, error paths, and integration scenarios.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from src.dydx_bot.connection.dydx_client import DydxClientManager, DydxClientError
from src.dydx_bot.config.settings import Settings, NetworkType


class TestDydxClientManagerCoverage:
    """Enhanced tests for complete coverage of DydxClientManager"""

    @pytest.fixture
    def testnet_settings(self):
        return Settings(
            dydx_network=NetworkType.TESTNET,
            risk_max_leverage=10.0,
            risk_tolerance=0.05
        )

    @pytest.fixture
    def mainnet_settings(self):
        return Settings(
            dydx_network=NetworkType.MAINNET,
            risk_max_leverage=5.0,
            risk_tolerance=0.02
        )

    @pytest.fixture
    def settings_with_wallet(self):
        return Settings(
            dydx_network=NetworkType.TESTNET,
            dydx_mnemonic="test mnemonic phrase for testing",
            risk_max_leverage=10.0,
            risk_tolerance=0.05
        )

    def test_invalid_network_configuration(self, testnet_settings):
        """Test line 64: Unknown network error"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Manually set invalid network to trigger error
        client_manager.settings.dydx_network = "INVALID_NETWORK"
        
        with pytest.raises(ValueError, match="Unknown network: INVALID_NETWORK"):
            client_manager._get_network()

    @pytest.mark.asyncio
    async def test_get_account_balance_auto_connect(self, testnet_settings):
        """Test line 120: Auto-connect when no client"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock connect method
        connect_called = False
        async def mock_connect():
            nonlocal connect_called
            connect_called = True
            # Setup mock client after connect
            mock_indexer = AsyncMock()
            mock_account = AsyncMock()
            mock_account.get_subaccount = AsyncMock(return_value={"balance": "500"})
            mock_indexer.account = mock_account
            client_manager._indexer_client = mock_indexer
        
        client_manager.connect = mock_connect
        
        result = await client_manager.get_account_balance("test_address")
        
        assert connect_called
        assert result == {"balance": "500"}

    @pytest.mark.asyncio
    async def test_get_account_balance_exception(self, testnet_settings):
        """Test lines 125-127: Exception handling in get_account_balance"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock client that raises exception
        mock_indexer = AsyncMock()
        mock_account = AsyncMock()
        mock_account.get_subaccount = AsyncMock(side_effect=Exception("Network timeout"))
        mock_indexer.account = mock_account
        client_manager._indexer_client = mock_indexer
        
        with pytest.raises(DydxClientError, match="Balance query failed: Network timeout"):
            await client_manager.get_account_balance("test_address")

    @pytest.mark.asyncio
    async def test_get_markets_auto_connect(self, testnet_settings):
        """Test line 133: Auto-connect when no client"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock connect method
        connect_called = False
        async def mock_connect():
            nonlocal connect_called
            connect_called = True
            # Setup mock client after connect
            mock_indexer = AsyncMock()
            mock_markets = AsyncMock()
            mock_markets.get_perpetual_markets = AsyncMock(return_value={"markets": {"BTC-USD": {}}})
            mock_indexer.markets = mock_markets
            client_manager._indexer_client = mock_indexer
        
        client_manager.connect = mock_connect
        
        result = await client_manager.get_markets()
        
        assert connect_called
        assert result == {"markets": {"BTC-USD": {}}}

    @pytest.mark.asyncio
    async def test_get_markets_exception(self, testnet_settings):
        """Test lines 138-140: Exception handling in get_markets"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock client that raises exception
        mock_indexer = AsyncMock()
        mock_markets = AsyncMock()
        mock_markets.get_perpetual_markets = AsyncMock(side_effect=Exception("API error"))
        mock_indexer.markets = mock_markets
        client_manager._indexer_client = mock_indexer
        
        with pytest.raises(DydxClientError, match="Markets query failed: API error"):
            await client_manager.get_markets()

    @pytest.mark.asyncio
    async def test_disconnect_with_sync_close_method(self, testnet_settings):
        """Test sync close method handling in disconnect"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Create mock socket with sync close method
        mock_socket = MagicMock()
        mock_socket.close = MagicMock()  # Synchronous close method
        
        client_manager._indexer_socket = mock_socket
        client_manager._is_connected = True
        
        await client_manager.disconnect()
        
        # Verify sync close was called
        mock_socket.close.assert_called_once()
        assert not client_manager.is_connected

    @pytest.mark.asyncio
    async def test_disconnect_with_async_close_method(self, testnet_settings):
        """Test async close method handling in disconnect"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Create mock socket with async close method
        mock_socket = MagicMock()
        async def async_close():
            pass
        mock_socket.close = async_close
        
        client_manager._indexer_socket = mock_socket
        client_manager._is_connected = True
        
        await client_manager.disconnect()
        
        assert not client_manager.is_connected

    @pytest.mark.asyncio
    async def test_disconnect_no_close_method(self, testnet_settings):
        """Test disconnect when socket has no close method"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Create mock socket without close method
        mock_socket = MagicMock(spec=[])  # Empty spec = no methods
        
        client_manager._indexer_socket = mock_socket
        client_manager._is_connected = True
        
        await client_manager.disconnect()
        
        assert not client_manager.is_connected

    @pytest.mark.asyncio
    async def test_disconnect_close_method_not_callable(self, testnet_settings):
        """Test disconnect when close attribute is not callable"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Create mock socket with close attribute that's not callable
        mock_socket = MagicMock()
        mock_socket.close = "not_callable"
        
        client_manager._indexer_socket = mock_socket
        client_manager._is_connected = True
        
        await client_manager.disconnect()
        
        assert not client_manager.is_connected

    @pytest.mark.asyncio
    async def test_health_check_exception_handling(self, testnet_settings):
        """Test lines 237-238: Health check exception handling"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock wallet that raises exception when accessing address
        mock_wallet = MagicMock()
        type(mock_wallet).address = PropertyMock(side_effect=Exception("Wallet error"))
        client_manager._wallet = mock_wallet
        
        # Should not raise exception, but handle gracefully
        health = await client_manager.health_check()
        
        # Basic health info should still be present
        assert "indexer_client" in health
        assert "indexer_socket" in health
        assert "node_client" in health

    @pytest.mark.asyncio
    async def test_health_check_wallet_with_no_address(self, testnet_settings):
        """Test wallet health check when address is None/empty"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock wallet with no address
        mock_wallet = MagicMock()
        mock_wallet.address = None
        client_manager._wallet = mock_wallet
        
        health = await client_manager.health_check()
        
        assert health["wallet"] is False

    @pytest.mark.asyncio
    async def test_health_check_wallet_with_empty_address(self, testnet_settings):
        """Test wallet health check when address is empty string"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock wallet with empty address
        mock_wallet = MagicMock()
        mock_wallet.address = ""
        client_manager._wallet = mock_wallet
        
        health = await client_manager.health_check()
        
        assert health["wallet"] is False

    @pytest.mark.asyncio
    async def test_health_check_wallet_with_valid_address(self, testnet_settings):
        """Test wallet health check when address is valid"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock wallet with valid address
        mock_wallet = MagicMock()
        mock_wallet.address = "dydx1valid_address_here"
        client_manager._wallet = mock_wallet

        health = await client_manager.health_check()

        assert health["wallet"] is True

    @pytest.mark.asyncio
    async def test_connect_with_wallet_mnemonic(self, settings_with_wallet):
        """Test connection with wallet mnemonic provided - wallet creation is separate step"""
        client_manager = DydxClientManager(settings_with_wallet)

        with patch('src.dydx_bot.connection.dydx_client.IndexerClient') as mock_indexer_client, \
             patch('src.dydx_bot.connection.dydx_client.IndexerSocket') as mock_socket_client, \
             patch('src.dydx_bot.connection.dydx_client.NodeClient') as mock_node_client:

            # Mock successful creation
            mock_indexer_client.return_value = AsyncMock()
            mock_socket_client.return_value = AsyncMock()
            mock_node_client_instance = AsyncMock()
            mock_node_client.connect = AsyncMock(return_value=mock_node_client_instance)

            await client_manager.connect()

            # Verify connection was successful (wallet creation is separate)
            assert client_manager.is_connected
            assert client_manager.indexer_client is not None
            assert client_manager.node_client is not None
            # Wallet should still be None since create_wallet() wasn't called
            assert client_manager.wallet is None

    @pytest.mark.asyncio
    async def test_connect_wallet_creation_failure(self, settings_with_wallet):
        """Test create_wallet method failure - this is a separate step from connect"""
        client_manager = DydxClientManager(settings_with_wallet)

        with patch('src.dydx_bot.connection.dydx_client.IndexerClient') as mock_indexer_client, \
             patch('src.dydx_bot.connection.dydx_client.IndexerSocket') as mock_socket_client, \
             patch('src.dydx_bot.connection.dydx_client.NodeClient') as mock_node_client, \
             patch('src.dydx_bot.connection.dydx_client.Wallet') as mock_wallet_class:

            # Mock successful client creation
            mock_indexer_client.return_value = AsyncMock()
            mock_socket_client.return_value = AsyncMock()
            mock_node_client_instance = AsyncMock()
            mock_node_client.connect = AsyncMock(return_value=mock_node_client_instance)

            # Connect first
            await client_manager.connect()
            
            # Mock wallet creation failure
            mock_wallet_class.from_mnemonic = AsyncMock(side_effect=Exception("Invalid mnemonic"))

            # Test wallet creation failure (separate from connect)
            with pytest.raises(DydxClientError, match="Wallet creation failed:"):
                await client_manager.create_wallet(
                    settings_with_wallet.dydx_mnemonic, 
                    "dydx1test_address"
                )

    @pytest.mark.asyncio
    async def test_create_wallet_success(self, settings_with_wallet):
        """Test successful wallet creation"""
        client_manager = DydxClientManager(settings_with_wallet)

        with patch('src.dydx_bot.connection.dydx_client.IndexerClient') as mock_indexer_client, \
             patch('src.dydx_bot.connection.dydx_client.IndexerSocket') as mock_socket_client, \
             patch('src.dydx_bot.connection.dydx_client.NodeClient') as mock_node_client, \
             patch('src.dydx_bot.connection.dydx_client.Wallet') as mock_wallet_class:

            # Mock successful client creation
            mock_indexer_client.return_value = AsyncMock()
            mock_socket_client.return_value = AsyncMock()
            mock_node_client_instance = AsyncMock()
            mock_node_client.connect = AsyncMock(return_value=mock_node_client_instance)

            # Connect first
            await client_manager.connect()
            
            # Mock successful wallet creation
            mock_wallet_instance = MagicMock()
            mock_wallet_instance.address = "dydx1test_wallet_address"
            mock_wallet_class.from_mnemonic = AsyncMock(return_value=mock_wallet_instance)

            # Test wallet creation success
            wallet = await client_manager.create_wallet(
                settings_with_wallet.dydx_mnemonic, 
                "dydx1test_address"
            )

            # Verify wallet was created and stored
            assert wallet is not None
            assert wallet.address == "dydx1test_wallet_address"
            assert client_manager.wallet is wallet
            mock_wallet_class.from_mnemonic.assert_called_once_with(
                mock_node_client_instance, 
                settings_with_wallet.dydx_mnemonic,
                "dydx1test_address"
            )

    @pytest.mark.asyncio
    async def test_create_wallet_auto_connect(self, settings_with_wallet):
        """Test create_wallet automatically connects if not connected"""
        client_manager = DydxClientManager(settings_with_wallet)

        with patch('src.dydx_bot.connection.dydx_client.IndexerClient') as mock_indexer_client, \
             patch('src.dydx_bot.connection.dydx_client.IndexerSocket') as mock_socket_client, \
             patch('src.dydx_bot.connection.dydx_client.NodeClient') as mock_node_client, \
             patch('src.dydx_bot.connection.dydx_client.Wallet') as mock_wallet_class:

            # Mock successful client creation
            mock_indexer_client.return_value = AsyncMock()
            mock_socket_client.return_value = AsyncMock()
            mock_node_client_instance = AsyncMock()
            mock_node_client.connect = AsyncMock(return_value=mock_node_client_instance)
            
            # Mock successful wallet creation
            mock_wallet_instance = MagicMock()
            mock_wallet_instance.address = "dydx1test_wallet_address"
            mock_wallet_class.from_mnemonic = AsyncMock(return_value=mock_wallet_instance)

            # Test create_wallet without connecting first (should auto-connect)
            wallet = await client_manager.create_wallet(
                settings_with_wallet.dydx_mnemonic, 
                "dydx1test_address"
            )

            # Verify wallet was created and connect was called
            assert wallet is not None
            assert wallet.address == "dydx1test_wallet_address"
            assert client_manager.wallet is wallet
            # Verify connect was called due to missing node_client
            mock_node_client.connect.assert_called_once()

    def test_mainnet_network_configuration(self, mainnet_settings):
        """Test mainnet network configuration"""
        client_manager = DydxClientManager(mainnet_settings)
        network = client_manager._get_network()
        
        assert network.node.chain_id == "dydx-mainnet-1"
        assert "indexer.dydx.exchange" in network.rest_indexer

    @pytest.mark.asyncio
    async def test_disconnect_exception_propagation(self, testnet_settings):
        """Test that disconnect exceptions are properly propagated"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock socket that raises exception on close
        mock_socket = AsyncMock()
        mock_socket.close = AsyncMock(side_effect=Exception("Socket close failed"))
        
        client_manager._indexer_socket = mock_socket
        client_manager._is_connected = True
        
        with pytest.raises(DydxClientError, match="Disconnection failed: Socket close failed"):
            await client_manager.disconnect()

    def test_property_access_edge_cases(self, testnet_settings):
        """Test property access edge cases"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Test accessing properties when not initialized
        with pytest.raises(RuntimeError, match="IndexerClient not initialized"):
            _ = client_manager.indexer_client
            
        with pytest.raises(RuntimeError, match="NodeClient not initialized"):
            _ = client_manager.node_client
            
        # Wallet returns None when not initialized (no exception)
        assert client_manager.wallet is None

    @pytest.mark.asyncio
    async def test_complex_disconnect_scenario(self, testnet_settings):
        """Test complex disconnect scenario with all components"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Setup all components
        mock_indexer = AsyncMock()
        mock_socket = AsyncMock()
        mock_socket.close = AsyncMock()
        mock_node = AsyncMock()
        mock_wallet = MagicMock()
        
        client_manager._indexer_client = mock_indexer
        client_manager._indexer_socket = mock_socket
        client_manager._node_client = mock_node
        client_manager._wallet = mock_wallet
        client_manager._is_connected = True
        
        await client_manager.disconnect()
        
        # Verify all components are cleaned up
        assert client_manager._indexer_client is None
        assert client_manager._indexer_socket is None
        assert client_manager._node_client is None
        assert client_manager._wallet is None
        assert not client_manager.is_connected
        
        # Verify close was called
        mock_socket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure_exception_handling(self, testnet_settings):
        """Test lines 91-93: Connection failure exception handling in connect method"""
        client_manager = DydxClientManager(testnet_settings)
        
        with patch('src.dydx_bot.connection.dydx_client.IndexerClient') as mock_indexer_client, \
             patch('src.dydx_bot.connection.dydx_client.IndexerSocket') as mock_socket_client, \
             patch('src.dydx_bot.connection.dydx_client.NodeClient') as mock_node_client:

            # Mock NodeClient.connect to raise exception during creation
            mock_node_client.connect = AsyncMock(side_effect=Exception("Failed to connect to dYdX v4"))
            
            # This should trigger the exception handler in lines 91-93
            with pytest.raises(DydxClientError, match="Connection failed:"):
                await client_manager.connect()

    def test_indexer_socket_not_initialized(self, testnet_settings):
        """Test lines 153-155: IndexerSocket property when not initialized"""
        client_manager = DydxClientManager(testnet_settings)
        
        with pytest.raises(RuntimeError, match="IndexerSocket not initialized. Call connect\\(\\) first."):
            _ = client_manager.indexer_socket

    @pytest.mark.asyncio
    async def test_health_check_indexer_client_failure(self, testnet_settings):
        """Test lines 219-224: Health check when IndexerClient exists but fails"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock IndexerClient that will fail during health check
        mock_indexer_client = MagicMock()
        mock_utility = MagicMock()
        mock_utility.get_time = AsyncMock(side_effect=Exception("API call failed"))
        mock_indexer_client.utility = mock_utility
        
        # Set the mocked client directly
        client_manager._indexer_client = mock_indexer_client
        
        health = await client_manager.health_check()
        
        assert health["indexer_client"] is False
        mock_utility.get_time.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_indexer_socket_exists(self, testnet_settings):
        """Test line 229: Health check when IndexerSocket exists"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock IndexerSocket with connected property
        mock_indexer_socket = MagicMock()
        mock_indexer_socket.connected = True
        
        client_manager._indexer_socket = mock_indexer_socket
        
        health = await client_manager.health_check()
        
        assert health["indexer_socket"] is True

    @pytest.mark.asyncio
    async def test_health_check_node_client_failure(self, testnet_settings):
        """Test lines 233-236: Health check when NodeClient exists but fails"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock NodeClient that will fail during health check
        mock_node_client = MagicMock()
        mock_node_client.latest_block_height = AsyncMock(side_effect=Exception("Node connection failed"))
        
        client_manager._node_client = mock_node_client
        
        health = await client_manager.health_check()
        
        assert health["node_client"] is False
        mock_node_client.latest_block_height.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_wallet_exists(self, testnet_settings):
        """Test lines 237-238: Health check when wallet exists"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock wallet with address
        mock_wallet = MagicMock()
        mock_wallet.address = "dydx1test_address"
        
        client_manager._wallet = mock_wallet
        
        health = await client_manager.health_check()
        
        assert health["wallet"] is True

    @pytest.mark.asyncio
    async def test_health_check_indexer_client_success(self, testnet_settings):
        """Test line 222: Health check when IndexerClient succeeds"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock IndexerClient that will succeed during health check
        mock_indexer_client = MagicMock()
        mock_utility = MagicMock()
        mock_utility.get_time = AsyncMock(return_value={"time": "2024-01-01T00:00:00Z"})
        mock_indexer_client.utility = mock_utility
        
        # Set the mocked client directly
        client_manager._indexer_client = mock_indexer_client
        
        health = await client_manager.health_check()
        
        assert health["indexer_client"] is True
        mock_utility.get_time.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_node_client_success(self, testnet_settings):
        """Test line 236: Health check when NodeClient succeeds"""
        client_manager = DydxClientManager(testnet_settings)
        
        # Mock NodeClient that will succeed during health check
        mock_node_client = MagicMock()
        mock_node_client.latest_block_height = AsyncMock(return_value=12345)
        
        client_manager._node_client = mock_node_client
        
        health = await client_manager.health_check()
        
        assert health["node_client"] is True
        mock_node_client.latest_block_height.assert_called_once()
