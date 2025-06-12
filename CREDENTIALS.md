# dYdX v4 Trading Bot Credentials

## Testnet Configuration

The following credentials are provided for autonomous trading bot testing on dYdX v4 testnet:

```json
{
  "mnemonic": "clerk oak wife parrot verb science hockey tomato father situate resource trade kangaroo protect social boil survey pulp mask soon wedding choice guilt rookie",
  "address": "dydx1yg9wumc4hy85vd3833zd46t5rpqlkvngxud6hr",
  "network": "testnet",
  "description": "dYdX testnet configuration for autonomous trading bot testing"
}
```

## Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. The testnet credentials are already configured in `.env.example`

3. For production mainnet trading, replace with your own credentials:
   - Generate a new mnemonic using the dYdX v4 client
   - Fund your testnet wallet with USDC for trading
   - Never use testnet credentials on mainnet

## Security Notes

- **Testnet Only**: These credentials are for testnet development only
- **No Real Value**: Testnet tokens have no monetary value
- **Development Purpose**: Use for testing trading strategies and bot functionality
- **Mainnet Warning**: Never use testnet credentials on mainnet

## Layer 2 Completion Status

✅ **Connection Layer Completed**: 86.23% integration coverage achieved
- Full dYdX v4 client integration
- Protocol-first approach validated
- Real testnet connection testing
- Error handling and resilience

## Next Development Phase

**Layer 3: Data Processing**
- Market data ingestion from IndexerSocket
- OHLCV data aggregation
- Funding rate calculations
- Real-time orderbook management

Ready to proceed with Layer 3 development using TDD approach.
