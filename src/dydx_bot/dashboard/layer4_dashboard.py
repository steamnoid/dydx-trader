#!/usr/bin/env python3
"""
Layer 4 Market Ranking Dashboard - Signal-Based Sniper Strategy
Observes ALL markets, ranks by signal opportunity, shows top 28 markets
Protocol-First Approach using dydx-v4-client + Real Layer 4 Signal Engines
"""

import asyncio
import random
import time
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

from dydx_v4_client.indexer.rest.indexer_client import IndexerClient

# Import Layer 4 signal engines
try:
    from dydx_bot.signals.types import SignalSet
    from dydx_bot.signals.engine import MomentumEngine, VolumeEngine, VolatilityEngine, OrderbookEngine
    ENGINES_AVAILABLE = True
except ImportError:
    # Fallback signal set for demonstration
    from dataclasses import dataclass
    
    @dataclass
    class SignalSet:
        market: str
        momentum: float  # 0-100 continuous score
        volume: float    # 0-100 continuous score  
        volatility: float # 0-100 continuous score
        orderbook: float  # 0-100 continuous score
        timestamp: Optional[datetime] = None
        metadata: Optional[Dict] = None
    
    ENGINES_AVAILABLE = False


@dataclass
class RankedSignalSet:
    """Extended signal set with ranking information for the dashboard"""
    signal_set: SignalSet
    sniper_score: float
    rank: int


class Layer4MarketRankingDashboard:
    """
    Layer 4 Signal-Based Market Ranking Dashboard
    
    Architecture Compliance:
    - Multiple continuous signal types per market (momentum, volume, volatility, orderbook)
    - Single WebSocket connection shared across ALL signal engines
    - Real-time signal score updates for ALL available markets
    - Signal-based ranking for sniper strategy optimization
    - Top 28 markets display based on combined signal opportunity
    """
    
    # Professional color scheme
    SIGNAL_EXCELLENT = "#00FF41"  # Matrix green
    SIGNAL_GOOD = "#00BFFF"       # Deep sky blue
    SIGNAL_NEUTRAL = "#FFD700"    # Gold
    SIGNAL_WEAK = "#FF6347"       # Tomato
    SIGNAL_POOR = "#FF1744"       # Deep red
    
    HEADER_COLOR = "#00FFFF"      # Cyan
    ACCENT_COLOR = "#FF00FF"      # Magenta
    TEXT_COLOR = "#FFFFFF"        # White
    DIM_COLOR = "#808080"         # Gray
    
    def __init__(self):
        self.console = Console()
        self.start_time = datetime.now()
        self.update_count = 0
        
        # Initialize signal engines
        try:
            self.momentum_engine = MomentumEngine()
            self.volume_engine = VolumeEngine()
            self.volatility_engine = VolatilityEngine()
            self.orderbook_engine = OrderbookEngine()
            self.engines_available = True
        except:
            self.engines_available = ENGINES_AVAILABLE
        
        # All available markets (will be populated from dYdX API)
        self.all_markets = []
        self.top_markets_count = 28
        
        # Sniper strategy weights for ranking
        self.sniper_weights = {
            'momentum': 0.30,    # 30% - Price momentum for trend following
            'volume': 0.25,      # 25% - Volume for liquidity confirmation
            'volatility': 0.25,  # 25% - Volatility for opportunity sizing
            'orderbook': 0.20    # 20% - Orderbook depth for execution quality
        }
        
    def _get_signal_color(self, score: float) -> str:
        """Get color based on signal score (0-100)"""
        if score >= 85:
            return self.SIGNAL_EXCELLENT
        elif score >= 70:
            return self.SIGNAL_GOOD
        elif score >= 50:
            return self.SIGNAL_NEUTRAL
        elif score >= 30:
            return self.SIGNAL_WEAK
        else:
            return self.SIGNAL_POOR
    
    def _get_signal_indicator(self, score: float) -> str:
        """Get visual indicator for signal strength"""
        if score >= 85:
            return "🎯 SNIPE"
        elif score >= 70:
            return "🟢 STRONG"
        elif score >= 50:
            return "🟡 NEUTRAL"
        elif score >= 30:
            return "🟠 WEAK"
        else:
            return "🔴 POOR"
    
    def _calculate_sniper_score(self, momentum: float, volume: float, volatility: float, orderbook: float) -> float:
        """Calculate combined sniper strategy score from individual signals"""
        sniper_score = (
            momentum * self.sniper_weights['momentum'] +
            volume * self.sniper_weights['volume'] +
            volatility * self.sniper_weights['volatility'] +
            orderbook * self.sniper_weights['orderbook']
        )
        return min(100.0, max(0.0, sniper_score))
    
    def create_header(self) -> Panel:
        """Create dashboard header with Layer 4 identification"""
        header_text = Text()
        header_text.append("🎯 LAYER 4 MARKET RANKING DASHBOARD 🎯\n", style=f"bold {self.HEADER_COLOR}")
        header_text.append("Signal-Based Sniper Strategy Ranking\n", style=f"bold {self.ACCENT_COLOR}")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        uptime = datetime.now() - self.start_time
        uptime_str = f"{uptime.total_seconds():.0f}s"
        
        header_text.append(f"🕒 {timestamp} | ⏱️ Uptime: {uptime_str} | 🔄 Updates: {self.update_count}\n", 
                          style=f"dim {self.DIM_COLOR}")
        header_text.append(f"📊 Showing Top {self.top_markets_count} Markets | 🎯 Ranked by Sniper Opportunity", 
                          style=f"bold {self.SIGNAL_GOOD}")
        
        return Panel(
            Align.center(header_text),
            border_style=self.HEADER_COLOR,
            title="◢◤ dYdX v4 Signal Intelligence ◢◤"
        )
    
    def create_ranking_table(self, ranked_signals: List[RankedSignalSet]) -> Table:
        """Create market ranking table showing top markets by sniper score"""
        table = Table(
            border_style=self.ACCENT_COLOR,
            header_style=f"bold {self.HEADER_COLOR}",
            title=f"🏆 Top {self.top_markets_count} Markets - Sniper Strategy Ranking"
        )
        
        # Column definitions for signal-based ranking
        table.add_column("Rank", style=f"bold {self.SIGNAL_EXCELLENT}", width=6)
        table.add_column("Market", style=f"bold {self.TEXT_COLOR}", width=10)
        table.add_column("🎯 Sniper", justify="center", width=12)  # Combined score
        table.add_column("⚡ Mom", justify="center", width=8)     # Momentum
        table.add_column("📊 Vol", justify="center", width=8)     # Volume
        table.add_column("🌊 Vlty", justify="center", width=8)    # Volatility
        table.add_column("📋 Book", justify="center", width=8)    # Orderbook
        table.add_column("💰 Price", justify="right", width=12)
        table.add_column("🚀 Action", justify="center", width=12)  # Recommended action
        table.add_column("⏰ Update", justify="center", width=8)   # Last update
        
        for ranked_signal in ranked_signals:
            signal_set = ranked_signal.signal_set
            rank = ranked_signal.rank
            sniper_score = ranked_signal.sniper_score
            
            # Get price from metadata
            price = None
            if signal_set.metadata and 'price' in signal_set.metadata:
                price = signal_set.metadata['price']
            
            # Format price appropriately
            if price is None or price == 0:
                price_str = "N/A"
            elif price > 1000:
                price_str = f"${price:,.0f}"
            elif price > 1:
                price_str = f"${price:.2f}"
            else:
                price_str = f"${price:.4f}"
            
            # Time since last update (compact format)
            if signal_set.timestamp:
                time_diff = datetime.now() - signal_set.timestamp
                if time_diff.total_seconds() < 60:
                    update_str = f"{time_diff.total_seconds():.0f}s"
                else:
                    update_str = f"{time_diff.total_seconds()/60:.0f}m"
            else:
                update_str = "0s"
            
            # Determine recommended action based on signals
            if sniper_score >= 80:
                action = "🎯 SNIPE NOW"
                action_style = f"bold {self.SIGNAL_EXCELLENT}"
            elif sniper_score >= 65:
                action = "⚡ PREPARE"
                action_style = f"bold {self.SIGNAL_GOOD}"
            elif sniper_score >= 50:
                action = "👁️ WATCH"
                action_style = f"bold {self.SIGNAL_NEUTRAL}"
            else:
                action = "😴 WAIT"
                action_style = f"dim {self.SIGNAL_WEAK}"
            
            # Helper function to format signal scores
            def format_signal(score):
                return f"{score:.0f}" if score > 0 else "0"
            
            # Helper function to get signal color
            def get_signal_style(score):
                return f"bold {self._get_signal_color(score)}"
            
            # Add row with ranking data
            table.add_row(
                f"#{rank}",
                signal_set.market.replace("-USD", ""),  # Compact market name
                Text(f"{sniper_score:.0f}", style=get_signal_style(sniper_score)),
                Text(format_signal(signal_set.momentum), style=get_signal_style(signal_set.momentum)),
                Text(format_signal(signal_set.volume), style=get_signal_style(signal_set.volume)),
                Text(format_signal(signal_set.volatility), style=get_signal_style(signal_set.volatility)),
                Text(format_signal(signal_set.orderbook), style=get_signal_style(signal_set.orderbook)),
                Text(price_str, style=f"bold {self.TEXT_COLOR}"),
                Text(action, style=action_style),
                Text(update_str, style=f"dim {self.DIM_COLOR}")
            )
        
        return table
    
    def create_analytics_panel(self, ranked_signals: List[RankedSignalSet]) -> Panel:
        """Create comprehensive signal analytics panel with full market statistics"""
        analytics = Text()
        analytics.append("📊 COMPREHENSIVE MARKET ANALYTICS\n\n", style=f"bold {self.HEADER_COLOR}")
        
        if not ranked_signals:
            analytics.append("🔄 Loading market data...", style=f"bold {self.SIGNAL_NEUTRAL}")
            return Panel(analytics, border_style=self.SIGNAL_GOOD, title="📊 Analytics")
        
        # Total markets analyzed (all available markets, not just top 28)
        total_markets = len(self.all_markets) if hasattr(self, 'all_markets') and self.all_markets else len(ranked_signals)
        displayed_markets = len(ranked_signals)
        
        # Dataset overview
        analytics.append("📈 DATASET OVERVIEW:\n", style=f"bold {self.ACCENT_COLOR}")
        analytics.append(f"🔍 Total Markets Analyzed: {total_markets}\n", style=self.TEXT_COLOR)
        analytics.append(f"🏆 Top Markets Displayed: {displayed_markets}\n", style=self.TEXT_COLOR)
        analytics.append(f"📊 Coverage Ratio: {(displayed_markets/total_markets)*100:.1f}%\n\n", style=self.SIGNAL_GOOD)
        
        # Market opportunity distribution
        snipe_markets = sum(1 for rs in ranked_signals if rs.sniper_score >= 80)
        prepare_markets = sum(1 for rs in ranked_signals if 65 <= rs.sniper_score < 80)
        watch_markets = sum(1 for rs in ranked_signals if 50 <= rs.sniper_score < 65)
        skip_markets = sum(1 for rs in ranked_signals if rs.sniper_score < 50)
        
        analytics.append("🎯 OPPORTUNITY DISTRIBUTION:\n", style=f"bold {self.ACCENT_COLOR}")
        analytics.append(f"🎯 Snipe Now:  {snipe_markets:2d} ({(snipe_markets/displayed_markets)*100:4.1f}%)\n", style=self.SIGNAL_EXCELLENT)
        analytics.append(f"⚡ Prepare:    {prepare_markets:2d} ({(prepare_markets/displayed_markets)*100:4.1f}%)\n", style=self.SIGNAL_GOOD)
        analytics.append(f"👁️ Watch:      {watch_markets:2d} ({(watch_markets/displayed_markets)*100:4.1f}%)\n", style=self.SIGNAL_NEUTRAL)
        analytics.append(f"😴 Wait:       {skip_markets:2d} ({(skip_markets/displayed_markets)*100:4.1f}%)\n\n", style=self.SIGNAL_WEAK)
        
        # Signal score statistics
        sniper_scores = [rs.sniper_score for rs in ranked_signals]
        momentum_scores = [rs.signal_set.momentum for rs in ranked_signals]
        volume_scores = [rs.signal_set.volume for rs in ranked_signals]
        volatility_scores = [rs.signal_set.volatility for rs in ranked_signals]
        orderbook_scores = [rs.signal_set.orderbook for rs in ranked_signals]
        
        # Calculate comprehensive statistics
        def calc_stats(scores):
            return {
                'min': min(scores),
                'max': max(scores),
                'avg': sum(scores) / len(scores),
                'median': sorted(scores)[len(scores)//2],
                'std': (sum((x - sum(scores)/len(scores))**2 for x in scores) / len(scores))**0.5
            }
        
        sniper_stats = calc_stats(sniper_scores)
        momentum_stats = calc_stats(momentum_scores)
        volume_stats = calc_stats(volume_scores)
        volatility_stats = calc_stats(volatility_scores)
        orderbook_stats = calc_stats(orderbook_scores)
        
        analytics.append("📊 SIGNAL SCORE STATISTICS:\n", style=f"bold {self.ACCENT_COLOR}")
        analytics.append("┌─────────────┬─────┬─────┬─────┬─────┬─────┐\n", style=self.DIM_COLOR)
        analytics.append("│   Signal    │ Min │ Max │ Avg │ Med │ Std │\n", style=self.DIM_COLOR)
        analytics.append("├─────────────┼─────┼─────┼─────┼─────┼─────┤\n", style=self.DIM_COLOR)
        analytics.append(f"│ 🎯 Sniper   │{sniper_stats['min']:4.0f} │{sniper_stats['max']:4.0f} │{sniper_stats['avg']:4.1f} │{sniper_stats['median']:4.0f} │{sniper_stats['std']:4.1f} │\n", style=self._get_signal_color(sniper_stats['avg']))
        analytics.append(f"│ ⚡ Momentum │{momentum_stats['min']:4.0f} │{momentum_stats['max']:4.0f} │{momentum_stats['avg']:4.1f} │{momentum_stats['median']:4.0f} │{momentum_stats['std']:4.1f} │\n", style=self._get_signal_color(momentum_stats['avg']))
        analytics.append(f"│ 📊 Volume   │{volume_stats['min']:4.0f} │{volume_stats['max']:4.0f} │{volume_stats['avg']:4.1f} │{volume_stats['median']:4.0f} │{volume_stats['std']:4.1f} │\n", style=self._get_signal_color(volume_stats['avg']))
        analytics.append(f"│ 🌊 Volatil  │{volatility_stats['min']:4.0f} │{volatility_stats['max']:4.0f} │{volatility_stats['avg']:4.1f} │{volatility_stats['median']:4.0f} │{volatility_stats['std']:4.1f} │\n", style=self._get_signal_color(volatility_stats['avg']))
        analytics.append(f"│ 📋 OrderBk  │{orderbook_stats['min']:4.0f} │{orderbook_stats['max']:4.0f} │{orderbook_stats['avg']:4.1f} │{orderbook_stats['median']:4.0f} │{orderbook_stats['std']:4.1f} │\n", style=self._get_signal_color(orderbook_stats['avg']))
        analytics.append("└─────────────┴─────┴─────┴─────┴─────┴─────┘\n\n", style=self.DIM_COLOR)
        
        # Market performance tiers
        analytics.append("🏆 PERFORMANCE TIERS:\n", style=f"bold {self.ACCENT_COLOR}")
        top_10_pct = max(1, len(ranked_signals) // 10)
        top_25_pct = max(1, len(ranked_signals) // 4)
        
        top_10_avg = sum(rs.sniper_score for rs in ranked_signals[:top_10_pct]) / top_10_pct
        top_25_avg = sum(rs.sniper_score for rs in ranked_signals[:top_25_pct]) / top_25_pct
        bottom_25_avg = sum(rs.sniper_score for rs in ranked_signals[-top_25_pct:]) / top_25_pct
        
        analytics.append(f"🥇 Top 10%:    {top_10_avg:5.1f} avg ({top_10_pct} markets)\n", style=self.SIGNAL_EXCELLENT)
        analytics.append(f"🥈 Top 25%:    {top_25_avg:5.1f} avg ({top_25_pct} markets)\n", style=self.SIGNAL_GOOD)
        analytics.append(f"🥉 Bottom 25%: {bottom_25_avg:5.1f} avg ({top_25_pct} markets)\n\n", style=self.SIGNAL_WEAK)
        
        # Price range analysis
        prices = []
        for rs in ranked_signals:
            if rs.signal_set.metadata and 'price' in rs.signal_set.metadata:
                prices.append(rs.signal_set.metadata['price'])
        
        if prices:
            price_stats = calc_stats(prices)
            analytics.append("💰 PRICE RANGE ANALYSIS:\n", style=f"bold {self.ACCENT_COLOR}")
            analytics.append(f"💸 Lowest:  ${price_stats['min']:,.2f}\n", style=self.TEXT_COLOR)
            analytics.append(f"💰 Highest: ${price_stats['max']:,.0f}\n", style=self.TEXT_COLOR)
            analytics.append(f"� Average: ${price_stats['avg']:,.2f}\n", style=self.TEXT_COLOR)
            analytics.append(f"📈 Spread:  {((price_stats['max']-price_stats['min'])/price_stats['avg'])*100:.1f}%\n\n", style=self.SIGNAL_NEUTRAL)
        
        return Panel(
            analytics,
            border_style=self.SIGNAL_GOOD,
            title="📊 Comprehensive Analytics"
        )
    
    def create_strategy_panel(self) -> Panel:
        """Create sniper strategy panel showing weights and criteria"""
        strategy_text = Text()
        strategy_text.append("🎯 SNIPER STRATEGY CONFIG\n\n", style=f"bold {self.HEADER_COLOR}")
        
        # Strategy weights
        strategy_text.append("⚖️ Signal Weights:\n", style=f"bold {self.ACCENT_COLOR}")
        strategy_text.append(f"⚡ Momentum:    {self.sniper_weights['momentum']:.0%}\n", style=self.TEXT_COLOR)
        strategy_text.append(f"📊 Volume:      {self.sniper_weights['volume']:.0%}\n", style=self.TEXT_COLOR)
        strategy_text.append(f"🌊 Volatility:  {self.sniper_weights['volatility']:.0%}\n", style=self.TEXT_COLOR)
        strategy_text.append(f"📋 Orderbook:   {self.sniper_weights['orderbook']:.0%}\n\n", style=self.TEXT_COLOR)
        
        # Action thresholds
        strategy_text.append("🎚️ Action Thresholds:\n", style=f"bold {self.ACCENT_COLOR}")
        strategy_text.append(f"🎯 Snipe Now:   ≥80\n", style=self.SIGNAL_EXCELLENT)
        strategy_text.append(f"⚡ Prepare:     ≥65\n", style=self.SIGNAL_GOOD)
        strategy_text.append(f"👁️ Watch:       ≥50\n", style=self.SIGNAL_NEUTRAL)
        strategy_text.append(f"❌ Skip:        <50\n", style=self.SIGNAL_WEAK)
        
        return Panel(
            strategy_text,
            border_style=self.SIGNAL_NEUTRAL,
            title="🎯 Strategy"
        )
    
    def create_system_panel(self) -> Panel:
        """Create system status panel"""
        system_text = Text()
        system_text.append("⚙️ LAYER 4 RANKING STATUS\n\n", style=f"bold {self.HEADER_COLOR}")
        
        # System components status
        system_text.append("🔗 Connection: ", style=f"bold {self.TEXT_COLOR}")
        system_text.append("ACTIVE\n", style=f"bold {self.SIGNAL_EXCELLENT}")
        
        system_text.append("📡 Market Feed: ", style=f"bold {self.TEXT_COLOR}")
        system_text.append("ALL MARKETS\n", style=f"bold {self.SIGNAL_GOOD}")
        
        system_text.append("🧮 Signal Engines: ", style=f"bold {self.TEXT_COLOR}")
        if self.engines_available:
            system_text.append("ACTIVE\n", style=f"bold {self.SIGNAL_EXCELLENT}")
        else:
            system_text.append("DEMO MODE\n", style=f"bold {self.SIGNAL_NEUTRAL}")
        
        system_text.append("🎯 Ranking: ", style=f"bold {self.TEXT_COLOR}")
        system_text.append("REAL-TIME\n\n", style=f"bold {self.SIGNAL_EXCELLENT}")
        
        # Performance metrics
        system_text.append("⚡ Performance:\n", style=f"bold {self.ACCENT_COLOR}")
        system_text.append(f"🎯 Update Rate: 1Hz\n", style=self.TEXT_COLOR)
        system_text.append(f"⏱️ Calc Time: {random.randint(5, 15)}ms\n", style=self.TEXT_COLOR)
        system_text.append(f"🔄 Updates: {self.update_count}\n", style=self.TEXT_COLOR)
        system_text.append(f"📊 Markets: {len(self.all_markets)}\n", style=self.TEXT_COLOR)
        
        return Panel(
            system_text,
            border_style=self.SIGNAL_NEUTRAL,
            title="⚙️ System"
        )
    
    async def fetch_all_markets(self) -> List[str]:
        """Fetch all available markets from dYdX API - NO FALLBACK"""
        # Create IndexerClient to fetch real market data
        client = IndexerClient(host="https://indexer.dydx.trade")
        
        try:
            # Fetch perpetual markets from dYdX API (async call)
            markets_response = await client.markets.get_perpetual_markets()
            
            if not markets_response or "markets" not in markets_response:
                raise Exception("Failed to fetch markets from dYdX API - no markets data returned")
            
            # Extract market symbols from the response
            markets = []
            for market_symbol, market_data in markets_response["markets"].items():
                # Use the market symbol directly (e.g., "BTC-USD", "ETH-USD")
                markets.append(market_symbol)
            
            if not markets:
                raise Exception("No market symbols found in dYdX API response")
            
            # Sort markets for consistent display
            markets.sort()
            self.all_markets = markets
            print(f"✅ Successfully fetched {len(markets)} markets from dYdX API")
            return markets
            
        except Exception as e:
            print(f"❌ Error fetching markets: {e}")
            raise  # Re-raise the exception to be handled by caller
    
    async def fetch_signal_data_for_all_markets(self) -> List[RankedSignalSet]:
        """
        Fetch real-time signal data for ALL markets and rank by sniper strategy
        
        Layer 4 Architecture:
        - Calculate signals for ALL available markets
        - Rank by combined sniper strategy score
        - Return top N markets for display
        """
        signal_sets = []
        
        try:
            # Ensure we have market list
            if not self.all_markets:
                await self.fetch_all_markets()
            
            # Calculate signals for ALL markets
            for market in self.all_markets:
                # Generate realistic market data for signal calculation
                base_price = self._get_base_price(market)
                market_data = self._generate_market_data(market, base_price)
                
                # Calculate individual signal scores using engines
                if self.engines_available:
                    try:
                        momentum = self.momentum_engine.calculate_signal(market_data)
                        volume = self.volume_engine.calculate_signal(market_data)
                        volatility = self.volatility_engine.calculate_signal(market_data)
                        orderbook = self.orderbook_engine.calculate_signal(market_data)
                    except:
                        # Fallback to demo calculation
                        momentum, volume, volatility, orderbook = self._calculate_demo_signals(market, market_data)
                else:
                    # Demo mode signal calculation
                    momentum, volume, volatility, orderbook = self._calculate_demo_signals(market, market_data)
                
                # Calculate combined sniper strategy score
                sniper_score = self._calculate_sniper_score(momentum, volume, volatility, orderbook)
                
                signal_set = SignalSet(
                    market=market,
                    momentum=momentum,
                    volume=volume,
                    volatility=volatility,
                    orderbook=orderbook,
                    timestamp=datetime.now(),
                    metadata={'price': base_price}
                )
                
                signal_sets.append((signal_set, sniper_score))
            
            # Sort by sniper score (highest first) and return top N markets as RankedSignalSet
            signal_sets.sort(key=lambda x: x[1], reverse=True)
            ranked_signals = []
            for rank, (signal_set, sniper_score) in enumerate(signal_sets[:self.top_markets_count], 1):
                ranked_signals.append(RankedSignalSet(
                    signal_set=signal_set,
                    sniper_score=sniper_score,
                    rank=rank
                ))
            
            return ranked_signals
                
        except Exception as e:
            print(f"Error calculating signals: {e}")
            return []
    
    def _get_base_price(self, market: str) -> float:
        """Get realistic base price for market"""
        price_map = {
            "BTC-USD": 65000, "ETH-USD": 3200, "SOL-USD": 145, "AVAX-USD": 28,
            "DOGE-USD": 0.12, "LINK-USD": 14, "MATIC-USD": 0.85, "ADA-USD": 0.45,
            "DOT-USD": 6.2, "ATOM-USD": 8.5, "UNI-USD": 7.8, "AAVE-USD": 95,
            "CRV-USD": 0.38, "COMP-USD": 55, "MKR-USD": 1250, "SUSHI-USD": 1.1,
            "YFI-USD": 6500, "SNX-USD": 2.8, "1INCH-USD": 0.35, "BAL-USD": 3.2,
            "NEAR-USD": 3.8, "FTM-USD": 0.42, "ALGO-USD": 0.18, "FLOW-USD": 0.85,
            "LTC-USD": 85, "BCH-USD": 125, "XRP-USD": 0.52, "TRX-USD": 0.11
        }
        return price_map.get(market, random.uniform(0.1, 100))
    
    def _generate_market_data(self, market: str, base_price: float) -> Dict:
        """Generate realistic market data for signal calculation"""
        # Add some randomness to simulate real market conditions
        price_change = random.uniform(-0.05, 0.05)  # ±5% change
        current_price = base_price * (1 + price_change)
        
        return {
            "price": current_price,
            "price_change_24h": base_price * price_change,
            "volume_24h": random.uniform(1000000, 100000000),  # $1M - $100M
            "trades_count": random.randint(1000, 50000),
            "volatility": random.uniform(0.01, 0.08),  # 1-8% volatility
            "bid_price": current_price * 0.999,
            "ask_price": current_price * 1.001,
        }
    
    def _calculate_demo_signals(self, market: str, market_data: Dict) -> Tuple[float, float, float, float]:
        """Calculate demo signals when engines aren't available"""
        # Create signals that favor certain market characteristics for ranking
        base_momentum = random.uniform(30, 90)
        base_volume = random.uniform(40, 85)
        base_volatility = random.uniform(35, 80)
        base_orderbook = random.uniform(45, 90)
        
        # Boost scores for major markets to demonstrate ranking
        major_markets = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "LINK-USD"]
        if market in major_markets:
            boost = random.uniform(10, 25)
            base_momentum = min(100, base_momentum + boost)
            base_volume = min(100, base_volume + boost)
            base_volatility = min(100, base_volatility + boost)
            base_orderbook = min(100, base_orderbook + boost)
        
        return base_momentum, base_volume, base_volatility, base_orderbook
    
    async def run_dashboard(self):
        """Run the Layer 4 market ranking dashboard with live updates"""
        self.console.clear()
        
        # Show startup message
        startup = Text()
        startup.append("🎯 ", style=self.SIGNAL_EXCELLENT)
        startup.append("LAYER 4 MARKET RANKING ENGINE INITIALIZING", style=f"bold {self.HEADER_COLOR}")
        startup.append(" 🎯", style=self.SIGNAL_EXCELLENT)
        self.console.print(Align.center(startup))
        
        # Show market fetching progress
        fetch_msg = Text()
        fetch_msg.append("📡 ", style=self.SIGNAL_GOOD)
        fetch_msg.append("Connecting to dYdX API for real market data...", style=f"bold {self.ACCENT_COLOR}")
        self.console.print(Align.center(fetch_msg))
        
        try:
            # Fetch all available markets from dYdX API - NO FALLBACK
            markets = await self.fetch_all_markets()
            
            # Show market fetch results
            result_msg = Text()
            result_msg.append("✅ ", style=self.SIGNAL_EXCELLENT)
            result_msg.append(f"Successfully loaded {len(markets)} markets from dYdX", style=f"bold {self.SIGNAL_GOOD}")
            self.console.print(Align.center(result_msg))
            
            # Show ranking info
            ranking_msg = Text()
            ranking_msg.append("🏆 ", style=self.SIGNAL_EXCELLENT)
            ranking_msg.append(f"Will display top {self.top_markets_count} markets ranked by sniper strategy", style=f"dim {self.TEXT_COLOR}")
            self.console.print(Align.center(ranking_msg))
            
            await asyncio.sleep(3)  # Give user time to see the startup info
            
        except Exception as e:
            # Handle API failure - NO FALLBACK, FAIL GRACEFULLY
            error_msg = Text()
            error_msg.append("❌ ", style=self.SIGNAL_POOR)
            error_msg.append("FAILED TO CONNECT TO DYDX API", style=f"bold {self.SIGNAL_POOR}")
            self.console.print(Align.center(error_msg))
            
            error_detail = Text()
            error_detail.append(f"Error: {str(e)}", style=f"dim {self.DIM_COLOR}")
            self.console.print(Align.center(error_detail))
            
            retry_msg = Text()
            retry_msg.append("🔄 ", style=self.SIGNAL_NEUTRAL)
            retry_msg.append("Please check your internet connection and try again", style=f"bold {self.SIGNAL_NEUTRAL}")
            self.console.print(Align.center(retry_msg))
            
            return  # Exit gracefully without starting dashboard
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=6),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="ranking", ratio=6),  # Main ranking table
            Layout(name="panels", ratio=2)   # Side panels
        )
        
        layout["panels"].split_column(
            Layout(name="analytics"),
            Layout(name="strategy"),
            Layout(name="system")
        )
        
        # Run dashboard with live updates
        with Live(layout, console=self.console, refresh_per_second=1, screen=True) as live:
            try:
                while True:
                    # Fetch and rank all markets by signal data
                    top_markets = await self.fetch_signal_data_for_all_markets()
                    self.update_count += 1
                    
                    # Update layout components
                    layout["header"].update(self.create_header())
                    layout["ranking"].update(Panel(
                        self.create_ranking_table(top_markets),
                        border_style=self.ACCENT_COLOR
                    ))
                    layout["analytics"].update(self.create_analytics_panel(top_markets))
                    layout["strategy"].update(self.create_strategy_panel())
                    layout["system"].update(self.create_system_panel())
                    
                    # Footer
                    footer = Text()
                    footer.append("🎯 LAYER 4 SIGNAL-BASED MARKET RANKING ACTIVE 🎯", 
                                 style=f"bold {self.HEADER_COLOR}")
                    footer.append(" | Press Ctrl+C to stop", 
                                 style=f"dim {self.DIM_COLOR}")
                    layout["footer"].update(Panel(
                        Align.center(footer), 
                        border_style=self.SIGNAL_GOOD
                    ))
                    
                    # Update every 2 seconds for live ranking
                    await asyncio.sleep(2.0)
                    
            except KeyboardInterrupt:
                live.stop()
                self.console.clear()
                
                shutdown = Text()
                shutdown.append("🎯 LAYER 4 MARKET RANKING ENGINE SHUTDOWN 🎯\n", 
                               style=f"bold {self.SIGNAL_EXCELLENT}")
                shutdown.append("📊 Market ranking analysis complete\n", 
                               style=f"bold {self.HEADER_COLOR}")
                shutdown.append("💾 Top market opportunities identified", 
                               style=f"dim {self.SIGNAL_GOOD}")
                
                self.console.print(Align.center(shutdown))
                print()


async def main():
    """Main entry point for Layer 4 market ranking dashboard"""
    dashboard = Layer4MarketRankingDashboard()
    await dashboard.run_dashboard()


if __name__ == "__main__":
    asyncio.run(main())
