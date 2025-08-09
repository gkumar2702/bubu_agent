"""Tests for provider functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from providers.messenger import Messenger
from providers.twilio_whatsapp import TwilioWhatsApp
from providers.meta_whatsapp import MetaWhatsApp
from providers.huggingface_llm import HuggingFaceLLM


class TestTwilioWhatsApp:
    """Test Twilio WhatsApp provider."""
    
    @pytest.fixture
    def twilio_provider(self):
        """Create Twilio provider."""
        return TwilioWhatsApp(
            account_sid="test_sid",
            auth_token="test_token",
            from_number="whatsapp:+1234567890"
        )
    
    @pytest.mark.asyncio
    async def test_send_text_success(self, twilio_provider):
        """Test successful message sending."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"sid": "msg_123", "status": "sent"}
            mock_post.return_value = mock_response
            
            result = await twilio_provider.send_text("+9876543210", "Hello!")
            
            assert result == "msg_123"
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_text_failure(self, twilio_provider):
        """Test failed message sending."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response
            
            result = await twilio_provider.send_text("+9876543210", "Hello!")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_send_text_exception(self, twilio_provider):
        """Test exception during message sending."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = Exception("Network error")
            
            result = await twilio_provider.send_text("+9876543210", "Hello!")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_is_available_success(self, twilio_provider):
        """Test availability check success."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = await twilio_provider.is_available()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_is_available_failure(self, twilio_provider):
        """Test availability check failure."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response
            
            result = await twilio_provider.is_available()
            
            assert result is False
    
    def test_get_provider_name(self, twilio_provider):
        """Test provider name."""
        assert twilio_provider.get_provider_name() == "twilio"


class TestMetaWhatsApp:
    """Test Meta WhatsApp provider."""
    
    @pytest.fixture
    def meta_provider(self):
        """Create Meta provider."""
        return MetaWhatsApp(
            access_token="test_token",
            phone_number_id="123456789"
        )
    
    @pytest.mark.asyncio
    async def test_send_text_success(self, meta_provider):
        """Test successful message sending."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "messages": [{"id": "msg_123"}]
            }
            mock_post.return_value = mock_response
            
            result = await meta_provider.send_text("+9876543210", "Hello!")
            
            assert result == "msg_123"
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_text_failure(self, meta_provider):
        """Test failed message sending."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response
            
            result = await meta_provider.send_text("+9876543210", "Hello!")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_is_available_success(self, meta_provider):
        """Test availability check success."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = await meta_provider.is_available()
            
            assert result is True
    
    def test_get_provider_name(self, meta_provider):
        """Test provider name."""
        assert meta_provider.get_provider_name() == "meta"


class TestHuggingFaceLLM:
    """Test Hugging Face LLM provider."""
    
    @pytest.fixture
    def hf_provider(self):
        """Create Hugging Face provider."""
        return HuggingFaceLLM(
            api_key="test_key",
            model_id="test/model"
        )
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self, hf_provider):
        """Test successful text generation."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {"generated_text": "Hello! How are you today?"}
            ]
            mock_post.return_value = mock_response
            
            result = await hf_provider.generate_text(
                "You are a helpful assistant.",
                "Generate a greeting."
            )
            
            assert result == "Hello! How are you today?"
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_text_model_loading(self, hf_provider):
        """Test text generation when model is loading."""
        with patch('httpx.AsyncClient.post') as mock_post:
            # First call returns 503 (model loading)
            mock_response1 = MagicMock()
            mock_response1.status_code = 503
            
            # Second call returns success
            mock_response2 = MagicMock()
            mock_response2.status_code = 200
            mock_response2.json.return_value = [
                {"generated_text": "Hello!"}
            ]
            
            mock_post.side_effect = [mock_response1, mock_response2]
            
            with patch('asyncio.sleep') as mock_sleep:
                result = await hf_provider.generate_text(
                    "You are a helpful assistant.",
                    "Generate a greeting."
                )
                
                assert result == "Hello!"
                assert mock_post.call_count == 2
                mock_sleep.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_text_failure(self, hf_provider):
        """Test failed text generation."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_post.return_value = mock_response
            
            result = await hf_provider.generate_text(
                "You are a helpful assistant.",
                "Generate a greeting."
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_text_timeout(self, hf_provider):
        """Test text generation timeout."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = Exception("Timeout")
            
            result = await hf_provider.generate_text(
                "You are a helpful assistant.",
                "Generate a greeting."
            )
            
            assert result is None
    
    def test_extract_generated_text_standard_format(self, hf_provider):
        """Test extracting text from standard response format."""
        response = [{"generated_text": "Hello world!"}]
        result = hf_provider._extract_generated_text(response)
        assert result == "Hello world!"
    
    def test_extract_generated_text_dict_format(self, hf_provider):
        """Test extracting text from dict response format."""
        response = {"generated_text": "Hello world!"}
        result = hf_provider._extract_generated_text(response)
        assert result == "Hello world!"
    
    def test_extract_generated_text_choices_format(self, hf_provider):
        """Test extracting text from choices response format."""
        response = {"choices": [{"text": "Hello world!"}]}
        result = hf_provider._extract_generated_text(response)
        assert result == "Hello world!"
    
    def test_extract_generated_text_empty(self, hf_provider):
        """Test extracting text from empty response."""
        response = []
        result = hf_provider._extract_generated_text(response)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_is_available_success(self, hf_provider):
        """Test availability check success."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = await hf_provider.is_available()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_is_available_failure(self, hf_provider):
        """Test availability check failure."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = await hf_provider.is_available()
            
            assert result is False


class TestMessengerInterface:
    """Test Messenger abstract interface."""
    
    def test_messenger_is_abstract(self):
        """Test that Messenger is an abstract base class."""
        with pytest.raises(TypeError):
            Messenger()
