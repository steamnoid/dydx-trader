# CHAOS PREVENTION METHODOLOGY - Universal Principles

## CORE PRINCIPLE
**ONE PROBLEM, ONE FILE, ONE FIX**
**Systematic approach to prevent development chaos**

## UNIVERSAL CHAOS PATTERNS (NEVER DO)
- ❌ Edit multiple files simultaneously
- ❌ Make sweeping changes across codebase
- ❌ Create complex scripts to "fix everything"
- ❌ Replace large code chunks without analysis
- ❌ Mix multiple concerns in single change

## UNIVERSAL SOLUTION PATTERNS (ALWAYS DO)
- ✅ **ONE PROBLEM** - Identify single specific issue
- ✅ **ONE FILE** - Make changes in single file only
- ✅ **ONE FIX** - Minimal change to address the issue
- ✅ **VERIFY** - Test the fix works before moving on
- ✅ **MOVE TO NEXT** - Only then tackle the next issue

## SYSTEMATIC DEBUGGING APPROACH

### Step 1: Isolate the Problem
- Run specific failing test/component
- Identify exact error message
- Locate the failing file/function
- Understand what should happen vs. what happens

### Step 2: Minimal Fix Strategy
- Make smallest possible change to fix the issue
- Change only the failing component
- Avoid "while I'm here" improvements
- Focus solely on the immediate problem

### Step 3: Verification Protocol
- Run the specific test/component again
- Verify the fix resolves the issue
- Ensure no new problems introduced
- Document what was changed and why

### Step 4: Move to Next Issue
- Only after current issue completely resolved
- Start fresh with new problem identification
- Don't carry over context from previous fix
- Maintain systematic approach

## TEST HANGING METHODOLOGY

### Systematic Approach
1. **Identify**: Which specific test hangs
   ```bash
   pytest path/to/test.py::test_name -v
   ```

2. **Analyze**: Read the hanging test code
   - What is the test trying to do?
   - Where might it get stuck?
   - What resources might not be cleaned up?

3. **Fix**: Make minimal change to hanging test only
   - Add proper cleanup
   - Fix resource management
   - Add timeouts if needed

4. **Verify**: Run the specific test again
   - Confirm it no longer hangs
   - Check it passes or fails appropriately
   - Move to next hanging test

## UNIVERSAL MOCK PATTERNS

### For External Dependencies
```python
# Pattern: Mock external services/APIs
with patch('module.external_service') as mock_service:
    mock_service.return_value = test_data
    # Test code here
```

### For Async Resources
```python
# Pattern: Proper async cleanup
@pytest.mark.asyncio
async def test_async_component():
    component = None
    try:
        component = create_async_component()
        # Test code here
    finally:
        if component:
            await component.cleanup()
```

## FILE MANAGEMENT METHODOLOGY

### Temporary Files
- ✅ Create in designated temp directory only
- ✅ Clean up after task completion
- ❌ Never scatter temp files in project
- ❌ Never create temp files in source directories

### File Edit Strategy
- Edit ONE file per fix
- Make minimal changes only
- Verify changes work immediately
- Document the specific change made

## WHEN CHAOS OCCURS

### Recognition Signs
- Multiple files being edited
- Complex changes across codebase
- Tests breaking in unexpected ways
- Unclear what change caused what effect

### Recovery Protocol
1. **STOP** immediately
2. **REVERT** to last known working state
3. **IDENTIFY** the specific problem to solve
4. **APPLY** systematic one-fix approach
5. **VERIFY** each change individually

## METHODOLOGY VALIDATION

### Success Indicators
- Problems get resolved systematically
- No unexpected side effects from changes
- Clear cause-and-effect relationship
- Steady forward progress

### Failure Indicators
- Same problems keep recurring
- Changes break unrelated functionality
- Unclear what change fixed what
- Development feels chaotic or random

## UNIVERSAL APPLICABILITY

### Project-Agnostic Elements
- One problem, one file, one fix principle
- Systematic debugging approach
- Proper test isolation
- Resource cleanup patterns

### Adaptable Elements
- Specific tools and commands
- Programming language syntax
- Project structure details
- Technology-specific patterns

## CHAOS PREVENTION CHECKLIST

Before making any change:
- [ ] Have I identified ONE specific problem?
- [ ] Will I edit only ONE file?
- [ ] Is this the MINIMAL fix needed?
- [ ] Do I know how to verify it works?
- [ ] Am I avoiding scope creep?

After making any change:
- [ ] Did the specific problem get resolved?
- [ ] Did I introduce any new problems?
- [ ] Is the codebase in a clean state?
- [ ] Am I ready for the next single problem?

## STREAM-BASED CHAOS PREVENTION

### Stream Layer Isolation Rules
- ✅ **Layer 2 ONLY**: Real API calls and recording
- ✅ **Layer 3+ ONLY**: Replayed streams as input
- ❌ **NEVER**: Mix real API calls in higher layers
- ❌ **NEVER**: Test higher layers with real network calls

### Stream Testing Chaos Prevention
- ✅ **ONE STREAM** - Test one stream transformation at a time
- ✅ **RECORDED DATA** - Use consistent replayed data for all Layer 3+ tests
- ✅ **STREAM ASSERTIONS** - Assert on stream output, not internal state
- ❌ **NEVER**: Mock stream data when recorded data available
- ❌ **NEVER**: Test multiple stream transformations in one test

### Recording Management Rules
- ✅ Create dedicated recordings for each test scenario
- ✅ Version recordings with clear naming conventions
- ✅ Keep recordings focused and minimal
- ❌ Never reuse complex recordings across different tests
- ❌ Never edit source code and recordings simultaneously

### Debugging Stream Problems
1. **Isolate the Layer**: Is problem in Layer 2 (real API) or Layer 3+ (replay)?
2. **Check Recording**: Is the recorded data what you expect?
3. **Test Replay**: Does the replayed stream match the recording?
4. **Validate Transform**: Is the stream transformation logic correct?
5. **Fix One Layer**: Make changes only in the problematic layer

## TDD FUNCTION JUMPING PREVENTION

### CRITICAL ANTI-PATTERN: Method Jumping
**The most dangerous TDD violation: Adding multiple incomplete functions**

#### Recognition Signs
- Multiple empty methods added in one session
- Testing method existence instead of functionality  
- Moving to new functions before current one actually works
- Integration tests before unit functionality proven

#### Prevention Protocol
1. **ONE FUNCTION RULE**: Complete current function before adding any new function
2. **PROOF OF WORK**: Function must actually do what its name promises
3. **REAL DATA TEST**: Must work with actual data, not just pass empty tests
4. **ERROR HANDLING**: Must handle basic failure cases

#### Example of Violation
```python
# ❌ WRONG: Function jumping anti-pattern
def start_recording(): pass
def stop_recording(): pass  
def get_status(): pass
# Multiple functions, none working
```

#### Example of Correct Approach  
```python
# ✅ CORRECT: Complete start_recording fully first
def start_recording():
    # Actually starts mitmproxy process
    # Actually captures HTTP traffic
    # Actually saves to file
    # Returns success/failure status
    
# ONLY add stop_recording after start_recording is COMPLETE
```

### ENFORCEMENT CHECKPOINT

Before adding ANY new function, ask:
- [ ] Does my current function actually work?
- [ ] Can I prove it with real data?
- [ ] Would I trust it in production?
- [ ] Does it handle basic errors?

**If any answer is NO, complete current function first.**
