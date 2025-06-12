````instructions
// filepath: /Users/pico/Develop/github/steamnoid/injective-trader/.github/dydx_instructions/testing_strategy.instructions.md
# dYdX v4 Perpetual Trading Comprehensive Testing Strategy Instructions

## 🎯 PERPETUAL TRADING BOT TESTING PYRAMID

```
                    /\
                   /  \
                  /E2E \     <- Real dYdX v4 + Full Perpetual Trading Flows
                 /______\
                /        \
               /INTEGRATION\ <- Multi-layer + Mock dYdX v4 APIs
              /__________\
             /            \
            /   UNIT TESTS  \ <- Individual layer logic (dYdX mocked)
           /________________\
```

## 🔄 THREE-TIER TESTING STRATEGY FOR dYdX v4

### Tier 1: UNIT TESTS (Foundation - 95%+ Coverage Required for Perpetuals)
- **Scope**: Individual perpetual trading layer components
- **Dependencies**: All external dependencies mocked (dYdX v4 APIs, gRPC, WebSocket)
- **Purpose**: Perpetual logic validation, margin edge cases, liquidation scenarios
- **Speed**: <1ms per test
- **Coverage**: 95%+ mandatory dla każdej warstwy including margin scenarios

### Tier 2: INTEGRATION TESTS (Perpetual Layer Interactions)
- **Scope**: Multi-layer perpetual trading interactions
- **Dependencies**: Mix of real i mocked dYdX v4 components
- **Purpose**: Cross-margin data flow validation, liquidation prevention interface compatibility
- **Speed**: <1s per test
- **Coverage**: All perpetual layer boundaries and margin calculations

### Tier 3: E2E TESTS (Real dYdX v4 Perpetual Trading Simulation)
- **Scope**: Complete perpetual trading workflows
- **Dependencies**: Real dYdX v4 testnet/mainnet connections
- **Purpose**: System validation, leveraged performance verification, liquidation prevention
- **Speed**: Minutes per complete perpetual scenario
- **Coverage**: Critical perpetual trading paths and emergency procedures

## 📋 LAYER-SPECIFIC TESTING REQUIREMENTS FOR dYdX v4

### Layer 1: Data Structures & Models (Perpetual-Focused)
```
Unit Tests (Mandatory):
- Perpetual model validation with valid/invalid margin data
- Position serialization/deserialization accuracy
- Funding rate calculation validation
- Cross-margin requirement calculations
- Liquidation price computation accuracy
- Memory usage validation for position tracking
- Performance benchmarks dla large perpetual datasets

Integration Tests:
- Perpetual model compatibility across layers
- Cross-margin data transformation accuracy
- Position state management across components
```

### Layer 2: WebSocket/REST Connection Layer (dYdX v4)
```
Unit Tests (Mandatory):
- dYdX v4 WebSocket connection establishment/failure scenarios
- JSON message parsing with malformed data
- Node failover and reconnection logic
- Rate limiting behavior dla dYdX v4 APIs
- WebSocket subscription management dla perpetuals
- Memory leak prevention during connection management

Integration Tests:
- Real WebSocket connection to dYdX v4 testnet
- WebSocket perpetual data subscription accuracy
- Message flow to perpetual data processing layer
- Connection recovery under stress with open positions

E2E Tests:
- Extended connection stability (24h+) with live positions
- Perpetual market data accuracy verification
- Node failover behavior with active margin monitoring
```

### Layer 3: Perpetual Market Data Processing
```
Unit Tests (Mandatory):
- Perpetual OHLCV calculation accuracy
- Funding rate calculation and application
- Mark vs index price processing
- Cross-margin position value updates
- Liquidation price real-time calculation
- Circular buffer behavior for perpetual data
- Data quality validation dla margin-critical data
- Performance under high perpetual message rates

Integration Tests:
- dYdX v4 WebSocket data to processed perpetual data pipeline
- Signal engine perpetual data consumption
- Memory usage under continuous margin monitoring
- Cross-margin calculation pipeline accuracy

E2E Tests:
- Real perpetual market data processing accuracy
- Performance under real high-volatility conditions
- Funding rate application accuracy validation
```

### Layer 4: Signal Generation Engine (Perpetual-Optimized)
```
Unit Tests (Mandatory):
- Perpetual mathematical calculations accuracy
- Funding rate-aware signal threshold logic
- Leverage-adjusted signal generation
- Edge cases (insufficient data, extreme leverage scenarios)
- Performance dla real-time liquidation prevention requirements
- Signal history management dla perpetual strategies

Integration Tests:
- Perpetual market data to signal pipeline
- Funding rate impact on signal generation
- Signal consumption by leveraged strategy engine
- Signal accuracy with real perpetual data patterns

E2E Tests:
- Signal generation under real perpetual market conditions
- Signal timing and latency validation dla liquidation prevention
- Funding rate signal integration accuracy
```

### Layer 5: Strategy Engine (Leverage-Aware)
```
Unit Tests (Mandatory):
- Perpetual strategy decision logic
- Dynamic position sizing with margin requirements
- Cross-margin strategy coordination
- Strategy selection algorithms dla leveraged positions
- Performance under various perpetual market conditions
- Funding-adjusted return calculations

Integration Tests:
- Perpetual signal to strategy decision pipeline
- Cross-margin risk management integration
- Multi-strategy coordination dla perpetuals
- Leverage optimization algorithms

E2E Tests:
- Strategy performance with real perpetual market data
- Strategy adaptation to funding rate changes
- Cross-margin efficiency optimization validation
```

### Layer 6: Risk Management (Liquidation Prevention)
```
Unit Tests (Mandatory - 100% Coverage):
- Cross-margin position limit enforcement
- Liquidation prevention trigger logic
- Portfolio-wide margin calculations
- Funding rate risk assessment
- Maximum leverage enforcement
- Emergency deleveraging procedures

Integration Tests:
- Strategy to perpetual risk management pipeline
- Liquidation prevention override scenarios
- Emergency shutdown procedures with open positions
- Cross-margin rebalancing algorithms

E2E Tests:
- Risk management under extreme perpetual market conditions
- Portfolio protection validation during liquidation cascades
- Funding rate shock response testing
```

### Layer 7: Paper Trading Engine (Perpetual Simulation)
```
Unit Tests (Mandatory):
- Perpetual order simulation accuracy
- Funding-adjusted P&L calculation precision
- Cross-margin account state management
- Liquidation scenario simulation
- Order rejection scenarios dla insufficient margin
- Funding payment simulation accuracy

Integration Tests:
- Strategy to perpetual paper trading pipeline
- Real-time perpetual order processing
- Cross-margin balance updates
- Liquidation prevention simulation

E2E Tests:
- Complete perpetual trading simulations
- Paper trading vs real dYdX v4 comparison
- Funding cost accuracy validation
```

### Layer 8: Terminal Dashboard (Perpetual Metrics)
```
Unit Tests (Mandatory):
- Perpetual UI component rendering
- Margin data formatting accuracy
- Liquidation distance display accuracy
- User interaction handling dla perpetual controls
- Performance under high-frequency perpetual data load
- Error state display dla margin scenarios

Integration Tests:
- Real-time perpetual data display pipeline
- Dashboard responsiveness during margin updates
- Memory usage during continuous position display
- Funding rate visualization accuracy

E2E Tests:
- Complete perpetual dashboard functionality
- Long-running display stability with live positions
- Liquidation alert system validation
```

### Layer 9: Main Application (dYdX v4 Integration)
```
Unit Tests (Mandatory):
- Application lifecycle management dla perpetuals
- dYdX v4 configuration loading/validation
- Component initialization dla perpetual trading
- Shutdown procedures with open positions
- Error recovery mechanisms dla margin scenarios

Integration Tests:
- Full dYdX v4 system integration
- Component interaction validation dla perpetuals
- Resource management under leverage
- Cross-margin coordination across components

E2E Tests:
- Complete autonomous perpetual operation
- 24/7 stability testing with live positions
- Recovery from various failure scenarios with margin preservation
```

## 🧪 SPECIALIZED PERPETUAL TRADING BOT TESTING

### Perpetual Market Data Testing:
- **Mock Perpetual Scenarios**: Bull/bear markets, funding rate volatility
- **Data Quality Testing**: Corrupted perpetual data, missing funding rates
- **Performance Testing**: High-frequency perpetual data processing
- **Stress Testing**: Extreme leverage and volatility conditions
- **Funding Rate Testing**: Various funding rate scenarios and calculations

### Perpetual Trading Logic Testing:
- **Strategy Backtesting**: Historical perpetual data simulation
- **Liquidation Scenario Testing**: Various liquidation cascade scenarios
- **Performance Testing**: Decision speed under margin pressure
- **Risk Scenario Testing**: Maximum liquidation risk scenarios
- **Cross-Margin Testing**: Margin efficiency optimization validation

### Real-time Perpetual Performance Testing:
- **Liquidation Prevention Latency**: Real-time margin monitoring speed
- **Throughput Testing**: Maximum perpetual message handling
- **Memory Testing**: Long-running stability with open positions
- **CPU Testing**: Processing efficiency under high leverage

## 📊 TESTING AUTOMATION FOR dYdX v4

### Continuous Perpetual Testing Pipeline:
- **Pre-commit**: Unit tests dla changed layers including margin scenarios
- **Layer Completion**: Full layer test suite with perpetual edge cases
- **Integration**: Cross-layer integration tests with dYdX v4 mocks
- **Milestone**: Complete E2E test suite with testnet

### Perpetual Performance Regression Testing:
- **Automated Benchmarks**: Perpetual trading performance tracking over time
- **Memory Regression**: Memory usage monitoring dla position tracking
- **Latency Regression**: Liquidation prevention processing time monitoring
- **Coverage Regression**: Test coverage monitoring including margin scenarios

## 🎯 TESTING TOOLS AND FRAMEWORKS FOR dYdX v4

### Unit Testing for Perpetuals:
- **pytest**: Core testing framework
- **pytest-asyncio**: Async test support dla gRPC/WebSocket
- **pytest-mock**: Sophisticated mocking dla dYdX v4 APIs
- **pytest-cov**: Coverage reporting including margin scenarios

### Perpetual Performance Testing:
- **memory_profiler**: Memory usage analysis dla position tracking
- **cProfile**: CPU profiling dla margin calculations
- **pytest-benchmark**: Performance benchmarks dla perpetual operations
- **asyncio profiling**: Async performance analysis dla dYdX v4 connections

### dYdX v4 Integration Testing:
- **pytest-xdist**: Parallel test execution
- **pytest-timeout**: Test timeout management dla gRPC calls
- **real dYdX v4 testnet**: Live perpetual integration testing
- **grpcio-testing**: gRPC client testing utilities

### Perpetual E2E Testing:
- **Real perpetual market data**: Actual leveraged trading scenarios
- **Extended runs**: Long-term stability testing with positions
- **Stress testing**: Extreme perpetual condition validation
- **Liquidation simulation**: Comprehensive liquidation scenario testing

## 🚀 TESTING QUALITY GATES FOR dYdX v4

### Perpetual Layer Advancement Criteria:
- [ ] 95%+ unit test coverage including margin scenarios
- [ ] All dYdX v4 integration tests passing
- [ ] Performance within limits dla perpetual operations
- [ ] Memory usage within bounds dla position tracking
- [ ] Liquidation scenarios covered and tested
- [ ] Documentation complete dla perpetual functionality

### Perpetual Release Criteria:
- [ ] All layers at 95%+ coverage including margin edge cases
- [ ] E2E tests passing with dYdX v4 testnet
- [ ] 24h stability test passed with simulated positions
- [ ] Performance benchmarks met dla leveraged operations
- [ ] Security testing passed dla perpetual trading
- [ ] Complete perpetual trading documentation

## 🛡️ dYdX v4 SPECIFIC TESTING REQUIREMENTS

### Protocol Testing:
- **gRPC Client Testing**: Complete dYdX v4 gRPC client validation
- **WebSocket Testing**: Real-time data subscription accuracy
- **REST API Testing**: Account and position query validation
- **Protobuf Testing**: Message parsing and validation
- **Rate Limiting Testing**: API rate limit compliance

### Perpetual Market Structure Testing:
- **Funding Rate Testing**: Calculation accuracy and timing
- **Liquidation Testing**: Liquidation price and process accuracy
- **Cross-Margin Testing**: Margin requirement calculations
- **Mark Price Testing**: Mark vs index price handling
- **Position Testing**: Position state management accuracy

### Risk Management Testing for Perpetuals:
- **Liquidation Prevention**: Algorithm testing under various scenarios
- **Emergency Procedures**: Deleveraging and emergency response testing
- **Funding Risk**: Funding rate shock response validation
- **Margin Monitoring**: Real-time margin tracking accuracy
- **Portfolio Risk**: Cross-margin portfolio risk calculations

### Performance Testing for Perpetuals:
- **High Leverage Testing**: System performance under maximum leverage
- **Volatility Testing**: Performance during extreme market volatility
- **Concurrent Position Testing**: Multiple position management efficiency
- **Real-time Monitoring**: Liquidation distance calculation performance
````
