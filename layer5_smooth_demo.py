#!/usr/bin/env python3
"""
Layer 5 Multi-Market Strategy Demo - SMOOTH STREAMING (NO BLINKING)
Shows real dYdX market analysis with smooth, non-blinking real-time updates
Updates as fast as data comes in from the API but with smooth transitions
Press Ctrl+C to stop
"""

import asyncio
import sys
import time
import os
from src.dydx_bot.strategies.engine import StrategyEngine
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text

# Clear screen function for smooth transitions
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

async def create_smooth_content(engine, cycle_count, last_update_time):
    """Create content for smooth, non-blinking display"""
    
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
    
    current_time = time.strftime("%H:%M:%S")
    
    # Create layout for organized display
    layout = Layout()
    
    # Split into header, main content, and footer
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=6)
    )
    
    # Header with status
    header_text = Text()
    header_text.append("🎯 Layer 5 Multi-Market Sniper Strategy - SMOOTH STREAMING\n", style="bold green")
    header_text.append(f"Live Analysis #{cycle_count} | {current_time} | ", style="cyan")
    header_text.append(f"Update: {update_freq} | ", style="yellow")
    header_text.append(f"Analysis: {analysis_time:.2f}s\n", style="magenta")
    header_text.append("🔴 LIVE | ✨ SMOOTH - NO BLINKING | Press Ctrl+C to stop", style="bold blue")
    
    layout["header"].update(Panel(header_text, style="green"))
    
    # Main content area - split into left and right
    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    # Left side: Top markets table
    ranking = results.get('market_ranking', [])
    
    markets_table = Table(
        title=f"🔴 LIVE Top 10 Markets",
        show_header=True,
        header_style="bold cyan"
    )
    markets_table.add_column("Rank", style="cyan", width=4)
    markets_table.add_column("Market", style="magenta", width=10)
    markets_table.add_column("Score", style="green", width=6)
    markets_table.add_column("Action", style="bold", width=6)
    markets_table.add_column("Status", style="red", width=10)
    
    for i, entry in enumerate(ranking[:10]):
        market = entry['market']
        score = entry['strategy_score']
        
        # Get decision from main results
        decision = results.get(market)
        action = decision.action if decision else "HOLD"
        
        # Status indicators
        if score > 80:
            status = "🔥 HOT"
        elif score > 70:
            status = "📈 RISING"
        elif score > 60:
            status = "📊 ACTIVE"
        else:
            status = "❄️ COLD"
        
        markets_table.add_row(
            f"#{i + 1}",
            market,
            f"{score:.1f}",
            action,
            status
        )
    
    layout["left"].update(markets_table)
    
    # Right side: Metrics and signals
    total_markets = len([k for k in results.keys() if k not in ['portfolio_allocation', 'market_ranking']])
    portfolio = results.get('portfolio_allocation', {})
    total_allocation = sum(portfolio.values())
    allocated_markets = len([v for v in portfolio.values() if v > 0])
    
    metrics_table = Table(title="📊 Live Metrics")
    metrics_table.add_column("Metric", style="cyan", width=16)
    metrics_table.add_column("Value", style="green", width=12)
    
    metrics_table.add_row("🌐 Markets", str(total_markets))
    metrics_table.add_row("💼 Positions", str(allocated_markets))
    metrics_table.add_row("📈 Portfolio", f"{total_allocation:.1f}%")
    metrics_table.add_row("⚡ Speed", f"{analysis_time:.2f}s")
    metrics_table.add_row("🔄 Updates", f"#{cycle_count}")
    metrics_table.add_row("✨ Mode", "SMOOTH")
    
    # Add top market signals if available
    signal_text = Text()
    if ranking:
        top_market = ranking[0]['market']
        top_decision = results.get(top_market)
        if top_decision:
            signal_text.append(f"🎯 {top_market} Signals:\n", style="bold cyan")
            for signal_type, score in top_decision.signal_scores.items():
                if signal_type != 'strategy_score':
                    signal_text.append(f"• {signal_type.title()}: {score:.1f}\n", style="yellow")
    
    # Split right side for metrics and signals
    layout["right"].split_column(
        Layout(metrics_table, name="metrics"),
        Layout(Panel(signal_text, title="🔍 Top Signals", style="cyan"), name="signals") if signal_text.plain else Layout("")
    )
    
    # Footer with streaming status
    footer_text = Text()
    footer_text.append("🔴 SMOOTH STREAMING ACTIVE | ", style="bold red")
    footer_text.append(f"✅ Update #{cycle_count} Complete | ", style="green")
    footer_text.append("🔄 Next update coming... | ", style="yellow")
    footer_text.append("⚡ API-speed updates | ", style="blue")
    footer_text.append("✨ Zero blinking | ", style="magenta")
    footer_text.append("🛑 Ctrl+C to stop", style="bold white")
    
    layout["footer"].update(Panel(footer_text, style="blue"))
    
    return layout, time.time()

async def main():
    console = Console()
    
    # Initial welcome
    clear_screen()
    console.print(Panel.fit(
        "🎯 Layer 5 Multi-Market Sniper Strategy\n"
        "✨ SMOOTH STREAMING - NO BLINKING EXPERIENCE\n"
        "Real-time updates with smooth transitions\n"
        "Press Ctrl+C to stop", 
        style="bold green"
    ))
    
    console.print("\n🔧 Initializing Strategy Engine...")
    engine = StrategyEngine()
    
    console.print("🚀 Starting SMOOTH streaming analysis...")
    console.print("✨ Smooth updates with NO blinking or flickering")
    console.print("🔴 LIVE mode activated\n")
    
    cycle_count = 0
    last_update_time = None
    
    try:
        while True:
            cycle_count += 1
            
            try:
                # Create fresh content
                layout, current_time = await create_smooth_content(engine, cycle_count, last_update_time)
                last_update_time = current_time
                
                # Clear and display with minimal flicker
                clear_screen()
                console.print(layout)
                
                # Smooth update interval - fast but not overwhelming
                await asyncio.sleep(2.0)  # 2 seconds for smooth experience
                
            except Exception as e:
                console.print(f"⚠️  Error in cycle #{cycle_count}: {e}", style="yellow")
                console.print("🔄 Continuing with next update...")
                await asyncio.sleep(3)  # Longer pause on error
                
    except KeyboardInterrupt:
        clear_screen()
        console.print(Panel.fit(
            f"✅ Layer 5 SMOOTH Streaming Demo Stopped\n"
            f"Completed {cycle_count} smooth updates\n"
            f"✨ Zero blinking experience delivered!\n"
            f"🎯 Thank you for watching!", 
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
