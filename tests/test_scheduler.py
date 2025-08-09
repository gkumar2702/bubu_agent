"""Tests for scheduler functionality."""

import pytest
from datetime import date, datetime, time
from unittest.mock import AsyncMock, MagicMock, patch

from scheduler import MessageScheduler


class TestMessageScheduler:
    """Test scheduler functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        with patch('scheduler.config') as mock_config:
            mock_config.settings.enabled = True
            mock_config.settings.whatsapp_provider = "twilio"
            mock_config.settings.twilio_account_sid = "test_sid"
            mock_config.settings.twilio_auth_token = "test_token"
            mock_config.settings.twilio_whatsapp_from = "whatsapp:+1234567890"
            mock_config.settings.gf_whatsapp_number = "+9876543210"
            mock_config.settings.timezone = "UTC"
            mock_config.settings.get_skip_dates_list.return_value = []
            yield mock_config
    
    @pytest.fixture
    def mock_messenger(self):
        """Create mock messenger."""
        messenger = MagicMock()
        messenger.send_text = AsyncMock()
        messenger.is_available = AsyncMock(return_value=True)
        messenger.get_provider_name.return_value = "twilio"
        return messenger
    
    @pytest.fixture
    def mock_composer(self):
        """Create mock composer."""
        composer = MagicMock()
        composer.compose_message = AsyncMock()
        composer.set_storage = MagicMock()
        return composer
    
    @pytest.fixture
    def mock_storage(self):
        """Create mock storage."""
        storage = MagicMock()
        storage.is_message_sent.return_value = False
        storage.record_message_sent = MagicMock()
        return storage
    
    @pytest.fixture
    def scheduler(self, mock_config, mock_messenger, mock_composer, mock_storage):
        """Create scheduler with mocks."""
        with patch('scheduler.TwilioWhatsApp', return_value=mock_messenger), \
             patch('scheduler.create_message_composer', return_value=mock_composer), \
             patch('scheduler.Storage', return_value=mock_storage):
            
            scheduler = MessageScheduler()
            scheduler.messenger = mock_messenger
            scheduler.composer = mock_composer
            scheduler.storage = mock_storage
            return scheduler
    
    def test_message_windows(self, scheduler):
        """Test message window definitions."""
        assert "morning" in scheduler.message_windows
        assert "flirty" in scheduler.message_windows
        assert "night" in scheduler.message_windows
        
        morning_start, morning_end = scheduler.message_windows["morning"]
        assert morning_start == time(6, 45)
        assert morning_end == time(9, 30)
    
    def test_generate_daily_times(self, scheduler):
        """Test daily time generation."""
        test_date = date(2024, 1, 1)
        times = scheduler._generate_daily_times(test_date)
        
        assert "morning" in times
        assert "flirty" in times
        assert "night" in times
        
        # All times should be datetime objects or None
        for time_val in times.values():
            assert time_val is None or isinstance(time_val, datetime)
    
    def test_generate_daily_times_consistency(self, scheduler):
        """Test that daily times are consistent for the same date."""
        test_date = date(2024, 1, 1)
        times1 = scheduler._generate_daily_times(test_date)
        times2 = scheduler._generate_daily_times(test_date)
        
        # Times should be the same for the same date
        for message_type in times1:
            if times1[message_type] is not None and times2[message_type] is not None:
                assert times1[message_type] == times2[message_type]
    
    @pytest.mark.asyncio
    async def test_send_message_already_sent(self, scheduler, mock_storage):
        """Test sending message when already sent."""
        mock_storage.is_message_sent.return_value = True
        
        await scheduler._send_message("morning", date.today())
        
        # Should not call composer or messenger
        scheduler.composer.compose_message.assert_not_called()
        scheduler.messenger.send_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, scheduler, mock_composer, mock_messenger, mock_storage):
        """Test successful message sending."""
        mock_composer.compose_message.return_value = ("Hello!", "ai_generated")
        mock_messenger.send_text.return_value = "msg_123"
        
        await scheduler._send_message("morning", date.today())
        
        # Should call composer and messenger
        mock_composer.compose_message.assert_called_once()
        mock_messenger.send_text.assert_called_once()
        mock_storage.record_message_sent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self, scheduler, mock_composer, mock_messenger, mock_storage):
        """Test message sending failure."""
        mock_composer.compose_message.return_value = ("Hello!", "ai_generated")
        mock_messenger.send_text.return_value = None
        
        await scheduler._send_message("morning", date.today())
        
        # Should still record the attempt
        mock_storage.record_message_sent.assert_called_once()
        args = mock_storage.record_message_sent.call_args
        assert args[1]["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_send_message_now_success(self, scheduler, mock_composer, mock_messenger, mock_storage):
        """Test sending message now successfully."""
        mock_composer.compose_message.return_value = ("Hello!", "ai_generated")
        mock_messenger.send_text.return_value = "msg_123"
        
        success, message = await scheduler.send_message_now("morning")
        
        assert success is True
        assert "successfully" in message.lower()
    
    @pytest.mark.asyncio
    async def test_send_message_now_already_sent(self, scheduler, mock_storage):
        """Test sending message now when already sent."""
        mock_storage.is_message_sent.return_value = True
        
        success, message = await scheduler.send_message_now("morning")
        
        assert success is False
        assert "already sent" in message.lower()
    
    def test_get_todays_plan(self, scheduler):
        """Test getting today's plan."""
        plan = scheduler.get_todays_plan()
        
        assert "morning" in plan
        assert "flirty" in plan
        assert "night" in plan
        
        # Values should be time strings or None
        for time_str in plan.values():
            assert time_str is None or isinstance(time_str, str)
    
    def test_remove_todays_jobs(self, scheduler):
        """Test removing today's jobs."""
        # Add a mock job
        mock_job = MagicMock()
        mock_job.id = f"{date.today().isoformat()}_morning"
        
        # Mock both get_jobs and remove_job methods
        with patch.object(scheduler.scheduler, 'get_jobs', return_value=[mock_job]), \
             patch.object(scheduler.scheduler, 'remove_job') as mock_remove:
            scheduler._remove_todays_jobs()
            
            # Should call remove_job
            mock_remove.assert_called_once_with(mock_job.id)


class TestTimeWindowValidation:
    """Test time window validation utilities."""
    
    def test_is_within_time_window_normal(self):
        """Test normal time window validation."""
        from utils import is_within_time_window
        
        start = time(9, 0)
        end = time(17, 0)
        
        # Within window
        assert is_within_time_window(time(12, 0), start, end) is True
        assert is_within_time_window(time(9, 0), start, end) is True
        assert is_within_time_window(time(17, 0), start, end) is True
        
        # Outside window
        assert is_within_time_window(time(8, 0), start, end) is False
        assert is_within_time_window(time(18, 0), start, end) is False
    
    def test_is_within_time_window_spanning_midnight(self):
        """Test time window validation spanning midnight."""
        from utils import is_within_time_window
        
        start = time(22, 0)
        end = time(6, 0)
        
        # Within window (spans midnight)
        assert is_within_time_window(time(23, 0), start, end) is True
        assert is_within_time_window(time(2, 0), start, end) is True
        assert is_within_time_window(time(22, 0), start, end) is True
        assert is_within_time_window(time(6, 0), start, end) is True
        
        # Outside window
        assert is_within_time_window(time(12, 0), start, end) is False
        assert is_within_time_window(time(8, 0), start, end) is False
