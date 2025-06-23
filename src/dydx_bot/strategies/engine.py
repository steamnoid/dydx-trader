"""
Strategy Engine - MINIMAL code to pass ONE test only.
"""

from datetime import datetime
from dydx_bot.strategies.types import StrategyDecision


class StrategyEngine:
    """Strategy engine for multi-market sniper decisions."""
    
    def __init__(self):
        """Initialize strategy engine."""
        pass
    
    def process_signals(self, signal_sets):
        """Process signals method - minimal implementation."""
        if not signal_sets:
            return {}
        
        result = {}
        best_market = None
        best_score = -1
        
        for signal_set in signal_sets:
            result[signal_set.market] = signal_set
            
            # Calculate overall score for this market (simple average)
            overall_score = (signal_set.momentum + signal_set.volume + 
                           signal_set.volatility + signal_set.orderbook) / 4
            
            if overall_score > best_score:
                best_score = overall_score
                best_market = signal_set.market
        
        # Set best market - guaranteed to be set since all SignalSet scores are 0-100 and best_score starts at -1
        result["best_market"] = best_market
            
        return result
    
    def generate_decision(self):
        """Generate decision method - minimal implementation."""
        return StrategyDecision(
            market="BTC-USD",
            action="HOLD",
            confidence=0.5,
            size=0.0,
            timestamp=datetime.now(),
            reason="Default decision",
            signal_scores={},
            metadata={"source_layer": "layer5", "strategy_engine_version": "1.0.0", "processing_timestamp": datetime.now()}
        )
    
    def generate_decision_from_signals(self, processed_signals):
        """Generate decision based on processed signals - minimal implementation."""
        # Get the best market from processed signals
        best_market = processed_signals.get("best_market", "BTC-USD")
        
        # Get the signal set for the best market
        best_signal_set = processed_signals.get(best_market)
        
        # Calculate decision based on signal scores
        if best_signal_set:
            # Calculate overall score (simple average)
            overall_score = (best_signal_set.momentum + best_signal_set.volume + 
                           best_signal_set.volatility + best_signal_set.orderbook) / 4
            
            # Determine action based on score thresholds
            if overall_score >= 80.0:  # High threshold for BUY
                action = "BUY"
                confidence = min(0.9, overall_score / 100.0 + 0.1)  # Higher confidence for higher scores
            elif overall_score <= 30.0:  # Low threshold for SELL
                action = "SELL"
                confidence = min(0.9, (100.0 - overall_score) / 100.0 + 0.1)
            else:
                action = "HOLD"
                confidence = 0.5
        else:
            action = "HOLD"
            confidence = 0.5
        
        # Collect metadata from Layer 4 signals for propagation
        layer4_metadata = {}
        if best_signal_set:
            # Extract useful Layer 4 metadata
            if hasattr(best_signal_set, 'metadata') and best_signal_set.metadata:
                layer4_metadata = {
                    f"layer4_{key}": value 
                    for key, value in best_signal_set.metadata.items()
                    if key in ["processor_version", "data_sources", "processing_time_ms", "signal_quality", "layer"]
                }
        
        # Create Layer 5 metadata and merge with Layer 4 metadata
        layer5_metadata = {
            "source_layer": "layer5",
            "strategy_engine_version": "1.0.0", 
            "processing_timestamp": datetime.now(),
            "total_markets_analyzed": len(processed_signals) - 1 if "best_market" in processed_signals else 0
        }
        
        # Merge Layer 4 and Layer 5 metadata
        combined_metadata = {**layer4_metadata, **layer5_metadata}
        
        return StrategyDecision(
            market=best_market,
            action=action,
            confidence=confidence,
            size=0.0,
            timestamp=datetime.now(),
            reason="Signal-based decision",
            signal_scores={},
            metadata=combined_metadata
        )
