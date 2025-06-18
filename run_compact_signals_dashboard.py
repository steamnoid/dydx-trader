#!/usr/bin/env python3
"""
Compact Layer 4 Signals Dashboard - Space-efficient design with dense information display.
"""

import asyncio
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from dydx_v4_client.indexer.rest.indexer_client import IndexerClient

from src.dydx_bot.dashboard.signals_dashboard import SignalsDashboard
from src.dydx_bot.signals.types import SignalSet


async def create_signal_from_market_data(market: str, market_data: dict) -> SignalSet:
    """Create a SignalSet from real market data."""
    # Use oracle price and volume data from dYdX API
    oracle_price = float(market_data.get('oraclePrice', 1000))
    volume_24h = float(market_data.get('volume24H', 1000000))
    price_change_24h = float(market_data.get('priceChange24H', 0))
    open_interest = float(market_data.get('openInterest', 1000000))
    
    # Calculate momentum from price change (scale to 0-100)
    momentum = (price_change_24h * 10) + 50  # Scale price change to 0-100
    momentum = max(0, min(100, momentum))
    
    # Calculate volume signal (normalized)
    volume_signal = min(100, volume_24h / 100000000)  # Scale volume to 0-100
    
    # Calculate volatility based on price change magnitude
    volatility = min(100, abs(price_change_24h * 20) + 30)  # Scale volatility to 0-100
    
    # Calculate orderbook signal based on open interest
    orderbook = min(100, open_interest / 50000000)  # Scale open interest to 0-100
    
    return SignalSet(
        market=market,
        momentum=momentum,
        volume=volume_signal,
        volatility=volatility,
        orderbook=orderbook,
        timestamp=datetime.utcnow(),
        metadata={
            "oracle_price": oracle_price,
            "volume_24h": volume_24h,
            "price_change_24h": price_change_24h,
            "open_interest": open_interest
        }
    )


def create_compact_signals_table(signal_sets):
    """Create a compact signals table with all data in minimal space."""
    table = Table(title="Live Signals", show_header=True, header_style="bold cyan", 
                 title_style="bold blue", box=None, padding=(0, 1))
    
    table.add_column("Market", style="white", width=8)
    table.add_column("Mom", justify="right", width=3)
    table.add_column("Vol", justify="right", width=3) 
    table.add_column("Vlt", justify="right", width=3)
    table.add_column("Ord", justify="right", width=3)
    table.add_column("Price", justify="right", width=8)
    table.add_column("24h%", justify="right", width=6)
    
    for signal_set in signal_sets:
        # Color code signals based on value ranges
        mom_color = "green" if signal_set.momentum > 70 else "yellow" if signal_set.momentum > 40 else "red"
        vol_color = "green" if signal_set.volume > 70 else "yellow" if signal_set.volume > 40 else "red"
        vlt_color = "green" if signal_set.volatility > 70 else "yellow" if signal_set.volatility > 40 else "red"
        ord_color = "green" if signal_set.orderbook > 70 else "yellow" if signal_set.orderbook > 40 else "red"
        
        # Get price and change from metadata
        price = signal_set.metadata.get('oracle_price', 0)
        change_24h = signal_set.metadata.get('price_change_24h', 0)
        change_color = "green" if change_24h > 0 else "red" if change_24h < 0 else "white"
        
        table.add_row(
            signal_set.market,
            Text(f"{signal_set.momentum:.0f}", style=mom_color),
            Text(f"{signal_set.volume:.0f}", style=vol_color),
            Text(f"{signal_set.volatility:.0f}", style=vlt_color),
            Text(f"{signal_set.orderbook:.0f}", style=ord_color),
            f"${price:,.0f}",
            Text(f"{change_24h:+.1f}%", style=change_color)
        )
    
    return table


def create_stats_panel(signal_sets):
    """Create a compact statistics panel."""
    if not signal_sets:
        return Panel("No data", title="Stats")
    
    avg_mom = sum(s.momentum for s in signal_sets) / len(signal_sets)
    avg_vol = sum(s.volume for s in signal_sets) / len(signal_sets)
    avg_vlt = sum(s.volatility for s in signal_sets) / len(signal_sets)
    avg_ord = sum(s.orderbook for s in signal_sets) / len(signal_sets)
    
    stats_text = f"""Markets: {len(signal_sets)}
Avg Mom: {avg_mom:.0f}
Avg Vol: {avg_vol:.0f}
Avg Vlt: {avg_vlt:.0f}
Avg Ord: {avg_ord:.0f}"""
    
    return Panel(stats_text, title="Stats", style="cyan")


def create_status_panel(update_count):
    """Create a compact status panel."""
    status_text = f"""dYdX v4 Layer 4
Updates: {update_count}
Time: {datetime.utcnow().strftime('%H:%M:%S')}
Status: ✅ Live"""
    
    return Panel(status_text, title="Status", style="green")


async def main():
    """Run the compact signals dashboard continuously."""
    console = Console()
    
    console.print("🚀 [bold blue]Compact dYdX v4 Signals Dashboard[/bold blue] 🚀")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]")
    
    try:
        # Create IndexerClient for real-time data
        client = IndexerClient(host="https://indexer.dydx.trade")
        update_count = 0
        
        # Continuous operation loop
        while True:
            try:
                # Fetch fresh market data
                markets_response = await client.markets.get_perpetual_markets()
                markets = markets_response.get('markets', {})
                
                if not markets:
                    console.print("[red]❌ No data, retrying...[/red]")
                    await asyncio.sleep(5)
                    continue
                
                # Get top 8 markets for compact display
                top_markets = list(markets.keys())[:8]
                signal_sets = []
                
                for market in top_markets:
                    market_data = markets[market]
                    signal_set = await create_signal_from_market_data(market, market_data)
                    signal_sets.append(signal_set)
                
                # Clear and display compact dashboard
                console.clear()
                console.print("🚀 [bold blue]Compact dYdX v4 Signals Dashboard[/bold blue] 🚀")
                console.print("[yellow]Press Ctrl+C to stop[/yellow]")
                
                # Create compact layout with panels side by side
                signals_table = create_compact_signals_table(signal_sets)
                stats_panel = create_stats_panel(signal_sets)
                status_panel = create_status_panel(update_count)
                
                # Display main signals table
                console.print(signals_table)
                
                # Display stats and status side by side to save space
                console.print(Columns([stats_panel, status_panel], equal=True, expand=True))
                
                update_count += 1
                
                # Wait 8 seconds for next update
                await asyncio.sleep(8)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                await asyncio.sleep(3)
                continue
        
    except KeyboardInterrupt:
        console.print(f"\n[bold yellow]Dashboard stopped[/bold yellow]")
        console.print(f"[green]Updates: {update_count}[/green]")
    except Exception as e:
        console.print(f"[red]Critical error: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(main())
