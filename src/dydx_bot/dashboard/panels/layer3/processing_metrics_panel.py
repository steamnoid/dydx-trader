"""
Processing Metrics Panel - Layer 3 Dashboard

Standalone Rich dashboard component displaying real-time data processing and performance metrics.
Autonomous forever-running panel using real dYdX API data processing metrics.
"""

import asyncio
import signal
import sys
import time
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.live import Live
from rich.align import Align
from rich.text import Text

from ....data.processor import MarketDataProcessor


class ProcessingMetricsPanel:
    """
    Autonomous Rich dashboard panel for data processing metrics.
    
    Features:
    - Real-time processing performance metrics
    - Message throughput statistics
    - Latency distribution analysis
    - Error tracking and uptime monitoring
    - Data generation counters
    """
    
    def __init__(self, market_id: str = "BTC-USD"):
        self.market_id = market_id
        self.console = Console()
        self.processor: Optional[MarketDataProcessor] = None
        self.running = False
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.console.print("\n[yellow]Shutting down Processing Metrics Panel...[/yellow]")
        self.running = False
    
    async def initialize(self):
        """Initialize the data processor"""
        self.processor = MarketDataProcessor(market_id=self.market_id)
        await self.processor.initialize()
    
    def _create_header_panel(self) -> Panel:
        """Create the header panel with basic info"""
        header_table = Table(show_header=False, box=None, padding=(0, 1))
        header_table.add_column("Key", style="bold cyan")
        header_table.add_column("Value", style="white")
        
        header_table.add_row("Panel", "Processing Metrics Dashboard")
        header_table.add_row("Market", self.market_id)
        header_table.add_row("Status", "[green]LIVE[/green]")
        header_table.add_row("Update Freq", "5 seconds")
        
        return Panel(
            Align.center(header_table),
            title="[bold blue]Layer 3 - Processing Metrics[/bold blue]",
            border_style="blue"
        )
    
    def _create_throughput_panel(self) -> Panel:
        """Create throughput metrics panel"""
        if not self.processor:
            return Panel("[red]Processor not initialized[/red]", title="Throughput")
        
        metrics = self.processor.get_processing_metrics()
        uptime = metrics.get_uptime_seconds()
        
        # Calculate rates per second
        msg_rate = metrics.messages_processed / max(uptime, 1)
        ohlcv_rate = metrics.ohlcv_generated / max(uptime, 1)
        orderbook_rate = metrics.orderbook_updates / max(uptime, 1)
        
        throughput_table = Table(show_header=True, header_style="bold magenta")
        throughput_table.add_column("Metric", style="cyan")
        throughput_table.add_column("Total", justify="right", style="yellow")
        throughput_table.add_column("Rate/sec", justify="right", style="green")
        
        throughput_table.add_row(
            "Messages Processed",
            f"{metrics.messages_processed:,}",
            f"{msg_rate:.2f}"
        )
        throughput_table.add_row(
            "OHLCV Candles Generated",
            f"{metrics.ohlcv_generated:,}",
            f"{ohlcv_rate:.4f}"
        )
        throughput_table.add_row(
            "Orderbook Updates",
            f"{metrics.orderbook_updates:,}",
            f"{orderbook_rate:.2f}"
        )
        
        return Panel(
            throughput_table,
            title="[bold magenta]Throughput Metrics[/bold magenta]",
            border_style="magenta"
        )
    
    def _create_latency_panel(self) -> Panel:
        """Create latency analysis panel"""
        if not self.processor:
            return Panel("[red]Processor not initialized[/red]", title="Latency")
        
        metrics = self.processor.get_processing_metrics()
        
        latency_table = Table(show_header=True, header_style="bold yellow")
        latency_table.add_column("Statistic", style="cyan")
        latency_table.add_column("Value (ms)", justify="right", style="yellow")
        latency_table.add_column("Status", justify="center")
        
        avg_latency = metrics.get_avg_latency_ms()
        p95_latency = metrics.get_p95_latency_ms()
        sample_count = len(metrics.processing_latency_ms)
        
        # Determine status colors based on latency thresholds
        avg_status = "[green]GOOD[/green]" if avg_latency < 10 else "[yellow]OK[/yellow]" if avg_latency < 50 else "[red]HIGH[/red]"
        p95_status = "[green]GOOD[/green]" if p95_latency < 20 else "[yellow]OK[/yellow]" if p95_latency < 100 else "[red]HIGH[/red]"
        
        latency_table.add_row(
            "Average Latency",
            f"{avg_latency:.2f}",
            avg_status
        )
        latency_table.add_row(
            "95th Percentile",
            f"{p95_latency:.2f}",
            p95_status
        )
        latency_table.add_row(
            "Sample Count",
            f"{sample_count:,}",
            "[blue]INFO[/blue]"
        )
        
        # Recent latency trend (last 10 samples)
        recent_samples = metrics.processing_latency_ms[-10:] if metrics.processing_latency_ms else []
        if recent_samples:
            recent_avg = sum(recent_samples) / len(recent_samples)
            trend_status = "[green]STABLE[/green]" if abs(recent_avg - avg_latency) < 5 else "[yellow]VARYING[/yellow]"
            latency_table.add_row(
                "Recent Trend (10 samples)",
                f"{recent_avg:.2f}",
                trend_status
            )
        
        return Panel(
            latency_table,
            title="[bold yellow]Latency Analysis[/bold yellow]",
            border_style="yellow"
        )
    
    def _create_reliability_panel(self) -> Panel:
        """Create reliability and error tracking panel"""
        if not self.processor:
            return Panel("[red]Processor not initialized[/red]", title="Reliability")
        
        metrics = self.processor.get_processing_metrics()
        uptime = metrics.get_uptime_seconds()
        
        # Calculate error rate
        total_operations = metrics.messages_processed
        error_rate = (metrics.error_count / max(total_operations, 1)) * 100 if total_operations > 0 else 0
        success_rate = 100 - error_rate
        
        reliability_table = Table(show_header=True, header_style="bold red")
        reliability_table.add_column("Metric", style="cyan")
        reliability_table.add_column("Value", justify="right")
        reliability_table.add_column("Status", justify="center")
        
        # Uptime formatting
        uptime_hours = uptime / 3600
        uptime_str = f"{uptime_hours:.2f}h" if uptime_hours >= 1 else f"{uptime:.0f}s"
        uptime_status = "[green]STABLE[/green]" if uptime > 300 else "[yellow]STARTING[/yellow]"
        
        # Success rate status
        success_status = "[green]EXCELLENT[/green]" if success_rate >= 99 else "[yellow]GOOD[/yellow]" if success_rate >= 95 else "[red]POOR[/red]"
        
        reliability_table.add_row(
            "Uptime",
            f"[white]{uptime_str}[/white]",
            uptime_status
        )
        reliability_table.add_row(
            "Total Errors",
            f"[white]{metrics.error_count:,}[/white]",
            "[red]ERRORS[/red]" if metrics.error_count > 0 else "[green]CLEAN[/green]"
        )
        reliability_table.add_row(
            "Error Rate",
            f"[white]{error_rate:.3f}%[/white]",
            "[red]HIGH[/red]" if error_rate > 1 else "[yellow]LOW[/yellow]" if error_rate > 0.1 else "[green]MINIMAL[/green]"
        )
        reliability_table.add_row(
            "Success Rate",
            f"[white]{success_rate:.3f}%[/white]",
            success_status
        )
        
        return Panel(
            reliability_table,
            title="[bold red]Reliability & Errors[/bold red]",
            border_style="red"
        )
    
    def _create_data_status_panel(self) -> Panel:
        """Create data status and connectivity panel"""
        if not self.processor:
            return Panel("[red]Processor not initialized[/red]", title="Data Status")
        
        data_table = Table(show_header=True, header_style="bold green")
        data_table.add_column("Component", style="cyan")
        data_table.add_column("Status", justify="center")
        data_table.add_column("Last Update")
        
        # Check processor status
        processor_status = "[green]RUNNING[/green]" if self.processor.is_running() else "[red]STOPPED[/red]"
        
        # Check recent data activity
        metrics = self.processor.get_processing_metrics()
        latest_orderbook = self.processor.get_latest_orderbook()
        latest_ohlcv = self.processor.get_latest_ohlcv(count=1)
        
        # Orderbook status
        orderbook_status = "[green]ACTIVE[/green]" if latest_orderbook else "[yellow]NO DATA[/yellow]"
        orderbook_time = time.strftime("%H:%M:%S", time.localtime(latest_orderbook.timestamp)) if latest_orderbook else "N/A"
        
        # OHLCV status
        ohlcv_status = "[green]ACTIVE[/green]" if latest_ohlcv else "[yellow]NO DATA[/yellow]"
        ohlcv_time = time.strftime("%H:%M:%S", time.localtime(latest_ohlcv[0].timestamp)) if latest_ohlcv else "N/A"
        
        # WebSocket connection status
        ws_status = "[green]CONNECTED[/green]" if self.processor.client and self.processor.client.indexer_socket else "[red]DISCONNECTED[/red]"
        
        data_table.add_row(
            "Data Processor",
            processor_status,
            "Active"
        )
        data_table.add_row(
            "WebSocket",
            ws_status,
            "Live"
        )
        data_table.add_row(
            "Orderbook Feed",
            orderbook_status,
            orderbook_time
        )
        data_table.add_row(
            "OHLCV Generation",
            ohlcv_status,
            ohlcv_time
        )
        
        return Panel(
            data_table,
            title="[bold green]Data Status[/bold green]",
            border_style="green"
        )
    
    def _create_performance_progress(self) -> Panel:
        """Create performance progress indicators"""
        if not self.processor:
            return Panel("[red]Processor not initialized[/red]", title="Performance")
        
        metrics = self.processor.get_processing_metrics()
        
        # Create progress bars for key metrics
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=20),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            expand=True
        ) as progress:
            
            # Messages processed (normalize to 10k for display)
            msg_progress = min((metrics.messages_processed / 10000) * 100, 100)
            progress.add_task("Messages (10k target)", completed=msg_progress)
            
            # Error rate (invert - lower is better, show as success rate)
            total_ops = max(metrics.messages_processed, 1)
            success_rate = ((total_ops - metrics.error_count) / total_ops) * 100
            progress.add_task("Success Rate", completed=success_rate)
            
            # Latency performance (invert - lower latency is better performance)
            avg_latency = metrics.get_avg_latency_ms()
            latency_score = max(0, 100 - (avg_latency * 2))  # 50ms = 0% score
            progress.add_task("Latency Score", completed=latency_score)
            
            # Uptime progress (24h target)
            uptime_hours = metrics.get_uptime_seconds() / 3600
            uptime_progress = min((uptime_hours / 24) * 100, 100)
            progress.add_task("Uptime (24h target)", completed=uptime_progress)
            
            return Panel(
                progress.renderable,
                title="[bold cyan]Performance Indicators[/bold cyan]",
                border_style="cyan"
            )
    
    def create_layout(self) -> Layout:
        """Create the main dashboard layout"""
        layout = Layout()
        
        # Split into header and body
        layout.split_column(
            Layout(name="header", size=7),
            Layout(name="body")
        )
        
        # Split body into two columns
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Split left column into top and bottom
        layout["left"].split_column(
            Layout(name="throughput", size=9),
            Layout(name="latency", size=10)
        )
        
        # Split right column into top and bottom
        layout["right"].split_column(
            Layout(name="reliability", size=9),
            Layout(name="data_status", size=10)
        )
        
        # Add panels to layout
        layout["header"].update(self._create_header_panel())
        layout["throughput"].update(self._create_throughput_panel())
        layout["latency"].update(self._create_latency_panel())
        layout["reliability"].update(self._create_reliability_panel())
        layout["data_status"].update(self._create_data_status_panel())
        
        return layout
    
    async def run(self):
        """Run the dashboard with live updates"""
        await self.initialize()
        self.running = True
        
        with Live(
            self.create_layout(),
            console=self.console,
            refresh_per_second=0.5,  # Moderate refresh rate for metrics
            screen=True
        ) as live:
            
            while self.running:
                try:
                    # Update the layout
                    live.update(self.create_layout())
                    
                    # Wait for next update cycle
                    await asyncio.sleep(5)  # 5-second update cycle
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    # Continue running on errors - resilient dashboard
                    await asyncio.sleep(1)
        
        # Cleanup
        if self.processor:
            await self.processor.shutdown()


async def main():
    """Main entry point for standalone execution"""
    panel = ProcessingMetricsPanel()
    
    try:
        await panel.run()
    except KeyboardInterrupt:
        print("\nShutdown complete.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
