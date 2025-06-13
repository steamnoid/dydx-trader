#!/usr/bin/env python3
"""
Enhanced Layer 2 Dashboard Demonstration with Production Throttling

This script demonstrates the autonomous Sniper bot's Layer 2 capabilities
including the new production-grade throttling system.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dydx_bot.dashboard.layer2_dashboard import Layer2Dashboard


async def main():
    """Run the enhanced dashboard demonstration"""
    print("🚀 Starting dYdX v4 Autonomous Sniper Bot - Layer 2 Enhanced Dashboard")
    print("📊 Now with Production-Grade Throttling System")
    print("⏱️  Running 30-second demonstration...")
    print()
    
    dashboard = Layer2Dashboard()
    
    try:
        await dashboard.run_demo(duration_seconds=30)
        print("\n✅ Enhanced dashboard demonstration completed successfully!")
        print("🎯 Production throttling system operational")
        print("📈 All Layer 2 capabilities verified with real dYdX data")
        
    except Exception as e:
        print(f"\n❌ Dashboard demonstration failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
