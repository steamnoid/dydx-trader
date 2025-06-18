# dYdX v4 Technical Architecture - Simplified

## Project Structure
```
src/dydx_bot/
├── main.py                 # Entry point
├── config/                 # Configuration
├── connection/             # Layer 2: dydx-v4-client wrapper
├── data/                   # Layer 3: Market data processing
├── signals/                # Layer 4: Continuous signal scoring
├── strategies/             # Layer 5: Multi-market sniper strategies
├── risk/                   # Layer 6: Risk management
├── trading/                # Layer 7: Paper trading
└── dashboard/              # Layer 8: Terminal UI

tests/
├── unit/                   # Layer-specific unit tests
├── integration/            # Cross-layer integration
└── e2e/                    # Real dYdX testnet tests
```

## Layer Dependencies & Architectural Flow
- Each layer depends only on previous layers
- Layer 2 (connection) is foundation - ✅ COMPLETED (86.23% coverage)
- No circular dependencies
- Real dydx-v4-client in production, mocks only in tests

### Signal Architecture (Layer 4):
- **Multiple Continuous Signals per Market**: Each market provides multiple signal types (momentum, volume, volatility, orderbook) with scores (0-100)
- **No Discrete Signals**: Pure continuous scoring, no threshold-based triggers
- **Single-Market Focus**: Each signal engine handles one market independently, outputting multiple signal types
- **Single WebSocket Connection**: ALL signal engines share ONE WebSocket connection via ConnectionManager (CRITICAL: no multiple connections)
- **High-Frequency Updates**: All signal scores update with every market data tick
- **Rich Signal Interface**: Multiple 0-100 scores per market for Layer 5+ consumption (momentum: 85, volume: 72, volatility: 68, orderbook: 91)

### Strategy Architecture (Layer 5+):
- **Multi-Market Sniper Logic**: Compares multiple continuous signal types (momentum, volume, volatility, orderbook) across multiple markets
- **Cross-Market Decision Making**: Portfolio allocation using rich signal data from each market
- **Strategy Engine**: Orchestrates multiple signal types from multiple Layer 4 engines (all sharing ONE WebSocket connection)
- **Position Management**: Handles multi-position portfolio decisions with granular signal insights
- **Threshold Management**: Applies own thresholds to multiple signal types for discrete decisions
- **Signal Weighting**: Combines different signal types (momentum: 85, volume: 72) for market prioritization

## Key Patterns
- **Observer**: Market data notifications
- **Strategy**: Pluggable trading strategies with multi-market sniper logic
- **State Machine**: Connection management
- **Circuit Breaker**: dYdX connection resilience
- **Singleton**: Single WebSocket connection shared across ALL signal engines and markets
- **Continuous Scoring**: Real-time signal opportunity scoring (Layer 4)
- **Discrete Triggers**: Threshold-based signal generation (Layer 4)
- **Multi-Market Orchestration**: Cross-market decision engine (Layer 5+)

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
