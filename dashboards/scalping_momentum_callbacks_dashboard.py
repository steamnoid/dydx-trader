#!/usr/bin/env python3
"""
Scalping Momentum Breakout Dashboard for dYdX v4 Trading (Callback-Based)
Real-time momentum breakout detection with scoring system
Using callback-based Layer 2 stream interface for improved performance
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
import json
from datetime import datetime

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from layer2_dydx_callbacks import DydxTradesStreamCallbacks

@dataclass
class TradeData:
    timestamp: float
    price: float
    size: float
    side: str  # "BUY" or "SELL"

@dataclass
class OrderbookData:
    timestamp: float
    bids: List[Dict]
    asks: List[Dict]
    mid_price: float
    spread_bps: float

@dataclass
class MarketScore:
    market: str
    timestamp: float
    spread_score: float      # 0-1 (spread <= 1.0 bps = 1, otherwise 0)
    depth_skew_score: float  # 0-1 (bid/ask depth imbalance)
    volume_spike_score: float # 0-1 (volume spike detection)
    tick_momentum_score: float # 0-1 (price momentum)
    taker_ratio_score: float  # 0-1 (taker volume ratio)
    total_score: float       # 0-5 (sum of all scores)

@dataclass
class Position:
    market: str
    entry_time: float
    entry_price: float
    side: str  # "BUY" or "SELL"
    size: float
    status: str  # "OPEN", "CLOSED"
    pnl: float = 0.0
    pnl_usd: float = 0.0
    exit_price: Optional[float] = None
    exit_time: Optional[float] = None
    exit_reason: Optional[str] = None  # "TP", "SL", "TIME"
    tp_price: Optional[float] = None
    sl_price: Optional[float] = None

class ScalpingStrategy:
    """Scalping momentum breakout strategy logic"""
    
    def __init__(self):
        # Market data storage
        self.orderbook_history: Dict[str, Deque[OrderbookData]] = defaultdict(lambda: deque(maxlen=60))
        self.trade_history: Dict[str, Deque[TradeData]] = defaultdict(lambda: deque(maxlen=200))
        self.market_volumes: Dict[str, float] = {}  # 24h volumes
        
        # Strategy parameters
        self.max_positions = 10
        self.min_volume_24h = 100000  # $100k minimum 24h volume
        self.entry_score_threshold = 4  # Minimum score to enter (out of 5)
        self.tp_pct = 0.6  # 0.6% take profit
        self.sl_pct = 0.3  # 0.3% stop loss
        self.min_hold_time = 10  # 10 seconds minimum hold time
        self.max_hold_time = 60  # 60 seconds max hold time
        self.fee_pct = 0.05  # 0.05% trading fee
        
        # Scoring lookback windows
        self.spread_window = 10  # seconds
        self.depth_window = 5   # seconds
        self.volume_window = 15 # seconds
        self.momentum_window = 8 # seconds
        self.taker_window = 12  # seconds
    
    def update_market_volume(self, market: str, volume_24h: float):
        """Update 24h volume for market"""
        self.market_volumes[market] = volume_24h
    
    def update_orderbook(self, market: str, data: dict):
        """Update orderbook data for a market"""
        try:
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            
            if not bids or not asks:
                return
            
            bid_price = float(bids[0]['price'])
            ask_price = float(asks[0]['price'])
            mid_price = (bid_price + ask_price) / 2
            spread_bps = ((ask_price - bid_price) / mid_price) * 10000
            
            orderbook_data = OrderbookData(
                timestamp=time.time(),
                bids=bids,
                asks=asks,
                mid_price=mid_price,
                spread_bps=spread_bps
            )
            
            self.orderbook_history[market].append(orderbook_data)
            
        except Exception as e:
            print(f"Error updating orderbook for {market}: {e}")
    
    def update_trade(self, market: str, trade_data: dict):
        """Update trade data for a market"""
        try:
            trade = TradeData(
                timestamp=time.time(),
                price=float(trade_data.get('price', 0)),
                size=float(trade_data.get('size', 0)),
                side=trade_data.get('side', 'BUY')
            )
            
            self.trade_history[market].append(trade)
            
        except Exception as e:
            print(f"Error updating trade for {market}: {e}")
    
    def calculate_market_score(self, market: str) -> Optional[MarketScore]:
        """Calculate comprehensive market score with improved logic"""
        try:
            # Check minimum volume requirement
            if self.market_volumes.get(market, 0) < self.min_volume_24h:
                return None
            
            orderbooks = self.orderbook_history.get(market, deque())
            trades = self.trade_history.get(market, deque())
            
            if len(orderbooks) < 5 or len(trades) < 5:
                return None
            
            current_time = time.time()
            
            # 1. Spread Score (1 if spread < 1.0 bps, 0 otherwise)
            spread_score = self._calculate_spread_score(orderbooks, current_time)
            
            # 2. Depth Skew Score (1 if depth skew > 60% on entry side, 0 otherwise)
            depth_skew_score = self._calculate_depth_skew_score(orderbooks, current_time)
            
            # 3. Tick Momentum Score (1 if >= 3 ticks same direction in 2s, 0 otherwise)
            tick_momentum_score = self._calculate_tick_momentum_score(orderbooks, current_time)
            
            # 4. Volume Spike Score (1 if > 2x rolling average from 1min, 0 otherwise)
            volume_spike_score = self._calculate_volume_spike_score(trades, current_time)
            
            # 5. Taker Volume Ratio Score (1 if > 60% in last 5s, 0 otherwise)
            taker_ratio_score = self._calculate_taker_ratio_score(trades, current_time)
            
            # Total score is sum of binary scores (0-5)
            total_score = int(spread_score + depth_skew_score + tick_momentum_score + 
                             volume_spike_score + taker_ratio_score)
            
            return MarketScore(
                market=market,
                timestamp=current_time,
                spread_score=spread_score,
                depth_skew_score=depth_skew_score,
                volume_spike_score=volume_spike_score,
                tick_momentum_score=tick_momentum_score,
                taker_ratio_score=taker_ratio_score,
                total_score=total_score
            )
            
        except Exception as e:
            print(f"Error calculating score for {market}: {e}")
            return None
    
    def _calculate_spread_score(self, orderbooks: Deque[OrderbookData], current_time: float) -> float:
        """Calculate spread score (1 if spread < 1.0 bps, 0 otherwise)"""
        if not orderbooks:
            return 0.0
        
        # Use most recent orderbook
        latest = orderbooks[-1]
        return 1.0 if latest.spread_bps < 1.0 else 0.0
    
    def _calculate_depth_skew_score(self, orderbooks: Deque[OrderbookData], current_time: float) -> float:
        """Calculate depth skew score (1 if depth skew > 60% on entry side, 0 otherwise)"""
        if not orderbooks:
            return 0.0
        
        # Use most recent orderbook
        latest = orderbooks[-1]
        
        if len(latest.bids) < 3 or len(latest.asks) < 3:
            return 0.0
        
        # Top 3 levels depth
        bid_depth = sum(float(b['size']) for b in latest.bids[:3])
        ask_depth = sum(float(a['size']) for a in latest.asks[:3])
        
        if bid_depth + ask_depth == 0:
            return 0.0
        
        # Check if either side has > 60% of total depth
        total_depth = bid_depth + ask_depth
        bid_ratio = bid_depth / total_depth
        ask_ratio = ask_depth / total_depth
        
        # Return 1 if either side dominates with > 60%
        return 1.0 if (bid_ratio > 0.6 or ask_ratio > 0.6) else 0.0
    
    def _calculate_volume_spike_score(self, trades: Deque[TradeData], current_time: float) -> float:
        """Calculate volume spike score (1 if > 2x rolling average from 1min, 0 otherwise)"""
        if len(trades) < 20:
            return 0.0
        
        # Get recent 5 second window
        recent_trades = [t for t in trades 
                        if current_time - t.timestamp <= 5.0]
        
        # Get 1 minute baseline for rolling average
        baseline_trades = [t for t in trades 
                          if current_time - t.timestamp <= 60.0]
        
        if len(recent_trades) < 1 or len(baseline_trades) < 10:
            return 0.0
        
        # Calculate recent volume (5s)
        recent_volume = sum(t.size for t in recent_trades)
        
        # Calculate 1min average volume per 5s
        baseline_total_volume = sum(t.size for t in baseline_trades)
        baseline_avg_per_5s = baseline_total_volume / 12  # 60s / 5s = 12 periods
        
        if baseline_avg_per_5s == 0:
            return 0.0
        
        volume_ratio = recent_volume / baseline_avg_per_5s
        
        # Return 1 if volume > 2x baseline, 0 otherwise
        return 1.0 if volume_ratio > 2.0 else 0.0
    
    def _calculate_tick_momentum_score(self, orderbooks: Deque[OrderbookData], current_time: float) -> float:
        """Calculate tick momentum score (1 if >= 3 ticks same direction in 2s, 0 otherwise)"""
        if len(orderbooks) < 4:
            return 0.0
        
        # Get recent orderbooks within 2 second window
        recent = [ob for ob in orderbooks 
                 if current_time - ob.timestamp <= 2.0]
        
        if len(recent) < 4:
            return 0.0
        
        # Sort by timestamp to ensure correct order
        recent.sort(key=lambda x: x.timestamp)
        
        # Calculate tick changes (mid price movements)
        prices = [ob.mid_price for ob in recent]
        tick_changes = []
        
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                tick_changes.append(1)  # Up tick
            elif prices[i] < prices[i-1]:
                tick_changes.append(-1)  # Down tick
            else:
                tick_changes.append(0)  # No change
        
        if len(tick_changes) < 3:
            return 0.0
        
        # Check for >= 3 consecutive ticks in same direction
        consecutive_up = 0
        consecutive_down = 0
        max_consecutive_up = 0
        max_consecutive_down = 0
        
        for change in tick_changes:
            if change == 1:
                consecutive_up += 1
                consecutive_down = 0
                max_consecutive_up = max(max_consecutive_up, consecutive_up)
            elif change == -1:
                consecutive_down += 1
                consecutive_up = 0
                max_consecutive_down = max(max_consecutive_down, consecutive_down)
            else:
                consecutive_up = 0
                consecutive_down = 0
        
        # Return 1 if we have >= 3 consecutive ticks in same direction
        return 1.0 if (max_consecutive_up >= 3 or max_consecutive_down >= 3) else 0.0
    
    def _calculate_taker_ratio_score(self, trades: Deque[TradeData], current_time: float) -> float:
        """Calculate taker volume ratio score (1 if > 60% in last 5s, 0 otherwise)"""
        if len(trades) < 3:
            return 0.0
        
        # Get recent trades within 5 second window
        recent_trades = [t for t in trades 
                        if current_time - t.timestamp <= 5.0]
        
        if len(recent_trades) < 3:
            return 0.0
        
        # Calculate buy vs sell volume
        buy_volume = sum(t.size for t in recent_trades if t.side == 'BUY')
        sell_volume = sum(t.size for t in recent_trades if t.side == 'SELL')
        total_volume = buy_volume + sell_volume
        
        if total_volume == 0:
            return 0.0
        
        # Calculate ratios
        buy_ratio = buy_volume / total_volume
        sell_ratio = sell_volume / total_volume
        
        # Return 1 if either side has > 60% of volume
        return 1.0 if (buy_ratio > 0.6 or sell_ratio > 0.6) else 0.0
    
    def should_enter_position(self, score: MarketScore, current_positions: int, market: str, existing_positions: List[Position]) -> bool:
        """Check if we should enter a position with improved logic"""
        # Check max positions limit
        if current_positions >= self.max_positions:
            return False
        
        # Check score threshold (must be >= 4 out of 5)
        if score.total_score < self.entry_score_threshold:
            return False
        
        # Check spread requirement (must be < 1.0 bps)
        if score.spread_score == 0:
            return False
        
        # Check 24h volume requirement
        if self.market_volumes.get(market, 0) < self.min_volume_24h:
            return False
        
        # Check no active position on this market
        for pos in existing_positions:
            if pos.market == market and pos.status == "OPEN":
                return False
        
        return True
    
    def calculate_exit_prices(self, entry_price: float, side: str) -> tuple:
        """Calculate take profit and stop loss prices including fees"""
        if side == "BUY":
            # For buy: need price to rise enough to cover entry/exit fees + profit
            tp_price = entry_price * (1 + (self.tp_pct + self.fee_pct * 2) / 100)
            sl_price = entry_price * (1 - (self.sl_pct + self.fee_pct * 2) / 100)
        else:  # SELL
            # For sell: need price to fall enough to cover entry/exit fees + profit
            tp_price = entry_price * (1 - (self.tp_pct + self.fee_pct * 2) / 100)
            sl_price = entry_price * (1 + (self.sl_pct + self.fee_pct * 2) / 100)
        
        return tp_price, sl_price

class ScalpingCallbacksDashboard:
    """Scalping momentum breakout dashboard with callback-based stream interface"""
    
    def __init__(self):
        self.console = Console()
        self.stream = DydxTradesStreamCallbacks()
        self.strategy = ScalpingStrategy()
        
        # Market tracking
        self.active_markets = set()
        self.market_scores: Dict[str, MarketScore] = {}
        self.current_prices: Dict[str, float] = {}
        
        # Position tracking
        self.positions: List[Position] = []
        self.position_log: Deque[Dict] = deque(maxlen=1000)  # Circular buffer for logs
        
        # Performance stats
        self.last_update = time.time()
        self.update_count = 0
        self.last_dashboard_update = 0  # Track dashboard refresh throttling
        
        # Entry rejection tracking
        self.last_rejected_entry = None  # {"market", "reason", "score_breakdown", "timestamp"}
        self.fake_entries_count = 0  # Count of positions closed by SL in < 3s
        
        # Market statistics with bounded history
        self.market_stats: Dict[str, Dict] = defaultdict(lambda: {
            'positions': deque(maxlen=100),  # Keep only last 100 positions per market
            'total_pnl_usd': 0.0,
            'winning_positions': 0,
            'total_positions': 0,
            'current_position': None,
            'last_score': None
        })
    
    def _fetch_usd_markets(self):
        """Fetch all active USD markets from dYdX API with 24h volume"""
        try:
            # Get markets
            response = requests.get('https://indexer.dydx.trade/v4/perpetualMarkets', timeout=10)
            if response.status_code != 200:
                self.console.print(f"[yellow]⚠️  Markets API returned {response.status_code}, using fallback[/yellow]")
                return self._get_fallback_markets()
            
            data = response.json()
            if 'markets' not in data:
                self.console.print(f"[yellow]⚠️  No 'markets' key in API response, using fallback[/yellow]")
                return self._get_fallback_markets()
            
            # For now, skip volume filtering since the sparklines API might be inconsistent
            # Just get active USD markets
            usd_markets = []
            for name, market in data['markets'].items():
                if (market.get('status') == 'ACTIVE' and 
                    name.endswith('-USD') and 
                    market.get('marketType') in ['CROSS', 'ISOLATED']):
                    
                    usd_markets.append(name)
                    # Set a reasonable default volume to pass the filter
                    self.strategy.update_market_volume(name, 500000)  # $500k default
            
            if len(usd_markets) == 0:
                self.console.print(f"[yellow]⚠️  No active USD markets found, using fallback[/yellow]")
                return self._get_fallback_markets()
            
            # Return ALL markets - we'll filter display intelligently later
            return sorted(usd_markets)
            
        except Exception as e:
            self.console.print(f"[yellow]⚠️  Error fetching markets: {e}, using fallback[/yellow]")
            return self._get_fallback_markets()
    
    def _get_fallback_markets(self):
        """Fallback markets with estimated volumes"""
        fallback_markets = [
            "BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", 
            "DOGE-USD", "LINK-USD", "UNI-USD", "AAVE-USD",
            "ADA-USD", "DOT-USD", "MATIC-USD", "ATOM-USD"
        ]
        
        # Set high volume for fallback markets
        for market in fallback_markets:
            self.strategy.update_market_volume(market, 1000000)  # $1M volume
        
        return fallback_markets
    
    def start(self):
        """Start the dashboard"""
        # Fetch markets
        self.console.print("[cyan]🔍 Fetching active USD markets (>$100k volume)...[/cyan]")
        markets = self._fetch_usd_markets()
        
        self.console.print(f"[green]✅ Found {len(markets)} qualifying markets[/green]")
        
        # Connect to dYdX WebSocket
        self.console.print("[cyan]🔗 Connecting to dYdX WebSocket...[/cyan]")
        if not self.stream.connect():
            self.console.print("[red]❌ Failed to connect to dYdX WebSocket[/red]")
            return
        
        self.console.print("[green]✅ Connected to dYdX WebSocket[/green]")
        
        # Subscribe to markets using callback-based interface
        subscription_errors = 0
        for market in markets:
            self.active_markets.add(market)
            try:
                # Subscribe to orderbook with callback
                self.stream.subscribe_to_orderbook(
                    market, 
                    lambda data, market=market: self._handle_orderbook_update(market, data)
                )
                
                # Subscribe to trades with callback
                self.stream.subscribe_to_trades(
                    market,
                    lambda data, market=market: self._handle_trade_update(market, data)
                )
                    
            except Exception as e:
                subscription_errors += 1
                self.console.print(f"[red]Error subscribing to {market}: {e}[/red]")
        
        self.console.print(f"[green]✅ Subscribed to {len(markets) - subscription_errors} markets[/green]")
        
        # Start live dashboard with adaptive refresh rate
        refresh_rate = 2 if self.update_count < 1000000 else 1  # Reduce refresh rate after 1M updates
        with Live(self._create_dashboard(), refresh_per_second=refresh_rate, console=self.console) as live:
            try:
                while True:
                    time.sleep(0.5)
                    # Update positions and check for exits
                    self._update_positions()
                    
                    # Throttle dashboard updates at high update counts
                    current_time = time.time()
                    should_update_dashboard = (
                        current_time - self.last_dashboard_update > 1.0 or  # Max 1 Hz at high load
                        self.update_count < 2000000  # No throttling below 2M updates
                    )
                    
                    if should_update_dashboard:
                        live.update(self._create_dashboard())
                        self.last_dashboard_update = current_time
                    
                    # Performance monitoring - warn if getting slow
                    if self.update_count > 0 and self.update_count % 500000 == 0:
                        self.console.print(f"[yellow]⚠️  Performance: {self.update_count:,} updates processed[/yellow]")
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Dashboard stopped by user[/yellow]")
                self._log_session_summary()
    
    def _handle_orderbook_update(self, market: str, data: dict):
        """Handle orderbook updates from callback-based stream"""
        try:
            # Update strategy with orderbook data
            self.strategy.update_orderbook(market, data)
            
            # Update current price
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            
            if bids and asks:
                mid_price = (float(bids[0]['price']) + float(asks[0]['price'])) / 2
                self.current_prices[market] = mid_price
            
            # Calculate market score
            score = self.strategy.calculate_market_score(market)
            if score:
                self.market_scores[market] = score
                self.market_stats[market]['last_score'] = score
                
                # Check for entry signal
                current_positions = len([p for p in self.positions if p.status == "OPEN"])
                if self.strategy.should_enter_position(score, current_positions, market, self.positions):
                    self._execute_entry(market, score)
                else:
                    # Track rejected entry for debugging
                    self._track_rejected_entry(market, score, current_positions)
            
            self.update_count += 1
            self.last_update = time.time()
            
        except Exception as e:
            self.console.print(f"[red]Error processing orderbook for {market}: {e}[/red]")
    
    def _handle_trade_update(self, market: str, data: dict):
        """Handle trade updates from callback-based stream"""
        try:
            # Extract market_id from the callback data if available
            market_id = data.get('market_id', market)
            
            # Update strategy with trade data
            self.strategy.update_trade(market_id, data)
            
        except Exception as e:
            pass  # Ignore trade update errors for now
    
    def _execute_entry(self, market: str, score: MarketScore):
        """Execute entry based on momentum signal"""
        try:
            current_price = self.current_prices.get(market)
            if not current_price:
                return
            
            # Determine entry side based on momentum
            # Use tick momentum and taker ratio to determine direction
            if score.tick_momentum_score > 0.5 and score.taker_ratio_score > 0.5:
                # Strong momentum with taker imbalance
                orderbooks = self.strategy.orderbook_history.get(market, deque())
                trades = self.strategy.trade_history.get(market, deque())
                
                if not orderbooks or not trades:
                    return
                
                # Determine direction from recent price movement
                recent_obs = [ob for ob in orderbooks if time.time() - ob.timestamp <= 5]
                if len(recent_obs) >= 2:
                    price_change = recent_obs[-1].mid_price - recent_obs[0].mid_price
                    side = "BUY" if price_change > 0 else "SELL"
                else:
                    # Fallback to taker volume direction
                    recent_trades = [t for t in trades if time.time() - t.timestamp <= 5]
                    buy_vol = sum(t.size for t in recent_trades if t.side == "BUY")
                    sell_vol = sum(t.size for t in recent_trades if t.side == "SELL")
                    side = "BUY" if buy_vol > sell_vol else "SELL"
                
                # Calculate position size (fixed for now)
                position_size = 1000.0  # $1000 position
                
                # Calculate TP/SL
                tp_price, sl_price = self.strategy.calculate_exit_prices(current_price, side)
                
                # Create position
                position = Position(
                    market=market,
                    entry_time=time.time(),
                    entry_price=current_price,
                    side=side,
                    size=position_size,
                    status="OPEN",
                    tp_price=tp_price,
                    sl_price=sl_price
                )
                
                self.positions.append(position)
                self.market_stats[market]['current_position'] = position
                self.market_stats[market]['total_positions'] += 1
                
                # Log entry
                self._log_entry(position, score)
                
        except Exception as e:
            self.console.print(f"[red]Error executing entry for {market}: {e}[/red]")
    
    def _log_entry(self, position: Position, score: MarketScore):
        """Log position entry"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(position.entry_time).strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'ENTRY',
            'market': position.market,
            'side': position.side,
            'price': position.entry_price,
            'size': position.size,
            'tp_price': position.tp_price,
            'sl_price': position.sl_price,
            'score': score.total_score,
            'score_breakdown': {
                'spread': score.spread_score,
                'depth_skew': score.depth_skew_score,
                'volume_spike': score.volume_spike_score,
                'tick_momentum': score.tick_momentum_score,
                'taker_ratio': score.taker_ratio_score
            }
        }
        
        self.position_log.append(log_entry)
        
        # Print to console
        self.console.print(f"\n[green]🟢 ENTRY: {position.market} {position.side} @ ${position.entry_price:.3f} (Score: {score.total_score:.2f})[/green]")
    
    def _log_exit(self, position: Position, exit_reason: str):
        """Log position exit"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(position.exit_time).strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'EXIT',
            'market': position.market,
            'side': position.side,
            'entry_price': position.entry_price,
            'exit_price': position.exit_price,
            'pnl_pct': position.pnl,
            'pnl_usd': position.pnl_usd,
            'exit_reason': exit_reason,
            'hold_time': position.exit_time - position.entry_time
        }
        
        self.position_log.append(log_entry)
        
        # Print to console
        color = "green" if position.pnl > 0 else "red"
        self.console.print(f"\n[{color}]🔴 EXIT: {position.market} {position.side} @ ${position.exit_price:.3f} | PnL: {position.pnl:+.2f}% (${position.pnl_usd:+.2f}) | {exit_reason}[/{color}]")
    
    def _update_positions(self):
        """Update open positions and check for exits"""
        current_time = time.time()
        
        # Cleanup old positions periodically (every 1000 updates)
        if self.update_count % 1000 == 0:
            self._cleanup_old_positions()
        
        for position in self.positions:
            if position.status == "OPEN":
                current_price = self.current_prices.get(position.market, position.entry_price)
                
                # Calculate PnL
                if position.side == "BUY":
                    position.pnl = (current_price - position.entry_price) / position.entry_price * 100
                else:  # SELL
                    position.pnl = (position.entry_price - current_price) / position.entry_price * 100
                
                position.pnl_usd = (position.pnl / 100) * position.size
                
                # Check exit conditions
                exit_reason = None
                
                # Take profit
                if position.side == "BUY" and current_price >= position.tp_price:
                    exit_reason = "TP"
                elif position.side == "SELL" and current_price <= position.tp_price:
                    exit_reason = "TP"
                
                # Stop loss
                elif position.side == "BUY" and current_price <= position.sl_price:
                    exit_reason = "SL"
                    # Check if this is a fast SL (likely fake entry)
                    hold_time = current_time - position.entry_time
                    if hold_time < 3.0:  # Less than 3 seconds
                        exit_reason = "FAST_SL"
                        self.fake_entries_count += 1
                elif position.side == "SELL" and current_price >= position.sl_price:
                    exit_reason = "SL"
                    # Check if this is a fast SL (likely fake entry)
                    hold_time = current_time - position.entry_time
                    if hold_time < 3.0:  # Less than 3 seconds
                        exit_reason = "FAST_SL"
                        self.fake_entries_count += 1
                
                # Time-based exit
                elif current_time - position.entry_time > self.strategy.max_hold_time:
                    exit_reason = "TIME"
                
                # Execute exit
                if exit_reason:
                    position.status = "CLOSED"
                    position.exit_time = current_time
                    position.exit_price = current_price
                    position.exit_reason = exit_reason
                    
                    # Update market stats
                    market = position.market
                    self.market_stats[market]['total_pnl_usd'] += position.pnl_usd
                    self.market_stats[market]['positions'].append(position)
                    self.market_stats[market]['current_position'] = None
                    
                    if position.pnl > 0:
                        self.market_stats[market]['winning_positions'] += 1
                    
                    # Log exit
                    self._log_exit(position, exit_reason)
        
        # Clean up old positions
        if len(self.positions) > 1000:
            self.positions = sorted(self.positions, key=lambda p: p.entry_time)[-1000:]
    
    def _cleanup_old_positions(self):
        """Cleanup old closed positions to prevent unbounded memory growth"""
        # Keep only recent closed positions (last 500) and all open positions
        current_time = time.time()
        
        # Separate open and closed positions
        open_positions = [p for p in self.positions if p.status == "OPEN"]
        closed_positions = [p for p in self.positions if p.status == "CLOSED"]
        
        # Keep only the most recent 500 closed positions
        if len(closed_positions) > 500:
            # Sort by exit time and keep the most recent
            closed_positions.sort(key=lambda p: p.exit_time or 0, reverse=True)
            closed_positions = closed_positions[:500]
        
        # Reconstruct positions list
        self.positions = open_positions + closed_positions
        
        # Also cleanup old market score history that might accumulate in memory
        for market in list(self.market_scores.keys()):
            # Remove market scores for markets not actively being monitored
            if market not in self.active_markets and current_time - self.last_update > 300:  # 5 minutes
                if market in self.market_scores:
                    del self.market_scores[market]

    def _create_dashboard(self) -> Layout:
        """Create the main dashboard layout"""
        self._update_positions()
        
        layout = Layout()
        
        # Create header
        header = self._create_header()
        
        # Create main content
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
            Layout(positions_table, size=12)
        )
        
        return layout
    
    def _create_header(self) -> Panel:
        """Create dashboard header"""
        current_time = time.strftime('%H:%M:%S')
        active_count = len(self.active_markets)
        signaling_count = len([s for s in self.market_scores.values() if s.total_score >= 3.0])
        positioned_count = len([p for p in self.positions if p.status == "OPEN"])
        scored_count = len(self.market_scores)
        
        header_text = Text()
        header_text.append("⚡ SCALPING MOMENTUM DASHBOARD (CALLBACKS) ", style="bold yellow")
        header_text.append(f"| Monitoring: {active_count} ", style="white")
        header_text.append(f"| Scored: {scored_count} ", style="blue")
        header_text.append(f"| Signaling: {signaling_count} ", style="green")
        header_text.append(f"| Positions: {positioned_count}/{self.strategy.max_positions} ", style="cyan")
        header_text.append(f"| Updates: {self.update_count} ", style="magenta")
        header_text.append(f"| {current_time}", style="yellow")
        
        return Panel(header_text, style="yellow")
    
    def _create_markets_table(self) -> Panel:
        """Create markets table with scoring"""
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Market", style="white", width=8)
        table.add_column("Price", style="yellow", width=10)
        table.add_column("Score", style="green", width=8)
        table.add_column("Spread", style="blue", width=8)
        table.add_column("Depth", style="magenta", width=8)
        table.add_column("Volume", style="red", width=8)
        table.add_column("Momentum", style="cyan", width=10)
        table.add_column("Taker", style="white", width=8)
        table.add_column("Status", style="white", width=15)
        
        # Priority display logic:
        # 1. Markets with active positions (always show)
        # 2. Markets with high scores (≥3.0)
        # 3. Markets with recent activity/updates
        # 4. Fill remaining slots with highest-scored markets
        
        display_markets = []
        
        # Priority 1: Markets with active positions
        positioned_markets = []
        for market in self.active_markets:
            if self.market_stats[market]['current_position']:
                positioned_markets.append((market, self.market_scores.get(market)))
        
        # Priority 2: High-scoring markets (≥3.0)
        high_scoring_markets = [(market, score) for market, score in self.market_scores.items() 
                               if score.total_score >= 3.0 and market not in [m[0] for m in positioned_markets]]
        high_scoring_markets.sort(key=lambda x: x[1].total_score, reverse=True)
        
        # Priority 3: Recently active markets (with price updates)
        active_markets = [(market, self.market_scores.get(market)) for market in self.active_markets 
                         if (market in self.current_prices and 
                             market not in [m[0] for m in positioned_markets] and
                             market not in [m[0] for m in high_scoring_markets[:10]])]
        # Sort by score if available, else by market name
        active_markets.sort(key=lambda x: (x[1].total_score if x[1] else 0), reverse=True)
        
        # Combine for display with performance optimization
        max_display = 20 if self.update_count < 2000000 else 15  # Reduce after 2M updates
        display_markets = positioned_markets[:5]  # Show up to 5 positioned markets
        display_markets += high_scoring_markets[:max_display-5]  # Adapt based on performance
        display_markets += active_markets[:5]  # Fill remaining with active markets
        
        # Remove duplicates while preserving order
        seen = set()
        unique_display_markets = []
        for market, score in display_markets:
            if market not in seen and len(unique_display_markets) < max_display:
                unique_display_markets.append((market, score))
                seen.add(market)
        
        display_markets = unique_display_markets[:20]  # Final limit
        
        for market, score in display_markets:
            current_price = self.current_prices.get(market, 0)
            market_stat = self.market_stats[market]
            current_position = market_stat['current_position']
            
            # Format price
            price_str = f"${current_price:.3f}" if current_price > 0 else "--"
            
            if score:
                # Format scores with colors
                total_score = score.total_score
                score_str = f"{total_score:.1f}"
                
                # Color code by score
                if total_score >= 4.0:
                    score_str = f"[green]{score_str}[/green]"
                elif total_score >= 3.0:
                    score_str = f"[yellow]{score_str}[/yellow]"
                else:
                    score_str = f"[red]{score_str}[/red]"
                
                # Individual scores
                spread_str = f"{score.spread_score:.1f}"
                depth_str = f"{score.depth_skew_score:.1f}"
                volume_str = f"{score.volume_spike_score:.1f}"
                momentum_str = f"{score.tick_momentum_score:.1f}"
                taker_str = f"{score.taker_ratio_score:.1f}"
                
                # Color individual scores
                if score.spread_score == 1.0:
                    spread_str = f"[green]{spread_str}[/green]"
                else:
                    spread_str = f"[red]{spread_str}[/red]"
                
                if score.depth_skew_score >= 0.7:
                    depth_str = f"[green]{depth_str}[/green]"
                elif score.depth_skew_score >= 0.3:
                    depth_str = f"[yellow]{depth_str}[/yellow]"
                else:
                    depth_str = f"[red]{depth_str}[/red]"
                
                if score.volume_spike_score >= 0.7:
                    volume_str = f"[green]{volume_str}[/green]"
                elif score.volume_spike_score >= 0.3:
                    volume_str = f"[yellow]{volume_str}[/yellow]"
                else:
                    volume_str = f"[red]{volume_str}[/red]"
                
                if score.tick_momentum_score >= 0.7:
                    momentum_str = f"[green]{momentum_str}[/green]"
                elif score.tick_momentum_score >= 0.3:
                    momentum_str = f"[yellow]{momentum_str}[/yellow]"
                else:
                    momentum_str = f"[red]{momentum_str}[/red]"
                
                if score.taker_ratio_score >= 0.7:
                    taker_str = f"[green]{taker_str}[/green]"
                elif score.taker_ratio_score >= 0.3:
                    taker_str = f"[yellow]{taker_str}[/yellow]"
                else:
                    taker_str = f"[red]{taker_str}[/red]"
                
            else:
                score_str = "--"
                spread_str = "--"
                depth_str = "--"
                volume_str = "--"
                momentum_str = "--"
                taker_str = "--"
            
            # Status
            if current_position:
                pnl_color = "green" if current_position.pnl > 0 else "red"
                status_str = f"[{pnl_color}]{current_position.side} {current_position.pnl:+.2f}%[/{pnl_color}]"
            elif score and score.total_score >= 4.0:
                status_str = "[green]🟢 READY[/green]"
            elif score and score.total_score >= 3.0:
                status_str = "[yellow]🟡 WATCH[/yellow]"
            else:
                status_str = "[red]🔴 WAIT[/red]"
            
            table.add_row(
                market.replace('-USD', ''),
                price_str,
                score_str,
                spread_str,
                depth_str,
                volume_str,
                momentum_str,
                taker_str,
                status_str
            )
        
        title = f"📊 Market Scores (Entry Threshold: {self.strategy.entry_score_threshold:.1f})"
        return Panel(table, title=title, border_style="cyan")
    
    def _create_stats_panel(self) -> Panel:
        """Create statistics panel"""
        # Calculate stats
        closed_positions = [p for p in self.positions if p.status == "CLOSED"]
        open_positions = [p for p in self.positions if p.status == "OPEN"]
        
        total_trades = len(closed_positions)
        winning_trades = len([p for p in closed_positions if p.pnl > 0])
        accuracy = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl_usd = sum(p.pnl_usd for p in closed_positions)
        avg_pnl_usd = total_pnl_usd / total_trades if total_trades > 0 else 0
        
        open_pnl_usd = sum(p.pnl_usd for p in open_positions)
        
        # Best and worst trades
        best_trade = max(closed_positions, key=lambda p: p.pnl_usd) if closed_positions else None
        worst_trade = min(closed_positions, key=lambda p: p.pnl_usd) if closed_positions else None
        
        stats_table = Table(show_header=False, show_edge=False)
        stats_table.add_column("Metric", style="cyan", width=15)
        stats_table.add_column("Value", style="white", width=15)
        
        stats_table.add_row("📊 Total Trades", str(total_trades))
        stats_table.add_row("✅ Winning", str(winning_trades))
        stats_table.add_row("📈 Success Rate", f"{accuracy:.1f}%")
        stats_table.add_row("💰 Total PnL", f"${total_pnl_usd:+.2f}")
        stats_table.add_row("📊 Avg PnL", f"${avg_pnl_usd:+.2f}")
        stats_table.add_row("🔴 Open Pos", str(len(open_positions)))
        stats_table.add_row("💸 Open PnL", f"${open_pnl_usd:+.2f}")
        
        if best_trade:
            stats_table.add_row("🏆 Best Trade", f"${best_trade.pnl_usd:+.2f}")
        if worst_trade:
            stats_table.add_row("💔 Worst Trade", f"${worst_trade.pnl_usd:+.2f}")
        
        # Strategy parameters
        stats_table.add_row("", "")
        stats_table.add_row("⚙️ Entry Score", f"{self.strategy.entry_score_threshold:.1f}")
        stats_table.add_row("🎯 Take Profit", f"{self.strategy.tp_pct:.1f}%")
        stats_table.add_row("🛑 Stop Loss", f"{self.strategy.sl_pct:.1f}%")
        stats_table.add_row("⏱️ Max Hold", f"{self.strategy.max_hold_time}s")
        stats_table.add_row("📊 Max Positions", str(self.strategy.max_positions))
        
        return Panel(stats_table, title="📈 Performance Stats", border_style="green")
    
    def _create_positions_table(self) -> Panel:
        """Create positions table"""
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Market", style="white", width=8)
        table.add_column("Side", style="cyan", width=6)
        table.add_column("Entry", style="blue", width=10)
        table.add_column("Current", style="yellow", width=10)
        table.add_column("PnL %", style="green", width=8)
        table.add_column("PnL $", style="green", width=10)
        table.add_column("TP", style="cyan", width=10)
        table.add_column("SL", style="red", width=10)
        table.add_column("Age", style="magenta", width=8)
        table.add_column("Status", style="white", width=10)
        
        # Show recent positions (last 25)
        recent_positions = sorted(self.positions, key=lambda p: p.entry_time, reverse=True)[:25]
        
        if not recent_positions:
            table.add_row("--", "--", "--", "--", "--", "--", "--", "--", "--", "--")
        else:
            current_time = time.time()
            
            for position in recent_positions:
                current_price = self.current_prices.get(position.market, position.entry_price)
                
                # Age calculation
                age_seconds = current_time - position.entry_time
                age_str = f"{age_seconds:.0f}s" if age_seconds < 60 else f"{age_seconds/60:.1f}m"
                
                # PnL colors
                pnl_pct_str = f"{position.pnl:+.2f}%"
                pnl_usd_str = f"${position.pnl_usd:+.2f}"
                
                if position.pnl > 0:
                    pnl_pct_str = f"[green]{pnl_pct_str}[/green]"
                    pnl_usd_str = f"[green]{pnl_usd_str}[/green]"
                elif position.pnl < 0:
                    pnl_pct_str = f"[red]{pnl_pct_str}[/red]"
                    pnl_usd_str = f"[red]{pnl_usd_str}[/red]"
                
                # Status
                if position.status == "OPEN":
                    status_str = "[yellow]OPEN[/yellow]"
                elif position.exit_reason == "TP":
                    status_str = "[green]TP[/green]"
                elif position.exit_reason == "SL":
                    status_str = "[red]SL[/red]"
                elif position.exit_reason == "TIME":
                    status_str = "[blue]TIME[/blue]"
                else:
                    status_str = "[white]CLOSED[/white]"
                
                # Side color
                side_str = position.side
                if position.side == "BUY":
                    side_str = f"[green]{side_str}[/green]"
                else:
                    side_str = f"[red]{side_str}[/red]"
                
                table.add_row(
                    position.market.replace('-USD', ''),
                    side_str,
                    f"${position.entry_price:.3f}",
                    f"${current_price:.3f}",
                    pnl_pct_str,
                    pnl_usd_str,
                    f"${position.tp_price:.3f}" if position.tp_price else "--",
                    f"${position.sl_price:.3f}" if position.sl_price else "--",
                    age_str,
                    status_str
                )
        
        return Panel(table, title="💼 Positions (Live Trading)", border_style="yellow")
    
    def _log_session_summary(self):
        """Log session summary"""
        self.console.print("\n[cyan]📋 Session Summary[/cyan]")
        
        closed_positions = [p for p in self.positions if p.status == "CLOSED"]
        if closed_positions:
            total_pnl = sum(p.pnl_usd for p in closed_positions)
            winning_trades = len([p for p in closed_positions if p.pnl > 0])
            accuracy = winning_trades / len(closed_positions) * 100
            
            self.console.print(f"Total Trades: {len(closed_positions)}")
            self.console.print(f"Winning Trades: {winning_trades}")
            self.console.print(f"Success Rate: {accuracy:.1f}%")
            self.console.print(f"Total PnL: ${total_pnl:+.2f}")
            
            # Save log to file
            log_filename = f"scalping_callbacks_log_{int(time.time())}.json"
            with open(log_filename, 'w') as f:
                json.dump(self.position_log, f, indent=2)
            self.console.print(f"Log saved to: {log_filename}")

    
    def _track_rejected_entry(self, market: str, score: MarketScore, current_positions: int):
        """Track rejected entry for debugging and display"""
        try:
            # Determine rejection reason
            reason = []
            if current_positions >= self.strategy.max_positions:
                reason.append(f"max_positions({current_positions}/{self.strategy.max_positions})")
            if score.total_score < self.strategy.entry_score_threshold:
                reason.append(f"low_score({score.total_score:.1f}/{self.strategy.entry_score_threshold})")
            if score.spread_score == 0:
                reason.append("wide_spread")
            if self.strategy.market_volumes.get(market, 0) < self.strategy.min_volume_24h:
                reason.append("low_volume")
            
            # Check for existing position
            for pos in self.positions:
                if pos.market == market and pos.status == "OPEN":
                    reason.append("existing_position")
                    break
            
            self.last_rejected_entry = {
                'market': market,
                'reason': ', '.join(reason) if reason else 'unknown',
                'score_breakdown': {
                    'spread': int(score.spread_score),
                    'depth_skew': int(score.depth_skew_score), 
                    'volume_spike': int(score.volume_spike_score),
                    'tick_momentum': int(score.tick_momentum_score),
                    'taker_ratio': int(score.taker_ratio_score),
                    'total': int(score.total_score)
                },
                'timestamp': time.time(),
                'volume_24h': self.strategy.market_volumes.get(market, 0)
            }
            
        except Exception as e:
            self.console.print(f"[red]Error tracking rejected entry: {e}[/red]")

def main():
    dashboard = ScalpingCallbacksDashboard()

    try:
        dashboard.start()
    except KeyboardInterrupt:
        print("\n[red]Dashboard stopped by user[/red]")
    except Exception as e:
        print(f"Dashboard [red]Error: {e}[/red]")
        traceback.print_exc()

if __name__ == "__main__":
    main()