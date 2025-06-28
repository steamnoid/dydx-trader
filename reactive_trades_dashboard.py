#!/usr/bin/env python3
"""
BTC Reactive Dashboard - Build-First UI Component
Shows live BTC trades using Layer 2 dYdX stream
"""
import time
import signal
import sys
import requests
from layer2_dydx_stream import DydxTradesStream
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel


class BTCDashboard:
    """Multi-market trades dashboard using reactive streams"""
    
    def __init__(self):
        self.console = Console()
        self.stream = DydxTradesStream()
        
        # Fetch active markets dynamically from dYdX
        self.markets = self._fetch_active_markets()
        
        # Initialize market data for all active markets
        self.market_data = {
            market: {"trade_count": 0, "last_price": 0.0} 
            for market in self.markets
        }
        
        self.running = True
        
        # Setup signal handler for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _fetch_active_markets(self):
        """Fetch active markets from dYdX REST API"""
        try:
            response = requests.get('https://indexer.dydx.trade/v4/perpetualMarkets', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'markets' in data:
                    markets = data['markets']
                    # Filter for active markets only
                    active_markets = [
                        name for name, market in markets.items() 
                        if market.get('status') == 'ACTIVE'
                    ]
                    # Sort markets for consistent display
                    return sorted(active_markets)
                else:
                    return self._get_fallback_markets()
            else:
                return self._get_fallback_markets()
        except Exception as e:
            return self._get_fallback_markets()
    
    def _get_fallback_markets(self):
        """Fallback markets in case API fetch fails"""
        return ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD"]
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
    
    def _create_display_table(self):
        """Create the main display table with 3 columns layout"""
        from rich.table import Table
        from rich.columns import Columns
        
        # Split markets into 3 columns
        markets_per_column = len(self.markets) // 3 + (1 if len(self.markets) % 3 else 0)
        
        columns = []
        for col_idx in range(3):
            start_idx = col_idx * markets_per_column
            end_idx = min(start_idx + markets_per_column, len(self.markets))
            
            if start_idx < len(self.markets):
                # Create table for this column
                table = Table(show_header=False, show_edge=False, pad_edge=False, box=None)
                table.add_column("Market", style="cyan", width=12)
                table.add_column("Trades", style="yellow", width=8)
                table.add_column("Price", style="green", width=12)
                table.add_column("Status", style="blue", width=12)
                
                # Add rows for markets in this column
                for i in range(start_idx, end_idx):
                    market = self.markets[i]
                    data = self.market_data[market]
                    price_str = f"${data['last_price']:,.2f}" if data['last_price'] > 0 else "Waiting..."
                    status = "🟢 Live" if data['trade_count'] > 0 else "🔄 Connecting..."
                    
                    table.add_row(
                        market,
                        str(data['trade_count']),
                        price_str,
                        status
                    )
                
                columns.append(table)
        
        # Create columns layout
        if columns:
            columns_display = Columns(columns, equal=True, expand=True)
        else:
            columns_display = "No markets available"
        
        # Create main container with title
        from rich.panel import Panel
        main_panel = Panel(
            columns_display,
            title=f"🚀 Live Trades Dashboard - {len(self.markets)} Active Markets",
            title_align="center",
            border_style="bold cyan",
            padding=(1, 2)
        )
        
        return main_panel
    
    def _on_trade_received(self, trade_data, market_id):
        """Handle incoming trade data for a specific market"""
        try:
            # Extract price from trade data
            if isinstance(trade_data, dict):
                price = float(trade_data.get('price', 0))
                if price > 0 and market_id in self.market_data:
                    self.market_data[market_id]['last_price'] = price
                    self.market_data[market_id]['trade_count'] += 1
        except Exception as e:
            pass  # Ignore parsing errors for now
    
    def run(self):
        """Run the dashboard"""
        # Connect to dYdX stream
        if not self.stream.connect():
            self.console.print("❌ Failed to connect to dYdX stream")
            return
        
        # Subscribe to each market
        subscriptions = []
        for market in self.markets:
            observable = self.stream.get_trades_observable(market)
            subscription = observable.subscribe(
                on_next=lambda trade_data, m=market: self._on_trade_received(trade_data, m),
                on_error=lambda e, m=market: None  # Silently handle stream errors
            )
            subscriptions.append(subscription)
        
        # Live dashboard loop
        with Live(self._create_display_table(), refresh_per_second=2) as live:
            try:
                while self.running:
                    live.update(self._create_display_table())
                    time.sleep(0.5)
            except KeyboardInterrupt:
                pass
        
        # Cleanup
        for subscription in subscriptions:
            subscription.dispose()


if __name__ == "__main__":
    dashboard = BTCDashboard()
    dashboard.run()
