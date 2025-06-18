"""
Layer 4 Signals Dashboard - MINIMAL implementation to pass tests.
"""

from rich.console import Console
from rich.table import Table


class SignalsDashboard:
    """Minimal SignalsDashboard to pass tests."""
    
    def __init__(self):
        """Initialize with console."""
        self.console = Console()
    
    def _get_color_for_score(self, score: float) -> str:
        """Return color based on signal score ranges."""
        if score > 80:
            return "green"  # High performance
        elif score >= 50:
            return "yellow"  # Medium performance
        else:
            return "red"  # Low performance
    
    def render_signals(self, signal_set) -> str:
        """Render signal data using actual signal_set values."""
        return f"{signal_set.market} {signal_set.momentum} {signal_set.volume}"
    
    def render_rich_signals(self, signal_set) -> str:
        """Render signals with Rich formatting using actual data."""
        return f"Signal Momentum {signal_set.momentum}"
    
    def render_table(self, signal_set, console: Console) -> None:
        """Render signals as a Rich table with all signal types."""
        table = Table()
        table.add_column("Signal Type")
        table.add_column("Value")
        
        table.add_row("Market", signal_set.market)
        table.add_row("Momentum", str(signal_set.momentum))
        table.add_row("Volume", str(signal_set.volume))
        table.add_row("Volatility", str(signal_set.volatility))
        table.add_row("Orderbook", str(signal_set.orderbook))
        
        console.print(table)
    
    def render_colored_table(self, signal_set, console: Console) -> None:
        """Render signals as a Rich table with color coding by score ranges."""
        from rich.text import Text
        
        table = Table()
        table.add_column("Signal Type")
        table.add_column("Value")
        
        # Add rows with colored signal values
        table.add_row("Market", signal_set.market)
        table.add_row("Momentum", Text(str(signal_set.momentum), style=self._get_color_for_score(signal_set.momentum)))
        table.add_row("Volume", Text(str(signal_set.volume), style=self._get_color_for_score(signal_set.volume)))
        table.add_row("Volatility", Text(str(signal_set.volatility), style=self._get_color_for_score(signal_set.volatility)))
        table.add_row("Orderbook", Text(str(signal_set.orderbook), style=self._get_color_for_score(signal_set.orderbook)))
        
        console.print(table)
    
    def render_multi_market_table(self, signal_sets, console: Console) -> None:
        """Render multiple markets in a single signals table."""
        from rich.text import Text
        
        table = Table()
        table.add_column("Market")
        table.add_column("Momentum")
        table.add_column("Volume")
        table.add_column("Volatility") 
        table.add_column("Orderbook")
        
        # Add a row for each market
        for signal_set in signal_sets:
            table.add_row(
                signal_set.market,
                Text(str(signal_set.momentum), style=self._get_color_for_score(signal_set.momentum)),
                Text(str(signal_set.volume), style=self._get_color_for_score(signal_set.volume)),
                Text(str(signal_set.volatility), style=self._get_color_for_score(signal_set.volatility)),
                Text(str(signal_set.orderbook), style=self._get_color_for_score(signal_set.orderbook))
            )
        
        console.print(table)
    
    def render_summary_statistics(self, signal_sets, console: Console) -> None:
        """Render summary statistics for signal performance."""
        from rich.text import Text
        
        table = Table(title="Summary Statistics")
        table.add_column("Statistic")
        table.add_column("Momentum")
        table.add_column("Volume")
        table.add_column("Volatility")
        table.add_column("Orderbook")
        
        # Calculate averages
        momentum_avg = sum(s.momentum for s in signal_sets) / len(signal_sets)
        volume_avg = sum(s.volume for s in signal_sets) / len(signal_sets)
        volatility_avg = sum(s.volatility for s in signal_sets) / len(signal_sets)
        orderbook_avg = sum(s.orderbook for s in signal_sets) / len(signal_sets)
        
        # Add average row with color coding
        table.add_row(
            "Average",
            Text(f"{momentum_avg:.1f}", style=self._get_color_for_score(momentum_avg)),
            Text(f"{volume_avg:.1f}", style=self._get_color_for_score(volume_avg)),
            Text(f"{volatility_avg:.1f}", style=self._get_color_for_score(volatility_avg)),
            Text(f"{orderbook_avg:.1f}", style=self._get_color_for_score(orderbook_avg))
        )
        
        # Add markets count
        table.add_row("Markets", str(len(signal_sets)), "", "", "")
        
        console.print(table)
    
    def render_table_with_timestamp(self, signal_set, console: Console) -> None:
        """Render signals table with formatted timestamp included."""
        from rich.text import Text
        
        table = Table()
        table.add_column("Signal Type")
        table.add_column("Value")
        
        # Add timestamp at the top
        formatted_time = signal_set.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        table.add_row("Timestamp", formatted_time)
        
        # Add market and signal data with color coding
        table.add_row("Market", signal_set.market)
        table.add_row("Momentum", Text(str(signal_set.momentum), style=self._get_color_for_score(signal_set.momentum)))
        table.add_row("Volume", Text(str(signal_set.volume), style=self._get_color_for_score(signal_set.volume)))
        table.add_row("Volatility", Text(str(signal_set.volatility), style=self._get_color_for_score(signal_set.volatility)))
        table.add_row("Orderbook", Text(str(signal_set.orderbook), style=self._get_color_for_score(signal_set.orderbook)))
        
        console.print(table)
    
    def render_table_with_thresholds(self, signal_set, thresholds, console: Console) -> None:
        """Render signals table with configurable threshold indicators."""
        from rich.text import Text
        
        table = Table()
        table.add_column("Signal Type")
        table.add_column("Value")
        table.add_column("Threshold")
        
        # Helper function to get threshold indicator
        def get_threshold_indicator(score: float, thresholds: dict) -> str:
            """Return threshold indicator based on score."""
            if score >= thresholds["high"]:
                return "HIGH ⭐"
            elif score >= thresholds["medium"]:
                return "MED ↗"
            elif score >= thresholds["low"]:
                return "LOW ↘"
            else:
                return "VERY LOW ⚠"
        
        # Add rows with threshold indicators
        table.add_row("Market", signal_set.market, "")
        table.add_row("Momentum", 
                     Text(str(signal_set.momentum), style=self._get_color_for_score(signal_set.momentum)),
                     get_threshold_indicator(signal_set.momentum, thresholds))
        table.add_row("Volume", 
                     Text(str(signal_set.volume), style=self._get_color_for_score(signal_set.volume)),
                     get_threshold_indicator(signal_set.volume, thresholds))
        table.add_row("Volatility", 
                     Text(str(signal_set.volatility), style=self._get_color_for_score(signal_set.volatility)),
                     get_threshold_indicator(signal_set.volatility, thresholds))
        table.add_row("Orderbook", 
                     Text(str(signal_set.orderbook), style=self._get_color_for_score(signal_set.orderbook)),
                     get_threshold_indicator(signal_set.orderbook, thresholds))
        
        console.print(table)
    
    def render_table_with_trends(self, current_signals, previous_signals, console: Console) -> None:
        """Render signals table with trend indicators comparing current vs previous."""
        from rich.text import Text
        
        table = Table()
        table.add_column("Signal Type")
        table.add_column("Current Value")
        table.add_column("Trend")
        
        # Helper function to get trend indicator
        def get_trend_indicator(current: float, previous: float) -> str:
            """Return trend indicator based on value comparison."""
            diff = current - previous
            if diff > 5:
                return "↑↑ STRONG UP"
            elif diff > 0:
                return "↑ UP"
            elif diff < -5:
                return "↓↓ STRONG DOWN"
            elif diff < 0:
                return "↓ DOWN"
            else:
                return "→ STABLE"
        
        # Add rows with trend indicators
        table.add_row("Market", current_signals.market, "")
        table.add_row("Momentum", 
                     Text(str(current_signals.momentum), style=self._get_color_for_score(current_signals.momentum)),
                     get_trend_indicator(current_signals.momentum, previous_signals.momentum))
        table.add_row("Volume", 
                     Text(str(current_signals.volume), style=self._get_color_for_score(current_signals.volume)),
                     get_trend_indicator(current_signals.volume, previous_signals.volume))
        table.add_row("Volatility", 
                     Text(str(current_signals.volatility), style=self._get_color_for_score(current_signals.volatility)),
                     get_trend_indicator(current_signals.volatility, previous_signals.volatility))
        table.add_row("Orderbook", 
                     Text(str(current_signals.orderbook), style=self._get_color_for_score(current_signals.orderbook)),
                     get_trend_indicator(current_signals.orderbook, previous_signals.orderbook))
        
        console.print(table)
