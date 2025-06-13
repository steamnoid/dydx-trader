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
3. **Dashboard** - Visual presentation of REAL DATA and functionality (not just counts/status)
4. **Coverage Report** - Proof of test quality

## Dashboard Content Requirements
**MANDATORY**: Every dashboard must show BOTH metrics/statistics AND actual data samples:

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
- Python 3.11+ with dydx-v4-client package
- WebSocket: IndexerSocket | REST: IndexerClient | Blockchain: NodeClient
- Auth: Wallet + KeyPair classes | UI: **Rich library only** (terminal)
- Tests: pytest + **Rich Console.capture() for dashboard E2E testing**

## Layer Development (95% Coverage Required Each)
```
🔧 LAYER 2: Client Integration (START HERE)
📊 LAYER 3: Data Processing  
⚡ LAYER 4: Signal Generation
🧠 LAYER 5: Trading Strategies
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

## Performance Targets
- Memory: <512MB | CPU: <25% | Liquidation calc: <25ms | Coverage: 95%+

## Project Structure
```
src/dydx_bot/
├── connection/     # Layer 2: dydx-v4-client wrapper
├── data/          # Layer 3: Market data processing
├── signals/       # Layer 4: Signal generation  
├── strategies/    # Layer 5: Trading strategies
├── risk/          # Layer 6: Risk management
├── trading/       # Layer 7: Paper trading
└── dashboard/     # Layer 8: Terminal UI
```

## Testing Strategy
- **Unit Tests**: 95%+ per layer, mock only dydx-v4-client network calls
- **Integration**: Multi-layer interaction testing
- **E2E**: Real dYdX testnet validation
- **Dashboard E2E**: Rich Console.capture() validation ensuring 100% operational guarantee
- **Rule**: No layer advancement until 95%+ coverage achieved
- **CRITICAL**: Never use async fixtures for dashboard objects - causes pytest hanging
- **Pattern**: Direct object creation + try/finally cleanup with shutdown() methods

## Development Workflow

### **For Core Logic (Unit/Integration Tests)**:
1. **Red**: Write failing test (including edge cases)
2. **Green**: Minimal code to pass test
3. **Refactor**: Clean, optimize code
4. **Coverage**: Verify 95%+ coverage

### **For Dashboards (Rich UI Components)**:
1. **Dashboard First**: Build working dashboard with real data
2. **Inspect Output**: Run dashboard, capture actual Rich console patterns
3. **Write E2E Tests**: Create tests based on actual output patterns
4. **Validate**: Ensure tests provide 100% operational guarantee
5. **Refactor**: Improve dashboard based on test insights

### **Rationale for Dashboard-First Approach**:
- **Rich Console Output is Unpredictable**: ANSI codes, formatting, exact field names
- **Visual Feedback Essential**: Need to see actual data flow and panel layouts
- **Accurate Test Patterns**: Tests match reality, not assumptions
- **Faster Development**: No guessing about Rich rendering behavior
- **Better E2E Tests**: Based on real output, not imagined patterns

5. **Advance**: Move to next layer only after completion
