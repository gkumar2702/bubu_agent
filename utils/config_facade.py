"""Configuration facade for Bubu Agent."""

from __future__ import annotations

from typing import Any, List

from .config import config
from .types import ConfigFacade, MessageType


class ConfigFacadeImpl(ConfigFacade):
    """Implementation of the configuration facade."""
    
    def get_general_setting(self, key: str, default: Any = None) -> Any:
        """Get general setting."""
        return config.get_general_setting(key, default)
    
    def get_hf_setting(self, key: str, default: Any = None) -> Any:
        """Get Hugging Face setting."""
        return config.get_hf_setting(key, default)
    
    def get_prompt_template(self, message_type: MessageType, template_type: str) -> str:
        """Get prompt template."""
        return config.get_prompt_template(message_type.value, template_type)
    
    def get_fallback_templates(self, message_type: MessageType) -> List[str]:
        """Get fallback templates."""
        return config.get_fallback_templates(message_type.value)
    
    def get_signature_closers(self) -> List[str]:
        """Get signature closers."""
        return config.get_signature_closers()
    
    def get_bollywood_quotes(self) -> List[str]:
        """Get Bollywood quotes."""
        return config.get_bollywood_quotes()
    
    def get_cheesy_lines(self) -> List[str]:
        """Get cheesy lines."""
        return config.get_cheesy_lines()
    
    @property
    def gf_name(self) -> str:
        """Get girlfriend's name."""
        return config.settings.gf_name
    
    @property
    def daily_flirty_tone(self) -> str:
        """Get daily flirty tone."""
        return config.settings.daily_flirty_tone
    
    def get_song_recommendation_setting(self, key: str, default: Any = None) -> Any:
        """Get song recommendation setting."""
        return config.get_song_recommendation_setting(key, default)
