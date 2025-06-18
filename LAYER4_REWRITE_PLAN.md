# Layer 4 Rewrite Plan - Continuous Signal Scoring Architecture

## Current Problems
1. **Missing Continuous Scoring**: Only discrete signals, no 0-100 opportunity scores
2. **No Multi-Market Interface**: Layer 5 can't compare signals across markets
3. **Signal Structure Issues**: Focused on discrete events, not continuous assessment
4. **Missing Real-Time Scoring**: Only generates signals on threshold crossings

## Required Rewrites

### 1. SignalTypes.py - Add Continuous Scoring
```python
@dataclass
class ContinuousSignalScore:
    """Continuous opportunity score (0-100) for a market"""
    market_id: str
    opportunity_score: float  # 0-100, higher = better opportunity
    confidence: float  # 0-1, how confident we are in this score
    trend_strength: float  # -1 to 1, bearish to bullish
    volatility_score: float  # 0-1, market volatility level
    volume_score: float  # 0-1, volume relative to average
    timestamp: float
    
    # Component scores that make up the opportunity_score
    momentum_score: float = 0.0  # 0-100
    mean_reversion_score: float = 0.0  # 0-100
    volume_signal_score: float = 0.0  # 0-100
    breakout_score: float = 0.0  # 0-100
    
    # Supporting data for Layer 5 decisions
    risk_factors: Dict[str, float] = field(default_factory=dict)
    market_conditions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DiscreteSignal:
    """Discrete signal when threshold is crossed"""
    signal_type: SignalType
    market_id: str
    trigger_price: float
    opportunity_score: float  # Score at time of trigger
    confidence: float
    timestamp: float
    
    # Context from continuous scoring
    score_history: List[float] = field(default_factory=list)  # Last 10 scores
    threshold_crossed: float = 0.0  # What threshold triggered this
```

### 2. SignalEngine.py - Add Continuous Scoring Engine
```python
class ContinuousSignalEngine:
    """
    Continuous signal scoring engine for multi-market comparison
    
    Provides:
    - Real-time opportunity scores (0-100) updated every market tick
    - Discrete signal triggers when thresholds are crossed
    - Standardized interface for multi-market comparison
    - Historical performance tracking
    """
    
    def __init__(self, market_id: str):
        self.market_id = market_id
        self.current_score: Optional[ContinuousSignalScore] = None
        self.score_history: deque = deque(maxlen=1000)
        self.discrete_signals: deque = deque(maxlen=100)
        
        # Scoring weights (can be tuned)
        self.scoring_weights = {
            'momentum': 0.3,
            'mean_reversion': 0.2,
            'volume': 0.2,
            'breakout': 0.3
        }
        
        # Thresholds for discrete signals
        self.signal_thresholds = {
            'buy_threshold': 75,  # Opportunity score > 75 = BUY signal
            'sell_threshold': 25,  # Opportunity score < 25 = SELL signal
            'confidence_minimum': 0.6  # Only trigger if confidence > 60%
        }
    
    async def calculate_continuous_score(self) -> ContinuousSignalScore:
        """Calculate real-time opportunity score (0-100)"""
        
    def get_current_opportunity_score(self) -> float:
        """Get current opportunity score for Layer 5 comparison"""
        
    def get_market_assessment(self) -> Dict[str, Any]:
        """Get comprehensive market assessment for Layer 5"""
        
    def check_discrete_signal_triggers(self) -> List[DiscreteSignal]:
        """Check if any discrete signal thresholds are crossed"""
```

### 3. New Multi-Market Interface for Layer 5
```python
class MultiMarketSignalAggregator:
    """
    Aggregates signals from multiple Layer 4 engines for Layer 5 consumption
    
    Provides standardized interface for multi-market sniper decisions
    """
    
    def __init__(self, markets: List[str]):
        self.markets = markets
        self.signal_engines: Dict[str, ContinuousSignalEngine] = {}
        
    async def get_market_opportunities(self) -> Dict[str, float]:
        """Get opportunity scores for all markets"""
        
    async def get_best_opportunity(self) -> Tuple[str, float]:
        """Get market with highest opportunity score"""
        
    async def get_market_rankings(self) -> List[Tuple[str, float]]:
        """Get markets ranked by opportunity score"""
        
    async def get_portfolio_allocation_data(self) -> Dict[str, Any]:
        """Get data needed for portfolio allocation decisions"""
```

## Implementation Priority

### Phase 1: Core Continuous Scoring (THIS WEEK)
1. Rewrite `signal_types.py` with `ContinuousSignalScore` and `DiscreteSignal`
2. Rewrite `engine.py` to provide continuous scoring
3. Update existing unit tests to work with new architecture
4. Ensure 95%+ test coverage maintained

### Phase 2: Multi-Market Interface (NEXT WEEK)
1. Create `MultiMarketSignalAggregator` class
2. Add Layer 4 → Layer 5 interface specifications
3. Create integration tests for multi-market scenarios
4. Update Signal Detection Panel to show continuous scores

### Phase 3: Enhanced Signal Generation (FOLLOWING WEEK)
1. Improve scoring algorithms for better market assessment
2. Add machine learning components for score optimization
3. Add historical performance tracking
4. Tune thresholds based on backtesting

## Benefits of Rewrite

### For Layer 5 (Strategies):
1. **Easy Market Comparison**: Compare BTC=85%, ETH=72%, SOL=45% opportunity scores
2. **Portfolio Allocation**: Allocate capital based on opportunity scores
3. **Risk Assessment**: Use confidence and volatility scores for risk management
4. **Dynamic Thresholds**: Adjust strategy based on market conditions

### For Overall Architecture:
1. **Clean Separation**: Layer 4 = single-market scoring, Layer 5 = multi-market decisions
2. **Scalable**: Easy to add new markets (just add new Layer 4 engine)
3. **Testable**: Clear interfaces make testing much easier
4. **Maintainable**: Well-defined responsibilities for each layer

## Current Implementation Status
- Layer 4 Core Logic: 96% coverage (needs rewrite for continuous scoring)
- Layer 4 Panels: Working but showing discrete signals only
- Layer 4 E2E Tests: Passing but testing old architecture

## Risk Mitigation
- Keep existing tests passing during rewrite
- Implement new architecture alongside old one initially
- Migrate gradually to avoid breaking existing functionality
- Maintain backward compatibility where possible

**RECOMMENDATION**: Start rewrite immediately. The current architecture cannot support proper multi-market sniper decisions.
