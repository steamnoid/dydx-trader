# dYdX v4 Technical Architecture Instructions

## Protocol-First Development Philosophy
**CRITICAL CHANGE**: We now follow a "protocol-first, domain-model-on-demand" approach instead of comprehensive domain modeling upfront. Build only what the dYdX v4 protocol requires, when it's required.

### Protocol-First Methodology:
1. **Start with dYdX v4 API**: Begin with actual protocol calls and responses
2. **Build Models On-Demand**: Create domain models only when protocol data needs structure
3. **Avoid Over-Engineering**: Don't build comprehensive models that force-fit protocol data
4. **Protocol Truth**: dYdX v4 API is the single source of truth for data structures
5. **Minimal Abstractions**: Only abstract when multiple protocol calls share patterns

## Stack Technologiczny (OBOWIĄZKOWY)
- **Język**: Python 3.11+
- **Główna biblioteka**: dydx-v4-client (oficjalna biblioteka dYdX v4 - MANDATORY)
- **WebSocket**: dydx-v4-client.indexer.socket.websocket.IndexerSocket (MANDATORY)
- **REST API**: dydx-v4-client.indexer.rest.indexer_client.IndexerClient (MANDATORY)
- **Blockchain**: dydx-v4-client.node.client.NodeClient (MANDATORY)
- **Authentication**: dydx-v4-client.wallet.Wallet + KeyPair (MANDATORY)
- **Network Config**: dydx-v4-client.network.TESTNET/MAINNET (MANDATORY)
- **Async Framework**: asyncio (native Python)
- **Terminal UI**: rich library
- **Testing**: pytest + pytest-asyncio + pytest-mock
- **Type Checking**: mypy z strict mode
- **Code Quality**: black, isort, flake8, pre-commit hooks
- **Profiling**: memory_profiler, cProfile dla optymalizacji

## dYdX Testnet Credentials
```json
{
  "mnemonic": "clerk oak wife parrot verb science hockey tomato father situate resource trade kangaroo protect social boil survey pulp mask soon wedding choice guilt rookie",
  "address": "dydx1yg9wumc4hy85vd3833zd46t5rpqlkvngxud6hr",
  "network": "testnet",
  "description": "dYdX testnet configuration for autonomous trading bot testing"
}
```

## Wzorce Architektoniczne (WYMAGANE)
- **Layered Architecture**: 9-layer stack z clear separation
- **Observer Pattern**: Market data notifications
- **Strategy Pattern**: Pluggable perpetual trading strategies  
- **State Machine**: Connection and trading state management
- **Circuit Breaker**: Resilience dla WebSocket connections
- **Producer-Consumer**: Async data processing pipelines
- **Singleton Pattern**: Application configuration and state

## Struktura Projektu dYdX v4
```
dydx-sniper-bot/
├── .github/
│   └── dydx_instructions/         # Instrukcje projektu dYdX v4
├── docs/                          # Dokumentacja
├── src/
│   └── dydx_bot/
│       ├── __init__.py
│       ├── main.py               # Entry point
│       ├── config/               # Konfiguracja dYdX v4
│       ├── models/               # Layer 1: Data models (perpetual-focused)
│       ├── connection/           # Layer 2: dYdX v4 Official Client management
│   ├── dydx_client.py   # Wrapper around official dydx-v4-client
│   ├── indexer_socket.py # IndexerSocket WebSocket management
│   ├── indexer_client.py # IndexerClient REST management
│   ├── node_client.py   # NodeClient blockchain operations
│   └── wallet_manager.py # Wallet & KeyPair authentication
│       ├── data/                 # Layer 3: Perpetual market data processing & aggregation
│   ├── aggregators/     # Stream data aggregation (orderbook, OHLCV, trades)
│   ├── processors/      # Real-time data processing
│   ├── validators/      # Data quality validation
│   └── buffers/         # Circular buffers for aggregated data
│       ├── signals/              # Layer 4: Perpetual signal generation
│       ├── strategies/           # Layer 5: Perpetual trading strategies
│       ├── risk/                 # Layer 6: Cross-margin risk management
│       ├── trading/              # Layer 7: Perpetual paper trading engine
│       ├── dashboard/            # Layer 8: Terminal UI
│       └── utils/                # Utilities i helpers
├── tests/                        # Comprehensive test suite
│   ├── unit/                    # Unit tests per layer
│   ├── integration/             # Cross-layer integration tests
│   ├── e2e/                     # End-to-end real dYdX testing
│   └── performance/             # Performance benchmarks
├── benchmarks/                   # Performance testing
├── requirements/                 # Dependencies
└── README.md
```

## Memory Architecture (KRYTYCZNE dla dYdX v4)
- **Circular Buffers**: OHLCV data z fixed size dla perpetuals
- **Ring Buffers**: Orderbook snapshots dla all markets
- **Memory Pools**: Object reuse dla high-frequency perpetual data
- **Lazy Loading**: On-demand data retrieval
- **Weak References**: Avoid memory leaks
- **Garbage Collection Tuning**: Optimized GC settings
- **Funding Rate Cache**: Efficient funding rate storage

## Performance Architecture (dydx-v4-client Optimized)
- **Async/Await**: All I/O operations non-blocking via official client
- **Vectorized Operations**: NumPy dla calculations
- **Compiled Extensions**: Numba dla critical paths
- **Official Client Pooling**: Efficient IndexerSocket connection management
- **Batch Processing**: Grouped operations via IndexerClient where possible
- **Zero-Copy Operations**: Minimize data copying from official client
- **dYdX Official Optimizations**: Leverage built-in client optimizations

## Data Flow Architecture (Official dYdX v4 Client)
```
dYdX v4 IndexerSocket → Stream Aggregator → Perpetual Data Processor → Signal Engine → Perpetual Strategy Engine → Cross-Margin Risk Manager → Paper Trading → Dashboard
     ↕                       ↕                       ↕
dYdX v4 IndexerClient → Account Manager ← NodeClient (Orders)

Stream Aggregation Layer:
├── Orderbook Frame Builder (delta → full snapshot)
├── OHLCV Candle Aggregator (ticks → candles)  
├── Trade Volume Aggregator (individual → volume analysis)
└── Funding Rate Compiler (multi-message → complete rates)
```

## Configuration Management dYdX v4
- **Environment Variables**: API keys and sensitive configuration
- **YAML Files**: Strategy parameters i perpetual settings
- **Runtime Configuration**: Dynamic parameter adjustment
- **Validation**: Pydantic models dla all config
- **Hot Reload**: Configuration updates without restart
- **API Key Management**: Secure credential handling

## Error Handling Architecture
- **Graceful Degradation**: Partial functionality w przypadku błędów
- **Automatic Recovery**: Self-healing mechanisms
- **Circuit Breakers**: Prevent cascade failures
- **Retry Logic**: Exponential backoff dla reconnections
- **Error Classification**: Different handling dla different error types
- **dYdX v4 Client Error Handling**: Official client's built-in error responses and recovery

## State Management
- **Application State**: Global state management
- **Connection State**: WebSocket connection status
- **Trading State**: Current perpetual positions i orders
- **Market State**: Current market conditions and funding rates
- **Margin State**: Real-time margin and liquidation risk

## dYdX v4 Specific Architecture Components

### Authentication Layer:
- **API Key Management**: Secure storage and rotation
- **Request Signing**: Automatic signature generation
- **Session Management**: Maintain authenticated sessions
- **Rate Limiting**: Respect API rate limits
- **Permission Validation**: Ensure proper access rights

### Perpetual Trading Layer:
- **Funding Rate Integration**: Real-time funding calculations
- **Cross-Margin Management**: Multi-position margin tracking
- **Leverage Optimization**: Dynamic leverage adjustment
- **Position Sizing**: Perpetual-specific sizing algorithms
- **Liquidation Monitoring**: Real-time liquidation risk

### Market Data Layer:
- **Perpetual Stream Processing**: High-frequency data handling
- **Funding Rate Streams**: Real-time funding updates
- **Market Maker Detection**: Institutional liquidity recognition
- **Arbitrage Detection**: Cross-market opportunity identification
- **Price Discovery**: Perpetual price formation analysis

## Security Architecture

### API Security:
- **Credential Management**: Secure API key handling
- **Request Signing**: All requests properly signed
- **SSL/TLS**: Encrypted connections only
- **Access Control**: Minimal required permissions
- **Audit Logging**: All API interactions logged

### Application Security:
- **Input Validation**: All external data validated
- **Error Handling**: No sensitive data in error messages
- **Logging Security**: No credentials in logs
- **Memory Security**: Secure memory handling
- **Configuration Security**: Encrypted sensitive config

## Performance Targets dYdX v4

### Latency Requirements:
- **WebSocket Processing**: <10ms per message
- **Signal Generation**: <30ms from data to signal
- **Order Decision**: <50ms strategy decision
- **Funding Calculation**: <5ms funding impact
- **Margin Update**: <10ms cross-margin calculation

### Resource Requirements:
- **Memory Usage**: <512MB sustained operation
- **CPU Usage**: <25% single core utilization
- **Network**: <1MB/s sustained bandwidth
- **Storage**: Memory-only operation
- **Connections**: <10 concurrent WebSocket connections

## Monitoring and Observability

### Application Metrics:
- **Performance Metrics**: Latency, throughput, resource usage
- **Trading Metrics**: P&L, positions, funding costs
- **Connection Metrics**: Uptime, reconnections, errors
- **Data Quality Metrics**: Message rates, data completeness
- **Risk Metrics**: Margin usage, liquidation distance

### Health Checks:
- **Connection Health**: WebSocket connection status
- **Data Health**: Data freshness and quality
- **Trading Health**: Position and margin status
- **System Health**: Resource usage and performance
- **API Health**: Rate limiting and authentication status

## Deployment Architecture

### Standalone Application:
- **Single Binary**: Self-contained executable
- **Configuration**: External config files
- **Logging**: Structured logging to files
- **Monitoring**: Built-in metrics collection
- **Management**: CLI interface dla control

### Environment Management:
- **Development**: Local development environment
- **Testing**: Automated testing environment
- **Staging**: Pre-production testing
- **Production**: Live trading environment
- **Disaster Recovery**: Backup and recovery procedures
