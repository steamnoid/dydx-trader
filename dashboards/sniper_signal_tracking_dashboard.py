#!/usr/bin/env python3
"""
Traditional Sniper Dashboard - Simplified Accuracy Validation Tool
Tracks when traditional sniper scores hit 80+ and measures subsequent market performance
Uses ONLY traditional order book metrics: spread, depth, imbalance, price impact.
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
class TraditionalSniperSignal:
    """Represents a traditional sniper signal when score hits 80+"""
    market: str
    timestamp: datetime
    score: float
    signal_price: float
    traditional_metrics: Dict
    
    # Outcome tracking (filled in over time)
    outcomes: Dict = field(default_factory=dict)  # timeframe -> outcome data
    is_complete: bool = False


@dataclass
class SignalOutcome:
    """Represents the outcome of a sniper signal after some time"""
    timeframe: str  # "1min", "5min", "15min", "30min"
    price_change_pct: float
    spread_change_pct: float
    volume_change_pct: float
    opportunity_duration: float  # seconds the opportunity lasted
    execution_feasible: bool  # could we have actually traded?
    profit_estimate: float  # estimated profit/loss in %


class TraditionalSniperDashboard:
    """Dashboard for tracking and validating traditional sniper metric accuracy"""
    
    def __init__(self):
        self.console = Console()
        self.stream = DydxTradesStream()
        
        # Fetch all USD markets for monitoring
        self.usd_markets = self._fetch_usd_markets()
        self.console.print(f"[green]✅ Monitoring {len(self.usd_markets)} USD markets for 80+ traditional sniper signals[/green]")
        
        # Signal tracking
        self.active_signals: List[TraditionalSniperSignal] = []  # Signals awaiting outcome measurement
        self.completed_signals: List[TraditionalSniperSignal] = []  # Signals with full outcome data
        self.market_current_data = {}  # market -> current orderbook/metrics
        
        # Track which markets have already triggered an action for the current signal
        self.markets_with_active_signal = set()
        
        # Performance tracking
        self.accuracy_stats = {
            'total_signals': 0,
            'profitable_signals': 0,
            'accuracy_rate': 0.0,
            'avg_return': 0.0,
            'best_return': 0.0,
            'worst_return': 0.0,
            'avg_duration': 0.0
        }
        
        # Market-specific performance
        self.market_performance = defaultdict(lambda: {
            'signals': 0,
            'profitable': 0,
            'accuracy': 0.0,
            'avg_return': 0.0
        })
        
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
                headers={'User-Agent': 'dydx-traditional-dashboard/1.0'}
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
                    
                    return sorted(usd_markets)  # Return ALL USD markets
            
            # Fallback to major USD markets
            return ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD", "ADA-USD", "DOT-USD", "LINK-USD"]
            
        except Exception as e:
            self.console.print(f"[yellow]⚠️  Error fetching markets: {e}, using fallback[/yellow]")
            return ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD", "ADA-USD", "DOT-USD", "LINK-USD"]
    
    def start(self):
        """Start the traditional sniper accuracy validation dashboard"""
        if not self.stream.connect():
            self.console.print("[red]❌ Failed to connect to dYdX stream[/red]")
            return
        
        self.console.print("[green]🎯 Traditional Sniper Dashboard Starting...[/green]")
        self.console.print("[yellow]📊 Tracking signals with traditional score ≥ 80 and measuring outcomes...[/yellow]")
        
        # Subscribe to orderbook streams for all markets
        for market in self.usd_markets:
            self._subscribe_to_market(market)
        
        # Start outcome tracking loop
        import threading
        outcome_thread = threading.Thread(target=self._outcome_tracking_loop, daemon=True)
        outcome_thread.start()
        
        # Start dashboard display
        with Live(self._create_dashboard_layout(), refresh_per_second=1) as live:
            try:
                while self.running:
                    time.sleep(1)
                    live.update(self._create_dashboard_layout())
            except KeyboardInterrupt:
                pass
        
        self.console.print("\n[yellow]🛑 Traditional Sniper Dashboard stopped[/yellow]")
    
    def _subscribe_to_market(self, market):
        """Subscribe to orderbook stream for a specific market"""
        try:
            orderbook_stream = self.stream.get_orderbook_observable(market)
            orderbook_stream.subscribe(
                on_next=lambda data, m=market: self._process_market_data(data, m),
                on_error=lambda e, m=market: self.console.print(f"[red]❌ Stream error for {m}: {e}[/red]")
            )
        except Exception as e:
            self.console.print(f"[red]❌ Failed to subscribe to {market}: {e}[/red]")
    
    def _process_market_data(self, orderbook_data, market):
        """Process orderbook data and check for 80+ traditional sniper signals"""
        if not orderbook_data or 'bids' not in orderbook_data or 'asks' not in orderbook_data:
            return

        if not orderbook_data['bids'] or not orderbook_data['asks']:
            return

        # Store current market data
        self.market_current_data[market] = {
            'orderbook': orderbook_data,
            'timestamp': datetime.now(),
            'price': (float(orderbook_data['bids'][0]['price']) + float(orderbook_data['asks'][0]['price'])) / 2
        }

        # Calculate traditional sniper score
        traditional_metrics = self._calculate_traditional_metrics(orderbook_data)
        sniper_score = self._calculate_traditional_sniper_score(traditional_metrics)

        # Only take action if this market does not already have an active signal
        if sniper_score >= 80.0 and market not in self.markets_with_active_signal:
            signal = TraditionalSniperSignal(
                market=market,
                timestamp=datetime.now(),
                score=sniper_score,
                signal_price=self.market_current_data[market]['price'],
                traditional_metrics=traditional_metrics.copy()
            )

            self.active_signals.append(signal)
            self.accuracy_stats['total_signals'] += 1
            self.market_performance[market]['signals'] += 1

            # Mark this market as having an active signal
            self.markets_with_active_signal.add(market)
            # Signal detected - tracked silently for dashboard display
    
    def _outcome_tracking_loop(self):
        """Background loop to track outcomes of active signals"""
        while self.running:
            try:
                current_time = datetime.now()

                # Check all active signals for outcome measurement opportunities
                signals_to_complete = []

                for signal in self.active_signals:
                    time_elapsed = (current_time - signal.timestamp).total_seconds()

                    # Measure outcomes at different timeframes
                    timeframes = [
                        (60, "1min"),
                        (300, "5min"),
                        (900, "15min"),
                        (1800, "30min")
                    ]

                    for duration, label in timeframes:
                        if (duration <= time_elapsed and
                            label not in signal.outcomes and
                            signal.market in self.market_current_data):

                            outcome = self._measure_signal_outcome(signal, duration, label)
                            signal.outcomes[label] = outcome

                    # Mark signal as complete after 30 minutes
                    if time_elapsed >= 1800 and not signal.is_complete:
                        signal.is_complete = True
                        signals_to_complete.append(signal)

                # Move completed signals
                for signal in signals_to_complete:
                    self.active_signals.remove(signal)
                    self.completed_signals.append(signal)
                    self._update_accuracy_stats(signal)
                    # Remove market from active set so it can trigger again
                    if signal.market in self.markets_with_active_signal:
                        self.markets_with_active_signal.remove(signal.market)

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                # Silently handle outcome tracking errors
                time.sleep(5)
    
    def _measure_signal_outcome(self, signal: TraditionalSniperSignal, duration: int, timeframe: str) -> SignalOutcome:
        """Measure the outcome of a signal after a specific duration"""
        try:
            current_data = self.market_current_data.get(signal.market)
            if not current_data:
                return self._empty_outcome(timeframe)
            
            current_price = current_data['price']
            price_change_pct = ((current_price - signal.signal_price) / signal.signal_price) * 100
            
            # Calculate other outcome metrics
            current_orderbook = current_data['orderbook']
            current_spread = float(current_orderbook['asks'][0]['price']) - float(current_orderbook['bids'][0]['price'])
            signal_spread = signal.traditional_metrics.get('spread_absolute', current_spread)
            spread_change_pct = ((current_spread - signal_spread) / signal_spread) * 100 if signal_spread > 0 else 0
            
            # Estimate if execution would have been feasible
            execution_feasible = current_spread < signal_spread * 2  # Spread didn't blow out
            
            # Estimate profit (assuming we could capture some of the spread tightening)
            profit_estimate = price_change_pct * 0.7 if execution_feasible else price_change_pct * 0.3
            
            return SignalOutcome(
                timeframe=timeframe,
                price_change_pct=price_change_pct,
                spread_change_pct=spread_change_pct,
                volume_change_pct=0.0,  # Would need volume data
                opportunity_duration=duration,
                execution_feasible=execution_feasible,
                profit_estimate=profit_estimate
            )
            
        except Exception as e:
            return self._empty_outcome(timeframe)
    
    def _empty_outcome(self, timeframe: str) -> SignalOutcome:
        """Return empty outcome when measurement fails"""
        return SignalOutcome(
            timeframe=timeframe,
            price_change_pct=0.0,
            spread_change_pct=0.0,
            volume_change_pct=0.0,
            opportunity_duration=0.0,
            execution_feasible=False,
            profit_estimate=0.0
        )
    
    def _update_accuracy_stats(self, signal: TraditionalSniperSignal):
        """Update overall accuracy statistics with completed signal"""
        if not signal.outcomes:
            return
        
        # Use 5-minute outcome as primary measure
        primary_outcome = signal.outcomes.get("5min")
        if not primary_outcome:
            return
        
        # Update global stats
        if primary_outcome.profit_estimate > 0:
            self.accuracy_stats['profitable_signals'] += 1
        
        self.accuracy_stats['accuracy_rate'] = (self.accuracy_stats['profitable_signals'] / 
                                               self.accuracy_stats['total_signals']) * 100
        
        # Update market-specific stats
        market_stats = self.market_performance[signal.market]
        if primary_outcome.profit_estimate > 0:
            market_stats['profitable'] += 1
        
        market_stats['accuracy'] = (market_stats['profitable'] / market_stats['signals']) * 100
        
        # Update return statistics
        all_returns = [s.outcomes.get("5min", self._empty_outcome("5min")).profit_estimate 
                      for s in self.completed_signals if s.outcomes.get("5min")]
        
        if all_returns:
            self.accuracy_stats['avg_return'] = statistics.mean(all_returns)
            self.accuracy_stats['best_return'] = max(all_returns)
            self.accuracy_stats['worst_return'] = min(all_returns)
    
    def _create_dashboard_layout(self):
        """Create the main traditional dashboard layout"""
        # Header
        header = Panel(
            f"[bold cyan]🎯 TRADITIONAL SNIPER ACCURACY DASHBOARD[/bold cyan]\n"
            f"[white]Traditional metrics only • 80+ threshold • Real-time outcome tracking[/white]",
            title="Traditional Methodology Validation Tool",
            border_style="cyan"
        )
        
        # Active signals table
        active_signals_table = self._create_active_signals_table()
        accuracy_stats_table = self._create_accuracy_stats_table()
        
        # Completed signals table
        completed_signals_table = self._create_completed_signals_table()
        market_performance_table = self._create_market_performance_table()
        
        # Layout
        top_row = Columns([
            Panel(active_signals_table, title="🚨 Active Signals (80+)", border_style="yellow", width=300),
            Panel(accuracy_stats_table, title="📊 Accuracy Stats", border_style="green", width=200)
        ])
        
        bottom_row = Columns([
            Panel(completed_signals_table, title="✅ Recent Outcomes", border_style="blue", width=300),
            Panel(market_performance_table, title="🏆 Market Performance", border_style="magenta", width=200)
        ])
        
        return Columns([header, top_row, bottom_row], equal=False)
    
    def _create_active_signals_table(self):
        """Create table showing currently active 80+ traditional signals"""
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("Market", style="white", width=60)
        table.add_column("Score", style="green", width=60)
        table.add_column("Price", style="cyan", width=60)
        table.add_column("Age", style="yellow", width=60)
        table.add_column("1min", style="blue", width=60)
        table.add_column("5min", style="blue", width=60)
        table.add_column("15min", style="blue", width=60)
        
        if not self.active_signals:
            table.add_row("--", "--", "--", "--", "--", "--", "--")
            return table
        
        current_time = datetime.now()
        
        # Show all active signals (not limited to top 10)
        for signal in sorted(self.active_signals, key=lambda s: s.timestamp, reverse=True):
            age = int((current_time - signal.timestamp).total_seconds())
            age_str = f"{age//60}m{age%60}s"
            
            # Get outcome data if available
            outcome_1min = signal.outcomes.get("1min")
            outcome_5min = signal.outcomes.get("5min")
            outcome_15min = signal.outcomes.get("15min")
            
            result_1min = f"{outcome_1min.profit_estimate:+.1f}%" if outcome_1min else "--"
            result_5min = f"{outcome_5min.profit_estimate:+.1f}%" if outcome_5min else "--"
            result_15min = f"{outcome_15min.profit_estimate:+.1f}%" if outcome_15min else "--"
            
            table.add_row(
                signal.market,
                f"{signal.score:.1f}",
                f"${signal.signal_price:.2f}",
                age_str,
                result_1min,
                result_5min,
                result_15min
            )
        
        return table
    
    def _create_accuracy_stats_table(self):
        """Create overall accuracy statistics table"""
        table = Table(show_header=False, show_edge=False, pad_edge=False, box=None)
        table.add_column("Metric", style="cyan", width=60)
        table.add_column("Value", style="white", width=60)
        
        table.add_row("📊 Total Signals", str(self.accuracy_stats['total_signals']))
        table.add_row("✅ Profitable", str(self.accuracy_stats['profitable_signals']))
        
        accuracy_color = "green" if self.accuracy_stats['accuracy_rate'] > 60 else "yellow" if self.accuracy_stats['accuracy_rate'] > 40 else "red"
        table.add_row("🎯 Accuracy Rate", f"[{accuracy_color}]{self.accuracy_stats['accuracy_rate']:.1f}%[/{accuracy_color}]")
        
        avg_return_color = "green" if self.accuracy_stats['avg_return'] > 0 else "red"
        table.add_row("📈 Avg Return", f"[{avg_return_color}]{self.accuracy_stats['avg_return']:+.2f}%[/{avg_return_color}]")
        
        table.add_row("⬆️ Best Return", f"[green]{self.accuracy_stats['best_return']:+.2f}%[/green]")
        table.add_row("⬇️ Worst Return", f"[red]{self.accuracy_stats['worst_return']:+.2f}%[/red]")
        
        # Signal frequency
        active_count = len(self.active_signals)
        table.add_row("🔴 Active Now", str(active_count))
        
        return table
    
    def _create_completed_signals_table(self):
        """Create table showing recent completed signals"""
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Market", style="white", width=60)
        table.add_column("Score", style="green", width=60)
        table.add_column("1min", style="blue", width=60)
        table.add_column("5min", style="yellow", width=60)
        table.add_column("15min", style="cyan", width=60)
        table.add_column("30min", style="magenta", width=60)
        table.add_column("Feasible", style="white", width=60)
        
        if not self.completed_signals:
            table.add_row("--", "--", "--", "--", "--", "--", "--")
            return table
        
        # Show most recent completed signals
        for signal in sorted(self.completed_signals, key=lambda s: s.timestamp, reverse=True):
            outcome_1min = signal.outcomes.get("1min", self._empty_outcome("1min"))
            outcome_5min = signal.outcomes.get("5min", self._empty_outcome("5min"))
            outcome_15min = signal.outcomes.get("15min", self._empty_outcome("15min"))
            outcome_30min = signal.outcomes.get("30min", self._empty_outcome("30min"))
            
            # Color code results
            def format_result(outcome):
                if outcome.profit_estimate > 0.5:
                    return f"[bright_green]{outcome.profit_estimate:+.1f}%[/bright_green]"
                elif outcome.profit_estimate > 0:
                    return f"[green]{outcome.profit_estimate:+.1f}%[/green]"
                elif outcome.profit_estimate > -0.5:
                    return f"[yellow]{outcome.profit_estimate:+.1f}%[/yellow]"
                else:
                    return f"[red]{outcome.profit_estimate:+.1f}%[/red]"
            
            feasible = "✅" if outcome_5min.execution_feasible else "❌"
            
            table.add_row(
                signal.market,
                f"{signal.score:.1f}",
                format_result(outcome_1min),
                format_result(outcome_5min),
                format_result(outcome_15min),
                format_result(outcome_30min),
                feasible
            )
        
        return table
    
    def _create_market_performance_table(self):
        """Create market-specific performance breakdown"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Market", style="white", width=60)
        table.add_column("Signals", style="cyan", width=60)
        table.add_column("Accuracy", style="green", width=60)
        table.add_column("Avg Return", style="yellow", width=60)
        
        if not self.market_performance:
            table.add_row("--", "--", "--", "--")
            return table
        
        # Sort markets by number of signals
        sorted_markets = sorted(self.market_performance.items(), 
                               key=lambda x: x[1]['signals'], reverse=True)
        
        for market, stats in sorted_markets:
            if stats['signals'] == 0:
                continue
                
            accuracy_color = "green" if stats['accuracy'] > 60 else "yellow" if stats['accuracy'] > 40 else "red"
            return_color = "green" if stats['avg_return'] > 0 else "red"
            
            table.add_row(
                market,
                str(stats['signals']),
                f"[{accuracy_color}]{stats['accuracy']:.1f}%[/{accuracy_color}]",
                f"[{return_color}]{stats['avg_return']:+.2f}%[/{return_color}]"
            )
        
        return table
    
    def _calculate_traditional_metrics(self, orderbook_data):
        """Calculate traditional order book metrics"""
        try:
            bids = orderbook_data['bids']
            asks = orderbook_data['asks']
            
            best_bid = float(bids[0]['price'])
            best_ask = float(asks[0]['price'])
            spread_absolute = best_ask - best_bid
            mid_price = (best_bid + best_ask) / 2
            spread_percentage = (spread_absolute / mid_price) * 100
            
            bid_depth = sum(float(level['size']) * float(level['price']) for level in bids[:5])
            ask_depth = sum(float(level['size']) * float(level['price']) for level in asks[:5])
            total_depth = bid_depth + ask_depth
            
            imbalance_ratio = bid_depth / ask_depth if ask_depth > 0 else 1
            imbalance_percentage = ((bid_depth - ask_depth) / total_depth) * 100 if total_depth > 0 else 0
            
            return {
                'spread_absolute': spread_absolute,
                'spread_percentage': spread_percentage,
                'depth_total': total_depth,
                'imbalance_percentage': imbalance_percentage,
                'price_impact_avg': 0.1  # Simplified
            }
            
        except (ValueError, KeyError, IndexError, ZeroDivisionError):
            return {'spread_absolute': 0, 'spread_percentage': 0, 'depth_total': 0, 
                   'imbalance_percentage': 0, 'price_impact_avg': 0}
    
    def _calculate_traditional_sniper_score(self, traditional_metrics):
        """Calculate sniper score using ONLY traditional metrics (100% weight)"""
        try:
            # Traditional components (100% weight - no innovative metrics)
            spread_score = max(0, min(100, 100 * (0.01 / traditional_metrics['spread_percentage']) ** 0.5)) if traditional_metrics['spread_percentage'] > 0 else 0
            depth_score = max(0, min(100, 25 * (1 + 3 * (traditional_metrics['depth_total'] / 10000) ** 0.3)))
            imbalance_score = 80 - abs(traditional_metrics['imbalance_percentage']) * 2
            impact_score = max(0, min(100, 100 * (1 - traditional_metrics['price_impact_avg'])))
            
            # Traditional score gets 100% weight (vs 60% in the full version)
            traditional_score = (spread_score * 0.3 + depth_score * 0.25 + 
                               imbalance_score * 0.25 + impact_score * 0.2)
            
            return max(0, min(100, traditional_score))
            
        except Exception:
            return 0
    
    def _signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False


def main():
    """Main entry point"""
    dashboard = TraditionalSniperDashboard()
    dashboard.start()


if __name__ == "__main__":
    main()
