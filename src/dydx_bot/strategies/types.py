"""
Strategy types - MINIMAL code to pass ONE test only.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class StrategyDecision:
    """Strategy decision dataclass for trading decisions."""
    market: str
    action: str
    confidence: float
    size: float
    timestamp: datetime
    reason: str
    signal_scores: Dict[str, int]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Validate action is valid enum value."""
        valid_actions = ["BUY", "SELL", "HOLD"]
        if self.action not in valid_actions:
            raise ValueError("Action must be BUY, SELL, or HOLD")
