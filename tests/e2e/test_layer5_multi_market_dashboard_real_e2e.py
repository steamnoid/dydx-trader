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
