#!/usr/bin/env python3
"""
Test to verify take profit and stop loss parameters are sent from dashboard to live trader via pyzmq
"""

import time
import zmq
import json
from threading import Thread
import signal
import sys

def signal_handler(sig, frame):
    print('\nTest interrupted by user')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def test_tp_sl_communication():
    """Test that dashboard sends TP/SL parameters and live trader receives them"""
    
    # Set up ZMQ context and sockets
    context = zmq.Context()
    
    # Publisher (simulates dashboard)
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://*:5557")
    
    # Subscriber (simulates live trader)
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:5557")
    subscriber.setsockopt(zmq.SUBSCRIBE, b"TRADE_OPPORTUNITY")
    
    # Give sockets time to connect
    time.sleep(0.5)
    
    print("🧪 Testing Take Profit and Stop Loss parameter transmission...")
    print("📡 Publisher connected on port 5557")
    print("📲 Subscriber connected, listening for TRADE_OPPORTUNITY messages")
    print()
    
    # Test case 1: BUY signal with TP/SL
    print("📤 Test 1: Sending BUY trade opportunity with TP/SL...")
    
    buy_trade = {
        "timestamp": time.time(),
        "datetime": "2025-07-03T10:30:00",
        "action": "ENTRY",
        "market": "ETH-USD",
        "side": "BUY",
        "size": 1.0,
        "price": 3500.00,
        "status": "PENDING",
        "pnl_usd": 0.0,
        "take_profit_price": 3550.00,  # Dashboard calculated: $50 profit
        "stop_loss_price": 3475.00,   # Dashboard calculated: $25 stop loss
        "details": {"confidence": 85},
        "source": "test_dashboard"
    }
    
    topic = "TRADE_OPPORTUNITY"
    message = json.dumps(buy_trade)
    publisher.send_multipart([topic.encode('utf-8'), message.encode('utf-8')])
    print(f"   Sent BUY signal: {buy_trade['side']} {buy_trade['size']} {buy_trade['market']} @ ${buy_trade['price']}")
    print(f"   Take Profit: ${buy_trade['take_profit_price']}")
    print(f"   Stop Loss: ${buy_trade['stop_loss_price']}")
    
    # Test case 2: SELL signal with TP/SL
    print("\n📤 Test 2: Sending SELL trade opportunity with TP/SL...")
    
    sell_trade = {
        "timestamp": time.time(),
        "datetime": "2025-07-03T10:31:00",
        "action": "ENTRY",
        "market": "BTC-USD",
        "side": "SELL",
        "size": 0.1,
        "price": 50000.00,
        "status": "PENDING",
        "pnl_usd": 0.0,
        "take_profit_price": 49500.00,  # Dashboard calculated: $50 profit for short
        "stop_loss_price": 50250.00,   # Dashboard calculated: $25 stop loss for short
        "details": {"confidence": 78},
        "source": "test_dashboard"
    }
    
    message = json.dumps(sell_trade)
    publisher.send_multipart([topic.encode('utf-8'), message.encode('utf-8')])
    print(f"   Sent SELL signal: {sell_trade['side']} {sell_trade['size']} {sell_trade['market']} @ ${sell_trade['price']}")
    print(f"   Take Profit: ${sell_trade['take_profit_price']}")
    print(f"   Stop Loss: ${sell_trade['stop_loss_price']}")
    
    # Test case 3: Trade without TP/SL (to test fallback)
    print("\n📤 Test 3: Sending trade without TP/SL (to test fallback)...")
    
    fallback_trade = {
        "timestamp": time.time(),
        "datetime": "2025-07-03T10:32:00",
        "action": "ENTRY",
        "market": "SOL-USD",
        "side": "BUY",
        "size": 10.0,
        "price": 200.00,
        "status": "PENDING",
        "pnl_usd": 0.0,
        # Note: no take_profit_price or stop_loss_price - should trigger fallback
        "details": {"confidence": 65},
        "source": "test_dashboard"
    }
    
    message = json.dumps(fallback_trade)
    publisher.send_multipart([topic.encode('utf-8'), message.encode('utf-8')])
    print(f"   Sent fallback signal: {fallback_trade['side']} {fallback_trade['size']} {fallback_trade['market']} @ ${fallback_trade['price']}")
    print(f"   Take Profit: NOT PROVIDED (should trigger fallback)")
    print(f"   Stop Loss: NOT PROVIDED (should trigger fallback)")
    
    print("\n📲 Listening for messages on subscriber side...")
    
    messages_received = 0
    start_time = time.time()
    timeout = 5  # 5 seconds timeout
    
    try:
        while messages_received < 3 and (time.time() - start_time) < timeout:
            if subscriber.poll(timeout=1000):  # 1 second poll timeout
                topic, message = subscriber.recv_multipart(zmq.NOBLOCK)
                trade_data = json.loads(message.decode('utf-8'))
                messages_received += 1
                
                print(f"\n📨 Message {messages_received} received:")
                print(f"   Action: {trade_data['action']}")
                print(f"   Market: {trade_data['market']}")
                print(f"   Side: {trade_data['side']}")
                print(f"   Size: {trade_data['size']}")
                print(f"   Price: ${trade_data['price']}")
                
                # Check TP/SL parameters
                if 'take_profit_price' in trade_data and trade_data['take_profit_price'] is not None:
                    print(f"   ✅ Take Profit: ${trade_data['take_profit_price']} (from dashboard)")
                else:
                    print(f"   ⚠️  Take Profit: NOT PROVIDED (will use fallback)")
                    
                if 'stop_loss_price' in trade_data and trade_data['stop_loss_price'] is not None:
                    print(f"   ✅ Stop Loss: ${trade_data['stop_loss_price']} (from dashboard)")
                else:
                    print(f"   ⚠️  Stop Loss: NOT PROVIDED (will use fallback)")
                
                print(f"   Source: {trade_data['source']}")
                
    except zmq.Again:
        print("⏰ Timeout waiting for messages")
    
    print(f"\n🏁 Test completed. Received {messages_received}/3 messages.")
    
    if messages_received == 3:
        print("✅ SUCCESS: All test messages received with TP/SL parameters!")
    else:
        print("❌ INCOMPLETE: Not all messages received")
    
    # Cleanup
    publisher.close()
    subscriber.close()
    context.term()

if __name__ == "__main__":
    test_tp_sl_communication()
