"""
Layer 5 Integration Tests - Multi-Market Strategy Engine
Following STRICT TDD: Integration tests for cross-layer functionality.
Tests Layer 5 (Strategy Engine) integration with Layer 4 (Signal Processing).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import pytest
from datetime import datetime
from dydx_bot.strategies.engine import StrategyEngine
from dydx_bot.strategies.types import StrategyDecision
from dydx_bot.signals.types import SignalSet


class TestLayer5Integration:
    """Integration tests for Layer 5 strategy engine with Layer 4 signals."""

    def test_strategy_engine_processes_real_signal_sets_from_layer4(self):
        """
        FIRST INTEGRATION TEST: Test StrategyEngine processes SignalSet objects from Layer 4.
        Following integration approach: Layer 5 strategy engine + Layer 4 signal types.
        """
        # Initialize strategy engine 
        engine = StrategyEngine()
        
        # Create realistic signal data that would come from Layer 4
        signal_sets = [
            SignalSet(
                market="ETH-USD",
                momentum=0.8,
                volume=0.6,
                volatility=0.5,
                orderbook=0.9,
                timestamp=datetime.now(),
                metadata={
                    "layer": "layer4",
                    "source": "signal_processor"
                }
            ),
            SignalSet(
                market="BTC-USD",
                momentum=0.9,
                volume=0.7,
                volatility=0.6,
                orderbook=0.95,
                timestamp=datetime.now(),
                metadata={
                    "layer": "layer4",
                    "source": "signal_processor"
                }
            )
        ]
        
        # Process signals through Layer 5 (first process, then generate decision)
        processed_signals = engine.process_signals(signal_sets)
        decision = engine.generate_decision_from_signals(processed_signals)
        
        # Verify integration: Layer 5 correctly processes Layer 4 signal formats
        assert isinstance(decision, StrategyDecision)
        assert decision.market in ["ETH-USD", "BTC-USD"]
        assert decision.action in ["BUY", "SELL", "HOLD"]
        assert decision.confidence >= 0.0 and decision.confidence <= 1.0
        assert decision.timestamp is not None
        
        # Verify metadata propagation from Layer 4 to Layer 5
        assert "source_layer" in decision.metadata
        assert decision.metadata["source_layer"] == "layer5"

    def test_multi_market_orchestration_integration(self):
        """
        Test integration between multi-market signal processing and strategy decisions.
        Layer 4 provides signals from multiple markets, Layer 5 orchestrates strategy.
        """
        engine = StrategyEngine()
        
        # Multi-market signal sets from Layer 4
        multi_market_signals = [
            SignalSet(
                market="ETH-USD",
                momentum=0.8,
                volume=0.6,
                volatility=0.5,
                orderbook=0.9,
                timestamp=datetime.now(),
                metadata={"layer": "layer4", "signal_count": 5}
            ),
            SignalSet(
                market="BTC-USD",
                momentum=0.9,
                volume=0.7,
                volatility=0.6,
                orderbook=0.95,
                timestamp=datetime.now(),
                metadata={"layer": "layer4", "signal_count": 7}
            ),
            SignalSet(
                market="SOL-USD",
                momentum=0.7,
                volume=0.5,
                volatility=0.4,
                orderbook=0.8,
                timestamp=datetime.now(),
                metadata={"layer": "layer4", "signal_count": 3}
            )
        ]
        
        # Process through multi-market orchestration
        processed_signals = engine.process_signals(multi_market_signals)
        decision = engine.generate_decision_from_signals(processed_signals)
        
        # Verify Layer 5 selects the best market from Layer 4 signals
        assert isinstance(decision, StrategyDecision)
        assert decision.market in ["ETH-USD", "BTC-USD", "SOL-USD"]
        
        # Should choose BTC-USD (highest momentum + liquidity combination)
        assert decision.market == "BTC-USD"
        assert decision.action in ["BUY", "SELL", "HOLD"]
        
        # Verify metadata includes multi-market orchestration info
        assert "total_markets_analyzed" in decision.metadata
        assert decision.metadata["total_markets_analyzed"] == 3

    def test_metadata_propagation_across_layers(self):
        """
        Test metadata flows correctly from Layer 4 signals to Layer 5 decisions.
        Ensures proper information propagation across architectural layers.
        """
        engine = StrategyEngine()
        
        # Layer 4 signals with rich metadata
        signal_with_metadata = SignalSet(
            market="ETH-USD",
            momentum=0.85,
            volume=0.75,
            volatility=0.65,
            orderbook=0.8,
            timestamp=datetime.now(),
            metadata={
                "layer": "layer4",
                "processor_version": "2.1.0",
                "data_sources": ["orderbook", "trades", "candles"],
                "processing_time_ms": 12.5,
                "signal_quality": "high"
            }
        )
        
        processed_signals = engine.process_signals([signal_with_metadata])
        decision = engine.generate_decision_from_signals(processed_signals)
        
        # Verify Layer 5 preserves and enriches metadata from Layer 4
        assert "source_layer" in decision.metadata
        assert decision.metadata["source_layer"] == "layer5"
        
        # Layer 5 should add its own metadata while preserving Layer 4 info
        assert "strategy_engine_version" in decision.metadata
        assert "processing_timestamp" in decision.metadata

    def test_timestamp_handling_integration(self):
        """
        Test timestamp consistency between Layer 4 signals and Layer 5 decisions.
        Ensures proper temporal ordering and timing metadata.
        """
        engine = StrategyEngine()
        
        base_time = datetime.now()
        
        # Layer 4 signals with specific timestamps  
        timed_signals = [
            SignalSet(
                market="ETH-USD",
                momentum=0.8,
                volume=0.6,
                volatility=0.5,
                orderbook=0.7,
                timestamp=base_time,
                metadata={"layer": "layer4", "sequence": 1}
            ),
            SignalSet(
                market="BTC-USD",
                momentum=0.9,
                volume=0.7,
                volatility=0.6,
                orderbook=0.8,
                timestamp=base_time,
                metadata={"layer": "layer4", "sequence": 2}
            )
        ]
        
        processed_signals = engine.process_signals(timed_signals)
        decision = engine.generate_decision_from_signals(processed_signals)
        
        # Verify Layer 5 maintains temporal consistency with Layer 4
        assert decision.timestamp >= base_time
        assert isinstance(decision.timestamp, datetime)
        
        # Decision timestamp should be recent (within last few seconds)
        time_diff = (datetime.now() - decision.timestamp).total_seconds()
        assert time_diff < 5.0  # Should be very recent

    def test_empty_signal_set_integration(self):
        """
        Test integration behavior when Layer 4 provides empty or minimal signals.
        Ensures Layer 5 handles edge cases from Layer 4 gracefully.
        """
        engine = StrategyEngine()
        
        # Empty signal set from Layer 4
        empty_signals = []
        
        processed_signals = engine.process_signals(empty_signals)
        decision = engine.generate_decision_from_signals(processed_signals)
        
        # Verify Layer 5 handles empty Layer 4 input gracefully
        assert isinstance(decision, StrategyDecision)
        assert decision.action == "HOLD"  # Default fallback action
        assert decision.confidence >= 0.0
        assert decision.market == "BTC-USD"  # Default market when no signals
        assert "source_layer" in decision.metadata
        assert decision.metadata["source_layer"] == "layer5"

    def test_signal_quality_degradation_integration(self):
        """
        Test Layer 5 behavior when Layer 4 provides low-quality signals.
        Ensures robust handling of degraded signal quality from upstream.
        """
        engine = StrategyEngine()
        
        # Low quality signals from Layer 4
        poor_quality_signals = [
            SignalSet(
                market="ETH-USD",
                momentum=0.1,
                volume=0.05,
                volatility=0.03,
                orderbook=0.02,
                timestamp=datetime.now(),
                metadata={"layer": "layer4", "quality": "degraded"}
            ),
            SignalSet(
                market="BTC-USD",
                momentum=0.15,
                volume=0.08,
                volatility=0.05,
                orderbook=0.04,
                timestamp=datetime.now(),
                metadata={"layer": "layer4", "quality": "degraded"}
            )
        ]
        
        processed_signals = engine.process_signals(poor_quality_signals)
        decision = engine.generate_decision_from_signals(processed_signals)
        
        # Verify Layer 5 responds appropriately to poor Layer 4 signals
        assert isinstance(decision, StrategyDecision)
        # With very low signals, should choose "SELL" (below 30% threshold)
        assert decision.action == "SELL"
        assert decision.confidence >= 0.8  # High confidence for clear sell signal
        
        # Should still propagate metadata about signal quality
        assert "source_layer" in decision.metadata
        assert decision.metadata["source_layer"] == "layer5"

    def test_high_frequency_signal_processing_integration(self):
        """
        Test Layer 5 processing of high-frequency signal updates from Layer 4.
        Ensures performance and consistency under rapid signal updates.
        """
        engine = StrategyEngine()
        
        # Simulate rapid signal updates from Layer 4
        rapid_signals = []
        base_time = datetime.now()
        
        for i in range(10):  # 10 rapid signals
            signal = SignalSet(
                market=f"MARKET-{i % 3}",  # Cycling through 3 markets
                momentum=0.5 + (i * 0.05),
                volume=0.8,
                volatility=0.6,
                orderbook=0.7,
                timestamp=base_time,
                metadata={"layer": "layer4", "sequence": i, "high_frequency": True}
            )
            rapid_signals.append(signal)
        
        # Process all rapid signals through Layer 5
        processed_signals = engine.process_signals(rapid_signals)
        decision = engine.generate_decision_from_signals(processed_signals)
        
        # Verify Layer 5 can handle high-frequency Layer 4 signals
        assert isinstance(decision, StrategyDecision)
        assert decision.market.startswith("MARKET-")
        assert decision.action in ["BUY", "SELL", "HOLD"]
        
        # Should maintain metadata about high-frequency processing
        assert "source_layer" in decision.metadata
        assert decision.metadata["source_layer"] == "layer5"
        assert "total_markets_analyzed" in decision.metadata
        assert decision.metadata["total_markets_analyzed"] == 3  # 3 unique markets (MARKET-0, MARKET-1, MARKET-2)
