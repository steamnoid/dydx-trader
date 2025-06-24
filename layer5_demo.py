#!/usr/bin/env python3
"""
Layer 5 Multi-Market Strategy Demo
Shows real dYdX market analysis with NO fallbacks
"""

import asyncio
import sys
from src.dydx_bot.strategies.engine import StrategyEngine
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

async def main():
    console = Console()
    
    console.print(Panel.fit(
        "🎯 Layer 5 Multi-Market Sniper Strategy\n"
        "Real dYdX API Analysis - NO Fallbacks", 
        style="bold green"
    ))
    
    try:
        # Create strategy engine
        console.print("\n🔧 Initializing Strategy Engine...")
        engine = StrategyEngine()
        
        # Analyze ALL markets using real dYdX data
        console.print("🌐 Fetching ALL markets from dYdX API...")
        console.print("⏳ This may take a moment - analyzing 200+ markets...")
        
        results = await asyncio.get_event_loop().run_in_executor(
            None, engine.analyze_all_markets
        )
        
        # Show results
        console.print(f"\n✅ Successfully analyzed {len([k for k in results.keys() if k not in ['portfolio_allocation', 'market_ranking']])} markets!")
        
        # Top markets table
        ranking = results.get('market_ranking', [])
        table = Table(title="🏆 Top 10 Markets by Strategy Score")
        table.add_column("Rank", style="cyan")
        table.add_column("Market", style="magenta")
        table.add_column("Strategy Score", style="green")
        table.add_column("Allocation %", style="yellow")
        table.add_column("Recommendation", style="bold")
        
        for i, entry in enumerate(ranking[:10]):
            market = entry['market']
            score = entry['strategy_score']
            allocation = entry['allocation_percentage']
            
            # Get decision from main results
            decision = results.get(market)
            action = decision.action if decision else "UNKNOWN"
            
            table.add_row(
                str(i + 1),
                market,
                f"{score:.1f}",
                f"{allocation:.1f}%",
                action
            )
        
        console.print(table)
        
        # Portfolio summary
        portfolio = results.get('portfolio_allocation', {})
        total_allocation = sum(portfolio.values())
        allocated_markets = len([v for v in portfolio.values() if v > 0])
        
        summary_table = Table(title="💰 Portfolio Allocation Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Total Markets Analyzed", str(len(results) - 2))
        summary_table.add_row("Markets with Allocation", str(allocated_markets))
        summary_table.add_row("Total Allocation", f"{total_allocation:.1f}%")
        summary_table.add_row("Data Source", "Real dYdX API")
        summary_table.add_row("Architecture", "Layer 5 Multi-Market Sniper")
        
        console.print(summary_table)
        
        # Show signal details for top market
        if ranking:
            top_market = ranking[0]['market']
            top_decision = results.get(top_market)
            if top_decision:
                console.print(f"\n🔍 Signal Analysis for Top Market: {top_market}")
                signal_table = Table()
                signal_table.add_column("Signal Type", style="cyan")
                signal_table.add_column("Score", style="green")
                
                for signal_type, score in top_decision.signal_scores.items():
                    if signal_type != 'strategy_score':
                        signal_table.add_row(signal_type.title(), f"{score:.1f}")
                
                console.print(signal_table)
        
        console.print(Panel.fit(
            "✅ Layer 5 Strategy Engine Successfully Analyzing\n"
            f"ALL {len(results) - 2} dYdX Markets with Real Data!", 
            style="bold green"
        ))
        
    except KeyboardInterrupt:
        console.print("\n⏹️  Demo stopped by user")
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="bold red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
