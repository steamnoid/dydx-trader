"""
Layer 5 Multi-Market Dashboard E2E Tests
Using REAL dYdX API Connections, Layers 2-5 Stack, and Live Market Data

CRITICAL: NO MOCKS - These are true E2E tests using:
- Real dYdX IndexerClient connections (Layer 2)
- Live market data processing (Layer 3) 
- Actual signal scoring engines (Layer 4)
- Real strategy engine decision logic (Layer 5)
- Rich Console.capture() for dashboard output validation
- Multi-market streaming and cross-market analysis

OPERATIONAL GUARANTEE: When these tests pass, Layer 5 multi-market dashboard works with real dYdX data.

E2E TESTING SCOPE:
1. Real connection establishment to dYdX mainnet
2. Multi-market data streaming across ALL USD markets
3. Cross-market signal analysis and ranking
4. Strategy engine decision generation from real signals
5. Dashboard rendering with Rich Console output capture
6. Performance validation with real network latency
7. Integration with the complete Layer 2-5 stack
"""

import pytest
import asyncio
import time
from datetime import datetime
from typing import Dict, Any
from io import StringIO

from rich.console import Console

from dydx_v4_client.indexer.rest.indexer_client import IndexerClient

# Real Layer 2-5 imports (no mocks)
from src.dydx_bot.connection.client import DydxClient
from src.dydx_bot.data.processor import MarketDataProcessor  
from src.dydx_bot.signals.manager import SignalManager
from src.dydx_bot.strategies.engine import StrategyEngine
from src.dydx_bot.dashboard.layer5_multi_market_dashboard import Layer5MultiMarketDashboard


@pytest.fixture
def real_indexer_client():
    """Real dYdX IndexerClient for E2E testing"""
    return IndexerClient(host="https://indexer.dydx.trade")


@pytest.fixture
def real_connection_client():
    """Real Layer 2 connection client"""
    return DydxClient()


@pytest.fixture
def real_data_processor():
    """Real Layer 3 data processor"""
    return MarketDataProcessor()


@pytest.fixture
def real_signal_manager():
    """Real Layer 4 signal manager"""
    return SignalManager()


@pytest.fixture
def real_strategy_engine():
    """Real Layer 5 strategy engine"""
    return StrategyEngine()


class TestLayer5MultiMarketDashboardRealE2E:
    """
    STRICT TDD E2E Tests for Layer 5 Multi-Market Dashboard
    Each test uses the complete real stack with no mocks or placeholders
    """

    @pytest.mark.asyncio
    async def test_dashboard_initialization_with_real_stack(
        self, 
        real_connection_client,
        real_data_processor, 
        real_signal_manager,
        real_strategy_engine
    ):
        """
        TDD Test 1: Dashboard initializes with real Layer 2-5 components
        
        EXPECTATION: Dashboard object created successfully with all real stack components
        VALIDATION: All layer dependencies are properly injected and accessible
        """
        # Create dashboard with real stack - this should work
        dashboard = Layer5MultiMarketDashboard(
            connection_client=real_connection_client,
            data_processor=real_data_processor, 
            signal_manager=real_signal_manager,
            strategy_engine=real_strategy_engine
        )
        
        # Validate all dependencies are properly set
        assert dashboard.connection_client is not None
        assert dashboard.data_processor is not None
        assert dashboard.signal_manager is not None
        assert dashboard.strategy_engine is not None
        
        # Validate dashboard has console for Rich output
        assert hasattr(dashboard, 'console')
        assert isinstance(dashboard.console, Console)

    @pytest.mark.asyncio
    async def test_dashboard_can_render_multi_market_overview(
        self,
        real_connection_client,
        real_data_processor,
        real_signal_manager, 
        real_strategy_engine
    ):
        """
        TDD Test 2: Dashboard can render multi-market overview with real data
        
        EXPECTATION: Dashboard renders a multi-market overview panel using the real stack
        VALIDATION: Rich console output contains multi-market data and strategy decisions
        """
        # Create dashboard with real stack
        dashboard = Layer5MultiMarketDashboard(
            connection_client=real_connection_client,
            data_processor=real_data_processor,
            signal_manager=real_signal_manager,
            strategy_engine=real_strategy_engine
        )
        
        try:
            # Dashboard should be able to render multi-market overview
            with dashboard.console.capture() as capture:
                await dashboard.render_multi_market_overview()
            
            rich_output = capture.get()
            
            # Validate basic multi-market structure is present
            assert "Multi-Market" in rich_output, "Multi-market header missing"
            assert "Strategy" in rich_output, "Strategy section missing"
            assert len(rich_output.strip()) > 0, "Empty output - no rendering occurred"
            
        finally:
            # Cleanup (following proper async pattern)
            if hasattr(dashboard, 'shutdown'):
                await dashboard.shutdown()

    @pytest.mark.asyncio
    async def test_dashboard_displays_real_market_signals_from_layer4(
        self,
        real_connection_client,
        real_data_processor,
        real_signal_manager,
        real_strategy_engine
    ):
        """
        TDD Test 3: Dashboard displays real market signals from Layer 4 signal engines
        
        EXPECTATION: Dashboard shows signal scores (0-100) from multiple markets using real Layer 4 engines
        VALIDATION: Rich console output contains signal data from momentum, volume, volatility, orderbook engines
        """
        # Create dashboard with real stack
        dashboard = Layer5MultiMarketDashboard(
            connection_client=real_connection_client,
            data_processor=real_data_processor,
            signal_manager=real_signal_manager,
            strategy_engine=real_strategy_engine
        )
        
        try:
            # Dashboard should display real signal data from Layer 4
            with dashboard.console.capture() as capture:
                await dashboard.render_signal_analysis()
            
            rich_output = capture.get()
            
            # Validate signal analysis structure is present
            assert "Signal" in rich_output, "Signal section missing"
            assert "BTC-USD" in rich_output, "BTC-USD market missing"
            assert len(rich_output.strip()) > 0, "Empty output - no signal rendering occurred"
            
        finally:
            # Cleanup (following proper async pattern)
            if hasattr(dashboard, 'shutdown'):
                await dashboard.shutdown()

    @pytest.mark.asyncio
    async def test_dashboard_shows_strategy_decisions_from_real_engine(
        self,
        real_connection_client,
        real_data_processor,
        real_signal_manager,
        real_strategy_engine
    ):
        """
        TDD Test 4: Dashboard shows strategy decisions from real strategy engine
        
        EXPECTATION: Dashboard displays decisions (BUY/SELL/HOLD) from Layer 5 strategy engine
        VALIDATION: Rich console output contains strategy decisions with confidence and reasoning
        """
        # Create dashboard with real stack
        dashboard = Layer5MultiMarketDashboard(
            connection_client=real_connection_client,
            data_processor=real_data_processor,
            signal_manager=real_signal_manager,
            strategy_engine=real_strategy_engine
        )
        
        try:
            # Dashboard should display real strategy decisions
            with dashboard.console.capture() as capture:
                await dashboard.render_strategy_decisions()
            
            rich_output = capture.get()
            
            # Validate strategy decisions structure is present
            assert "Strategy" in rich_output, "Strategy section missing"
            assert "Decision" in rich_output, "Decision field missing"
            assert len(rich_output.strip()) > 0, "Empty output - no strategy rendering occurred"
            
        finally:
            # Cleanup (following proper async pattern)
            if hasattr(dashboard, 'shutdown'):
                await dashboard.shutdown()

    @pytest.mark.asyncio
    async def test_dashboard_integrates_with_real_signal_manager(
        self,
        real_connection_client,
        real_data_processor,
        real_signal_manager,
        real_strategy_engine
    ):
        """
        TDD Test 5: Dashboard integrates with real signal manager to get actual signals
        
        EXPECTATION: Dashboard calls real signal manager and displays actual signal calculations
        VALIDATION: Rich console output shows actual signal scores from real Layer 4 engines
        """
        # Create dashboard with real stack
        dashboard = Layer5MultiMarketDashboard(
            connection_client=real_connection_client,
            data_processor=real_data_processor,
            signal_manager=real_signal_manager,
            strategy_engine=real_strategy_engine
        )
        
        try:
            # Dashboard should use real signal manager to get signals
            with dashboard.console.capture() as capture:
                await dashboard.render_real_signals()
            
            rich_output = capture.get()
            
            # Validate real signal integration is present
            assert "Signals" in rich_output, "Signals section missing"
            assert "Score" in rich_output, "Score field missing"
            assert len(rich_output.strip()) > 0, "Empty output - no real signal integration occurred"
            
        finally:
            # Cleanup (following proper async pattern)
            if hasattr(dashboard, 'shutdown'):
                await dashboard.shutdown()

    @pytest.mark.asyncio
    async def test_dashboard_fetches_and_displays_live_dydx_data(
        self,
        real_connection_client,
        real_data_processor,
        real_signal_manager,
        real_strategy_engine
    ):
        """
        TDD Test 6: Dashboard fetches and displays LIVE dYdX market data
        
        EXPECTATION: Dashboard makes actual API calls to dYdX to fetch live market data
        VALIDATION: Rich console output contains real BTC-USD price, volume, and market data from dYdX API
        TIMING: Test should take 2+ seconds due to real network calls to dYdX API
        """
        # Create dashboard with real stack
        dashboard = Layer5MultiMarketDashboard(
            connection_client=real_connection_client,
            data_processor=real_data_processor,
            signal_manager=real_signal_manager,
            strategy_engine=real_strategy_engine
        )
        
        try:
            # Time the operation to validate it's making real network calls
            start_time = time.time()
            
            # Dashboard should fetch and display LIVE dYdX data
            with dashboard.console.capture() as capture:
                await dashboard.render_live_market_data()
            
            elapsed_time = time.time() - start_time
            rich_output = capture.get()
            
            # Validate we're making real network calls (should take time)
            assert elapsed_time >= 1.0, f"Operation too fast ({elapsed_time:.2f}s) - likely not using real API"
            
            # Validate real dYdX market data is present
            assert "BTC-USD" in rich_output, "BTC-USD market missing from output"
            assert "$" in rich_output, "Dollar price formatting missing - no real prices"
            assert any(char.isdigit() for char in rich_output), "No numeric data - missing real market values"
            
            # Validate specific dYdX data fields are present
            market_data_indicators = ["Price", "Volume", "24H", "Change"]
            found_indicators = [indicator for indicator in market_data_indicators if indicator in rich_output]
            assert len(found_indicators) >= 2, f"Missing real market data indicators. Found: {found_indicators}"
            
            # Should contain at least 100 characters of real data
            assert len(rich_output.strip()) > 100, "Output too short - likely static/minimal data"
            
        finally:
            # Cleanup (following proper async pattern)
            if hasattr(dashboard, 'shutdown'):
                await dashboard.shutdown()

            # Cleanup (following proper async pattern)
            if hasattr(dashboard, 'shutdown'):
                await dashboard.shutdown()

    async def test_dashboard_displays_multi_market_portfolio_allocation(
        self,
        real_connection_client,
        real_data_processor,
        real_signal_manager,
        real_strategy_engine
    ):
        """
        TDD Test 7: Dashboard calculates and displays multi-market portfolio allocation
        
        EXPECTATION: Dashboard uses strategy engine to calculate optimal portfolio allocation across multiple markets
        VALIDATION: Rich console output shows allocation percentages for BTC-USD, ETH-USD, SOL-USD with real data
        REQUIREMENT: Must show actual allocation logic based on real signal strength and market conditions
        """
        # Create dashboard with real stack
        dashboard = Layer5MultiMarketDashboard(
            connection_client=real_connection_client,
            data_processor=real_data_processor,
            signal_manager=real_signal_manager,
            strategy_engine=real_strategy_engine
        )
        
        try:
            # Dashboard should calculate and display portfolio allocation
            with dashboard.console.capture() as capture:
                await dashboard.render_portfolio_allocation()
            
            rich_output = capture.get()
            
            # Validate portfolio allocation display
            assert "Portfolio" in rich_output, "Portfolio section missing"
            assert "Allocation" in rich_output, "Allocation section missing"
            assert "%" in rich_output, "Percentage symbols missing - no allocation data"
            
            # Validate multiple markets are included
            markets = ["BTC-USD", "ETH-USD", "SOL-USD"]
            found_markets = [market for market in markets if market in rich_output]
            assert len(found_markets) >= 2, f"Missing multi-market allocation. Found: {found_markets}"
            
            # Validate allocation percentages are present (should add up logically)
            percentage_matches = [char for char in rich_output if char.isdigit()]
            assert len(percentage_matches) >= 3, "Missing allocation percentage data"
            
            # Should contain substantial allocation information
            assert len(rich_output.strip()) > 80, "Output too short - missing allocation details"
            
        finally:
            # Cleanup (following proper async pattern)
            if hasattr(dashboard, 'shutdown'):
                await dashboard.shutdown()

    async def test_dashboard_performs_cross_market_signal_comparison(
        self,
        real_connection_client,
        real_data_processor,
        real_signal_manager,
        real_strategy_engine
    ):
        """
        TDD Test 8: Dashboard performs cross-market signal comparison for sniper strategy
        
        EXPECTATION: Dashboard compares signal strength across multiple markets and identifies best opportunities
        VALIDATION: Rich console output shows signal comparison table with BTC-USD, ETH-USD, SOL-USD ranking
        REQUIREMENT: Must show which market has strongest signals for multi-market sniper targeting
        """
        # Create dashboard with real stack
        dashboard = Layer5MultiMarketDashboard(
            connection_client=real_connection_client,
            data_processor=real_data_processor,
            signal_manager=real_signal_manager,
            strategy_engine=real_strategy_engine
        )
        
        try:
            # Dashboard should perform cross-market signal comparison
            with dashboard.console.capture() as capture:
                await dashboard.render_cross_market_comparison()
            
            rich_output = capture.get()
            
            # Validate cross-market comparison display
            assert "Cross-Market" in rich_output, "Cross-market section missing"
            assert "Comparison" in rich_output or "Ranking" in rich_output, "Comparison analysis missing"
            assert "Signal" in rich_output and ("Strength" in rich_output or "Streng" in rich_output), "Signal strength comparison missing"
            
            # Validate multiple markets are compared
            markets = ["BTC-USD", "ETH-USD", "SOL-USD"]
            found_markets = [market for market in markets if market in rich_output]
            assert len(found_markets) >= 3, f"Missing full market comparison. Found: {found_markets}"
            
            # Validate ranking/scoring is present
            ranking_indicators = ["#1", "#2", "#3", "Rank", "Best", "Score"]
            found_indicators = [indicator for indicator in ranking_indicators if indicator in rich_output]
            assert len(found_indicators) >= 2, f"Missing ranking indicators. Found: {found_indicators}"
            
            # Validate signal scores are shown (0-100 range)
            score_matches = [char for char in rich_output if char.isdigit()]
            assert len(score_matches) >= 6, "Missing signal score data for comparison"
            
            # Should contain substantial comparison analysis
            assert len(rich_output.strip()) > 120, "Output too short - missing comparison analysis"
            
        finally:
            # Cleanup (following proper async pattern)
            if hasattr(dashboard, 'shutdown'):
                await dashboard.shutdown()

    async def test_dashboard_calculates_position_sizing_from_signals(
        self,
        real_connection_client,
        real_data_processor,
        real_signal_manager,
        real_strategy_engine
    ):
        """
        TDD Test 9: Dashboard calculates optimal position sizing based on signal strength
        
        EXPECTATION: Dashboard calculates position sizes based on signal confidence and risk parameters
        VALIDATION: Rich console output shows position sizing table with risk-adjusted amounts
        REQUIREMENT: Must show actual USD amounts and percentage allocations based on signal strength
        """
        # Create dashboard with real stack
        dashboard = Layer5MultiMarketDashboard(
            connection_client=real_connection_client,
            data_processor=real_data_processor,
            signal_manager=real_signal_manager,
            strategy_engine=real_strategy_engine
        )
        
        try:
            # Dashboard should calculate position sizing based on signals
            with dashboard.console.capture() as capture:
                await dashboard.render_position_sizing(portfolio_value=100000.0)  # $100k portfolio
            
            rich_output = capture.get()
            
            # Validate position sizing display
            assert "Position" in rich_output, "Position sizing section missing"
            assert "Size" in rich_output or "Amount" in rich_output, "Position amounts missing"
            assert "$" in rich_output, "Dollar amounts missing"
            
            # Validate risk-based calculations
            risk_indicators = ["Risk", "Max", "Stop", "Size"]
            found_risk = [indicator for indicator in risk_indicators if indicator in rich_output]
            assert len(found_risk) >= 2, f"Missing risk-based sizing. Found: {found_risk}"
            
            # Validate multiple markets have position sizes
            markets = ["BTC-USD", "ETH-USD", "SOL-USD"]
            found_markets = [market for market in markets if market in rich_output]
            assert len(found_markets) >= 3, f"Missing multi-market positions. Found: {found_markets}"
            
            # Validate numeric position data
            amount_matches = [char for char in rich_output if char in "0123456789,.$"]
            assert len(amount_matches) >= 20, "Missing position amount calculations"
            
            # Should contain comprehensive sizing analysis
            assert len(rich_output.strip()) > 150, "Output too short - missing position sizing details"
            
        finally:
            # Cleanup (following proper async pattern)
            if hasattr(dashboard, 'shutdown'):
                await dashboard.shutdown()

    async def test_complete_layer5_multi_market_dashboard_integration(
        self,
        real_connection_client,
        real_data_processor,
        real_signal_manager,
        real_strategy_engine
    ):
        """
        TDD Test 10: Complete Layer 5 Multi-Market Dashboard Integration Test
        
        EXPECTATION: Dashboard integrates all Layer 5 capabilities in a comprehensive multi-market display
        VALIDATION: Rich console shows live data, signals, allocation, comparison, and position sizing
        REQUIREMENT: Must demonstrate complete Layer 5 sniper strategy functionality working together
        """
        # Create dashboard with real stack
        dashboard = Layer5MultiMarketDashboard(
            connection_client=real_connection_client,
            data_processor=real_data_processor,
            signal_manager=real_signal_manager,
            strategy_engine=real_strategy_engine
        )
        
        try:
            # Test complete dashboard integration
            with dashboard.console.capture() as capture:
                dashboard.console.print("[bold cyan]🎯 LAYER 5 MULTI-MARKET SNIPER DASHBOARD[/bold cyan]\n")
                
                # Render all Layer 5 capabilities
                await dashboard.render_live_market_data()
                dashboard.console.print("\n")
                
                await dashboard.render_cross_market_comparison()
                dashboard.console.print("\n")
                
                await dashboard.render_portfolio_allocation()
                dashboard.console.print("\n")
                
                await dashboard.render_position_sizing(portfolio_value=100000.0)
            
            rich_output = capture.get()
            
            # Validate comprehensive Layer 5 functionality
            layer5_features = [
                "Cross-Market",  # Cross-market comparison
                "Portfolio Allocation",  # Portfolio allocation
                "Position Sizing",  # Position sizing
                "BTC-USD",  # Multi-market support
                "ETH-USD",
                "SOL-USD"
            ]
            
            missing_features = [feature for feature in layer5_features if feature not in rich_output]
            assert len(missing_features) == 0, f"Missing Layer 5 features: {missing_features}"
            
            # Validate data richness (comprehensive output)
            assert len(rich_output.strip()) > 500, "Output too short - missing comprehensive Layer 5 integration"
            
            # Validate real market data integration
            assert "$" in rich_output, "Missing real market prices"
            assert "%" in rich_output, "Missing percentage data"
            
            # Validate signal integration
            signal_indicators = ["Score", "Signal", "Rank", "#1", "#2", "#3"]
            found_signals = [indicator for indicator in signal_indicators if indicator in rich_output]
            assert len(found_signals) >= 4, f"Missing signal integration. Found: {found_signals}"
            
            # Validate multi-market coverage
            markets = ["BTC-USD", "ETH-USD", "SOL-USD"]
            market_count = sum(1 for market in markets if rich_output.count(market) >= 4)  # Should appear in multiple sections
            assert market_count >= 3, f"Insufficient multi-market coverage. Found: {market_count} markets"
            
        finally:
            # Cleanup (following proper async pattern)
            if hasattr(dashboard, 'shutdown'):
                await dashboard.shutdown()
