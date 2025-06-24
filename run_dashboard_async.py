#!/usr/bin/env python3
"""
Async version of Layer 5 Multi-Market Dashboard Demo
Shows live real-time analysis of all dYdX markets with strategy decisions
"""

import asyncio
import logging
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dydx_bot.dashboard.layer5_multi_market_dashboard import Layer5MultiMarketDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Run the Layer 5 Multi-Market Dashboard with real data"""
    print("🎯 Layer 5 Multi-Market Sniper Strategy Dashboard")
    print("=" * 60)
    print()
    
    # Initialize dashboard
    dashboard = Layer5MultiMarketDashboard()
    
    try:
        print("📊 Multi-Market Overview:")
        await dashboard.render_multi_market_overview()
        print()
        
        print("💰 Live Market Data:")
        await dashboard.render_live_market_data()
        print()
        
        print("⚡ Real Signals:")
        await dashboard.render_real_signals()
        print()
        
        print("🔍 Cross-Market Comparison:")
        await dashboard.render_cross_market_comparison()
        print()
        
        print("📏 Position Sizing:")
        await dashboard.render_position_sizing()
        print()
        
        print("💼 Portfolio Allocation:")
        await dashboard.render_portfolio_allocation()
        print()
        
        print("🧠 Strategy Decisions:")
        await dashboard.render_strategy_decisions()
        print()
        
        print("✅ Layer 5 Multi-Market Dashboard Demo Complete!")
        print("🎯 All Layer 5 features implemented and working with real Layer 2-5 stack!")
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
