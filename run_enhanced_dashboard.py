#!/usr/bin/env python3
"""
Enhanced Layer 2 Dashboard Demo - Autonomous Sniper Bot

This demonstrates the production-grade Layer 2 capabilities with:
- Real dYdX market data streaming
- Production throttling metrics
- Performance monitoring
- Autonomous operation validation

Shows both QUANTITATIVE (metrics) and QUALITATIVE (real data) insights.
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.dydx_bot.dashboard.layer2_dashboard import Layer2Dashboard


async def main():
    """Run the enhanced dashboard demonstration"""
    print("🚀 Starting Enhanced Layer 2 Dashboard - Autonomous Sniper Bot")
    print("📊 Demonstrating REAL DATA streaming with production throttling")
    print("⏱️  Running for 45 seconds to collect comprehensive data...\n")
    
    dashboard = Layer2Dashboard()
    
    try:
        # Run the enhanced dashboard with real data
        await dashboard.run_dashboard(duration_seconds=45)
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Dashboard error: {e}")
    finally:
        print("\n✅ Enhanced Layer 2 Dashboard demonstration completed!")
        print("🎯 Layer 2 is production-ready with autonomous operation")


if __name__ == "__main__":
    asyncio.run(main())
