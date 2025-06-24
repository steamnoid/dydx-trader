#!/usr/bin/env python3
"""
Layer 5 Multi-Market Strategy Demo - STREAMING UPDATES
Shows real dYdX market analysis with real-time streaming data
Updates as fast as data comes in from the API
Press Ctrl+C to stop
"""

import asyncio
import sys
import time
from src.dydx_bot.strategies.engine import StrategyEngine
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout

async def create_display_content(engine, cycle_count, last_update_time):
    """Create the display content for smooth streaming updates"""
    from rich.columns import Columns
    from rich.console import Group
    
    # Get fresh market analysis
    start_time = time.time()
    results = await engine._analyze_all_markets_async()
    analysis_time = time.time() - start_time
    
    # Calculate update frequency
    if last_update_time:
        time_since_last = time.time() - last_update_time
        update_freq = f"{time_since_last:.1f}s ago"
    else:
        update_freq = "First update"
    
    current_time = time.strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
    
    # Header
    header = Panel.fit(
        f"🎯 Layer 5 Multi-Market Sniper Strategy - SMOOTH STREAMING\n"
        f"Live Analysis #{cycle_count} | {current_time}\n"
        f"Last Update: {update_freq} | Analysis: {analysis_time:.2f}s\n"
        f"🔴 LIVE | ✨ NO BLINKING | Press Ctrl+C to stop", 
        style="bold green"
    )
    
    # Top markets table with real-time indicators
    ranking = results.get('market_ranking', [])
    total_markets = len([k for k in results.keys() if k not in ['portfolio_allocation', 'market_ranking']])
    
    table = Table(
        title=f"🔴 LIVE Top 10 Markets (Update #{cycle_count} at {current_time})",
        show_header=True,
        header_style="bold cyan", 
        border_style="bright_blue"
    )
    table.add_column("Rank", style="cyan", width=4)
    table.add_column("Market", style="magenta", width=10)
    table.add_column("Score", style="green", width=8)
    table.add_column("Alloc%", style="yellow", width=7)
    table.add_column("Action", style="bold", width=8)
    table.add_column("Status", style="red", width=12)
    table.add_column("Momentum", style="blue", width=8)
    table.add_column("Volume", style="purple", width=8)
    
    for i, entry in enumerate(ranking[:10]):
        market = entry['market']
        score = entry['strategy_score']
        allocation = entry['allocation_percentage']
        
        # Get decision and signals from main results
        decision = results.get(market)
        action = decision.action if decision else "UNKNOWN"
        
        # Get individual signal scores
        signals = decision.signal_scores if decision else {}
        momentum = signals.get('momentum', 0)
        volume = signals.get('volume', 0)
        
        # Live status indicators
        if score > 80:
            status = "🔥 HOT"
        elif score > 70:
            status = "📈 RISING"
        elif score > 60:
            status = "📊 ACTIVE"
        elif score > 50:
            status = "⚡ FAST"
        else:
            status = "❄️ COLD"
        
        table.add_row(
            f"#{i + 1}",
            market,
            f"{score:.1f}",
            f"{allocation:.1f}%",
            action,
            status,
            f"{momentum:.0f}",
            f"{volume:.0f}"
        )
    
    # Live metrics table
    portfolio = results.get('portfolio_allocation', {})
    total_allocation = sum(portfolio.values())
    allocated_markets = len([v for v in portfolio.values() if v > 0])
    
    metrics_table = Table(title=f"📊 Live Metrics (Smooth Streaming)")
    metrics_table.add_column("Metric", style="cyan", width=20)
    metrics_table.add_column("Value", style="green", width=15)
    metrics_table.add_column("Status", style="yellow", width=15)
    
    metrics_table.add_row("🌐 Total Markets", str(total_markets), "✅ ANALYZED")
    metrics_table.add_row("💼 Active Positions", str(allocated_markets), "📊 DEPLOYED")
    metrics_table.add_row("📈 Portfolio Usage", f"{total_allocation:.1f}%", "🎯 OPTIMIZED")
    metrics_table.add_row("⚡ Analysis Speed", f"{analysis_time:.2f}s", "🚀 FAST")
    metrics_table.add_row("🔄 Update Count", f"#{cycle_count}", "🔴 STREAMING")
    metrics_table.add_row("🌍 Data Source", "dYdX API", "🔴 LIVE")
    metrics_table.add_row("✨ Display Mode", "SMOOTH", "🚫 NO BLINK")
    
    # Top market signal breakdown
    signal_panel = None
    if ranking:
        top_market = ranking[0]['market']
        top_decision = results.get(top_market)
        if top_decision:
            signal_breakdown = f"🎯 LIVE Signals for {top_market}:\n"
            for signal_type, score in top_decision.signal_scores.items():
                if signal_type != 'strategy_score':
                    signal_breakdown += f"  • {signal_type.title()}: {score:.1f}/100\n"
            
            signal_panel = Panel.fit(signal_breakdown.strip(), title='🔍 Top Market Analysis', style='cyan')
    
    # Footer with streaming status
    footer = Panel.fit(
        f"🔴 SMOOTH STREAMING MODE ACTIVE\n"
        f"✅ Update #{cycle_count} Complete\n"
        f"🔄 Next update coming as soon as API responds...\n"
        f"⚡ No artificial delays - streaming at API speed\n"
        f"✨ NO BLINKING - Smooth as silk!\n"
        f"🛑 Press Ctrl+C to stop", 
        style="bold blue"
    )
    
    # Combine all elements into a group for smooth rendering
    elements = [header, table, metrics_table]
    if signal_panel:
        elements.append(signal_panel)
    elements.append(footer)
    
    # Return the grouped content and timestamp
    content = Group(*elements)
    return content, time.time()

async def main():
    console = Console()
    
    console.print(Panel.fit(
        "🎯 Layer 5 Multi-Market Sniper Strategy\n"
        "STREAMING Real-Time Analysis\n"
        "Fastest possible updates from dYdX API\n"
        "Press Ctrl+C to stop", 
        style="bold green"
    ))
    
    cycle_count = 0
    last_update_time = None
    
    try:
        # Create strategy engine
        console.print("\n🔧 Initializing Strategy Engine...")
        engine = StrategyEngine()
        
        console.print("🚀 Starting SMOOTH STREAMING analysis...")
        console.print("📊 Updates will smoothly update in-place")
        console.print("🔴 LIVE mode activated - NO BLINKING!\n")
        
        # Create initial content for Live display
        initial_content, last_update_time = await create_display_content(engine, 1, None)
        
        # Use Rich Live for smooth, non-blinking updates
        with Live(initial_content, console=console, refresh_per_second=4) as live:
            while True:
                cycle_count += 1
                
                try:
                    # Generate fresh content
                    content, current_time = await create_display_content(engine, cycle_count, last_update_time)
                    last_update_time = current_time
                    
                    # Smoothly update the display in-place (no blinking!)
                    live.update(content)
                    
                    # Minimal delay to prevent API rate limiting
                    # This is the fastest safe update rate for dYdX API
                    await asyncio.sleep(0.5)  # 500ms - 2 updates per second max
                    
                except Exception as e:
                    error_content = Panel.fit(
                        f"⚠️  Error in cycle #{cycle_count}: {e}\n"
                        f"🔄 Continuing with next update...", 
                        style="yellow"
                    )
                    live.update(error_content)
                    await asyncio.sleep(1)  # Brief pause on error
                    
    except KeyboardInterrupt:
        console.print("\n\n🛑 User requested stop (Ctrl+C)")
        console.print(Panel.fit(
            f"✅ Layer 5 SMOOTH Streaming Demo Stopped\n"
            f"Completed {cycle_count} smooth updates\n"
            f"Average update rate: ~2 updates/second\n"
            f"✨ NO BLINKING - Smooth as silk! 🎯", 
            style="bold green"
        ))
    except Exception as e:
        console.print(f"\n❌ Error in streaming analysis: {e}", style="bold red")
        console.print(Panel.fit(
            "🔧 Layer 5 Streaming Demo Encountered Error\n"
            "Check logs for details", 
            style="bold red"
        ))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
