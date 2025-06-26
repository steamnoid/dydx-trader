# PROJECT CONTEXT - dYdX v4 Trading Bot

## PROJECT PURPOSE IN METHODOLOGY DEVELOPMENT
**This project serves as our test case for validating universal development methodology**
**Success = methodology works, not necessarily complete trading bot**

## PROJECT SCOPE FOR METHODOLOGY TESTING

### Core Technical Challenges (Good for Methodology Testing)
- **Reactive Programming**: RxPY Observable streams
- **Real-time Data**: WebSocket connections and streaming
- **Test-Driven Development**: Complex algorithms and calculations
- **UI Components**: Rich terminal interfaces
- **Integration Testing**: Multiple layers and external APIs
- **Performance Requirements**: Sub-second latency constraints

### Business Context (Secondary to Methodology)
- dYdX v4 perpetual futures trading
- Autonomous operation without human intervention
- Liquidation prevention and risk management
- Multi-market strategy implementation

## TECHNICAL STACK (For Methodology Validation)

### Core Technologies
- **Language**: Python 3.11+
- **Reactive Programming**: RxPY (reactivex) - tests streaming methodology
- **Client Library**: dydx-v4-client - tests protocol-first approach
- **Stream Recording**: mitmproxy - HTTP/WebSocket proxy for recording and replay
- **Testing**: pytest - validates TDD methodology
- **UI**: Rich library - tests build-first UI methodology

### Architecture Layers (Stream-Based Methodology Test Cases)
```
Layer 2: Real Data Streams + Recording - Tests reactive TDD with real APIs
  - dYdX v4 OHLCV data as RxPY Observable streams
  - Stream recording mechanism for deterministic replay
  - Tests: Real API integration, stream isolation, record/replay

Layer 3+: Replayed Stream Processing - Tests deterministic stream testing
  - All higher layers use ONLY replayed streams as input
  - No direct API calls above Layer 2
  - Tests: Stream-based assertions, deterministic behavior
  
Layer 4: Data Processing - Tests streaming transformations
Layer 5: Signal Scoring - Tests complex stream calculations  
Layer 6: Strategy - Tests multi-stream reactive methodology
Layer 7+: Risk, Trading, Dashboard - Tests integration methodology
```

## PERFORMANCE TARGETS (Methodology Validation)
- **Memory**: <512MB sustained - tests resource management methodology
- **CPU**: <25% single core - tests efficiency methodology
- **Latency**: <25ms critical calculations - tests performance methodology
- **Coverage**: 95%+ per layer - tests TDD methodology effectiveness

## DOMAIN-SPECIFIC REQUIREMENTS

### dYdX v4 Integration Points
- **IndexerSocket**: Real-time WebSocket data
- **IndexerClient**: REST API queries
- **NodeClient**: Blockchain operations
- **Wallet**: Authentication and signing

### Trading-Specific Constraints
- **Perpetual Futures**: Only supported product type
- **Cross-Margin**: dYdX v4 margin system
- **Funding Rates**: 8-hour cycle considerations
- **Liquidation Prevention**: Primary risk management focus

## METHODOLOGY VALIDATION THROUGH PROJECT

### What This Project Tests
1. **Stream-Based TDD**: Can we build reactive systems with recorded/replayed streams?
2. **Real API Integration**: Does Layer 2 recording work with actual dYdX data?
3. **Deterministic Testing**: Do replayed streams enable reliable higher-layer testing?
4. **UI Methodology**: Does build-first work for Rich console interfaces?
5. **Chaos Prevention**: Can systematic approach handle stream-based integration?
6. **Universal Applicability**: Are stream patterns reusable beyond trading?

### What This Project Doesn't Need
- Complete trading bot functionality
- Production-ready autonomous operation
- Full market coverage or strategies
- Business optimization or profitability

## SUCCESS CRITERIA FOR METHODOLOGY

### Primary Success (Methodology Works)
- TDD produces working reactive components
- Build-first creates functional UI panels
- Chaos prevention maintains code quality
- Performance targets are met with methodology
- Instructions are clear and followable

### Secondary Success (Project Works)
- Basic trading bot functionality demonstrated
- Real dYdX API integration working
- Observable streams processing market data
- Dashboard showing real-time information

## METHODOLOGY LEARNING OPPORTUNITIES

### Expected Challenges
1. **Stream Recording**: Finding/implementing reliable HTTP/stream recording for RxPY
2. **Deterministic Replay**: Maintaining timing and data fidelity in replayed streams
3. **Stream-Based Testing**: Asserting on continuous data flows vs. discrete outputs
4. **Integration**: Connecting recorded Layer 2 with higher layer stream processing
5. **Performance**: Meeting latency targets with recorded/replayed stream approach

### Learning Documentation
- Track where methodology works well
- Document where approaches break down
- Identify universal patterns that emerge
- Note project-specific vs. universal elements

## ITERATION DECISION CRITERIA

### Continue Current Iteration If:
- Methodology is being validated effectively
- Learning is occurring about approach effectiveness
- Forward progress on methodology development
- Clear path to universal applicability

### Start Fresh If:
- Methodology isn't being tested properly
- Stuck on project specifics vs. methodology
- No clear learning about universal patterns
- Approach fundamentally not working

## PROJECT BOUNDARIES FOR METHODOLOGY FOCUS

### In Scope (Methodology Relevant)
- Core reactive programming patterns
- TDD for algorithmic components
- UI testing methodologies
- Integration testing approaches
- Performance validation under methodology

### Out of Scope (Project-Specific)
- Complete trading strategy implementation
- Business logic optimization
- Production deployment concerns
- Advanced trading features
- Market analysis algorithms

This project exists to prove our methodology works on complex, real-world challenges.

## STREAM-BASED TESTING METHODOLOGY

### Layer 2: Real API + Recording (One-Time Recording)
- **Purpose**: Capture real dYdX OHLCV data as Observable streams
- **Recording**: Store stream data for deterministic replay
- **Testing**: Validate real API integration and recording mechanism
- **Output**: Recorded stream files for higher layer consumption

### Layer 3+: Replayed Stream Testing (Deterministic)
- **Input**: ONLY replayed streams from Layer 2 recordings
- **Testing**: All assertions based on stream data, not isolated units
- **Benefits**: Deterministic behavior, fast execution, no API dependencies
- **Pattern**: Stream-in → Stream-out → Assert on stream data

### Stream Testing Requirements
```python
# Example: All higher layer tests follow this pattern
def test_data_processing_stream():
    # Use replayed stream as input
    replayed_stream = load_recorded_stream("ohlcv_sample.json")
    
    # Process through component
    result_stream = data_processor.process(replayed_stream)
    
    # Assert on stream output
    result_values = collect_stream_values(result_stream)
    assert len(result_values) == expected_count
    assert result_values[0].price > 0
```

### Recording/Replay Implementation Goals
- **Proxy Solution**: mitmproxy as HTTP/WebSocket proxy between dYdX client and API
- **Recording Mode**: Capture all HTTP requests and WebSocket messages to files
- **Replay Mode**: Serve recorded responses without hitting real API
- **Integration**: Embed mitmproxy in Layer 2 for seamless recording/replay
