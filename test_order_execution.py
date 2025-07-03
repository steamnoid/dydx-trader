#!/usr/bin/env python3
"""
Test script to verify live trader order execution with TTL
"""

import asyncio
from live_trader import LiveTrader, LiveTraderConfig


async def test_order_execution():
    """Test order execution functionality"""
    print("Testing Live Trader Order Execution...")
    
    # Create config with live trading enabled
    config = LiveTraderConfig(
        network_type="testnet",
        wallet_mnemonic="faint void funny program truth life pulse pioneer convince sting current child moment olympic concert lounge invest mirror piano yard extra strong reveal near",
        wallet_address="dydx1rd8nkf25gv3jm8xnt8rzqdw3f0232spu49wfvq",
        enable_live_trading=True,
        max_position_size_usd=100.0
    )
    
    # Create trader instance
    trader = LiveTrader(config)
    
    # Connect to testnet
    connected = await trader.connect_to_testnet()
    if not connected:
        print("❌ Failed to connect to testnet")
        return
    
    print("✅ Connected to testnet")
    
    # Test order execution
    print("\n🧪 Testing order execution...")
    await trader._execute_trade("BTC-USD", "BUY", 0.001, 50000.0)
    
    print("\n🧪 Testing another order...")
    await trader._execute_trade("ETH-USD", "SELL", 0.01, 3000.0)
    
    print("\n✅ Order execution test completed")


if __name__ == "__main__":
    asyncio.run(test_order_execution())
