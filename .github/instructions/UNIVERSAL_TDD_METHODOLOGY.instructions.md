# UNIVERSAL TDD METHODOLOGY - Core Development Approach

## METHODOLOGY PURPOSE
**Universal Test-Driven Development approach for complex technical projects**
**Validated through: dYdX v4 Trading Bot implementation**

## CORE TDD PRINCIPLES - UNIVERSALLY APPLICABLE

### STRICT TDD RULES (Non-Negotiable)
1. **Write ONLY ONE test function at a time**
2. **RUN TEST immediately** - Must see RED (failing)
3. **Write ONLY minimal code** - Just enough to pass that ONE test
4. **RUN TEST immediately** - Must see GREEN (passing)
5. **Refactor ONLY if necessary** - Minimal improvements only
6. **RUN TEST immediately** - Must stay GREEN after refactor
7. **REPEAT** - Next single test function

### CRITICAL ENFORCEMENT RULES
- ❌ NO multiple files simultaneously
- ❌ NO comprehensive implementations before tests
- ❌ NO skipping test runs
- ❌ NO taking shortcuts
- ✅ MUST follow Red→Green→Refactor with test validation

## COMPONENT TYPE METHODOLOGY SELECTION

### Core Business Logic: STRICT TDD-FIRST
**When to use**: Engines, calculators, algorithms, data processors
**Characteristics**: Predictable I/O, performance-critical, complex calculations
**Process**: STRICT TDD - no exceptions

**Benefits**:
- Predictable inputs/outputs enable clear test cases
- Performance requirements demand robust validation
- Complex algorithms need comprehensive test coverage

### UI/Display Components: BUILD-FIRST
**When to use**: Panels, dashboards, visual components, console output
**Characteristics**: Unpredictable formatting, visual feedback essential
**Process**: Build working component first, then create tests based on reality

**Benefits**:
- Visual output patterns hard to predict beforehand
- Need to see actual behavior to write accurate tests
- Tests validate what actually exists, not assumptions

## STREAM-BASED TDD EXTENSIONS

### Layer 2: Real API Components (TDD + Recording)
**When to use**: API connection layers, real-time data sources
**Characteristics**: External dependencies, real network calls, recording capability
**Process**: TDD for connection logic + recording integration testing

**Example TDD Cycle**:
1. Test: Can create API client
2. Code: Empty client class  
3. Test: Can get stream from API
4. Code: Return empty Observable
5. Test: Can record stream data
6. Code: Add recording mechanism

### Layer 3+: Stream Processing Components (TDD + Replay)
**When to use**: Data transformation, analysis, business logic on streams
**Characteristics**: Stream input/output, deterministic behavior, no external calls
**Process**: STRICT TDD with replayed streams as test data

**Example TDD Cycle**:
1. Test: Can process replayed stream
2. Code: Return empty stream
3. Test: Calculates correct transformation
4. Code: Add minimal transformation logic
5. Test: Handles edge cases in stream
6. Code: Add error handling

### TDD Testing Requirements
```python
# Pattern: Single test function with clear validation
def test_single_functionality():
    # Arrange
    input_data = create_test_input()
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output
```

### Build-First Testing Requirements
```python
# Pattern: Capture actual output, then validate
def test_ui_component_output():
    component = create_component()
    actual_output = capture_component_output(component)
    
    # Validate based on actual patterns observed
    assert expected_pattern in actual_output
```

### Stream Testing Requirements
```python
# Layer 2: Integration testing with recording
def test_api_stream_integration():
    client = ApiClient()
    recorder = StreamRecorder("integration_test.json")
    
    stream = client.get_data_stream()
    recorded_stream = recorder.record_stream(stream)
    
    # Test real integration
    values = []
    recorded_stream.take(5).subscribe(values.append)
    
    assert len(values) > 0
    recorder.save_recording()

# Layer 3+: Unit testing with replay
def test_stream_transformation():
    # Use recorded data as input
    replayer = StreamReplayer("test_data.json")
    input_stream = replayer.replay_stream()
    
    # Test transformation
    result_stream = transform_stream(input_stream)
    
    # Assert on stream output
    results = []
    result_stream.subscribe(results.append)
    assert len(results) == expected_count
```

## FUNCTION COMPLETION DISCIPLINE

### CRITICAL RULE: ONE FUNCTION TO COMPLETION
**Complete each function FULLY before starting the next one**

#### Wrong Approach (What NOT to do):
```python
# ❌ BAD: Adding multiple incomplete functions
def start_recording():
    pass  # Empty implementation

def stop_recording():
    pass  # Empty implementation

def is_recording():
    pass  # Empty implementation
```

#### Correct Approach (What TO do):
```python
# ✅ GOOD: Complete start_recording() FULLY first
def start_recording():
    # Actually starts mitmproxy
    # Actually records HTTP calls
    # Actually verifies recording works
    # Returns meaningful status
    
# ONLY add stop_recording() after start_recording() is COMPLETE
```

### FUNCTION COMPLETION CHECKLIST

Before moving to next function:
- [ ] Does the function actually DO what its name says?
- [ ] Can I prove it works with a test that uses real data?
- [ ] Does it handle basic error cases?
- [ ] Would another developer understand how to use it?

### TDD FUNCTION DISCIPLINE

#### Step 1: Test Function Exists
```python
def test_has_start_recording_method():
    assert hasattr(client, 'start_recording')
```

#### Step 2: Test Function Actually Works
```python
def test_start_recording_actually_records():
    client.start_recording()
    # Make HTTP call
    recorded_data = client.get_recorded_data()
    assert len(recorded_data) > 0  # Prove it recorded something
```

#### Step 3: Test Function Handles Errors
```python
def test_start_recording_handles_port_conflict():
    # Test what happens when port is busy
    result = client.start_recording()
    assert result.success == False
    assert "port" in result.error_message
```

#### Step 4: ONLY THEN move to next function

### AVOID FUNCTION JUMPING ANTI-PATTERNS

#### ❌ Method Collector Pattern
Adding many empty methods without implementing any:
```python
def start_recording(): pass
def stop_recording(): pass
def get_status(): pass
def restart(): pass
```

#### ❌ Happy Path Only Pattern
Only testing that methods exist, not that they work:
```python
def test_has_all_methods():
    assert hasattr(client, 'start_recording')
    assert hasattr(client, 'stop_recording')  # But do they work?
```

#### ❌ Integration Before Unit Pattern
Testing complex interactions before basic functionality works:
```python
def test_full_workflow():
    client.start_recording()
    client.make_api_call()
    client.stop_recording()
    # What if start_recording() doesn't actually work?
```

### METHODOLOGY ENFORCEMENT

#### Before Writing ANY Test
- [ ] What ONE function am I completing?
- [ ] What does "working" mean for this function?
- [ ] How will I prove it actually works?

#### Before Moving to Next Function
- [ ] Can I demonstrate this function works with real data?
- [ ] Would I trust this function in production?
- [ ] Does it do everything its name promises?

#### Red Flag Questions
- Am I adding methods faster than I'm completing them?
- Am I testing method existence instead of method functionality?
- Am I assuming methods work without proving it?

**PRINCIPLE: One function, fully working, before touching another function.**

## METHODOLOGY VALIDATION CHECKLIST

### Before Starting Any Component
- [ ] Identify component type (core logic vs. UI)
- [ ] Choose appropriate methodology (TDD vs. Build-First)
- [ ] Set up proper testing infrastructure
- [ ] Define clear success criteria

### During Development
- [ ] Follow chosen methodology strictly
- [ ] Document deviations and learnings
- [ ] Validate methodology effectiveness
- [ ] Update instructions based on experience

### After Component Completion
- [ ] Assess methodology success
- [ ] Document lessons learned
- [ ] Update universal patterns
- [ ] Prepare for next component

## ITERATION LEARNING FRAMEWORK

### What to Track
1. **Methodology Adherence**: Did we follow the approach?
2. **Effectiveness**: Did it produce quality results?
3. **Efficiency**: Was development speed acceptable?
4. **Pain Points**: What was difficult or unclear?
5. **Improvements**: How can methodology be enhanced?

### Documentation Requirements
- Record actual experience vs. planned approach
- Note where methodology broke down
- Identify universal patterns that emerged
- Update instructions based on real learnings

## UNIVERSAL APPLICABILITY PRINCIPLES

### Project-Agnostic Elements
- TDD Red→Green→Refactor cycle
- Component type classification
- Testing pattern selection
- Iteration learning framework

### Project-Specific Elements (Separate)
- Technology stack choices
- Domain-specific requirements
- Performance targets
- Business logic details

## METHODOLOGY SUCCESS METRICS
- **Consistency**: Same approach works across different components
- **Quality**: High test coverage and working code
- **Speed**: Efficient development without chaos
- **Clarity**: Instructions can be followed by others
- **Universality**: Applicable beyond current project
