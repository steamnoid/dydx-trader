```instructions
// filepath: /Users/pico/Develop/github/steamnoid/injective-trader/.github/dydx_instructions/trading_strategies.instructions.md
# dYdX v4 Perpetual Trading Strategies Instructions

## Protocol-First Development Philosophy
**Critical**: Follow dYdX v4 client nomenclature and patterns directly. Build strategy models ON-DEMAND when they provide clear value, not comprehensively upfront.

## Strategia Perpetual Trading (LEVERAGED MOMENTUM SNIPER)

### Główne Podejście: Funding-Aware Momentum Sniper Trading
**Philosophy**: Use dYdX v4 client data structures directly. Early momentum detection in perpetual markets with funding rate optimization and liquidation prevention using native protocol patterns.

### Priorytety Sygnałów dla dYdX v4 Perpetuals

#### Tier 1: Critical Perpetual Signals (Implementuj Pierwsze)
1. **Funding Rate Arbitrage Signals**
   - Funding rate discrepancies across timeframes
   - Predicted funding rate changes
   - Funding rate mean reversion
   - Cross-market funding rate analysis
   - Optimal entry timing dla funding cycle

2. **Leverage-Aware Orderbook Signals**
   - Bid/Ask ratio analysis with liquidation clustering
   - Large order detection with leverage impact
   - Liquidity gaps identification at critical levels
   - Price level concentration near liquidation zones
   - Market maker behavior around margin calls

3. **Perpetual Volume Surge Detection**
   - Abnormal volume spikes w perpetual markets
   - Volume profile analysis with leverage weighting
   - Volume-price correlation in leveraged environment
   - Accumulation/distribution patterns w perpetuals
   - Liquidation cascade volume detection

4. **Margin-Aware Price Momentum Signals**
   - Breakout detection with margin expansion capability
   - Trend strength measurement considering leverage
   - Support/resistance levels weighted by liquidations
   - Price velocity analysis with funding cost impact
   - Momentum sustainability w leveraged environment

#### Tier 2: Advanced Perpetual Signals
5. **Cross-Perpetual Market Analysis**
   - Price discrepancies between perpetual markets
   - Correlation analysis across perpetual pairs
   - Lead-lag relationships in leveraged markets
   - Market coupling strength during volatile periods
   - Arbitrage opportunities between perpetuals

6. **Volatility Signals (Leverage-Adjusted)**
   - Volatility expansion/contraction with leverage impact
   - ATR-based signals adjusted dla funding costs
   - Volatility clustering in perpetual environment
   - Implied volatility from funding rates
   - Liquidation-driven volatility patterns

7. **Perpetual Market Microstructure**
   - Trade size analysis with leverage distribution
   - Order flow imbalance considering margin requirements
   - Market maker behavior during funding periods
   - Smart money detection in leveraged positions
   - Liquidation event pattern recognition

#### Tier 3: Innovation Perpetual Signals
8. **Machine Learning Signals (Perpetual-Focused)**
   - Funding rate prediction models
   - Liquidation cascade prediction
   - Optimal leverage level determination
   - Cross-margin efficiency optimization
   - Pattern recognition dla leveraged market behavior

9. **dYdX v4 Protocol Analysis**
   - Insurance fund health monitoring
   - ADL (Auto-Deleveraging) queue analysis
   - Oracle price feed reliability signals
   - Node performance impact on trading
   - Governance decision impact assessment

## Funding Rate Strategy Framework

### Funding Rate Optimization:
- **Funding Cycle Timing**: Optimal entry/exit around 8-hour cycles
- **Rate Prediction**: Machine learning dla funding rate forecasting
- **Cross-Market Arbitrage**: Exploit funding rate differences
- **Long-term Positioning**: Strategies dla sustained funding collection
- **Risk Management**: Hedge against adverse funding movements

### Funding-Aware Position Management:
- **Cost-Benefit Analysis**: Trading decisions including funding costs
- **Time Decay Management**: Position timing considering funding
- **Rate Change Adaptation**: Dynamic strategy adjustment
- **Funding Budget**: Allocate budget dla funding payments
- **Exit Strategy**: Funding-optimized position closure

## Leverage Strategy Implementation

### Dynamic Leverage Management:
- **Signal Confidence Scaling**: Higher confidence = higher leverage allowed
- **Market Volatility Adjustment**: Reduce leverage during high volatility
- **Funding Rate Consideration**: Adjust leverage based on funding costs
- **Cross-Margin Optimization**: Maximize margin efficiency across positions
- **Liquidation Distance Maintenance**: Ensure safe distance from liquidation

### Leverage Risk Framework:
- **Maximum Leverage Caps**: Hard limits based on market conditions
- **Progressive Leverage**: Gradually increase leverage with performance
- **Emergency Deleveraging**: Automatic leverage reduction triggers
- **Portfolio Leverage**: Overall portfolio leverage coordination
- **Stress Testing**: Leverage performance under extreme scenarios

## Perpetual Signal Processing Framework

### Real-time Perpetual Signal Generation:
- **Sliding Window Analysis**: Configurable time windows dla perpetual data
- **Multi-timeframe Coordination**: 1m, 5m, 15m, 1h, 8h (funding) coordination
- **Funding-Adjusted Signals**: Signals adjusted dla funding rate impact
- **Leverage-Weighted Aggregation**: Position size weighted signal combination
- **Margin-Aware Filtering**: Filter signals based on margin requirements

### Perpetual Signal Quality Control:
- **Funding Rate Validation**: Verify funding rate calculation accuracy
- **Liquidation Impact Assessment**: Evaluate signal impact on liquidation risk
- **Cross-Margin Compatibility**: Ensure signals work with cross-margin system
- **Performance Tracking**: Track signal performance including funding costs
- **Adaptive Thresholds**: Dynamic calibration dla perpetual environment

## Strategy Implementation Patterns dla Perpetuals

### Perpetual Strategy Selection Framework:
- **Market Regime Detection**: Bull/bear/sideways w leveraged context
- **Volatility Adaptation**: Strategy selection considering liquidation risk
- **Liquidity Assessment**: Strategy suitability dla perpetual market depth
- **Funding Environment**: Strategy selection based on funding rate regime
- **Cross-Margin Efficiency**: Strategy coordination dla margin optimization

### Perpetual Position Management:
- **Entry Logic**: Multi-signal confirmation including funding timing
- **Leverage Sizing**: Kelly criterion adapted dla leveraged perpetuals
- **Exit Logic**: Profit taking considering funding costs and liquidation risk
- **Cross-Position Coordination**: Manage correlation and margin efficiency
- **Dynamic Risk Scaling**: Position sizing based on margin utilization

## Advanced Perpetual Trading Strategies

### Strategy 1: Funding Rate Momentum
- **Concept**: Trade momentum while collecting/avoiding funding payments
- **Entry**: Strong momentum + favorable funding rate positioning
- **Management**: Hold through funding periods when profitable
- **Exit**: Momentum exhaustion or adverse funding rate changes

### Strategy 2: Liquidation Zone Contrarian
- **Concept**: Contrarian trades around major liquidation clusters
- **Entry**: Identify liquidation clusters and trade opposite direction
- **Management**: Quick profits from liquidation-driven overshoots
- **Exit**: Rapid exit after liquidation cascade completion

### Strategy 3: Cross-Margin Arbitrage
- **Concept**: Exploit margin efficiency differences across positions
- **Entry**: Identify margin-inefficient positions in portfolio
- **Management**: Rebalance dla optimal cross-margin utilization
- **Exit**: When margin efficiency is optimized

### Strategy 4: Funding Rate Mean Reversion
- **Concept**: Trade mean reversion of extreme funding rates
- **Entry**: Funding rates at historical extremes
- **Management**: Hold positions expecting funding normalization
- **Exit**: Funding rates return to historical means

### Strategy 5: Volatility Breakout w/ Leverage Scaling
- **Concept**: Breakout trading with dynamic leverage adjustment
- **Entry**: Confirmed breakouts with volume confirmation
- **Management**: Scale leverage based on volatility and momentum
- **Exit**: Volatility contraction or momentum failure

## Performance Optimization dla Perpetuals

### Signal Processing Performance (Margin-Critical):
- **Vectorized Calculations**: NumPy dla bulk funding rate calculations
- **Incremental Updates**: Avoid full margin recalculation
- **Parallel Processing**: Multi-threaded perpetual signal generation
- **Memory Efficiency**: Minimal data copying dla position tracking
- **Cache Optimization**: Cache frequent margin calculations

### Strategy Performance (Liquidation-Aware):
- **Hot Path Optimization**: Critical path optimization dla margin monitoring
- **Decision Speed**: <50ms strategy decisions dla liquidation prevention
- **Memory Footprint**: Minimal strategy state dla position tracking
- **CPU Efficiency**: Optimized algorithms dla real-time margin calculations
- **Resource Monitoring**: Real-time performance tracking under leverage

## Innovation Areas dla Competitive Advantage

### Unique Perpetual Signal Development:
- **Funding Rate Micropatterns**: Novel funding rate pattern recognition
- **Cross-Perpetual Signals**: Multi-market perpetual coordination
- **Liquidation Cascade Prediction**: Advanced liquidation event forecasting
- **Oracle Price Analysis**: Index vs mark price divergence signals
- **Cross-Margin Optimization**: Dynamic margin allocation signals

### Adaptive Perpetual Intelligence:
- **Funding Rate Learning**: Self-improving funding rate prediction
- **Leverage Optimization**: Real-time leverage level optimization
- **Margin Efficiency**: Automated cross-margin optimization
- **Risk Adaptation**: Dynamic risk parameter adjustment
- **Performance Feedback**: Closed-loop learning including funding costs

## Risk-Adjusted Strategy Design dla Perpetuals

### Perpetual Risk Metrics Integration:
- **Funding-Adjusted Sharpe**: Risk-adjusted returns including funding costs
- **Liquidation-Aware Drawdown**: Maximum drawdown considering liquidation risk
- **Margin VaR**: Value at Risk considering cross-margin requirements
- **Leverage Correlation**: Portfolio correlation under different leverage
- **Tail Risk Protection**: Black swan protection dla leveraged positions

### Perpetual Strategy Diversification:
- **Funding Strategy Mix**: Long/short funding rate strategies
- **Leverage Diversification**: Different leverage levels across strategies
- **Time Horizon Mix**: Different holding periods considering funding cycles
- **Market Condition Adaptation**: Strategies dla volatile vs stable periods
- **Cross-Margin Strategies**: Strategies optimizing total margin efficiency

## Autonomous Perpetual Strategy Management

### Self-Monitoring dla Perpetuals:
- **Strategy Health Checks**: Monitor including funding rate impact
- **Liquidation Risk Detection**: Early warning dla liquidation approach
- **Funding Cost Monitoring**: Track actual vs expected funding costs
- **Margin Efficiency Tracking**: Monitor cross-margin optimization
- **Emergency Procedures**: Critical situation handling preserving positions

### Continuous Improvement dla Perpetuals:
- **Funding Rate A/B Testing**: Test different funding strategies
- **Leverage Optimization**: Continuous leverage level optimization
- **Margin Efficiency Analytics**: Deep analysis of cross-margin usage
- **Liquidation Prevention**: Improve liquidation avoidance algorithms
- **Innovation Pipeline**: New perpetual strategy development and testing

## dYdX v4 Specific Considerations

### Protocol Integration:
- **Noble USDC Optimization**: Timing strategies around bridge delays
- **Oracle Price Monitoring**: Strategies based on price feed reliability
- **Governance Awareness**: Adapt strategies based on protocol changes
- **Insurance Fund Health**: Strategy adjustment based on fund status

### Network Optimization:
- **Node Performance**: Route orders based on node performance
- **Gas Optimization**: Minimize transaction costs w strategy execution
- **Rate Limit Management**: Optimize API usage within limits
- **Failover Strategies**: Strategy continuity during node failures

### Advanced dYdX v4 Features:
- **ADL Queue Management**: Strategies considering auto-deleveraging risk
- **Market Making Integration**: Strategies considering market maker presence
- **Cross-Chain Timing**: Strategies optimized dla cross-chain operations
- **Protocol Upgrade Adaptation**: Strategy evolution with protocol changes
```
