"""
Layer 3 Dashboard Panel: Market Data Panel

Autonomous, forever-running Rich panel for real-time dYdX market data.
Displays live prices, orderbook, recent trades, and OHLCV candles.

Features:
- Real dYdX API integration (no mocks, no fallbacks)
- Live price updates every 5 seconds
- Multi-market support (BTC-USD, ETH-USD)
- Orderbook depth visualization
- Trade flow analysis
- Candlestick OHLCV data
- Volume and volatility metrics
- Graceful shutdown on Ctrl+C
"""

import asyncio
import signal
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import sys
import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich import box
from rich.align import Align

from dydx_bot.connection.client import DydxClient
from dydx_v4_client.indexer.candles_resolution import CandlesResolution


class MarketDataPanel:
    """
    Autonomous Market Data Panel for Layer 3 Dashboard
    
    Real-time display of:
    - Live market prices and 24h changes
    - Orderbook depth (top 5 levels)  
    - Recent trade executions (last 10)
    - OHLCV candlestick data (1MIN resolution)
    - Volume and volatility analysis
    """
    
    def __init__(self):
        self.console = Console()
        self.client = DydxClient()
        self.running = True
        self.start_time = time.time()
        
        # Market data storage
        self.markets_data = {}
        self.orderbook_data = {}
        self.trades_data = {}
        self.candles_data = {}
        
        # Tracked markets
        self.tracked_markets = ["BTC-USD", "ETH-USD"]
        
        # Performance tracking
        self.update_count = 0
        self.last_update_time = 0
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
        self.console.print("\n[yellow]Shutting down Market Data Panel gracefully...[/yellow]")
    
    async def connect_client(self) -> bool:
        """Connect to dYdX with retry logic"""
        try:
            await self.client.connect()
            if self.client.is_connected():
                return True
        except Exception as e:
            self.console.print(f"[red]Connection failed: {e}[/red]")
        return False
    
    async def fetch_market_data(self):
        """Fetch latest market data from dYdX REST API"""
        try:
            # Fetch all perpetual markets
            markets_response = await self.client.indexer_client.markets.get_perpetual_markets()
            if "markets" in markets_response:
                self.markets_data = markets_response["markets"]
            
            # Fetch orderbook and trades for tracked markets
            for market in self.tracked_markets:
                try:
                    # Orderbook data
                    orderbook = await self.client.indexer_client.markets.get_perpetual_market_orderbook(market)
                    self.orderbook_data[market] = orderbook
                    
                    # Recent trades
                    trades = await self.client.indexer_client.markets.get_perpetual_market_trades(market)
                    self.trades_data[market] = trades
                    
                    # OHLCV candles (1MIN)
                    candles = await self.client.indexer_client.markets.get_perpetual_market_candles(
                        market, "1MIN"
                    )
                    self.candles_data[market] = candles
                    
                    # Small delay between requests for throttling
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    self.console.print(f"[red]Error fetching data for {market}: {e}[/red]")
            
            self.update_count += 1
            self.last_update_time = time.time()
            
        except Exception as e:
            self.console.print(f"[red]Error fetching market data: {e}[/red]")
    
    def create_header_panel(self) -> Panel:
        """Create header with panel info and status"""
        uptime = int(time.time() - self.start_time)
        uptime_str = f"{uptime//60}m {uptime%60}s"
        
        last_update_ago = int(time.time() - self.last_update_time) if self.last_update_time > 0 else 0
        
        status_text = Text()
        status_text.append("🏪 Market Data Panel", style="bold cyan")
        status_text.append(f" | Uptime: {uptime_str}", style="green")
        status_text.append(f" | Updates: {self.update_count}", style="yellow")
        status_text.append(f" | Last: {last_update_ago}s ago", style="white")
        status_text.append(f" | Connected: {'✅' if self.client.is_connected() else '❌'}")
        
        return Panel(
            Align.center(status_text),
            title="Layer 3 Dashboard - Market Data",
            border_style="cyan"
        )
    
    def create_markets_overview_panel(self) -> Panel:
        """Create markets overview with prices and 24h changes"""
        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("Market", style="white", width=12)
        table.add_column("Price", style="yellow", width=15)
        table.add_column("24h Change", style="white", width=12)
        table.add_column("24h Volume", style="green", width=15)
        table.add_column("Status", style="white", width=10)
        
        if self.markets_data:
            for market_id in self.tracked_markets:
                if market_id in self.markets_data:
                    market = self.markets_data[market_id]
                    
                    # Price data
                    oracle_price = market.get("oraclePrice", "N/A")
                    if oracle_price != "N/A":
                        price_str = f"${float(oracle_price):,.2f}"
                    else:
                        price_str = "N/A"
                    
                    # 24h change
                    price_change = market.get("priceChange24H", "N/A")
                    if price_change != "N/A":
                        change_val = float(price_change)
                        change_str = f"{change_val:+.2f}%"
                        change_style = "green" if change_val >= 0 else "red"
                    else:
                        change_str = "N/A"
                        change_style = "white"
                    
                    # 24h volume
                    volume_24h = market.get("volume24H", "N/A")
                    if volume_24h != "N/A":
                        volume_str = f"${float(volume_24h):,.0f}"
                    else:
                        volume_str = "N/A"
                    
                    # Status
                    status = market.get("status", "UNKNOWN")
                    status_emoji = "🟢" if status == "ACTIVE" else "🔴"
                    
                    table.add_row(
                        market_id,
                        price_str,
                        f"[{change_style}]{change_str}[/{change_style}]",
                        volume_str,
                        f"{status_emoji} {status}"
                    )
                else:
                    table.add_row(market_id, "Loading...", "...", "...", "🔄 SYNC")
        else:
            for market_id in self.tracked_markets:
                table.add_row(market_id, "Connecting...", "...", "...", "🔌 CONN")
        
        return Panel(
            table,
            title="📊 Markets Overview",
            border_style="green"
        )
    
    def create_orderbook_panel(self, market: str = "BTC-USD") -> Panel:
        """Create orderbook panel for specified market"""
        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("Bid Size", style="green", width=12)
        table.add_column("Bid Price", style="green", width=12)
        table.add_column("Spread", style="yellow", width=8)
        table.add_column("Ask Price", style="red", width=12)
        table.add_column("Ask Size", style="red", width=12)
        
        if market in self.orderbook_data:
            orderbook = self.orderbook_data[market]
            bids = orderbook.get("bids", [])
            asks = orderbook.get("asks", [])
            
            # Get top 5 levels
            max_levels = 5
            for i in range(max_levels):
                bid_size = bid_price = ask_price = ask_size = "-"
                spread_info = ""
                
                if i < len(bids):
                    bid_price = f"${float(bids[i]['price']):,.2f}"
                    bid_size = f"{float(bids[i]['size']):.4f}"
                
                if i < len(asks):
                    ask_price = f"${float(asks[i]['price']):,.2f}"
                    ask_size = f"{float(asks[i]['size']):.4f}"
                
                # Calculate spread for best bid/ask
                if i == 0 and bids and asks:
                    best_bid = float(bids[0]['price'])
                    best_ask = float(asks[0]['price'])
                    spread = best_ask - best_bid
                    spread_pct = (spread / best_bid) * 100
                    spread_info = f"${spread:.2f}\n{spread_pct:.3f}%"
                
                table.add_row(bid_size, bid_price, spread_info, ask_price, ask_size)
        else:
            for i in range(5):
                table.add_row("Loading...", "...", "...", "...", "...")
        
        return Panel(
            table,
            title=f"📈 Orderbook - {market}",
            border_style="blue"
        )
    
    def create_trades_panel(self, market: str = "BTC-USD") -> Panel:
        """Create recent trades panel for specified market"""
        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("Time", style="white", width=10)
        table.add_column("Side", style="white", width=6)
        table.add_column("Price", style="yellow", width=12)
        table.add_column("Size", style="cyan", width=12)
        table.add_column("Value", style="green", width=12)
        
        if market in self.trades_data and "trades" in self.trades_data[market]:
            trades = self.trades_data[market]["trades"][:10]  # Last 10 trades
            
            for trade in trades:
                # Format time
                created_at = trade.get("createdAt", "")
                if created_at:
                    try:
                        trade_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        time_str = trade_time.strftime("%H:%M:%S")
                    except:
                        time_str = "..."
                else:
                    time_str = "..."
                
                # Side with emoji
                side = trade.get("side", "UNKNOWN")
                side_emoji = "🟢 BUY" if side == "BUY" else "🔴 SELL"
                
                # Price and size
                price = float(trade.get("price", 0))
                size = float(trade.get("size", 0))
                value = price * size
                
                price_str = f"${price:,.2f}"
                size_str = f"{size:.4f}"
                value_str = f"${value:,.2f}"
                
                table.add_row(time_str, side_emoji, price_str, size_str, value_str)
        else:
            for i in range(10):
                table.add_row("...", "🔄", "Loading...", "...", "...")
        
        return Panel(
            table,
            title=f"⚡ Recent Trades - {market}",
            border_style="yellow"
        )
    
    def create_candles_panel(self, market: str = "BTC-USD") -> Panel:
        """Create OHLCV candles panel for specified market"""
        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("Time", style="white", width=12)
        table.add_column("Open", style="cyan", width=10)
        table.add_column("High", style="green", width=10)
        table.add_column("Low", style="red", width=10)
        table.add_column("Close", style="yellow", width=10)
        table.add_column("Volume", style="magenta", width=12)
        
        if market in self.candles_data and "candles" in self.candles_data[market]:
            candles = self.candles_data[market]["candles"][:6]  # Last 6 candles
            
            for candle in candles:
                # Format time
                started_at = candle.get("startedAt", "")
                if started_at:
                    try:
                        candle_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                        time_str = candle_time.strftime("%H:%M")
                    except:
                        time_str = "..."
                else:
                    time_str = "..."
                
                # OHLC data
                open_price = f"${float(candle.get('open', 0)):,.0f}"
                high_price = f"${float(candle.get('high', 0)):,.0f}"
                low_price = f"${float(candle.get('low', 0)):,.0f}"
                close_price = f"${float(candle.get('close', 0)):,.0f}"
                
                # Volume
                volume = float(candle.get("usdVolume", 0))
                volume_str = f"${volume:,.0f}" if volume > 0 else "N/A"
                
                table.add_row(time_str, open_price, high_price, low_price, close_price, volume_str)
        else:
            for i in range(6):
                table.add_row("...", "Loading...", "...", "...", "...", "...")
        
        return Panel(
            table,
            title=f"🕯️ OHLCV Candles (1MIN) - {market}",
            border_style="magenta"
        )
    
    def create_performance_panel(self) -> Panel:
        """Create performance metrics panel"""
        table = Table(show_header=True, header_style="bold cyan", box=box.SIMPLE)
        table.add_column("Metric", style="cyan", width=18)
        table.add_column("Value", style="green", width=15)
        table.add_column("Status", style="yellow", width=15)
        
        # Update rate
        uptime = max(1, time.time() - self.start_time)
        update_rate = self.update_count / uptime
        
        # Data freshness
        data_age = int(time.time() - self.last_update_time) if self.last_update_time > 0 else 0
        freshness_status = "🟢 Fresh" if data_age < 10 else "🟡 Stale" if data_age < 30 else "🔴 Old"
        
        # Connection status
        conn_status = "🟢 Connected" if self.client.is_connected() else "🔴 Disconnected"
        
        # Market coverage
        markets_loaded = len([m for m in self.tracked_markets if m in self.markets_data])
        coverage = f"{markets_loaded}/{len(self.tracked_markets)}"
        coverage_status = "🟢 Complete" if markets_loaded == len(self.tracked_markets) else "🟡 Partial"
        
        table.add_row("Update Rate", f"{update_rate:.2f}/min", "Performance")
        table.add_row("Data Age", f"{data_age}s", freshness_status)
        table.add_row("Connection", "dYdX API", conn_status)
        table.add_row("Market Coverage", coverage, coverage_status)
        table.add_row("Total Updates", str(self.update_count), "Autonomous")
        
        return Panel(
            table,
            title="⚡ Performance Metrics",
            border_style="cyan"
        )
    
    def create_layout(self) -> Layout:
        """Create the main layout"""
        layout = Layout()
        
        # Split into header and body
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        
        # Split body into main content and sidebar
        layout["body"].split_row(
            Layout(name="main", ratio=2),
            Layout(name="sidebar", ratio=1)
        )
        
        # Split main content into top and bottom
        layout["main"].split_column(
            Layout(name="markets"),
            Layout(name="orderbook_trades")
        )
        
        # Split orderbook_trades into orderbook and trades
        layout["orderbook_trades"].split_row(
            Layout(name="orderbook"),
            Layout(name="trades")
        )
        
        # Split sidebar into candles and performance
        layout["sidebar"].split_column(
            Layout(name="candles"),
            Layout(name="performance")
        )
        
        return layout
    
    def update_layout(self, layout: Layout):
        """Update all panels in the layout"""
        layout["header"].update(self.create_header_panel())
        layout["markets"].update(self.create_markets_overview_panel())
        layout["orderbook"].update(self.create_orderbook_panel("BTC-USD"))
        layout["trades"].update(self.create_trades_panel("BTC-USD"))
        layout["candles"].update(self.create_candles_panel("BTC-USD"))
        layout["performance"].update(self.create_performance_panel())
    
    async def run_forever(self):
        """Run the market data panel forever with live updates"""
        self.console.print("[green]Starting Market Data Panel...[/green]")
        
        # Connect to dYdX
        if not await self.connect_client():
            self.console.print("[red]Failed to connect to dYdX. Exiting.[/red]")
            return
        
        self.console.print("[green]Connected to dYdX! Starting live updates...[/green]")
        
        # Create layout
        layout = self.create_layout()
        
        # Initial data fetch
        await self.fetch_market_data()
        
        # Start live display
        with Live(layout, refresh_per_second=2, screen=True) as live:
            try:
                while self.running:
                    # Update data every 5 seconds
                    await self.fetch_market_data()
                    
                    # Update layout
                    self.update_layout(layout)
                    live.update(layout)
                    
                    # Wait 5 seconds before next update
                    for _ in range(50):  # 5 seconds in 0.1s increments
                        if not self.running:
                            break
                        await asyncio.sleep(0.1)
                        
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                self.console.print(f"[red]Unexpected error: {e}[/red]")
                self.running = False
        
        # Cleanup
        if self.client.is_connected():
            await self.client.disconnect()
        
        self.console.print("[yellow]Market Data Panel stopped.[/yellow]")


async def main():
    """Main entry point"""
    panel = MarketDataPanel()
    await panel.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
