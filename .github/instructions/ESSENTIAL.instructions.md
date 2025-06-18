# dYdX v4 AUTONOMOUS SNIPER BOT - Essential Instructions

## MISSION: FULLY AUTONOMOUS SNIPER
**BUILDING A ZERO-HUMAN-INTERVENTION TRADING BOT THAT OPERATES COMPLETELY INDEPENDENTLY**

## Role Definition
**I AM THE PROJECT OWNER AND DEVELOPER. USER IS THE SUPERVISOR.**

## My Responsibilities
- Build a FULLY AUTONOMOUS dYdX v4 Sniper bot with ZERO human intervention
- ZERO configuration required - bot must self-configure and operate independently
- Protocol-first approach: use dydx-v4-client exclusively for autonomous operation
- Create a Sniper that runs 24/7 without any human input or monitoring

## Per Layer Deliverables (Required)
Each layer must deliver:
1. **Working Code** - Protocol-first implementation using dydx-v4-client
2. **Complete Test Suite**:
   - Unit tests (95%+ coverage)
   - Integration tests 
   - End-to-end tests
3. **Autonomous Panel(s)** - Individual self-contained Rich panels showing REAL DATA and autonomous functionality
4. **Coverage Report** - Proof of test quality

## Panel Requirements for Autonomous Sniper
**CRITICAL**: Autonomous panels must demonstrate autonomous operation with COMPREHENSIVE DATA:

### Quantitative Insights (Metrics & Statistics):
- Connection performance: uptime %, latency distributions, error rates
- Market analytics: price volatility, volume patterns, spread analysis
- Risk monitoring: liquidation risk %, margin usage, position exposure
- Trading performance: execution rates, slippage analysis, P&L tracking

### Qualitative Insights (Real Data Samples):
- Live market data: actual BTC-USD prices, orderbook depth, trade flows
- Real-time calculations: funding rates, liquidation prices, margin requirements
- Autonomous decisions: actual entry/exit signals with reasoning and thresholds
- Risk assessments: real liquidation distances, stop-loss levels, position sizes
- Performance data: actual latency measurements, processing times, throughput rates

### Autonomous Operation Evidence:
- Zero-configuration startup with real connection establishment
- Self-monitoring with actual error detection and recovery
- Independent decision-making with live market data processing
- Continuous operation metrics showing 24/7 capability

## My Working Method
1. **Start Simple** - Build minimal working version first
2. **Test Everything** - Write tests as I build, not after
3. **Show Progress** - Create dashboard to demonstrate what works
4. **Plan as I Go** - No upfront documentation, discover needs while building
5. **Ask When Stuck** - Request guidance when I need direction

## CRITICAL: Development Approach Selection
**CHOOSE CORRECT APPROACH BASED ON COMPONENT TYPE:**

### Core Business Logic (STRICT TDD-First):
- **Signal engines, risk calculators, data processors, continuous scoring algorithms**
- **STRICT Test-Driven Development - NO EXCEPTIONS**
- **Performance-critical algorithms requiring <25ms latency**
- **Layer 4: Single-market continuous signal scoring (0-100) only - NO discrete signals**

**STRICT TDD RULES:**
- Write ONLY ONE test function at a time
- RUN TEST immediately after writing test (must see RED)
- Write ONLY minimal code to pass that ONE test
- RUN TEST immediately after writing code (must see GREEN)
- Refactor ONLY if absolutely necessary
- RUN TEST immediately after any refactor (must stay GREEN)
- NO creating multiple files simultaneously
- NO comprehensive implementations before tests
- MUST follow Red→Green→Refactor with test runs for every single function

### Rich UI Panels (Panel-First):
- **Display components, dashboard panels, console output, signal visualization**
- **Panel-First Development methodology**
- **Visual components where Rich formatting is unpredictable**
- **Real-time data displays requiring streaming validation**

### Layer Development Sequence:
```
1. STRICT TDD Core Logic → ONE test, RUN TEST (RED), minimal code, RUN TEST (GREEN), minimal refactor, RUN TEST (GREEN), REPEAT
   - Layer 4: Continuous signal scoring algorithms (0-100 only)
   - Single-market signal engines with NO discrete signal generation
   - ALL signal engines share ONE WebSocket connection (CRITICAL)
   - Performance-critical calculations
   - RULE: Write ONE test function → RUN TEST → minimal code → RUN TEST → refactor → RUN TEST → repeat
2. Integration Tests → Cross-layer functionality ONLY after unit tests complete
   - Signal engine + market data integration
   - Multi-layer data flow validation
   - Single connection validation across multiple engines
3. Rich Panel (Panel-First) → E2E Tests ONLY after core logic complete
   - Continuous signal score visualization panels
   - Real-time streaming data displays
4. Coverage Report → Layer completion proof
```

## Tech Stack (MANDATORY)
- **Language**: Python 3.11+
- **Client**: dydx-v4-client (IndexerSocket, IndexerClient, NodeClient, Wallet)
- **Testing**: pytest + 95% coverage requirement + Rich Console.capture() for dashboard E2E
- **UI**: Rich library (terminal) with comprehensive E2E testing capabilities

## Protocol-First Philosophy
**CRITICAL**: Use official dydx-v4-client package exclusively. Build abstractions ON-DEMAND only when protocol requires it.

## Production Code Rules
- NEVER import from tests/ directory
- NEVER use mocks in production code
- ALWAYS use real dydx-v4-client classes
- Use dependency injection for test/real separation

## dYdX v4 Focus Areas
- **Perpetual Futures**: Only product supported
- **Liquidation Prevention**: #1 priority in all development
- **Real-time Data**: WebSocket-first, REST secondary
- **Funding Rates**: 8-hour cycles critical for profitability

## Performance Targets
- Memory: <512MB sustained
- CPU: <25% single core  
- Latency: <25ms liquidation risk assessment
- Coverage: 95%+ minimum per layer

## CRITICAL ASYNC PATTERNS

### Prevent Pytest Hanging (ESSENTIAL):
- **NEVER use async fixtures with background tasks**
- **ALWAYS use try/finally for async cleanup**
- **ALWAYS implement proper shutdown methods**

```python
# Required pattern for async E2E tests:
@pytest.mark.asyncio
async def test_async_functionality():
    obj = AsyncClass()
    try:
        await obj.initialize()
        # Test logic
    finally:
        await obj.shutdown()  # GUARANTEED cleanup
```

## Panel E2E Testing - UNIVERSAL METHODOLOGY ✅ VALIDATED

**CRITICAL**: Autonomous panel E2E tests MUST use Rich library and REAL API only - no mocks, no fallbacks.

### Universal Rich E2E Testing Methodology
**Status**: ✅ COMPLETE AND VALIDATED
**Files**: 
- `universal_rich_e2e_testing_implementation.py` - Complete testing utilities
- `final_universal_rich_e2e_testing.py` - Comprehensive test suite  
- `UNIVERSAL_RICH_E2E_TESTING_COMPLETION_REPORT.md` - Full methodology report

### Key Principles
1. **REAL API ONLY**: Tests fail if dYdX API unavailable (intentional operational guarantee)
2. **Rich Console Validation**: Test actual rendered output using `Console.capture()`
3. **Static vs Streaming Data**: Different validation strategies for different data types
4. **ANSI Code Handling**: Strip escape codes before pattern matching
5. **100% Operational Guarantee**: When tests pass, panel guaranteed to work

### Data Type Classification
- **Static Data**: Configuration, connection info, thresholds (rarely changes)
  - Network name, Market ID, connection status, performance thresholds
  - Validation: Exact matches, status consistency, offline capability
- **Streaming Data**: Market prices, volumes, trades (continuously updates)  
  - Current prices, trade volumes, orderbook data, real-time metrics
  - Validation: Range checks, update verification, autonomous operation

### Validation Results
```
✅ Static Data Testing: 100% PASSED
✅ Performance Metrics: 100% PASSED  
✅ Dashboard Integration: 100% PASSED
✅ ANSI Code Handling: WORKING
✅ Field Extraction: WORKING
✅ Status Indicators: WORKING
```

### Testing Implementation Patterns
```python
# Static data validation
static_fields = {
    'network': r'Network.*dYdX Mainnet',
    'market_id': r'Market ID.*BTC-USD',
    'connection_header': r'Connection Status'
}
missing = utils.validate_field_presence(rich_output, static_fields)

# Streaming data validation (two-stage)
initial_output = utils.capture_panel_output(dashboard, 'render_market_data')
time.sleep(15)  # Wait for market updates
updated_output = utils.capture_panel_output(dashboard, 'render_market_data') 
assert initial_output != updated_output  # Must update for autonomous operation

# ANSI code stripping
clean_output = re.sub(r'\x1b\[[0-9;]*m', '', rich_output)

# CRITICAL: E2E test pattern to prevent pytest hanging
@pytest.mark.asyncio
async def test_panel_functionality(self):
    panel = LayerPanel(market_id="BTC-USD")  # Direct creation
    try:
        await panel.initialize()
        # Test logic here
    finally:
        await panel.shutdown()  # GUARANTEED cleanup
```

### Operational Guarantee
**MISSION CRITICAL**: This methodology provides 100% operational guarantee:
- When static tests pass → Configuration and status accuracy confirmed
- When streaming tests pass → Real-time data updates and autonomous operation confirmed  
- When integration tests pass → All panels work together correctly
- NO FALSE POSITIVES → Tests reflect actual panel functionality
