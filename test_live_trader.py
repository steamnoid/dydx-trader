#!/usr/bin/env python3
"""
Test-Driven Development for dYdX v4 Live Trading
Following STRICT TDD methodology: Red→Green→Refactor

Based on dYdX v4 official documentation and examples:
- Uses dydx_v4_client (v2) - the official modern client
- Supports both testnet and mainnet networks
- Implements proper async patterns for trading
"""

import pytest
import asyncio
import os
from live_trader import LiveTrader, LiveTraderConfig


def test_can_create_live_trader():
    """Test: Can create a LiveTrader instance"""
    trader = LiveTrader()
    assert trader is not None
    assert isinstance(trader, LiveTrader)


@pytest.mark.asyncio
async def test_can_connect_to_testnet():
    """Test: Can connect to dYdX v4 testnet using official client"""
    trader = LiveTrader()
    result = await trader.connect_to_testnet()
    assert result is True


@pytest.mark.asyncio
async def test_testnet_connection_actually_works():
    """Test: Testnet connection actually retrieves real account data with wallet"""
    # Test with actual testnet credentials provided by user
    testnet_mnemonic = "faint void funny program truth life pulse pioneer convince sting current child moment olympic concert lounge invest mirror piano yard extra strong reveal near"
    testnet_address = "dydx1rd8nkf25gv3jm8xnt8rzqdw3f0232spu49wfvq"
    
    config = LiveTraderConfig(
        network_type="testnet",
        wallet_mnemonic=testnet_mnemonic,
        wallet_address=testnet_address
    )
    
    trader = LiveTrader(config)
    await trader.connect_to_testnet()
    account_info = await trader.get_account_info()
    assert account_info is not None
    assert 'equity' in account_info


@pytest.mark.asyncio
async def test_can_authenticate_with_testnet_wallet():
    """Test: Can authenticate with testnet wallet using mnemonic"""
    # Test with actual testnet credentials provided by user
    testnet_mnemonic = "faint void funny program truth life pulse pioneer convince sting current child moment olympic concert lounge invest mirror piano yard extra strong reveal near"
    testnet_address = "dydx1rd8nkf25gv3jm8xnt8rzqdw3f0232spu49wfvq"
    
    config = LiveTraderConfig(
        network_type="testnet",
        wallet_mnemonic=testnet_mnemonic,
        wallet_address=testnet_address
    )
    
    trader = LiveTrader(config)
    connected = await trader.connect_to_testnet()
    assert connected is True
    
    # Verify wallet is properly authenticated
    assert trader.wallet is not None
    assert trader.wallet.address == testnet_address


@pytest.mark.asyncio
async def test_can_authenticate_with_mainnet_from_env():
    """Test: Can authenticate with mainnet using environment variables"""
    # Skip if env vars not set (for CI/CD)
    if 'DYDX_MNEMONIC' not in os.environ or 'DYDX_ADDRESS' not in os.environ:
        pytest.skip("Mainnet environment variables not set")
    
    config = LiveTraderConfig(network_type="mainnet")
    trader = LiveTrader(config)
    
    # Should read from environment
    connected = await trader.connect_to_mainnet()
    assert connected is True
    assert trader.wallet is not None
    assert trader.wallet.address == os.environ['DYDX_ADDRESS']


@pytest.mark.asyncio
async def test_real_account_info_from_testnet():
    """Test: Can fetch real account info from testnet with authenticated wallet"""
    testnet_mnemonic = "faint void funny program truth life pulse pioneer convince sting current child moment olympic concert lounge invest mirror piano yard extra strong reveal near"
    testnet_address = "dydx1rd8nkf25gv3jm8xnt8rzqdw3f0232spu49wfvq"
    
    config = LiveTraderConfig(
        network_type="testnet",
        wallet_mnemonic=testnet_mnemonic,
        wallet_address=testnet_address
    )
    
    trader = LiveTrader(config)
    await trader.connect_to_testnet()
    
    account_info = await trader.get_account_info()
    assert account_info is not None
    
    # Should have real dYdX account structure
    assert 'equity' in account_info
    assert 'freeCollateral' in account_info
    assert 'totalAccountValue' in account_info or 'totalValue' in account_info
    
    # Values should be numeric strings or numbers, not just mock data
    assert isinstance(account_info['equity'], (str, int, float))


@pytest.mark.asyncio
async def test_can_setup_trade_consumer():
    """Test: Can set up pyzmq trade consumer"""
    trader = LiveTrader()
    result = await trader.setup_trade_consumer()
    assert result is True
    assert trader.trade_subscriber is not None
    await trader.stop_consuming()


@pytest.mark.asyncio
async def test_can_process_trade_opportunity():
    """Test: Can process trade opportunity from queue"""
    trader = LiveTrader()
    
    # Mock trade opportunity data
    trade_data = {
        "timestamp": 1234567890.0,
        "datetime": "2023-01-01T00:00:00",
        "action": "ENTRY",
        "market": "BTC-USD",
        "side": "BUY",
        "size": 0.01,
        "price": 50000.0,
        "status": "PENDING",
        "pnl_usd": 0.0,
        "details": {},
        "source": "test"
    }
    
    # Should not raise exceptions
    await trader._process_trade_opportunity(trade_data)


@pytest.mark.asyncio 
async def test_live_trading_disabled_by_default():
    """Test: Live trading is disabled by default for safety"""
    config = LiveTraderConfig()
    assert config.enable_live_trading is False
    
    trader = LiveTrader(config)
    
    # Mock trade opportunity
    trade_data = {
        "action": "ENTRY",
        "market": "BTC-USD", 
        "side": "BUY",
        "size": 0.01,
        "price": 50000.0
    }
    
    # Should not execute trade when disabled
    await trader._process_trade_opportunity(trade_data)
