# REACTIVE PROGRAMMING METHODOLOGY - RxPY Testing Patterns

## METHODOLOGY PURPOSE
**Universal patterns for Test-Driven Development with reactive programming**
**Validated through: RxPY Observable streams in dYdX project**

## REACTIVE PROGRAMMING CHALLENGES FOR TDD

### Core Testing Problems
1. **Timing**: Observable streams emit over time
2. **Asynchronous**: Events happen on different threads
3. **Stateful**: Streams maintain internal state
4. **Composition**: Multiple streams combine in complex ways
5. **Error Handling**: Failures can occur at any point

### Traditional TDD Limitations
- Regular assertions don't work with time-based emissions
- Simple input/output testing insufficient for streams
- Mock objects don't capture reactive behavior properly
- Test isolation difficult with persistent streams

## UNIVERSAL RXPY TESTING METHODOLOGY

### Core Testing Infrastructure
```python
# Pattern: TestScheduler for deterministic timing
from reactivex.testing import TestScheduler, marbles

def test_observable_with_scheduler():
    scheduler = TestScheduler()
    
    # Create observable with predictable timing
    source = scheduler.create_hot_observable(
        marbles("a-b-c|")
    )
    
    # Test the stream behavior
    result = scheduler.create_observer()
    source.subscribe(result)
    scheduler.start()
    
    # Assert on the message sequence
    assert result.messages == expected_messages
```

### Marble Testing Pattern
```python
# Pattern: Visual stream testing with marble diagrams
def test_stream_transformation():
    scheduler = TestScheduler()
    
    # Input stream: a-b-c|
    source = scheduler.create_hot_observable("a-b-c|")
    
    # Apply transformation
    result_stream = source.pipe(
        map(lambda x: x.upper())
    )
    
    # Expected output: A-B-C|
    expected = scheduler.create_hot_observable("A-B-C|")
    
    # Verify streams match
    assert_streams_equal(result_stream, expected)
```

### Stream Isolation Pattern
```python
# Pattern: Isolated stream testing with controlled sources
def test_signal_calculation():
    # Create controlled data source
    test_data = [
        {"price": 100, "timestamp": 1000},
        {"price": 105, "timestamp": 2000},
        {"price": 102, "timestamp": 3000}
    ]
    
    # Create Observable from test data
    source = Observable.from_iterable(test_data)
    
    # Test the signal calculation
    result_values = []
    source.pipe(
        signal_calculation_operator()
    ).subscribe(result_values.append)
    
    # Verify results
    assert len(result_values) == 3
    assert result_values[0].score == expected_score
```

## STRICT TDD WITH REACTIVE STREAMS

### Step 1: Write ONE Test for Observable Creation
```python
def test_can_create_market_data_stream():
    client = ReactiveClient()
    stream = client.get_market_data_stream()
    assert isinstance(stream, Observable)
```

### Step 2: Write Minimal Code to Pass
```python
def get_market_data_stream(self) -> Observable:
    return Observable.empty()  # Minimal implementation
```

### Step 3: Test Observable Emission
```python
def test_stream_emits_market_data():
    scheduler = TestScheduler()
    client = ReactiveClient()
    
    stream = client.get_market_data_stream()
    result = scheduler.create_observer()
    stream.subscribe(result)
    
    # Trigger emission somehow
    client.emit_test_data({"price": 100})
    
    scheduler.start()
    assert len(result.messages) == 1
    assert result.messages[0].value == {"price": 100}
```

### Step 4: Extend Implementation Minimally
```python
def get_market_data_stream(self) -> Observable:
    def on_subscribe(observer, scheduler):
        # Store observer for later emission
        self._observer = observer
        return lambda: None  # Disposal
    
    return Observable.create(on_subscribe)

def emit_test_data(self, data):
    if hasattr(self, '_observer'):
        self._observer.on_next(data)
```

## REACTIVE OPERATOR TESTING METHODOLOGY

### Testing Stream Transformations
```python
def test_price_filter_operator():
    scheduler = TestScheduler()
    
    # Input: prices with some below threshold
    input_data = [
        {"price": 50},   # Below threshold
        {"price": 150},  # Above threshold
        {"price": 75},   # Below threshold
        {"price": 200}   # Above threshold
    ]
    
    source = Observable.from_iterable(input_data)
    
    # Apply filter
    result_values = []
    source.pipe(
        filter(lambda x: x["price"] > 100)
    ).subscribe(result_values.append)
    
    # Should only have prices > 100
    assert len(result_values) == 2
    assert result_values[0]["price"] == 150
    assert result_values[1]["price"] == 200
```

### Testing Stream Combinations
```python
def test_combine_market_streams():
    scheduler = TestScheduler()
    
    price_stream = scheduler.create_hot_observable("a-b-c|")
    volume_stream = scheduler.create_hot_observable("x-y-z|")
    
    combined = price_stream.pipe(
        combine_latest(volume_stream),
        map(lambda pair: {"price": pair[0], "volume": pair[1]})
    )
    
    result = scheduler.create_observer()
    combined.subscribe(result)
    scheduler.start()
    
    # Verify combination logic
    assert len(result.messages) > 0
```

## ERROR HANDLING TESTING METHODOLOGY

### Testing Stream Error Recovery
```python
def test_connection_error_recovery():
    scheduler = TestScheduler()
    
    # Stream that errors then recovers
    source = scheduler.create_hot_observable("a-b-#")  # # = error
    
    # Apply error recovery
    recovered = source.pipe(
        catch(lambda error, source: Observable.just({"status": "fallback"}))
    )
    
    result = scheduler.create_observer()
    recovered.subscribe(result)
    scheduler.start()
    
    # Should get fallback data after error
    fallback_message = result.messages[-1]
    assert fallback_message.value == {"status": "fallback"}
```

## PERFORMANCE TESTING WITH REACTIVE STREAMS

### Latency Testing Pattern
```python
def test_stream_processing_latency():
    import time
    
    start_time = time.time()
    result_count = 0
    
    def on_result(value):
        nonlocal result_count, start_time
        result_count += 1
        if result_count == 1000:  # After 1000 messages
            elapsed = time.time() - start_time
            assert elapsed < 1.0  # Must process 1000 messages in <1 second
    
    # Create high-frequency stream
    source = create_high_frequency_stream()
    source.subscribe(on_result)
    
    # Let it run
    time.sleep(2)
```

## METHODOLOGY VALIDATION CHECKLIST

### Before Testing Reactive Component
- [ ] Set up TestScheduler for deterministic timing
- [ ] Choose marble testing or observer pattern
- [ ] Plan for stream isolation and mocking
- [ ] Define clear success criteria for stream behavior

### During Reactive TDD
- [ ] One test function at a time
- [ ] Focus on stream behavior, not just final values
- [ ] Test error cases and recovery
- [ ] Verify timing and sequence requirements

### After Reactive Component
- [ ] Validate performance under realistic load
- [ ] Test integration with other streams
- [ ] Document patterns for reuse
- [ ] Update methodology based on experience

## UNIVERSAL APPLICABILITY

### Technology-Agnostic Patterns
- TestScheduler concept for deterministic timing
- Stream isolation for predictable testing
- Error recovery testing patterns
- Performance validation approaches

### RxPY-Specific Elements
- Marble testing syntax
- Observable creation patterns
- Operator testing methods
- Scheduler implementation details

This methodology should work with any reactive programming library.
