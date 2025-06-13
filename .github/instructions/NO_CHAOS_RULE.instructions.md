# NO CHAOS RULE - CRITICAL DEVELOPMENT PRINCIPLE

## STOP MAKING CHAOS IN FILES

### NEVER DO THIS:
- ❌ Edit multiple files at once
- ❌ Make big sweeping changes across codebase
- ❌ Create complex scripts to "fix everything"
- ❌ Replace large chunks of code without careful analysis

### ALWAYS DO THIS:
- ✅ **ONE PROBLEM, ONE FILE, ONE FIX**
- ✅ **TEST FIRST** - run failing test to understand the exact issue
- ✅ **MINIMAL CHANGE** - fix only what's broken
- ✅ **VERIFY FIX** - run test again to confirm it works
- ✅ **MOVE TO NEXT** - only then tackle the next issue

### HANGING TESTS - SYSTEMATIC APPROACH:

1. **Identify** which specific test hangs: `pytest test_file.py::test_name -v`
2. **Analyze** what the test does (read the test code)
3. **Fix** only that one test with minimal change
4. **Verify** the fix works
5. **Repeat** for next hanging test

### MOCK PATTERN FOR dYdX TESTS:
```python
# ALWAYS mock BOTH components to prevent real connections:
with patch('src.dydx_bot.connection.client.IndexerClient') as mock_indexer, \
     patch('src.dydx_bot.connection.client.IndexerSocket') as mock_socket:
    
    mock_indexer.return_value = AsyncMock()
    mock_socket_instance = AsyncMock()
    mock_socket.return_value = mock_socket_instance
```

### TEMPORARY FILES MANAGEMENT:
- ✅ **CREATE** temporary files in `./tmp/` directory only
- ✅ **DELETE** temporary files when no longer needed
- ✅ **CLEAN UP** after each task completion
- ❌ **NEVER** leave temporary files scattered in project root
- ❌ **NEVER** create temp files in src/ or tests/ directories

### WHEN USER SAYS "CHAOS" OR "BURZA":
- STOP immediately
- Ask which SPECIFIC test to fix
- Fix ONLY that one test
- Show the fix works
- Wait for next instruction

**REMEMBER: Slow and steady wins the race. One fix at a time.**
