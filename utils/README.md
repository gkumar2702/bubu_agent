# MessageComposer Refactored

This document describes the refactored `MessageComposer` module, which has been redesigned to be more idiomatic, well-typed, robust, and maintainable.

## Design Principles

### 1. Type Safety
- **Full type hints**: All functions and methods have complete type annotations
- **Protocols**: Uses `Protocol` classes for dependency injection (LLM, Storage, Config)
- **Enums**: Replaced stringly-typed message types with `MessageType` enum
- **Dataclasses**: Uses `@dataclass(slots=True)` for data containers

### 2. Dependency Injection
- **LLMProtocol**: Abstract interface for text generation
- **StorageProtocol**: Abstract interface for idempotency checks
- **ConfigFacade**: Abstract interface for configuration access
- **NullStorage**: Default implementation that always returns False

### 3. Error Handling
- **Typed Results**: `GenerationResult` and `MessageResult` with detailed status
- **Graceful Degradation**: Falls back to templates when AI generation fails
- **Exception Safety**: Narrow exception handling with proper logging
- **Timeout Handling**: Explicit timeout handling for LLM calls

### 4. Deterministic Behavior
- **Seeded Randomness**: All random selections use date-based seeds
- **Consistent Outputs**: Same date always produces same message
- **Testable**: Fixed seeds enable deterministic testing

## Architecture

### Core Components

```python
class MessageComposer:
    def __init__(
        self,
        llm: LLMProtocol,
        config: ConfigFacade,
        storage: StorageProtocol = NullStorage()
    ):
        # Dependencies injected via constructor
```

### Message Composition Flow

1. **Idempotency Check**: Verify message not already sent
2. **AI Generation**: Attempt to generate with LLM
3. **Validation**: Check length, emojis, content policy
4. **Fallback**: Use templates if AI fails
5. **Result**: Return typed result with status

### Error Handling Strategy

```python
async def compose_message(...) -> MessageResult:
    try:
        # Main composition logic
        return MessageResult(text=message, status=MessageStatus.AI_GENERATED)
    except Exception as e:
        # Emergency fallback
        return MessageResult(text=fallback, status=MessageStatus.ERROR_FALLBACK)
```

## Seeding Strategy

### Deterministic Randomness
- **Date-based seeds**: `get_date_seed(date_obj)` generates consistent seeds
- **Per-method seeding**: Each random selection uses the same date seed
- **Consistent output**: Same date always produces same message

### Seeded Components
- **Signature closers**: Rotating closers based on date
- **Fallback templates**: Template selection based on date
- **Bollywood quotes**: Quote selection based on date
- **Cheesy lines**: Line selection based on date

### Example
```python
# Same date always produces same results
date1 = date(2024, 1, 15)
date2 = date(2024, 1, 15)

closer1 = composer._get_signature_closer(date1)
closer2 = composer._get_signature_closer(date2)
assert closer1 == closer2  # Always true
```

## Error Handling

### LLM Generation Errors
- **Missing prompts**: Returns `LLMResult.MISSING_PROMPTS`
- **Empty response**: Returns `LLMResult.EMPTY`
- **Timeout**: Returns `LLMResult.TIMEOUT`
- **Exceptions**: Returns `LLMResult.EXCEPTION`

### Message Validation
- **Length limits**: Truncates to max length with "..."
- **Emoji limits**: Removes excess emojis
- **Content policy**: Validates against forbidden topics

### Graceful Degradation
1. **AI generation fails** → Use fallback templates
2. **Template formatting fails** → Use emergency fallback
3. **Storage fails** → Assume message not sent
4. **Config fails** → Use default values

## Extension Points

### Adding New Message Types
1. **Update MessageType enum**:
   ```python
   class MessageType(Enum):
       MORNING = "morning"
       FLIRTY = "flirty"
       NIGHT = "night"
       NEW_TYPE = "new_type"  # Add here
   ```

2. **Add templates to config.yaml**:
   ```yaml
   fallback_templates:
     new_type:
       - "Template for {GF_NAME} {closer}"
   ```

3. **Add prompt templates**:
   ```yaml
   prompt_templates:
     new_type:
       system: "System prompt for new type"
       user: "User prompt for new type"
   ```

### Adding New LLM Providers
1. **Implement LLMProtocol**:
   ```python
   class NewLLM(LLMProtocol):
       async def generate_text(...) -> Optional[str]:
           # Implementation
   ```

2. **Use in composer**:
   ```python
   composer = MessageComposer(
       llm=NewLLM(),
       config=config_facade,
       storage=storage_protocol
   )
   ```

### Adding New Storage Backends
1. **Implement StorageProtocol**:
   ```python
   class NewStorage(StorageProtocol):
       def is_message_sent(self, date_obj: date, message_type: MessageType) -> bool:
           # Implementation
   ```

2. **Use in composer**:
   ```python
   composer = MessageComposer(
       llm=llm,
       config=config_facade,
       storage=NewStorage()
   )
   ```

## Testing Strategy

### Unit Tests
- **Fake implementations**: `FakeLLM`, `FakeStorage`, `FakeConfig`
- **Deterministic testing**: Fixed seeds for consistent results
- **Error scenarios**: Test all error paths
- **Edge cases**: Test boundary conditions

### Test Coverage
- **Message composition**: All status paths
- **AI generation**: Success and failure scenarios
- **Fallback logic**: Template selection and formatting
- **Validation**: Length, emoji, and content validation
- **Seeding**: Deterministic behavior verification

### Example Test
```python
@pytest.mark.asyncio
async def test_compose_message_ai_generated(composer, fixed_seed_date):
    result = await composer.compose_message(MessageType.MORNING, fixed_seed_date)
    assert result.status == MessageStatus.AI_GENERATED
    assert "TestGirlfriend" in result.text
```

## Performance Considerations

### Caching
- **Prompt templates**: LRU cache for frequently accessed templates
- **Config values**: Cached in facade implementation
- **Seeded RNG**: Reused for same date

### Async Operations
- **LLM calls**: Properly awaited with timeouts
- **No blocking calls**: All I/O operations are async
- **Concurrent safety**: Thread-safe seeded random

### Memory Management
- **Slots**: Dataclasses use `slots=True` for memory efficiency
- **Lazy loading**: Config values loaded on demand
- **Cleanup**: Proper resource cleanup in error cases

## Migration Guide

### From Old to New
1. **Update imports**:
   ```python
   # Old
   from utils.compose import create_message_composer
   
   # New
   from utils.compose_refactored import create_message_composer_refactored
   ```

2. **Update usage**:
   ```python
   # Old
   composer = create_message_composer()
   message, status = await composer.compose_message("morning", date.today())
   
   # New
   composer = create_message_composer_refactored(llm, storage)
   result = await composer.compose_message(MessageType.MORNING, date.today())
   message = result.text
   status = result.status.value
   ```

3. **Update tests**:
   ```python
   # Old
   assert status == "ai_generated"
   
   # New
   assert result.status == MessageStatus.AI_GENERATED
   ```

## Best Practices

### Development
1. **Use type hints**: Always add type annotations
2. **Follow protocols**: Implement required interfaces
3. **Handle errors**: Use typed results for error handling
4. **Test deterministically**: Use fixed seeds for tests
5. **Document changes**: Update this README when extending

### Production
1. **Monitor errors**: Log all error cases with details
2. **Set timeouts**: Configure appropriate LLM timeouts
3. **Use fallbacks**: Always have fallback templates
4. **Validate inputs**: Check all external inputs
5. **Test thoroughly**: Run full test suite before deployment

## Troubleshooting

### Common Issues
1. **Type errors**: Ensure all dependencies implement required protocols
2. **Timeout errors**: Increase timeout or optimize LLM calls
3. **Template errors**: Check config.yaml for missing templates
4. **Seeding issues**: Verify date objects are timezone-naive

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Run composer operations to see detailed logs
```

### Performance Profiling
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Run composer operations
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats()
```
