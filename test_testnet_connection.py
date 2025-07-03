#!/usr/bin/env python3
"""
Test script to verify testnet dashboard connection
"""
import time
import sys
import os

# Add the parent directory to sys.path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboards.realistic_mean_reversion_callbacks_testnet_dashboard import RealisticMeanReversionDashboard

def test_testnet_connection():
    """Test if the testnet dashboard can connect successfully"""
    print("🧪 Testing testnet dashboard connection...")
    
    try:
        # Initialize the testnet dashboard
        dashboard = RealisticMeanReversionDashboard()
        print("✅ Dashboard initialized successfully")
        
        # Test connection to testnet WebSocket
        print("🔗 Attempting to connect to dYdX testnet WebSocket...")
        connected = dashboard.stream.connect()
        
        if connected:
            print("✅ Successfully connected to dYdX testnet WebSocket!")
            print(f"📡 Connected to: {dashboard.stream._websocket_url}")
            print(f"🔑 Connection ID: {dashboard.stream._connection_id}")
            
            # Keep connection alive briefly to test stability
            print("⏳ Testing connection stability (5 seconds)...")
            time.sleep(5)
            
            if dashboard.stream._is_connected:
                print("✅ Connection remained stable")
                
                # Test subscribing to a market
                print("📈 Testing market subscription (BTC-USD)...")
                success = dashboard.stream.subscribe_to_orderbook("BTC-USD")
                
                if success:
                    print("✅ Successfully subscribed to BTC-USD orderbook")
                    
                    # Wait for some data
                    print("⏳ Waiting for market data (10 seconds)...")
                    time.sleep(10)
                    
                    # Check if we received data
                    if "BTC-USD" in dashboard.stream._current_orderbooks:
                        print("✅ Received market data from testnet!")
                        orderbook = dashboard.stream._current_orderbooks["BTC-USD"]
                        print(f"📊 Orderbook has {len(orderbook.get('bids', []))} bids and {len(orderbook.get('asks', []))} asks")
                    else:
                        print("⚠️  No market data received yet (this may be normal for testnet)")
                else:
                    print("❌ Failed to subscribe to market")
            else:
                print("❌ Connection became unstable")
            
            # Clean disconnect
            dashboard.stream.disconnect()
            print("🔌 Disconnected from testnet WebSocket")
            
        else:
            print(f"❌ Failed to connect to testnet WebSocket")
            if dashboard.stream.last_error:
                print(f"🚨 Error: {dashboard.stream.last_error}")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return connected

if __name__ == "__main__":
    success = test_testnet_connection()
    if success:
        print("\n🎉 Testnet connection test PASSED!")
        sys.exit(0)
    else:
        print("\n💥 Testnet connection test FAILED!")
        sys.exit(1)
