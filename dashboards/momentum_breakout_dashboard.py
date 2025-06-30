#!/usr/bin/env python3
"""
Momentum Breakout Dashboard for dYdX v4 Trading
Live paper trading dashboard for momentum breakout strategy with Rich terminal UI
"""

import time
import asyncio
import requests
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
class OHLCVCandle:
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class OrderBookSnapshot:
    timestamp: float
    best_bid: float
    best_ask: float
    spread_pct: float

@dataclass
class BreakoutSignal:
    market: str
    timestamp: float
    signal_type: str  # "LONG", "SHORT"
    entry_price: float
    breakout_type: str  # "HIGH_BREAK", "LOW_BREAK"
    volume_ratio: float  # Current vol / avg vol
    confidence: float  # 0-100

@dataclass
class Position:
    market: str
    entry_time: float
    entry_price: float
    signal_type: str  # "LONG", "SHORT"
    size: float
    status: str  # "OPEN", "CLOSED"
    exit_reason: Optional[str] = None  # "TP", "SL", "TIMEOUT"
    pnl_pct: float = 0.0
    pnl_usd: float = 0.0
    unrealized_pnl_pct: float = 0.0
    unrealized_pnl_usd: float = 0.0
    exit_price: Optional[float] = None
    exit_time: Optional[float] = None
    duration_seconds: float = 0.0
    fees_paid: float = 0.0
    slippage_paid: float = 0.0

class MomentumBreakoutStrategy:
    """Momentum breakout strategy with volume confirmation"""
    
    def __init__(self, 
                 lookback_minutes: int = 10,
                 volume_lookback_candles: int = 10,
                 volume_threshold: float = 1.5,
                 max_spread_pct: float = 0.1):
        self.lookback_minutes = lookback_minutes
        self.volume_lookback_candles = volume_lookback_candles
        self.volume_threshold = volume_threshold
        self.max_spread_pct = max_spread_pct
        
        # Market data storage
        self.candles: Dict[str, Deque[OHLCVCandle]] = defaultdict(lambda: deque(maxlen=50))
        self.orderbook: Dict[str, OrderBookSnapshot] = {}
        self.last_prices: Dict[str, float] = {}
    
    def update_trade(self, market: str, trade_data: dict):
        """Update with trade data to build OHLCV candles"""
        try:
            price = float(trade_data.get('price', 0))
            size = float(trade_data.get('size', 0))
            timestamp = time.time()
            
            self.last_prices[market] = price
            
            # Simple 1-minute candle aggregation (simplified for demo)
            current_minute = int(timestamp // 60) * 60
            
            if not self.candles[market] or self.candles[market][-1].timestamp < current_minute:
                # New candle
                candle = OHLCVCandle(
                    timestamp=current_minute,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=size
                )
                self.candles[market].append(candle)
            else:
                # Update current candle
                candle = self.candles[market][-1]
                candle.high = max(candle.high, price)
                candle.low = min(candle.low, price)
                candle.close = price
                candle.volume += size
                
        except Exception as e:
            pass  # Ignore individual trade errors
    
    def update_orderbook(self, market: str, orderbook_data: dict):
        """Update orderbook snapshot"""
        try:
            bids = orderbook_data.get('bids', [])
            asks = orderbook_data.get('asks', [])
            
            if not bids or not asks:
                return
                
            best_bid = float(bids[0]['price'])
            best_ask = float(asks[0]['price'])
            spread_pct = ((best_ask - best_bid) / best_bid) * 100
            
            self.orderbook[market] = OrderBookSnapshot(
                timestamp=time.time(),
                best_bid=best_bid,
                best_ask=best_ask,
                spread_pct=spread_pct
            )
            
        except Exception as e:
            pass  # Ignore individual orderbook errors
    
    def calculate_signal(self, market: str) -> Optional[BreakoutSignal]:
        """Calculate momentum breakout signal"""
        if market not in self.candles or len(self.candles[market]) < self.volume_lookback_candles:
            return None
            
        if market not in self.orderbook:
            return None
            
        # PERFORMANCE FIX: Avoid creating list copy, work directly with deque
        candles_deque = self.candles[market]
        
        # Enhanced current price detection: use trade price with orderbook fallback
        current_price = self.last_prices.get(market, 0)
        if current_price == 0:
            # Fallback to orderbook mid-price for more responsive price detection
            orderbook_snapshot = self.orderbook[market]
            current_price = (orderbook_snapshot.best_bid + orderbook_snapshot.best_ask) / 2
        
        if current_price == 0:
            return None
            
        # Check spread constraint
        orderbook_snapshot = self.orderbook[market]
        if orderbook_snapshot.spread_pct > self.max_spread_pct:
            return None
        
        # Calculate 10-minute high/low (last 10 candles)
        # Work directly with deque elements to avoid list conversion
        if len(candles_deque) < self.lookback_minutes:
            return None
            
        # Get the last N candles for analysis (excluding current incomplete candle)
        lookback_candles = list(candles_deque)[-self.lookback_minutes:-1] if len(candles_deque) > self.lookback_minutes else list(candles_deque)[:-1]
        
        if len(lookback_candles) < self.lookback_minutes - 1:
            return None
            
        high_10min = max(c.high for c in lookback_candles)
        low_10min = min(c.low for c in lookback_candles)
        
        # Calculate volume ratio (last 3 candles vs average of 10)
        if len(candles_deque) < self.volume_lookback_candles:
            return None
            
        # Work with the deque directly for volume calculation
        last_3_candles = list(candles_deque)[-3:]
        last_10_candles = list(candles_deque)[-self.volume_lookback_candles:]
        
        last_3_volume = sum(c.volume for c in last_3_candles)
        avg_volume_10 = sum(c.volume for c in last_10_candles) / self.volume_lookback_candles
        
        if avg_volume_10 == 0:
            return None
            
        volume_ratio = last_3_volume / (avg_volume_10 * 3)  # Normalize for 3 candles
        
        # Check breakout conditions
        signal_type = None
        breakout_type = None
        confidence = 0
        
        if current_price > high_10min and volume_ratio > self.volume_threshold:
            signal_type = "LONG"
            breakout_type = "HIGH_BREAK"
            confidence = min(100, (volume_ratio - 1) * 50)  # Scale confidence based on volume
            
        elif current_price < low_10min and volume_ratio > self.volume_threshold:
            signal_type = "SHORT" 
            breakout_type = "LOW_BREAK"
            confidence = min(100, (volume_ratio - 1) * 50)
            
        if signal_type:
            return BreakoutSignal(
                market=market,
                timestamp=time.time(),
                signal_type=signal_type,
                entry_price=current_price,
                breakout_type=breakout_type,
                volume_ratio=volume_ratio,
                confidence=confidence
            )
            
        return None

class MomentumBreakoutDashboard:
    """Live momentum breakout trading dashboard with Rich terminal UI"""
    
    def __init__(self):
        self.console = Console()
        self.stream = DydxTradesStream()
        self.strategy = MomentumBreakoutStrategy()
        
        # Trading parameters
        self.POSITION_SIZE_USD = 100.0  # Fixed position size
        self.TAKE_PROFIT_PCT = 0.6
        self.STOP_LOSS_PCT = 0.3
        self.POSITION_TIMEOUT_SECONDS = 60
        self.TAKER_FEE_PCT = 0.05
        self.SLIPPAGE_PCT = 0.02
        
        # Market tracking
        self.active_markets = set()
        self.current_prices: Dict[str, float] = {}
        self.signals: Dict[str, BreakoutSignal] = {}
        
        # Position tracking
        self.positions: List[Position] = []
        self.open_positions: List[Position] = []
        self.closed_positions: List[Position] = []
        
        # Performance stats
        self.total_pnl_usd = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_fees_paid = 0.0
        
        # Dashboard stats
        self.last_update = time.time()
        self.update_count = 0
        
        # PERFORMANCE: Add signal calculation throttling to prevent excessive computation
        self.last_signal_check: Dict[str, float] = {}
        self.signal_check_interval = 5.0  # Only check signals every 5 seconds per market
        
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
                # Subscribe to both trades and orderbook
                trades_stream = self.stream.get_trades_observable(market)
                orderbook_stream = self.stream.get_orderbook_observable(market)
                
                # Use default parameter to capture market value properly
                trades_stream.subscribe(
                    lambda data, market=market: self._handle_trade_update(market, data)
                )
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
    
    def _handle_trade_update(self, market: str, data: dict):
        """Handle trade updates from stream"""
        try:
            # Update strategy with trade data
            self.strategy.update_trade(market, data)
            
            # Update current price
            if 'price' in data:
                self.current_prices[market] = float(data['price'])
            
            # PERFORMANCE FIX: Only check for signals periodically, not on every trade
            current_time = time.time()
            last_check = self.last_signal_check.get(market, 0)
            
            if current_time - last_check >= self.signal_check_interval:
                self.last_signal_check[market] = current_time
                
                # Check for breakout signal
                signal = self.strategy.calculate_signal(market)
                if signal and signal.confidence > 60:  # Minimum confidence threshold
                    self.signals[market] = signal
                    self._execute_signal(signal)
            
            self.update_count += 1
            # Reset update counter to prevent unbounded growth and performance degradation
            if self.update_count > 1000000:  # Reset every 1M updates
                self.update_count = 1
            self.last_update = time.time()
            
        except Exception as e:
            self.console.print(f"[red]Error processing trade {market}: {e}[/red]")
    
    def _handle_orderbook_update(self, market: str, data: dict):
        """Handle orderbook updates from stream"""
        try:
            # Update strategy with orderbook data
            self.strategy.update_orderbook(market, data)
            
        except Exception as e:
            self.console.print(f"[red]Error processing orderbook {market}: {e}[/red]")
    
    def _execute_signal(self, signal: BreakoutSignal):
        """Execute trading signal (paper trading)"""
        # Check if we already have a position in this market
        existing_position = next(
            (p for p in self.open_positions if p.market == signal.market),
            None
        )
        
        if existing_position:
            return  # Already have position in this market
        
        # Calculate fees and slippage
        entry_price = signal.entry_price
        if signal.signal_type == "LONG":
            # Long: buy at ask + slippage
            entry_price *= (1 + self.SLIPPAGE_PCT / 100)
        else:
            # Short: sell at bid - slippage
            entry_price *= (1 - self.SLIPPAGE_PCT / 100)
        
        fees = self.POSITION_SIZE_USD * (self.TAKER_FEE_PCT / 100)
        
        # Create new position
        position = Position(
            market=signal.market,
            entry_time=signal.timestamp,
            entry_price=entry_price,
            signal_type=signal.signal_type,
            size=self.POSITION_SIZE_USD,
            status="OPEN",
            fees_paid=fees,
            slippage_paid=abs(entry_price - signal.entry_price) / signal.entry_price * self.POSITION_SIZE_USD
        )
        
        self.positions.append(position)
        self.open_positions.append(position)
        self.total_trades += 1
        self.total_fees_paid += fees
    
    def _update_positions(self):
        """Update open positions and check for exits"""
        current_time = time.time()
        positions_to_close = []
        
        for position in self.open_positions:
            current_price = self.current_prices.get(position.market, position.entry_price)
            
            # Calculate unrealized PnL
            if position.signal_type == "LONG":
                pnl_pct = ((current_price - position.entry_price) / position.entry_price) * 100
            else:  # SHORT
                pnl_pct = ((position.entry_price - current_price) / position.entry_price) * 100
            
            # Account for fees and slippage
            pnl_pct -= (position.fees_paid + position.slippage_paid) / position.size * 100
            
            position.unrealized_pnl_pct = pnl_pct
            position.unrealized_pnl_usd = (pnl_pct / 100) * position.size
            position.duration_seconds = current_time - position.entry_time
            
            # Check exit conditions
            exit_reason = None
            
            if pnl_pct >= self.TAKE_PROFIT_PCT:
                exit_reason = "TP"
            elif pnl_pct <= -self.STOP_LOSS_PCT:
                exit_reason = "SL"
            elif position.duration_seconds > self.POSITION_TIMEOUT_SECONDS:
                exit_reason = "TIMEOUT"
            
            if exit_reason:
                positions_to_close.append((position, exit_reason, current_price))
        
        # Close positions
        for position, exit_reason, exit_price in positions_to_close:
            self._close_position(position, exit_reason, exit_price)
    
    def _close_position(self, position: Position, exit_reason: str, exit_price: float):
        """Close a position"""
        # Calculate additional exit fees and slippage
        exit_fees = position.size * (self.TAKER_FEE_PCT / 100)
        
        if position.signal_type == "LONG":
            # Long exit: sell at bid - slippage
            exit_price *= (1 - self.SLIPPAGE_PCT / 100)
        else:
            # Short exit: buy at ask + slippage
            exit_price *= (1 + self.SLIPPAGE_PCT / 100)
        
        # Calculate final PnL
        if position.signal_type == "LONG":
            pnl_pct = ((exit_price - position.entry_price) / position.entry_price) * 100
        else:  # SHORT
            pnl_pct = ((position.entry_price - exit_price) / position.entry_price) * 100
        
        total_fees = position.fees_paid + exit_fees
        total_slippage = position.slippage_paid + abs(exit_price - self.current_prices.get(position.market, exit_price)) / self.current_prices.get(position.market, exit_price) * position.size
        
        # Account for all costs
        pnl_pct -= (total_fees + total_slippage) / position.size * 100
        pnl_usd = (pnl_pct / 100) * position.size
        
        # Update position
        position.status = "CLOSED"
        position.exit_reason = exit_reason
        position.exit_price = exit_price
        position.exit_time = time.time()
        position.pnl_pct = pnl_pct
        position.pnl_usd = pnl_usd
        position.fees_paid = total_fees
        position.slippage_paid = total_slippage
        
        # Update stats
        self.total_pnl_usd += pnl_usd
        self.total_fees_paid += exit_fees
        
        if pnl_usd > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Move to closed positions
        self.open_positions.remove(position)
        self.closed_positions.append(position)
        
        # Keep only last 100 closed positions
        if len(self.closed_positions) > 100:
            self.closed_positions = self.closed_positions[-100:]
        
        # Clean up main positions list to prevent memory leak
        if len(self.positions) > 500:
            self.positions = sorted(self.positions, key=lambda p: p.entry_time)[-500:]
        
        # PERFORMANCE: Clean up old signal check timestamps to prevent memory growth
        current_time = time.time()
        markets_to_clean = [
            market for market, last_check in self.last_signal_check.items()
            if current_time - last_check > 3600  # Remove timestamps older than 1 hour
        ]
        for market in markets_to_clean:
            del self.last_signal_check[market]
    
    def _create_dashboard(self) -> Layout:
        """Create the main dashboard layout"""
        self._update_positions()
        
        layout = Layout()
        
        # Create components
        header = self._create_header()
        overview_stats = self._create_overview_stats()
        open_positions_table = self._create_open_positions_table()
        closed_positions_table = self._create_closed_positions_table()
        top_trades_panel = self._create_top_trades_panel()
        
        # Layout structure
        layout.split_column(
            Layout(header, size=3),
            Layout(
                Columns([overview_stats, top_trades_panel], equal=True)
            ),
            Layout(open_positions_table, size=12),
            Layout(closed_positions_table, size=12)
        )
        
        return layout
    
    def _create_header(self) -> Panel:
        """Create dashboard header"""
        current_time = time.strftime('%H:%M:%S')
        active_count = len(self.active_markets)
        signal_count = len([s for s in self.signals.values() if s.confidence > 60])
        
        header_text = Text()
        header_text.append("🚀 MOMENTUM BREAKOUT DASHBOARD ", style="bold green")
        header_text.append(f"| Markets: {active_count} ", style="white")
        header_text.append(f"| Signals: {signal_count} ", style="yellow")
        header_text.append(f"| Updates: {self.update_count} ", style="cyan")
        header_text.append(f"| Time: {current_time}", style="magenta")
        
        return Panel(header_text, style="green")
    
    def _create_overview_stats(self) -> Panel:
        """Create overview statistics panel"""
        accuracy = (self.winning_trades / max(1, self.winning_trades + self.losing_trades)) * 100
        avg_pnl = self.total_pnl_usd / max(1, len(self.closed_positions))
        
        stats_table = Table(show_header=False, show_edge=False)
        stats_table.add_column("Metric", style="cyan", width=18)
        stats_table.add_column("Value", style="white", width=15)
        
        stats_table.add_row("📊 Total Trades", str(self.total_trades))
        stats_table.add_row("🟢 Open Positions", str(len(self.open_positions)))
        stats_table.add_row("🔴 Closed Positions", str(len(self.closed_positions)))
        stats_table.add_row("✅ Winning Trades", str(self.winning_trades))
        stats_table.add_row("❌ Losing Trades", str(self.losing_trades))
        stats_table.add_row("🎯 Accuracy", f"{accuracy:.1f}%")
        stats_table.add_row("💰 Total PnL", f"${self.total_pnl_usd:.2f}")
        stats_table.add_row("📈 Avg PnL/Trade", f"${avg_pnl:.2f}")
        stats_table.add_row("💸 Total Fees", f"${self.total_fees_paid:.2f}")
        
        # Strategy parameters
        stats_table.add_row("", "")
        stats_table.add_row("⚙️ Position Size", f"${self.POSITION_SIZE_USD}")
        stats_table.add_row("🎯 Take Profit", f"{self.TAKE_PROFIT_PCT}%")
        stats_table.add_row("🛑 Stop Loss", f"{self.STOP_LOSS_PCT}%")
        stats_table.add_row("⏰ Timeout", f"{self.POSITION_TIMEOUT_SECONDS}s")
        
        return Panel(stats_table, title="📈 Trading Overview", border_style="blue")
    
    def _create_open_positions_table(self) -> Panel:
        """Create open positions table"""
        table = Table(show_header=True, header_style="bold green")
        table.add_column("Market", style="white", width=8)
        table.add_column("Side", style="cyan", width=6)
        table.add_column("Entry", style="blue", width=10)
        table.add_column("Current", style="yellow", width=10)
        table.add_column("PnL %", style="white", width=8)
        table.add_column("PnL $", style="white", width=8)
        table.add_column("Duration", style="magenta", width=8)
        table.add_column("Size", style="white", width=8)
        
        if not self.open_positions:
            table.add_row("--", "--", "--", "--", "--", "--", "--", "--")
        else:
            for position in sorted(self.open_positions, key=lambda p: p.entry_time, reverse=True):
                current_price = self.current_prices.get(position.market, position.entry_price)
                
                # Duration formatting
                duration = position.duration_seconds
                if duration < 60:
                    duration_str = f"{duration:.0f}s"
                else:
                    duration_str = f"{duration/60:.1f}m"
                
                # PnL coloring
                pnl_pct_str = f"{position.unrealized_pnl_pct:+.2f}%"
                pnl_usd_str = f"${position.unrealized_pnl_usd:+.2f}"
                
                if position.unrealized_pnl_pct > 0:
                    pnl_pct_str = f"[green]{pnl_pct_str}[/green]"
                    pnl_usd_str = f"[green]{pnl_usd_str}[/green]"
                elif position.unrealized_pnl_pct < 0:
                    pnl_pct_str = f"[red]{pnl_pct_str}[/red]"
                    pnl_usd_str = f"[red]{pnl_usd_str}[/red]"
                
                # Side coloring
                side_str = position.signal_type
                if position.signal_type == "LONG":
                    side_str = f"[green]LONG[/green]"
                else:
                    side_str = f"[red]SHORT[/red]"
                
                table.add_row(
                    position.market.replace('-USD', ''),
                    side_str,
                    f"${position.entry_price:.2f}",
                    f"${current_price:.2f}",
                    pnl_pct_str,
                    pnl_usd_str,
                    duration_str,
                    f"${position.size:.0f}"
                )
        
        return Panel(table, title=f"🟢 Open Positions ({len(self.open_positions)})", border_style="green")
    
    def _create_closed_positions_table(self) -> Panel:
        """Create closed positions table (recent 10)"""
        table = Table(show_header=True, header_style="bold red")
        table.add_column("Market", style="white", width=8)
        table.add_column("Side", style="cyan", width=6)
        table.add_column("Entry", style="blue", width=10)
        table.add_column("Exit", style="yellow", width=10)
        table.add_column("PnL %", style="white", width=8)
        table.add_column("PnL $", style="white", width=8)
        table.add_column("Duration", style="magenta", width=8)
        table.add_column("Exit", style="white", width=8)
        
        recent_closed = sorted(self.closed_positions, key=lambda p: p.exit_time or 0, reverse=True)[:10]
        
        if not recent_closed:
            table.add_row("--", "--", "--", "--", "--", "--", "--", "--")
        else:
            for position in recent_closed:
                # Duration formatting
                duration = position.duration_seconds
                if duration < 60:
                    duration_str = f"{duration:.0f}s"
                else:
                    duration_str = f"{duration/60:.1f}m"
                
                # PnL coloring
                pnl_pct_str = f"{position.pnl_pct:+.2f}%"
                pnl_usd_str = f"${position.pnl_usd:+.2f}"
                
                if position.pnl_usd > 0:
                    pnl_pct_str = f"[green]{pnl_pct_str}[/green]"
                    pnl_usd_str = f"[green]{pnl_usd_str}[/green]"
                else:
                    pnl_pct_str = f"[red]{pnl_pct_str}[/red]"
                    pnl_usd_str = f"[red]{pnl_usd_str}[/red]"
                
                # Side coloring
                side_str = position.signal_type
                if position.signal_type == "LONG":
                    side_str = f"[green]LONG[/green]"
                else:
                    side_str = f"[red]SHORT[/red]"
                
                # Exit reason coloring
                exit_str = position.exit_reason or "UNKNOWN"
                if exit_str == "TP":
                    exit_str = f"[green]TP[/green]"
                elif exit_str == "SL":
                    exit_str = f"[red]SL[/red]"
                else:
                    exit_str = f"[yellow]{exit_str}[/yellow]"
                
                table.add_row(
                    position.market.replace('-USD', ''),
                    side_str,
                    f"${position.entry_price:.2f}",
                    f"${position.exit_price or 0:.2f}",
                    pnl_pct_str,
                    pnl_usd_str,
                    duration_str,
                    exit_str
                )
        
        return Panel(table, title=f"🔴 Recent Closed Positions (Last 10)", border_style="red")
    
    def _create_top_trades_panel(self) -> Panel:
        """Create top/worst trades panel"""
        if not self.closed_positions:
            return Panel(Text("No closed trades yet", style="yellow"), title="🏆 Best & Worst Trades", border_style="yellow")
        
        # Sort by PnL
        sorted_positions = sorted(self.closed_positions, key=lambda p: p.pnl_usd, reverse=True)
        
        best_3 = sorted_positions[:3]
        worst_3 = sorted_positions[-3:]
        
        content_table = Table(show_header=True, show_edge=False)
        content_table.add_column("Type", style="white", width=6)
        content_table.add_column("Market", style="cyan", width=8)
        content_table.add_column("Side", style="white", width=6)
        content_table.add_column("PnL $", style="white", width=8)
        content_table.add_column("Exit", style="white", width=6)
        
        # Add best trades
        for i, pos in enumerate(best_3):
            side_str = "🟢 L" if pos.signal_type == "LONG" else "🔴 S"
            pnl_str = f"[green]${pos.pnl_usd:+.2f}[/green]"
            exit_str = pos.exit_reason or "?"
            
            content_table.add_row(
                f"#{i+1} 🏆",
                pos.market.replace('-USD', ''),
                side_str,
                pnl_str,
                exit_str
            )
        
        # Add separator
        content_table.add_row("", "", "", "", "")
        
        # Add worst trades
        for i, pos in enumerate(reversed(worst_3)):
            side_str = "🟢 L" if pos.signal_type == "LONG" else "🔴 S"
            pnl_str = f"[red]${pos.pnl_usd:+.2f}[/red]"
            exit_str = pos.exit_reason or "?"
            
            content_table.add_row(
                f"#{i+1} 💀",
                pos.market.replace('-USD', ''),
                side_str,
                pnl_str,
                exit_str
            )
        
        return Panel(content_table, title="🏆 Best & Worst Trades", border_style="yellow")

def main():
    """Main entry point"""
    dashboard = MomentumBreakoutDashboard()
    
    try:
        dashboard.start()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    except Exception as e:
        print(f"Dashboard error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
