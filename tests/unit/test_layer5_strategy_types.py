"""
Layer 5 Strategy Types - TDD Tests
"""

import pytest
from datetime import datetime
from src.dydx_bot.strategies.types import StrategyDecision


class TestStrategyDecision:
    """Test StrategyDecision dataclass."""
    
    def test_strategy_decision_creation(self):
        """Test StrategyDecision can be created with required fields."""
        decision = StrategyDecision(
            market="BTC-USD",
            action="BUY", 
            confidence=85.5,
            size=1000.0,
            timestamp=datetime.now(),
            reason="High momentum + volume signals",
            signal_scores={"momentum": 85, "volume": 90, "volatility": 60, "orderbook": 80},
            metadata={"layer": "5", "test": "unit"}
        )
        
        assert decision.market == "BTC-USD"
        assert decision.action == "BUY"
        assert decision.confidence == 85.5
        assert decision.size == 1000.0
        assert isinstance(decision.timestamp, datetime)
        assert decision.reason == "High momentum + volume signals"
        assert decision.signal_scores["momentum"] == 85

    def test_strategy_decision_validates_action_enum(self):
        """
        NEW TEST: Test StrategyDecision validates action is valid enum value.
        Following STRICT TDD: This test should FAIL first (RED)
        """
        with pytest.raises(ValueError, match="Action must be BUY, SELL, or HOLD"):
            StrategyDecision(
                market="BTC-USD",
                action="INVALID_ACTION",  # This should trigger validation error
                confidence=85.5,
                size=1000.0,
                timestamp=datetime.now(),
                reason="Test invalid action",
                signal_scores={"momentum": 85},
                metadata={"layer": "5", "test": "unit"}
            )
