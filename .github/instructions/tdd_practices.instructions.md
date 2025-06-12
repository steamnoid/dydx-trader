````instructions
// filepath: /Users/pico/Develop/github/steamnoid/injective-trader/.github/dydx_instructions/tdd_practices.instructions.md
# dYdX v4 Perpetual Trading TDD Best Practices and Enforcement Instructions

## 🎯 PERPETUAL TRADING BOT SPECIFIC TDD STRATEGY

### MANDATORY Layer-by-Layer TDD Approach for dYdX v4:
Each layer MUST achieve 95%+ test coverage before advancing to the next layer. This ensures rock-solid foundation for autonomous perpetual trading operations where liquidation prevention is critical.

### 🔄 STRICT TDD WORKFLOW PER LAYER (dYdX v4 Focused)

```
📝 PLAN     → Define layer responsibilities for perpetual trading
❌ RED      → Write failing tests including liquidation scenarios
✅ GREEN    → Minimal code to pass all tests (margin-aware)
🔧 REFACTOR → Optimize for perpetual trading performance
📊 MEASURE  → Verify coverage including margin edge cases
🔗 INTEGRATE → Test layer integration with dYdX v4 protocol
📋 DOCUMENT → Document layer API and perpetual trading characteristics
⬆️ ADVANCE  → Move to next layer only after 95%+ coverage + margin tests
```

## 🏗️ LAYER-SPECIFIC TDD REQUIREMENTS FOR dYdX v4

### Layer 1: Data Structures & Models (Perpetual-Focused)
**TDD Focus**: Perpetual data integrity, margin validation, position serialization
- **Red**: Define all perpetual model validation scenarios (leverage, margin, funding)
- **Green**: Implement Pydantic models with perpetual-specific validation
- **Test Coverage**: 100% - critical foundation including margin calculations
- **Performance**: Memory allocation benchmarks for position tracking
- **Specific Tests**: Funding rate calculations, liquidation price accuracy, cross-margin validation

### Layer 2: WebSocket/REST Connection Layer (dYdX v4)
**TDD Focus**: dYdX v4 connection stability, reconnection, message handling
- **Red**: Connection failure scenarios, dYdX node failover, message parsing edge cases
- **Green**: Robust WebSocket/REST implementation with dydx-v4-client-py
- **Test Coverage**: 95%+ including dYdX-specific error scenarios
- **Performance**: <10ms message processing latency for liquidation-critical data
- **Specific Tests**: WebSocket timeout handling, node failover, JSON parsing errors

### Layer 3: Perpetual Market Data Processing
**TDD Focus**: Real-time perpetual data processing, funding rate tracking, margin calculations
- **Red**: Data corruption scenarios, funding rate calculation errors, liquidation price accuracy
- **Green**: Efficient perpetual data structures and cross-margin processing pipelines
- **Test Coverage**: 95%+ including malformed perpetual data handling
- **Performance**: <25ms processing latency for liquidation monitoring, memory bounds for positions
- **Specific Tests**: Mark vs index price validation, funding rate application, cross-margin updates

### Layer 4: Signal Generation Engine (Perpetual-Optimized)
**TDD Focus**: Funding-aware signal accuracy, leverage-adjusted calculations, liquidation risk signals
- **Red**: Mathematical edge cases, insufficient perpetual data scenarios, funding rate impacts
- **Green**: Signal algorithms with proper perpetual trading error handling
- **Test Coverage**: 95%+ including perpetual market edge conditions
- **Performance**: Real-time signal generation within latency limits for leveraged trading
- **Specific Tests**: Funding rate signal integration, leverage impact on signals, liquidation proximity signals

### Layer 5: Strategy Engine (Leverage-Aware)
**TDD Focus**: Perpetual decision logic, dynamic position sizing, cross-margin strategy coordination
- **Red**: Complex perpetual market scenarios, conflicting leveraged signals, margin requirement changes
- **Green**: Strategy implementation with clear perpetual trading decision paths
- **Test Coverage**: 95%+ including extreme leveraged market conditions
- **Performance**: Strategy decisions within millisecond timeframes for liquidation prevention
- **Specific Tests**: Leverage optimization, cross-margin efficiency, funding cost minimization

### Layer 6: Risk Management (Liquidation Prevention)
**TDD Focus**: Margin limits, liquidation prevention, cross-margin risk, funding rate risk
- **Red**: High-leverage scenarios, liquidation cascade simulations, funding rate shocks
- **Green**: Comprehensive perpetual risk controls and real-time margin monitoring
- **Test Coverage**: 100% - critical for liquidation prevention and capital protection
- **Performance**: Real-time margin calculation and liquidation distance monitoring
- **Specific Tests**: Liquidation prevention algorithms, cross-margin optimization, funding rate hedging

### Layer 7: Paper Trading Engine (Perpetual Simulation)
**TDD Focus**: Perpetual order simulation, funding-adjusted P&L, cross-margin account state
- **Red**: Complex leveraged trading scenarios, liquidation scenarios, funding payment simulations
- **Green**: Accurate perpetual trading simulation matching real dYdX v4 behavior
- **Test Coverage**: 95%+ including perpetual order rejection and liquidation scenarios
- **Performance**: Real-time perpetual order processing simulation with funding costs
- **Specific Tests**: Liquidation simulation accuracy, funding payment calculations, cross-margin efficiency

### Layer 8: Terminal Dashboard (Perpetual Metrics)
**TDD Focus**: Perpetual UI responsiveness, margin data display, liquidation risk visualization
- **Red**: Display edge cases, margin data formatting, liquidation distance visualization
- **Green**: Rich-based terminal interface with real-time perpetual updates
- **Test Coverage**: 95%+ including perpetual dashboard refresh scenarios
- **Performance**: <100ms dashboard refresh rate for margin monitoring
- **Specific Tests**: Liquidation price display accuracy, funding rate visualization, cross-margin status

### Layer 9: Main Application (dYdX v4 Integration)
**TDD Focus**: Full dYdX v4 system integration, autonomous perpetual operation, margin emergency recovery
- **Red**: System-wide failure scenarios, dYdX v4 integration edge cases, liquidation emergencies
- **Green**: Complete application with all perpetual trading components integrated
- **Test Coverage**: 95%+ end-to-end perpetual trading scenarios
- **Performance**: Full system within resource limits under high-leverage conditions
- **Specific Tests**: Emergency deleveraging, node failover with open positions, funding rate shock response

## 🧪 THREE-TIER TESTING ARCHITECTURE FOR PERPETUALS

### Tier 1: UNIT TESTS (Per-Layer Foundation for Perpetuals)
- **Scope**: Individual perpetual trading component functionality
- **Dependencies**: All external services mocked, including dYdX v4 APIs
- **Speed**: Milliseconds per test
- **Coverage**: 95%+ of each layer including margin edge cases
- **Focus**: Perpetual business logic, liquidation scenarios, funding rate calculations

### Tier 2: INTEGRATION TESTS (Cross-Layer Perpetual Validation)
- **Scope**: Layer-to-layer interactions for perpetual trading
- **Dependencies**: Mock dYdX v4 APIs, real internal perpetual communication
- **Speed**: Seconds per test suite
- **Coverage**: All layer interfaces and perpetual data flows
- **Focus**: Margin data transformation, cross-margin communication protocols

### Tier 3: END-TO-END TESTS (dYdX v4 System Validation)
- **Scope**: Complete perpetual trading workflows
- **Dependencies**: Real dYdX v4 testnet connections
- **Speed**: Minutes per complete perpetual scenario
- **Coverage**: Critical perpetual trading paths and liquidation recovery
- **Focus**: Real-world performance and autonomous perpetual operation

## 📋 TDD COMPLETION CRITERIA PER LAYER (dYdX v4 Specific)

### Mandatory Before Layer Advancement:
- [ ] All planned perpetual functionality implemented
- [ ] 95%+ unit test coverage achieved including margin scenarios
- [ ] All dYdX v4 integration tests passing
- [ ] Performance benchmarks within limits for leveraged trading
- [ ] Memory usage within allocated bounds for position tracking
- [ ] CPU utilization within target range for real-time margin monitoring
- [ ] Error handling covers all perpetual trading scenarios
- [ ] Documentation complete for layer API including perpetual specifics

### Perpetual Layer Quality Gates:
- **Code Quality**: Type hints, docstrings, perpetual-aware clean architecture
- **Performance**: Profiling results within targets for leveraged operations
- **Reliability**: Liquidation scenarios tested and handled
- **Maintainability**: Clear separation of concerns for perpetual trading

## 🎯 PERPETUAL TRADING-SPECIFIC TDD PATTERNS

### Perpetual Market Data Testing:
- Mock dYdX v4 perpetual data streams with realistic timing and funding rates
- Test perpetual data quality validation and error recovery
- Validate real-time processing under high-leverage load
- Test funding rate calculation accuracy and application timing

### Perpetual Signal Testing:
- Use historical perpetual data patterns for signal validation
- Test signal accuracy with known leveraged market scenarios
- Validate signal timing and latency requirements for liquidation prevention
- Test funding rate impact on signal generation

### Leveraged Strategy Testing:
- Mock complex perpetual market conditions with extreme leverage
- Test strategy performance with various liquidation scenarios
- Validate risk-adjusted returns including funding costs
- Test cross-margin efficiency optimization

### Perpetual Risk Management Testing:
- Test extreme leveraged market scenarios and liquidation cascades
- Validate position limits and liquidation prevention triggers
- Test cross-margin portfolio-level risk calculations
- Validate funding rate shock response

## 🚀 PERFORMANCE-DRIVEN TDD FOR PERPETUALS

### Memory Optimization TDD for Perpetuals:
- Write tests that validate memory usage bounds for position tracking
- Test for memory leaks in long-running perpetual trading scenarios
- Validate garbage collection behavior during position updates
- Test memory efficiency for cross-margin calculations

### CPU Optimization TDD for Perpetuals:
- Benchmark critical path performance for liquidation monitoring
- Test algorithmic complexity with large perpetual position datasets
- Validate real-time processing capabilities under margin pressure
- Test funding rate calculation performance

### Latency Optimization TDD for Perpetuals:
- Test end-to-end latency measurements for liquidation prevention
- Validate dYdX v4 message processing speed for margin-critical data
- Test dashboard refresh performance for real-time margin monitoring
- Validate liquidation distance calculation speed

## 📊 CONTINUOUS TESTING VALIDATION FOR PERPETUALS

### Automated Test Execution for dYdX v4:
- Unit tests run on every code change including margin scenarios
- Integration tests run on layer completion with dYdX v4 mocks
- E2E tests run on milestone completion with testnet
- Performance tests run on optimization changes under leverage

### Perpetual Coverage Monitoring:
- Real-time coverage tracking per layer including liquidation scenarios
- Coverage regression prevention for margin-critical code paths
- Mandatory coverage gates before advancement including perpetual edge cases

### Perpetual Performance Regression Prevention:
- Automated performance benchmarking for leveraged operations
- Memory usage regression detection for position tracking
- Latency regression prevention for liquidation monitoring
- Funding rate calculation performance validation

## 🛡️ dYdX v4 SPECIFIC TESTING REQUIREMENTS

### Protocol Integration Testing:
- Test dYdX v4 gRPC client integration and error handling
- Validate WebSocket subscription accuracy for perpetual markets
- Test REST API integration for account and position queries
- Validate protobuf message parsing for all dYdX v4 message types

### Perpetual Market Structure Testing:
- Test funding rate calculation accuracy against dYdX v4 specification
- Validate liquidation price calculation matching dYdX v4 behavior
- Test cross-margin requirement calculations
- Validate mark price vs index price handling

### Risk Management Testing for Perpetuals:
- Test liquidation prevention algorithms under various scenarios
- Validate emergency deleveraging response procedures
- Test funding rate shock response and hedging mechanisms
- Validate cross-margin optimization algorithms

### Performance Testing for Perpetuals:
- Test system performance under maximum leverage conditions
- Validate real-time margin monitoring performance
- Test liquidation distance calculation speed and accuracy
- Validate funding rate processing performance during rate changes
````
