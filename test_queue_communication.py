#!/usr/bin/env python3
"""
Test script to verify pyzmq communication between dashboard and live trader
"""

import asyncio
import json
import time
import zmq
import zmq.asyncio
from datetime import datetime


async def test_publisher():
    """Test publishing trade opportunities"""
    print("Setting up test publisher...")
    
    context = zmq.asyncio.Context()
    publisher = context.socket(zmq.PUB)
    publisher.bind("tcp://127.0.0.1:5556")  # Use different port for test
    
    # Give time for binding
    await asyncio.sleep(1)
    
    print("Publishing test trade opportunities...")
    
    for i in range(5):
        trade_message = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "action": "ENTRY",
            "market": f"BTC-USD",
            "side": "BUY" if i % 2 == 0 else "SELL",
            "size": 0.01 + (i * 0.005),
            "price": 50000 + (i * 100),
            "status": "PENDING",
            "pnl_usd": 0.0,
            "details": {"test_id": i},
            "source": "test_publisher"
        }
        
        topic = "TRADE_OPPORTUNITY"
        message = json.dumps(trade_message)
        publisher.send_multipart([topic.encode('utf-8'), message.encode('utf-8')])
        
        print(f"Published: {trade_message['action']} {trade_message['market']} {trade_message['side']}")
        await asyncio.sleep(2)
    
    publisher.close()
    context.term()
    print("Test publisher finished")


async def test_consumer():
    """Test consuming trade opportunities"""
    print("Setting up test consumer...")
    
    context = zmq.asyncio.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://127.0.0.1:5556")  # Connect to test publisher
    subscriber.setsockopt(zmq.SUBSCRIBE, b"TRADE_OPPORTUNITY")
    
    print("Consuming test trade opportunities...")
    
    received_count = 0
    timeout_count = 0
    max_timeouts = 10  # Stop after 10 consecutive timeouts
    
    while timeout_count < max_timeouts:
        try:
            # Wait for message with timeout
            topic, message = await asyncio.wait_for(
                subscriber.recv_multipart(),
                timeout=1.0
            )
            
            # Reset timeout count on successful receive
            timeout_count = 0
            
            # Decode and process
            trade_data = json.loads(message.decode('utf-8'))
            received_count += 1
            
            print(f"Received #{received_count}: {trade_data['action']} {trade_data['market']} {trade_data['side']} @ {trade_data['price']}")
            
        except asyncio.TimeoutError:
            timeout_count += 1
            print(f"Timeout {timeout_count}/{max_timeouts}")
    
    subscriber.close()
    context.term()
    print(f"Test consumer finished - received {received_count} messages")


async def run_test():
    """Run publisher and consumer simultaneously"""
    print("Starting pyzmq communication test...")
    
    # Run publisher and consumer concurrently
    publisher_task = asyncio.create_task(test_publisher())
    consumer_task = asyncio.create_task(test_consumer())
    
    # Wait for both to complete
    await asyncio.gather(publisher_task, consumer_task)
    
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(run_test())
