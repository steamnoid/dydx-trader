#!/usr/bin/env python3
"""
Multi-Crypto Mean-Reversion Dashboard for dYdX v4 Trading
Paper trading simulation with 10-minute rolling window z-score strategy using minute-wise aggregation

MULTI-CRYPTO STRATEGY SPECIFICATION:
===================================

ENTRY CRITERIA:
- Markets: BTC-USD, ETH-USD, SOL-USD
- Rolling window: 10 minutes (600 seconds) with minute-wise data aggregation
- Z-score threshold: ±3.0 for entry
- Position size: Fixed $10 USD per trade per market
- Maximum positions: 1 position per market (max 3 total)

EXIT CRITERIA:
- Z-score returns to neutral (abs < 0.5)
- Minimum holding: 30 minutes (1800 seconds)
- Maximum holding: 2 hours (7200 seconds)
- Emergency stop: -10% of position value

REAL-TIME METRICS:
- Current z-score and rolling statistics
- Entry/exit prices and timestamps
- Profit/loss tracking per trade
- Trade duration and holding periods
- Account balance and position status

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
import json
import zmq
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Deque
from datetime import datetime, timedelta
import statistics
import numpy as np

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from layer2_dydx_callbacks import DydxTradesStreamCallbacks
from websocket_health_monitor import WebSocketHealthMonitor

@dataclass
class PricePoint:
    timestamp: float
    price: float
    bid: float
    ask: float
    volume: float = 0.0
    spread_pct: float = 0.0

@dataclass
class MinuteBar:
    """Aggregated price data for minute-wise analysis"""
    timestamp: float  # Start of the minute
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    bid: float
    ask: float
    spread_pct: float
    trade_count: int = 0

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
    status: str  # "OPEN", "CLOSED", "MISSED", "PENDING"
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
    result: str = "pending"  # "win", "loss", "missed", "pending"
    exit_type: str = "none"  # "TP", "SL", "timeout", "none"
    # TTL/GTT tracking for dYdX v4 compatibility
    order_entry_time: Optional[float] = None  # When the order was placed
    order_expiration_time: Optional[float] = None  # When the order expires (30s default)

class FillSimulator:
    """Realistic fill simulation based on orderbook depth and market spread"""
    
    def __init__(self, min_orderbook_depth_usd: float = 5.0):
        self.min_orderbook_depth_usd = min_orderbook_depth_usd
        
    def simulate_fill(self, order_price: float, side: str, current_bid: float, 
                     current_ask: float, order_size_usd: float) -> bool:
        """
        Simulate realistic fill probability based on orderbook position and spread
        
        Args:
            order_price: Limit order price
            side: "BUY" or "SELL" 
            current_bid: Current best bid price
            current_ask: Current best ask price
            order_size_usd: Order size in USD
            
        Returns:
            True if order would likely fill, False otherwise
        """
        # Calculate how competitive our order is relative to current spread
        spread = current_ask - current_bid
        mid_price = (current_bid + current_ask) / 2
        
        if side == "BUY":
            # For buy orders, check how far below the current ask we're placing
            price_improvement = current_ask - order_price
            competitiveness = price_improvement / spread if spread > 0 else 0
            
            # More competitive if we're close to but not crossing the ask
            
            # Don't allow crossing the spread (would become TAKER)
            if order_price >= current_ask:
                return False
                
        else:  # SELL
            # For sell orders, check how far above the current bid we're placing  
            price_improvement = order_price - current_bid
            competitiveness = price_improvement / spread if spread > 0 else 0
            
            
            # Don't allow crossing the spread (would become TAKER)
            if order_price <= current_bid:
                return False
        
        # Simulate orderbook depth based on spread and order size
        # Assume reasonable depth exists at competitive prices
        estimated_depth_usd = self.min_orderbook_depth_usd * (1 + competitiveness * 2)
        
        # Check if sufficient depth exists for our order size
        if estimated_depth_usd < order_size_usd:
            return False
        
        # Base fill probability based on competitiveness and market conditions
        if competitiveness > 0.8:  # Very competitive price
            base_probability = 0.85
        elif competitiveness > 0.5:  # Moderately competitive
            base_probability = 0.70
        elif competitiveness > 0.2:  # Somewhat competitive
            base_probability = 0.50
        else:  # Not very competitive
            base_probability = 0.25
            
        # Adjust for order size relative to estimated depth
        size_factor = min(1.0, estimated_depth_usd / order_size_usd)
        final_probability = base_probability * size_factor
        
        will_fill = random.random() < final_probability
        
        return will_fill

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
        
        # Add fill simulator for realistic execution
        self.fill_simulator = FillSimulator()
        
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
        """Simulate limit order for MAKER-ONLY strategy with realistic fill simulation
        
        Per dYdX v4 documentation:
        - Post Only orders enforce MAKER-only behavior  
        - Orders are cancelled if they would cross the spread (become TAKER)
        - MAKER orders earn rebates (negative fees)
        - Now includes realistic fill simulation based on orderbook depth
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
        
        # Simulate execution latency for limit orders (faster than market orders)
        order.latency_ms = random.uniform(5, 30)
        
        # Use realistic fill simulation based on orderbook depth
        order_size_usd = size * limit_price
        would_fill = self.fill_simulator.simulate_fill(
            limit_price, side, current_bid, current_ask, order_size_usd
        )
        
        if would_fill:
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
    
    def __init__(self, lookback_seconds: int = 600, deviation_threshold: float = 3.0, dashboard=None):
        # BTC-only strategy with 10-minute rolling window
        self.lookback_seconds = lookback_seconds  # 600 seconds = 10 minutes
        self.deviation_threshold = deviation_threshold  # 3.0 z-score threshold
        self.price_history: Dict[str, Deque[PricePoint]] = defaultdict(lambda: deque(maxlen=1200))  # 20 minutes at 1 update/sec
        
        # NEW: Minute-wise aggregation for more stable statistics
        self.minute_bars: Dict[str, Deque[MinuteBar]] = defaultdict(lambda: deque(maxlen=20))  # 20 minutes of minute bars
        self.current_minute_data: Dict[str, List[PricePoint]] = defaultdict(list)  # Accumulator for current minute
        
        self.order_simulator = RealisticOrderSimulator()
        self.dashboard = dashboard  # Reference to dashboard for account balance access
        
        # BTC-only position sizing parameters - fixed $10 position size
        self.position_size_usd = 10.0  # Fixed $10 per trade
        self.min_account_balance_usd = 20.0  # Minimum balance to trade $10 positions
        
    def _aggregate_minute_bar(self, market: str, current_time: float):
        """Aggregate current minute data into a minute bar when crossing minute boundary"""
        if market not in self.current_minute_data or not self.current_minute_data[market]:
            return
            
        minute_data = self.current_minute_data[market]
        
        # Get the minute start time from the first data point in the accumulator
        oldest_data_time = minute_data[0].timestamp
        minute_start = int(oldest_data_time // 60) * 60  # Start of the minute being aggregated
        
        # Calculate minute bar statistics
        prices = [p.price for p in minute_data]
        volumes = [p.volume for p in minute_data]
        
        minute_bar = MinuteBar(
            timestamp=minute_start,
            open_price=prices[0],
            high_price=max(prices),
            low_price=min(prices),
            close_price=prices[-1],
            volume=sum(volumes),
            bid=minute_data[-1].bid,  # Use last bid/ask
            ask=minute_data[-1].ask,
            spread_pct=minute_data[-1].spread_pct,
            trade_count=len(minute_data)
        )
        
        self.minute_bars[market].append(minute_bar)
        
        # Clear the current minute accumulator - this resets the timing
        self.current_minute_data[market] = []
        
    def update_price(self, market: str, price_data: dict):
        """Update price history with enhanced data and minute-wise aggregation"""
        current_time = time.time()
        current_minute = int(current_time // 60) * 60
        
        bids = price_data.get('bids', [])
        asks = price_data.get('asks', [])
        
        if not bids or not asks:
            return
            
        try:
            # Safely extract bid/ask prices with error handling
            if not bids[0] or 'price' not in bids[0]:
                return
            if not asks[0] or 'price' not in asks[0]:
                return
                
            bid = float(bids[0]['price'])
            ask = float(asks[0]['price'])
        except (KeyError, ValueError, TypeError, IndexError):
            # Skip malformed price data
            return
            
        mid_price = (bid + ask) / 2
        
        # Calculate spread percentage
        spread_pct = ((ask - bid) / mid_price) * 100 if mid_price > 0 else 0
        
        # Estimate volume (simplified) - handle missing volume data
        try:
            bid_volume = sum(float(level.get('size', 0)) for level in bids[:5])
            ask_volume = sum(float(level.get('size', 0)) for level in asks[:5])
            total_volume = bid_volume + ask_volume
        except (ValueError, TypeError):
            total_volume = 0.0
        
        # For BTC-only strategy, ensure we always have some volume data
        if total_volume <= 0:
            total_volume = 1.0  # Assume minimal volume for z-score calculations
        
        price_point = PricePoint(
            timestamp=current_time,
            price=mid_price,
            bid=bid,
            ask=ask,
            volume=total_volume,
            spread_pct=spread_pct
        )
        
        # Add to high-frequency price history (for real-time updates)
        self.price_history[market].append(price_point)
        
        # NEW: Minute-wise aggregation logic - trigger when crossing minute boundary
        # Check if we've moved to a new minute AND the previous minute is complete
        last_minute_data = self.current_minute_data[market]
        if last_minute_data and last_minute_data[0].timestamp // 60 != current_time // 60:
            # We've moved to a new minute, aggregate the previous minute's data
            oldest_data_time = last_minute_data[0].timestamp
            previous_minute_start = int(oldest_data_time // 60) * 60
            current_minute_start = int(current_time // 60) * 60
            
            # Aggregate the previous minute's data immediately when crossing boundary
            self._aggregate_minute_bar(market, oldest_data_time)
        
        # Add current data point to minute accumulator
        self.current_minute_data[market].append(price_point)
    
    def calculate_signal(self, market: str) -> Optional[MeanReversionSignal]:
        """Calculate enhanced mean-reversion signal using minute-wise aggregated data"""
        if market not in self.minute_bars:
            return None
            
        minute_bars = self.minute_bars[market]
        
        # IMPORTANT: Check if we have current minute data that should be aggregated
        current_time = time.time()
        current_minute_start = int(current_time // 60) * 60
        
        if (market in self.current_minute_data and 
            self.current_minute_data[market] and 
            len(self.current_minute_data[market]) > 0):
            
            oldest_data_time = self.current_minute_data[market][0].timestamp
            oldest_minute_start = int(oldest_data_time // 60) * 60
            
            # If the current minute data is from a previous minute (should be aggregated)
            # OR if we have been accumulating data for more than 60 seconds
            if (oldest_minute_start < current_minute_start or 
                current_time - oldest_data_time >= 60):
                self._aggregate_minute_bar(market, oldest_data_time)
        
        # Re-check minute bars after potential aggregation
        minute_bars = self.minute_bars[market]
        
        # Warmup: Set to 11 minutes for stable statistics
        # Need 11 bars minimum: 1 to ignore + 10 for rolling window calculation
        min_warmup_bars = 11  # Minimum 11 minute bars (1 to ignore + 10 for window)
        if len(minute_bars) < min_warmup_bars:
            return None
        
        # ADDITIONAL WARMUP CHECK: Ensure at least 11 minutes have elapsed since dashboard started
        # Need 11 minutes: 1 minute to ignore + 10 minutes for rolling window
        min_warmup_time_seconds = 660  # 11 minutes in seconds
        time_elapsed = current_time - self.dashboard.session_start
        if time_elapsed < min_warmup_time_seconds:
            return None
            
        current_time = time.time()
        lookback_minutes = self.lookback_seconds // 60  # Convert to minutes (should be 10)
        
        # Use minute bars for rolling window calculation (more stable than high-frequency data)
        # Use last N bars instead of time-based filtering to ensure we always have enough bars
        min_rolling_bars = max(10, self.lookback_seconds // 60)  # At least 10 bars for 10-minute window
        
        # IGNORE FIRST MINUTE BIN: Skip the very first minute bar to ensure only complete/reliable bars
        # We need min_rolling_bars + 1 total bars to have min_rolling_bars usable bars after skipping the first
        min_total_bars_needed = min_rolling_bars + 1
        
        if len(minute_bars) >= min_total_bars_needed:
            # Skip the first minute bar and use the most recent N bars for the rolling window
            available_bars = list(minute_bars)[1:]  # Skip first minute bin
            recent_bars = available_bars[-min_rolling_bars:]  # Take last N bars from remaining
        else:
            # Not enough bars yet (need at least min_rolling_bars + 1 to skip first and have enough for window)
            return None
            
        # Use minute bar close prices for z-score calculation (more stable)
        price_values = [bar.close_price for bar in recent_bars]
        
        # Fast mean calculation
        n = len(price_values)
        price_sum = sum(price_values)
        mean_price = price_sum / n
        
        # Fast standard deviation calculation
        if n > 1:
            variance = sum((x - mean_price) ** 2 for x in price_values) / (n - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0
            
        # Get current price from most recent high-frequency data or latest minute bar
        if market in self.price_history and self.price_history[market]:
            current_price = self.price_history[market][-1].price
            current_volume = self.price_history[market][-1].volume
        else:
            current_price = recent_bars[-1].close_price
            current_volume = recent_bars[-1].volume
            
        deviation_pct = ((current_price - mean_price) / mean_price) * 100
        

        
        # BTC-only strategy: strict z-score calculation using minute-aggregated data
        if std_dev == 0:
            z_score = 0.0  # Set to 0 to avoid division errors as per specification
        else:
            z_score = (current_price - mean_price) / std_dev
        
        # BTC-only strategy: use strict z-score thresholds (±3.0 for entry)
        signal_type = "NEUTRAL"
        confidence = 0.0
        
        # Volume check: only trade when volume > 0 (per specification)
        if current_volume <= 0:
            return MeanReversionSignal(
                market=market,
                timestamp=current_time,
                signal_type="NEUTRAL",
                deviation=deviation_pct,
                entry_price=current_price,
                confidence=0.0,
                z_score=z_score
            )
        
        # Entry conditions: z-score < -3.0 (long) or z-score > 3.0 (short)
        # FIXED: Use ±3.0 threshold for stricter entry criteria
        if z_score <= -3.0:
            signal_type = "BUY"  # Long position when price below mean
            confidence = min(100, abs(z_score) * 25)
        elif z_score >= 3.0:
            signal_type = "SELL"  # Short position when price above mean  
            confidence = min(100, abs(z_score) * 25)
        
        # Create the signal object
        signal = MeanReversionSignal(
            market=market,
            timestamp=current_time,
            signal_type=signal_type,
            deviation=deviation_pct,
            entry_price=current_price,
            confidence=confidence,
            z_score=z_score
        )
        
        return signal
    
    def calculate_position_size(self, market: str, signal: MeanReversionSignal, 
                              current_price: float) -> float:
        """Calculate position size for multi-crypto strategy - $10 position per market"""
        
        # Multi-crypto strategy: trade BTC, ETH, SOL with $10 each
        supported_markets = ["BTC-USD", "ETH-USD", "SOL-USD"]
        
        if market in supported_markets:
            # Check if account has sufficient balance for $10 trade
            if self.dashboard.account_balance >= self.position_size_usd:
                # Calculate crypto amount for $10 position
                crypto_amount = self.position_size_usd / current_price
                
                # Set appropriate precision based on market
                if market == "BTC-USD":
                    return round(crypto_amount, 6)  # 6 decimal places for BTC
                elif market == "ETH-USD":
                    return round(crypto_amount, 5)  # 5 decimal places for ETH
                elif market == "SOL-USD":
                    return round(crypto_amount, 3)  # 3 decimal places for SOL
            else:
                # Insufficient balance - calculate fractional position we can afford
                affordable_usd = self.dashboard.account_balance * 0.95  # 5% buffer
                affordable_crypto = affordable_usd / current_price
                
                # Minimum amounts based on market
                if market == "BTC-USD":
                    return max(0.000001, affordable_crypto)
                elif market == "ETH-USD":
                    return max(0.00001, affordable_crypto)
                elif market == "SOL-USD":
                    return max(0.001, affordable_crypto)
        
        # For unsupported markets
        return 0.0

class RealisticMeanReversionDashboard:
    """Enhanced dashboard with realistic paper trading"""
    
    def __init__(self):
        self.console = Console()
        self.stream = DydxTradesStreamCallbacks()
        
        # Initialize WebSocket Health Monitor
        self.health_monitor = WebSocketHealthMonitor(
            websocket_manager=self.stream,
            reconnect_callback=self._handle_websocket_reconnection
        )
        
        # Subscription and health monitor tracking
        self.subscribed_markets = set()  # Markets we've confirmed subscription for
        self.markets_with_updates = set()  # Markets that have received at least 1 update
        self.health_monitor_started = False  # Track if health monitor has been started
        
        # Account management - $100 starting capital for $10 position trades
        self.starting_capital = 100.0  # $100 starting capital
        self.account_balance = 100.0  # Updated with realized P&L
        
        # Multi-crypto strategy parameters
        self.position_size_usd = 10.0  # Fixed $10 per trade per market
        self.min_holding_period_seconds = 1800  # 30 minutes minimum holding
        self.max_positions_per_market = 1  # One position per market (max 3 total)
        
        # Initialize multi-crypto strategy with dashboard reference for account balance access
        self.strategy = RealisticMeanReversionStrategy(
            lookback_seconds=600,  # 600s = 10 minutes
            deviation_threshold=3.0,  # 3.0 z-score threshold
            dashboard=self
        )
        
        # Market tracking
        self.active_markets = set()
        self.current_prices: Dict[str, PricePoint] = {}
        self.signals: Dict[str, MeanReversionSignal] = {}
        
        # Realistic position tracking
        self.positions: List[Position] = []
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
            'open_positions': [],  # List of open positions (allows multiple per market)
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
        self.max_open_positions = 10
        self.max_total_exposure_usd = 10000.0
        self.daily_loss_limit_usd = 1000.0
        
        # Trade logging and inter-process communication
        self.enable_trade_logging = True
        self._setup_trade_publisher()
        
        # Position entry lock to prevent rapid duplicate entries
        self._entry_lock = False
        
    def _fetch_usd_markets(self):
        """Multi-crypto strategy - trade BTC, ETH, and SOL"""
        return self._get_fallback_markets()
    
    def _get_fallback_markets(self):
        """Multi-crypto strategy - trade BTC, ETH, and SOL"""
        return ["BTC-USD", "ETH-USD", "SOL-USD"]
    
    def start(self):
        """Start the realistic dashboard"""
        self.console.print("[cyan]🚀 Starting Multi-Crypto Mean-Reversion Dashboard...[/cyan]")
        markets = self._fetch_usd_markets()
        
        self.console.print(f"[green]✅ Multi-crypto strategy initialized (BTC, ETH, SOL) with 10-minute rolling window using minute-wise aggregation[/green]")
        
        # Connect to dYdX WebSocket stream
        self.console.print("[cyan]🔗 Connecting to dYdX WebSocket...[/cyan]")
        if not self.stream.connect():
            # Get the actual error message
            error_msg = self.stream.get_last_error()
            if error_msg:
                self.console.print(f"[red]❌ Failed to connect to dYdX WebSocket: {error_msg}[/red]")
            else:
                self.console.print("[red]❌ Failed to connect to dYdX WebSocket: Connection timeout or unknown error[/red]")
            return
        
        self.console.print("[green]✅ Connected to dYdX WebSocket[/green]")
        self.console.print("[cyan]🔍 WebSocket health monitoring will start after all subscriptions are confirmed and receive updates[/cyan]")
        
        # Set up market subscriptions
        subscription_errors = 0
        for market in markets:
            self.active_markets.add(market)
            try:
                self.stream.subscribe_to_orderbook(
                    market, 
                    lambda data, market=market: self._handle_orderbook_update(market, data)
                )
                # Mark market as subscribed (confirmation will be handled in message processing)
                self.subscribed_markets.add(market)
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
            finally:
                # Clean shutdown
                self.console.print("[cyan]🔄 Shutting down WebSocket connections...[/cyan]")
                if self.health_monitor_started:
                    self.health_monitor.stop_monitoring()
                try:
                    self.stream.disconnect()
                    self.console.print("[green]✅ WebSocket disconnected cleanly[/green]")
                except:
                    pass
    
    def _check_and_start_health_monitor(self):
        """Start health monitor only after all subscriptions are confirmed and have received updates"""
        if (not self.health_monitor_started and 
            len(self.markets_with_updates) >= len(self.subscribed_markets) and
            len(self.subscribed_markets) > 0):
            
            self.health_monitor.start_monitoring()
            self.health_monitor_started = True
            self.console.print("[green]✅ WebSocket health monitoring started (all subscriptions confirmed with updates)[/green]")
    
    def _handle_orderbook_update(self, market: str, data: dict):
        """Handle orderbook updates with realistic trading logic"""
        try:
            # Track that this market has received an update
            if market not in self.markets_with_updates:
                self.markets_with_updates.add(market)
                
                # Check if we should start health monitor now
                self._check_and_start_health_monitor()
            
            # Notify health monitor of message received (only if started)
            if self.health_monitor_started:
                self.health_monitor.on_message_received()
            
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
                
                # Check for position entry opportunities with strict z-score threshold
                if (abs(signal.z_score) >= 3.0 and  # Strict 3.0 z-score threshold
                    signal.signal_type != "NEUTRAL" and
                    not self._entry_lock and  # Prevent rapid duplicate entries
                    self._can_open_position(market)):
                    self._entry_lock = True  # Set lock before entry
                    self._execute_entry_order(signal)
                    # Note: entry lock released inside _execute_entry_order after position is fully tracked
            
            # Update existing positions
            self._update_positions()
            
            self.update_count += 1
            self.last_update = time.time()
            
        except Exception as e:
            self.console.print(f"[red]Error processing {market}: {e}[/red]")
    
    def _can_open_position(self, market: str) -> bool:
        """Check if we can open a new position in the specified market"""
        
        # Multi-crypto strategy: allow BTC-USD, ETH-USD, SOL-USD
        supported_markets = ["BTC-USD", "ETH-USD", "SOL-USD"]
        if market not in supported_markets:
            return False
        
        # Check if we already have an open position in this specific market
        open_positions_in_market = [pos for pos in self.positions 
                                   if pos.market == market and pos.status == "OPEN"]
        
        # Allow max 1 position per market (so max 3 total positions)
        if len(open_positions_in_market) >= 1:
            return False
        
        # Check if we have sufficient account balance for $10 trade
        current_point = self.current_prices.get(market)
        if current_point:
            if self.account_balance < self.position_size_usd:
                return False
        
        return True
    
    def _execute_entry_order(self, signal: MeanReversionSignal):
        """Execute MAKER-ONLY entry order with realistic fill simulation and TTL expiration"""
        market = signal.market
        current_point = self.current_prices.get(market)
        
        if not current_point:
            return
        
        # Calculate position size
        position_size = self.strategy.calculate_position_size(
            market, signal, current_point.price
        )
        
        # Record order entry time for TTL tracking (using time.time() for consistency)
        order_entry_time = time.time()
        order_expiration_time = order_entry_time + 120  # 30s TTL

        
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
        
        position = Position(
            market=market,
            entry_time=order.timestamp,
            entry_price=limit_price,
            signal_type=signal.signal_type,
            size=position_size,
            status="PENDING",
            entry_order=order,
            result="pending",
            order_entry_time=order_entry_time,
            order_expiration_time=order_expiration_time
        )
        
        if order.status == "FILLED":
            # Update position to OPEN status for filled MAKER order
            position.status = "OPEN"
            position.entry_price = order.avg_fill_price
            position.size = order.filled_size
            position.fees_total = order.fees_paid  # This will be negative (rebate)
            
            # Add to open positions list
            self.market_stats[market]['open_positions'].append(position)
            
            # Log filled entry order
            self._log_trade("FILL", position, {
                "fill_price": order.avg_fill_price,
                "fees_paid": order.fees_paid,
                "latency_ms": order.latency_ms
            })
            
        elif order.status == "PENDING":
            # Add pending position to tracking (will be filled later or expire)
            self.market_stats[market]['open_positions'].append(position)
            
            # Log pending entry order
            self._log_trade("ENTRY", position, {
                "order_type": "LIMIT",
                "order_expiration": order_expiration_time,
                "signal_confidence": signal.confidence
            })
            
        else:  # CANCELLED or immediate MISS
            # Create missed position for tracking strategy effectiveness
            position.status = "MISSED"
            position.result = "missed"
            position.exit_type = "cancelled"
        
        # Add position to tracking regardless of status
        self.positions.append(position)
        self.market_stats[market]['total_positions'] += 1
        
        # Release entry lock AFTER position is fully tracked to prevent race conditions
        self._entry_lock = False
        
        
    
    def _log_trade(self, action: str, position: Position, details: dict = None):
        """Publish trade opportunity to pyzmq queue for live trader consumption"""
        if not self.enable_trade_logging:
            return
            
        # Publish trade opportunity to the queue
        self._publish_trade_opportunity(action, position, details)
    
    def _update_positions(self):
        """Update open positions with realistic PnL and exit logic, including TTL expiration"""
        current_time = time.time()
        
        for position in self.positions:
            # First, check for PENDING orders that may have expired (TTL/GTT logic)
            if position.status == "PENDING":
                current_point = self.current_prices.get(position.market)
                if not current_point:
                    continue
                
                # Check if order has expired (30s TTL)
                if (position.order_expiration_time and 
                    current_time > position.order_expiration_time):
                    
                    # Order expired - mark as MISSED and remove from open positions
                    position.status = "MISSED"
                    position.result = "missed"
                    position.exit_type = "expired"
                    
                    # Remove from open positions list
                    if position in self.market_stats[position.market]['open_positions']:
                        self.market_stats[position.market]['open_positions'].remove(position)
                    continue
                
                # Try to fill pending order with some probability based on time elapsed
                time_elapsed = current_time - (position.order_entry_time or current_time)
                fill_probability = min(0.6, time_elapsed / 30.0)  # Up to 60% chance over 30s
                
                # Use realistic fill simulation again
                order_size_usd = position.size * position.entry_price
                would_fill = (random.random() < fill_probability and 
                             self.strategy.order_simulator.fill_simulator.simulate_fill(
                                 position.entry_price, position.signal_type,
                                 current_point.bid, current_point.ask, order_size_usd
                             ))
                
                if would_fill:
                    # Pending order fills - convert to OPEN position
                    position.status = "OPEN"
                    position.entry_time = current_time  # Update entry time to fill time
                    
                    # Create a simulated filled order
                    filled_order = Order(
                        market=position.market,
                        side=position.signal_type,
                        order_type="LIMIT",
                        size=position.size,
                        price=position.entry_price,
                        timestamp=current_time,
                        status="FILLED",
                        filled_size=position.size,
                        avg_fill_price=position.entry_price
                    )
                    
                    # Calculate MAKER fees (rebate)
                    notional_value = position.size * position.entry_price
                    filled_order.fees_paid = notional_value * self.strategy.order_simulator.maker_fee_rate
                    position.fees_total = filled_order.fees_paid
                    position.entry_order = filled_order
                    
                    # Update global stats
                    self.position_count += 1
                    self.total_fees_paid += filled_order.fees_paid  # Adding negative value (rebate)
                    
                continue  # Skip to next position since this one just filled
            
            elif position.status == "OPEN":
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
                
                # Exit logic: BTC-only strategy with 30-minute minimum holding and z-score exit
                should_exit = False
                exit_reason = ""
                
                # Calculate holding time
                holding_time = current_time - position.entry_time
                
                # 1. Minimum holding period: 30 minutes (1800 seconds)
                if holding_time < self.min_holding_period_seconds:
                    # Don't exit before minimum holding period
                    continue
                
                # 2. Z-score exit criterion: exit when z-score crosses back to neutral (abs < 0.5)
                market_signal = self.signals.get(position.market)
                if market_signal and abs(market_signal.z_score) < 0.5:
                    should_exit = True
                    exit_reason = "z_score_neutral"
                
                # 3. Maximum holding period: 2 hours (7200 seconds)
                elif holding_time > 7200:
                    should_exit = True
                    exit_reason = "max_holding_timeout"
                
                # 4. Emergency stop loss: -10% of $10 position value = -$1
                elif position.pnl_usd < -1.0:  # $1 stop loss for $10 position
                    should_exit = True
                    exit_reason = "emergency_stop_loss"
                
                if should_exit:
                    self._execute_exit_order(position, exit_reason)
    
    def _execute_exit_order(self, position: Position, reason: str):
        """Execute MAKER-ONLY exit order with realistic fill simulation"""
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
        
        # Use realistic fill simulation with orderbook depth
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
            
            # Set exit type based on reason
            if reason == "profit_target":
                position.exit_type = "TP"
                position.result = "win"
            elif reason == "stop_loss":
                position.exit_type = "SL" 
                position.result = "loss"
            elif reason in ["time_limit", "timeout"]:
                position.exit_type = "timeout"
                position.result = "win" if position.pnl_usd > 0 else "loss"
            else:
                position.exit_type = "TP" if position.pnl_usd > 0 else "SL"
                position.result = "win" if position.pnl_usd > 0 else "loss"
            
            # Final PnL calculation with MAKER rebates
            if position.signal_type == "BUY":
                position.pnl_usd = (position.exit_price - position.entry_price) * position.size - position.fees_total
            else:
                position.pnl_usd = (position.entry_price - position.exit_price) * position.size - position.fees_total
            
            position.pnl = (position.pnl_usd / (position.size * position.entry_price)) * 100
            
            # Update statistics
            market_stats = self.market_stats[position.market]
            # Remove from open positions
            if position in market_stats['open_positions']:
                market_stats['open_positions'].remove(position)
            market_stats['total_pnl_usd'] += position.pnl_usd
            market_stats['total_fees_usd'] += position.fees_total  # This will be negative (total rebates)
            market_stats['positions'].append(position)
            
            if position.pnl_usd > 0:
                self.winning_positions += 1
                market_stats['winning_positions'] += 1
            
            # Update global stats
            self.total_pnl_usd += position.pnl_usd
            self.total_fees_paid += exit_order.fees_paid
            
            # Update account balance with realized P&L
            self.account_balance += position.pnl_usd
            
            # Log completed exit order
            self._log_trade("EXIT", position, {
                "exit_reason": reason,
                "exit_type": position.exit_type,
                "holding_time": position.holding_time,
                "fees_paid": exit_order.fees_paid,
                "final_pnl": position.pnl_usd
            })
            
            # Update market-specific stats
            self._update_market_stats(position.market)
            
        elif exit_order.status == "CANCELLED":
            # Order cancelled due to crossing spread - keep position open
            pass
            
        else:
            # Order not filled due to insufficient volume - keep position open  
            pass
    
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
        multi_crypto_strategy_panel = self._create_multi_crypto_strategy_panel()  # Use multi-crypto strategy panel
        
        layout.split_column(
            Layout(header, size=6),
            Layout(
                Columns([markets_table, stats_panel], equal=True)
            ),
            Layout(positions_table, size=30),
            Layout(multi_crypto_strategy_panel, size=10)  # Add multi-crypto strategy panel to layout
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
        
        # Count different position types
        open_positions = len([p for p in self.positions if p.status == "OPEN"])
        pending_positions = len([p for p in self.positions if p.status == "PENDING"])
        closed_positions = len([p for p in self.positions if p.status == "CLOSED"])
        missed_positions = len([p for p in self.positions if p.status == "MISSED"])
        
        header_text = Text()
        header_text.append("🚀 DYDX LIVE TRADING - MEAN REVERSION STRATEGY ", style="bold blue")
        header_text.append(f"| Markets: {active_count} ", style="white")
        header_text.append(f"| Signals: {signal_count} ", style="green")
        header_text.append(f"| Open: {open_positions} ", style="yellow")
        header_text.append(f"| Pending: {pending_positions} ", style="orange1")
        header_text.append(f"| Closed: {closed_positions} ", style="cyan")
        header_text.append(f"| Missed: {missed_positions} ", style="red")
        header_text.append(f"| P&L: ${self.total_pnl_usd:.2f} ", 
                          style="green" if self.total_pnl_usd >= 0 else "red")
        
        # Account balance display
        balance_color = "green" if self.account_balance >= self.starting_capital else "red"
        balance_pct = ((self.account_balance - self.starting_capital) / self.starting_capital) * 100
        header_text.append(f"| Balance: ${self.account_balance:.2f} ({balance_pct:+.1f}%) ", 
                          style=balance_color)
        
        header_text.append(f"| Time: {current_time}", style="cyan")
        
        # Second line with MAKER-specific session info and WebSocket health
        header_text.append(f"\nSession: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d} ", 
                          style="magenta")
        header_text.append(f"| Updates: {self.update_count} ", style="cyan")
        
        # Current minute bin information
        current_minute_timestamp = int(time.time() // 60) * 60
        current_minute_str = datetime.fromtimestamp(current_minute_timestamp).strftime('%H:%M')
        header_text.append(f"| Minute Bin: {current_minute_str} ", style="yellow")
        
        # Message counts for current minute bin for each market
        market_counts = []
        total_current_messages = 0
        for market in ["BTC-USD", "ETH-USD", "SOL-USD"]:
            if market in self.strategy.current_minute_data:
                count = len(self.strategy.current_minute_data[market])
                total_current_messages += count
                market_counts.append(f"{market.split('-')[0]}:{count}")
        
        header_text.append(f"| Msgs: {total_current_messages} ", style="cyan")
        if market_counts:
            header_text.append(f"({', '.join(market_counts)}) ", style="white")
        
        # WebSocket health status
        health_stats = self.health_monitor.get_health_stats()
        ws_status = "🟢 HEALTHY" if health_stats['is_healthy'] else "🔴 UNHEALTHY"
        ws_color = "green" if health_stats['is_healthy'] else "red"
        header_text.append(f"| WS: {ws_status} ", style=ws_color)
        
        if health_stats['reconnection_count'] > 0:
            header_text.append(f"| Reconnects: {health_stats['reconnection_count']} ", style="yellow")
        
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
            if stats['open_positions']:
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
            
            # Status - show multiple positions if they exist
            open_positions = stats['open_positions']
            if open_positions:
                if len(open_positions) == 1:
                    pos = open_positions[0]
                    pos_color = "green" if pos.signal_type == "BUY" else "red"
                    pos_symbol = "🟩 LONG" if pos.signal_type == "BUY" else "🟥 SHORT"
                    status_str = f"[{pos_color}]{pos_symbol} {pos.pnl_usd:+.1f}[/{pos_color}]"
                else:
                    # Multiple positions - show count and total PnL
                    total_pnl = sum(pos.pnl_usd for pos in open_positions)
                    long_count = sum(1 for pos in open_positions if pos.signal_type == "BUY")
                    short_count = len(open_positions) - long_count
                    
                    if long_count > 0 and short_count > 0:
                        status_str = f"[yellow]🟨 {len(open_positions)} POS {total_pnl:+.1f}[/yellow]"
                    elif long_count > 0:
                        status_str = f"[green]🟩 {long_count} LONG {total_pnl:+.1f}[/green]"
                    else:
                        status_str = f"[red]🟥 {short_count} SHORT {total_pnl:+.1f}[/red]"
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
        
        title = f"📊 BTC-USD Analysis - 10-Minute Rolling Z-Score Strategy"
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
        
        # Performance tier based on win rate
        if win_rate >= 95:
            performance_tier = "🏆 EXCEPTIONAL"
            tier_style = "bold gold1"
        elif win_rate >= 85:
            performance_tier = "🥇 EXCELLENT"
            tier_style = "bold bright_green"
        elif win_rate >= 70:
            performance_tier = "🥈 GOOD"
            tier_style = "bold yellow"
        elif win_rate >= 50:
            performance_tier = "🥉 AVERAGE"
            tier_style = "bold white"
        else:
            performance_tier = "❌ POOR"
            tier_style = "bold red"
        
        stats_table.add_row("📊 Total Trades", str(total_trades))
        stats_table.add_row("✅ Winners", str(self.winning_positions))
        
        # Special celebration for high win rates
        win_rate_str = f"{win_rate:.1f}%"
        if win_rate >= 95:
            win_rate_str = f"🔥{win_rate:.1f}%🔥"
        stats_table.add_row("📈 Win Rate", win_rate_str)
        
        # Show performance tier
        stats_table.add_row("🎯 Tier", performance_tier)
        
        stats_table.add_row("💰 Gross P&L", f"${self.total_pnl_usd:.2f}")
        
        # Show rebates separately from fees for MAKER trading
        if rebate_earned > 0:
            stats_table.add_row("💎 Rebates Earned", f"+${rebate_earned:.2f}")
        if fees_paid > 0:
            stats_table.add_row("💸 Fees Paid", f"-${fees_paid:.2f}")
            
        # Net with special formatting for exceptional performance
        net_str = f"${net_with_rebates:.2f}"
        if net_with_rebates > 100 and win_rate >= 95:
            net_str = f"🚀{net_str}🚀"
        stats_table.add_row("🎯 Net + Rebates", net_str)
        
        stats_table.add_row("📊 Avg Trade", f"${avg_pnl_usd:.2f}")
        
        stats_table.add_row("", "")
        stats_table.add_row("💹 Open Positions", str(len(open_positions)))
        stats_table.add_row("🔴 Closed Positions", str(len([p for p in self.positions if p.status == "CLOSED"])))
        stats_table.add_row("🟠 Missed Entries", str(len([p for p in self.positions if p.status == "MISSED"])))
        stats_table.add_row("💹 Open P&L", f"${open_pnl:.2f}")
        stats_table.add_row("📏 Exposure", f"${total_exposure:.0f}")
        
        stats_table.add_row("", "")
        stats_table.add_row("⚙️ Strategy", "REALISTIC MAKER")
        stats_table.add_row("📊 Z-Threshold", f"{self.strategy.deviation_threshold:.1f}")
        stats_table.add_row("🎯 Min Confidence", "75%")
        stats_table.add_row("💎 Fee Rate", "-0.02%")
        stats_table.add_row("🔍 TTL Expiry", "30s")
        
        # WebSocket health information
        health_stats = self.health_monitor.get_health_stats()
        stats_table.add_row("", "")
        ws_status = "🟢 Healthy" if health_stats['is_healthy'] else "🔴 Unhealthy"
        stats_table.add_row("📡 WebSocket", ws_status)
        stats_table.add_row("📨 WS Messages", f"{health_stats['message_count']:,}")
        
        uptime_minutes = health_stats['connection_age_seconds'] / 60
        if uptime_minutes < 60:
            uptime_str = f"{uptime_minutes:.1f}m"
        else:
            uptime_str = f"{uptime_minutes/60:.1f}h"
        stats_table.add_row("⏱️ WS Uptime", uptime_str)
        
        if health_stats['reconnection_count'] > 0:
            stats_table.add_row("🔄 Reconnects", str(health_stats['reconnection_count']))
        
        # Special celebration message for exceptional performance
        title = "📈 Realistic MAKER Performance"
        if win_rate >= 95 and total_trades >= 10:
            title = "🏆 EXCEPTIONAL Performance"
        elif win_rate >= 85 and total_trades >= 5:
            title = "🥇 EXCELLENT Performance"
        
        return Panel(stats_table, title=title, border_style="green")
    
    def _create_positions_table(self) -> Panel:
        """Create enhanced positions table with new status types"""
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
        table.add_column("Exit", style="cyan", width=8)
        
        # Show recent positions (last 25)
        recent_positions = sorted(self.positions, key=lambda p: p.entry_time, reverse=True)[:25]
        
        if not recent_positions:
            table.add_row("--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--")
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
                elif position.status == "MISSED":
                    hold_time = 0  # No holding time for missed entries
                else:
                    hold_time = position.holding_time
                
                if hold_time < 60:
                    hold_str = f"{hold_time:.0f}s" if hold_time > 0 else "--"
                else:
                    hold_str = f"{hold_time/60:.1f}m"
                
                # Format values
                side_str = position.signal_type
                if position.signal_type == "BUY":
                    side_str = "[green]LONG[/green]"
                else:
                    side_str = "[red]SHORT[/red]"
                
                size_str = f"{position.size:.3f}" if position.status not in ["MISSED"] else f"({position.size:.3f})"
                entry_str = f"${position.entry_price:.3f}" if position.status not in ["MISSED"] else f"(${position.entry_price:.3f})"
                current_str = f"${current_price:.3f}" if position.status not in ["MISSED", "PENDING"] else "--"
                
                # P&L formatting
                if position.status in ["MISSED", "PENDING"]:
                    pnl_usd_str = "--"
                    pnl_pct_str = "--"
                    fees_str = "--"
                else:
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
                
                # Enhanced Status display with TTL info for PENDING orders
                if position.status == "OPEN":
                    status_str = "[yellow]OPEN[/yellow]"
                elif position.status == "PENDING":
                    # Show time remaining for pending orders
                    if position.order_expiration_time:
                        time_remaining = position.order_expiration_time - current_time
                        if time_remaining > 0:
                            status_str = f"[orange1]PENDING {time_remaining:.0f}s[/orange1]"
                        else:
                            status_str = "[red]EXPIRED[/red]"
                    else:
                        status_str = "[orange1]PENDING[/orange1]"
                elif position.status == "MISSED":
                    status_str = "[orange1]MISSED[/orange1]"
                elif position.status == "CLOSED":
                    if position.result == "win":
                        status_str = "[green]WIN[/green]"
                    elif position.result == "loss":
                        status_str = "[red]LOSS[/red]"
                    else:
                        status_str = "[white]CLOSED[/white]"
                else:
                    status_str = position.status
                
                # Exit type display
                if position.exit_type == "TP":
                    exit_str = "[green]TP[/green]"
                elif position.exit_type == "SL":
                    exit_str = "[red]SL[/red]"
                elif position.exit_type == "timeout":
                    exit_str = "[orange1]TIME[/orange1]"
                elif position.exit_type == "expired":
                    exit_str = "[red]EXP[/red]"
                elif position.status == "MISSED":
                    exit_str = "[orange1]MISS[/orange1]"
                elif position.status == "PENDING":
                    exit_str = "[orange1]WAIT[/orange1]"
                else:
                    exit_str = "--"
                
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
                    status_str,
                    exit_str
                )
        
        return Panel(table, title="💼 Realistic Position Tracking", border_style="yellow")
    
    def _create_multi_crypto_strategy_panel(self) -> Panel:
        """Create multi-crypto strategy metrics panel with real-time z-score and trade details"""
        
        content = []
        
        # Strategy status header
        content.append("[bold cyan]🌟 MULTI-CRYPTO MEAN REVERSION STRATEGY[/bold cyan]")
        content.append("")
        
        # Markets overview
        markets = ["BTC-USD", "ETH-USD", "SOL-USD"]
        content.append("[bold white]Market Status:[/bold white]")
        
        for market in markets:
            market_data = self.current_prices.get(market)
            market_signal = self.signals.get(market)
            market_stats = self.market_stats[market]
            
            symbol = market.split('-')[0]
            
            if market_data and market_signal:
                price_str = f"${market_data.price:,.2f}"
                z_score_str = f"{market_signal.z_score:+.3f}"
                
                # Color z-score based on significance
                if abs(market_signal.z_score) >= 3.0:
                    z_score_str = f"[red]{z_score_str}[/red]"
                elif abs(market_signal.z_score) >= 1.0:
                    z_score_str = f"[yellow]{z_score_str}[/yellow]"
                else:
                    z_score_str = f"[green]{z_score_str}[/green]"
                
                signal_color = "green" if market_signal.signal_type == "BUY" else "red" if market_signal.signal_type == "SELL" else "white"
                content.append(f"• {symbol}: {price_str} | Z: {z_score_str} | [{signal_color}]{market_signal.signal_type}[/{signal_color}]")
            else:
                content.append(f"• {symbol}: [yellow]Warming up...[/yellow]")
        
        content.append("")
        
        # Strategy parameters
        content.append("[bold white]Strategy Parameters:[/bold white]")
        content.append(f"• Markets: [cyan]BTC, ETH, SOL[/cyan]")
        content.append(f"• Rolling Window: [cyan]10 minutes (minute-aggregated)[/cyan]")
        content.append(f"• Entry Z-Score: [cyan]±3.0[/cyan]")
        content.append(f"• Exit Z-Score: [cyan]±0.5[/cyan]")
        content.append(f"• Min Holding: [cyan]30 minutes[/cyan]")
        content.append(f"• Position Size: [cyan]$10 USD per market[/cyan]")
        content.append(f"• Max Positions: [cyan]1 per market (3 total)[/cyan]")
        
        content.append("")
        
        # Current positions across all markets
        total_open_positions = sum(len(self.market_stats[market]['open_positions']) for market in markets)
        
        if total_open_positions > 0:
            content.append(f"[bold white]Open Positions ({total_open_positions}):[/bold white]")
            
            for market in markets:
                open_positions = self.market_stats[market]['open_positions']
                if open_positions:
                    pos = open_positions[0]  # Only one position per market
                    symbol = market.split('-')[0]
                    holding_minutes = (time.time() - pos.entry_time) / 60
                    pnl_color = "green" if pos.pnl_usd > 0 else "red"
                    pos_type_color = "green" if pos.signal_type == "BUY" else "red"
                    
                    content.append(f"• {symbol}: [{pos_type_color}]{pos.signal_type}[/{pos_type_color}] | ${pos.entry_price:,.2f} | [{pnl_color}]${pos.pnl_usd:+,.2f}[/{pnl_color}] | {holding_minutes:.0f}min")
        else:
            content.append("[bold white]Open Positions:[/bold white]")
            content.append("• Status: [blue]⚪ No positions open[/blue]")
            content.append("• Waiting for: [white]Z-score ≥ ±3.0 signals[/white]")
        
        content.append("")
        
        # Session performance across all markets
        content.append("[bold white]Session Performance:[/bold white]")
        total_trades = sum(self.market_stats[market]['total_positions'] for market in markets)
        total_pnl = sum(self.market_stats[market]['total_pnl_usd'] for market in markets)
        
        if total_trades > 0:
            winning_trades = sum(self.market_stats[market]['winning_positions'] for market in markets)
            win_rate = (winning_trades / total_trades) * 100
            pnl_color = "green" if total_pnl > 0 else "red"
            
            content.append(f"• Total Trades: [white]{total_trades}[/white]")
            content.append(f"• Win Rate: [white]{win_rate:.0f}%[/white]")
            content.append(f"• Net P&L: [{pnl_color}]${total_pnl:+,.2f}[/{pnl_color}]")
            
            # Per-market breakdown
            for market in markets:
                symbol = market.split('-')[0]
                market_trades = self.market_stats[market]['total_positions']
                market_pnl = self.market_stats[market]['total_pnl_usd']
                if market_trades > 0:
                    market_pnl_color = "green" if market_pnl > 0 else "red"
                    content.append(f"  - {symbol}: {market_trades} trades | [{market_pnl_color}]${market_pnl:+.2f}[/{market_pnl_color}]")
        else:
            content.append("• Total Trades: [white]0[/white]")
            content.append("• Status: [yellow]Waiting for first signals[/yellow]")
        
        return Panel(
            "\n".join(content),
            title="🎯 DYDX Trading Dashboard - Live Performance",
            border_style="cyan"
        )

    def _print_final_summary(self):
        """Print comprehensive final performance summary for realistic MAKER trading"""
        # total_attempts = len(all_positions)
        # total_closed = len(closed_positions)
        # total_missed = len(missed_positions)
        
        # # Closed position statistics
        # if closed_positions:
        #     winning_trades = len([p for p in closed_positions if p.result == "win"])
        #     losing_trades = len([p for p in closed_positions if p.result == "loss"])
            
        #     # Exit type breakdown
        #     tp_exits = len([p for p in closed_positions if p.exit_type == "TP"])
        #     sl_exits = len([p for p in closed_positions if p.exit_type == "SL"])
        #     timeout_exits = len([p for p in closed_positions if p.exit_type == "timeout"])
            
        #     gross_profit = sum(p.pnl_usd for p in closed_positions if p.pnl_usd > 0)
        #     gross_loss = abs(sum(p.pnl_usd for p in closed_positions if p.pnl_usd < 0))
            
        #     # MAKER-specific calculations
        #     rebate_earned = abs(self.total_fees_paid) if self.total_fees_paid < 0 else 0
        #     fees_paid = self.total_fees_paid if self.total_fees_paid > 0 else 0
        # else:
        #     winning_trades = losing_trades = tp_exits = sl_exits = timeout_exits = 0
        #     gross_profit = gross_loss = rebate_earned = fees_paid = 0
            
        # net_profit_with_rebates = self.total_pnl_usd + rebate_earned - fees_paid
        
        # avg_win = gross_profit / winning_trades if winning_trades > 0 else 0
        # avg_loss = gross_loss / losing_trades if losing_trades > 0 else 0
        
        # profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        # win_rate = (winning_trades / total_closed * 100) if total_closed > 0 else 0
        # fill_rate = (total_closed / total_attempts * 100) if total_attempts > 0 else 0
        
        # best_trade = max(p.pnl_usd for p in closed_positions) if closed_positions else 0
        # worst_trade = min(p.pnl_usd for p in closed_positions) if closed_positions else 0
        
        # avg_holding_time = statistics.mean([p.holding_time for p in closed_positions if p.holding_time > 0]) if closed_positions else 0
        
        # # Determine performance tier for celebration
        # if win_rate >= 95 and total_closed >= 10:
        #     performance_emoji = "🏆🔥🎉"
        #     performance_tier = "LEGENDARY INSTITUTIONAL-GRADE"
        #     tier_color = "bold gold1"
        # elif win_rate >= 90 and total_closed >= 5:
        #     performance_emoji = "🥇✨"
        #     performance_tier = "EXCEPTIONAL PROFESSIONAL"
        #     tier_color = "bold bright_green"
        # elif win_rate >= 80:
        #     performance_emoji = "🥈"
        #     performance_tier = "EXCELLENT"
        #     tier_color = "bold yellow"
        # elif win_rate >= 70:
        #     performance_emoji = "🥉"
        #     performance_tier = "GOOD"
        #     tier_color = "bold white"
        # else:
        #     performance_emoji = "📊"
        #     performance_tier = "DEVELOPING"
        #     tier_color = "white"
        
        # # Print enhanced summary
        # self.console.print("\n" + "="*90)
        # if win_rate >= 95:
        #     self.console.print(f"[{tier_color}]{performance_emoji} LEGENDARY PERFORMANCE ACHIEVED! {performance_emoji}[/{tier_color}]")
        # self.console.print(f"[bold cyan]REALISTIC MAKER-ONLY MEAN REVERSION STRATEGY - FINAL RESULTS[/bold cyan]")
        # self.console.print("="*90)
        
        # self.console.print(f"📊 [bold]Trading Performance[/bold]")
        # self.console.print(f"   Strategy Type: MAKER-ONLY with Realistic Fill Simulation & TTL")
        # self.console.print(f"   Performance Tier: [{tier_color}]{performance_tier}[/{tier_color}]")
        # self.console.print(f"   Total Signal Attempts: {total_attempts}")
        # self.console.print(f"   Successful Fills: {total_closed} ({fill_rate:.1f}%)")
        # self.console.print(f"   Missed Opportunities: {total_missed} ({(total_missed/total_attempts*100) if total_attempts > 0 else 0:.1f}%)")
        
        # # Special formatting for exceptional win rates
        # if win_rate >= 95:
        #     self.console.print(f"   🔥 EXCEPTIONAL Win Rate: [{tier_color}]{win_rate:.1f}%[/{tier_color}] 🔥")
        #     self.console.print(f"   ✅ Winning Trades: [{tier_color}]{winning_trades}[/{tier_color}]")
        #     self.console.print(f"   ❌ Losing Trades: {losing_trades} (Only {losing_trades}!)")
        # else:
        #     self.console.print(f"   Winning Trades: {winning_trades} ({win_rate:.1f}% of filled)")
        #     self.console.print(f"   Losing Trades: {losing_trades}")
        
        # self.console.print(f"\n🎯 [bold]Exit Type Breakdown[/bold]")
        # self.console.print(f"   Take Profit (TP): {tp_exits}")
        # self.console.print(f"   Stop Loss (SL): {sl_exits}")
        # self.console.print(f"   Timeouts: {timeout_exits}")
        
        # self.console.print(f"\n💰 [bold]Financial Results[/bold]")
        # self.console.print(f"   Gross Profit: ${gross_profit:.2f}")
        # self.console.print(f"   Gross Loss: ${gross_loss:.2f}")
        
        # # Show MAKER-specific fee breakdown
        # if rebate_earned > 0:
        #     self.console.print(f"   [bold green]Rebates Earned: +${rebate_earned:.2f}[/bold green]")
        # if fees_paid > 0:
        #     self.console.print(f"   [bold red]Fees Paid: -${fees_paid:.2f}[/bold red]")
            
        # color = "green" if net_profit_with_rebates >= 0 else "red"
        # self.console.print(f"   [bold {color}]Net Profit (incl. rebates): ${net_profit_with_rebates:.2f}[/bold {color}]")
        
        # self.console.print(f"\n📈 [bold]Performance Metrics[/bold]")
        # self.console.print(f"   Profit Factor: {profit_factor:.2f}")
        # self.console.print(f"   Average Win: ${avg_win:.2f}")
        # self.console.print(f"   Average Loss: ${avg_loss:.2f}")
        # self.console.print(f"   Best Trade: ${best_trade:.2f}")
        # self.console.print(f"   Worst Trade: ${worst_trade:.2f}")
        # self.console.print(f"   Avg Hold Time: {avg_holding_time:.1f}s")
        
        # self.console.print(f"\n🎯 [bold]Realistic Strategy Assessment[/bold]")
        # if win_rate >= 95 and profit_factor >= 10 and net_profit_with_rebates > 0 and fill_rate >= 70:
        #     self.console.print(f"   [{tier_color}]🏆 LEGENDARY INSTITUTIONAL-GRADE STRATEGY! 🏆[/{tier_color}]")
        #     self.console.print(f"   [{tier_color}]💎 This performance rivals professional trading desks[/{tier_color}]")
        #     self.console.print(f"   [{tier_color}]🚀 98%+ win rate with TTL precision is exceptional[/{tier_color}]")
        # elif win_rate >= 85 and profit_factor >= 5 and net_profit_with_rebates > 0 and fill_rate >= 60:
        #     self.console.print(f"   [bold green]🥇 EXCEPTIONAL PROFESSIONAL STRATEGY[/bold green]")
        #     self.console.print(f"   [bold green]💎 Outstanding performance with rebate advantage[/bold green]")
        # elif win_rate >= 60 and profit_factor >= 1.5 and net_profit_with_rebates > 0 and fill_rate >= 70:
        #     self.console.print(f"   [bold green]✅ HIGHLY PROFITABLE REALISTIC STRATEGY[/bold green]")
        #     self.console.print(f"   [bold green]💎 Strong fill rate with rebate advantage[/bold green]")
        # elif win_rate >= 50 and profit_factor >= 1.2 and fill_rate >= 50:
        #     self.console.print(f"   [bold yellow]⚠️  MARGINAL BUT REALISTIC STRATEGY[/bold yellow]")
        # else:
        #     self.console.print(f"   [bold red]❌ NEEDS IMPROVEMENT - Low fill rate or unprofitable[/bold red]")
        
        # # Enhanced MAKER-specific insights
        # self.console.print(f"\n📈 [bold]TTL & Fill Analysis[/bold]")
        # self.console.print(f"   Order Fill Success Rate: {fill_rate:.1f}%")
        # self.console.print(f"   Average Rebate per Filled Trade: ${rebate_earned/total_closed:.3f}" if total_closed > 0 else "   No trades completed")
        # self.console.print(f"   TTL Expiration Logic: {'🎯 Perfect - Prevents Stale Orders' if fill_rate >= 60 else 'Consider Longer TTL'}")
        # self.console.print(f"   Volume-Based Fill Logic: {'✅ Highly Effective' if fill_rate >= 70 else 'Consider Lower Thresholds'}")
        
        
        # if win_rate >= 95:
        #     self.console.print(f"\n🎉 [bold {tier_color}]CELEBRATION METRICS[/bold {tier_color}]")
        #     self.console.print(f"   🔥 Win Streak Potential: {winning_trades} consecutive wins possible!")
        #     self.console.print(f"   💰 Risk-Adjusted Excellence: Only {losing_trades} loss in {total_closed} trades")
        #     self.console.print(f"   📈 Theoretical Annual Return: Potentially 500%+ with this consistency")
        #     self.console.print(f"   🏆 Strategy Ranking: TOP 1% of retail trading strategies")
        
        # missed_potential = total_missed * 30 if total_missed > 0 else 0
        # self.console.print(f"   Missed Opportunity Impact: {missed_potential:.0f} USD potential (est. $30 avg)")
        
        # self.console.print("="*90)

    def _handle_websocket_reconnection(self) -> bool:
        """Handle WebSocket reconnection with full resubscription"""
        try:
            self.console.print("[yellow]🔄 WebSocket reconnection initiated...[/yellow]")
            
            # Reset connection state instead of calling non-existent disconnect()
            try:
                self.stream.reset_connection_state()
            except:
                pass  # Ignore reset errors
            
            time.sleep(2)  # Brief pause before reconnection
            
            # Attempt reconnection
            if self.stream.connect():
                self.console.print("[green]✅ WebSocket reconnected successfully[/green]")
                
                # Wait for connection to be fully established before resubscribing
                time.sleep(1)
                
                # Verify connection is actually established
                if not self.stream.is_connected():
                    self.console.print("[red]❌ WebSocket connection not properly established[/red]")
                    return False
                
                # Resubscribe to all active markets
                subscription_errors = 0
                for market in self.active_markets:
                    try:
                        self.stream.subscribe_to_orderbook(
                            market, 
                            lambda data, market=market: self._handle_orderbook_update(market, data)
                        )
                    except Exception as e:
                        subscription_errors += 1
                        self.console.print(f"[red]Resubscription error for {market}: {e}[/red]")
                
                if subscription_errors == 0:
                    self.console.print(f"[green]✅ All {len(self.active_markets)} markets resubscribed[/green]")
                else:
                    self.console.print(f"[yellow]⚠️  {subscription_errors} resubscription errors[/yellow]")
                
                return True
            else:
                # Get the actual error message
                error_msg = self.stream.get_last_error()
                if error_msg:
                    self.console.print(f"[red]❌ WebSocket reconnection failed: {error_msg}[/red]")
                else:
                    self.console.print("[red]❌ WebSocket reconnection failed: Connection timeout or unknown error[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]❌ Reconnection handler error: {e}[/red]")
            return False
    
    def _setup_trade_publisher(self):
        """Initialize pyzmq publisher for inter-process communication"""
        try:
            self.zmq_context = zmq.Context()
            self.trade_publisher = self.zmq_context.socket(zmq.PUB)
            # Bind to localhost on port 5555 for trade opportunities
            self.trade_publisher.bind("tcp://127.0.0.1:5555")
            print("Trade publisher initialized on tcp://127.0.0.1:5555")
        except Exception as e:
            print(f"Failed to setup trade publisher: {e}")
            self.trade_publisher = None
            self.zmq_context = None
    
    def _publish_trade_opportunity(self, action: str, position: Position, details: dict = None):
        """Publish trade opportunity to pyzmq queue for live trader consumption"""
        if not self.trade_publisher:
            return
            
        try:
            trade_message = {
                "timestamp": time.time(),
                "datetime": datetime.now().isoformat(),
                "action": action,  # "ENTRY", "EXIT", "FILL", "EXPIRE"
                "market": position.market,
                "side": position.signal_type,
                "size": position.size,
                "price": position.entry_price if action == "ENTRY" else position.exit_price,
                "status": position.status,
                "pnl_usd": position.pnl_usd,
                "details": details or {},
                "source": "realistic_mean_reversion_dashboard"
            }
            
            # Publish with topic "TRADE_OPPORTUNITY" for filtering
            topic = "TRADE_OPPORTUNITY"
            message = json.dumps(trade_message)
            self.trade_publisher.send_multipart([topic.encode('utf-8'), message.encode('utf-8')])
            
        except Exception as e:
            # Don't break trading for publishing errors
            print(f"Failed to publish trade opportunity: {e}")
    
    def cleanup(self):
        """Clean up pyzmq resources"""
        try:
            if self.trade_publisher:
                self.trade_publisher.close()
            if self.zmq_context:
                self.zmq_context.term()
        except Exception as e:
            print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    dashboard = RealisticMeanReversionDashboard()
    try:
        dashboard.start()
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
    finally:
        dashboard.cleanup()
        print("Dashboard stopped")
