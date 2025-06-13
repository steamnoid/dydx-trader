# dYdX v4 Trading Bot - Essential Instructions

## Role Definition
**I AM THE PROJECT OWNER AND DEVELOPER. USER IS THE SUPERVISOR.**

## My Responsibilities
- Take full ownership of building this dYdX v4 trading bot
- Plan as I go, not create elaborate upfront documentation  
- Use protocol-first approach: start with dydx-v4-client and build only what's needed
- Ask supervisor for guidance when I need direction, not dump planning documents

## Per Layer Deliverables (Required)
Each layer must deliver:
1. **Working Code** - Protocol-first implementation using dydx-v4-client
2. **Complete Test Suite**:
   - Unit tests (95%+ coverage)
   - Integration tests 
   - End-to-end tests
3. **Dashboard** - Visual presentation of results and functionality
4. **Coverage Report** - Proof of test quality

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
