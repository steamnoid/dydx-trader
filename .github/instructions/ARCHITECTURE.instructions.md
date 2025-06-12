# dYdX v4 Technical Architecture - Simplified

## Project Structure
```
src/dydx_bot/
├── main.py                 # Entry point
├── config/                 # Configuration
├── connection/             # Layer 2: dydx-v4-client wrapper
├── data/                   # Layer 3: Market data processing
├── signals/                # Layer 4: Signal generation
├── strategies/             # Layer 5: Trading strategies
├── risk/                   # Layer 6: Risk management
├── trading/                # Layer 7: Paper trading
└── dashboard/              # Layer 8: Terminal UI

tests/
├── unit/                   # Layer-specific unit tests
├── integration/            # Cross-layer integration
└── e2e/                    # Real dYdX testnet tests
```

## Layer Dependencies
- Each layer depends only on previous layers
- Layer 2 (connection) is foundation - ✅ COMPLETED (86.23% coverage)
- No circular dependencies
- Real dydx-v4-client in production, mocks only in tests

## Key Patterns
- **Observer**: Market data notifications
- **Strategy**: Pluggable trading strategies
- **State Machine**: Connection management
- **Circuit Breaker**: dYdX connection resilience

## dYdX v4 Integration Points
- **IndexerSocket**: Real-time perpetual data (WebSocket)
- **IndexerClient**: Account queries, historical data (REST)
- **NodeClient**: Order placement, blockchain operations
- **Wallet**: Authentication and signing

## Performance Requirements
- <512MB memory (fixed allocation preferred)
- <25% CPU utilization
- <25ms liquidation risk calculations
- >99.9% connection uptime
