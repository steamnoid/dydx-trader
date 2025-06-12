"""
Protocol-First dYdX v4 Client Manager

Direct wrapper around official dydx-v4-client with minimal abstractions.
Leverages client's built-in connection management, authentication, and error handling.
"""

import asyncio
import logging
from typing import Optional, Dict, Any

from dydx_v4_client.indexer.rest.indexer_client import IndexerClient
from dydx_v4_client.indexer.socket.websocket import IndexerSocket
from dydx_v4_client.node.client import NodeClient
from dydx_v4_client.network import TESTNET, make_mainnet
from dydx_v4_client.wallet import Wallet

from ..config.settings import Settings, NetworkType


class DydxClientError(Exception):
    """Custom exception for dYdX client errors"""
    pass


class DydxClientManager:
    """
    Protocol-First dYdX v4 Client Manager
    
    Minimal wrapper around official dydx-v4-client components:
    - IndexerSocket: WebSocket connections for real-time data
    - IndexerClient: REST API for queries and historical data  
    - NodeClient: Blockchain operations for trading
    - Wallet: Authentication and key management
    
    Philosophy: Use client's patterns directly, don't over-abstract.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._logger = logging.getLogger(__name__)
        self._wallet: Optional[Wallet] = None
        self._indexer_client: Optional[IndexerClient] = None
        self._indexer_socket: Optional[IndexerSocket] = None
        self._node_client: Optional[NodeClient] = None
        self._is_connected = False
        
        # Use official client network configurations
        self.network = self._get_network()
    
    def _get_network(self):
        """Get network configuration using official client patterns"""
        if self.settings.dydx_network == NetworkType.TESTNET:
            return TESTNET
        elif self.settings.dydx_network == NetworkType.MAINNET:
            # For mainnet, we'd need the actual endpoints
            # Using placeholders for now - would need real mainnet endpoints
            return make_mainnet(
                rest_indexer="https://indexer.dydx.exchange",
                websocket_indexer="wss://indexer.dydx.exchange/v4/ws", 
                node_url="dydx-mainnet-full-rpc.public.blastapi.io:443"
            )
        else:
            raise ValueError(f"Unknown network: {self.settings.dydx_network}")
    
    async def connect(self) -> None:
        """
        Connect to dYdX v4 network using official client patterns
        
        Based on examples from: 
        - https://github.com/dydxprotocol/v4-clients/tree/main/v4-client-py-v2/examples
        """
        try:
            self._logger.info(f"Connecting to dYdX v4 {self.settings.dydx_network}")
            
            # Create NodeClient first (required for wallet creation)
            self._node_client = await NodeClient.connect(self.network.node)
            self._logger.info("NodeClient connected")
            
            # Create IndexerClient for REST API operations
            self._indexer_client = IndexerClient(self.network.rest_indexer)
            self._logger.info("IndexerClient created")
            
            # Create IndexerSocket for WebSocket operations
            self._indexer_socket = IndexerSocket(self.network.websocket_indexer)
            self._logger.info("IndexerSocket created")
            
            self._is_connected = True
            self._logger.info("dYdX v4 client connection complete")
            
        except Exception as e:
            self._logger.error(f"Failed to connect to dYdX v4: {e}")
            raise DydxClientError(f"Connection failed: {e}")
    
    async def create_wallet(self, mnemonic: str, address: str) -> Wallet:
        """Create wallet from mnemonic using official client patterns"""
        try:
            if not self._node_client:
                await self.connect()
            
            # Create wallet using NodeClient (required by dydx-v4-client API)
            # Based on examples: Wallet.from_mnemonic(node, mnemonic, address)
            # Note: Wallet.from_mnemonic is async based on the examples
            wallet = await Wallet.from_mnemonic(
                self._node_client,  # Pass NodeClient as required by API
                mnemonic,
                address
            )
            self._wallet = wallet
            self._logger.info(f"Wallet created for address: {wallet.address}")
            return wallet
        except Exception as e:
            self._logger.error(f"Failed to create wallet: {e}")
            raise DydxClientError(f"Wallet creation failed: {e}")

    async def get_account_balance(self, address: str) -> dict:
        """Get account balance using IndexerClient"""
        try:
            if not self._indexer_client:
                await self.connect()
            
            # Use IndexerClient to get account balance
            response = await self._indexer_client.account.get_subaccount(address, 0)
            return response
        except Exception as e:
            self._logger.error(f"Failed to get account balance: {e}")
            raise DydxClientError(f"Balance query failed: {e}")
    
    async def get_markets(self) -> dict:
        """Get perpetual markets using IndexerClient"""
        try:
            if not self._indexer_client:
                await self.connect()
            
            # Use IndexerClient to get perpetual markets
            response = await self._indexer_client.markets.get_perpetual_markets()
            return response
        except Exception as e:
            self._logger.error(f"Failed to get markets: {e}")
            raise DydxClientError(f"Markets query failed: {e}")
    
    # Protocol-Native Client Access
    @property
    def indexer_client(self) -> IndexerClient:
        """Get IndexerClient for REST API operations"""
        if not self._indexer_client:
            raise RuntimeError("IndexerClient not initialized. Call connect() first.")
        return self._indexer_client
    
    @property 
    def indexer_socket(self) -> IndexerSocket:
        """Get IndexerSocket for WebSocket operations"""
        if not self._indexer_socket:
            raise RuntimeError("IndexerSocket not initialized. Call connect() first.")
        return self._indexer_socket
    
    @property
    def node_client(self) -> NodeClient:
        """Get NodeClient for blockchain operations"""
        if not self._node_client:
            raise RuntimeError("NodeClient not initialized. Call connect() first.")
        return self._node_client
    
    @property
    def wallet(self) -> Optional[Wallet]:
        """Get wallet for authentication (optional)"""
        return self._wallet
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected and ready"""
        return self._is_connected
    
    async def disconnect(self) -> None:
        """Disconnect all client connections"""
        try:
            self._logger.info("Disconnecting dYdX v4 clients")
            
            # Close WebSocket connection if it has a close method
            if self._indexer_socket and hasattr(self._indexer_socket, 'close'):
                close_method = getattr(self._indexer_socket, 'close')
                if callable(close_method):
                    # Check if close method is async
                    import asyncio
                    if asyncio.iscoroutinefunction(close_method):
                        await close_method()
                    else:
                        close_method()
            
            # Reset clients
            self._indexer_client = None
            self._indexer_socket = None
            self._node_client = None
            self._wallet = None
            self._is_connected = False
            
            self._logger.info("dYdX v4 client disconnection complete")
            
        except Exception as e:
            self._logger.error(f"Error during client disconnection: {e}")
            raise DydxClientError(f"Disconnection failed: {e}")
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Perform health check on all client components
        
        Uses official client health check methods where available.
        """
        health = {
            "indexer_client": False,
            "indexer_socket": False, 
            "node_client": False,
            "wallet": False
        }
        
        try:
            # Check IndexerClient (REST API)
            if self._indexer_client:
                try:
                    # Try a simple API call to test connectivity
                    response = await self._indexer_client.utility.get_time()
                    health["indexer_client"] = bool(response)
                except:
                    health["indexer_client"] = False
            
            # Check IndexerSocket (WebSocket) 
            if self._indexer_socket:
                # Check if socket is connected (if property exists)
                health["indexer_socket"] = getattr(self._indexer_socket, 'connected', False)
            
            # Check NodeClient 
            if self._node_client:
                try:
                    # Try to get latest block height as a health check
                    await self._node_client.latest_block_height()
                    health["node_client"] = True
                except:
                    health["node_client"] = False
            
            # Check Wallet
            if self._wallet:
                health["wallet"] = bool(self._wallet.address)
                
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
        
        return health
