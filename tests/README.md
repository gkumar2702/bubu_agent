# Tests Directory

This directory contains comprehensive tests for the Bubu Agent.

## Test Files

### Core Functionality Tests
- **test_message_composer.py** - Tests for the refactored MessageComposer
- **test_scheduler.py** - Tests for the MessageScheduler
- **test_provider_stub.py** - Tests for WhatsApp providers and LLM

### Test Configuration
- **conftest.py** - Pytest configuration and shared fixtures
- **__init__.py** - Makes this directory a Python package

## Running Tests

### Run All Tests
```bash
# From project root
pytest tests/

# With verbose output
pytest tests/ -v

# With coverage
pytest tests/ --cov=utils --cov=providers
```

### Run Specific Test Files
```bash
# Test message composition
pytest tests/test_message_composer.py -v

# Test scheduler
pytest tests/test_scheduler.py -v

# Test providers
pytest tests/test_provider_stub.py -v
```

### Run Specific Test Classes
```bash
# Test MessageComposer class
pytest tests/test_message_composer.py::TestMessageComposer -v

# Test scheduler functionality
pytest tests/test_scheduler.py::TestMessageScheduler -v
```

### Run Specific Test Methods
```bash
# Test specific functionality
pytest tests/test_message_composer.py::TestMessageComposer::test_compose_message_ai_generated -v
```

## Test Coverage

The tests cover:
- Message composition and generation
- Scheduler functionality
- WhatsApp provider integration
- LLM integration
- Error handling and fallbacks
- Configuration management
- Storage operations

## Test Structure

### MessageComposer Tests
- AI message generation
- Fallback message generation
- Message validation and cleaning
- Idempotency checks
- Error handling

### Scheduler Tests
- Message scheduling
- Time window calculations
- Provider integration
- Storage operations

### Provider Tests
- WhatsApp provider functionality
- LLM integration
- Error handling
- Availability checks

## Notes

- Tests use mock objects to avoid external API calls
- Async tests are properly marked with `@pytest.mark.asyncio`
- Tests include both success and failure scenarios
- Coverage includes edge cases and error conditions
