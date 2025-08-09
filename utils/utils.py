"""Utility functions for Bubu Agent."""

import logging
import os
import random
import re
from datetime import datetime, time
from typing import Optional

import structlog
from pytz import timezone


def setup_logging(log_level: str = "INFO") -> None:
    """Setup structured logging with structlog."""
    logging.basicConfig(
        format="%(message)s",
        stream=open(os.devnull, "w") if log_level == "SILENT" else None,
        level=getattr(logging, log_level.upper()),
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def mask_phone_number(phone: str) -> str:
    """Mask phone number for logging (show only last 4 digits)."""
    if not phone or len(phone) < 4:
        return "***"
    return f"{'*' * (len(phone) - 4)}{phone[-4:]}"


def scrub_secrets_from_logs(data: dict) -> dict:
    """Remove sensitive information from logs."""
    scrubbed = data.copy()
    sensitive_keys = [
        'hf_api_key', 'twilio_auth_token', 'meta_access_token',
        'api_bearer_token', 'password', 'token', 'secret'
    ]
    
    for key in sensitive_keys:
        if key in scrubbed:
            scrubbed[key] = '***'
    
    # Mask phone numbers
    for key in ['gf_whatsapp_number', 'sender_whatsapp_number', 'twilio_whatsapp_from']:
        if key in scrubbed and scrubbed[key]:
            scrubbed[key] = mask_phone_number(scrubbed[key])
    
    return scrubbed


class SeededRandom:
    """A seedable random number generator for deterministic testing."""
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self._rng = random.Random(seed)
    
    def choice(self, seq):
        """Choose a random element from a sequence."""
        return self._rng.choice(seq)
    
    def randint(self, a: int, b: int) -> int:
        """Generate a random integer between a and b (inclusive)."""
        return self._rng.randint(a, b)
    
    def random(self) -> float:
        """Generate a random float between 0.0 and 1.0."""
        return self._rng.random()
    
    def shuffle(self, seq):
        """Shuffle a sequence in place."""
        self._rng.shuffle(seq)
        return seq


def get_date_seed(date_obj: datetime) -> int:
    """Generate a seed from a date for deterministic randomization."""
    return int(date_obj.strftime("%Y%m%d"))


def get_timezone_aware_datetime(dt: datetime, tz_name: str) -> datetime:
    """Convert datetime to timezone-aware datetime."""
    tz = timezone(tz_name)
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    else:
        dt = dt.astimezone(tz)
    return dt


def is_within_time_window(current_time: time, start_time: time, end_time: time) -> bool:
    """Check if current time is within a time window."""
    if start_time <= end_time:
        return start_time <= current_time <= end_time
    else:  # Window spans midnight
        return current_time >= start_time or current_time <= end_time


def count_emojis(text: str) -> int:
    """Count emojis in text using Unicode emoji patterns."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    return len(emoji_pattern.findall(text))


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max_length, preserving word boundaries."""
    if len(text) <= max_length:
        return text
    
    # Try to truncate at word boundary
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If we can find a good word boundary
        truncated = truncated[:last_space]
    
    return truncated + suffix


def validate_message_content(text: str, max_length: int = 300) -> tuple[bool, str]:
    """Validate message content for length and basic safety."""
    if not text or not text.strip():
        return False, "Message is empty"
    
    if len(text) > max_length:
        return False, f"Message too long ({len(text)} chars, max {max_length})"
    
    # Basic content safety checks
    unsafe_patterns = [
        r'\b(medical|health|doctor|medicine|treatment)\b',
        r'\b(money|finance|investment|stock|crypto)\b',
        r'\b(political|election|vote|government)\b',
        r'\b(religious|god|prayer|church|temple)\b',
    ]
    
    for pattern in unsafe_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"Message contains forbidden content: {pattern}"
    
    return True, "OK"


def format_time_for_display(dt: datetime, tz_name: str) -> str:
    """Format datetime for display in specified timezone."""
    tz = timezone(tz_name)
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    else:
        dt = dt.astimezone(tz)
    
    return dt.strftime("%I:%M %p %Z")


# Global logger instance
logger = get_logger(__name__)
