# dYdX v4 Sniper Bot - Project Overview

## Protocol-First Development Philosophy
**Critical**: Follow dYdX v4 client nomenclature and patterns directly. Build domain models ON-DEMAND when they provide clear value, not comprehensively upfront. Start with official dydx-v4-client integration.

## Mission Statement
Stworzenie w pełni autonomicznego bota tradingowego wykorzystującego dYdX v4 Protocol via official dydx-v4-client to sniper trading na wszystkich parach perpetual futures z wykorzystaniem protocol-native signals and metrics.

## Cele Biznesowe
- **Główny**: Autonomiczny sniper trading na dYdX v4 perpetual markets
- **Cel**: Maksymalizacja zysków poprzez wczesne wykrywanie możliwości tradingowych na perpetuals
- **Wynik**: Działający bot tradingowy z paper trading i live trading capabilities dla dYdX v4

## Kluczowe Komponenty Systemu
1. **Official dYdX Client Manager** - IndexerSocket/IndexerClient/NodeClient wrapper
2. **Market Scanner** - monitorowanie wszystkich perpetual markets via IndexerSocket
3. **Signal Engine** - analiza OHLCV, orderbook i funding rate metryk
4. **Strategy Engine** - wybór optymalnych pozycji perpetual
5. **Risk Manager** - zarządzanie ryzykiem i leverage
6. **Paper Trading** - symulacja na danych mainnet z realistic funding
7. **Terminal Dashboard** - interfejs użytkownika (rich library)

## Wymagania Techniczne
- **Język**: Python 3.11+
- **Główna biblioteka**: dydx-v4-client (oficjalna biblioteka dYdX v4 - MANDATORY)
- **WebSocket**: dydx-v4-client IndexerSocket class (NO manual websockets)
- **REST**: dydx-v4-client IndexerClient class (NO manual REST calls)
- **Blockchain**: dydx-v4-client NodeClient class for order management
- **Authentication**: dydx-v4-client Wallet & KeyPair classes
- **Dashboard**: rich library (terminal UI)
- **Brak bazy danych**: wszystkie dane z dYdX v4 Official Client API
- **Optymalizacja**: RAM i CPU optimized dla high-frequency perpetual trading
- **Deployment**: Standalone Python application

## Kluczowe Źródła Danych (dYdX v4 Official Client)
1. **Perpetual Market Streams** - OHLCV real-time via IndexerSocket dla wszystkich perpetuals
2. **Orderbook Streams** - depth, spreads, liquidity via IndexerSocket dla perpetuals
3. **Trade Streams** - wykonane transakcje perpetual via IndexerSocket
4. **Account Streams** - pozycje, balanse, margin via IndexerSocket (paper trading)
5. **Funding Rate Streams** - funding rates via IndexerSocket dla wszystkich perpetuals
6. **Market Metadata** - tick size, lot size, fees, margin requirements via IndexerClient

## Ograniczenia i Wymagania dYdX v4
- Focus na perpetual futures (główny produkt dYdX v4)
- Funding rate optimization critical dla profitability
- Cross-margining system understanding
- Real-time margin monitoring
- dYdX v4 specific fee structure
- USDC settlement currency only

## Success Metrics
- **Performance**: <30ms signal processing latency (faster than Injective due to centralized nature)
- **Memory**: <512MB RAM usage sustained
- **CPU**: <25% single core utilization
- **Uptime**: >99.9% connection stability
- **Testing**: >95% unit test coverage
- **Paper Trading**: Profitable simulation results accounting dla funding costs

- **Development Strategy
- **Bottom-up TDD**: Start from lowest layer
- **Layer-by-layer**: Complete testing before next layer
- **Official dYdX v4 Client Focus**: Use dydx-v4-client package exclusively
- **Real-time Focus**: Optimize for low-latency perpetual trading
- **Autonomous Design**: Self-contained, self-managing system
- **Funding Rate Aware**: All strategies must account dla funding costs

## Risk Management Framework - dYdX v4 Specific
- Position sizing based on cross-margin system
- Dynamic leverage adjustment based on funding rates
- Liquidation risk monitoring (dYdX v4 specific thresholds)
- Funding rate impact on position profitability
- USDC balance management
- Cross-collateralization risk assessment

## Monitoring and Observability
- Real-time P&L tracking including funding costs
- Funding rate impact analysis
- Margin utilization monitoring
- Liquidation distance tracking
- Position performance metrics
- dYdX v4 specific execution analytics

## dYdX v4 Advantages vs Injective
- **Centralized Matching**: Lower latency, better fills
- **Deep Liquidity**: Professional market makers
- **Advanced Perpetual Features**: Funding rates, cross-margin
- **Institutional Grade**: Better for larger position sizes
- **Lower Gas Costs**: No blockchain gas fees dla trading
- **24/7 Trading**: True perpetual trading without downtime

## dYdX v4 Specific Considerations
- **Funding Rate Strategy**: Key differentiator from spot trading
- **Cross-Margin System**: More complex risk management
- **Professional Competition**: Higher quality competition requires better signals
- **Regulatory Compliance**: KYC/AML requirements dla live trading
- **USDC Only**: Simplified but limits diversification
- **Centralized Risk**: Platform risk vs decentralized protocols
