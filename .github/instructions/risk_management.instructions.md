```instructions
// filepath: /Users/pico/Develop/github/steamnoid/injective-trader/.github/dydx_instructions/risk_management.instructions.md
# dYdX v4 Perpetual Trading Risk Management Framework Instructions

## 🛡️ COMPREHENSIVE PERPETUAL TRADING RISK MANAGEMENT STRATEGY

### Philosophy: Liquidation Prevention First
**Priority**: Zapobieganie likwidacji ma absolutny priorytet nad zyskami. W perpetual trading, likwidacja oznacza całkowitą stratę pozycji bez możliwości odzyskania.

## Multi-Layer Risk Architecture for Perpetuals

### Layer 1: Position-Level Risk (Margin-Aware)
- **Position Sizing**: Kelly criterion z conservative multiplier adjusted dla leverage
- **Liquidation Distance Management**: Maintain safe distance from liquidation price
- **Stop-Loss Management**: Dynamic stop-loss adjusted dla funding costs
- **Take-Profit Logic**: Scaled profit taking considering funding rates
- **Leverage Optimization**: Dynamic leverage adjustment per position
- **Funding Rate Risk**: Monitor and manage funding cost exposure

### Layer 2: Cross-Margin Portfolio Risk
- **Maximum Cross-Margin Utilization**: Total margin usage limits (max 70%)
- **Sector Diversification**: Avoid concentration w correlated perpetuals
- **Leverage Concentration**: Prevent excessive leverage clustering
- **Cross-Margin Efficiency**: Optimize margin utilization across positions
- **Portfolio Liquidation Risk**: Monitor aggregate liquidation exposure
- **Funding Rate Portfolio Impact**: Total funding cost management

### Layer 3: dYdX v4 System-Level Risk
- **Operational Risk**: dYdX v4 protocol and node failure protection
- **Connectivity Risk**: WebSocket/REST disconnection handling
- **Market Risk**: Extreme perpetual market condition protection
- **Liquidity Risk**: Perpetual market liquidity assessment
- **Protocol Risk**: dYdX v4 protocol upgrade and governance risk
- **Oracle Risk**: Index price vs mark price deviation monitoring

## Perpetual Position Risk Management

### Leverage-Aware Position Sizing Framework:
- **Base Position Size**: 1-2% of available margin per position
- **Maximum Position Size**: Never exceed 10% of cross-margin dla single position
- **Leverage Scaling**: Higher confidence = higher leverage allowed (max 20x)
- **Volatility Adjustment**: Significantly reduced leverage w high volatility
- **Correlation Adjustment**: Reduced size dla correlated perpetual positions
- **Funding Rate Adjustment**: Position size based on expected funding costs

### Dynamic Liquidation Prevention System:
- **Liquidation Buffer**: Maintain minimum 25% buffer from liquidation price
- **Real-time Monitoring**: Continuous liquidation price tracking
- **Auto-Deleveraging Protection**: Prevent ADL through position management
- **Emergency Reduction**: Automatic position reduction near liquidation
- **Cross-Margin Optimization**: Use cross-margin efficiency dla safety
- **Funding Rate Hedging**: Hedge against adverse funding rate movements

### Advanced Leverage Risk Control:
- **Maximum Portfolio Leverage**: 10:1 average portfolio leverage limit
- **Dynamic Leverage Caps**: Adjust max leverage based on market conditions
- **Confidence-Based Leverage**: Higher signal confidence = higher leverage
- **Volatility-Adjusted Leverage**: Dramatic reduction during high volatility
- **Cross-Margin Monitoring**: Real-time total margin utilization tracking
- **Margin Safety Buffer**: Maintain 30%+ unused margin capacity

## Cross-Margin Portfolio Risk Management

### Perpetual Diversification Requirements:
- **Maximum Correlation**: No more than 60% correlation between perpetual positions
- **Market Category Limits**: Maximum exposure per perpetual category (crypto, FX, etc.)
- **Leverage Distribution**: Spread high-leverage positions across time
- **Strategy Diversification**: Multiple perpetual strategies deployment
- **Funding Rate Diversification**: Mix of positive/negative funding rate positions

### Perpetual Risk Limits and Controls:
- **Daily Loss Limit**: Maximum 3% cross-margin loss per day
- **Weekly Loss Limit**: Maximum 7% cross-margin loss per week
- **Monthly Loss Limit**: Maximum 12% cross-margin loss per month
- **Liquidation Proximity Limit**: Close positions approaching liquidation
- **Consecutive Loss Limit**: Stop after 3 consecutive liquidated positions
- **Funding Cost Limit**: Maximum 1% daily funding cost exposure

### Cross-Margin Correlation Management:
- **Real-time Correlation Monitoring**: Continuous perpetual correlation calculation
- **Leverage-Weighted Correlation**: Correlation weighted by position leverage
- **Funding Rate Correlation**: Monitor funding rate correlation patterns
- **Diversification Scoring**: Cross-margin diversification measurement
- **Risk Concentration Limits**: Avoid risk concentration w single factors
- **Dynamic Rebalancing**: Auto-adjustment dla correlation and margin efficiency

## Emergency Risk Procedures for Perpetuals

### Liquidation Emergency Triggers:
- **High Margin Utilization**: >85% cross-margin utilization
- **Approaching Liquidation**: Any position within 10% of liquidation
- **Extreme Volatility**: Perpetual market volatility > critical threshold
- **Funding Rate Shock**: Funding rate > 1% (annualized >365%)
- **Oracle Price Divergence**: Index vs mark price deviation > threshold
- **System Latency**: Liquidation monitoring latency > 100ms

### Emergency Response Procedures for Perpetuals:
- **Immediate Position Reduction**: Reduce positions within 30 seconds
- **Cross-Margin Optimization**: Reallocate margin dla maximum efficiency
- **Liquidation Assessment**: Evaluate all liquidation risks
- **Funding Cost Assessment**: Calculate immediate funding impact
- **System Diagnostics**: Check dYdX v4 connection and performance
- **Market Analysis**: Assess perpetual market conditions
- **Recovery Planning**: Plan dla safe position re-establishment

### Perpetual Risk Override Mechanisms:
- **Emergency Deleveraging**: Immediate leverage reduction across portfolio
- **Margin Call Response**: Automatic margin increase or position reduction
- **Funding Rate Hedging**: Immediate hedging dla funding rate exposure
- **Market Suspension**: Specific perpetual market suspension
- **Cross-Margin Rebalancing**: Emergency cross-margin optimization
- **System Maintenance Mode**: Safe shutdown preserving positions

## Real-time Perpetual Risk Monitoring

### Continuous Perpetual Risk Metrics:
- **Cross-Margin Utilization**: Real-time margin usage percentage
- **Portfolio Liquidation Distance**: Weighted average liquidation distance
- **Funding Rate Exposure**: Total funding cost per 8-hour period
- **Leverage Distribution**: Current leverage across all positions
- **Value at Risk (VaR)**: Daily VaR calculation including leverage
- **Expected Shortfall**: Tail risk measurement dla leveraged positions

### Perpetual Risk Alerting System:
- **Liquidation Warnings**: Multiple liquidation proximity thresholds
- **Margin Utilization Alerts**: Cross-margin usage warnings
- **Funding Rate Alerts**: Extreme funding rate notifications
- **Leverage Concentration Alerts**: High leverage clustering warnings
- **Correlation Alerts**: High perpetual correlation warnings
- **Performance Alerts**: Unusual perpetual trading patterns

### Perpetual Risk Dashboard Integration:
- **Real-time Liquidation Display**: Current liquidation distances
- **Cross-Margin Utilization**: Visual margin usage representation
- **Funding Rate Impact**: Real-time funding cost visualization
- **Position Leverage Breakdown**: Individual position leverage display
- **Portfolio Risk Summary**: Overall perpetual portfolio risk
- **Risk Trend Visualization**: Risk evolution over time dla perpetuals

## Adaptive Perpetual Risk Management

### Dynamic Risk Adjustment for Perpetuals:
- **Volatility-Based Adjustment**: Risk parameters adjust to perpetual volatility
- **Funding Rate Adjustment**: Risk based on current funding rate environment
- **Liquidity-Based Adjustment**: Risk based on perpetual market liquidity
- **Cross-Margin Efficiency**: Risk based on margin utilization efficiency
- **Time-Based Adjustment**: Risk based on funding rate cycles (8-hour periods)
- **Performance-Based Adjustment**: Risk based on recent liquidation history

### Machine Learning Risk Enhancement for Perpetuals:
- **Liquidation Prediction**: ML models dla liquidation probability
- **Funding Rate Prediction**: Forward-looking funding rate assessment
- **Volatility Clustering**: Perpetual volatility pattern recognition
- **Cross-Margin Optimization**: ML-based margin allocation optimization
- **Risk Pattern Recognition**: Historical perpetual risk pattern analysis
- **Stress Testing**: Scenario-based perpetual risk testing

## Performance vs Risk Optimization for Perpetuals

### Perpetual Risk-Adjusted Performance Targets:
- **Target Sharpe Ratio**: >2.0 minimum (higher dla leveraged trading)
- **Target Maximum Drawdown**: <10% acceptable dla perpetuals
- **Liquidation Avoidance**: 0% liquidation rate target
- **Target Win Rate**: >60% dla profitable leveraged operation
- **Funding-Adjusted Returns**: Target positive returns after funding costs
- **Target Leverage Efficiency**: Minimum 1.5x return improvement per 1x leverage

### Perpetual Risk Budget Allocation:
- **Strategy Risk Budgets**: Risk allocation per perpetual strategy
- **Market Risk Budgets**: Risk allocation per perpetual market
- **Leverage Risk Budgets**: Risk allocation across leverage levels
- **Funding Rate Risk Budgets**: Risk allocation dla funding rate exposure
- **Time Risk Budgets**: Risk allocation across funding rate cycles
- **Total Cross-Margin Budget**: Overall portfolio margin risk budget

## dYdX v4 Specific Risk Considerations

### Protocol-Specific Risk Management:
- **Node Reliability**: Monitor dYdX v4 node performance and failover
- **Rate Limiting**: Manage API rate limits dla risk monitoring
- **Protocol Upgrades**: Risk assessment dla dYdX v4 protocol changes
- **Governance Risk**: Monitor dYdX governance decisions affecting trading
- **Oracle Risk**: Monitor chainlink price feed reliability
- **Network Congestion**: Assess network congestion impact on trading

### Noble USDC Bridge Risk:
- **Bridge Delays**: Account dla Noble USDC deposit/withdrawal delays
- **Bridge Failures**: Risk management dla bridge unavailability
- **USDC Depeg Risk**: Monitor USDC price stability
- **Cross-Chain Risk**: Assess cross-chain bridge security risks

### Perpetual Market Structure Risk:
- **Funding Rate Manipulation**: Monitor dla unusual funding rate patterns
- **Market Making**: Assess impact of market maker presence/absence
- **Liquidation Cascades**: Monitor dla chain liquidation scenarios
- **ADL Risk**: Auto-deleveraging impact on positions
- **Insurance Fund**: Monitor dYdX v4 insurance fund health

## Compliance and Governance for Perpetuals

### Perpetual Risk Policy Enforcement:
- **Automated Liquidation Prevention**: Automatic rule enforcement
- **Exception Handling**: Emergency liquidation scenario management
- **Audit Trail**: Complete perpetual risk decision logging
- **Performance Review**: Regular leveraged trading risk assessment
- **Policy Updates**: Perpetual risk policy evolution

### DeFi Regulatory Considerations:
- **Leverage Limits**: Self-imposed leverage compliance
- **Position Reporting**: Internal position size documentation
- **Risk Disclosure**: Perpetual trading risk methodology transparency
- **Best Practices**: DeFi perpetual trading risk standards
- **Liquidation Documentation**: Complete liquidation event documentation
```
