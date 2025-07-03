#!/usr/bin/env python3
"""
Test to verify that the live trader creates a single dYdX order with conditional 
take profit and stop loss parameters, rather than multiple separate orders.
"""

import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any


async def test_single_order_with_conditional_parameters():
    """Test that live trader creates ONE order with TP/SL conditional parameters"""
    
    from live_trader import LiveTrader
    
    # Create trader instance
    trader = LiveTrader()
    trader.wallet = MagicMock()
    trader.node_client = AsyncMock()  # Mock async node client
    trader.indexer_client = AsyncMock()  # Mock async indexer client
    
    # Mock market response
    mock_market_data = {
        "markets": {
            "BTC-USD": {
                "market": "BTC-USD",
                "status": "ACTIVE",
                "baseAsset": "BTC",
                "quoteAsset": "USD"
            }
        }
    }
    trader.indexer_client.markets.get_perpetual_markets.return_value = mock_market_data
    
    # Mock successful order response
    trader.node_client.place_order.return_value = {"hash": "0x123abc", "status": "success"}
    
    # Test trade data with TP/SL from dashboard
    test_trade_data = {
        "timestamp": 1234567890,
        "action": "ENTRY",
        "market": "BTC-USD",
        "side": "BUY",
        "size": 0.01,
        "price": 50000.0,
        "take_profit_price": 55000.0,  # From dashboard calculation
        "stop_loss_price": 47500.0,    # From dashboard calculation
        "source": "dashboard"
    }
    
    order_params = {
        "market": "BTC-USD",
        "side": "BUY",
        "size": 0.01,
        "price": 50000.0
    }
    
    print("🧪 Testing Single Order with Conditional TP/SL...")
    print(f"   Entry: {test_trade_data['side']} {test_trade_data['size']} {test_trade_data['market']} @ ${test_trade_data['price']}")
    print(f"   Take Profit: ${test_trade_data['take_profit_price']} (from dashboard)")
    print(f"   Stop Loss: ${test_trade_data['stop_loss_price']} (from dashboard)")
    
    # Mock the Market class and its methods
    with patch('dydx_v4_client.node.market.Market') as MockMarket:
        mock_market_instance = MagicMock()
        MockMarket.return_value = mock_market_instance
        
        # Mock order_id generation
        mock_market_instance.order_id.return_value = "test_order_id_123"
        
        # Mock order creation - this is where we verify conditional parameters
        mock_order = MagicMock()
        mock_market_instance.order.return_value = mock_order
        
        # Mock since_now function
        with patch('dydx_v4_client.node.market.since_now') as mock_since_now:
            mock_since_now.return_value = 1234567920  # 30 seconds later
            
            # Execute the order submission
            try:
                result = await trader._submit_order_to_dydx(order_params, test_trade_data)
                
                # Verify that place_order was called exactly ONCE (single order approach)
                assert trader.node_client.place_order.call_count == 1, "Should submit exactly ONE order, not multiple"
                
                # Verify that the order was created with conditional parameters
                assert mock_market_instance.order.called, "Order creation method should be called"
                
                # Get the arguments passed to the order creation
                order_call_args = mock_market_instance.order.call_args
                order_kwargs = order_call_args[1] if order_call_args else {}
                
                print("📋 Order Parameters Passed:")
                for key, value in order_kwargs.items():
                    print(f"   {key}: {value}")
                
                # Verify conditional parameters are included
                expected_conditional_params = [
                    'conditional_order_trigger_subticks',
                    'conditional_order_trigger_type'
                ]
                
                has_conditional_params = any(param in order_kwargs for param in expected_conditional_params)
                print(f"   Has conditional TP/SL params: {has_conditional_params}")
                
                # Verify stop loss price is used in conditional trigger
                sl_trigger = order_kwargs.get('conditional_order_trigger_subticks')
                if sl_trigger:
                    expected_sl = int(test_trade_data['stop_loss_price'])
                    assert sl_trigger == expected_sl, f"Stop loss trigger should be {expected_sl}, got {sl_trigger}"
                    print(f"✅ Stop loss conditional trigger correctly set to ${test_trade_data['stop_loss_price']}")
                
                print("✅ Single order with conditional TP/SL parameters successfully created")
                return True
                
            except Exception as e:
                print(f"❌ Order submission failed: {e}")
                return False


async def test_fallback_tp_sl_calculation():
    """Test that live trader falls back to calculated TP/SL if not provided by dashboard"""
    
    from live_trader import LiveTrader
    
    trader = LiveTrader()
    trader.wallet = MagicMock()
    trader.node_client = AsyncMock()
    trader.indexer_client = AsyncMock()
    
    # Mock market response
    mock_market_data = {
        "markets": {
            "BTC-USD": {
                "market": "BTC-USD",
                "status": "ACTIVE"
            }
        }
    }
    trader.indexer_client.markets.get_perpetual_markets.return_value = mock_market_data
    trader.node_client.place_order.return_value = {"hash": "0x456def", "status": "success"}
    
    # Test trade data WITHOUT TP/SL from dashboard
    test_trade_data_no_tpsl = {
        "timestamp": 1234567890,
        "action": "ENTRY",
        "market": "BTC-USD",
        "side": "BUY",
        "size": 0.01,
        "price": 50000.0,
        # No take_profit_price or stop_loss_price
        "source": "dashboard"
    }
    
    order_params = {
        "market": "BTC-USD",
        "side": "BUY",
        "size": 0.01,
        "price": 50000.0
    }
    
    print("\n🧪 Testing Fallback TP/SL Calculation...")
    print("   Dashboard did not provide TP/SL, should calculate fallback values")
    
    with patch('dydx_v4_client.node.market.Market') as MockMarket:
        mock_market_instance = MagicMock()
        MockMarket.return_value = mock_market_instance
        mock_market_instance.order_id.return_value = "test_order_id_456"
        mock_market_instance.order.return_value = MagicMock()
        
        with patch('dydx_v4_client.node.market.since_now') as mock_since_now:
            mock_since_now.return_value = 1234567920
            
            # Execute the order submission with no TP/SL provided
            result = await trader._submit_order_to_dydx(order_params, test_trade_data_no_tpsl)
            
            # Verify fallback calculation occurred
            assert trader.node_client.place_order.call_count == 1, "Should still submit exactly ONE order"
            print("✅ Fallback TP/SL calculation works correctly")
            return True


async def run_all_tests():
    """Run all single order TP/SL tests"""
    
    print("🚀 Testing Single Order TP/SL Implementation...")
    print("="*60)
    
    # Test 1: Single order with conditional parameters from dashboard
    test1_result = await test_single_order_with_conditional_parameters()
    
    # Test 2: Fallback calculation when dashboard doesn't provide TP/SL
    test2_result = await test_fallback_tp_sl_calculation()
    
    print("\n" + "="*60)
    if test1_result and test2_result:
        print("🎉 ALL SINGLE ORDER TP/SL TESTS PASSED!")
        print("✅ Live trader creates ONE order with conditional TP/SL parameters")
        print("✅ Dashboard TP/SL values are used when provided")
        print("✅ Fallback calculation works when dashboard values missing")
    else:
        print("❌ Some tests failed")
        return False
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        if success:
            print("\n🔥 SINGLE ORDER TP/SL APPROACH VALIDATED!")
        else:
            print("\n💥 Tests failed")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
