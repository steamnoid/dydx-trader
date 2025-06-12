# dYdX v4 Data Sources Integration Instructions

## Protocol-First Development Philosophy
**Critical**: Follow dYdX v4 client nomenclature and patterns directly. Build domain models ON-DEMAND when they provide clear value, not comprehensively upfront.

## Źródła Danych dYdX v4 Protocol

### Jedyne Źródło Danych: dYdX v4 Perpetual DEX
**Philosophy**: Zero external dependencies - all data from dYdX v4 ecosystem via WebSocket-first architecture using official dydx-v4-client patterns

### Główne Strumienie Danych (WebSocket Priority)

#### 1. **Perpetual Market Data Streams (Priorytet #1)**
- **Endpoint**: dYdX v4 WebSocket Market Data
- **Data**: Real-time OHLCV dla wszystkich perpetual markets
- **Format**: JSON messages via WebSocket (tick data requiring aggregation)
- **Frequency**: Real-time tick data
- **Aggregation Required**: Build OHLCV candles from individual tick updates
- **Critical dla**: Signal generation, strategy decisions
- **dYdX Specific**: Funding rate integration with price data

#### 2. **Orderbook Streams (Priorytet #1)**
- **Endpoint**: dYdX v4 WebSocket Orderbook
- **Data**: Real-time order book depth, spreads dla perpetuals
- **Format**: JSON orderbook snapshots and incremental updates
- **Frequency**: Real-time updates (sub-second)
- **Aggregation Required**: Combine incremental updates to maintain full orderbook state
- **Critical dla**: Liquidity analysis, entry/exit timing
- **dYdX Specific**: Professional market maker liquidity patterns

#### 3. **Trade Streams (Priorytet #2)**
- **Endpoint**: dYdX v4 WebSocket Trades
- **Data**: Executed trades, volume, price impact
- **Format**: Individual trade execution messages
- **Frequency**: Real-time trade notifications
- **Aggregation Required**: Aggregate trades for volume analysis and market impact assessment
- **Critical dla**: Market momentum, volume analysis
- **dYdX Specific**: Institutional trade pattern recognition

#### 4. **Funding Rate Streams (Priorytet #1 - dYdX Specific)**
- **Endpoint**: dYdX v4 WebSocket Funding Rates
- **Data**: Real-time funding rates dla all perpetuals
- **Format**: Funding rate updates and historical data messages
- **Frequency**: Every 8 hours with real-time rate changes
- **Aggregation Required**: Compile funding data across multiple messages for complete rate history
- **Critical dla**: Funding arbitrage, position timing
- **Unique Feature**: Key competitive advantage dla perpetual trading

#### 5. **Account Streams (Paper Trading)**
- **Endpoint**: dYdX v4 WebSocket Account Updates
- **Data**: Positions, balances, margin, orders (simulated)
- **Format**: Account state messages
- **Frequency**: Real-time account updates
- **Critical dla**: Paper trading simulation, P&L tracking
- **dYdX Specific**: Cross-margin system simulation

#### 6. **Market Metadata**
- **Endpoint**: dYdX v4 REST API Market Config
- **Data**: Tick sizes, lot sizes, margin requirements, funding caps
- **Format**: Market configuration JSON
- **Frequency**: On market changes
- **Critical dla**: Order sizing, margin calculations
- **dYdX Specific**: Dynamic margin requirements

## Implementacja Connectorów dYdX v4

### Wzorzec WebSocket-First dYdX v4 Connector
**Philosophy**: Official dydx-v4-client package primary for WebSocket (IndexerSocket), REST API (IndexerClient) secondary dla dYdX v4 z multiple data stream management through official client interfaces

### Wymagania Implementacyjne

#### Official dYdX v4 Client Integration (MANDATORY):
- **dydx-v4-client Package**: Use official pip package for all dYdX v4 operations
- **IndexerSocket Class**: Primary WebSocket implementation for real-time data
- **IndexerClient Class**: REST API operations for historical data and account queries
- **NodeClient Class**: Blockchain operations for order placement and management
- **Wallet & KeyPair Classes**: Official authentication and key management
- **Network Configuration**: Use TESTNET/MAINNET configuration from official client
- **Built-in Rate Limiting**: Leverage client's built-in rate limiting mechanisms

#### WebSocket Management (Primary - dydx-v4-client):
- **Official dYdX Client**: Use dydx-v4-client pip package IndexerSocket class
- **Built-in Connection Management**: Leverage official client's connection pooling
- **Automatic Reconnection**: Use client's built-in exponential backoff retry logic
- **Message Routing**: Stream-specific message handling via client's dispatcher
- **Data Frame Aggregation**: Combine multiple WebSocket messages into complete data structures
- **Incremental Updates**: Handle orderbook delta updates and rebuild full snapshots
- **Rate Limiting**: Respect dYdX v4 WebSocket limits through official client
- **Error Recovery**: Graceful handling via official client's error mechanisms
- **Authentication**: Use official client's authentication for private streams

#### REST API Integration (Secondary - dydx-v4-client):
- **Official IndexerClient**: Use dydx-v4-client pip package IndexerClient class
- **Account Queries**: Historical data and account state via official client
- **Order Management**: Order placement and cancellation through NodeClient
- **Market Configuration**: Market metadata retrieval via IndexerClient
- **Authentication**: Secure authentication through official Wallet and KeyPair classes
- **Rate Limiting**: Respect dYdX v4 REST API limits via official client
- **Error Handling**: Comprehensive error recovery through client's built-in mechanisms
#### Data Processing:
- **Real-time Processing**: <10ms WebSocket message processing
- **Stream Data Aggregation**: Aggregate multiple IndexerSocket messages to build complete data frames
- **Orderbook Reconstruction**: Combine incremental orderbook updates into full snapshots
- **OHLCV Frame Building**: Aggregate tick data into proper OHLCV candles
- **Funding Rate Compilation**: Collect funding data across multiple messages for complete rates
- **Data Validation**: Comprehensive data quality checks on aggregated frames
- **Memory Management**: Circular buffers dla historical aggregated data
- **Stream Synchronization**: Coordinate multiple WebSocket streams for frame completion
- **Deduplication**: Handle duplicate messages during frame aggregation
- **Funding Rate Integration**: Embed aggregated funding data with market data frames

#### Performance Optimization:
- **Memory Efficiency**: Minimal object creation dla WebSocket handling
- **CPU Optimization**: Vectorized calculations
- **Latency Minimization**: Direct JSON processing
- **Resource Management**: Controlled memory footprint
- **Garbage Collection**: Optimized GC behavior
- **dYdX Specific**: Optimized dla high-frequency perpetual data via WebSocket

## Walidacja Danych (KRYTYCZNA)

### Perpetual Market Data Validation:
- **Price Range Validation**: Reasonable price movements
- **Volume Validation**: Realistic volume patterns dla perpetuals
- **Timestamp Validation**: Chronological data order
- **Completeness Check**: No missing critical data
- **Consistency Check**: Cross-stream data correlation
- **Funding Rate Validation**: Reasonable funding rate changes

### Orderbook Validation:
- **Spread Validation**: Reasonable bid-ask spreads dla perpetuals
- **Depth Validation**: Sufficient liquidity depth
- **Price Level Validation**: Proper price level ordering
- **Update Validation**: Consistent orderbook updates
- **Arbitrage Detection**: Cross-market opportunities
- **Market Maker Recognition**: Identify institutional liquidity

### Trade Data Validation:
- **Execution Validation**: Valid perpetual trade executions
- **Price Validation**: Within orderbook bounds
- **Volume Validation**: Realistic trade sizes dla perpetuals
- **Frequency Validation**: Normal trading patterns
- **Market Impact Validation**: Expected price impact
- **Funding Impact Validation**: Trade timing vs funding periods

### Funding Rate Data Validation:
- **Rate Range Validation**: Funding rates within reasonable bounds
- **Historical Consistency**: Funding rate trend validation
- **Cross-Market Validation**: Funding rates vs market conditions
- **Timing Validation**: Funding period accuracy
- **Impact Assessment**: Funding rate impact on positions

## WebSocket-First Implementation Strategy

### Primary WebSocket Streams (dydx-v4-client IndexerSocket):
1. **Market Data Stream**: Real-time OHLCV dla all perpetuals via IndexerSocket (requires tick aggregation)
2. **Orderbook Stream**: Live order book updates via IndexerSocket subscriptions (requires delta aggregation)
3. **Trade Stream**: Real-time trade execution data via IndexerSocket (requires volume aggregation)
4. **Funding Rate Stream**: 8-hour funding rate cycles via IndexerSocket (requires multi-message compilation)
5. **Account Stream**: Position and balance updates via IndexerSocket (paper trading)

### Secondary REST API Usage (dydx-v4-client IndexerClient/NodeClient):
1. **Historical Data**: Backfill dla missing WebSocket data via IndexerClient
2. **Account Queries**: Initial account state via IndexerClient
3. **Market Configuration**: Market rules and parameters via IndexerClient
4. **Order Management**: Order placement and management via NodeClient

### Connection Architecture (Official dYdX v4 Client):
```
dYdX v4 Official Client Manager
├── IndexerSocket (WebSocket - Primary)
│   ├── Market Data Connection
│   ├── Orderbook Data Connection
│   ├── Trade Data Connection
│   └── Account Data Connection (Private)
├── IndexerClient (REST - Secondary)
│   ├── Account Endpoints
│   ├── Market Endpoints
│   └── Historical Data Endpoints
└── NodeClient (Blockchain Operations)
    ├── Order Placement
    ├── Order Cancellation
    └── Account Management
```
- **Volume Validation**: Realistic volume patterns dla perpetuals from aggregated streams
- **Timestamp Validation**: Chronological data order across multiple message frames
- **Completeness Check**: No missing critical data in aggregated frames
- **Consistency Check**: Cross-stream data correlation after aggregation
- **Funding Rate Validation**: Reasonable funding rate changes from compiled data

### Orderbook Validation:
- **Spread Validation**: Reasonable bid-ask spreads dla perpetuals
- **Depth Validation**: Sufficient liquidity depth from aggregated updates
- **Price Level Validation**: Proper price level ordering after incremental updates
- **Update Validation**: Consistent orderbook state after delta aggregation
- **Arbitrage Detection**: Cross-market opportunities from complete orderbook frames
- **Market Maker Recognition**: Identify institutional liquidity patterns from aggregated data

### Trade Data Validation:
- **Execution Validation**: Valid perpetual trade executions from aggregated trade streams
- **Price Validation**: Within orderbook bounds using reconstructed orderbook
- **Volume Validation**: Realistic trade sizes dla perpetuals from volume aggregation
- **Frequency Validation**: Normal trading patterns from aggregated trade frequency
- **Market Impact Validation**: Expected price impact from trade aggregation analysis
- **Funding Impact Validation**: Trade timing vs funding periods using compiled funding data

### Funding Rate Data Validation:
- **Rate Range Validation**: Funding rates within reasonable bounds
- **Historical Consistency**: Funding rate trend validation
- **Cross-Market Validation**: Funding rates vs market conditions
- **Timing Validation**: Funding period accuracy
- **Impact Assessment**: Funding rate impact on positions

## Cache Strategy (Memory-Only)

### Hot Data Cache:
- **Current Prices**: Real-time price cache dla all perpetuals
- **Recent Orderbook**: Last 100 levels per side
- **Trade History**: Last 1000 trades per market
- **Funding Rates**: Current and historical funding rates
- **Account State**: Current positions and margin
- **Market Metadata**: Configuration cache

### Cache Optimization:
- **LRU Eviction**: Least recently used data removal
- **Time-Based Expiry**: Automatic data expiration
- **Memory Bounds**: Fixed memory allocation
- **Cache Warming**: Pre-load critical data
- **Access Patterns**: Optimize dla trading patterns
- **Funding Rate Cache**: Optimized funding rate storage

## dYdX v4 API Integration

### REST API Usage:
- **Market Discovery**: Get available perpetual markets
- **Historical Data**: Fetch historical funding rates
- **Account Management**: Account setup and configuration
- **Market Metadata**: Get market specifications
- **Rate Limiting**: Respect REST API limits

### WebSocket API Usage:
- **Real-time Subscriptions**: Market data, orderbook, trades
- **Account Updates**: Position and margin changes
- **Funding Updates**: Real-time funding rate changes
- **Order Updates**: Order status changes
- **Connection Management**: Maintain persistent connections

### Authentication:
- **API Key Management**: Secure key storage and rotation
- **Signature Generation**: Request signing dla private endpoints
- **Session Management**: Maintain authenticated sessions
- **Permission Validation**: Ensure proper API permissions
- **Security**: Secure credential handling

## Performance Benchmarks

### Target Performance:
- **WebSocket Latency**: <10ms message processing
- **Signal Generation**: <30ms from data to signal
- **Order Processing**: <50ms decision to order simulation
- **Memory Usage**: <512MB total allocation
- **CPU Usage**: <25% single core
- **Connection Uptime**: >99.9% stability

### dYdX v4 Specific Optimizations:
- **Funding Rate Processing**: <5ms funding impact calculation
- **Cross-Margin Calculation**: <10ms margin requirement updates
- **Perpetual Signal Processing**: Optimized dla leverage instruments
- **Market Maker Detection**: Fast institutional pattern recognition
- **Arbitrage Detection**: Ultra-low latency opportunity identification
