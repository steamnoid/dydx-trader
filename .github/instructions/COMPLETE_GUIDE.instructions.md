# dYdX v4 Trading Bot - Complete Development Guide

## My Role & Responsibilities
**I AM THE PROJECT OWNER AND DEVELOPER. USER IS THE SUPERVISOR.**

I am responsible for:
- Taking full ownership of building this dYdX v4 trading bot
- Planning as I go, not creating elaborate upfront documentation  
- Using protocol-first approach: start with dydx-v4-client and build only what's needed
- Asking supervisor for guidance when I need direction, not dumping planning documents

## Per Layer Deliverables (What I Must Deliver)
Each layer must deliver:
1. **Working Code** - Protocol-first implementation using dydx-v4-client
2. **Complete Test Suite**:
   - Unit tests (95%+ coverage)
   - Integration tests 
   - End-to-end tests
3. **Autonomous Panel(s)** - Individual self-contained Rich panels showing REAL DATA and functionality
4. **Coverage Report** - Proof of test quality

## Panel Content Requirements
**MANDATORY**: Every autonomous panel must show BOTH metrics/statistics AND actual data samples:

### Quantitative Insights (Metrics & Statistics):
- Performance metrics: latency percentiles, throughput rates, error counts
- Market statistics: price ranges, volume analysis, volatility measurements
- Risk metrics: liquidation distances, margin utilization percentages
- Trading statistics: win rates, P&L distributions, position sizing stats

### Qualitative Insights (Actual Data Samples):
- Real market prices, spreads, orderbook bids/asks with actual values
- Live trade executions showing price/size/timestamp details
- Candlestick OHLCV data with actual price movements
- Signal calculations showing actual threshold values and trigger points
- Risk calculations displaying real liquidation prices and margin requirements
- Autonomous decision logs with actual reasoning and calculated values

### Integration Requirements:
- Show how raw data flows through processing layers with before/after examples
- Display autonomous decision-making process with real inputs → calculations → outputs
- Present live performance monitoring with actual latency measurements and data rates

## Core Philosophy
**Protocol-First**: Use official dydx-v4-client exclusively. Build abstractions only when protocol requires it.

## Tech Stack (MANDATORY)
- Python 3.11+ with **RxPY (reactivex)** for reactive programming (PRIMARY requirement Layer 2+)
- **dydx-v4-client package**: WebSocket: IndexerSocket | REST: IndexerClient | Blockchain: NodeClient
- Auth: Wallet + KeyPair classes | UI: **Rich library only** (terminal)
- Tests: pytest + **RxPY TestScheduler + Marble Testing** + **Rich Console.capture() for dashboard E2E testing**

## Layer Development (95% Coverage Required Each) - RxPY REACTIVE ARCHITECTURE
```
🔧 LAYER 2: RxPY Client Integration (Observable<MarketData> streams)
📊 LAYER 3: Reactive Data Processing (Observable<ProcessedData>)
⚡ LAYER 4: Streaming Signal Scoring (Observable<SignalScores>) 
🧠 LAYER 5: Reactive Multi-Market Strategies (Observable<StrategyDecisions>)
🛡️ LAYER 6: Risk Management (liquidation prevention)
📋 LAYER 7: Paper Trading (perpetual simulation)
🖥️ LAYER 8: Terminal Dashboard
🚀 LAYER 9: Main Application
```

## Production Code Rules
- NEVER import from tests/ directory
- NEVER use mocks in production code  
- ALWAYS use real dydx-v4-client classes
- Keep test mocks isolated in test files only

## dYdX v4 Focus Areas
- **Perpetual Futures**: Only product supported
- **Cross-Margin**: System used by dYdX v4
- **Funding Rates**: 8-hour cycles critical for profitability
- **Liquidation Prevention**: #1 priority in all development
- **Real-time Data**: WebSocket-first, REST secondary

## Reactive Signal vs Strategy Architecture (RxPY)
### Layer 4 (Signals): Observable<SignalScore> Streams
- **Single Signal Engine per Signal Type**: One momentum Observable, one volume Observable, etc. (not per-market)
- **Reactive Continuous Signals**: Observable<SignalScore> streams using RxPY operators (scan, map, combine_latest)
- **Multi-Market Processing**: Single engine instance processes all markets via shared Observable<MarketData> stream
- **NO Discrete Signals**: Layer 4 provides ONLY Observable<SignalScore> streams (0-100), no buy/sell/hold signals
- **RxPY Operators**: Uses window(), scan(), combine_latest() for real-time reactive signal calculations
- **Shared Observable**: ALL signal engines subscribe to same Observable<MarketData> stream (CRITICAL: single source)
- **High-Frequency Updates**: Signal score Observables emit with every market data tick using reactive operators
- **No Cross-Market Logic**: Focuses purely on single-market signal quality across multiple dimensions
- **Rich Streaming Interface**: Provides multiple Observable<SignalScore> streams per market to Layer 5+

### Layer 5+ (Strategies): Observable<StrategyDecision> Streams  
- **Multi-Market Reactive Logic**: Combines multiple Observable<SignalScore> streams across markets using combine_latest(), merge()
- **Cross-Market Decision Streams**: Observable<StrategyDecision> using reactive portfolio allocation operators
- **Reactive Strategy Engine**: Orchestrates multiple signal Observable streams using throttle(), debounce(), distinct_until_changed()
- **Strategic Decisions**: When/where/how much to deploy capital using reactive operators on multiple signal streams
- **Market Selection**: Chooses best opportunities using reactive operators on multiple Observable<SignalScore> streams
- **Signal Processing**: Uses combine_latest(), map(), filter() on multiple continuous signal Observable streams

## Performance Targets
- Memory: <512MB | CPU: <25% | Liquidation calc: <25ms | Coverage: 95%+

## Project Structure
```
src/dydx_bot/
├── connection/     # Layer 2: dydx-v4-client wrapper
├── data/          # Layer 3: Market data processing
├── signals/       # Layer 4: Continuous signal scoring only
├── strategies/    # Layer 5: Multi-market sniper strategies
├── risk/          # Layer 6: Risk management
├── trading/       # Layer 7: Paper trading
└── dashboard/     # Layer 8: Terminal UI
```

## Testing Strategy
- **Unit Tests**: 95%+ per layer, mock only dydx-v4-client network calls
- **Integration**: Multi-layer interaction testing
- **E2E**: Real dYdX testnet validation
- **Panel E2E**: Rich Console.capture() validation ensuring 100% operational guarantee
- **Rule**: No layer advancement until 95%+ coverage achieved
- **CRITICAL**: Never use async fixtures for panel objects - causes pytest hanging
- **Pattern**: Direct object creation + try/finally cleanup with shutdown() methods

## Development Workflow

### **CRITICAL: Choose Correct Approach Based on Component Type**

### **For Core Business Logic (RxPY Reactive Engines, Types, Algorithms)**:
**USE STRICT TDD + RxPY TESTING - NO EXCEPTIONS:**
1. **WRITE ONE TEST FUNCTION ONLY** - Single failing test case using RxPY TestScheduler
2. **RUN TEST** - Verify it FAILS (RED phase) 
3. **WRITE MINIMAL PRODUCTION CODE** - Only enough RxPY Observable/operators to pass the one test
4. **RUN TEST** - Verify it PASSES (GREEN phase)
5. **MINIMAL REFACTOR ONLY** - Clean only what's necessary in RxPY streams
6. **RUN TEST** - Verify it still PASSES after refactor
7. **REPEAT** - Write next single test, run test, minimal code, run test, minimal refactor, run test

**RxPY TESTING REQUIREMENTS:**
- **Use TestScheduler for time-based Observable testing**
- **Marble testing for Observable stream validation**
- **Mock Observable sources for predictable stream behavior**
- **Test reactive operators: map(), scan(), combine_latest(), etc.**

**Components**: ReactiveSignalEngine, StreamingRiskCalculator, ObservableStrategyEngine, etc.

### **For Rich UI Panels (Display Components)**:
**USE PANEL-FIRST DEVELOPMENT:**
1. **Panel First**: Build working autonomous panel with real data
2. **Inspect Output**: Run panel, capture actual Rich console patterns
3. **Write E2E Tests**: Create tests based on actual output patterns
4. **Validate**: Ensure tests provide 100% operational guarantee
5. **Refactor**: Improve panel based on test insights

**Components**: MarketDataPanel, SignalPanel, RiskPanel, TradingPanel, etc.

### **MANDATORY Layer Development Order**:
```
Each Layer MUST Follow This STRICT TDD Sequence:
1. **Write ONE Test Function** → Run test (RED)
2. **Write Minimal Production Code** → Run test (GREEN)
3. **Minimal Refactor Only** → Run test (still GREEN)
4. **Repeat** → Write next ONE test function → Run test (RED) → minimal code → Run test (GREEN) → refactor → Run test (GREEN)
5. **Coverage Verification** → Only after all functions implemented via TDD
6. **Integration Tests** → Cross-layer functionality only after unit tests complete
7. **Rich Panel** (Panel-First) → E2E Tests only after core logic complete
```

### **STRICT TDD ENFORCEMENT**:
- **ONE TEST AT A TIME** - Never write multiple test functions together
- **RUN TEST IMMEDIATELY** - After writing test, after writing code, after refactoring
- **MINIMAL CODE ONLY** - Write only enough code to pass the current test
- **NO ANTICIPATION** - Don't write code for future tests
- **NO FILE CHAOS** - Focus on one file at a time
- **RED→GREEN→REFACTOR** - Must follow cycle with test runs for every single function

### **Rationale for Different Approaches**:

**Core Logic TDD**:
- **Predictable Behavior**: Business logic has defined inputs/outputs
- **Performance Critical**: Must meet <25ms latency requirements
- **Testable Algorithms**: Signal generation, risk calculations, strategy logic
- **Protocol-First**: Direct integration with dydx-v4-client

**Panel-First Development**:
- **Rich Console Output is Unpredictable**: ANSI codes, formatting, exact field names
- **Visual Feedback Essential**: Need to see actual data flow and panel layouts
- **Accurate Test Patterns**: Tests match reality, not assumptions
- **Faster Development**: No guessing about Rich rendering behavior
- **Better E2E Tests**: Based on real output, not imagined patterns

### **Example Layer 4 Implementation Order**:
1. **SignalEngine + SignalTypes** (TDD) → Unit tests for signal algorithms
2. **Integration Tests** → SignalEngine + MarketDataProcessor
3. **SignalPanel** (Panel-First) → Rich display + E2E tests
4. **Coverage Report** → 95%+ layer completion proof
