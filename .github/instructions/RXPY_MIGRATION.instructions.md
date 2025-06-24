````instructions
# RxPY Reactive Programming Migration Plan

## MISSION: REACTIVE STREAMING ARCHITECTURE
**Transform dYdX v4 trading bot from callback/batch processing to unified RxPY streaming architecture**

## MIGRATION STRATEGY: INCREMENTAL REFACTOR

### Decision Rationale
- **REFACTOR (not rewrite)**: Strong foundation with 86.23% test coverage
- **Proven Architecture**: Layer separation, clear dependencies, comprehensive tests
- **Migration Path**: Clear upgrade path from callbacks to RxPY Observables
- **Risk Mitigation**: Maintain existing functionality during transition

### Performance Problem Analysis
**Current State**:
- Layer 4 (Signals): Subsecond performance ✅
- Layer 5 (Strategy): ~3 second degradation ❌
- **Root Cause**: Batch processing, per-market engine instantiation, callback inefficiency

**Target State with RxPY**:
- End-to-end streaming: <1 second latency
- Single engine instances (not per-market)
- Unified data flow with reactive operators
- True streaming from WebSocket to final decisions

## RXPY ARCHITECTURE DESIGN

### Reactive Data Flow
```
dYdX WebSocket → Observable<MarketData>
    ↓ share(), retry(), catch()
Layer 2: Connection Management
    ↓ map(), filter(), throttle()
Layer 3: Data Processing  
    ↓ window(), buffer(), scan()
Layer 4: Signal Scoring
    ↓ combine_latest(), merge(), debounce()
Layer 5: Strategy Decisions
    ↓ distinct_until_changed(), sample()
Layer 6+: Risk & Trading
```

### Key RxPY Operators by Layer
- **Layer 2**: `share()`, `retry()`, `catch()`, `connect_observable()`
- **Layer 3**: `map()`, `filter()`, `window()`, `buffer()`, `scan()`
- **Layer 4**: `combine_latest()`, `merge()`, `throttle()`, `scan()`
- **Layer 5**: `debounce()`, `distinct_until_changed()`, `sample()`

### Engine Architecture Change
**Before (Current)**:
```python
# One engine instance per market
btc_momentum_engine = MomentumSignalEngine("BTC-USD")
eth_momentum_engine = MomentumSignalEngine("ETH-USD")
# Result: Multiple instances, batch processing
```

**After (RxPY)**:
```python
# Single engine instance, processes all markets
momentum_engine = ReactiveSignalEngine()
momentum_scores = market_data_stream.pipe(
    momentum_engine.calculate_scores()  # Processes all markets
)
# Result: Single instance, streaming processing
```

## MIGRATION PHASES

### Phase 1: Layer 2 WebSocket Streaming
**Target**: Convert WebSocket callbacks to Observable<MarketData>

#### Current Implementation
```python
# Callback-based (current)
def on_message(self, ws, message):
    data = parse_message(message)
    self.callback_handler(data)
```

#### RxPY Implementation  
```python
# Observable-based (target)
def market_data_stream(self) -> Observable:
    return Observable.create(self._websocket_observer).pipe(
        map(parse_message),
        share(),  # Share stream across subscribers
        retry(3),  # Connection resilience
        catch(handle_error)
    )
```

#### Testing Strategy
- Use RxPY TestScheduler for predictable timing
- Marble testing for stream validation
- Mock WebSocket for test isolation

### Phase 2: Layer 3 Reactive Data Processing
**Target**: Transform processors to RxPY operators

#### Current Implementation
```python
# Callback-based processing (current)
def process_market_data(self, data):
    processed = self.transform_data(data)
    self.notify_subscribers(processed)
```

#### RxPY Implementation
```python
# Reactive processing (target)
def processed_data_stream(self, source: Observable) -> Observable:
    return source.pipe(
        map(self.transform_data),
        window(timedelta(seconds=1)),  # Time-based windows
        flat_map(lambda w: w.buffer_with_count(10)),  # Batch processing
        filter(lambda batch: len(batch) > 0)
    )
```

### Phase 3: Layer 4 Reactive Signal Engines
**Target**: Single-instance engines with Observable<SignalScores>

#### Current Implementation
```python
# Per-market engines (current)
class MomentumSignalEngine:
    def __init__(self, market_id: str):
        self.market_id = market_id  # Tied to specific market
    
    def calculate_score(self, data) -> float:
        # Batch calculation for single market
```

#### RxPY Implementation
```python
# Single-instance reactive engine (target)
class ReactiveSignalEngine:
    def calculate_momentum_scores(self) -> OperatorFunction:
        return compose(
            map(lambda data: self._extract_momentum_data(data)),
            scan(self._accumulate_momentum, initial_state),
            map(lambda state: self._calculate_score(state)),
            throttle(timedelta(milliseconds=100))  # Rate limiting
        )
```

#### Benefits
- **Single Instance**: One MomentumEngine for all markets
- **Streaming**: Continuous Observable<SignalScore> output
- **Performance**: No per-market instantiation overhead
- **Composability**: Operators can be combined and tested independently

### Phase 4: Layer 5 Reactive Strategy Engine
**Target**: Multi-market reactive decision making

#### Current Implementation
```python
# Batch-based strategy (current)
def execute_strategy(self):
    signals = self.collect_all_signals()  # Blocking collection
    decision = self.analyze_signals(signals)  # Batch analysis
    return decision
```

#### RxPY Implementation
```python
# Reactive strategy (target)
def strategy_decisions(self, *signal_streams) -> Observable:
    return combine_latest(*signal_streams).pipe(
        map(self.analyze_combined_signals),
        debounce(timedelta(milliseconds=500)),  # Avoid rapid decisions
        distinct_until_changed(),  # Only emit when decision changes
        filter(lambda decision: decision.confidence > 0.8)
    )
```

### Phase 5: Integration & Performance Validation
**Target**: End-to-end streaming validation

#### Performance Tests
```python
@pytest.mark.asyncio 
async def test_end_to_end_streaming_performance():
    """Validate <1 second end-to-end latency"""
    scheduler = TestScheduler()
    
    # Mock market data stream
    market_data = scheduler.create_hot_observable(
        on_next(0, market_data_btc),
        on_next(100, market_data_eth)
    )
    
    # Full pipeline
    decisions = market_data.pipe(
        data_processor.process(),
        signal_engine.calculate_scores(),
        strategy_engine.make_decisions()
    )
    
    # Measure latency
    start_time = scheduler.clock
    result = scheduler.start(lambda: decisions, create=0, subscribed=0, disposed=1000)
    end_time = scheduler.clock
    
    latency = end_time - start_time
    assert latency < 1000  # <1 second target
```

## TESTING STRATEGY

### RxPY Testing Requirements
1. **TestScheduler**: Virtual time testing for predictable timing
2. **Marble Testing**: Visual Observable stream validation
3. **Mock Streams**: Isolated testing with controlled data
4. **Performance Testing**: Latency and throughput validation

### Example Test Patterns
```python
def test_momentum_signal_calculation():
    """Test reactive momentum signal calculation"""
    scheduler = TestScheduler()
    
    # Input stream
    market_data = scheduler.create_hot_observable(
        on_next(100, {"price": 50000, "volume": 100}),
        on_next(200, {"price": 51000, "volume": 150}),
        on_next(300, {"price": 50500, "volume": 120})
    )
    
    # Apply signal engine
    signal_engine = ReactiveSignalEngine()
    result = scheduler.start(
        lambda: market_data.pipe(
            signal_engine.calculate_momentum_scores()
        )
    )
    
    # Expected outcomes
    expected = [
        on_next(100, 50.0),  # Initial neutral score
        on_next(200, 75.0),  # Positive momentum
        on_next(300, 60.0)   # Slight pullback
    ]
    
    assert result.messages == expected
```

### Migration Testing Approach
1. **Parallel Implementation**: Build RxPY alongside existing code
2. **A/B Testing**: Compare outputs between callback and RxPY versions
3. **Performance Benchmarking**: Validate latency improvements
4. **Gradual Cutover**: Layer-by-layer migration with fallbacks

## IMPLEMENTATION CHECKLIST

### Dependencies
- [ ] Add RxPY (reactivex) to pyproject.toml
- [ ] Add RxPY TestScheduler to test dependencies
- [ ] Update type hints for Observable types

### Layer 2 (Connection)
- [ ] Convert WebSocket callbacks to Observable<MarketData>
- [ ] Add connection resilience operators (retry, catch)
- [ ] Implement shared Observable stream
- [ ] Add TestScheduler tests for connection behavior

### Layer 3 (Data Processing)
- [ ] Transform processors to RxPY operators
- [ ] Add time-based windowing for data aggregation
- [ ] Implement reactive data validation
- [ ] Add marble tests for data transformations

### Layer 4 (Signal Engines)
- [ ] Refactor to single-instance reactive engines
- [ ] Replace batch calculations with streaming operators
- [ ] Add Observable<SignalScore> outputs
- [ ] Add performance tests for signal latency

### Layer 5 (Strategy)
- [ ] Implement reactive multi-market strategy decisions
- [ ] Add combine_latest for signal correlation
- [ ] Add debouncing for decision stability
- [ ] Add integration tests across layers

### Performance Validation
- [ ] End-to-end latency testing (<1 second target)
- [ ] Memory usage validation (maintain <512MB)
- [ ] CPU utilization testing (maintain <25%)
- [ ] Throughput testing under high-frequency data

## RISK MITIGATION

### Backward Compatibility
- Maintain existing interfaces during migration
- Use adapter pattern for gradual transition
- Keep original implementations as fallbacks

### Testing Safety
- Comprehensive test coverage before migration
- Parallel testing of old vs new implementations
- Performance regression testing

### Performance Monitoring
- Real-time latency monitoring during migration
- Memory usage tracking
- CPU utilization alerts
- Automatic rollback triggers for performance degradation

## SUCCESS CRITERIA

### Performance Targets
- [x] Layer 4: Maintain subsecond performance
- [ ] Layer 5: Reduce from 3s to <1s (67% improvement)
- [ ] End-to-end: <1s latency target
- [ ] Memory: Maintain <512MB usage
- [ ] CPU: Maintain <25% utilization

### Architectural Goals
- [ ] Single engine instances (not per-market)
- [ ] Unified Observable data flow
- [ ] Reactive operators throughout pipeline
- [ ] Testable stream compositions
- [ ] Maintainable reactive architecture

### Quality Assurance
- [ ] Maintain 95%+ test coverage
- [ ] All existing tests continue to pass
- [ ] New RxPY-specific tests added
- [ ] Performance benchmarks established
- [ ] Documentation updated for reactive patterns

## NEXT STEPS
1. Add RxPY dependency to project
2. Create initial Observable<MarketData> stream in Layer 2
3. Add TestScheduler testing infrastructure
4. Begin incremental migration with Layer 2
5. Validate performance improvements at each phase
````
