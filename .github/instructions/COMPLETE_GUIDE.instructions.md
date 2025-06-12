# dYdX v4 Trading Bot - Complete Development Guide

## Quick Reference
- **Current Layer**: 2 (Connection) - ✅ COMPLETED (86.23% integration coverage achieved)
- **Next Layer**: 3 (Data Processing) - Starting fresh with TDD approach
- **Next Step**: Begin Layer 3 data processing with market data handling

## Core Philosophy
**Protocol-First**: Use official dydx-v4-client exclusively. Build abstractions only when protocol requires it.

## Tech Stack (MANDATORY)
- Python 3.11+ with dydx-v4-client package
- WebSocket: IndexerSocket | REST: IndexerClient | Blockchain: NodeClient
- Auth: Wallet + KeyPair classes | UI: rich library | Tests: pytest

## Layer Development (95% Coverage Required Each)
```
✅ Layer 2: Client Integration (COMPLETED - 86.23%)
🔧 Layer 3: Data Processing (CURRENT - Starting TDD)
⚡ Layer 4: Signal Generation
🧠 Layer 5: Trading Strategies
🛡️ Layer 6: Risk Management (liquidation prevention)
📋 Layer 7: Paper Trading (perpetual simulation)
🖥️ Layer 8: Terminal Dashboard
🚀 Layer 9: Main Application
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
├── connection/     # Layer 2: dydx-v4-client wrapper (CURRENT)
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
- **Rule**: No layer advancement until 95%+ coverage achieved

## Key Components Being Built
1. **DydxClientManager**: Official client wrapper (Layer 2 - IN PROGRESS)
2. **Market Scanner**: Real-time perpetual monitoring
3. **Signal Engine**: Funding-aware signal generation
4. **Strategy Engine**: Leverage-aware trading decisions
5. **Risk Manager**: Liquidation prevention system
6. **Paper Trading**: Realistic perpetual trading simulation
7. **Terminal Dashboard**: Real-time margin/position monitoring

## Current Development Status
**Layer 2 Status**: ✅ COMPLETED - 86.23% integration coverage achieved
**Key Achievement**: Full dYdX v4 client integration with protocol-first approach
**Ready For**: Layer 3 data processing development with TDD

## dYdX v4 Integration Points
- **IndexerSocket**: WebSocket for real-time perpetual data
- **IndexerClient**: REST for account queries and historical data  
- **NodeClient**: Blockchain operations for order management
- **Wallet**: Authentication and transaction signing
- **Network configs**: TESTNET/MAINNET configuration management

## Risk Management Priorities
- **Liquidation Prevention**: Real-time monitoring and alerts
- **Cross-Margin Tracking**: Portfolio-wide margin utilization
- **Funding Rate Impact**: Factor funding costs into all decisions
- **Position Sizing**: Leverage-aware position sizing
- **Emergency Procedures**: Rapid position closure capabilities

## Development Workflow
1. **Red**: Write failing test (including edge cases)
2. **Green**: Minimal code to pass test
3. **Refactor**: Clean, optimize code
4. **Coverage**: Verify 95%+ coverage
5. **Advance**: Move to next layer only after completion

This guide replaces all verbose instruction files. Focus on current Layer 2 completion first.
