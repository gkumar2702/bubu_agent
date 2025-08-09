"""Tests for message composition."""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from compose import MessageComposer
from providers.huggingface_llm import HuggingFaceLLM


class TestMessageComposer:
    """Test message composition functionality."""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM."""
        llm = MagicMock(spec=HuggingFaceLLM)
        llm.generate_text = AsyncMock()
        return llm
    
    @pytest.fixture
    def composer(self, mock_llm):
        """Create a message composer with mock LLM."""
        return MessageComposer(mock_llm)
    
    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage."""
        storage = MagicMock()
        storage.is_message_sent.return_value = False
        return storage
    
    def test_get_signature_closer(self, composer):
        """Test signature closer selection."""
        today = date.today()
        closer = composer._get_signature_closer(today)
        
        assert closer is not None
        assert len(closer) > 0
        assert "bubu" in closer.lower()
    
    def test_get_fallback_message(self, composer):
        """Test fallback message generation."""
        closer = "— your bubu"
        message = composer._get_fallback_message("morning", closer)
        
        assert message is not None
        assert len(message) > 0
        assert "bubu" in message.lower()
    
    def test_clean_generated_text(self, composer):
        """Test text cleaning and formatting."""
        text = "  Hello   there!  😊  "
        closer = "— bubu"
        
        cleaned = composer._clean_generated_text(text, closer)
        
        assert cleaned == "Hello there! 😊 — bubu"
    
    def test_clean_generated_text_with_existing_closer(self, composer):
        """Test text cleaning when closer already exists."""
        text = "Hello there! — bubu 😊"
        closer = "— bubu"
        
        cleaned = composer._clean_generated_text(text, closer)
        
        assert cleaned == "Hello there!  😊 — bubu"
    
    @pytest.mark.asyncio
    async def test_compose_message_already_sent(self, composer, mock_storage):
        """Test composing message when already sent."""
        composer.set_storage(mock_storage)
        mock_storage.is_message_sent.return_value = True
        
        message, status = await composer.compose_message("morning", date.today())
        
        assert message == ""
        assert status == "already_sent"
    
    @pytest.mark.asyncio
    async def test_compose_message_force_fallback(self, composer, mock_storage):
        """Test composing message with force fallback."""
        composer.set_storage(mock_storage)
        
        message, status = await composer.compose_message(
            "morning", 
            date.today(), 
            force_fallback=True
        )
        
        assert message is not None
        assert len(message) > 0
        assert status == "fallback"
    
    @pytest.mark.asyncio
    async def test_compose_message_ai_generation_success(self, composer, mock_storage, mock_llm):
        """Test successful AI message generation."""
        composer.set_storage(mock_storage)
        mock_llm.generate_text.return_value = "Good morning! Have a wonderful day! 😊"
        
        message, status = await composer.compose_message("morning", date.today())
        
        assert message is not None
        assert len(message) > 0
        assert status == "ai_generated"
        mock_llm.generate_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_compose_message_ai_generation_failure(self, composer, mock_storage, mock_llm):
        """Test AI generation failure falls back to template."""
        composer.set_storage(mock_storage)
        mock_llm.generate_text.return_value = None
        
        message, status = await composer.compose_message("morning", date.today())
        
        assert message is not None
        assert len(message) > 0
        assert status == "fallback"
    
    def test_get_message_preview(self, composer):
        """Test message preview generation."""
        message = composer.get_message_preview("morning")
        
        assert message is not None
        assert len(message) > 0
        assert "bubu" in message.lower()
    
    def test_get_message_preview_with_fallback_option(self, composer):
        """Test message preview with fallback option."""
        options = {"use_fallback": True}
        message = composer.get_message_preview("morning", options)
        
        assert message is not None
        assert len(message) > 0
        assert "bubu" in message.lower()


class TestSeededRandom:
    """Test seeded random number generation."""
    
    def test_seeded_random_consistency(self):
        """Test that seeded random produces consistent results."""
        from utils import SeededRandom
        
        seed = 12345
        rng1 = SeededRandom(seed)
        rng2 = SeededRandom(seed)
        
        # Test multiple operations
        for _ in range(10):
            assert rng1.randint(1, 100) == rng2.randint(1, 100)
            assert rng1.random() == rng2.random()
    
    def test_seeded_random_choice(self):
        """Test seeded random choice."""
        from utils import SeededRandom
        
        seed = 12345
        rng = SeededRandom(seed)
        choices = ["a", "b", "c", "d"]
        
        # Should be deterministic
        choice1 = rng.choice(choices)
        choice2 = rng.choice(choices)
        
        assert choice1 in choices
        assert choice2 in choices
