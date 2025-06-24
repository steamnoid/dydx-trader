# dYdX v4 Technical Architecture - RxPY Reactive Streaming

## ARCHITECTURAL PARADIGM SHIFT: RxPY/REACTIVE PROGRAMMING

### Migration Strategy: REFACTOR (NOT REWRITE)
**Decision**: Incremental refactor to RxPY/reactive programming starting from Layer 2 upward
**Rationale**: Strong foundation, 86.23% test coverage, clear migration path, proven components
**Target**: Unified streaming data flow with each layer adding reactive operators to the stream

### RxPY Reactive Architecture
```
Layer 2 (Connection) → Observable<MarketData>
    ↓ map(), filter(), share()
Layer 3 (Data) → Observable<ProcessedData>  
    ↓ window(), buffer(), scan()
Layer 4 (Signals) → Observable<SignalScores>
    ↓ combine_latest(), merge(), throttle()
Layer 5 (Strategy) → Observable<StrategyDecisions>
    ↓ debounce(), distinct_until_changed()
Layer 6+ → Observable<Actions>
```

**Key Benefits**:
- True streaming from WebSocket to final decisions
- Single engine instances (not per-market)
- Unified error handling and backpressure
- Composable, testable stream operators
- Sub-second end-to-end latency

## Project Structure
```
src/dydx_bot/
├── main.py                 # Entry point
├── config/                 # Configuration
├── connection/             # Layer 2: RxPY WebSocket streams
├── data/                   # Layer 3: Reactive data processing
├── signals/                # Layer 4: Streaming signal scoring
├── strategies/             # Layer 5: Reactive multi-market strategies
├── risk/                   # Layer 6: Risk management
├── trading/                # Layer 7: Paper trading
└── dashboard/              # Layer 8: Terminal UI

tests/
├── unit/                   # Layer-specific unit tests
├── integration/            # Cross-layer integration
└── e2e/                    # Real dYdX testnet tests
```

## Layer Dependencies & Architectural Flow
- Each layer depends only on previous layers
- Layer 2 (connection) is foundation - ✅ COMPLETED (86.23% coverage)
- No circular dependencies
- Real dydx-v4-client in production, mocks only in tests
- **NEW**: RxPY streams flow upward through all layers starting Layer 2
- Real dydx-v4-client in production, mocks only in tests

### Reactive Signal Architecture (Layer 4):
- **Single Signal Engine per Signal Type**: One momentum engine, one volume engine, etc. (not per-market)
- **Streaming Continuous Signals**: Observable<SignalScores> with reactive operators (map, scan, combine_latest)
- **Multi-Market Processing**: Single engine instance processes all markets via shared WebSocket stream
- **No Discrete Signals**: Pure continuous scoring Observable streams (0-100), no threshold-based triggers
- **RxPY Operators**: Uses window(), scan(), combine_latest() for real-time signal calculations
- **Shared Observable Stream**: ALL signal engines subscribe to same WebSocket Observable (CRITICAL: no multiple connections)
- **High-Frequency Updates**: Signal score Observables emit with every market data tick
- **Rich Signal Interface**: Multiple Observable<SignalScore> streams per market for Layer 5+ consumption

### Reactive Strategy Architecture (Layer 5+):
- **Multi-Market Reactive Logic**: Combines multiple Observable<SignalScores> streams across multiple markets using combine_latest(), merge()
- **Cross-Market Decision Streams**: Observable<StrategyDecision> using reactive operators for portfolio allocation
- **Reactive Strategy Engine**: Orchestrates multiple signal Observable streams using RxPY operators (throttle, debounce, distinct_until_changed)
- **Position Management**: Observable<PositionUpdate> streams for multi-position portfolio decisions
- **Threshold Management**: Applies reactive operators (filter, map) to signal Observable streams for discrete decisions
- **Signal Weighting**: Uses combine_latest(), map() to weight different signal Observable streams for market prioritization

## Key Patterns
- **Reactive Streams**: RxPY Observable streams with operators throughout architecture
- **Observer**: Market data notifications via Observable<MarketData>
- **Strategy**: Pluggable reactive strategies with Observable<StrategyDecision> streams  
- **State Machine**: Connection management with Observable<ConnectionState>
- **Circuit Breaker**: dYdX connection resilience via retry(), catch() operators
- **Singleton**: Single WebSocket Observable shared across ALL signal engines and markets
- **Continuous Scoring**: Real-time signal opportunity scoring via Observable<SignalScore> streams (Layer 4)
- **Reactive Triggers**: Threshold-based signal generation using filter(), map() operators (Layer 4)
- **Multi-Market Orchestration**: Cross-market decision engine via combine_latest(), merge() (Layer 5+)

## RxPY Migration Phases

### Phase 1: Layer 2 WebSocket → Observable<MarketData>
- Convert WebSocket callback system to RxPY Observable
- Add operators: share(), retry(), catch() for connection resilience
- Maintain backward compatibility during migration

### Phase 2: Layer 3 Data Processing → Observable<ProcessedData>
- Transform data processors to RxPY operators (map, filter, scan)
- Add window(), buffer() for time-based data aggregation
- Connect to Layer 2 Observable stream

### Phase 3: Layer 4 Signal Engines → Observable<SignalScores>
- Refactor to single engine instances (not per-market)
- Convert to reactive signal calculations using scan(), combine_latest()
- Subscribe to Layer 3 Observable stream

### Phase 4: Layer 5+ Strategy → Observable<StrategyDecisions>
- Transform multi-market logic to reactive operators
- Use throttle(), debounce(), distinct_until_changed()
- Subscribe to multiple Layer 4 Observable streams

### Phase 5: Integration & Testing
- End-to-end RxPY stream validation
- Performance testing: sub-second latency target
- Migration completion and cleanup

## dYdX v4 Integration Points
- **IndexerSocket**: Real-time perpetual data (WebSocket)
- **IndexerClient**: Account queries, historical data (REST)
- **NodeClient**: Order placement, blockchain operations
- **Wallet**: Authentication and signing

## Performance Requirements
- <512MB memory (fixed allocation preferred)
- <25% CPU utilization
- <25ms liquidation risk calculations
- >99.9% connection uptime
