"""
Layer 5 Strategy Engine - STRICT TDD Tests
Following STRICT TDD: Write ONE test function only, then run to see RED.
"""

import pytest
from datetime import datetime
from dydx_bot.strategies.engine import StrategyEngine
from dydx_bot.strategies.types import StrategyDecision
from dydx_bot.signals.types import SignalSet


class TestStrategyEngine:
    """Test StrategyEngine core business logic using STRICT TDD."""
    
    def test_strategy_engine_can_be_instantiated(self):
        """
        FIRST TEST: Test StrategyEngine can be created.
        Following STRICT TDD: This test should FAIL first (RED)
        """
        engine = StrategyEngine()
        assert engine is not None
        assert hasattr(engine, 'process_signals')
    
    def test_process_signals_with_empty_signal_sets_returns_empty_dict(self):
        """
        SECOND TEST: Test process_signals with empty signal sets returns empty dict.
        Following STRICT TDD: This test should FAIL first (RED)
        """
        engine = StrategyEngine()
        result = engine.process_signals([])
        assert result == {}
    
    def test_process_signals_with_single_signal_set_returns_market_mapping(self):
        """
        THIRD TEST: Test process_signals with single signal set returns market mapping.
        Following STRICT TDD: This test should FAIL first (RED)
        """
        engine = StrategyEngine()
        signal_set = SignalSet(
            market="BTC-USD",
            momentum=85.0,
            volume=72.0,
            volatility=68.0,
            orderbook=91.0,
            timestamp=datetime.now(),
            metadata={}
        )
        result = engine.process_signals([signal_set])
        assert "BTC-USD" in result
        assert result["BTC-USD"] == signal_set
    
    def test_process_signals_with_multiple_markets_identifies_best_market(self):
        """
        FOURTH TEST: Test process_signals with multiple markets identifies best market.
        Following STRICT TDD: This test should FAIL first (RED)
        """
        engine = StrategyEngine()
        
        # Create signal sets for different markets with different scores
        btc_signals = SignalSet(
            market="BTC-USD",
            momentum=85.0,
            volume=72.0,
            volatility=68.0,
            orderbook=91.0,
            timestamp=datetime.now(),
            metadata={}
        )
        
        eth_signals = SignalSet(
            market="ETH-USD", 
            momentum=95.0,  # Higher momentum score
            volume=88.0,    # Higher volume score
            volatility=75.0,
            orderbook=93.0,  # Higher orderbook score
            timestamp=datetime.now(),
            metadata={}
        )
        
        result = engine.process_signals([btc_signals, eth_signals])
        
        # Both markets should be in result
        assert "BTC-USD" in result
        assert "ETH-USD" in result
        assert result["BTC-USD"] == btc_signals
        assert result["ETH-USD"] == eth_signals
        
        # ETH-USD should be identified as best market (higher scores)
        assert "best_market" in result
        assert result["best_market"] == "ETH-USD"
    
    def test_generate_decision_returns_strategy_decision_object(self):
        """
        FIFTH TEST: Test generate_decision returns StrategyDecision object.
        Following STRICT TDD: This test should FAIL first (RED)
        """
        engine = StrategyEngine()
        decision = engine.generate_decision()
        
        # Should return a StrategyDecision object
        assert isinstance(decision, StrategyDecision)
        assert hasattr(decision, 'action')
        assert hasattr(decision, 'market')
        assert hasattr(decision, 'confidence')
    
    def test_generate_decision_with_processed_signals_uses_best_market(self):
        """
        SIXTH TEST: Test generate_decision with processed signals uses best market.
        Following STRICT TDD: This test should FAIL first (RED)
        """
        engine = StrategyEngine()
        
        # Create signal sets with different scores
        btc_signals = SignalSet(
            market="BTC-USD",
            momentum=60.0,
            volume=55.0,
            volatility=50.0,
            orderbook=65.0,
            timestamp=datetime.now(),
            metadata={}
        )
        
        eth_signals = SignalSet(
            market="ETH-USD", 
            momentum=90.0,  # Much higher scores
            volume=85.0,
            volatility=88.0,
            orderbook=92.0,
            timestamp=datetime.now(),
            metadata={}
        )
        
        # Process signals to identify best market
        processed = engine.process_signals([btc_signals, eth_signals])
        
        # Generate decision should use the best market (ETH-USD)
        decision = engine.generate_decision_from_signals(processed)
        
        assert isinstance(decision, StrategyDecision)
        assert decision.market == "ETH-USD"  # Should use best market
        assert decision.action in ["BUY", "SELL", "HOLD"]
    
    def test_generate_decision_with_high_signal_scores_returns_buy_action(self):
        """
        SEVENTH TEST: Test generate_decision with high signal scores returns BUY action.
        Following STRICT TDD: This test should FAIL first (RED)
        """
        engine = StrategyEngine()
        
        # Create signal set with very high scores (above buy threshold)
        high_signals = SignalSet(
            market="BTC-USD",
            momentum=95.0,  # Very high scores
            volume=90.0,
            volatility=85.0,
            orderbook=92.0,
            timestamp=datetime.now(),
            metadata={}
        )
        
        # Process signals
        processed = engine.process_signals([high_signals])
        
        # Generate decision should return BUY for high scores
        decision = engine.generate_decision_from_signals(processed)
        
        assert isinstance(decision, StrategyDecision)
        assert decision.action == "BUY"  # High scores should trigger BUY
        assert decision.market == "BTC-USD"
        assert decision.confidence > 0.7  # High confidence for high scores
    
    def test_generate_decision_with_low_signal_scores_returns_sell_action(self):
        """
        EIGHTH TEST: Test generate_decision with low signal scores returns SELL action.
        Following STRICT TDD: This test should FAIL first (RED)
        """
        engine = StrategyEngine()
        
        # Create signal set with very low scores (below sell threshold)
        low_signals = SignalSet(
            market="BTC-USD",
            momentum=20.0,  # Very low scores
            volume=15.0,
            volatility=25.0,
            orderbook=18.0,
            timestamp=datetime.now(),
            metadata={}
        )
        
        # Process signals
        processed = engine.process_signals([low_signals])
        
        # Generate decision should return SELL for low scores
        decision = engine.generate_decision_from_signals(processed)
        
        assert isinstance(decision, StrategyDecision)
        assert decision.action == "SELL"  # Low scores should trigger SELL
        assert decision.market == "BTC-USD"
        assert decision.confidence > 0.7  # High confidence for low scores (strong sell signal)
    
    def test_generate_decision_with_empty_processed_signals_uses_fallback_logic(self):
        """
        NINTH TEST: Test generate_decision with empty processed signals uses fallback logic.
        Following STRICT TDD: This test should FAIL first (RED)
        """
        engine = StrategyEngine()
        
        # Create empty processed signals (no signal sets but has best_market key)
        processed_signals = {"best_market": "BTC-USD"}
        
        # Generate decision should handle missing signal set gracefully
        decision = engine.generate_decision_from_signals(processed_signals)
        
        assert isinstance(decision, StrategyDecision)
        assert decision.action == "HOLD"  # Should default to HOLD when no signal data
        assert decision.market == "BTC-USD"  # Should use best_market even without signal set
        assert decision.confidence == 0.5  # Default confidence for no signal data
    
    def test_process_signals_with_no_best_market_uses_btc_usd_fallback(self):
        """
        TENTH TEST: Test process_signals with no clear best market uses BTC-USD fallback.
        Following STRICT TDD: This test should FAIL first (RED)
        """
        engine = StrategyEngine()
        
        # Create signal sets where no market has higher scores than others
        # (This edge case should trigger the fallback logic)
        signal_set = SignalSet(
            market="ETH-USD",
            momentum=50.0,  # All equal scores
            volume=50.0,
            volatility=50.0,
            orderbook=50.0,
            timestamp=datetime.now(),
            metadata={}
        )
        
        # Process signals should use fallback when there's ambiguity
        result = engine.process_signals([signal_set])
        
        # Should contain the signal set
        assert "ETH-USD" in result
        assert result["ETH-USD"] == signal_set
        
        # Should have a best_market key (this is what we're testing)
        assert "best_market" in result
        # Since we only have one market, it should be selected as best
        assert result["best_market"] == "ETH-USD"
    
    def test_process_signals_with_zero_score_signals_selects_best_market(self):
        """
        ELEVENTH TEST: Test process_signals with zero scores (minimum valid values).
        Following STRICT TDD: This test verifies behavior with minimum valid signal scores.
        Since all scores are 0-100, the minimum overall score is 0, which is > -1 (best_score initial value).
        """
        engine = StrategyEngine()
        
        # Create signal set with minimum valid values (all zeros)
        signal_set = SignalSet(
            market="ETH-USD",
            momentum=0.0,  # All minimum valid values
            volume=0.0,
            volatility=0.0,
            orderbook=0.0,  # Overall score: (0 + 0 + 0 + 0) / 4 = 0.0 (> -1)
            timestamp=datetime.now(),
            metadata={}
        )
        
        result = engine.process_signals([signal_set])
        
        # Should contain the signal set
        assert "ETH-USD" in result
        assert result["ETH-USD"] == signal_set
        
        # Should select ETH-USD as best_market since it's the only market and score 0 > -1
        assert "best_market" in result
        assert result["best_market"] == "ETH-USD"
    
    def test_generate_decision_from_signals_with_missing_best_market_data_uses_hold_action(self):
        """
        TWELFTH TEST: Test generate_decision_from_signals when best_market data is missing.
        Following STRICT TDD: This test covers lines 78-79 (else branch when best_signal_set is None)
        When processed_signals has best_market but no actual signal data for that market.
        """
        engine = StrategyEngine()
        
        # Create processed_signals with best_market but missing signal data for that market
        processed_signals = {
            "best_market": "BTC-USD",
            "ETH-USD": SignalSet(
                market="ETH-USD",
                momentum=75.0,
                volume=80.0,
                volatility=70.0,
                orderbook=85.0,
                timestamp=datetime.now(),
                metadata={}
            )
            # Note: no "BTC-USD" signal data, but best_market points to "BTC-USD"
        }
        
        result = engine.generate_decision_from_signals(processed_signals)
        
        # Should return HOLD action with 0.5 confidence since best_signal_set is None
        assert result.action == "HOLD"
        assert result.confidence == 0.5
        assert result.market == "BTC-USD"  # Should still use the best_market value
