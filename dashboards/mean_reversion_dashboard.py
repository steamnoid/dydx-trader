#!/usr/bin/env python3
"""
Mean-Reversion Dashboard for dYdX v4 Trading
Clean, simple terminal dashboard for mean-reversion strategy visualization
"""

import time
import asyncio
import requests
import os
import traceback
from collections import deque, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Deque
import statistics
import numpy as np

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns

from layer2_dydx_stream import DydxTradesStream

@dataclass
class PricePoint:
    timestamp: float
    price: float
    bid: float
    ask: float

@dataclass
class MeanReversionSignal:
    market: str
    timestamp: float
    signal_type: str  # "BUY", "SELL", "NEUTRAL"
    deviation: float  # deviation from mean in %
    entry_price: float
    confidence: float  # 0-100

@dataclass
class Position:
    market: str
    entry_time: float
    entry_price: float
    signal_type: str
    size: float
    status: str  # "OPEN", "CLOSED"
    pnl: float = 0.0
    exit_price: Optional[float] = None
    exit_time: Optional[float] = None

class MeanReversionStrategy:
    """Simple mean-reversion strategy logic"""
    
    def __init__(self, lookback_seconds: int = 10, deviation_threshold: float = 1.5):
        self.lookback_seconds = lookback_seconds
        self.deviation_threshold = deviation_threshold
        self.price_history: Dict[str, Deque[PricePoint]] = defaultdict(lambda: deque(maxlen=100))
    
    def update_price(self, market: str, price_data: dict):
        """Update price history for a market"""
        current_time = time.time()
        
        # Extract price data
        bids = price_data.get('bids', [])
        asks = price_data.get('asks', [])
        
        if not bids or not asks:
            return
            
        bid = float(bids[0]['price'])
        ask = float(asks[0]['price'])
        mid_price = (bid + ask) / 2
        
        price_point = PricePoint(
            timestamp=current_time,
            price=mid_price,
            bid=bid,
            ask=ask
        )
        
        self.price_history[market].append(price_point)
    
    def calculate_signal(self, market: str) -> Optional[MeanReversionSignal]:
        """Calculate mean-reversion signal for a market"""
        if market not in self.price_history:
            return None
            
        prices = self.price_history[market]
        if len(prices) < 5:  # Need minimum history
            return None
            
        current_time = time.time()
        
        # Filter prices within lookback window
        recent_prices = [
            p for p in prices 
            if current_time - p.timestamp <= self.lookback_seconds
        ]
        
        if len(recent_prices) < 3:
            return None
            
        # Calculate statistics
        price_values = [p.price for p in recent_prices]
        mean_price = statistics.mean(price_values)
        std_dev = statistics.stdev(price_values) if len(price_values) > 1 else 0
        
        if std_dev == 0:
            return None
            
        current_price = recent_prices[-1].price
        deviation_pct = ((current_price - mean_price) / mean_price) * 100
        z_score = abs((current_price - mean_price) / std_dev)
        
        # Generate signal
        signal_type = "NEUTRAL"
        confidence = 0.0
        
        if z_score > self.deviation_threshold:
            if current_price > mean_price:
                signal_type = "SELL"  # Price too high, expect reversion down
            else:
                signal_type = "BUY"   # Price too low, expect reversion up
            
            confidence = min(100, z_score * 20)  # Scale confidence
        
        return MeanReversionSignal(
            market=market,
            timestamp=current_time,
            signal_type=signal_type,
            deviation=deviation_pct,
            entry_price=current_price,
            confidence=confidence
        )

class MeanReversionDashboard:
    """Clean mean-reversion dashboard with Rich terminal UI"""
    
    def __init__(self):
        self.console = Console()
        self.stream = DydxTradesStream()
        self.strategy = MeanReversionStrategy()
        
        # Market tracking
        self.active_markets = set()
        self.current_prices: Dict[str, float] = {}
        self.signals: Dict[str, MeanReversionSignal] = {}
        
        # Position tracking (paper trading)
        self.positions: List[Position] = []
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.position_count = 0
        self.winning_positions = 0
        
        # Enhanced market-specific tracking
        self.market_stats: Dict[str, Dict] = defaultdict(lambda: {
            'positions': [],
            'total_pnl_usd': 0.0,
            'winning_positions': 0,
            'total_positions': 0,
            'current_position': None
        })
        
        # Performance stats
        self.last_update = time.time()
        self.update_count = 0
        
    def _fetch_usd_markets(self):
        """Fetch all active USD markets from dYdX API"""
        try:
            response = requests.get('https://indexer.dydx.trade/v4/perpetualMarkets', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'markets' in data:
                    markets = data['markets']
                    
                    # Filter for active USD markets only
                    usd_markets = []
                    for name, market in markets.items():
                        if (market.get('status') == 'ACTIVE' and 
                            name.endswith('-USD') and 
                            market.get('marketType') in ['CROSS', 'ISOLATED']):
                            usd_markets.append(name)
                    
                    # Sort markets for consistent display
                    return sorted(usd_markets)
            
            # Fallback to major USD markets if API fails
            return self._get_fallback_markets()
            
        except Exception as e:
            self.console.print(f"[yellow]⚠️  Error fetching markets: {e}, using fallback[/yellow]")
            return self._get_fallback_markets()
    
    def _get_fallback_markets(self):
        """Fallback markets in case API fetch fails"""
        return [
            "BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", 
            "DOGE-USD", "LINK-USD", "UNI-USD", "AAVE-USD",
            "ADA-USD", "DOT-USD", "MATIC-USD", "ATOM-USD",
            "NEAR-USD", "FTM-USD", "ALGO-USD", "ICP-USD"
        ]
        
    def start(self):
        """Start the dashboard"""
        # Fetch all active USD markets dynamically
        self.console.print("[cyan]🔍 Fetching active USD markets from dYdX...[/cyan]")
        markets = self._fetch_usd_markets()
        
        self.console.print(f"[green]✅ Found {len(markets)} active USD markets[/green]")
        if len(markets) > 20:
            self.console.print(f"[yellow]⚠️  Monitoring {len(markets)} markets - display may be crowded[/yellow]")
        
        # Connect to dYdX WebSocket stream
        self.console.print("[cyan]🔗 Connecting to dYdX WebSocket...[/cyan]")
        if not self.stream.connect():
            self.console.print("[red]❌ Failed to connect to dYdX WebSocket[/red]")
            return
        
        self.console.print("[green]✅ Connected to dYdX WebSocket[/green]")
        
        # Set up market subscriptions
        subscription_errors = 0
        for market in markets:
            self.active_markets.add(market)
            try:
                orderbook_stream = self.stream.get_orderbook_observable(market)
                # Fix: Use default parameter to capture market value properly
                orderbook_stream.subscribe(
                    lambda data, market=market: self._handle_orderbook_update(market, data)
                )
            except Exception as e:
                subscription_errors += 1
                self.console.print(f"[red]Error subscribing to {market}: {e}[/red]")
        
        if subscription_errors > 0:
            self.console.print(f"[yellow]⚠️  {subscription_errors} subscription errors out of {len(markets)} markets[/yellow]")
        
        self.console.print(f"[green]✅ Subscribed to {len(markets) - subscription_errors} markets[/green]")
        
        # Start live dashboard
        with Live(self._create_dashboard(), refresh_per_second=2, console=self.console) as live:
            try:
                while True:
                    time.sleep(0.5)
                    live.update(self._create_dashboard())
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Dashboard stopped by user[/yellow]")
    
    def _handle_orderbook_update(self, market: str, data: dict):
        """Handle orderbook updates from stream"""
        try:
            # Update strategy with new price data
            self.strategy.update_price(market, data)
            
            # Calculate current price
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            
            if bids and asks:
                mid_price = (float(bids[0]['price']) + float(asks[0]['price'])) / 2
                self.current_prices[market] = mid_price
            
            # Generate signal
            signal = self.strategy.calculate_signal(market)
            if signal:
                self.signals[market] = signal
                
                # Simulate position taking for strong signals
                if signal.confidence > 70 and signal.signal_type != "NEUTRAL":
                    self._simulate_position(signal)
            
            self.update_count += 1
            self.last_update = time.time()
            
        except Exception as e:
            # Enhanced error logging for debugging
            self.console.print(f"[red]Error processing {market}: {e}[/red]")
            import traceback
            self.console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
    
    def _simulate_position(self, signal: MeanReversionSignal):
        """Simulate taking a position (paper trading)"""
        # Check if we already have a position in this market
        existing_position = next(
            (p for p in self.positions if p.market == signal.market and p.status == "OPEN"),
            None
        )
        
        if existing_position:
            return  # Already have position in this market
        
        # Create new position
        position = Position(
            market=signal.market,
            entry_time=signal.timestamp,
            entry_price=signal.entry_price,
            signal_type=signal.signal_type,
            size=1000.0,  # Fixed size for simulation
            status="OPEN"
        )
        
        self.positions.append(position)
        self.position_count += 1
        
        # Track market-specific position
        self.market_stats[signal.market]['current_position'] = position
        self.market_stats[signal.market]['total_positions'] += 1
    
    def _update_positions(self):
        """Update open positions with current PnL"""
        current_time = time.time()
        
        for position in self.positions:
            if position.status == "OPEN":
                current_price = self.current_prices.get(position.market, position.entry_price)
                
                # Calculate PnL
                if position.signal_type == "BUY":
                    position.pnl = (current_price - position.entry_price) / position.entry_price * 100
                else:  # SELL
                    position.pnl = (position.entry_price - current_price) / position.entry_price * 100
                
                # Close position after 30 seconds (mean reversion strategy)
                if current_time - position.entry_time > 30:
                    position.status = "CLOSED"
                    position.exit_time = current_time
                    position.exit_price = current_price
                    
                    # Update market-specific stats
                    market = position.market
                    pnl_usd = (position.pnl / 100) * position.size  # Convert % to USD
                    
                    self.market_stats[market]['total_pnl_usd'] += pnl_usd
                    self.market_stats[market]['positions'].append(position)
                    self.market_stats[market]['current_position'] = None
                    
                    if position.pnl > 0:
                        self.winning_positions += 1
                        self.market_stats[market]['winning_positions'] += 1
                    
                    # Keep only last 100 positions per market for avg calculation
                    if len(self.market_stats[market]['positions']) > 100:
                        self.market_stats[market]['positions'] = self.market_stats[market]['positions'][-100:]
                    
                    self.total_pnl += position.pnl
        
        # CRITICAL FIX: Prevent memory leak by cleaning up old closed positions
        # Keep only last 500 positions total (not per market) to prevent unbounded growth
        if len(self.positions) > 500:
            self.positions = sorted(self.positions, key=lambda p: p.entry_time)[-500:]
    
    def _create_dashboard(self) -> Layout:
        """Create the main dashboard layout"""
        self._update_positions()
        
        layout = Layout()
        
        # Create header
        header = self._create_header()
        
        # Create main content - 2 columns
        markets_table = self._create_markets_table()
        stats_panel = self._create_stats_panel()
        
        # Create positions table
        positions_table = self._create_positions_table()
        
        # Layout structure
        layout.split_column(
            Layout(header, size=3),
            Layout(
                Columns([markets_table, stats_panel], equal=True)
            ),
            Layout(positions_table, size=10)
        )
        
        return layout
    
    def _create_header(self) -> Panel:
        """Create dashboard header"""
        current_time = time.strftime('%H:%M:%S')
        active_count = len(self.active_markets)
        signal_count = len([s for s in self.signals.values() if s.signal_type != "NEUTRAL"])
        
        header_text = Text()
        header_text.append("📈 MEAN-REVERSION DASHBOARD ", style="bold blue")
        header_text.append(f"| Markets: {active_count} ", style="white")
        header_text.append(f"| Active Signals: {signal_count} ", style="green")
        header_text.append(f"| Updates: {self.update_count} ", style="cyan")
        header_text.append(f"| Time: {current_time}", style="yellow")
        
        return Panel(header_text, style="blue")
    
    def _create_markets_table(self) -> Panel:
        """Create enhanced markets overview table with comprehensive statistics"""
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Market", style="white", width=8)
        table.add_column("Mid Price", style="yellow", width=10)
        table.add_column("μ (Mean)", style="blue", width=10)
        table.add_column("σ (StdDev)", style="magenta", width=8)
        table.add_column("Deviation", style="green", width=10)
        table.add_column("Avg PnL", style="cyan", width=8)
        table.add_column("Cum PnL", style="yellow", width=9)
        table.add_column("Acc", style="green", width=6)
        table.add_column("W/T", style="white", width=7)
        table.add_column("Status", style="white", width=12)
        
        # Get markets with signals first, then others
        markets_with_signals = []
        markets_without_signals = []
        
        for market in self.active_markets:
            signal = self.signals.get(market)
            if signal and signal.signal_type != "NEUTRAL" and signal.confidence > 50:
                markets_with_signals.append((market, signal.confidence))
            else:
                markets_without_signals.append(market)
        
        # Sort by signal strength (descending)
        markets_with_signals.sort(key=lambda x: x[1], reverse=True)
        
        # Show top signaling markets first, then major markets
        major_markets = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD"]
        other_majors = [m for m in major_markets if m in markets_without_signals]
        
        # Combine lists: active signals first, then major markets, limit to reasonable display size
        display_markets = []
        display_markets.extend([m[0] for m in markets_with_signals[:8]])  # Top 8 signaling markets
        
        remaining_slots = max(0, 12 - len(display_markets))  # Show max 12 markets total
        for market in other_majors[:remaining_slots]:
            if market not in display_markets:
                display_markets.append(market)
        
        # Fill remaining slots with other markets
        remaining_slots = max(0, 12 - len(display_markets))
        for market in sorted(markets_without_signals)[:remaining_slots]:
            if market not in display_markets and market not in major_markets:
                display_markets.append(market)
        
        # Add market rows with enhanced statistics
        for market in display_markets:
            current_price = self.current_prices.get(market, 0)
            signal = self.signals.get(market)
            market_stat = self.market_stats[market]
            
            # Calculate rolling mean and standard deviation
            prices = self.strategy.price_history.get(market, deque())
            recent_prices = [
                p.price for p in prices 
                if time.time() - p.timestamp <= 10
            ]
            
            if recent_prices and len(recent_prices) > 1:
                mean_price = statistics.mean(recent_prices)
                std_dev = statistics.stdev(recent_prices)
                deviation_pct = ((current_price - mean_price) / mean_price) * 100 if mean_price > 0 else 0
                sigma_deviation = (current_price - mean_price) / std_dev if std_dev > 0 else 0
            else:
                mean_price = current_price
                std_dev = 0
                deviation_pct = 0
                sigma_deviation = 0
            
            # Calculate market-specific statistics
            closed_positions = market_stat['positions']
            avg_pnl = statistics.mean([p.pnl for p in closed_positions]) if closed_positions else 0
            cum_pnl_usd = market_stat['total_pnl_usd']
            accuracy = (market_stat['winning_positions'] / len(closed_positions) * 100) if closed_positions else 0
            win_count = market_stat['winning_positions']
            total_count = market_stat['total_positions']
            current_position = market_stat['current_position']
            
            # Format values
            price_str = f"${current_price:.2f}" if current_price > 0 else "--"
            mean_str = f"${mean_price:.2f}" if mean_price > 0 else "--"
            std_str = f"{std_dev:.2f}" if std_dev > 0 else "0.00"
            
            # Deviation with sigma notation
            if abs(sigma_deviation) > 0.1:
                dev_str = f"{sigma_deviation:+.2f}σ"
                if abs(sigma_deviation) > 2.0:
                    dev_str = f"[red]{dev_str}[/red]"
                elif abs(sigma_deviation) > 1.0:
                    dev_str = f"[yellow]{dev_str}[/yellow]"
                else:
                    dev_str = f"[green]{dev_str}[/green]"
            else:
                dev_str = "[blue]~0σ[/blue]"
            
            # Average PnL
            avg_pnl_str = f"{avg_pnl:+.2f}%" if avg_pnl != 0 else "0.00%"
            if avg_pnl > 0:
                avg_pnl_str = f"[green]{avg_pnl_str}[/green]"
            elif avg_pnl < 0:
                avg_pnl_str = f"[red]{avg_pnl_str}[/red]"
            
            # Cumulative PnL in USD
            cum_pnl_str = f"${cum_pnl_usd:+.1f}" if cum_pnl_usd != 0 else "$0.0"
            if cum_pnl_usd > 0:
                cum_pnl_str = f"[green]{cum_pnl_str}[/green]"
            elif cum_pnl_usd < 0:
                cum_pnl_str = f"[red]{cum_pnl_str}[/red]"
            
            # Accuracy
            acc_str = f"{accuracy:.0f}%" if total_count > 0 else "--"
            if accuracy >= 70:
                acc_str = f"[green]{acc_str}[/green]"
            elif accuracy >= 50:
                acc_str = f"[yellow]{acc_str}[/yellow]"
            elif accuracy > 0:
                acc_str = f"[red]{acc_str}[/red]"
            
            # Win/Total ratio
            wt_str = f"{win_count}/{total_count}" if total_count > 0 else "0/0"
            
            # Status with position indicator
            if current_position:
                if current_position.signal_type == "BUY":
                    status_str = f"[green]🟩 LONG {current_position.pnl:+.1f}%[/green]"
                else:
                    status_str = f"[red]🟥 SHORT {current_position.pnl:+.1f}%[/red]"
            elif signal and signal.signal_type != "NEUTRAL":
                if signal.signal_type == "BUY":
                    status_str = f"[yellow]📈 BUY {signal.confidence:.0f}%[/yellow]"
                else:
                    status_str = f"[yellow]📉 SELL {signal.confidence:.0f}%[/yellow]"
            else:
                status_str = "[blue]⚪ Monitor[/blue]"
            
            table.add_row(
                market.replace('-USD', ''),
                price_str,
                mean_str,
                std_str,
                dev_str,
                avg_pnl_str,
                cum_pnl_str,
                acc_str,
                wt_str,
                status_str
            )
        
        # Calculate summary stats
        total_markets = len(self.active_markets)
        signaling_markets = len([m for m in self.active_markets 
                               if self.signals.get(m) and self.signals.get(m).signal_type != "NEUTRAL"])
        active_positions = len([m for m in self.active_markets 
                              if self.market_stats[m]['current_position'] is not None])
        
        title = f"📊 Market Analytics (Showing {len(display_markets)}/{total_markets} markets, {signaling_markets} signaling, {active_positions} positioned)"
        return Panel(table, title=title, border_style="cyan")
    
    def _create_stats_panel(self) -> Panel:
        """Create statistics panel"""
        # Calculate accuracy
        closed_positions = [p for p in self.positions if p.status == "CLOSED"]
        accuracy = (self.winning_positions / len(closed_positions) * 100) if closed_positions else 0
        
        # Average PnL
        avg_pnl = (sum(p.pnl for p in closed_positions) / len(closed_positions)) if closed_positions else 0
        
        # Open positions
        open_positions = [p for p in self.positions if p.status == "OPEN"]
        open_pnl = sum(p.pnl for p in open_positions)
        
        stats_table = Table(show_header=False, show_edge=False)
        stats_table.add_column("Metric", style="cyan", width=15)
        stats_table.add_column("Value", style="white", width=15)
        
        stats_table.add_row("📊 Total Trades", str(self.position_count))
        stats_table.add_row("✅ Winning", str(self.winning_positions))
        stats_table.add_row("📈 Accuracy", f"{accuracy:.1f}%")
        stats_table.add_row("💰 Total PnL", f"{self.total_pnl:.2f}%")
        stats_table.add_row("📊 Avg PnL", f"{avg_pnl:.2f}%")
        stats_table.add_row("🔴 Open Pos", str(len(open_positions)))
        stats_table.add_row("💸 Open PnL", f"{open_pnl:.2f}%")
        
        # Strategy parameters
        stats_table.add_row("", "")
        stats_table.add_row("⚙️ Lookback", f"{self.strategy.lookback_seconds}s")
        stats_table.add_row("📏 Threshold", f"{self.strategy.deviation_threshold:.1f}σ")
        stats_table.add_row("🎯 Min Signal", "70%")
        
        return Panel(stats_table, title="📈 Performance Stats", border_style="green")
    
    def _create_positions_table(self) -> Panel:
        """Create positions table"""
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Market", style="white", width=8)
        table.add_column("Type", style="cyan", width=6)
        table.add_column("Entry", style="blue", width=10)
        table.add_column("Current", style="yellow", width=10)
        table.add_column("PnL %", style="green", width=8)
        table.add_column("Age", style="magenta", width=8)
        table.add_column("Status", style="white", width=8)
        
        # Show recent positions (last 20)
        recent_positions = sorted(self.positions, key=lambda p: p.entry_time, reverse=True)[:20]
        
        if not recent_positions:
            table.add_row("--", "--", "--", "--", "--", "--", "--")
        else:
            current_time = time.time()
            
            for position in recent_positions:
                current_price = self.current_prices.get(position.market, position.entry_price)
                
                # Age calculation
                age_seconds = current_time - position.entry_time
                if age_seconds < 60:
                    age_str = f"{age_seconds:.0f}s"
                else:
                    age_str = f"{age_seconds/60:.1f}m"
                
                # PnL color
                pnl_str = f"{position.pnl:+.2f}%"
                if position.pnl > 0:
                    pnl_str = f"[green]{pnl_str}[/green]"
                elif position.pnl < 0:
                    pnl_str = f"[red]{pnl_str}[/red]"
                
                # Status color
                status_str = position.status
                if position.status == "OPEN":
                    status_str = "[yellow]OPEN[/yellow]"
                elif position.pnl > 0:
                    status_str = "[green]CLOSED[/green]"
                else:
                    status_str = "[red]CLOSED[/red]"
                
                # Signal type color
                signal_str = position.signal_type
                if position.signal_type == "BUY":
                    signal_str = "[green]BUY[/green]"
                else:
                    signal_str = "[red]SELL[/red]"
                
                table.add_row(
                    position.market.replace('-USD', ''),
                    signal_str,
                    f"${position.entry_price:.2f}",
                    f"${current_price:.2f}",
                    pnl_str,
                    age_str,
                    status_str
                )
        
        return Panel(table, title="💼 Recent Positions (Paper Trading)", border_style="yellow")

def main():
    """Main entry point"""
    dashboard = MeanReversionDashboard()
    
    try:
        dashboard.start()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    except Exception as e:
        print(f"Dashboard error: {e}")

if __name__ == "__main__":
    main()
