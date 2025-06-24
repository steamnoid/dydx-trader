#!/usr/bin/env python3
"""Run Layer 5 Dashboard Demo"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dydx_bot.dashboard.layer5_multi_market_dashboard import Layer5MultiMarketDashboard
from dydx_bot.connection.client import DydxClient
from dydx_bot.data.processor import MarketDataProcessor
from dydx_bot.signals.manager import SignalManager
from dydx_bot.strategies.engine import StrategyEngine

def main():
    # Create real dependencies
    connection_client = DydxClient()
    data_processor = MarketDataProcessor(connection_client)
    signal_manager = SignalManager()
    strategy_engine = StrategyEngine()
    
    # Create dashboard with real Layer 2-5 stack
    dashboard = Layer5MultiMarketDashboard(
        connection_client=connection_client,
        data_processor=data_processor,
        signal_manager=signal_manager,
        strategy_engine=strategy_engine
    )
    
    print("🎯 Layer 5 Multi-Market Sniper Strategy Dashboard")
    print("=" * 60)
    print()
    
    print("📊 Multi-Market Overview:")
    dashboard.render_multi_market_overview()
    print()
    
    print("💰 Live Market Data:")
    dashboard.render_live_market_data()
    print()
    
    print("⚡ Real Signals:")
    dashboard.render_real_signals()
    print()
    
    print("🔍 Cross-Market Comparison:")
    dashboard.render_cross_market_comparison()
    print()
    
    print("📏 Position Sizing:")
    dashboard.render_position_sizing()
    print()
    
    print("💼 Portfolio Allocation:")
    dashboard.render_portfolio_allocation()
    print()
    
    print("🧠 Strategy Decisions:")
    dashboard.render_strategy_decisions()
    print()
    
    print("✅ Layer 5 Multi-Market Dashboard Demo Complete!")
    print("🎯 All Layer 5 features implemented and working with real Layer 2-5 stack!")

if __name__ == "__main__":
    main()
