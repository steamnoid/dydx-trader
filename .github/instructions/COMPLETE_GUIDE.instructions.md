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
3. **Dashboard** - Visual presentation of results and functionality
4. **Coverage Report** - Proof of test quality

## Core Philosophy
**Protocol-First**: Use official dydx-v4-client exclusively. Build abstractions only when protocol requires it.

## Tech Stack (MANDATORY)
- Python 3.11+ with dydx-v4-client package
- WebSocket: IndexerSocket | REST: IndexerClient | Blockchain: NodeClient
- Auth: Wallet + KeyPair classes | UI: rich library | Tests: pytest

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
- **Rule**: No layer advancement until 95%+ coverage achieved

## Development Workflow
1. **Red**: Write failing test (including edge cases)
2. **Green**: Minimal code to pass test
3. **Refactor**: Clean, optimize code
4. **Coverage**: Verify 95%+ coverage
5. **Advance**: Move to next layer only after completion
