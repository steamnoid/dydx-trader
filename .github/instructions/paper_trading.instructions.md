```instructions
// filepath: /Users/pico/Develop/github/steamnoid/injective-trader/.github/dydx_instructions/paper_trading.instructions.md
# dYdX v4 Perpetual Paper Trading Implementation Instructions

## 🎯 PERPETUAL PAPER TRADING PHILOSOPHY

### Core Principle: Maximum Realism for Leveraged Trading
**Goal**: Paper trading musi być identyczne z real perpetual trading minus actual money exchange. Wszystkie aspekty real perpetual trading - funding rates, margin requirements, liquidations, slippage, fees, latency - muszą być accurately simulated.

## dYdX v4 Paper Trading Architecture

### Virtual Account Management (Cross-Margin Focus):
- **Starting Capital**: Configurable initial USDC portfolio value
- **Cross-Margin Balance**: Real-time cross-margin balance tracking
- **Position Tracking**: All open perpetual positions with leverage
- **Margin Utilization**: Current margin usage and available margin
- **Liquidation Price Tracking**: Real-time liquidation price calculation
- **Funding Payment History**: Complete funding rate payment log
- **Transaction History**: Complete perpetual trade history
- **P&L Calculation**: Real-time profit/loss including funding costs
- **Portfolio Value**: Mark-to-market portfolio valuation

### Perpetual Order Simulation Framework:
- **Order Types**: Market, limit, stop-loss, take-profit, reduce-only orders
- **Leverage Validation**: Position size vs available margin validation
- **Order Rejection**: Simulate realistic rejection scenarios for perpetuals
- **Partial Fills**: Simulate partial order execution with size restrictions
- **Position Limits**: Respect dYdX v4 position size limits per market
- **Cross-Margin Impact**: Simulate cross-margin effects of new positions
- **Slippage Simulation**: Realistic slippage based on perpetual orderbook depth

### dYdX v4 Market Data Integration:
- **Real-time Perpetual Pricing**: Use actual dYdX v4 market data
- **Index Price vs Mark Price**: Accurate pricing differential tracking
- **Funding Rate Data**: Real-time funding rate calculation and application
- **Orderbook Integration**: Simulate fills based on real perpetual orderbook
- **Liquidity Assessment**: Account dla actual perpetual market liquidity
- **24/7 Trading**: Continuous operation simulation
- **Market Events**: Simulate response to funding rate changes and volatility

## Realistic Perpetual Trading Simulation

### dYdX v4 Fee Structure Simulation:
- **Trading Fees**: Exact dYdX v4 fee structure (maker/taker)
- **Funding Rate Payments**: Hourly funding rate charge/credit simulation
- **Position Size Impact**: Fee structure based on position size
- **Cross-Margin Efficiency**: Accurate margin requirement calculation
- **Network Costs**: Minimal gas costs for dYdX v4 operations
- **Total Cost Calculation**: All-in cost per trade including funding

### Execution Simulation for Perpetuals:
- **Market Orders**: Immediate execution with perpetual-specific slippage
- **Limit Orders**: Queue-based execution with funding rate considerations
- **Stop Orders**: Triggered execution based on mark price vs index price
- **Execution Latency**: Simulate realistic dYdX v4 execution delays
- **Rejection Scenarios**: Insufficient margin, position limits, market conditions
- **Partial Execution**: Large perpetual orders split across price levels
- **Cross-Margin Calculations**: Real-time margin requirement updates

### Margin and Liquidation Simulation:
- **Cross-Margin Requirements**: Exact dYdX v4 margin calculation
- **Liquidation Engine**: Automatic position closure simulation
- **Liquidation Price Updates**: Real-time liquidation price calculation
- **Margin Calls**: Simulate margin call scenarios
- **Position Limits**: Per-market and total portfolio position limits
- **Risk Monitoring**: Real-time cross-margin risk calculation
- **Emergency Deleveraging**: Simulate ADL (Auto-Deleveraging) scenarios

## Advanced Perpetual Paper Trading Features

### Multi-Perpetual Strategy Simulation:
- **Strategy Isolation**: Separate P&L per perpetual strategy
- **Cross-Margin Allocation**: Dynamic margin allocation per strategy
- **Funding Rate Strategies**: Funding rate arbitrage simulation
- **Leverage Optimization**: Dynamic leverage adjustment per strategy
- **Cross-Strategy Correlation**: Perpetual portfolio correlation analysis
- **Strategy Risk**: Individual strategy risk metrics for leveraged positions
- **Dynamic Rebalancing**: Real-time portfolio rebalancing with margin efficiency

### Perpetual Market Condition Simulation:
- **High Volatility**: Extreme perpetual market volatility simulation
- **Funding Rate Volatility**: Funding rate spike simulation
- **Low Liquidity**: Thin perpetual market simulation
- **Liquidation Cascades**: Chain liquidation scenario simulation
- **Cross-Market Correlation**: Multi-perpetual correlation scenarios
- **Network Congestion**: dYdX v4 network congestion simulation
- **Oracle Price Deviations**: Index vs mark price extreme scenarios

### Leveraged Risk Testing Scenarios:
- **Stress Testing**: Extreme leveraged position scenarios
- **Black Swan Events**: Rare event simulation with high leverage
- **Margin Call Cascades**: Multiple position liquidation scenarios
- **Funding Rate Shocks**: Extreme funding rate scenario testing
- **Cross-Margin Breakdown**: Portfolio cross-margin failure simulation
- **Liquidity Crisis**: Perpetual market liquidity disappearance
- **Recovery Testing**: System recovery validation after liquidations

## Perpetual Performance Tracking and Analytics

### Real-time Perpetual Performance Metrics:
- **Unrealized P&L**: Current perpetual position value (mark-to-market)
- **Realized P&L**: Closed perpetual position profits/losses
- **Funding P&L**: Cumulative funding rate payments/receipts
- **Daily P&L**: Daily performance including funding costs
- **Portfolio Value**: Total cross-margin portfolio valuation
- **Leverage Ratio**: Current portfolio leverage utilization
- **Margin Utilization**: Percentage of available margin used
- **Liquidation Distance**: Distance to liquidation prices

### Perpetual Trading Analytics:
- **Win Rate**: Percentage of profitable perpetual trades
- **Average Win/Loss**: Leveraged trade size analytics
- **Funding-Adjusted Sharpe**: Risk-adjusted performance including funding
- **Maximum Drawdown**: Worst portfolio decline with leverage
- **Leverage Efficiency**: Return per unit of leverage utilized
- **Position Holding Time**: Average perpetual position duration
- **Funding Rate Impact**: Total funding cost/benefit analysis

### Cross-Margin Strategy Performance Analysis:
- **Strategy Attribution**: Performance per perpetual strategy
- **Funding Factor Analysis**: Funding rate impact per strategy
- **Market Regime Performance**: Performance w different volatility regimes
- **Leverage Correlation**: Strategy correlation under different leverage
- **Risk Contribution**: Cross-margin risk attribution per strategy
- **Alpha Generation**: Excess return after funding costs

## dYdX v4 Validation and Accuracy

### Perpetual Data Accuracy Validation:
- **Mark Price vs Index Price**: Validate pricing differential accuracy
- **Funding Rate Calculation**: Verify funding rate computation
- **Margin Requirement Accuracy**: Confirm cross-margin calculations
- **Liquidation Price Accuracy**: Validate liquidation price calculation
- **Execution Price Validation**: Confirm realistic perpetual execution
- **Fee Calculation Verification**: Validate all perpetual fee calculations
- **P&L Accuracy**: Verify profit/loss including funding costs

### Perpetual Simulation Quality Metrics:
- **Slippage Accuracy**: Compare simulated vs real perpetual slippage
- **Funding Rate Accuracy**: Validate funding rate application
- **Margin Call Timing**: Verify margin call trigger accuracy
- **Liquidation Simulation**: Confirm realistic liquidation scenarios
- **Cross-Margin Efficiency**: Validate margin utilization calculations
- **Latency Simulation**: Confirm realistic dYdX v4 latency

### Benchmarking Against Real Perpetual Trading:
- **Performance Correlation**: Compare with real dYdX v4 performance
- **Risk Metric Validation**: Verify leveraged risk calculations
- **Funding Cost Accuracy**: Confirm funding rate cost calculations
- **Margin Efficiency**: Validate cross-margin optimization
- **Strategy Effectiveness**: Confirm perpetual strategy viability
- **Scalability Assessment**: Evaluate real-world leveraged scalability

## dYdX v4 Perpetual Paper Trading Dashboard

### Real-time Display Components:
- **Cross-Margin Overview**: Current portfolio margin status
- **Perpetual Positions**: All open positions with leverage and liquidation prices
- **Funding Rate Display**: Current and historical funding rates
- **Order Status**: Active and recent perpetual orders
- **Margin Utilization**: Visual margin usage and available capacity
- **P&L Summary**: Performance including funding costs
- **Risk Metrics**: Real-time leveraged risk exposure
- **Market Data**: Real-time perpetual market information

### Perpetual Performance Visualization:
- **P&L Charts**: Portfolio performance over time including funding
- **Position Charts**: Individual perpetual position performance
- **Funding Rate Charts**: Funding rate impact over time
- **Leverage Charts**: Leverage utilization evolution
- **Risk Charts**: Cross-margin risk metric evolution
- **Trade History**: Complete perpetual trading activity
- **Strategy Performance**: Per-strategy analytics with funding impact
- **Market Correlation**: Portfolio perpetual market correlation

### Interactive Perpetual Controls:
- **Emergency Deleveraging**: Manual position reduction controls
- **Leverage Adjustment**: Real-time leverage modification
- **Margin Management**: Cross-margin allocation controls
- **Strategy Control**: Enable/disable perpetual strategies
- **Risk Parameter Adjustment**: Real-time risk limit changes
- **Position Management**: Manual perpetual position adjustments
- **Alert Management**: Margin and liquidation alert configuration
- **Simulation Control**: Perpetual paper trading parameters

## Transition to Live Perpetual Trading

### Live Perpetual Trading Readiness Criteria:
- **Consistent Profitability**: Sustained profitable perpetual paper trading
- **Funding-Adjusted Returns**: Positive returns after funding costs
- **Risk Management Validation**: Proven leveraged risk control
- **Margin Efficiency**: Optimal cross-margin utilization
- **System Stability**: Robust perpetual operation under stress
- **Liquidation Avoidance**: Demonstrated liquidation prevention
- **Performance Metrics**: Acceptable risk-adjusted leveraged returns
- **Strategy Validation**: Proven perpetual strategy effectiveness

### Paper to Live Perpetual Trading Bridge:
- **dYdX v4 Testnet Integration**: Smooth transition from simulation to testnet
- **Mainnet Account Setup**: Real dYdX v4 account connection
- **Cross-Margin Configuration**: Live trading margin setup
- **Risk Parameter Calibration**: Live perpetual trading risk adjustment
- **Performance Monitoring**: Enhanced live leveraged trading monitoring
- **Emergency Procedures**: Live perpetual trading emergency protocols
- **Compliance Integration**: DeFi regulatory compliance activation
- **Funding Rate Monitoring**: Real-time funding cost optimization

## dYdX v4 Specific Considerations

### Noble USDC Integration:
- **USDC Bridge Simulation**: Noble USDC deposit/withdrawal simulation
- **Cross-Chain Delays**: Simulate realistic USDC bridge timing
- **Bridge Fee Simulation**: Include bridge costs in calculations

### Perpetual Market Specifics:
- **24/7 Operation**: Continuous trading simulation
- **No Settlement**: Perpetual contract characteristics
- **Funding Rate Mechanics**: 8-hour funding rate cycles
- **Index Price Tracking**: Underlying asset price tracking
- **Mark Price Calculation**: dYdX v4 mark price methodology

### Risk Management for Perpetuals:
- **Leverage Limits**: Respect maximum leverage per market
- **Cross-Margin Optimization**: Efficient margin utilization
- **Liquidation Prevention**: Advanced liquidation avoidance
- **Position Concentration**: Limit position concentration risk
- **Funding Rate Risk**: Manage funding rate exposure
```
