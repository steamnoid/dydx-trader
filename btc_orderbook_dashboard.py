#!/usr/bin/env python3
"""
BTC Orderbook Dashboard - Build-First UI Component
Shows live BTC orderbook using Layer 2 dYdX stream
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


class BTCOrderbookDashboard:
    """BTC orderbook dashboard using reactive streams"""
    
    def __init__(self):
        self.console = Console()
        self.stream = DydxTradesStream()
        self.current_orderbook = {"asks": [], "bids": []}
        self.running = True
        self.last_update_time = 0
        self.update_count = 0
        self.live_display = None  # Will hold the Live display reference
        self.update_queue = queue.Queue()  # Thread-safe queue for updates
        self.last_display_hash = None  # Track when display actually changed
        self.min_update_interval = 0.1  # Minimum time between UI updates (100ms)
        self.last_ui_update = 0  # Track last UI update time
        
        # Setup signal handler for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
    
    def _create_orderbook_display(self):
        """Create the orderbook display with asks and bids"""
        asks = self.current_orderbook.get("asks", [])[:50]  # Top 50 asks
        bids = self.current_orderbook.get("bids", [])[:50]  # Top 50 bids
        
        # Create asks table (sell orders)
        asks_table = Table(title="🔴 ASKS (Sellers)", show_header=True, header_style="red")
        asks_table.add_column("Price", style="red", width=12)
        asks_table.add_column("Size", style="white", width=12)
        
        for ask in asks:  # Show lowest prices first (ascending)
            price = float(ask.get("price", 0))
            size = float(ask.get("size", 0))
            asks_table.add_row(f"${price:,.2f}", f"{size:.4f}")
        
        # Create bids table (buy orders)
        bids_table = Table(title="🟢 BIDS (Buyers)", show_header=True, header_style="green")
        bids_table.add_column("Price", style="green", width=12)
        bids_table.add_column("Size", style="white", width=12)
        
        for bid in bids:  # Already sorted descending
            price = float(bid.get("price", 0))
            size = float(bid.get("size", 0))
            bids_table.add_row(f"${price:,.2f}", f"{size:.4f}")
        
        # Create stats panel
        stats = self._create_stats_panel()
        
        # Layout
        main_layout = Layout()
        main_layout.split_column(
            Layout(stats, size=6),
            Layout(Columns([asks_table, bids_table], equal=True))
        )
        
        return main_layout
    
    def _create_stats_panel(self):
        """Create statistics panel"""
        asks = self.current_orderbook.get("asks", [])
        bids = self.current_orderbook.get("bids", [])
        
        if asks and bids:
            best_ask = float(asks[0].get("price", 0))
            best_bid = float(bids[0].get("price", 0))
            spread = best_ask - best_bid
            mid_price = (best_ask + best_bid) / 2
        else:
            best_ask = best_bid = spread = mid_price = 0
        
        # Time since last update
        time_since_update = time.time() - self.last_update_time if self.last_update_time > 0 else 0
        
        stats_text = f"""
🚀 [bold cyan]BTC-USD Orderbook[/bold cyan] | Levels: {len(asks)} asks, {len(bids)} bids

📊 [yellow]Market Stats:[/yellow]
   • Best Ask: [red]${best_ask:,.2f}[/red]
   • Best Bid: [green]${best_bid:,.2f}[/green] 
   • Spread: [blue]${spread:.2f}[/blue]
   • Mid Price: [magenta]${mid_price:,.2f}[/magenta]

🔄 [cyan]Update Stats:[/cyan]
   • Updates: [white]{self.update_count}[/white]
   • Last Update: [white]{time_since_update:.1f}s ago[/white]
        """
        
        return Panel(stats_text.strip(), border_style="blue")
    
    def _on_orderbook_update(self, orderbook_data):
        """Handle incoming orderbook updates - queue for thread-safe processing"""
        # Put update in queue (thread-safe operation)
        self.update_queue.put(orderbook_data)
    
    def _create_display_hash(self):
        """Create a hash of the current display state to detect changes"""
        asks = self.current_orderbook.get("asks", [])[:50]
        bids = self.current_orderbook.get("bids", [])[:50]
        
        # Create a simple hash of the top levels
        ask_hash = str([(ask.get("price", 0), ask.get("size", 0)) for ask in asks[:10]])
        bid_hash = str([(bid.get("price", 0), bid.get("size", 0)) for bid in bids[:10]])
        
        return hash(ask_hash + bid_hash + str(self.update_count))
    
    def _process_updates(self):
        """Process queued updates in main thread"""
        try:
            # Process all queued updates
            updated = False
            while not self.update_queue.empty():
                try:
                    orderbook_data = self.update_queue.get_nowait()
                    self.current_orderbook = orderbook_data
                    self.update_count += 1
                    self.last_update_time = time.time()
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
                        self.live_display.update(self._create_orderbook_display())
                        self.last_display_hash = current_hash
                        self.last_ui_update = current_time
                
        except Exception as e:
            # In case of UI update errors, continue silently
            pass
    
    def run(self):
        """Run the dashboard"""
        try:
            # Connect to stream
            self.console.print("🔄 Connecting to dYdX Layer 2 stream...")
            self.stream.connect()
            
            # Wait for connection
            time.sleep(2)
            
            # Get orderbook observable and subscribe
            orderbook_stream = self.stream.get_orderbook_observable("BTC-USD")
            subscription = orderbook_stream.subscribe(
                on_next=self._on_orderbook_update,
                on_error=lambda e: self.console.print(f"❌ Error: {e}"),
                on_completed=lambda: self.console.print("✅ Stream completed")
            )
            
            # Start live display with controlled refresh
            with Live(self._create_orderbook_display(), refresh_per_second=10) as live:
                self.live_display = live  # Store reference for updates
                self.console.print("🎯 BTC Orderbook Dashboard Started! (Press Ctrl+C to stop)")
                
                # Initialize display hash
                self.last_display_hash = self._create_display_hash()
                
                # Main loop - process updates from queue in main thread
                while self.running:
                    try:
                        # Process any queued updates
                        self._process_updates()
                        time.sleep(0.1)  # Check for updates every 100ms to reduce CPU usage
                    except KeyboardInterrupt:
                        break
                
        except Exception as e:
            self.console.print(f"❌ Error: {e}")
        finally:
            # Clean up
            self.live_display = None  # Clear reference
            
            if 'subscription' in locals():
                try:
                    subscription.dispose()
                except:
                    pass
            
            self.console.print("👋 Dashboard stopped")


if __name__ == "__main__":
    dashboard = BTCOrderbookDashboard()
    dashboard.run()
