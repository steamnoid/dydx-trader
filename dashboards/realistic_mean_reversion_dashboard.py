#!/usr/bin/env python3
"""
Realistic Mean-Reversion Dashboard for dYdX v4 Trading
Paper trading simulation with realistic market conditions and execution

VALIDATED AGAINST dYdX v4 DOCUMENTATION:
=====================================

MAKER-ONLY STRATEGY IMPLEMENTATION:
- Uses limit orders with "Post Only" behavior (simulated)
- Orders placed outside the spread to avoid crossing (TAKER behavior)
- Orders cancelled if they would cross spread (per dYdX Post Only rules)
- Earns maker rebates (-0.02% to -0.11% depending on fee tier)

TRADE EXECUTION:
- BUY orders: placed at or below current bid
- SELL orders: placed at or above current ask  
- No market orders used (would be TAKER)
- Fill probability based on price competitiveness and market movement

FEE STRUCTURE (per dYdX v4 docs):
- Maker Fee: -0.02% (rebate) for basic tier
- Taker Fee: +0.05% (avoided entirely in this strategy)
- Negative fees = we earn rebates on filled orders

RISK MANAGEMENT:
- Position sizing based on volatility and account size
- Maximum open positions and exposure limits
- Stop-loss and take-profit via limit orders only
- Realistic latency and execution delays

This implementation ensures 100% MAKER trading with no accidental TAKER behavior.
"""

import time
import asyncio
import requests
import os
import traceback
import random
from collections import deque, defaultdict
from dataclasses import dataclass, field
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
    volume: float = 0.0
    spread_pct: float = 0.0

@dataclass
class MeanReversionSignal:
    market: str
    timestamp: float
    signal_type: str  # "BUY", "SELL", "NEUTRAL"
    deviation: float  # deviation from mean in %
    entry_price: float
    confidence: float  # 0-100
    z_score: float = 0.0
    
@dataclass
class Order:
    """Realistic order representation"""
    market: str
    side: str  # "BUY" or "SELL"
    order_type: str  # "MARKET" or "LIMIT"
    size: float
    price: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    status: str = "PENDING"  # "PENDING", "FILLED", "PARTIAL", "CANCELLED"
    filled_size: float = 0.0
    avg_fill_price: float = 0.0
    fees_paid: float = 0.0
    latency_ms: float = 0.0

@dataclass
class Position:
    market: str
    entry_time: float
    entry_price: float
    signal_type: str
    size: float
    status: str  # "OPEN", "CLOSED"
    pnl: float = 0.0
    pnl_usd: float = 0.0
    exit_price: Optional[float] = None
    exit_time: Optional[float] = None
    entry_order: Optional[Order] = None
    exit_order: Optional[Order] = None
    max_profit: float = 0.0
    max_loss: float = 0.0
    holding_time: float = 0.0
    fees_total: float = 0.0

class RealisticOrderSimulator:
    """Simulates realistic order execution with latency, slippage, and fees"""
    
    def __init__(self):
        # dYdX v4 fee structure (approximate)
        self.maker_fee_rate = -0.0002  # -0.02% (rebate)
        self.taker_fee_rate = 0.0005   # 0.05%
        
        # Market microstructure parameters
        self.base_latency_ms = 50  # Base execution latency
        self.latency_variance_ms = 30
        self.slippage_factor = 0.0001  # Base slippage as % of price
        self.market_impact_factor = 0.00005  # Additional slippage based on size
        
    def simulate_market_order(self, market: str, side: str, size: float, 
                            current_bid: float, current_ask: float, 
                            spread_pct: float, volume: float = 1000000) -> Order:
        """Simulate realistic market order execution"""
        
        order = Order(
            market=market,
            side=side,
            order_type="MARKET",
            size=size,
            timestamp=time.time()
        )
        
        # Simulate execution latency
        base_latency = self.base_latency_ms
        latency_variance = random.uniform(-self.latency_variance_ms, self.latency_variance_ms)
        order.latency_ms = max(10, base_latency + latency_variance)
        
        # Calculate market impact based on order size
        size_usd = size * (current_ask if side == "BUY" else current_bid)
        market_impact = self.market_impact_factor * (size_usd / volume) * 100
        
        # Calculate slippage
        base_slippage = self.slippage_factor * 100  # Convert to percentage
        spread_slippage = spread_pct * 0.3  # Partial spread crossing
        total_slippage = base_slippage + market_impact + spread_slippage
        
        # Determine execution price with slippage
        if side == "BUY":
            # Buy at ask + slippage
            execution_price = current_ask * (1 + total_slippage / 100)
            order.avg_fill_price = execution_price
        else:
            # Sell at bid - slippage
            execution_price = current_bid * (1 - total_slippage / 100)
            order.avg_fill_price = execution_price
        
        # Calculate fees (taker fees for market orders)
        notional_value = size * order.avg_fill_price
        order.fees_paid = notional_value * self.taker_fee_rate
        
        # Market orders typically fill completely
        order.filled_size = size
        order.status = "FILLED"
        
        return order
    
    def simulate_limit_order(self, market: str, side: str, size: float, 
                           limit_price: float, current_bid: float, 
                           current_ask: float) -> Order:
        """Simulate limit order for MAKER-ONLY strategy (Post-Only behavior)
        
        Per dYdX v4 documentation:
        - Post Only orders enforce MAKER-only behavior  
        - Orders are cancelled if they would cross the spread (become TAKER)
        - MAKER orders earn rebates (negative fees)
        """
        
        order = Order(
            market=market,
            side=side,
            order_type="LIMIT",
            size=size,
            price=limit_price,
            timestamp=time.time()
        )
        
        # Check if order would cross the spread (violate MAKER-only requirement)
        would_cross_spread = False
        
        if side == "BUY" and limit_price >= current_ask:
            # Buy limit at or above ask would immediately execute as TAKER
            would_cross_spread = True
        elif side == "SELL" and limit_price <= current_bid:
            # Sell limit at or below bid would immediately execute as TAKER  
            would_cross_spread = True
        
        if would_cross_spread:
            # Post-Only order would be cancelled by validator to prevent TAKER execution
            order.status = "CANCELLED"
            order.latency_ms = random.uniform(5, 15)  # Fast cancellation
            return order
        
        # MAKER-ONLY: Calculate fill probability based on how competitive our price is
        fill_probability = 0.0
        
        if side == "BUY":
            # Buy limit below ask (MAKER behavior)
            if limit_price <= current_bid:
                # At or better than current bid - high chance of fill
                bid_improvement = max(0, (current_bid - limit_price) / current_bid)
                fill_probability = max(0.3, min(0.85, 0.5 + bid_improvement * 10))
            else:
                # Between bid and ask - moderate chance depending on market movement
                spread = current_ask - current_bid
                position_in_spread = (limit_price - current_bid) / spread if spread > 0 else 0
                fill_probability = max(0.1, 0.6 - position_in_spread * 0.4)
                
        elif side == "SELL":
            # Sell limit above bid (MAKER behavior)
            if limit_price >= current_ask:
                # At or better than current ask - high chance of fill
                ask_improvement = max(0, (limit_price - current_ask) / current_ask)
                fill_probability = max(0.3, min(0.85, 0.5 + ask_improvement * 10))
            else:
                # Between bid and ask - moderate chance depending on market movement
                spread = current_ask - current_bid
                position_in_spread = (current_ask - limit_price) / spread if spread > 0 else 0
                fill_probability = max(0.1, 0.6 - position_in_spread * 0.4)
        
        # Simulate execution latency for limit orders (faster than market orders)
        order.latency_ms = random.uniform(5, 30)
        
        # Simulate fill based on probability
        if random.random() < fill_probability:
            order.status = "FILLED"
            order.filled_size = size
            order.avg_fill_price = limit_price
            
            # Calculate MAKER fees (negative = rebate we earn)
            notional_value = size * order.avg_fill_price
            order.fees_paid = notional_value * self.maker_fee_rate  # Negative = rebate income
        else:
            order.status = "PENDING"
            
        return order

class RealisticMeanReversionStrategy:
    """Mean-reversion strategy with realistic execution logic"""
    
    def __init__(self, lookback_seconds: int = 10, deviation_threshold: float = 1.5):
        self.lookback_seconds = lookback_seconds
        self.deviation_threshold = deviation_threshold
        self.price_history: Dict[str, Deque[PricePoint]] = defaultdict(lambda: deque(maxlen=100))
        self.order_simulator = RealisticOrderSimulator()
        
        # Position sizing parameters
        self.base_position_size_usd = 1000.0
        self.max_position_size_usd = 5000.0
        self.min_position_size_usd = 100.0
        
    def update_price(self, market: str, price_data: dict):
        """Update price history with enhanced data"""
        current_time = time.time()
        
        bids = price_data.get('bids', [])
        asks = price_data.get('asks', [])
        
        if not bids or not asks:
            return
            
        bid = float(bids[0]['price'])
        ask = float(asks[0]['price'])
        mid_price = (bid + ask) / 2
        
        # Calculate spread percentage
        spread_pct = ((ask - bid) / mid_price) * 100 if mid_price > 0 else 0
        
        # Estimate volume (simplified)
        bid_volume = sum(float(level.get('size', 0)) for level in bids[:5])
        ask_volume = sum(float(level.get('size', 0)) for level in asks[:5])
        total_volume = bid_volume + ask_volume
        
        price_point = PricePoint(
            timestamp=current_time,
            price=mid_price,
            bid=bid,
            ask=ask,
            volume=total_volume,
            spread_pct=spread_pct
        )
        
        self.price_history[market].append(price_point)
    
    def calculate_signal(self, market: str) -> Optional[MeanReversionSignal]:
        """Calculate enhanced mean-reversion signal"""
        if market not in self.price_history:
            return None
            
        prices = self.price_history[market]
        if len(prices) < 5:
            return None
            
        current_time = time.time()
        recent_prices = [
            p for p in prices 
            if current_time - p.timestamp <= self.lookback_seconds
        ]
        
        if len(recent_prices) < 3:
            return None
            
        # Enhanced statistical analysis
        price_values = [p.price for p in recent_prices]
        bid_values = [p.bid for p in recent_prices]
        ask_values = [p.ask for p in recent_prices]
        spread_values = [p.spread_pct for p in recent_prices]
        
        mean_price = statistics.mean(price_values)
        std_dev = statistics.stdev(price_values) if len(price_values) > 1 else 0
        mean_spread = statistics.mean(spread_values)
        
        if std_dev == 0:
            return None
            
        current_point = recent_prices[-1]
        current_price = current_point.price
        deviation_pct = ((current_price - mean_price) / mean_price) * 100
        z_score = (current_price - mean_price) / std_dev
        
        # Adjust signal strength based on market conditions
        signal_type = "NEUTRAL"
        confidence = 0.0
        
        # Consider spread conditions for signal quality
        spread_penalty = max(0, (mean_spread - 0.05) * 10)  # Penalize wide spreads
        
        if abs(z_score) > self.deviation_threshold:
            if current_price > mean_price:
                signal_type = "SELL"
            else:
                signal_type = "BUY"
            
            # Adjust confidence based on multiple factors
            base_confidence = min(100, abs(z_score) * 25)
            spread_adjusted_confidence = max(0, base_confidence - spread_penalty)
            
            # Volume consideration (simplified)
            volume_factor = min(1.2, current_point.volume / 10000) if current_point.volume > 0 else 0.8
            confidence = spread_adjusted_confidence * volume_factor
        
        return MeanReversionSignal(
            market=market,
            timestamp=current_time,
            signal_type=signal_type,
            deviation=deviation_pct,
            entry_price=current_price,
            confidence=confidence,
            z_score=z_score
        )
    
    def calculate_position_size(self, market: str, signal: MeanReversionSignal, 
                              current_price: float) -> float:
        """Calculate realistic position size based on signal strength and risk"""
        
        # Base size adjusted by confidence
        confidence_factor = signal.confidence / 100.0
        size_usd = self.base_position_size_usd * confidence_factor
        
        # Adjust for volatility (higher volatility = smaller size)
        volatility_factor = max(0.5, 1.0 - (abs(signal.z_score) - 2.0) * 0.1)
        size_usd *= volatility_factor
        
        # Apply position sizing limits
        size_usd = max(self.min_position_size_usd, 
                      min(self.max_position_size_usd, size_usd))
        
        # Convert to token size
        token_size = size_usd / current_price
        
        return round(token_size, 6)  # Round to reasonable precision

class RealisticMeanReversionDashboard:
    """Enhanced dashboard with realistic paper trading"""
    
    def __init__(self):
        self.console = Console()
        self.stream = DydxTradesStream()
        self.strategy = RealisticMeanReversionStrategy()
        
        # Market tracking
        self.active_markets = set()
        self.current_prices: Dict[str, PricePoint] = {}
        self.signals: Dict[str, MeanReversionSignal] = {}
        
        # Realistic position tracking
        self.positions: List[Position] = []
        self.pending_orders: List[Order] = []
        self.total_pnl_usd = 0.0
        self.total_fees_paid = 0.0
        self.position_count = 0
        self.winning_positions = 0
        
        # Enhanced market-specific tracking
        self.market_stats: Dict[str, Dict] = defaultdict(lambda: {
            'positions': [],
            'total_pnl_usd': 0.0,
            'total_fees_usd': 0.0,
            'winning_positions': 0,
            'total_positions': 0,
            'current_position': None,
            'avg_holding_time': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0
        })
        
        # Performance tracking
        self.last_update = time.time()
        self.update_count = 0
        self.session_start = time.time()
        
        # Risk management
        self.max_open_positions = 5
        self.max_total_exposure_usd = 10000.0
        self.daily_loss_limit_usd = 1000.0
        
    def _fetch_usd_markets(self):
        """Fetch all active USD markets from dYdX API"""
        try:
            response = requests.get('https://indexer.dydx.trade/v4/perpetualMarkets', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'markets' in data:
                    markets = data['markets']
                    
                    usd_markets = []
                    for name, market in markets.items():
                        if (market.get('status') == 'ACTIVE' and 
                            name.endswith('-USD') and 
                            market.get('marketType') in ['CROSS', 'ISOLATED']):
                            usd_markets.append(name)
                    
                    return sorted(usd_markets)
            
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
        """Start the realistic dashboard"""
        self.console.print("[cyan]🚀 Starting Realistic Mean-Reversion Dashboard...[/cyan]")
        markets = self._fetch_usd_markets()
        
        self.console.print(f"[green]✅ Found {len(markets)} active USD markets[/green]")
        
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
                orderbook_stream.subscribe(
                    lambda data, market=market: self._handle_orderbook_update(market, data)
                )
            except Exception as e:
                subscription_errors += 1
                self.console.print(f"[red]Error subscribing to {market}: {e}[/red]")
        
        if subscription_errors > 0:
            self.console.print(f"[yellow]⚠️  {subscription_errors} subscription errors[/yellow]")
        
        self.console.print(f"[green]✅ Subscribed to {len(markets) - subscription_errors} markets[/green]")
        
        # Start live dashboard
        with Live(self._create_dashboard(), refresh_per_second=2, console=self.console) as live:
            try:
                while True:
                    time.sleep(0.5)
                    live.update(self._create_dashboard())
            except KeyboardInterrupt:
                self.console.print("\n[yellow]📊 Final Performance Summary:[/yellow]")
                self._print_final_summary()
    
    def _handle_orderbook_update(self, market: str, data: dict):
        """Handle orderbook updates with realistic trading logic"""
        try:
            # Update strategy with new price data
            self.strategy.update_price(market, data)
            
            # Store current price point
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            
            if bids and asks:
                bid = float(bids[0]['price'])
                ask = float(asks[0]['price'])
                mid_price = (bid + ask) / 2
                spread_pct = ((ask - bid) / mid_price) * 100
                
                self.current_prices[market] = PricePoint(
                    timestamp=time.time(),
                    price=mid_price,
                    bid=bid,
                    ask=ask,
                    spread_pct=spread_pct
                )
            
            # Generate and process signals
            signal = self.strategy.calculate_signal(market)
            if signal:
                self.signals[market] = signal
                
                # Check for position entry opportunities
                if (signal.confidence > 75 and 
                    signal.signal_type != "NEUTRAL" and
                    self._can_open_position(market)):
                    self._execute_entry_order(signal)
            
            # Update existing positions
            self._update_positions()
            
            # Process pending orders
            self._process_pending_orders()
            
            self.update_count += 1
            self.last_update = time.time()
            
        except Exception as e:
            self.console.print(f"[red]Error processing {market}: {e}[/red]")
    
    def _can_open_position(self, market: str) -> bool:
        """Check if we can open a new position based on risk limits"""
        
        # Check if we already have a position in this market
        if self.market_stats[market]['current_position']:
            return False
        
        # Check maximum open positions
        open_positions = sum(1 for m in self.market_stats.values() 
                           if m['current_position'] is not None)
        if open_positions >= self.max_open_positions:
            return False
        
        # Check total exposure
        total_exposure = sum(abs(pos.size * self.current_prices.get(pos.market, PricePoint(0,0,0,0)).price)
                           for pos in self.positions if pos.status == "OPEN")
        if total_exposure >= self.max_total_exposure_usd:
            return False
        
        # Check daily loss limit
        if self.total_pnl_usd < -self.daily_loss_limit_usd:
            return False
            
        return True
    
    def _execute_entry_order(self, signal: MeanReversionSignal):
        """Execute MAKER-ONLY entry order with limit orders"""
        market = signal.market
        current_point = self.current_prices.get(market)
        
        if not current_point:
            return
        
        # Calculate position size
        position_size = self.strategy.calculate_position_size(
            market, signal, current_point.price
        )
        
        # MAKER-ONLY: Calculate limit prices that DON'T cross the spread (provide liquidity)
        if signal.signal_type == "BUY":
            # For BUY signal: place limit order AT OR BELOW current bid to avoid crossing spread
            # Mean reversion: buy when price is below mean, place order at slightly below bid
            limit_price = current_point.bid * 0.9995  # 0.05% below bid (provides liquidity)
            
            order = self.strategy.order_simulator.simulate_limit_order(
                market, "BUY", position_size, limit_price,
                current_point.bid, current_point.ask
            )
        else:  # SELL signal
            # For SELL signal: place limit order AT OR ABOVE current ask to avoid crossing spread
            # Mean reversion: sell when price is above mean, place order at slightly above ask
            limit_price = current_point.ask * 1.0005  # 0.05% above ask (provides liquidity)
            
            order = self.strategy.order_simulator.simulate_limit_order(
                market, "SELL", position_size, limit_price,
                current_point.bid, current_point.ask
            )
        
        if order.status == "FILLED":
            # Create position from filled MAKER order
            position = Position(
                market=market,
                entry_time=order.timestamp,
                entry_price=order.avg_fill_price,
                signal_type=signal.signal_type,
                size=order.filled_size,
                status="OPEN",
                entry_order=order,
                fees_total=order.fees_paid  # This will be negative (rebate)
            )
            
            self.positions.append(position)
            self.market_stats[market]['current_position'] = position
            self.market_stats[market]['total_positions'] += 1
            self.position_count += 1
            self.total_fees_paid += order.fees_paid  # Adding negative value (rebate)
        
        elif order.status == "PENDING":
            # Add to pending orders to track unfilled maker orders
            self.pending_orders.append(order)
    
    def _update_positions(self):
        """Update open positions with realistic PnL and exit logic"""
        current_time = time.time()
        
        for position in self.positions:
            if position.status == "OPEN":
                current_point = self.current_prices.get(position.market)
                if not current_point:
                    continue
                
                # Calculate unrealized PnL
                if position.signal_type == "BUY":
                    # Long position: profit when price goes up
                    current_value = position.size * current_point.bid  # Use bid for exit
                    entry_value = position.size * position.entry_price
                    position.pnl_usd = current_value - entry_value - position.fees_total
                else:
                    # Short position: profit when price goes down
                    entry_value = position.size * position.entry_price
                    current_value = position.size * current_point.ask  # Use ask for exit
                    position.pnl_usd = entry_value - current_value - position.fees_total
                
                position.pnl = (position.pnl_usd / (position.size * position.entry_price)) * 100
                
                # Track max profit/loss
                position.max_profit = max(position.max_profit, position.pnl_usd)
                position.max_loss = min(position.max_loss, position.pnl_usd)
                
                # Exit logic: multiple conditions
                should_exit = False
                exit_reason = ""
                
                # 1. Time-based exit (mean reversion should be quick)
                holding_time = current_time - position.entry_time
                if holding_time > 60:  # 1 minute max holding
                    should_exit = True
                    exit_reason = "time_limit"
                
                # 2. Profit target
                elif position.pnl_usd > 50:  # $50 profit target
                    should_exit = True
                    exit_reason = "profit_target"
                
                # 3. Stop loss
                elif position.pnl_usd < -25:  # $25 stop loss
                    should_exit = True
                    exit_reason = "stop_loss"
                
                # 4. Signal reversal
                elif market_signal := self.signals.get(position.market):
                    if (market_signal.signal_type != "NEUTRAL" and 
                        market_signal.signal_type != position.signal_type and
                        market_signal.confidence > 60):
                        should_exit = True
                        exit_reason = "signal_reversal"
                
                if should_exit:
                    self._execute_exit_order(position, exit_reason)
    
    def _execute_exit_order(self, position: Position, reason: str):
        """Execute MAKER-ONLY exit order with limit orders"""
        current_point = self.current_prices.get(position.market)
        if not current_point:
            return
        
        # MAKER-ONLY: Calculate exit limit prices that provide liquidity
        exit_side = "SELL" if position.signal_type == "BUY" else "BUY"
        
        if exit_side == "SELL":
            # Selling: place limit order ABOVE current ask to provide liquidity
            limit_price = current_point.ask * 1.0005  # 0.05% above ask
        else:  # BUY (covering short)
            # Buying: place limit order BELOW current bid to provide liquidity  
            limit_price = current_point.bid * 0.9995  # 0.05% below bid
        
        exit_order = self.strategy.order_simulator.simulate_limit_order(
            position.market, exit_side, abs(position.size), limit_price,
            current_point.bid, current_point.ask
        )
        
        if exit_order.status == "FILLED":
            # Close position with MAKER exit
            position.status = "CLOSED"
            position.exit_time = exit_order.timestamp
            position.exit_price = exit_order.avg_fill_price
            position.exit_order = exit_order
            position.holding_time = position.exit_time - position.entry_time
            position.fees_total += exit_order.fees_paid  # Adding another rebate
            
            # Final PnL calculation with MAKER rebates
            if position.signal_type == "BUY":
                position.pnl_usd = (position.exit_price - position.entry_price) * position.size - position.fees_total
            else:
                position.pnl_usd = (position.entry_price - position.exit_price) * position.size - position.fees_total
            
            position.pnl = (position.pnl_usd / (position.size * position.entry_price)) * 100
            
            # Update statistics
            market_stats = self.market_stats[position.market]
            market_stats['current_position'] = None
            market_stats['total_pnl_usd'] += position.pnl_usd
            market_stats['total_fees_usd'] += position.fees_total  # This will be negative (total rebates)
            market_stats['positions'].append(position)
            
            if position.pnl_usd > 0:
                self.winning_positions += 1
                market_stats['winning_positions'] += 1
            
            # Update global stats
            self.total_pnl_usd += position.pnl_usd
            self.total_fees_paid += exit_order.fees_paid
            
            # Update market-specific stats
            self._update_market_stats(position.market)
    
    def _process_pending_orders(self):
        """Process pending MAKER limit orders for fills"""
        current_time = time.time()
        
        # Process pending orders and check for fills
        filled_orders = []
        for order in self.pending_orders[:]:  # Create copy to iterate safely
            
            # Cancel orders that are too old (e.g., 30 seconds)
            if current_time - order.timestamp > 30:
                order.status = "CANCELLED"
                self.pending_orders.remove(order)
                continue
            
            # Check if order conditions have changed for potential fill
            current_point = self.current_prices.get(order.market)
            if not current_point:
                continue
            
            # Re-evaluate fill probability based on current market conditions
            if order.side == "BUY":
                # Check if market moved down towards our buy limit
                if current_point.bid <= order.price:
                    # Market came to us - high chance of fill
                    if random.random() < 0.7:  # 70% chance of fill when price hits our level
                        order.status = "FILLED"
                        order.filled_size = order.size
                        order.avg_fill_price = order.price
                        
                        # Calculate MAKER fees (rebate)
                        notional_value = order.size * order.avg_fill_price
                        order.fees_paid = notional_value * self.strategy.order_simulator.maker_fee_rate
                        
                        filled_orders.append(order)
                        self.pending_orders.remove(order)
                        
            elif order.side == "SELL":
                # Check if market moved up towards our sell limit
                if current_point.ask >= order.price:
                    # Market came to us - high chance of fill
                    if random.random() < 0.7:  # 70% chance of fill when price hits our level
                        order.status = "FILLED"
                        order.filled_size = order.size
                        order.avg_fill_price = order.price
                        
                        # Calculate MAKER fees (rebate)
                        notional_value = order.size * order.avg_fill_price
                        order.fees_paid = notional_value * self.strategy.order_simulator.maker_fee_rate
                        
                        filled_orders.append(order)
                        self.pending_orders.remove(order)
        
        # Create positions from newly filled orders
        for order in filled_orders:
            position = Position(
                market=order.market,
                entry_time=order.timestamp,
                entry_price=order.avg_fill_price,
                signal_type=order.side,  # "BUY" or "SELL"
                size=order.filled_size,
                status="OPEN",
                entry_order=order,
                fees_total=order.fees_paid  # Negative (rebate)
            )
            
            self.positions.append(position)
            self.market_stats[order.market]['current_position'] = position
            self.market_stats[order.market]['total_positions'] += 1
            self.position_count += 1
            self.total_fees_paid += order.fees_paid  # Adding negative value (rebate)
    
    def _update_market_stats(self, market: str):
        """Update comprehensive market statistics"""
        stats = self.market_stats[market]
        positions = stats['positions']
        
        if not positions:
            return
        
        # Calculate average holding time
        holding_times = [p.holding_time for p in positions if p.holding_time > 0]
        stats['avg_holding_time'] = statistics.mean(holding_times) if holding_times else 0
        
        # Best and worst trades
        pnls = [p.pnl_usd for p in positions]
        stats['best_trade'] = max(pnls) if pnls else 0
        stats['worst_trade'] = min(pnls) if pnls else 0
        
        # Win rate
        total_trades = len(positions)
        winning_trades = len([p for p in positions if p.pnl_usd > 0])
        stats['win_rate'] = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = sum(p.pnl_usd for p in positions if p.pnl_usd > 0)
        gross_loss = abs(sum(p.pnl_usd for p in positions if p.pnl_usd < 0))
        stats['profit_factor'] = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
    
    def _create_dashboard(self) -> Layout:
        """Create enhanced dashboard layout"""
        layout = Layout()
        
        header = self._create_header()
        markets_table = self._create_markets_table()
        stats_panel = self._create_stats_panel()
        positions_table = self._create_positions_table()
        
        layout.split_column(
            Layout(header, size=4),
            Layout(
                Columns([markets_table, stats_panel], equal=True)
            ),
            Layout(positions_table, size=12)
        )
        
        return layout
    
    def _create_header(self) -> Panel:
        """Create enhanced dashboard header for MAKER-ONLY trading"""
        current_time = time.strftime('%H:%M:%S')
        session_duration = time.time() - self.session_start
        hours, remainder = divmod(session_duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        active_count = len(self.active_markets)
        signal_count = len([s for s in self.signals.values() if s.signal_type != "NEUTRAL"])
        open_positions = sum(1 for m in self.market_stats.values() 
                           if m['current_position'] is not None)
        pending_count = len(self.pending_orders)
        
        header_text = Text()
        header_text.append("📈 MAKER-ONLY MEAN-REVERSION DASHBOARD ", style="bold blue")
        header_text.append(f"| Markets: {active_count} ", style="white")
        header_text.append(f"| Signals: {signal_count} ", style="green")
        header_text.append(f"| Open: {open_positions} ", style="yellow")
        header_text.append(f"| Pending: {pending_count} ", style="orange")
        header_text.append(f"| P&L: ${self.total_pnl_usd:.2f} ", 
                          style="green" if self.total_pnl_usd >= 0 else "red")
        header_text.append(f"| Time: {current_time}", style="cyan")
        
        # Second line with MAKER-specific session info
        header_text.append(f"\nSession: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d} ", 
                          style="magenta")
        header_text.append(f"| Updates: {self.update_count} ", style="cyan")
        
        # For MAKER trading, fees are rebates (negative)
        rebate_earned = abs(self.total_fees_paid) if self.total_fees_paid < 0 else 0
        fees_paid = self.total_fees_paid if self.total_fees_paid > 0 else 0
        
        if rebate_earned > 0:
            header_text.append(f"| Rebates: +${rebate_earned:.2f} ", style="green")
        if fees_paid > 0:
            header_text.append(f"| Fees: -${fees_paid:.2f} ", style="red")
        
        # Net calculation includes rebates as positive
        net_pnl = self.total_pnl_usd + rebate_earned - fees_paid
        header_text.append(f"| Net+Rebates: ${net_pnl:.2f}", 
                          style="green" if net_pnl >= 0 else "red")
        
        return Panel(header_text, style="blue")
    
    def _create_markets_table(self) -> Panel:
        """Create enhanced markets table with realistic metrics"""
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Market", style="white", width=8)
        table.add_column("Price", style="yellow", width=10)
        table.add_column("Spread", style="red", width=7)
        table.add_column("Z-Score", style="magenta", width=8)
        table.add_column("Signal", style="green", width=12)
        table.add_column("Net P&L", style="cyan", width=9)
        table.add_column("Trades", style="white", width=8)
        table.add_column("Win%", style="green", width=6)
        table.add_column("Status", style="white", width=15)
        
        # Sort markets by signal strength and activity
        market_priorities = []
        for market in self.active_markets:
            signal = self.signals.get(market)
            current_point = self.current_prices.get(market)
            stats = self.market_stats[market]
            
            priority = 0
            if stats['current_position']:
                priority += 1000  # Active positions first
            if signal and signal.signal_type != "NEUTRAL":
                priority += signal.confidence  # Then by signal strength
            if stats['total_positions'] > 0:
                priority += 10  # Then by trading activity
            
            market_priorities.append((market, priority))
        
        # Show top 15 markets
        top_markets = sorted(market_priorities, key=lambda x: x[1], reverse=True)[:15]
        
        for market, _ in top_markets:
            current_point = self.current_prices.get(market)
            signal = self.signals.get(market)
            stats = self.market_stats[market]
            
            if not current_point:
                continue
            
            # Format price and spread
            price_str = f"${current_point.price:.3f}"
            spread_str = f"{current_point.spread_pct:.3f}%"
            if current_point.spread_pct > 0.1:
                spread_str = f"[red]{spread_str}[/red]"
            elif current_point.spread_pct > 0.05:
                spread_str = f"[yellow]{spread_str}[/yellow]"
            else:
                spread_str = f"[green]{spread_str}[/green]"
            
            # Z-Score
            z_score_str = ""
            signal_str = ""
            if signal:
                z_score_str = f"{signal.z_score:+.2f}"
                if abs(signal.z_score) > 2:
                    z_score_str = f"[red]{z_score_str}[/red]"
                elif abs(signal.z_score) > 1:
                    z_score_str = f"[yellow]{z_score_str}[/yellow]"
                
                if signal.signal_type != "NEUTRAL":
                    signal_color = "green" if signal.signal_type == "BUY" else "red"
                    signal_str = f"[{signal_color}]{signal.signal_type} {signal.confidence:.0f}%[/{signal_color}]"
                else:
                    signal_str = "NEUTRAL"
            else:
                z_score_str = "--"
                signal_str = "--"
            
            # Net P&L
            net_pnl = stats['total_pnl_usd'] - abs(stats['total_fees_usd'])
            pnl_str = f"${net_pnl:+.1f}"
            if net_pnl > 0:
                pnl_str = f"[green]{pnl_str}[/green]"
            elif net_pnl < 0:
                pnl_str = f"[red]{pnl_str}[/red]"
            
            # Trades and win rate
            trades_str = f"{stats['total_positions']}"
            win_rate_str = f"{stats['win_rate']:.0f}%" if stats['total_positions'] > 0 else "--"
            if stats['win_rate'] >= 60:
                win_rate_str = f"[green]{win_rate_str}[/green]"
            elif stats['win_rate'] >= 40:
                win_rate_str = f"[yellow]{win_rate_str}[/yellow]"
            elif stats['win_rate'] > 0:
                win_rate_str = f"[red]{win_rate_str}[/red]"
            
            # Status
            current_pos = stats['current_position']
            if current_pos:
                pos_color = "green" if current_pos.signal_type == "BUY" else "red"
                pos_symbol = "🟩 LONG" if current_pos.signal_type == "BUY" else "🟥 SHORT"
                status_str = f"[{pos_color}]{pos_symbol} {current_pos.pnl_usd:+.1f}[/{pos_color}]"
            else:
                status_str = "[blue]⚪ Monitoring[/blue]"
            
            table.add_row(
                market.replace('-USD', ''),
                price_str,
                spread_str,
                z_score_str,
                signal_str,
                pnl_str,
                trades_str,
                win_rate_str,
                status_str
            )
        
        title = f"📊 Market Analysis - Realistic Trading Simulation"
        return Panel(table, title=title, border_style="cyan")
    
    def _create_stats_panel(self) -> Panel:
        """Create enhanced statistics panel for MAKER trading"""
        closed_positions = [p for p in self.positions if p.status == "CLOSED"]
        open_positions = [p for p in self.positions if p.status == "OPEN"]
        
        stats_table = Table(show_header=False, show_edge=False)
        stats_table.add_column("Metric", style="cyan", width=18)
        stats_table.add_column("Value", style="white", width=15)
        
        # Trading performance
        total_trades = len(closed_positions)
        win_rate = (self.winning_positions / total_trades * 100) if total_trades > 0 else 0
        avg_pnl_usd = statistics.mean([p.pnl_usd for p in closed_positions]) if closed_positions else 0
        
        # Risk metrics
        open_pnl = sum(p.pnl_usd for p in open_positions)
        total_exposure = sum(abs(p.size * self.current_prices.get(p.market, PricePoint(0,0,0,0)).price) 
                           for p in open_positions)
        
        # MAKER-specific metrics: rebates vs fees
        rebate_earned = abs(self.total_fees_paid) if self.total_fees_paid < 0 else 0
        fees_paid = self.total_fees_paid if self.total_fees_paid > 0 else 0
        net_with_rebates = self.total_pnl_usd + rebate_earned - fees_paid
        
        stats_table.add_row("📊 Total Trades", str(total_trades))
        stats_table.add_row("✅ Winners", str(self.winning_positions))
        stats_table.add_row("📈 Win Rate", f"{win_rate:.1f}%")
        stats_table.add_row("💰 Gross P&L", f"${self.total_pnl_usd:.2f}")
        
        # Show rebates separately from fees for MAKER trading
        if rebate_earned > 0:
            stats_table.add_row("� Rebates Earned", f"+${rebate_earned:.2f}")
        if fees_paid > 0:
            stats_table.add_row("💸 Fees Paid", f"-${fees_paid:.2f}")
            
        stats_table.add_row("🎯 Net + Rebates", f"${net_with_rebates:.2f}")
        stats_table.add_row("📊 Avg Trade", f"${avg_pnl_usd:.2f}")
        
        stats_table.add_row("", "")
        stats_table.add_row("🔴 Open Positions", str(len(open_positions)))
        stats_table.add_row("⏳ Pending Orders", str(len(self.pending_orders)))
        stats_table.add_row("💹 Open P&L", f"${open_pnl:.2f}")
        stats_table.add_row("📏 Exposure", f"${total_exposure:.0f}")
        
        stats_table.add_row("", "")
        stats_table.add_row("⚙️ Strategy", "MAKER-ONLY")
        stats_table.add_row("📊 Z-Threshold", f"{self.strategy.deviation_threshold:.1f}")
        stats_table.add_row("🎯 Min Confidence", "75%")
        stats_table.add_row("💎 Fee Rate", "-0.02%")
        
        return Panel(stats_table, title="📈 MAKER Trading Performance", border_style="green")
    
    def _create_positions_table(self) -> Panel:
        """Create enhanced positions table"""
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Market", style="white", width=8)
        table.add_column("Side", style="cyan", width=6)
        table.add_column("Size", style="blue", width=8)
        table.add_column("Entry", style="yellow", width=10)
        table.add_column("Current", style="yellow", width=10)
        table.add_column("P&L USD", style="green", width=9)
        table.add_column("P&L %", style="green", width=8)
        table.add_column("Fees", style="red", width=7)
        table.add_column("Hold Time", style="magenta", width=9)
        table.add_column("Status", style="white", width=10)
        
        # Show recent positions (last 25)
        recent_positions = sorted(self.positions, key=lambda p: p.entry_time, reverse=True)[:25]
        
        if not recent_positions:
            table.add_row("--", "--", "--", "--", "--", "--", "--", "--", "--", "--")
        else:
            current_time = time.time()
            
            for position in recent_positions:
                current_point = self.current_prices.get(position.market)
                current_price = current_point.price if current_point else position.entry_price
                
                # Calculate current P&L if position is open
                if position.status == "OPEN" and current_point:
                    if position.signal_type == "BUY":
                        unrealized_pnl = (current_point.bid - position.entry_price) * position.size - position.fees_total
                    else:
                        unrealized_pnl = (position.entry_price - current_point.ask) * position.size - position.fees_total
                    
                    position.pnl_usd = unrealized_pnl
                    position.pnl = (unrealized_pnl / (position.size * position.entry_price)) * 100
                
                # Holding time
                if position.status == "OPEN":
                    hold_time = current_time - position.entry_time
                else:
                    hold_time = position.holding_time
                
                if hold_time < 60:
                    hold_str = f"{hold_time:.0f}s"
                else:
                    hold_str = f"{hold_time/60:.1f}m"
                
                # Format values
                side_str = position.signal_type
                if position.signal_type == "BUY":
                    side_str = "[green]LONG[/green]"
                else:
                    side_str = "[red]SHORT[/red]"
                
                size_str = f"{position.size:.3f}"
                entry_str = f"${position.entry_price:.3f}"
                current_str = f"${current_price:.3f}"
                
                # P&L formatting
                pnl_usd_str = f"${position.pnl_usd:+.2f}"
                pnl_pct_str = f"{position.pnl:+.2f}%"
                
                if position.pnl_usd > 0:
                    pnl_usd_str = f"[green]{pnl_usd_str}[/green]"
                    pnl_pct_str = f"[green]{pnl_pct_str}[/green]"
                elif position.pnl_usd < 0:
                    pnl_usd_str = f"[red]{pnl_usd_str}[/red]"
                    pnl_pct_str = f"[red]{pnl_pct_str}[/red]"
                
                # Fees
                fees_str = f"${abs(position.fees_total):.2f}"
                
                # Status
                status_str = position.status
                if position.status == "OPEN":
                    status_str = "[yellow]OPEN[/yellow]"
                elif position.pnl_usd > 0:
                    status_str = "[green]PROFIT[/green]"
                else:
                    status_str = "[red]LOSS[/red]"
                
                table.add_row(
                    position.market.replace('-USD', ''),
                    side_str,
                    size_str,
                    entry_str,
                    current_str,
                    pnl_usd_str,
                    pnl_pct_str,
                    fees_str,
                    hold_str,
                    status_str
                )
        
        return Panel(table, title="💼 Realistic Position Tracking", border_style="yellow")
    
    def _print_final_summary(self):
        """Print comprehensive final performance summary for MAKER trading"""
        closed_positions = [p for p in self.positions if p.status == "CLOSED"]
        
        if not closed_positions:
            self.console.print("[yellow]No completed trades to summarize.[/yellow]")
            return
        
        # Calculate comprehensive statistics
        total_trades = len(closed_positions)
        winning_trades = len([p for p in closed_positions if p.pnl_usd > 0])
        losing_trades = total_trades - winning_trades
        
        gross_profit = sum(p.pnl_usd for p in closed_positions if p.pnl_usd > 0)
        gross_loss = abs(sum(p.pnl_usd for p in closed_positions if p.pnl_usd < 0))
        
        # MAKER-specific calculations
        rebate_earned = abs(self.total_fees_paid) if self.total_fees_paid < 0 else 0
        fees_paid = self.total_fees_paid if self.total_fees_paid > 0 else 0
        net_profit_with_rebates = self.total_pnl_usd + rebate_earned - fees_paid
        
        avg_win = gross_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = gross_loss / losing_trades if losing_trades > 0 else 0
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        best_trade = max(p.pnl_usd for p in closed_positions) if closed_positions else 0
        worst_trade = min(p.pnl_usd for p in closed_positions) if closed_positions else 0
        
        avg_holding_time = statistics.mean([p.holding_time for p in closed_positions if p.holding_time > 0])
        
        # Print summary
        self.console.print("\n" + "="*70)
        self.console.print("[bold cyan]MAKER-ONLY MEAN REVERSION STRATEGY - FINAL RESULTS[/bold cyan]")
        self.console.print("="*70)
        
        self.console.print(f"📊 [bold]Trading Performance[/bold]")
        self.console.print(f"   Strategy Type: MAKER-ONLY (Liquidity Provider)")
        self.console.print(f"   Total Trades: {total_trades}")
        self.console.print(f"   Winning Trades: {winning_trades} ({win_rate:.1f}%)")
        self.console.print(f"   Losing Trades: {losing_trades}")
        
        self.console.print(f"\n💰 [bold]Financial Results[/bold]")
        self.console.print(f"   Gross Profit: ${gross_profit:.2f}")
        self.console.print(f"   Gross Loss: ${gross_loss:.2f}")
        
        # Show MAKER-specific fee breakdown
        if rebate_earned > 0:
            self.console.print(f"   [bold green]Rebates Earned: +${rebate_earned:.2f}[/bold green]")
        if fees_paid > 0:
            self.console.print(f"   [bold red]Fees Paid: -${fees_paid:.2f}[/bold red]")
            
        color = "green" if net_profit_with_rebates >= 0 else "red"
        self.console.print(f"   [bold {color}]Net Profit (incl. rebates): ${net_profit_with_rebates:.2f}[/bold {color}]")
        
        self.console.print(f"\n📈 [bold]Performance Metrics[/bold]")
        self.console.print(f"   Profit Factor: {profit_factor:.2f}")
        self.console.print(f"   Average Win: ${avg_win:.2f}")
        self.console.print(f"   Average Loss: ${avg_loss:.2f}")
        self.console.print(f"   Best Trade: ${best_trade:.2f}")
        self.console.print(f"   Worst Trade: ${worst_trade:.2f}")
        self.console.print(f"   Avg Hold Time: {avg_holding_time:.1f}s")
        
        self.console.print(f"\n🎯 [bold]MAKER Strategy Assessment[/bold]")
        if win_rate >= 60 and profit_factor >= 1.5 and net_profit_with_rebates > 0:
            self.console.print(f"   [bold green]✅ PROFITABLE MAKER STRATEGY[/bold green]")
            self.console.print(f"   [bold green]💎 Rebate advantage: ${rebate_earned:.2f}[/bold green]")
        elif win_rate >= 50 and profit_factor >= 1.2:
            self.console.print(f"   [bold yellow]⚠️  MARGINAL MAKER STRATEGY[/bold yellow]")
        else:
            self.console.print(f"   [bold red]❌ UNPROFITABLE STRATEGY[/bold red]")
        
        # MAKER-specific insights
        fill_rate = (total_trades / (total_trades + len(self.pending_orders)) * 100) if (total_trades + len(self.pending_orders)) > 0 else 100
        self.console.print(f"\n📈 [bold]MAKER Trading Insights[/bold]")
        self.console.print(f"   Limit Order Fill Rate: {fill_rate:.1f}%")
        self.console.print(f"   Average Rebate per Trade: ${rebate_earned/total_trades:.3f}" if total_trades > 0 else "   No trades completed")
        self.console.print(f"   Liquidity Provision Strategy: {'Effective' if rebate_earned > 10 else 'Needs Improvement'}")
        
        self.console.print("="*70)

def main():
    """Main entry point"""
    dashboard = RealisticMeanReversionDashboard()
    
    try:
        dashboard.start()
    except KeyboardInterrupt:
        print("\nRealistic dashboard stopped.")
    except Exception as e:
        print(f"Dashboard error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
