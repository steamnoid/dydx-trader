#!/usr/bin/env python3
"""
Layer 5 Multi-Market Strategy Demo - CONTINUOUS UPDATES
Shows real dYdX market analysis with live streaming updates
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

async def main():
    console = Console()
    
    console.print(Panel.fit(
        "🎯 Layer 5 Multi-Market Sniper Strategy\n"
        "CONTINUOUS Real-Time Analysis\n"
        "Press Ctrl+C to stop", 
        style="bold green"
    ))
    
    cycle_count = 0
    
    try:
        # Create strategy engine
        console.print("\n🔧 Initializing Strategy Engine...")
        engine = StrategyEngine()
        
        while True:
            cycle_count += 1
            
            # Clear screen for fresh display
            console.clear()
            
            console.print(Panel.fit(
                f"🎯 Layer 5 Multi-Market Sniper Strategy\n"
                f"CONTINUOUS Real-Time Analysis - Cycle #{cycle_count}\n"
                f"Time: {time.strftime('%H:%M:%S')}\n"
                f"Press Ctrl+C to stop", 
                style="bold green"
            ))
            
            console.print(f"\n🌐 Analyzing ALL dYdX markets... (Cycle #{cycle_count})")
            start_time = time.time()
            
            # Analyze all markets using real dYdX data
            results = await engine._analyze_all_markets_async()
            
            analysis_time = time.time() - start_time
            current_time = time.strftime("%H:%M:%S")
            
            # Show results
            total_markets = len([k for k in results.keys() if k not in ['portfolio_allocation', 'market_ranking']])
            console.print(f"✅ Analyzed {total_markets} markets in {analysis_time:.2f}s at {current_time}")
            
            # Top markets table with live indicators
            ranking = results.get('market_ranking', [])
            table = Table(title=f"🏆 Top 10 Markets by Strategy Score (Cycle #{cycle_count})")
            table.add_column("Rank", style="cyan")
            table.add_column("Market", style="magenta")
            table.add_column("Strategy Score", style="green")
            table.add_column("Allocation %", style="yellow")
            table.add_column("Recommendation", style="bold")
            table.add_column("Status", style="red")
            
            for i, entry in enumerate(ranking[:10]):
                market = entry['market']
                score = entry['strategy_score']
                allocation = entry['allocation_percentage']
                
                # Get decision from main results
                decision = results.get(market)
                action = decision.action if decision else "UNKNOWN"
                
                # Add live indicators
                if score > 80:
                    status = "🔥 HOT"
                elif score > 70:
                    status = "📈 RISING"
                elif score > 60:
                    status = "📊 STABLE"
                else:
                    status = "🔴 COLD"
                
                table.add_row(
                    str(i + 1),
                    market,
                    f"{score:.1f}",
                    f"{allocation:.1f}%",
                    action,
                    status
                )
            
            console.print(table)
            
            # Real-time portfolio summary
            portfolio = results.get('portfolio_allocation', {})
            total_allocation = sum(portfolio.values())
            allocated_markets = len([v for v in portfolio.values() if v > 0])
            
            summary_table = Table(title=f"💰 Live Portfolio Allocation (Updated: {current_time})")
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="green")
            summary_table.add_column("Status", style="yellow")
            
            summary_table.add_row("Total Markets Analyzed", str(total_markets), "✅ COMPLETE")
            summary_table.add_row("Markets with Allocation", str(allocated_markets), "📊 ACTIVE")
            summary_table.add_row("Total Allocation", f"{total_allocation:.1f}%", "💼 DEPLOYED")
            summary_table.add_row("Analysis Time", f"{analysis_time:.2f}s", "⚡ FAST")
            summary_table.add_row("Update Cycle", f"#{cycle_count}", "🔄 LIVE")
            summary_table.add_row("Data Source", "Real dYdX API", "🌐 REAL")
            summary_table.add_row("Architecture", "Layer 5 Multi-Market", "🎯 SNIPER")
            
            console.print(summary_table)
            
            # Show live signal details for top market
            if ranking:
                top_market = ranking[0]['market']
                top_decision = results.get(top_market)
                if top_decision:
                    console.print(f"\n🔍 Live Signal Analysis for Top Market: {top_market}")
                    signal_table = Table()
                    signal_table.add_column("Signal Type", style="cyan")
                    signal_table.add_column("Score", style="green")
                    signal_table.add_column("Strength", style="yellow")
                    
                    for signal_type, score in top_decision.signal_scores.items():
                        if signal_type != 'strategy_score':
                            if score > 80:
                                strength = "🟢 STRONG"
                            elif score > 60:
                                strength = "🟡 MODERATE"
                            else:
                                strength = "🔴 WEAK"
                            
                            signal_table.add_row(signal_type.title(), f"{score:.1f}", strength)
                    
                    console.print(signal_table)
            
            console.print(Panel.fit(
                f"🔄 AUTONOMOUS CONTINUOUS OPERATION\n"
                f"✅ Cycle #{cycle_count} Complete - ALL {total_markets} Markets Analyzed\n"
                f"🔄 Next update in 30 seconds...\n"
                f"🛑 Press Ctrl+C to stop", 
                style="bold blue"
            ))
            
            # Wait for next cycle (30 seconds) with countdown
            console.print(f"\n⏱️  Waiting 30 seconds for next analysis cycle...")
            for remaining in range(30, 0, -5):
                console.print(f"   Next update in {remaining} seconds...", end="\r")
                await asyncio.sleep(5)
            
            console.print("   Starting next cycle...              ")
            
    except KeyboardInterrupt:
        console.print("\n\n🛑 User requested stop (Ctrl+C)")
        console.print(Panel.fit(
            f"✅ Layer 5 Continuous Demo Stopped\n"
            f"Completed {cycle_count} analysis cycles\n"
            f"Thank you for watching! 🎯", 
            style="bold green"
        ))
    except Exception as e:
        console.print(f"\n❌ Error in continuous analysis: {e}", style="bold red")
        console.print(Panel.fit(
            "🔧 Layer 5 Demo Encountered Error\n"
            "Check logs for details", 
            style="bold red"
        ))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
