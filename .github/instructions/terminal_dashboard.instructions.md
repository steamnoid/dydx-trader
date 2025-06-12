````instructions
// filepath: /Users/pico/Develop/github/steamnoid/injective-trader/.github/dydx_instructions/terminal_dashboard.instructions.md
# dYdX v4 Perpetual Trading Terminal Dashboard Implementation Instructions

## 🖥️ RICH-BASED PERPETUAL TRADING TERMINAL UI STRATEGY

### Design Philosophy: Margin-Aware, Liquidation Prevention Focused
**Goal**: Maximize perpetual trading information density with critical focus on margin monitoring and liquidation prevention. Every pixel serves real-time leveraged trading decision support.

## Perpetual Dashboard Layout Architecture

### Multi-Panel Layout Structure (dYdX v4 Optimized):
```
┌─────────────────────────────────────────────────────────────────────────┐
│ [HEADER] Portfolio: $X,XXX | Cross-Margin: XX% | Liquidation Risk: SAFE │
│          Funding Cost: $XXX/8h | Available Margin: $X,XXX | Leverage: Xx │
├─────────────────────────────────────────────────────────────────────────┤
│ [LEFT PANEL]          │ [CENTER PANEL]         │ [RIGHT PANEL]         │
│ Perpetual Scanner     │ Position Management    │ Risk Dashboard        │
│ - Funding Leaders     │ - Open Positions       │ - Liquidation Distance│
│ - Volatility Ranking  │ - Real-time P&L        │ - Margin Utilization  │
│ - Volume Leaders      │ - Liquidation Prices   │ - Funding Rate Risk   │
│ - Signal Alerts       │ - Leverage Per Position│ - Portfolio Health    │
│ - Market Overview     │ - Order Status         │ - Performance Metrics │
├─────────────────────────────────────────────────────────────────────────┤
│ [BOTTOM PANEL] Live Feed: Funding Updates, Margin Alerts, Trade Execution│
└─────────────────────────────────────────────────────────────────────────┤
│ [FOOTER] CPU: XX% | RAM: XXX MB | dYdX Latency: XX ms | Uptime: XXd XXh │
└─────────────────────────────────────────────────────────────────────────┘
```

### Perpetual-Specific Color Coding System:
- **Green**: Profits, positive funding, healthy margin, safe positions
- **Red**: Losses, negative funding, liquidation risk, critical alerts
- **Yellow**: Warning margin levels, funding rate changes, attention needed
- **Orange**: Approaching liquidation, margin calls, urgent action needed
- **Blue**: Information, system status, neutral market data
- **Purple**: High-leverage positions, critical funding alerts
- **Gray**: Inactive markets, disabled strategies, secondary information

## Real-time Perpetual Data Display Components

### Portfolio Overview Panel (Cross-Margin Focus):
- **Total Portfolio Value**: Large, prominent cross-margin display
- **Cross-Margin Utilization**: Real-time percentage with visual bar
- **Daily P&L**: Absolute and percentage change including funding costs
- **Funding P&L**: 8-hour funding payments/receipts tracking
- **Unrealized P&L**: Current perpetual position values (mark-to-market)
- **Realized P&L**: Closed perpetual position profits/losses
- **Available Margin**: For additional position sizing
- **Portfolio Leverage**: Current average portfolio leverage
- **Liquidation Distance**: Closest position to liquidation
- **Portfolio Performance Chart**: Mini chart with funding impact

### Perpetual Market Scanner Panel:
- **Active Perpetuals**: All perpetual markets being monitored
- **Funding Rates**: Current 8-hour funding rates with trends
- **Price Changes**: Real-time perpetual price movements
- **Volume Leaders**: Highest volume perpetual markets
- **Volatility Rankings**: Most volatile perpetual markets
- **Signal Strength**: Current signal scores per perpetual market
- **Funding Opportunities**: Best funding rate arbitrage opportunities
- **Market Status**: Trading status per perpetual market

### Position Management Panel (Margin-Aware):
- **Open Positions Table**: All current perpetual positions
  - Market/Symbol
  - Position Size & Leverage
  - Entry Price / Mark Price / Index Price
  - Unrealized P&L (USD + %)
  - Liquidation Price
  - Distance to Liquidation (%)
  - Margin Used
  - Funding Rate (current)
  - Duration / Next Funding
- **Position Risk Status**: Visual risk indicators per position
- **Cross-Margin Impact**: How each position affects total margin
- **Funding Cost Summary**: Total funding costs per position

### Risk Dashboard Panel (Liquidation Prevention):
- **Liquidation Risk Gauge**: Overall portfolio liquidation risk
- **Margin Utilization Meter**: Real-time cross-margin usage
- **Funding Rate Exposure**: Net funding rate position exposure
- **Portfolio Leverage Gauge**: Current vs maximum leverage
- **Risk Level Assessment**: Current portfolio risk level
- **Emergency Procedures**: Quick access to emergency controls
- **Performance Metrics**: Leverage-adjusted performance indicators
- **Correlation Risk**: Cross-position correlation risks

## Interactive Features for Perpetuals

### Keyboard Navigation (Margin-Aware):
- **Tab Navigation**: Move between panels
- **Arrow Keys**: Navigate within panels
- **Enter**: Select/activate items
- **Space**: Toggle strategy on/off
- **L**: Quick liquidation risk check
- **M**: Margin status overview
- **F**: Funding rate summary
- **ESC**: Emergency deleveraging
- **F1-F12**: Quick access to perpetual functions

### Real-time Updates (High-Frequency):
- **Streaming Data**: Continuous perpetual market updates
- **Margin Monitoring**: Real-time margin requirement updates
- **Liquidation Tracking**: Continuous liquidation price monitoring
- **Funding Rate Updates**: Real-time funding rate changes
- **Smart Updates**: Prioritize margin-critical data updates
- **Animation**: Smooth transitions dla margin changes
- **Priority Updates**: Liquidation alerts take absolute precedence

### Alert System (Liquidation-Focused):
- **Liquidation Warnings**: Multiple proximity alert levels
  - Green: >20% distance to liquidation
  - Yellow: 10-20% distance to liquidation
  - Orange: 5-10% distance to liquidation
  - Red: <5% distance to liquidation
- **Margin Alerts**: Cross-margin utilization warnings
- **Funding Rate Alerts**: Extreme funding rate notifications
- **Portfolio Risk Alerts**: Portfolio-wide risk warnings
- **Emergency Alerts**: Critical system alerts requiring immediate action
- **Audio Alerts**: Configurable sound notifications dla critical alerts

## Performance Optimization for Perpetuals

### UI Performance Requirements (Real-time Critical):
- **Refresh Rate**: 20 FPS minimum dla liquidation monitoring
- **Memory Usage**: <75MB dla entire perpetual UI
- **CPU Usage**: <8% dla UI rendering under high leverage
- **Latency**: <50ms from dYdX data to display (critical dla liquidation)
- **Responsiveness**: Immediate response to margin-critical user input
- **Stability**: Zero UI freezing during liquidation scenarios

### Perpetual Data Processing Optimization:
- **Incremental Updates**: Only update changed perpetual data
- **Margin Caching**: Cache frequently accessed margin calculations
- **Lazy Rendering**: Render only visible perpetual elements
- **Efficient Layouts**: Optimized rich layouts dla position tables
- **Memory Management**: Proper cleanup dla position objects
- **Threading**: Separate UI thread from margin calculations

### Display Optimization for High-Frequency Data:
- **Text Compression**: Efficient perpetual data representation
- **Color Optimization**: Efficient color usage dla risk indicators
- **Layout Caching**: Cache complex perpetual layouts
- **Redraw Optimization**: Minimize full redraws during margin updates
- **Double Buffering**: Smooth display updates dla rapid changes
- **Terminal Compatibility**: Work with various terminals under stress

## Advanced Perpetual UI Features

### Customizable Layouts (Trading-Focused):
- **Panel Sizing**: Adjustable panel sizes dla preferred risk monitoring
- **Panel Visibility**: Show/hide panels based on trading style
- **Custom Views**: User-defined layouts dla different strategies
- **Saved Configurations**: Multiple layout presets dla different market conditions
- **Context Switching**: Quick layout changes dla emergency scenarios
- **Responsive Design**: Adapt to terminal size maintaining critical info

### Perpetual Data Visualization:
- **Liquidation Distance Charts**: Visual distance to liquidation
- **Funding Rate Charts**: Historical and predicted funding rates
- **Margin Utilization Bars**: Visual cross-margin usage
- **Leverage Meters**: Real-time leverage gauges per position
- **Risk Heatmaps**: Portfolio risk visualization
- **Trend Indicators**: Funding rate and volatility trends
- **P&L Sparklines**: Performance charts including funding costs

### Information Density Optimization (Perpetual-Specific):
- **Data Compression**: Maximum perpetual info per screen space
- **Smart Formatting**: Context-appropriate number formatting dla margin data
- **Abbreviations**: Consistent perpetual trading abbreviation system
- **Hierarchical Display**: Expandable position details
- **Contextual Details**: Drill-down liquidation scenario analysis
- **Summary Views**: High-level cross-margin overview sections

## System Status Integration for dYdX v4

### Health Monitoring Display (dYdX-Specific):
- **dYdX Connection Status**: gRPC and WebSocket connection health
- **Node Status**: Current dYdX node performance and failover status
- **Data Flow**: Real-time perpetual data flow indicators
- **System Performance**: CPU, memory, latency metrics
- **API Rate Limits**: Current dYdX API usage and limits
- **Uptime**: System uptime with position preservation tracking

### Diagnostics Panel (Perpetual-Focused):
- **Performance Metrics**: Detailed perpetual trading performance data
- **Error Logs**: Recent dYdX-specific error messages
- **Debug Information**: Perpetual system debug data
- **Network Status**: dYdX network connectivity information
- **Resource Usage**: Detailed resource utilization dla margin monitoring
- **Configuration Status**: Current perpetual trading configuration validation

### Emergency Controls (Liquidation Prevention):
- **Emergency Deleveraging**: Immediate portfolio leverage reduction
- **Position Closure**: Quick position closure dla specific markets
- **Margin Management**: Emergency margin allocation adjustments
- **Strategy Controls**: Individual perpetual strategy enable/disable
- **Risk Override**: Emergency risk parameter changes
- **System Restart**: Safe system restart preserving positions
- **Maintenance Mode**: Safe maintenance state with position monitoring

## User Experience Design for Perpetuals

### Usability Principles (Margin-Aware):
- **Clarity**: Clear, unambiguous perpetual trading information display
- **Consistency**: Consistent UI patterns throughout perpetual interface
- **Efficiency**: Quick access to liquidation prevention functions
- **Feedback**: Immediate feedback dla margin-affecting user actions
- **Error Prevention**: Prevent user errors that could cause liquidation
- **Recovery**: Easy error recovery mechanisms preserving positions

### Accessibility Features (Trading-Focused):
- **High Contrast**: Support dla high contrast displays w trading environments
- **Large Text**: Configurable text sizes dla critical margin data
- **Color Blind Support**: Alternative color schemes dla risk indicators
- **Keyboard Only**: Full keyboard navigation dla rapid trading
- **Screen Reader**: Compatible with screen readers dla accessibility
- **Alternative Displays**: Support dla different terminal configurations

### Training and Documentation (Perpetual-Specific):
- **Help System**: Built-in help dla perpetual trading concepts
- **Tooltips**: Contextual help dla margin and liquidation information
- **Tutorials**: Interactive perpetual trading tutorials
- **Quick Reference**: Keyboard shortcut reference dla emergency actions
- **User Guide**: Comprehensive perpetual trading documentation
- **Video Guides**: Visual tutorial materials dla dYdX v4 features

## Integration with dYdX v4 Trading System

### Real-time Data Integration (dYdX-Specific):
- **Perpetual Market Data**: Direct feed from dYdX v4 market data layer
- **Funding Rate Data**: Real-time funding rate updates and calculations
- **Margin Data**: Cross-margin calculations and updates
- **Signal Data**: Real-time perpetual signal updates
- **Strategy Data**: Perpetual strategy performance and status
- **Risk Data**: Current margin risk metrics and liquidation alerts
- **Trading Data**: Perpetual position and order updates
- **System Data**: dYdX v4 performance and health metrics

### Control Integration (Perpetual-Focused):
- **Strategy Control**: Enable/disable perpetual strategies from UI
- **Risk Control**: Adjust margin and leverage parameters from UI
- **Position Control**: Manual perpetual position management
- **Margin Control**: Cross-margin allocation and optimization
- **Emergency Control**: Critical liquidation prevention functions
- **Configuration Control**: Real-time perpetual trading config changes

## dYdX v4 Specific Dashboard Features

### Noble USDC Integration Display:
- **Bridge Status**: Noble USDC bridge connection and status
- **Deposit/Withdrawal Queue**: Pending cross-chain transactions
- **Bridge Fees**: Current bridge costs and timing

### Protocol-Specific Monitoring:
- **Oracle Status**: Chainlink price feed health and accuracy
- **Governance Updates**: dYdX governance proposals affecting trading
- **Protocol Upgrades**: Network upgrade status and impact
- **Insurance Fund**: dYdX insurance fund health monitoring

### Advanced Perpetual Features:
- **Auto-Deleveraging Queue**: ADL queue position and risk
- **Market Making Status**: Market maker presence and liquidity
- **Funding Rate Prediction**: Predicted funding rates based on current conditions
- **Cross-Market Analysis**: Correlation analysis across perpetual markets
````
