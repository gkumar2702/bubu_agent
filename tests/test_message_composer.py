"""Tests for the refactored MessageComposer."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from utils.compose_refactored import MessageComposer
from utils.types import (
    GenerationResult, LLMResult, MessageResult, MessageStatus, MessageType,
    NullStorage
)


class FakeLLM:
    """Fake LLM implementation for testing."""
    
    def __init__(self, responses: Dict[str, str]):
        """Initialize with predefined responses."""
        self.responses = responses
        self.call_count = 0
    
    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        do_sample: bool
    ) -> Optional[str]:
        """Return predefined response based on message type."""
        self.call_count += 1
        
        # Extract message type from system prompt
        if "morning" in system_prompt.lower():
            return self.responses.get("morning", "Good morning test!")
        elif "flirty" in system_prompt.lower():
            return self.responses.get("flirty", "Hey there test!")
        elif "night" in system_prompt.lower():
            return self.responses.get("night", "Good night test!")
        
        return self.responses.get("default", "Hello test!")


class FakeStorage:
    """Fake storage implementation for testing."""
    
    def __init__(self, sent_messages: List[tuple[date, MessageType]]):
        """Initialize with list of sent messages."""
        self.sent_messages = sent_messages
    
    def is_message_sent(self, date_obj: date, message_type: MessageType) -> bool:
        """Check if message was sent."""
        return (date_obj, message_type) in self.sent_messages


class FakeConfig:
    """Fake configuration implementation for testing."""
    
    def __init__(self):
        """Initialize with test configuration."""
        self.gf_name = "TestGirlfriend"
        self.daily_flirty_tone = "romantic"
    
    def get_general_setting(self, key: str, default: Any = None) -> Any:
        """Get general setting."""
        settings = {
            "max_message_length": 700,
            "max_emojis": 5
        }
        return settings.get(key, default)
    
    def get_hf_setting(self, key: str, default: Any = None) -> Any:
        """Get Hugging Face setting."""
        settings = {
            "max_new_tokens": 150,
            "temperature": 0.8,
            "top_p": 0.9,
            "do_sample": True,
            "timeout_seconds": 30
        }
        return settings.get(key, default)
    
    def get_prompt_template(self, message_type: MessageType, template_type: str) -> str:
        """Get prompt template."""
        templates = {
            (MessageType.MORNING, "system"): "You are sending a morning message to {GF_NAME}.",
            (MessageType.MORNING, "user"): "Create a morning message for {GF_NAME}.",
            (MessageType.FLIRTY, "system"): "You are sending a flirty message to {GF_NAME}.",
            (MessageType.FLIRTY, "user"): "Create a flirty message for {GF_NAME}.",
            (MessageType.NIGHT, "system"): "You are sending a night message to {GF_NAME}.",
            (MessageType.NIGHT, "user"): "Create a night message for {GF_NAME}."
        }
        return templates.get((message_type, template_type), "")
    
    def get_fallback_templates(self, message_type: MessageType) -> List[str]:
        """Get fallback templates."""
        templates = {
            MessageType.MORNING: [
                "Good morning {GF_NAME}! Have a wonderful day! {closer}",
                "Morning {GF_NAME}! You're amazing! {closer}"
            ],
            MessageType.FLIRTY: [
                "Hey {GF_NAME}! You're beautiful! {closer}",
                "Hi {GF_NAME}! I miss you! {closer}"
            ],
            MessageType.NIGHT: [
                "Good night {GF_NAME}! Sweet dreams! {closer}",
                "Night {GF_NAME}! Sleep well! {closer}"
            ]
        }
        return templates.get(message_type, [])
    
    def get_signature_closers(self) -> List[str]:
        """Get signature closers."""
        return ["— bubu", "— love", "— your bubu"]
    
    def get_bollywood_quotes(self) -> List[str]:
        """Get Bollywood quotes."""
        return ["Tumhari muskaan meri duniya hai", "Mere liye tum perfect ho"]
    
    def get_cheesy_lines(self) -> List[str]:
        """Get cheesy lines."""
        return ["You're the WiFi to my heart!", "Are you a magician?"]


@pytest.fixture
def fake_llm() -> FakeLLM:
    """Create a fake LLM for testing."""
    return FakeLLM({
        "morning": "Good morning TestGirlfriend! Have an amazing day! — bubu",
        "flirty": "Hey TestGirlfriend! You're absolutely beautiful! — love",
        "night": "Good night TestGirlfriend! Sweet dreams! — your bubu"
    })


@pytest.fixture
def fake_config() -> FakeConfig:
    """Create a fake config for testing."""
    return FakeConfig()


@pytest.fixture
def fake_storage() -> FakeStorage:
    """Create a fake storage for testing."""
    return FakeStorage([])


@pytest.fixture
def composer(fake_llm: FakeLLM, fake_config: FakeConfig, fake_storage: FakeStorage) -> MessageComposer:
    """Create a message composer for testing."""
    return MessageComposer(
        llm=fake_llm,
        config=fake_config,
        storage=fake_storage
    )


@pytest.fixture
def fixed_seed_date() -> date:
    """Return a fixed date for deterministic testing."""
    return date(2024, 1, 15)


class TestMessageComposer:
    """Test cases for MessageComposer."""
    
    def test_init(self, fake_llm: FakeLLM, fake_config: FakeConfig):
        """Test MessageComposer initialization."""
        composer = MessageComposer(fake_llm, fake_config)
        assert composer.llm == fake_llm
        assert composer.config == fake_config
        assert isinstance(composer.storage, NullStorage)
    
    def test_init_with_storage(self, fake_llm: FakeLLM, fake_config: FakeConfig, fake_storage: FakeStorage):
        """Test MessageComposer initialization with storage."""
        composer = MessageComposer(fake_llm, fake_config, fake_storage)
        assert composer.storage == fake_storage
    
    @pytest.mark.asyncio
    async def test_compose_message_already_sent(
        self,
        composer: MessageComposer,
        fake_storage: FakeStorage,
        fixed_seed_date: date
    ):
        """Test that already sent messages return appropriate status."""
        # Mark message as already sent
        fake_storage.sent_messages.append((fixed_seed_date, MessageType.MORNING))
        
        result = await composer.compose_message(MessageType.MORNING, fixed_seed_date)
        
        assert result.status == MessageStatus.ALREADY_SENT
        assert result.text == ""
        assert result.details["message_type"] == "morning"
    
    @pytest.mark.asyncio
    async def test_compose_message_ai_generated(
        self,
        composer: MessageComposer,
        fixed_seed_date: date
    ):
        """Test successful AI message generation."""
        result = await composer.compose_message(MessageType.MORNING, fixed_seed_date)
        
        assert result.status == MessageStatus.AI_GENERATED
        assert "Good morning TestGirlfriend" in result.text
        assert result.details["message_type"] == "morning"
    
    @pytest.mark.asyncio
    async def test_compose_message_fallback_on_ai_failure(
        self,
        fake_llm: FakeLLM,
        fake_config: FakeConfig,
        fake_storage: FakeStorage,
        fixed_seed_date: date
    ):
        """Test fallback when AI generation fails."""
        # Configure LLM to return None (failure)
        fake_llm.responses["morning"] = None
        
        composer = MessageComposer(fake_llm, fake_config, fake_storage)
        result = await composer.compose_message(MessageType.MORNING, fixed_seed_date)
        
        assert result.status == MessageStatus.FALLBACK
        assert "Good morning TestGirlfriend" in result.text
        assert result.details["reason"] == "ai_generation_failed"
    
    @pytest.mark.asyncio
    async def test_compose_message_force_fallback(
        self,
        composer: MessageComposer,
        fixed_seed_date: date
    ):
        """Test forced fallback mode."""
        result = await composer.compose_message(
            MessageType.MORNING,
            fixed_seed_date,
            force_fallback=True
        )
        
        assert result.status == MessageStatus.FALLBACK
        assert "Good morning TestGirlfriend" in result.text
        assert result.details["reason"] == "forced_fallback"
    
    def test_get_fallback_message_deterministic(
        self,
        composer: MessageComposer,
        fixed_seed_date: date
    ):
        """Test that fallback messages are deterministic for the same date."""
        closer = composer._get_signature_closer(fixed_seed_date)
        
        message1 = composer._get_fallback_message(MessageType.MORNING, closer, fixed_seed_date)
        message2 = composer._get_fallback_message(MessageType.MORNING, closer, fixed_seed_date)
        
        assert message1 == message2
    
    def test_get_fallback_message_different_dates(
        self,
        composer: MessageComposer
    ):
        """Test that fallback messages can be different for different dates."""
        closer = "— bubu"
        date1 = date(2024, 1, 15)
        date2 = date(2024, 1, 16)
        
        message1 = composer._get_fallback_message(MessageType.MORNING, closer, date1)
        message2 = composer._get_fallback_message(MessageType.MORNING, closer, date2)
        
        # Messages might be different due to seeded randomness
        # This test ensures the method works with different dates
        assert isinstance(message1, str)
        assert isinstance(message2, str)
        assert "TestGirlfriend" in message1
        assert "TestGirlfriend" in message2
    
    def test_get_signature_closer_deterministic(
        self,
        composer: MessageComposer,
        fixed_seed_date: date
    ):
        """Test that signature closers are deterministic for the same date."""
        closer1 = composer._get_signature_closer(fixed_seed_date)
        closer2 = composer._get_signature_closer(fixed_seed_date)
        
        assert closer1 == closer2
    
    def test_validate_and_trim_within_limits(self, composer: MessageComposer):
        """Test text validation within limits."""
        text = "Hello world! 🌟"
        result = composer._validate_and_trim(text, max_length=100, max_emojis=5)
        
        assert result == text
    
    def test_validate_and_trim_exceeds_length(self, composer: MessageComposer):
        """Test text validation when exceeding length limit."""
        text = "This is a very long message that exceeds the maximum length limit"
        result = composer._validate_and_trim(text, max_length=20, max_emojis=5)
        
        assert len(result) <= 20
        assert result.endswith("...")
    
    def test_validate_and_trim_exceeds_emojis(self, composer: MessageComposer):
        """Test text validation when exceeding emoji limit."""
        text = "Hello 🌟 world 🌟 with 🌟 too 🌟 many 🌟 emojis 🌟"
        result = composer._validate_and_trim(text, max_length=100, max_emojis=3)
        
        emoji_count = len([c for c in result if ord(c) > 0xFFFF])
        assert emoji_count <= 3
    
    def test_get_message_preview(self, composer: MessageComposer):
        """Test message preview generation."""
        preview = composer.get_message_preview(MessageType.MORNING)
        
        assert isinstance(preview, str)
        assert "TestGirlfriend" in preview
    
    def test_get_message_preview_with_options(self, composer: MessageComposer):
        """Test message preview with options."""
        preview = composer.get_message_preview(
            MessageType.MORNING,
            options={"randomize": True, "seed": 123}
        )
        
        assert isinstance(preview, str)
        assert "TestGirlfriend" in preview
    
    def test_get_fallback_templates(self, composer: MessageComposer):
        """Test getting fallback templates."""
        templates = composer.get_fallback_templates(MessageType.MORNING)
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert all(isinstance(t, str) for t in templates)
    
    @pytest.mark.asyncio
    async def test_generate_ai_message_success(
        self,
        composer: MessageComposer,
        fixed_seed_date: date
    ):
        """Test successful AI message generation."""
        closer = "— bubu"
        result = await composer._generate_ai_message(MessageType.MORNING, closer, fixed_seed_date)
        
        assert result.reason == LLMResult.OK
        assert result.text is not None
        assert "TestGirlfriend" in result.text
        assert result.details["message_type"] == "morning"
    
    @pytest.mark.asyncio
    async def test_generate_ai_message_missing_prompts(
        self,
        fake_llm: FakeLLM,
        fake_config: FakeConfig,
        fake_storage: FakeStorage,
        fixed_seed_date: date
    ):
        """Test AI generation with missing prompts."""
        # Create config that returns empty prompts
        fake_config.get_prompt_template = lambda mt, tt: ""
        
        composer = MessageComposer(fake_llm, fake_config, fake_storage)
        closer = "— bubu"
        result = await composer._generate_ai_message(MessageType.MORNING, closer, fixed_seed_date)
        
        assert result.reason == LLMResult.MISSING_PROMPTS
        assert result.text is None
        assert result.details["message_type"] == "morning"
    
    @pytest.mark.asyncio
    async def test_generate_ai_message_empty_response(
        self,
        fake_llm: FakeLLM,
        fake_config: FakeConfig,
        fake_storage: FakeStorage,
        fixed_seed_date: date
    ):
        """Test AI generation with empty response."""
        fake_llm.responses["morning"] = None
        
        composer = MessageComposer(fake_llm, fake_config, fake_storage)
        closer = "— bubu"
        result = await composer._generate_ai_message(MessageType.MORNING, closer, fixed_seed_date)
        
        assert result.reason == LLMResult.EMPTY
        assert result.text is None
        assert result.details["message_type"] == "morning"
    
    def test_clean_generated_text(self, composer: MessageComposer):
        """Test cleaning generated text."""
        text = "  Hello   world  "
        closer = "— bubu"
        result = composer._clean_generated_text(text, closer)
        
        assert result == "Hello world — bubu"
    
    def test_clean_generated_text_with_existing_closer(self, composer: MessageComposer):
        """Test cleaning text that already contains the closer."""
        text = "Hello world — bubu extra text"
        closer = "— bubu"
        result = composer._clean_generated_text(text, closer)
        
        assert result == "Hello world extra text — bubu"
    
    def test_rng_consistency(self, composer: MessageComposer, fixed_seed_date: date):
        """Test that RNG is consistent for the same date."""
        rng1 = composer._rng(fixed_seed_date)
        rng2 = composer._rng(fixed_seed_date)
        
        # Test that they produce the same sequence
        assert rng1.random() == rng2.random()
        assert rng1.random() == rng2.random()


class TestMessageType:
    """Test cases for MessageType enum."""
    
    def test_message_type_values(self):
        """Test MessageType enum values."""
        assert MessageType.MORNING.value == "morning"
        assert MessageType.FLIRTY.value == "flirty"
        assert MessageType.NIGHT.value == "night"
    
    def test_message_type_from_string(self):
        """Test creating MessageType from string."""
        assert MessageType("morning") == MessageType.MORNING
        assert MessageType("flirty") == MessageType.FLIRTY
        assert MessageType("night") == MessageType.NIGHT


class TestMessageStatus:
    """Test cases for MessageStatus enum."""
    
    def test_message_status_values(self):
        """Test MessageStatus enum values."""
        assert MessageStatus.ALREADY_SENT.value == "already_sent"
        assert MessageStatus.AI_GENERATED.value == "ai_generated"
        assert MessageStatus.FALLBACK.value == "fallback"
        assert MessageStatus.ERROR_FALLBACK.value == "error_fallback"


class TestLLMResult:
    """Test cases for LLMResult enum."""
    
    def test_llm_result_values(self):
        """Test LLMResult enum values."""
        assert LLMResult.OK.value == "ok"
        assert LLMResult.MISSING_PROMPTS.value == "missing_prompts"
        assert LLMResult.EMPTY.value == "empty"
        assert LLMResult.EXCEPTION.value == "exception"
        assert LLMResult.TIMEOUT.value == "timeout"
