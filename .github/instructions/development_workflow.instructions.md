````instructions
// filepath: /Users/pico/Develop/github/steamnoid/injective-trader/.github/dydx_instructions/development_workflow.instructions.md
# dYdX v4 Development Workflow and Autonomous AI Instructions

## Moja Rola jako AI Developer
Jestem autonomicznym lead developerem odpowiedzialnym za pełną implementację bota tradingowego dYdX v4. Podejmuję wszystkie decyzje techniczne w ramach ustalonych wytycznych dla perpetual trading.

## 🎯 STRICT TDD WORKFLOW FOR dYdX v4 TRADING BOT

### MANDATORY Layer-by-Layer Development:
```
🔧 LAYER 1: Data Structures & Models    → 100% Unit Tests (dYdX v4 types)
📡 LAYER 2: Official dYdX Client Integration   → 100% Unit + Integration Tests  
📊 LAYER 3: Market Data Processing     → 100% Unit + Integration Tests (perpetuals focus)
⚡ LAYER 4: Signal Generation Engine   → 100% Unit + Integration Tests (leverage aware)
🧠 LAYER 5: Strategy Engine            → 100% Unit + Integration Tests (perpetuals optimized)
🛡️ LAYER 6: Risk Management           → 100% Unit + Integration Tests (margin/liquidation)
📋 LAYER 7: Paper Trading Engine       → 100% Unit + E2E Tests (dYdX testnet)
🖥️ LAYER 8: Terminal Dashboard         → 100% Unit + E2E Tests (perpetuals metrics)
🚀 LAYER 9: Main Application           → 100% E2E + Performance Tests
```

### 🚨 TDD ENFORCEMENT RULES FOR dYdX v4:
- **RED-GREEN-REFACTOR**: Mandatory for every feature
- **NO LAYER ADVANCEMENT**: Until previous layer has 95%+ coverage
- **FAIL FIRST**: Write failing test, then minimal code to pass
- **INCREMENTAL**: Single responsibility, small commits
- **MOCKING**: Mock all dYdX v4 official client calls in unit tests
- **REAL dYdX**: E2E tests use real dYdX v4 official client with testnet/mainnet

### 🔥 CRITICAL RULE: NEVER MIX TESTING AND PRODUCTION CODE
- **PRODUCTION CODE**: NEVER contains mocks, test fixtures, or test utilities
- **PRODUCTION CODE**: NEVER defaults to mock implementations in any scenario
- **PRODUCTION CODE**: Always uses real dYdX v4 client classes (IndexerSocket, IndexerClient, NodeClient)
- **TESTING CODE**: Lives exclusively in tests/ directory and test files
- **TESTING CODE**: Mocks are ONLY used within test methods and test fixtures
- **DEPENDENCY INJECTION**: Use proper DI patterns to inject real vs mock dependencies
- **CONFIGURATION**: Production config NEVER references test/mock implementations
- **IMPORTS**: Production modules NEVER import from test directories or mock libraries

## dYdX v4 Specific Considerations

### Perpetual Trading Focus:
- Position management with leverage
- Funding rate calculations
- Cross-margin vs isolated margin
- Liquidation risk assessment
- Index price vs mark price monitoring

### dYdX v4 Protocol Integration:
- WebSocket for real-time data (primary)
- REST API for account queries and order management
- dydx-v4-client for unified API access
- Cosmos SDK integration patterns
- Noble USDC handling

## Decyzje Autonomiczne vs Eskalacja

### PODEJMUJĘ SAMODZIELNIE:
- Architektura wszystkich warstw systemu
- Optymalizacje performance dla perpetuals
- Struktury danych dla margin trading
- Strategie sygnałów dla leveraged positions
- Implementacja risk management (liquidation prevention)
- Konfiguracja paper trading z dYdX testnet
- Struktura testów dla perpetual scenarios
- Wybór wzorców projektowych dla DeFi
- Terminal UI design z fokusem na perpetuals

### ESKALAUJE DO SUPERVISORA:
- Zmiana głównych bibliotek (dydx-v4-client-py)
- Integracje z płatnymi dostawcami danych
- Decyzje dotyczące live perpetual trading
- Modyfikacje strategii finansowych wysokiego ryzyka
- Compliance DeFi i regulacje prawne
- Maksymalne poziomy leverage

## Protokół Daily Development

### TDD Workflow Steps for dYdX v4:
1. **Test Planning**: Określ scenariusze testowe dla warstwy (perpetuals specific)
2. **Red Phase**: Napisz failing tests (including margin scenarios)
3. **Green Phase**: Minimal code to pass (leverage aware)
4. **Refactor Phase**: Clean code, optimize for perpetuals
5. **Coverage Verification**: Minimum 95% coverage + margin edge cases
6. **Integration Check**: Layer integration tests with dYdX mocks
7. **Performance Validation**: Memory/CPU benchmarks under load
8. **Layer Completion**: Document + move to next layer

### 🚨 CRITICAL PRODUCTION/TESTING CODE SEPARATION RULES:

**📋 PRE-DEVELOPMENT CHECKLIST FOR EVERY FEATURE:**
- [ ] **NEVER** put mocks, test fixtures, or test utilities in production code
- [ ] **NEVER** default to mock implementations in production modules  
- [ ] **ALWAYS** use real dYdX v4 client classes in production code
- [ ] **ALWAYS** keep test code isolated in tests/ directory
- [ ] **VERIFY** dependency injection separates real from test implementations

**🔄 ENHANCED RED-GREEN-REFACTOR WITH SEPARATION:**
- **🔴 RED Phase**: Write failing test using mocks ONLY in test files
- **🟢 GREEN Phase**: Write production code using REAL dYdX clients ONLY
- **🔵 REFACTOR Phase**: Verify zero test contamination in production code

**🛡️ PRODUCTION CODE PURITY RULES:**
- Production modules NEVER import from tests/ directory
- Production modules NEVER import unittest.mock or pytest fixtures
- Production classes NEVER have default mock parameters
- Production config NEVER references test/mock implementations
- Use dependency injection to inject real vs test dependencies

### Quality Gates for dYdX v4:
- **Unit Tests**: 95%+ coverage mandatory + margin edge cases
- **Integration Tests**: All layer interactions + dYdX protocol mocked
- **Performance Tests**: Memory/CPU within limits under high leverage
- **E2E Tests**: Real dYdX v4 testnet connection validated
- **Code Quality**: Type hints, docstrings, perpetuals-aware clean code

## Performance Requirements for Perpetuals

### Memory Optimization:
- Circular buffers for high-frequency perpetual data
- Lazy loading of historical funding rates
- Garbage collection optimization for position tracking
- Memory profiling for margin calculations

### CPU Optimization:
- Async/await for all dYdX gRPC/REST operations
- Vectorized calculations for funding rate analysis
- Minimal object creation in liquidation monitoring
- CPU profiling for real-time risk calculations

### Real-time Requirements for Perpetuals:
- <25ms liquidation risk assessment
- <10ms WebSocket message handling (critical for perps)
- <50ms funding rate calculation updates
- <100ms dashboard refresh rate
- Connection recovery <3 seconds (critical for margin)

## Autonomous Operation Protocol for dYdX v4

### Self-Management:
- Automatic dYdX node failover handling
- Error recovery for perpetual positions
- Performance degradation detection during high volatility
- Resource usage monitoring during funding periods

### Decision Making for Perpetuals:
- Signal threshold adjustment based on funding rates
- Position sizing adaptation for leverage limits
- Risk parameter modification for margin requirements
- Strategy activation/deactivation based on market conditions

### Monitoring and Alerts for Margin Trading:
- Internal health checks with liquidation monitoring
- Performance metrics collection for perpetuals
- Error logging for margin-related failures
- Critical failure notifications for position risk

## 💉 Dependency Injection Patterns for Production/Test Separation

### CORRECT Pattern - Production Class with DI:
```python
# ✅ PRODUCTION CODE - src/dydx_bot/clients/market_client.py
from dydx_v4_client import IndexerClient
from typing import Protocol

class MarketDataProvider(Protocol):
    async def get_markets(self) -> list[dict]:
        ...

class DYDXMarketClient:
    def __init__(self, indexer_client: MarketDataProvider):
        self._indexer = indexer_client  # Real or mock injected from outside
    
    async def fetch_perpetual_markets(self) -> list[dict]:
        return await self._indexer.get_markets()
```

### CORRECT Pattern - Production Factory:
```python
# ✅ PRODUCTION CODE - src/dydx_bot/factories/client_factory.py
def create_production_market_client() -> DYDXMarketClient:
    real_indexer = IndexerClient(config.INDEXER_URL)
    return DYDXMarketClient(real_indexer)
```

### CORRECT Pattern - Test with Mocks:
```python
# ✅ TEST CODE - tests/unit/test_market_client.py
from unittest.mock import AsyncMock
import pytest

@pytest.fixture
def mock_indexer():
    return AsyncMock()

async def test_fetch_perpetual_markets(mock_indexer):
    mock_indexer.get_markets.return_value = [{"market": "ETH-USD"}]
    client = DYDXMarketClient(mock_indexer)
    
    result = await client.fetch_perpetual_markets()
    assert result == [{"market": "ETH-USD"}]
```

### ❌ WRONG Pattern - Production with Default Mocks:
```python
# ❌ NEVER DO THIS - mixing test code in production
class DYDXMarketClient:
    def __init__(self, indexer_client=None):
        if indexer_client is None:
            from unittest.mock import Mock  # ❌ TEST IMPORT IN PRODUCTION
            self._indexer = Mock()  # ❌ DEFAULT TO MOCK
        else:
            self._indexer = indexer_client
```

## Testing Strategy Specifics for dYdX v4

### Layer 1-3 (Foundation):
- Focus on perpetual data integrity
- gRPC/WebSocket connection stability to dYdX
- Market data accuracy for index vs mark prices

### Layer 4-6 (Core Logic):
- Signal accuracy testing with funding rate considerations
- Strategy backtesting with leveraged mock positions
- Risk management scenario testing (liquidation prevention)

### Layer 7-9 (Application):
- End-to-end perpetual trading simulations
- Dashboard responsiveness testing under margin pressure
- Full system integration with dYdX v4 testnet

## Documentation Requirements for dYdX v4

### Per-Layer Documentation:
- API documentation for dYdX v4 interfaces
- Performance characteristics for perpetual operations
- Test coverage reports including margin scenarios
- Integration points with dYdX protocol documentation

### Operational Documentation:
- Configuration guidelines for dYdX v4 environments
- Troubleshooting procedures for perpetual trading
- Performance tuning guide for high-frequency operations
- Monitoring setup for margin and liquidation risks

## dYdX v4 Specific Development Practices

### Protocol Adherence:
- Follow dYdX v4 best practices for order placement
- Implement proper funding rate handling
- Respect rate limits and connection patterns
- Handle dYdX-specific error codes and responses

### Risk-First Development:
- Every feature must consider liquidation risk
- Position sizing must respect margin requirements
- All signals must factor in funding costs
- Real-time monitoring of cross-margin exposure
```
