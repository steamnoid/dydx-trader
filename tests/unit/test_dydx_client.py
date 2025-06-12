"""
Unit tests for dYdX v4 Client Manager

Tests the protocol-first wrapper around official dydx-v4-client.
Focus on testing integration patterns rather than comprehensive abstractions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.dydx_bot.connection.dydx_client import DydxClientManager, DydxClientError
from src.dydx_bot.config.settings import Settings, NetworkType


class TestDydxClientManager:
    """Test dYdX v4 client manager protocol integration"""
    
    @pytest.fixture
    def settings(self):
        """Create test settings"""
        return Settings(
            dydx_network=NetworkType.TESTNET,
            dydx_mnemonic="test mnemonic phrase here for testing purposes only",
            dydx_address="dydx1test_address_here",
            risk_max_leverage=10.0,
            risk_tolerance=0.05
        )
    
    @pytest.fixture  
    def client_manager(self, settings):
        """Create client manager instance"""
        return DydxClientManager(settings)
    
    def test_init(self, client_manager, settings):
        """Test client manager initialization"""
        assert client_manager.settings == settings
        assert not client_manager.is_connected
        assert client_manager.network is not None
        assert client_manager._wallet is None
        assert client_manager._indexer_client is None
        assert client_manager._indexer_socket is None
        assert client_manager._node_client is None
    
    def test_get_network_testnet(self, client_manager):
        """Test network configuration for testnet"""
        # Network should be TESTNET
        assert client_manager.network.node.chain_id == "dydx-testnet-4"
        assert "testnet" in client_manager.network.rest_indexer.lower()
    
    @patch('src.dydx_bot.connection.dydx_client.NodeClient')
    @patch('src.dydx_bot.connection.dydx_client.IndexerClient')
    @patch('src.dydx_bot.connection.dydx_client.IndexerSocket')
    async def test_connect_success(self, mock_socket, mock_indexer, mock_node, client_manager):
        """Test successful connection to dYdX v4"""
        # Mock NodeClient.connect as an async method
        mock_node_instance = AsyncMock()
        mock_node.connect = AsyncMock(return_value=mock_node_instance)
        
        # Mock other clients
        mock_indexer_instance = MagicMock()
        mock_indexer.return_value = mock_indexer_instance
        
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        
        # Test connection
        await client_manager.connect()
        
        # Verify calls
        mock_node.connect.assert_called_once_with(client_manager.network.node)
        mock_indexer.assert_called_once_with(client_manager.network.rest_indexer)
        mock_socket.assert_called_once_with(client_manager.network.websocket_indexer)
        
        # Verify state
        assert client_manager.is_connected
        assert client_manager._node_client == mock_node_instance
        assert client_manager._indexer_client == mock_indexer_instance
        assert client_manager._indexer_socket == mock_socket_instance
    
    @patch('src.dydx_bot.connection.dydx_client.NodeClient')
    async def test_connect_failure(self, mock_node, client_manager):
        """Test connection failure handling"""
        # Mock connection failure
        mock_node.connect = AsyncMock(side_effect=Exception("Connection failed"))
        
        # Test connection failure
        with pytest.raises(DydxClientError, match="Connection failed"):
            await client_manager.connect()
        
        # Verify state remains disconnected
        assert not client_manager.is_connected
    
    @patch('src.dydx_bot.connection.dydx_client.Wallet')
    async def test_create_wallet_success(self, mock_wallet, client_manager):
        """Test successful wallet creation"""
        # Setup mocks
        mock_node_client = AsyncMock()
        client_manager._node_client = mock_node_client
        
        mock_wallet_instance = MagicMock()
        mock_wallet_instance.address = "dydx1test_wallet_address"
        mock_wallet.from_mnemonic = AsyncMock(return_value=mock_wallet_instance)
        
        # Test wallet creation
        mnemonic = "test mnemonic"
        address = "dydx1test_address"
        
        result = await client_manager.create_wallet(mnemonic, address)
        
        # Verify calls
        mock_wallet.from_mnemonic.assert_called_once_with(
            mock_node_client, mnemonic, address
        )
        
        # Verify result
        assert result == mock_wallet_instance
        assert client_manager._wallet == mock_wallet_instance
    
    @patch('src.dydx_bot.connection.dydx_client.Wallet')
    async def test_create_wallet_auto_connect(self, mock_wallet, client_manager):
        """Test wallet creation triggers connection if not connected"""
        # Setup mocks
        mock_wallet_instance = MagicMock()
        mock_wallet_instance.address = "dydx1test_wallet_address"
        mock_wallet.from_mnemonic = AsyncMock(return_value=mock_wallet_instance)
        
        # Mock connect method
        with patch.object(client_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_node_client = AsyncMock()
            
            async def connect_side_effect():
                client_manager._node_client = mock_node_client
                client_manager._is_connected = True
            
            mock_connect.side_effect = connect_side_effect
            
            # Test wallet creation without prior connection
            result = await client_manager.create_wallet("test", "address")
            
            # Verify connect was called
            mock_connect.assert_called_once()
            
            # Verify wallet creation
            mock_wallet.from_mnemonic.assert_called_once_with(
                mock_node_client, "test", "address"
            )
    
    @patch('src.dydx_bot.connection.dydx_client.Wallet')
    async def test_create_wallet_failure(self, mock_wallet, client_manager):
        """Test wallet creation failure handling"""
        # Setup mocks
        mock_node_client = AsyncMock()
        client_manager._node_client = mock_node_client
        
        # Mock wallet creation failure
        mock_wallet.from_mnemonic = AsyncMock(side_effect=Exception("Wallet creation failed"))
        
        # Test wallet creation failure
        with pytest.raises(DydxClientError, match="Wallet creation failed"):
            await client_manager.create_wallet("test", "address")
    
    async def test_get_account_balance_success(self, client_manager):
        """Test successful account balance retrieval"""
        # Setup mocks
        mock_indexer = AsyncMock()
        mock_indexer.account.get_subaccount.return_value = {"balance": "1000"}
        client_manager._indexer_client = mock_indexer
        
        # Test balance retrieval
        result = await client_manager.get_account_balance("test_address")
        
        # Verify calls
        mock_indexer.account.get_subaccount.assert_called_once_with("test_address", 0)
        
        # Verify result
        assert result == {"balance": "1000"}
    
    async def test_get_markets_success(self, client_manager):
        """Test successful markets retrieval"""
        # Setup mocks
        mock_indexer = AsyncMock()
        mock_indexer.markets.get_perpetual_markets.return_value = {"markets": {}}
        client_manager._indexer_client = mock_indexer
        
        # Test markets retrieval
        result = await client_manager.get_markets()
        
        # Verify calls
        mock_indexer.markets.get_perpetual_markets.assert_called_once()
        
        # Verify result
        assert result == {"markets": {}}
    
    def test_property_access_uninitialized(self, client_manager):
        """Test property access when clients not initialized"""
        with pytest.raises(RuntimeError, match="IndexerClient not initialized"):
            _ = client_manager.indexer_client
        
        with pytest.raises(RuntimeError, match="IndexerSocket not initialized"):
            _ = client_manager.indexer_socket
        
        with pytest.raises(RuntimeError, match="NodeClient not initialized"):
            _ = client_manager.node_client
        
        # Wallet should return None when not initialized
        assert client_manager.wallet is None
    
    def test_property_access_initialized(self, client_manager):
        """Test property access when clients are initialized"""
        # Setup mock clients
        mock_indexer = MagicMock()
        mock_socket = MagicMock()
        mock_node = MagicMock()
        mock_wallet = MagicMock()
        
        client_manager._indexer_client = mock_indexer
        client_manager._indexer_socket = mock_socket
        client_manager._node_client = mock_node
        client_manager._wallet = mock_wallet
        
        # Test property access
        assert client_manager.indexer_client == mock_indexer
        assert client_manager.indexer_socket == mock_socket
        assert client_manager.node_client == mock_node
        assert client_manager.wallet == mock_wallet
    
    async def test_disconnect_success(self, client_manager):
        """Test successful disconnection"""
        # Setup mock clients
        mock_socket = AsyncMock()
        mock_socket.close = AsyncMock()
        
        client_manager._indexer_client = MagicMock()
        client_manager._indexer_socket = mock_socket
        client_manager._node_client = MagicMock()
        client_manager._wallet = MagicMock()
        client_manager._is_connected = True
        
        # Test disconnection
        await client_manager.disconnect()
        
        # Verify socket close was called
        mock_socket.close.assert_called_once()
        
        # Verify clients are reset
        assert client_manager._indexer_client is None
        assert client_manager._indexer_socket is None
        assert client_manager._node_client is None
        assert client_manager._wallet is None
        assert not client_manager.is_connected
    
    async def test_health_check_all_healthy(self, client_manager):
        """Test health check when all components are healthy"""
        # Setup mocks
        mock_indexer = AsyncMock()
        mock_indexer.utility.get_time.return_value = {"time": "2024-01-01"}
        
        mock_socket = MagicMock()
        mock_socket.connected = True
        
        mock_node = AsyncMock()
        mock_node.latest_block_height.return_value = 12345
        
        mock_wallet = MagicMock()
        mock_wallet.address = "dydx1test_address"
        
        client_manager._indexer_client = mock_indexer
        client_manager._indexer_socket = mock_socket
        client_manager._node_client = mock_node
        client_manager._wallet = mock_wallet
        
        # Test health check
        health = await client_manager.health_check()
        
        # Verify all components are healthy
        assert health["indexer_client"] is True
        assert health["indexer_socket"] is True
        assert health["node_client"] is True
        assert health["wallet"] is True
    
    async def test_health_check_all_unhealthy(self, client_manager):
        """Test health check when all components are unhealthy"""
        # Setup mocks that fail
        mock_indexer = AsyncMock()
        mock_indexer.utility.get_time.side_effect = Exception("API error")
        
        mock_socket = MagicMock()
        mock_socket.connected = False
        
        mock_node = AsyncMock()
        mock_node.latest_block_height.side_effect = Exception("Node error")
        
        client_manager._indexer_client = mock_indexer
        client_manager._indexer_socket = mock_socket
        client_manager._node_client = mock_node
        client_manager._wallet = None
        
        # Test health check
        health = await client_manager.health_check()
        
        # Verify all components are unhealthy
        assert health["indexer_client"] is False
        assert health["indexer_socket"] is False
        assert health["node_client"] is False
        assert health["wallet"] is False
    
    def test_unknown_network_error(self, settings):
        """Test that unknown network raises ValueError"""
        client_manager = DydxClientManager(settings)
        
        # Temporarily change to invalid network
        original_network = client_manager.settings.dydx_network
        client_manager.settings.dydx_network = "INVALID_NETWORK"
        
        with pytest.raises(ValueError, match="Unknown network: INVALID_NETWORK"):
            client_manager._get_network()
        
        # Restore original
        client_manager.settings.dydx_network = original_network
