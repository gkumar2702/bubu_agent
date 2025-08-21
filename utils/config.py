"""Configuration management for Bubu Agent."""

import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Core settings
    enabled: bool = Field(default=True, description="Enable/disable the agent")
    gf_name: str = Field(..., description="Girlfriend's name for personalization")
    gf_whatsapp_number: str = Field(..., description="Girlfriend's WhatsApp number (E.164)")
    sender_whatsapp_number: str = Field(..., description="Sender's WhatsApp number (E.164)")
    
    # Hugging Face settings
    hf_api_key: str = Field(..., description="Hugging Face API key")
    hf_model_id: str = Field(default="microsoft/DialoGPT-medium", description="Hugging Face model ID")
    
    # WhatsApp provider settings
    whatsapp_provider: str = Field(default="twilio", description="WhatsApp provider (twilio/meta/ultramsg)")
    
    # Twilio settings
    twilio_account_sid: Optional[str] = Field(None, description="Twilio account SID")
    twilio_auth_token: Optional[str] = Field(None, description="Twilio auth token")
    twilio_whatsapp_from: Optional[str] = Field(None, description="Twilio WhatsApp from number")
    
    # Meta settings
    meta_access_token: Optional[str] = Field(None, description="Meta access token")
    meta_phone_number_id: Optional[str] = Field(None, description="Meta phone number ID")
    
    # Ultramsg settings
    ultramsg_api_key: Optional[str] = Field(None, description="Ultramsg API key")
    ultramsg_instance_id: Optional[str] = Field(None, description="Ultramsg instance ID")
    
    # Timezone and scheduling
    timezone: str = Field(default="Asia/Kolkata", description="Timezone for scheduling")
    daily_flirty_tone: str = Field(default="playful", description="Daily flirty tone")
    
    # API security
    api_bearer_token: str = Field(..., description="Bearer token for API authentication")
    
    # Optional skip dates
    skip_dates: Optional[str] = Field(None, description="Comma-separated skip dates (YYYY-MM-DD)")
    
    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    
    @field_validator('whatsapp_provider')
    @classmethod
    def validate_whatsapp_provider(cls, v):
        if v not in ['twilio', 'meta', 'ultramsg']:
            raise ValueError('whatsapp_provider must be either "twilio", "meta", or "ultramsg"')
        return v
    
    @field_validator('daily_flirty_tone')
    @classmethod
    def validate_flirty_tone(cls, v):
        if v not in ['playful', 'romantic', 'witty']:
            raise ValueError('daily_flirty_tone must be one of: playful, romantic, witty')
        return v
    
    @field_validator('gf_whatsapp_number', 'sender_whatsapp_number')
    @classmethod
    def validate_phone_number(cls, v):
        if not v.startswith('+'):
            raise ValueError('Phone numbers must be in E.164 format (start with +)')
        return v
    
    def get_skip_dates_list(self) -> List[date]:
        """Parse skip_dates string into a list of date objects."""
        if not self.skip_dates:
            return []
        
        dates = []
        for date_str in self.skip_dates.split(','):
            try:
                dates.append(date.fromisoformat(date_str.strip()))
            except ValueError:
                continue
        return dates
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


class ConfigManager:
    """Manages application configuration from YAML and environment."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.settings = Settings()
        self.yaml_config = self._load_yaml_config()
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            return {}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load config.yaml: {e}")
            return {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support."""
        keys = key.split('.')
        value = self.yaml_config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_fallback_templates(self, message_type: str) -> List[str]:
        """Get fallback templates for a message type."""
        templates = self.get(f'fallback_templates.{message_type}', [])
        return templates if isinstance(templates, list) else []
    
    def get_signature_closers(self) -> List[str]:
        """Get signature closers."""
        closers = self.get('signature_closers', [])
        return closers if isinstance(closers, list) else []
    
    def get_prompt_template(self, message_type: str, template_type: str) -> str:
        """Get prompt template for a message type."""
        return self.get(f'prompt_templates.{message_type}.{template_type}', '')
    
    def get_general_setting(self, key: str, default: Any = None) -> Any:
        """Get general setting."""
        return self.get(f'general.{key}', default)
    
    def get_hf_setting(self, key: str, default: Any = None) -> Any:
        """Get Hugging Face setting."""
        return self.get(f'huggingface.{key}', default)
    
    def get_content_policy(self) -> Dict[str, Any]:
        """Get content policy settings."""
        return self.get('content_policy', {})
    
    def get_tone_setting(self, key: str, default: Any = None) -> Any:
        """Get tone setting."""
        return self.get(f'tone.{key}', default)
    
    def get_bollywood_quotes(self) -> List[str]:
        """Get Bollywood romantic quotes."""
        quotes = self.get('bollywood_quotes', [])
        return quotes if isinstance(quotes, list) else []
    
    def get_cheesy_lines(self) -> List[str]:
        """Get cheesy romantic lines."""
        lines = self.get('cheesy_lines', [])
        return lines if isinstance(lines, list) else []
    
    def get_song_recommendation_setting(self, key: str, default: Any = None) -> Any:
        """Get song recommendation setting from config."""
        return self.get(f'song_recommendation.{key}', default)


# Global configuration instance
config = ConfigManager()
