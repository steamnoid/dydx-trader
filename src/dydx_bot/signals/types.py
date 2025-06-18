"""
Signal types - MINIMAL code to pass ONE test only.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any


class SignalType(str, Enum):
    """Signal types - MOMENTUM, VOLUME, VOLATILITY, and ORDERBOOK."""
    MOMENTUM = "momentum"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    ORDERBOOK = "orderbook"


@dataclass
class SignalSet:
    """Signal set dataclass for holding multiple signal scores per market."""
    market: str
    momentum: float
    volume: float
    volatility: float
    orderbook: float
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Validate signal scores are within 0-100 range."""
        for score_name, score_value in [
            ("momentum", self.momentum),
            ("volume", self.volume),
            ("volatility", self.volatility),
            ("orderbook", self.orderbook)
        ]:
            if not (0 <= score_value <= 100):
                raise ValueError("Signal scores must be between 0 and 100")
