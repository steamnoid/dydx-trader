#!/usr/bin/env python3
"""
Live Trader Process - dYdX v4 Trading Bot

This script runs the live trader as a separate process, consuming trade opportunities
from the dashboard via pyzmq queue and executing them on testnet or mainnet.

Usage:
    python run_live_trader.py --network testnet --mnemonic "your mnemonic" --address "your address"
    python run_live_trader.py --network mainnet  # Uses environment variables for credentials
"""

import asyncio
import argparse
import signal
import sys
import os

from live_trader import LiveTrader, LiveTraderConfig


class LiveTraderProcess:
    """Main process for running the live trader"""
    
    def __init__(self, config: LiveTraderConfig):
        self.config = config
        self.trader = LiveTrader(config)
        self.shutdown_event = asyncio.Event()
        
    async def run(self):
        """Main run loop for the live trader process"""
        print(f"Starting Live Trader Process")
        print(f"Network: {self.config.network_type}")
        print(f"Live Trading: {'ENABLED' if self.config.enable_live_trading else 'DISABLED (DRY RUN)'}")
        
        # Set up signal handlers for graceful shutdown
        def signal_handler():
            print("\nReceived shutdown signal, stopping trader...")
            self.shutdown_event.set()
        
        signal.signal(signal.SIGINT, lambda s, f: signal_handler())
        signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
        
        try:
            # Connect to appropriate network
            if self.config.network_type == "testnet":
                connected = await self.trader.connect_to_testnet()
            else:  # mainnet
                connected = await self.trader.connect_to_mainnet()
            
            if not connected:
                print("Failed to connect to trading network")
                return False
            
            print(f"Successfully connected to {self.config.network_type}")
            
            # Get account info
            account_info = await self.trader.get_account_info()
            if account_info:
                print(f"Account Info: {account_info}")
            
            # Set up trade consumer
            consumer_setup = await self.trader.setup_trade_consumer()
            if not consumer_setup:
                print("Failed to setup trade consumer")
                return False
            
            # Start consuming trade opportunities in the background
            consumer_task = asyncio.create_task(self.trader.consume_trade_opportunities())
            
            print("Live trader is now running and consuming trade opportunities...")
            print("Press Ctrl+C to stop")
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
            # Graceful shutdown
            print("Shutting down live trader...")
            await self.trader.stop_consuming()
            
            # Wait for consumer task to finish
            consumer_task.cancel()
            try:
                await consumer_task
            except asyncio.CancelledError:
                pass
            
            print("Live trader stopped")
            return True
            
        except Exception as e:
            print(f"Live trader error: {e}")
            return False


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="dYdX v4 Live Trader Process")
    
    parser.add_argument(
        "--network", 
        choices=["testnet", "mainnet"], 
        default="testnet",
        help="Network to connect to (default: testnet)"
    )
    
    parser.add_argument(
        "--mnemonic",
        help="Wallet mnemonic (required for testnet, ignored for mainnet)"
    )
    
    parser.add_argument(
        "--address", 
        help="Wallet address (required for testnet, ignored for mainnet)"
    )
    
    parser.add_argument(
        "--enable-live-trading",
        action="store_true",
        help="Enable live trading (default: dry run mode)"
    )
    
    parser.add_argument(
        "--max-position-size",
        type=float,
        default=100.0,
        help="Maximum position size in USD (default: 100.0)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Create trader configuration
    config = LiveTraderConfig(
        network_type=args.network,
        enable_live_trading=args.enable_live_trading,
        max_position_size_usd=args.max_position_size
    )
    
    # Set credentials based on network
    if args.network == "testnet":
        if not args.mnemonic or not args.address:
            print("Error: --mnemonic and --address are required for testnet")
            sys.exit(1)
        config.wallet_mnemonic = args.mnemonic
        config.wallet_address = args.address
    else:  # mainnet
        # Mainnet uses environment variables (validated in connect_to_mainnet)
        if args.mnemonic or args.address:
            print("Warning: --mnemonic and --address ignored for mainnet (uses environment variables)")
    
    # Create and run the live trader process
    trader_process = LiveTraderProcess(config)
    
    try:
        success = asyncio.run(trader_process.run())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
