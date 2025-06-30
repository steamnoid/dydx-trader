#!/usr/bin/env python3
"""
Objective Market Quality Dashboard - Market Condition Assessment Tool
Uses objective thresholds based on market microstructure research to assess market quality
Prevents false signals during stagnant periods by using absolute criteria, not relative scoring.
"""
import time
import signal
import sys
import os
import requests
import statistics
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from layer2_dydx_stream import DydxTradesStream
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.columns import Columns
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text


@dataclass
class MarketQualityMetrics:
    """Represents objective market quality assessment for a market"""
    market: str
    timestamp: datetime
    
    # Objective thresholds (based on market microstructure research)
    spread_bps: float          # Spread in basis points
    event_rate: float          # Updates per minute
    price_volatility_pct: float # Price movement percentage
    order_concentration: float  # Order density at best levels
    is_weekend: bool           # Weekend trading period
    
    # Overall quality assessment
    quality_score: str         # "EXCELLENT", "GOOD", "POOR", "STAGNANT"
    is_tradeable: bool         # Whether market is suitable for trading
    quality_reasons: List[str] # Reasons for quality assessment


class ObjectiveMarketQualityDashboard:
    """Dashboard for assessing market quality using objective, research-based thresholds"""
    
    def __init__(self):
        self.console = Console()
        self.stream = DydxTradesStream()
        
        # Fetch all USD markets for monitoring
        self.usd_markets = self._fetch_usd_markets()
        self.console.print(f"[green]✅ Monitoring {len(self.usd_markets)} USD markets for objective quality assessment[/green]")
        
        # Market tracking data
        self.market_current_data = {}  # market -> current orderbook/metrics
        self.market_event_history = defaultdict(lambda: deque(maxlen=60))  # market -> recent events (1 hour)
        self.market_price_history = defaultdict(lambda: deque(maxlen=20))   # market -> recent prices
        self.market_spread_history = defaultdict(lambda: deque(maxlen=30))  # market -> recent spreads
        
        # Quality tracking
        self.market_quality_metrics = {}  # market -> MarketQualityMetrics
        self.quality_history = defaultdict(lambda: deque(maxlen=100))  # market -> quality history
        
        # Performance stats
        self.quality_stats = {
            'total_markets': 0,
            'excellent_markets': 0,
            'good_markets': 0,
            'poor_markets': 0,
            'stagnant_markets': 0,
            'tradeable_markets': 0
        }
        
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _fetch_usd_markets(self):
        """Fetch all active USD markets from dYdX API"""
        try:
            session = requests.Session()
            
            # Proxy configuration
            if os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY'):
                session.verify = False
                requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
            
            response = session.get(
                'https://indexer.dydx.trade/v4/perpetualMarkets',
                timeout=(5, 15),
                headers={'User-Agent': 'dydx-quality-dashboard/1.0'}
            )
            
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
                    
                    return sorted(usd_markets)  # Track all USD markets
            
            # Fallback to major USD markets
            return ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD", "ADA-USD", "DOT-USD", "LINK-USD"]
            
        except Exception as e:
            self.console.print(f"[yellow]⚠️  Error fetching markets: {e}, using fallback[/yellow]")
            return ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD", "ADA-USD", "DOT-USD", "LINK-USD"]
    
    def start(self):
        """Start the objective market quality dashboard"""
        if not self.stream.connect():
            self.console.print("[red]❌ Failed to connect to dYdX stream[/red]")
            return
        
        self.console.print("[green]📊 Objective Market Quality Dashboard Starting...[/green]")
        self.console.print("[yellow]🔍 Assessing market quality using research-based objective thresholds...[/yellow]")
        
        # Subscribe to orderbook streams for all markets
        for market in self.usd_markets:
            self._subscribe_to_market(market)
        
        # Main display loop
        try:
            with Live(self._create_dashboard_layout(), refresh_per_second=2, console=self.console) as live:
                while self.running:
                    live.update(self._create_dashboard_layout())
                    time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            self.stream.disconnect()
            self.console.print("\n[yellow]👋 Market Quality Dashboard stopped[/yellow]")

    def _subscribe_to_market(self, market):
        """Subscribe to a single market's orderbook stream"""
        try:
            orderbook_stream = self.stream.get_orderbook_observable(market)
            orderbook_stream.subscribe(
                on_next=lambda data, m=market: self._handle_orderbook_update(m, data),
                on_error=lambda e, m=market: self.console.print(f"[red]❌ Stream error for {m}: {e}[/red]")
            )
        except Exception as e:
            self.console.print(f"[red]❌ Failed to subscribe to {market}: {e}[/red]")
    
    def _handle_orderbook_update(self, market, orderbook_data):
        """Handle incoming orderbook update and assess market quality"""
        current_time = datetime.now()
        
        try:
            # Store orderbook data
            mid_price = (float(orderbook_data['bids'][0]['price']) + float(orderbook_data['asks'][0]['price'])) / 2
            spread = float(orderbook_data['asks'][0]['price']) - float(orderbook_data['bids'][0]['price'])
            
            # Update tracking data
            self.market_event_history[market].append(current_time)
            self.market_price_history[market].append(mid_price)
            self.market_spread_history[market].append(spread)
            
            # Store current market data
            self.market_current_data[market] = {
                'orderbook': orderbook_data,
                'price': mid_price,
                'spread': spread,
                'timestamp': current_time
            }
            
            # Assess market quality using objective thresholds
            quality_metrics = self._assess_market_quality(market, orderbook_data, mid_price, spread, current_time)
            self.market_quality_metrics[market] = quality_metrics
            self.quality_history[market].append(quality_metrics)
            
            # Update overall stats
            self._update_quality_stats()
            
        except Exception as e:
            # Silently handle update errors
            pass

    def _assess_market_quality(self, market, orderbook_data, mid_price, spread, current_time) -> MarketQualityMetrics:
        """
        Assess market quality using objective thresholds based on market microstructure research
        """
        try:
            bids = orderbook_data['bids']
            asks = orderbook_data['asks']
            
            # 1. SPREAD ANALYSIS (Basis Points)
            spread_bps = (spread / mid_price) * 10000 if mid_price > 0 else 10000
            
            # 2. EVENT RATE ANALYSIS (Updates per minute)
            event_history = self.market_event_history[market]
            recent_events = [t for t in event_history if (current_time - t).total_seconds() < 60]
            event_rate = len(recent_events)
            
            # 3. PRICE VOLATILITY ANALYSIS (Recent price movement)
            price_history = self.market_price_history[market]
            if len(price_history) >= 10:
                price_range = max(price_history[-10:]) - min(price_history[-10:])
                price_volatility_pct = (price_range / mid_price) * 100 if mid_price > 0 else 0
            else:
                price_volatility_pct = 0
            
            # 4. ORDER CONCENTRATION ANALYSIS
            top_bid_size = float(bids[0]['size']) if len(bids) > 0 else 0
            top_ask_size = float(asks[0]['size']) if len(asks) > 0 else 0
            level2_bid_size = float(bids[1]['size']) if len(bids) > 1 else 0
            level2_ask_size = float(asks[1]['size']) if len(asks) > 1 else 0
            
            bid_concentration = top_bid_size / (top_bid_size + level2_bid_size) if (top_bid_size + level2_bid_size) > 0 else 0.5
            ask_concentration = top_ask_size / (top_ask_size + level2_ask_size) if (top_ask_size + level2_ask_size) > 0 else 0.5
            order_concentration = (bid_concentration + ask_concentration) / 2
            
            # 5. TIME-BASED ANALYSIS
            is_weekend = current_time.weekday() >= 5  # Saturday=5, Sunday=6
            
            # OBJECTIVE QUALITY ASSESSMENT BASED ON RESEARCH
            quality_reasons = []
            
            # Spread Quality (Based on institutional trading standards)
            if spread_bps <= 10:        # ≤ 0.10% = Excellent
                spread_quality = "EXCELLENT"
            elif spread_bps <= 25:      # ≤ 0.25% = Good  
                spread_quality = "GOOD"
            elif spread_bps <= 50:      # ≤ 0.50% = Fair
                spread_quality = "FAIR"
            else:                       # > 0.50% = Poor
                spread_quality = "POOR"
                quality_reasons.append(f"Wide spread ({spread_bps:.1f}bps)")
            
            # Event Rate Quality (Based on market activity research)
            if event_rate >= 30:        # ≥ 30/min = Very Active
                activity_quality = "EXCELLENT"
            elif event_rate >= 15:      # ≥ 15/min = Active
                activity_quality = "GOOD"
            elif event_rate >= 5:       # ≥ 5/min = Moderate
                activity_quality = "FAIR"
            else:                       # < 5/min = Stagnant
                activity_quality = "POOR"
                quality_reasons.append(f"Low activity ({event_rate}/min)")
            
            # Price Movement Quality
            if price_volatility_pct >= 0.5:     # ≥ 0.5% = Good movement
                movement_quality = "GOOD"
            elif price_volatility_pct >= 0.1:   # ≥ 0.1% = Some movement
                movement_quality = "FAIR"
            else:                               # < 0.1% = Stagnant
                movement_quality = "POOR"
                quality_reasons.append(f"No price movement ({price_volatility_pct:.3f}%)")
            
            # Order Concentration Quality
            if order_concentration <= 0.7:      # ≤ 70% = Good distribution
                concentration_quality = "GOOD"
            elif order_concentration <= 0.9:    # ≤ 90% = Fair distribution
                concentration_quality = "FAIR"
            else:                               # > 90% = Concentrated (wash trading?)
                concentration_quality = "POOR"
                quality_reasons.append(f"High order concentration ({order_concentration:.1f}%)")
            
            # Weekend Penalty
            if is_weekend:
                quality_reasons.append("Weekend trading (lower liquidity)")
            
            # OVERALL QUALITY DETERMINATION
            quality_scores = [spread_quality, activity_quality, movement_quality, concentration_quality]
            excellent_count = quality_scores.count("EXCELLENT")
            good_count = quality_scores.count("GOOD")
            fair_count = quality_scores.count("FAIR")
            poor_count = quality_scores.count("POOR")
            
            if poor_count >= 2:
                overall_quality = "STAGNANT"
                is_tradeable = False
            elif poor_count >= 1 and good_count == 0:
                overall_quality = "POOR"
                is_tradeable = False
            elif excellent_count >= 2 and poor_count == 0:
                overall_quality = "EXCELLENT"
                is_tradeable = True
            elif good_count >= 2 and poor_count == 0:
                overall_quality = "GOOD"
                is_tradeable = True
            else:
                overall_quality = "FAIR"
                is_tradeable = not is_weekend  # Fair quality is tradeable except on weekends
            
            # Weekend override for strict quality
            if is_weekend and overall_quality in ["FAIR", "POOR"]:
                is_tradeable = False
                
            return MarketQualityMetrics(
                market=market,
                timestamp=current_time,
                spread_bps=spread_bps,
                event_rate=event_rate,
                price_volatility_pct=price_volatility_pct,
                order_concentration=order_concentration,
                is_weekend=is_weekend,
                quality_score=overall_quality,
                is_tradeable=is_tradeable,
                quality_reasons=quality_reasons
            )
            
        except Exception as e:
            # Return default poor quality assessment on error
            return MarketQualityMetrics(
                market=market,
                timestamp=current_time,
                spread_bps=10000,
                event_rate=0,
                price_volatility_pct=0,
                order_concentration=1.0,
                is_weekend=True,
                quality_score="STAGNANT",
                is_tradeable=False,
                quality_reasons=["Error in quality assessment"]
            )

    def _update_quality_stats(self):
        """Update overall quality statistics"""
        total_markets = len(self.market_quality_metrics)
        if total_markets == 0:
            return
        
        excellent_markets = sum(1 for m in self.market_quality_metrics.values() if m.quality_score == "EXCELLENT")
        good_markets = sum(1 for m in self.market_quality_metrics.values() if m.quality_score == "GOOD")
        poor_markets = sum(1 for m in self.market_quality_metrics.values() if m.quality_score == "POOR")
        stagnant_markets = sum(1 for m in self.market_quality_metrics.values() if m.quality_score == "STAGNANT")
        tradeable_markets = sum(1 for m in self.market_quality_metrics.values() if m.is_tradeable)
        
        self.quality_stats = {
            'total_markets': total_markets,
            'excellent_markets': excellent_markets,
            'good_markets': good_markets,
            'poor_markets': poor_markets,
            'stagnant_markets': stagnant_markets,
            'tradeable_markets': tradeable_markets
        }

    def _create_dashboard_layout(self):
        """Create the main dashboard layout"""
        # Header
        header = Panel(
            "[bold cyan]📊 Objective Market Quality Dashboard[/bold cyan]\n"
            f"[green]🔍 Research-based thresholds • "
            f"📈 {self.quality_stats['tradeable_markets']}/{self.quality_stats['total_markets']} tradeable • "
            f"⏰ Updated: {datetime.now().strftime('%H:%M:%S')}[/green]",
            title="Market Microstructure Analysis",
            border_style="cyan"
        )
        
        # Top row: Overall stats and quality distribution
        overall_stats = self._create_overall_stats_table()
        quality_distribution = self._create_quality_distribution_table()
        
        top_row = Columns([overall_stats, quality_distribution], equal=True)
        
        # Bottom row: Best and worst markets
        best_markets = self._create_best_markets_table()
        worst_markets = self._create_worst_markets_table()
        
        bottom_row = Columns([best_markets, worst_markets], equal=True)
        
        return Columns([header, top_row, bottom_row], equal=False)

    def _create_overall_stats_table(self):
        """Create overall market quality statistics table"""
        table = Table(title="📊 Market Quality Overview", border_style="green", title_style="bold green")
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", style="bright_white", width=20)
        
        stats = self.quality_stats
        total = stats['total_markets']
        
        table.add_row("Total Markets", str(total))
        table.add_row("Tradeable Markets", f"{stats['tradeable_markets']} ({stats['tradeable_markets']/total*100:.1f}%)" if total > 0 else "0")
        table.add_row("Excellent Quality", f"{stats['excellent_markets']} ({stats['excellent_markets']/total*100:.1f}%)" if total > 0 else "0")
        table.add_row("Good Quality", f"{stats['good_markets']} ({stats['good_markets']/total*100:.1f}%)" if total > 0 else "0")
        table.add_row("Poor Quality", f"{stats['poor_markets']} ({stats['poor_markets']/total*100:.1f}%)" if total > 0 else "0")
        table.add_row("Stagnant Markets", f"{stats['stagnant_markets']} ({stats['stagnant_markets']/total*100:.1f}%)" if total > 0 else "0")
        
        return Panel(table, title="Statistics", border_style="green")

    def _create_quality_distribution_table(self):
        """Create quality distribution breakdown table"""
        table = Table(title="🎯 Quality Thresholds", border_style="blue", title_style="bold blue")
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Excellent", style="green", width=12)
        table.add_column("Good", style="yellow", width=12)
        table.add_column("Poor", style="red", width=12)
        
        table.add_row("Spread (bps)", "≤ 10", "≤ 25", "> 50")
        table.add_row("Activity (/min)", "≥ 30", "≥ 15", "< 5")
        table.add_row("Movement (%)", "≥ 0.5", "≥ 0.1", "< 0.1")
        table.add_row("Concentration", "≤ 70%", "≤ 90%", "> 90%")
        
        return Panel(table, title="Objective Thresholds", border_style="blue")

    def _create_best_markets_table(self):
        """Create table of best quality markets"""
        table = Table(title="🏆 Best Quality Markets", border_style="green", title_style="bold green")
        table.add_column("Market", style="cyan", width=12)
        table.add_column("Quality", style="bright_white", width=12)
        table.add_column("Spread (bps)", style="bright_white", width=12)
        table.add_column("Activity", style="bright_white", width=10)
        table.add_column("Tradeable", style="bright_white", width=10)
        
        # Sort by quality (EXCELLENT > GOOD > FAIR > POOR > STAGNANT)
        quality_order = {"EXCELLENT": 4, "GOOD": 3, "FAIR": 2, "POOR": 1, "STAGNANT": 0}
        sorted_markets = sorted(
            self.market_quality_metrics.items(),
            key=lambda x: (quality_order.get(x[1].quality_score, 0), -x[1].event_rate),
            reverse=True
        )
        
        for market, metrics in sorted_markets[:8]:  # Show top 8
            quality_color = {
                "EXCELLENT": "bright_green",
                "GOOD": "green", 
                "FAIR": "yellow",
                "POOR": "red",
                "STAGNANT": "dim red"
            }.get(metrics.quality_score, "white")
            
            tradeable_color = "green" if metrics.is_tradeable else "red"
            
            table.add_row(
                market,
                f"[{quality_color}]{metrics.quality_score}[/{quality_color}]",
                f"{metrics.spread_bps:.1f}",
                f"{metrics.event_rate:.0f}/min",
                f"[{tradeable_color}]{'Yes' if metrics.is_tradeable else 'No'}[/{tradeable_color}]"
            )
        
        return Panel(table, title="Best Markets", border_style="green")

    def _create_worst_markets_table(self):
        """Create table of worst quality markets with reasons"""
        table = Table(title="⚠️  Problematic Markets", border_style="red", title_style="bold red")
        table.add_column("Market", style="cyan", width=12)
        table.add_column("Quality", style="bright_white", width=12)
        table.add_column("Issues", style="bright_white", width=30)
        
        # Sort by quality (worst first)
        quality_order = {"EXCELLENT": 4, "GOOD": 3, "FAIR": 2, "POOR": 1, "STAGNANT": 0}
        sorted_markets = sorted(
            self.market_quality_metrics.items(),
            key=lambda x: (quality_order.get(x[1].quality_score, 0), x[1].event_rate),
            reverse=False
        )
        
        for market, metrics in sorted_markets[:8]:  # Show worst 8
            if metrics.quality_score in ["POOR", "STAGNANT"]:
                quality_color = {
                    "POOR": "red",
                    "STAGNANT": "dim red"
                }.get(metrics.quality_score, "white")
                
                issues = ", ".join(metrics.quality_reasons[:2])  # Show first 2 issues
                if len(issues) > 28:
                    issues = issues[:25] + "..."
                
                table.add_row(
                    market,
                    f"[{quality_color}]{metrics.quality_score}[/{quality_color}]",
                    issues
                )
        
        return Panel(table, title="Problem Markets", border_style="red")
    
    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False


def main():
    """Main entry point"""
    dashboard = ObjectiveMarketQualityDashboard()
    dashboard.start()


if __name__ == "__main__":
    main()
