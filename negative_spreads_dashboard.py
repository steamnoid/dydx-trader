#!/usr/bin/env python3
"""
Negative Spreads Dashboard - Build-First UI Component
Shows ONLY markets with negative spreads using Layer 2 dYdX stream
Negative spreads indicate arbitrage opportunities
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


# dYdX Fee Structure (from official documentation)
# https://docs.dydx.exchange/api_integration-guides/fees_limits_parameters
DYDX_TAKER_FEE_TIER1 = 0.0005  # 5.0 bps (0.05%) for < $1M volume
DYDX_MAKER_FEE_TIER1 = 0.0001  # 1.0 bps (0.01%) for < $1M volume

# For orderbook arbitrage, both trades are typically taker fees
ARBITRAGE_TOTAL_FEES = DYDX_TAKER_FEE_TIER1 * 2  # 10.0 bps (0.10%) total
MINIMUM_PROFITABLE_SPREAD_PCT = ARBITRAGE_TOTAL_FEES * 100  # 0.10%


class NegativeSpreadsDashboard:
    """Dashboard showing only markets with negative spreads (arbitrage opportunities)"""
    
    def __init__(self):
        self.console = Console()
        self.stream = DydxTradesStream()
        
        # Fetch active markets dynamically from dYdX
        self.markets = self._fetch_active_markets()
        
        # Initialize market data for all active markets
        self.market_data = {
            market: {"spread": 0.0, "spread_percentage": 0.0, "mid_price": 0.0} 
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
                    self.console.print(f"[green]✅ Found {len(active_markets)} active markets[/green]")
                    return active_markets
            
            # Fallback if API fails
            self.console.print("[yellow]⚠️  API call failed, using default markets[/yellow]")
            return ["BTC-USD", "ETH-USD", "SOL-USD"]
            
        except Exception as e:
            self.console.print(f"[red]❌ Error fetching markets: {e}[/red]")
            return ["BTC-USD", "ETH-USD", "SOL-USD"]
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.console.print("\n[yellow]🛑 Shutting down dashboard...[/yellow]")
        self.running = False
        sys.exit(0)
    
    def _render_dashboard(self):
        """Render the dashboard showing only negative spreads"""
        from rich.table import Table
        from rich.columns import Columns
        
        # Filter markets to show only those with PROFITABLE negative spreads (after fees)
        negative_spread_markets = [
            market for market in self.markets 
            if (self.market_data[market]['spread'] < 0 and 
                self.market_data[market].get('is_profitable', False))
        ]
        
        if not negative_spread_markets:
            # No negative spreads found
            no_opportunities_table = Table(title="🔍 Arbitrage Opportunities Monitor", show_header=True)
            no_opportunities_table.add_column("Status", style="cyan", width=40)
            no_opportunities_table.add_column("Details", style="yellow", width=40)
            
            no_opportunities_table.add_row(
                "🚫 No Profitable Arbitrage Found",
                f"No spreads > 0.10% fee threshold..."
            )
            
            total_live = sum(1 for market in self.markets if self.market_data[market]['spread'] != 0)
            no_opportunities_table.add_row(
                f"📊 Markets Status",
                f"{total_live}/{len(self.markets)} markets live"
            )
            
            return Panel(
                no_opportunities_table,
                title="🏦 dYdX Negative Spreads Dashboard",
                border_style="blue"
            )
        
        # Show profitable negative spread markets in organized table
        table = Table(title="⚡ PROFITABLE ARBITRAGE OPPORTUNITIES (After 0.10% dYdX Fees)", show_header=True)
        table.add_column("Market", style="cyan", width=12)
        table.add_column("Spread ($)", style="green", width=12)
        table.add_column("Gross %", style="white", width=10)
        table.add_column("Net Profit %", style="bright_green", width=12)
        table.add_column("Mid Price", style="white", width=12)
        table.add_column("Opportunity", style="yellow", width=18)
        
        # Sort by highest net profit (best opportunities first)
        sorted_markets = sorted(
            negative_spread_markets,
            key=lambda m: self.market_data[m]['net_profit_percentage'],
            reverse=True
        )
        
        for market in sorted_markets:
            data = self.market_data[market]
            
            # Classify opportunity by net profit after fees
            net_profit = data['net_profit_percentage']
            
            if net_profit > 0.05:  # > 0.05% net profit
                opportunity_desc = f"🔥 MAJOR ({net_profit:.3f}%)"
            elif net_profit > 0.02:  # > 0.02% net profit
                opportunity_desc = f"⚡ STRONG ({net_profit:.3f}%)"
            elif net_profit > 0:  # Any positive net profit
                opportunity_desc = f"💡 MINOR ({net_profit:.3f}%)"
            else:
                opportunity_desc = f"❌ UNPROFITABLE"
            
            table.add_row(
                market,
                f"[bright_green]${data['spread']:.4f}[/bright_green]",
                f"{data['spread_percentage']:.3f}%",
                f"[bright_green]{data['net_profit_percentage']:.3f}%[/bright_green]",
                f"${data['mid_price']:.2f}" if data['mid_price'] > 0 else "Calculating...",
                opportunity_desc
            )
        
        # Summary statistics
        summary_table = Table(show_header=False, show_edge=False, pad_edge=False, box=None)
        summary_table.add_column("Metric", style="cyan", width=25)
        summary_table.add_column("Value", style="yellow", width=25)
        
        total_negative = len(negative_spread_markets)
        total_monitored = len(self.markets)
        total_live = sum(1 for market in self.markets if self.market_data[market]['spread'] != 0)
        
        summary_table.add_row("🎯 Negative Spreads", f"{total_negative}")
        summary_table.add_row("📊 Markets Monitored", f"{total_monitored}")
        summary_table.add_row("🟢 Markets Live", f"{total_live}")
        
        if negative_spread_markets:
            best_spread = min(self.market_data[m]['spread'] for m in negative_spread_markets)
            summary_table.add_row("⭐ Best Opportunity", f"${best_spread:.4f}")
        
        # Combine tables in columns
        main_content = Columns([table, summary_table], equal=False)
        
        return Panel(
            main_content,
            title="🏦 dYdX Negative Spreads Dashboard - Live Arbitrage Monitor",
            border_style="green"
        )
    
    def _update_market_data_from_orderbook(self, orderbook_data, market):
        """Update market data directly from orderbook updates"""
        if market in self.market_data:
            try:
                # Calculate spread directly from orderbook data
                if orderbook_data and 'bids' in orderbook_data and 'asks' in orderbook_data:
                    if orderbook_data['bids'] and orderbook_data['asks']:
                        best_bid = float(orderbook_data['bids'][0]['price'])
                        best_ask = float(orderbook_data['asks'][0]['price'])
                        
                        spread = best_ask - best_bid
                        mid_price = (best_bid + best_ask) / 2
                        spread_percentage = (spread / mid_price) * 100
                        
                        # Calculate net profit after dYdX fees (both trades = taker fees)
                        fee_cost_percentage = ARBITRAGE_TOTAL_FEES * 100  # 0.10%
                        net_profit_percentage = spread_percentage - fee_cost_percentage
                        
                        self.market_data[market] = {
                            'spread': spread,
                            'spread_percentage': spread_percentage,
                            'net_profit_percentage': net_profit_percentage,
                            'mid_price': mid_price,
                            'is_profitable': net_profit_percentage > 0
                        }
            except Exception as e:
                # Don't crash on calculation errors
                pass

    def run(self):
        """Run the negative spreads dashboard"""
        self.console.print("[blue]🚀 Starting Negative Spreads Dashboard...[/blue]")
        
        # Connect to stream
        if not self.stream.connect():
            self.console.print("[red]❌ Failed to connect to dYdX stream[/red]")
            return
        
        # Subscribe to orderbook updates for all markets
        for market in self.markets:
            orderbook_obs = self.stream.get_orderbook_observable(market)
            orderbook_obs.subscribe(on_next=lambda data, m=market: self._update_market_data_from_orderbook(data, m))
        
        # Start live dashboard
        try:
            with Live(self._render_dashboard(), refresh_per_second=2, screen=True) as live:
                while self.running:
                    live.update(self._render_dashboard())
                    time.sleep(0.5)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]👋 Dashboard stopped by user[/yellow]")
        finally:
            self.stream.disconnect()


if __name__ == "__main__":
    dashboard = NegativeSpreadsDashboard()
    dashboard.run()
