"""Type definitions for Bubu Agent."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Protocol

# Precompile emoji regex at module load time
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"  # enclosed characters
    "]+",
    flags=re.UNICODE
)


class MessageType(Enum):
    """Message types for the Bubu Agent."""
    MORNING = "morning"
    FLIRTY = "flirty"
    NIGHT = "night"


class MessageStatus(Enum):
    """Status of message composition."""
    ALREADY_SENT = "already_sent"
    AI_GENERATED = "ai_generated"
    FALLBACK = "fallback"
    ERROR_FALLBACK = "error_fallback"


class LLMResult(Enum):
    """Result of LLM generation."""
    OK = "ok"
    MISSING_PROMPTS = "missing_prompts"
    EMPTY = "empty"
    EXCEPTION = "exception"
    TIMEOUT = "timeout"


@dataclass(slots=True)
class GenerationResult:
    """Result of AI message generation."""
    text: Optional[str]
    reason: LLMResult
    details: Dict[str, Any]


@dataclass(slots=True)
class MessageResult:
    """Result of message composition."""
    text: str
    status: MessageStatus
    details: Dict[str, Any]


@dataclass(slots=True)
class SongRecommendation:
    """Song recommendation result."""
    song_id: str
    title: str
    url: str


class StorageProtocol(Protocol):
    """Protocol for storage operations."""
    
    def is_message_sent(self, date_obj: date, message_type: MessageType) -> bool:
        """Check if a message was already sent for the given date and type."""
        ...
    
    def record_song_recommendation(self, date_obj: date, slot: str, song_id: str, song_title: str) -> None:
        """Record a song recommendation."""
        ...
    
    def get_recent_song_ids(self, days: int = 30) -> set[str]:
        """Get set of recently recommended song IDs."""
        ...


class LLMProtocol(Protocol):
    """Protocol for LLM operations."""
    
    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        do_sample: bool
    ) -> Optional[str]:
        """Generate text using the LLM."""
        ...


@dataclass(slots=True)
class ConfigFacade:
    """Facade for configuration access."""
    
    def get_general_setting(self, key: str, default: Any = None) -> Any:
        """Get general setting."""
        ...
    
    def get_hf_setting(self, key: str, default: Any = None) -> Any:
        """Get Hugging Face setting."""
        ...
    
    def get_prompt_template(self, message_type: MessageType, template_type: str) -> str:
        """Get prompt template."""
        ...
    
    def get_fallback_templates(self, message_type: MessageType) -> List[str]:
        """Get fallback templates."""
        ...
    
    def get_signature_closers(self) -> List[str]:
        """Get signature closers."""
        ...
    
    def get_bollywood_quotes(self) -> List[str]:
        """Get Bollywood quotes."""
        ...
    
    def get_cheesy_lines(self) -> List[str]:
        """Get cheesy lines."""
        ...
    
    def get_song_recommendation_setting(self, key: str, default: Any = None) -> Any:
        """Get song recommendation setting."""
        ...
    
    @property
    def gf_name(self) -> str:
        """Get girlfriend's name."""
        ...
    
    @property
    def daily_flirty_tone(self) -> str:
        """Get daily flirty tone."""
        ...


class NullStorage:
    """Null storage implementation that always returns False."""
    
    def is_message_sent(self, date_obj: date, message_type: MessageType) -> bool:
        """Always return False (no messages sent)."""
        return False
    
    def record_song_recommendation(self, date_obj: date, slot: str, song_id: str, song_title: str) -> None:
        """Do nothing for null storage."""
        pass
    
    def get_recent_song_ids(self, days: int = 30) -> set[str]:
        """Return empty set for null storage."""
        return set()
