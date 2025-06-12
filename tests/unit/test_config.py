"""
Unit tests for protocol-first configuration

Tests dYdX v4 configuration following protocol patterns directly.
No over-engineered abstractions - test client compatibility.
"""

import pytest
from unittest.mock import patch, MagicMock

from dydx_bot.config.settings import Settings, NetworkType


class TestSettingsProtocolFirst:
    """Test settings using protocol-first approach"""
    
    def test_default_configuration(self):
        """Test default configuration matches protocol expectations"""
        settings = Settings()
        
        assert settings.dydx_network == NetworkType.TESTNET
        assert settings.paper_trading is True
        assert settings.initial_capital == 10000.0
        assert settings.max_leverage == 10.0
        assert settings.risk_tolerance == 0.02
        assert settings.log_level == "INFO"
        assert settings.debug is False
    
    def test_network_type_enum_protocol_compatibility(self):
        """Test NetworkType enum matches dydx-v4-client expectations"""
        assert NetworkType.TESTNET.value == "testnet"
        assert NetworkType.MAINNET.value == "mainnet"
        
        # Ensure string values work with protocol
        settings = Settings(dydx_network="testnet")
        assert settings.dydx_network == NetworkType.TESTNET
        
        settings = Settings(dydx_network="mainnet") 
        assert settings.dydx_network == NetworkType.MAINNET
    
    def test_testnet_mainnet_helpers(self):
        """Test network detection helpers"""
        testnet_settings = Settings(dydx_network=NetworkType.TESTNET)
        assert testnet_settings.is_testnet() is True
        assert testnet_settings.is_mainnet() is False
        
        mainnet_settings = Settings(dydx_network=NetworkType.MAINNET)
        assert mainnet_settings.is_testnet() is False
        assert mainnet_settings.is_mainnet() is True
    
    def test_wallet_configuration_validation(self):
        """Test wallet configuration validation for protocol compatibility"""
        # Incomplete wallet config
        settings = Settings()
        assert settings.has_wallet_config() is False
        
        # Complete wallet config
        settings = Settings(
            dydx_mnemonic="test mnemonic here",
            dydx_wallet_address="test_address", 
            dydx_private_key="test_private_key"
        )
        assert settings.has_wallet_config() is True
    
    def test_trading_validation_protocol_limits(self):
        """Test trading validation against dYdX v4 protocol limits"""
        # Valid configuration
        settings = Settings(
            dydx_mnemonic="test mnemonic",
            dydx_wallet_address="test_address",
            dydx_private_key="test_key",
            max_leverage=10.0,
            risk_tolerance=0.05
        )
        settings.validate_for_trading()  # Should not raise
        
        # Invalid: missing wallet config
        settings = Settings()
        with pytest.raises(ValueError, match="Wallet configuration incomplete"):
            settings.validate_for_trading()
        
        # Invalid: leverage exceeds protocol limit
        settings = Settings(
            dydx_mnemonic="test mnemonic",
            dydx_wallet_address="test_address", 
            dydx_private_key="test_key",
            max_leverage=25.0  # Exceeds dYdX v4 20x limit
        )
        with pytest.raises(ValueError, match="Max leverage cannot exceed 20x"):
            settings.validate_for_trading()
        
        # Invalid: risk tolerance too high
        settings = Settings(
            dydx_mnemonic="test mnemonic",
            dydx_wallet_address="test_address",
            dydx_private_key="test_key", 
            risk_tolerance=0.15  # 15% > 10% limit
        )
        with pytest.raises(ValueError, match="Risk tolerance cannot exceed 10%"):
            settings.validate_for_trading()
    
    @patch.dict("os.environ", {
        "DYDX_NETWORK": "mainnet",
        "DYDX_MNEMONIC": "env_mnemonic",
        "DYDX_WALLET_ADDRESS": "env_address",
        "DYDX_PRIVATE_KEY": "env_key",
        "PAPER_TRADING": "false",
        "MAX_LEVERAGE": "15.0",
        "LOG_LEVEL": "DEBUG"
    })
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables"""
        settings = Settings()
        
        assert settings.dydx_network == NetworkType.MAINNET
        assert settings.dydx_mnemonic == "env_mnemonic"
        assert settings.dydx_wallet_address == "env_address"
        assert settings.dydx_private_key == "env_key"
        assert settings.paper_trading is False
        assert settings.max_leverage == 15.0
        assert settings.log_level == "DEBUG"
    
    def test_optional_url_overrides(self):
        """Test optional URL overrides for custom endpoints"""
        settings = Settings(
            dydx_node_url="https://custom-node.example.com",
            dydx_indexer_url="https://custom-indexer.example.com"
        )
        
        assert settings.dydx_node_url == "https://custom-node.example.com"
        assert settings.dydx_indexer_url == "https://custom-indexer.example.com"
        
        # Test defaults (None means use client defaults)
        default_settings = Settings()
        assert default_settings.dydx_node_url is None
        assert default_settings.dydx_indexer_url is None
    
    def test_performance_limits_configuration(self):
        """Test performance limit configuration"""
        settings = Settings(
            max_memory_mb=1024,
            max_cpu_percent=50.0
        )
        
        assert settings.max_memory_mb == 1024
        assert settings.max_cpu_percent == 50.0


class TestSettingsEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_invalid_network_type(self):
        """Test invalid network type handling"""
        with pytest.raises(ValueError):
            Settings(dydx_network="invalid_network")
    
    def test_boundary_values_protocol_limits(self):
        """Test boundary values for protocol limits"""
        # Exactly at dYdX v4 20x leverage limit
        settings = Settings(
            dydx_mnemonic="test",
            dydx_wallet_address="test",
            dydx_private_key="test",
            max_leverage=20.0
        )
        settings.validate_for_trading()  # Should not raise
        
        # Exactly at 10% risk tolerance limit
        settings = Settings(
            dydx_mnemonic="test",
            dydx_wallet_address="test", 
            dydx_private_key="test",
            risk_tolerance=0.1
        )
        settings.validate_for_trading()  # Should not raise
    
    def test_case_insensitive_environment_variables(self):
        """Test case insensitive environment variable handling"""
        with patch.dict("os.environ", {"dydx_network": "testnet"}):
            settings = Settings()
            assert settings.dydx_network == NetworkType.TESTNET
