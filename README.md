# dYdX v4 Perpetual Trading Bot

## Protocol-First Development Philosophy

This project follows a **protocol-first, domain-model-on-demand** approach. We start with the official dydx-v4-client and build abstractions only when they provide clear value beyond the protocol's native capabilities.

### Key Principles:
- **Protocol Truth**: dYdX v4 API is the single source of truth
- **Official Client First**: Use dydx-v4-client exclusively for all dYdX operations
- **Minimal Abstractions**: Build domain models ON-DEMAND, not comprehensively upfront
- **No Over-Engineering**: Avoid complex abstractions that force-fit protocol data

## Quick Start

### Prerequisites
- Python 3.11+
- dYdX v4 testnet account (for testing)

### Installation

```bash
# Clone the repository
git clone https://github.com/steamnoid/dydx-trader.git
cd dydx-trader

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### Configuration

Create a `.env` file with your dYdX v4 testnet credentials:

```bash
# dYdX v4 Testnet Configuration
DYDX_NETWORK=testnet
DYDX_MNEMONIC="your testnet mnemonic here"
DYDX_WALLET_ADDRESS="your testnet wallet address"
DYDX_PRIVATE_KEY="your testnet private key"

# Optional: Advanced settings
DYDX_NODE_URL="https://dydx-testnet.nodereal.io"
DYDX_INDEXER_URL="https://indexer.v4testnet.dydx.exchange"
```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m e2e            # End-to-end tests only

# Run tests with detailed output
pytest -v --cov-report=term-missing
```

### Development Workflow

This project follows strict TDD practices with protocol-first development:

1. **Start with Protocol**: Begin with actual dydx-v4-client integration
2. **Write Tests First**: Red-Green-Refactor cycle for each feature
3. **Minimal Models**: Create domain models only when protocol data needs structure
4. **95% Coverage**: Required before advancing to next layer

## Architecture

### 9-Layer Architecture (Protocol-First)

1. **Layer 1**: Protocol Data Structures - Use dydx-v4-client types directly
2. **Layer 2**: Official Client Integration - IndexerSocket, IndexerClient, NodeClient
3. **Layer 3**: Protocol Data Processing - Process client responses minimally
4. **Layer 4**: Protocol-Native Signals - Generate signals from client data
5. **Layer 5**: Strategy Engine - Minimal abstractions for trading logic
6. **Layer 6**: Protocol Risk Management - Leverage client's margin features
7. **Layer 7**: Paper Trading - dYdX testnet integration
8. **Layer 8**: Terminal Dashboard - Display protocol metrics
9. **Layer 9**: Main Application - Orchestrate all layers

### Key Components

- **dYdX Client Manager**: Wrapper around official dydx-v4-client
- **Market Scanner**: Monitor perpetual markets via IndexerSocket
- **Signal Engine**: Analyze OHLCV, orderbook, and funding rates
- **Risk Manager**: Leverage/margin management using client features
- **Paper Trading**: Simulation using testnet
- **Terminal Dashboard**: Rich-based UI

## 🎯 Current Status: Layer 2 Complete ✅

**Protocol-First Foundation Ready** - Official dYdX v4 client integration complete with 95%+ test coverage.

### ✅ Completed Layers
- **Layer 1**: Protocol Data Structures (Settings, Validation) ✅
- **Layer 2**: Official dYdX v4 Client Integration (NodeClient, IndexerClient, IndexerSocket, Wallet) ✅

### 🚧 Next: Layer 3 - Protocol Data Processing & Aggregation
Building real-time data processing using IndexerSocket patterns for:
- Perpetual OHLCV aggregation from tick data
- Orderbook reconstruction from incremental updates  
- Funding rate calculation and tracking
- Memory-optimized circular buffers for high-frequency data

### 📊 Current Metrics
- **25/25 unit tests passing** ✅
- **Protocol integration validated** ✅
- **Ready for Layer 3 development** 🟢

## Development Status

- [x] **Layer 1**: Protocol data structures setup ✅
- [x] **Layer 2**: Official dydx-v4-client integration ✅
- [ ] **Layer 3**: Market data processing 🚧
- [ ] **Layer 4**: Signal generation
- [ ] **Layer 5**: Strategy engine
- [ ] **Layer 6**: Risk management
- [ ] **Layer 7**: Paper trading
- [ ] **Layer 8**: Terminal dashboard
- [ ] **Layer 9**: Main application

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/protocol-improvement`)
3. Follow TDD practices with protocol-first approach
4. Ensure 95%+ test coverage
5. Run pre-commit hooks (`pre-commit run --all-files`)
6. Submit a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

This is educational/research software. Not financial advice. Use at your own risk.
