"""
Protocol-First Configuration for dYdX v4 Client Integration

Uses official dydx-v4-client configuration patterns directly.
No custom abstractions - leverage client's built-in settings.
"""

from enum import Enum
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NetworkType(str, Enum):
    """dYdX v4 Network Types - matches client enum exactly"""
    TESTNET = "testnet"
    MAINNET = "mainnet"


class Settings(BaseSettings):
    """
    Protocol-First Settings
    
    Follows dydx-v4-client configuration patterns exactly.
    Minimal custom logic - leverage client's built-in network configs.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # dYdX v4 Protocol Configuration - Official Client Format
    dydx_network: NetworkType = Field(
        default=NetworkType.TESTNET,
        description="dYdX v4 network (testnet/mainnet)"
    )
    
    dydx_mnemonic: Optional[str] = Field(
        default=None,
        description="Wallet mnemonic for dYdX v4 client authentication"
    )
    
    dydx_wallet_address: Optional[str] = Field(
        default=None,
        description="Wallet address for dYdX v4 operations"
    )
    
    dydx_private_key: Optional[str] = Field(
        default=None,
        description="Private key for dYdX v4 signing operations"
    )
    
    # Optional: Override default URLs (client has built-in defaults)
    dydx_node_url: Optional[str] = Field(
        default=None,
        description="Custom dYdX v4 node URL (optional - client has defaults)"
    )
    
    dydx_indexer_url: Optional[str] = Field(
        default=None,
        description="Custom dYdX v4 indexer URL (optional - client has defaults)"
    )
    
    # Application Settings
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Trading Configuration (Protocol-Native Values)
    paper_trading: bool = Field(
        default=True,
        description="Use paper trading mode"
    )
    
    initial_capital: float = Field(
        default=10000.0,
        description="Initial capital in USDC for trading"
    )
    
    max_leverage: float = Field(
        default=10.0,
        description="Maximum leverage to use (matches dYdX v4 limits)"
    )
    
    risk_tolerance: float = Field(
        default=0.02,
        description="Risk tolerance as fraction of portfolio"
    )
    
    # Performance Limits
    max_memory_mb: int = Field(
        default=512,
        description="Maximum memory usage in MB"
    )
    
    max_cpu_percent: float = Field(
        default=25.0,
        description="Maximum CPU usage percentage"
    )
    
    def is_testnet(self) -> bool:
        """Check if using testnet configuration"""
        return self.dydx_network == NetworkType.TESTNET
    
    def is_mainnet(self) -> bool:
        """Check if using mainnet configuration"""
        return self.dydx_network == NetworkType.MAINNET
    
    def has_wallet_config(self) -> bool:
        """Check if wallet configuration is complete"""
        return bool(
            self.dydx_mnemonic 
            and self.dydx_wallet_address 
            and self.dydx_private_key
        )
    
    def validate_for_trading(self) -> None:
        """Validate configuration for trading operations"""
        if not self.has_wallet_config():
            raise ValueError(
                "Wallet configuration incomplete. Need mnemonic, address, and private key."
            )
        
        if self.max_leverage > 20.0:
            raise ValueError("Max leverage cannot exceed 20x (dYdX v4 limit)")
        
        if self.risk_tolerance > 0.1:
            raise ValueError("Risk tolerance cannot exceed 10% of portfolio")


# Global settings instance
settings = Settings()
