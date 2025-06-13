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
3. **Dashboard** - Visual presentation of REAL DATA and autonomous functionality
4. **Coverage Report** - Proof of test quality

## Dashboard Requirements for Autonomous Sniper
**CRITICAL**: Dashboards must demonstrate autonomous operation with COMPREHENSIVE DATA:

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

## Tech Stack (MANDATORY)
- **Language**: Python 3.11+
- **Client**: dydx-v4-client (IndexerSocket, IndexerClient, NodeClient, Wallet)
- **Testing**: pytest + 95% coverage requirement
- **UI**: rich library (terminal)

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
