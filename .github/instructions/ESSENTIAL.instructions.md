# dYdX v4 Trading Bot - Essential Instructions

## Protocol-First Philosophy
**CRITICAL**: Use official dydx-v4-client package exclusively. Build abstractions ON-DEMAND only when protocol requires it.

## Stack (MANDATORY)
- **Language**: Python 3.11+
- **Client**: dydx-v4-client (IndexerSocket, IndexerClient, NodeClient, Wallet)
- **Testing**: pytest + 95% coverage requirement
- **UI**: rich library (terminal)

## TDD Workflow (STRICT)
```
🔧 LAYER 2: Official Client Integration → 95%+ coverage
📊 LAYER 3: Data Processing → 95%+ coverage  
⚡ LAYER 4: Signals → 95%+ coverage
🧠 LAYER 5: Strategies → 95%+ coverage
🛡️ LAYER 6: Risk Management → 95%+ coverage
📋 LAYER 7: Paper Trading → 95%+ coverage
🖥️ LAYER 8: Terminal Dashboard → 95%+ coverage
🚀 LAYER 9: Main Application → 95%+ coverage
```

**NEVER advance to next layer until current layer has 95%+ coverage.**

## Production Code Rules
- NEVER import from tests/ directory
- NEVER use mocks in production code
- ALWAYS use real dydx-v4-client classes
- Use dependency injection for test/real separation

## dYdX v4 Specifics
- **Focus**: Perpetual futures only
- **Margin**: Cross-margin system
- **Funding**: 8-hour cycles critical
- **Risk**: Liquidation prevention priority #1
- **Data**: WebSocket-first (IndexerSocket), REST secondary

## Performance Targets
- Memory: <512MB sustained
- CPU: <25% single core
- Latency: <25ms liquidation risk assessment
- Coverage: 95%+ minimum

## Key Components
1. **DydxClientManager**: Official client wrapper
2. **Market Scanner**: Perpetual market monitoring
3. **Signal Engine**: Funding-aware signals
4. **Strategy Engine**: Leverage-aware decisions
5. **Risk Manager**: Liquidation prevention
6. **Paper Trading**: Realistic perpetual simulation
7. **Terminal Dashboard**: Real-time margin monitoring

## Current Status
- **Layer 2**: ✅ COMPLETED (86.23% coverage)
- **Achievement**: Full dYdX v4 client integration with protocol-first approach
- **Ready For**: Layer 3 data processing development with TDD

## Next Steps
1. Begin Layer 3 data processing development
2. Implement market data handling with TDD
3. Target 95% coverage for Layer 3 completion
