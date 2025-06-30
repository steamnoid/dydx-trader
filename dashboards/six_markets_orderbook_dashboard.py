#!/usr/bin/env python3
"""
Multi-Market Orderbook Dashboard - Build-First UI Component
Shows live orderbook for BTC, ETH, and SOL side-by-side using Layer 2 dYdX streams
"""
import time
import signal
import sys
import queue
import threading
from layer2_dydx_stream import DydxTradesStream
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.columns import Columns


class MultiMarketDashboard:
    """Multi-market orderbook dashboard using reactive streams"""
    
    def __init__(self):
        self.console = Console()
        self.stream = DydxTradesStream()
        
        # Track orderbooks for each market - 6 markets in 2 rows
        self.markets = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD", "ATOM-USD"]
        self.orderbooks = {
            "BTC-USD": {"asks": [], "bids": []},
            "ETH-USD": {"asks": [], "bids": []},
            "SOL-USD": {"asks": [], "bids": []},
            "AVAX-USD": {"asks": [], "bids": []},
            "DOGE-USD": {"asks": [], "bids": []},
            "ATOM-USD": {"asks": [], "bids": []}
        }
        
        # Update tracking
        self.running = True
        self.last_update_times = {market: 0 for market in self.markets}
        self.update_counts = {market: 0 for market in self.markets}
        self.live_display = None
        self.update_queue = queue.Queue()
        self.last_display_hash = None
        self.min_update_interval = 0.1  # 100ms minimum between UI updates
        self.last_ui_update = 0
        
        # Setup signal handler for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
    
    def _create_market_column(self, market_id: str):
        """Create orderbook display for a single market"""
        orderbook = self.orderbooks.get(market_id, {"asks": [], "bids": []})
        asks = orderbook.get("asks", [])[:15]  # Top 15 asks (reduced for side-by-side)
        bids = orderbook.get("bids", [])[:15]  # Top 15 bids
        
        # Get market symbol for display
        symbol = market_id.split("-")[0]
        
        # Create asks table (sell orders) - wider for better price display
        asks_table = Table(title=f"🔴 ASKS", show_header=True, header_style="red", width=28)
        asks_table.add_column("Price", style="red", width=16)
        asks_table.add_column("Size", style="white", width=10)
        
        for ask in asks:
            price = float(ask.get("price", 0))
            size = float(ask.get("size", 0))
            asks_table.add_row(f"${price:,.2f}", f"{size:.3f}")
        
        # Create bids table (buy orders) - wider for better price display  
        bids_table = Table(title=f"🟢 BIDS", show_header=True, header_style="green", width=28)
        bids_table.add_column("Price", style="green", width=16)
        bids_table.add_column("Size", style="white", width=10)
        
        for bid in bids:
            price = float(bid.get("price", 0))
            size = float(bid.get("size", 0))
            bids_table.add_row(f"${price:,.2f}", f"{size:.3f}")
        
        # Create stats for this market
        stats_panel = self._create_market_stats(market_id)
        
        # Create orderbook layout - asks and bids side-by-side
        orderbook_layout = Layout()
        orderbook_layout.split_row(
            Layout(asks_table),
            Layout(bids_table)
        )
        
        # Create column layout for this market - stats on top, orderbook below
        market_layout = Layout()
        market_layout.split_column(
            Layout(stats_panel, size=8),
            Layout(orderbook_layout, size=34)
        )
        
        return Panel(market_layout, title=f"📈 {symbol}", border_style="blue")
    
    def _create_market_stats(self, market_id: str):
        """Create statistics panel for a market"""
        orderbook = self.orderbooks.get(market_id, {"asks": [], "bids": []})
        asks = orderbook.get("asks", [])
        bids = orderbook.get("bids", [])
        symbol = market_id.split("-")[0]
        
        if asks and bids:
            best_ask = float(asks[0].get("price", 0))
            best_bid = float(bids[0].get("price", 0))
            spread = best_ask - best_bid
            mid_price = (best_ask + best_bid) / 2
        else:
            best_ask = best_bid = spread = mid_price = 0
        
        # Time since last update
        time_since_update = time.time() - self.last_update_times.get(market_id, 0) if self.last_update_times.get(market_id, 0) > 0 else 0
        update_count = self.update_counts.get(market_id, 0)
        
        stats_text = f"""[bold]{symbol}[/bold]
Ask: [red]${best_ask:,.2f}[/red]
Bid: [green]${best_bid:,.2f}[/green]
Spread: [blue]${spread:.2f}[/blue]
Mid: [magenta]${mid_price:,.2f}[/magenta]
Updates: [white]{update_count}[/white]
Last: [white]{time_since_update:.1f}s[/white]
        """
        
        return Panel(stats_text.strip(), border_style="cyan", height=8)
    
    def _create_dashboard_display(self):
        """Create the complete dashboard display with 6 markets in 2 rows"""
        # Create market columns for first row
        btc_column = self._create_market_column("BTC-USD")
        eth_column = self._create_market_column("ETH-USD") 
        sol_column = self._create_market_column("SOL-USD")
        
        # Create market columns for second row
        avax_column = self._create_market_column("AVAX-USD")
        doge_column = self._create_market_column("DOGE-USD")
        atom_column = self._create_market_column("ATOM-USD")
        
        # Create first row layout
        first_row = Layout()
        first_row.split_row(
            Layout(btc_column),
            Layout(eth_column),
            Layout(sol_column)
        )
        
        # Create second row layout
        second_row = Layout()
        second_row.split_row(
            Layout(avax_column),
            Layout(doge_column),
            Layout(atom_column)
        )
        
        # Create main layout with two rows
        main_layout = Layout()
        main_layout.split_column(
            Layout(first_row),
            Layout(second_row)
        )
        
        return main_layout
    
    def _on_orderbook_update(self, market_id: str):
        """Create orderbook update handler for specific market"""
        def handler(orderbook_data):
            # Put update in queue with market identifier
            self.update_queue.put((market_id, orderbook_data))
        return handler
    
    def _create_display_hash(self):
        """Create a hash of the current display state to detect changes"""
        hash_data = []
        for market_id in self.markets:
            orderbook = self.orderbooks.get(market_id, {"asks": [], "bids": []})
            asks = orderbook.get("asks", [])[:5]  # Top 5 for hash
            bids = orderbook.get("bids", [])[:5]
            
            ask_data = [(ask.get("price", 0), ask.get("size", 0)) for ask in asks]
            bid_data = [(bid.get("price", 0), bid.get("size", 0)) for bid in bids]
            hash_data.append((market_id, ask_data, bid_data, self.update_counts.get(market_id, 0)))
        
        return hash(str(hash_data))
    
    def _process_updates(self):
        """Process queued updates in main thread"""
        try:
            # Process all queued updates
            updated = False
            while not self.update_queue.empty():
                try:
                    market_id, orderbook_data = self.update_queue.get_nowait()
                    self.orderbooks[market_id] = orderbook_data
                    self.update_counts[market_id] += 1
                    self.last_update_times[market_id] = time.time()
                    updated = True
                except queue.Empty:
                    break
            
            # Only update UI if we have updates and enough time has passed
            if updated and self.live_display:
                current_time = time.time()
                
                # Check if minimum interval has passed
                if current_time - self.last_ui_update >= self.min_update_interval:
                    # Check if display content actually changed
                    current_hash = self._create_display_hash()
                    if current_hash != self.last_display_hash:
                        self.live_display.update(self._create_dashboard_display())
                        self.last_display_hash = current_hash
                        self.last_ui_update = current_time
                
        except Exception as e:
            # In case of UI update errors, continue silently
            pass
    
    def run(self):
        """Run the multi-market dashboard"""
        try:
            # Connect to stream
            self.console.print("🔄 Connecting to dYdX Layer 2 stream...")
            self.stream.connect()
            
            # Wait for connection
            time.sleep(2)
            
            # Subscribe to orderbook streams for all markets
            subscriptions = []
            for market_id in self.markets:
                self.console.print(f"📡 Subscribing to {market_id} orderbook...")
                orderbook_stream = self.stream.get_orderbook_observable(market_id)
                subscription = orderbook_stream.subscribe(
                    on_next=self._on_orderbook_update(market_id),
                    on_error=lambda e, market=market_id: self.console.print(f"❌ {market} Error: {e}"),
                    on_completed=lambda market=market_id: self.console.print(f"✅ {market} Stream completed")
                )
                subscriptions.append(subscription)
            
            # Start live display
            with Live(self._create_dashboard_display(), refresh_per_second=10) as live:
                self.live_display = live
                self.console.print("🎯 Multi-Market Dashboard Started! (Press Ctrl+C to stop)")
                self.console.print("📊 Row 1: BTC-USD | ETH-USD | SOL-USD")
                self.console.print("📊 Row 2: AVAX-USD | DOGE-USD | ATOM-USD")
                
                # Initialize display hash
                self.last_display_hash = self._create_display_hash()
                
                # Main loop - process updates from queue in main thread
                while self.running:
                    try:
                        # Process any queued updates
                        self._process_updates()
                        time.sleep(0.1)  # Check for updates every 100ms
                    except KeyboardInterrupt:
                        break
                
        except Exception as e:
            self.console.print(f"❌ Error: {e}")
        finally:
            # Clean up
            self.live_display = None
            
            # Dispose all subscriptions
            if 'subscriptions' in locals():
                for subscription in subscriptions:
                    try:
                        subscription.dispose()
                    except:
                        pass
            
            self.console.print("👋 Multi-Market Dashboard stopped")


if __name__ == "__main__":
    dashboard = MultiMarketDashboard()
    dashboard.run()
