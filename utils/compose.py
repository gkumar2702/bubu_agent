"""Message composition and text generation for Bubu Agent."""

import random
from datetime import date
from typing import List, Optional, Tuple

from .config import config
from providers.huggingface_llm import HuggingFaceLLM
from .utils import (
    SeededRandom, count_emojis, get_date_seed, get_logger,
    truncate_text, validate_message_content
)

logger = get_logger(__name__)


class MessageComposer:
    """Handles message composition and text generation."""
    
    def __init__(self, llm: HuggingFaceLLM):
        self.llm = llm
        self.storage = None  # Will be set by scheduler
    
    def set_storage(self, storage):
        """Set storage instance for idempotency checks."""
        self.storage = storage
    
    async def compose_message(
        self,
        message_type: str,
        date_obj: date,
        force_fallback: bool = False
    ) -> Tuple[str, str]:
        """
        Compose a message for the given type and date.
        
        Args:
            message_type: Type of message (morning, flirty, night)
            date_obj: Date for the message
            force_fallback: Force use of fallback templates
            
        Returns:
            Tuple of (message_text, status)
        """
        try:
            # Check if message already sent
            if self.storage and self.storage.is_message_sent(date_obj, message_type):
                logger.info(
                    "Message already sent for this date and slot",
                    date=date_obj.isoformat(),
                    slot=message_type
                )
                return "", "already_sent"
            
            # Get signature closer
            closer = self._get_signature_closer(date_obj)
            
            if force_fallback:
                message = self._get_fallback_message(message_type, closer)
                return message, "fallback"
            
            # Try AI generation first
            message = await self._generate_ai_message(message_type, closer, date_obj)
            
            if message:
                # Validate and clean the message
                is_valid, validation_msg = validate_message_content(
                    message,
                    config.get_general_setting("max_message_length", 300)
                )
                
                if is_valid:
                    return message, "ai_generated"
                else:
                    logger.warning(
                        "AI generated message failed validation, using fallback",
                        validation_msg=validation_msg,
                        message_type=message_type
                    )
            
            # Fallback to template
            message = self._get_fallback_message(message_type, closer)
            return message, "fallback"
            
        except Exception as e:
            logger.error(
                "Error composing message",
                message_type=message_type,
                date=date_obj.isoformat(),
                error=str(e)
            )
            # Emergency fallback
            closer = self._get_signature_closer(date_obj)
            message = self._get_fallback_message(message_type, closer)
            return message, "error_fallback"
    
    async def _generate_ai_message(
        self,
        message_type: str,
        closer: str,
        date_obj: date
    ) -> Optional[str]:
        """Generate message using AI."""
        try:
            # Get prompt templates
            system_prompt = config.get_prompt_template(message_type, "system")
            user_prompt = config.get_prompt_template(message_type, "user")
            
            if not system_prompt or not user_prompt:
                logger.warning(
                    "Missing prompt templates for message type",
                    message_type=message_type
                )
                return None
            
            # Replace placeholders
            replacements = {
                "GF_NAME": config.settings.gf_name,
                "DAILY_FLIRTY_TONE": config.settings.daily_flirty_tone,
                "closer": closer
            }
            
            for key, value in replacements.items():
                system_prompt = system_prompt.replace(f"{{{key}}}", value)
                user_prompt = user_prompt.replace(f"{{{key}}}", value)
            
            # Get generation parameters
            max_tokens = config.get_hf_setting("max_new_tokens", 150)
            temperature = config.get_hf_setting("temperature", 0.8)
            top_p = config.get_hf_setting("top_p", 0.9)
            do_sample = config.get_hf_setting("do_sample", True)
            
            # Generate text
            generated_text = await self.llm.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample
            )
            
            if not generated_text:
                return None
            
            # Clean and format the message
            message = self._clean_generated_text(generated_text, closer)
            
            # Final validation
            max_length = config.get_general_setting("max_message_length", 300)
            if len(message) > max_length:
                message = truncate_text(message, max_length)
            
            return message
            
        except Exception as e:
            logger.error(
                "Error generating AI message",
                message_type=message_type,
                error=str(e)
            )
            return None
    
    def _get_fallback_message(self, message_type: str, closer: str) -> str:
        """Get a fallback message from templates."""
        templates = config.get_fallback_templates(message_type)
        
        if not templates:
            # Emergency fallback
            return f"Hello {config.settings.gf_name}! {closer}"
        
        # Use seeded random for consistent selection per day
        seed = get_date_seed(date.today())
        rng = SeededRandom(seed)
        
        template = rng.choice(templates)
        return template.format(
            GF_NAME=config.settings.gf_name,
            closer=closer
        )
    
    def _get_signature_closer(self, date_obj: date) -> str:
        """Get a signature closer for the date."""
        closers = config.get_signature_closers()
        
        if not closers:
            return "— bubu"
        
        # Use seeded random for consistent selection per day
        seed = get_date_seed(date_obj)
        rng = SeededRandom(seed)
        
        return rng.choice(closers)
    
    def _clean_generated_text(self, text: str, closer: str) -> str:
        """Clean and format generated text."""
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove the closer if it's already in the text
        if closer in text:
            text = text.replace(closer, "").strip()
        
        # Add the closer
        text = f"{text} {closer}"
        
        # Check emoji count
        max_emojis = config.get_general_setting("max_emojis", 3)
        emoji_count = count_emojis(text)
        
        if emoji_count > max_emojis:
            # Simple emoji reduction (remove excess emojis)
            import re
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"
                "\U0001F300-\U0001F5FF"
                "\U0001F680-\U0001F6FF"
                "\U0001F1E0-\U0001F1FF"
                "\U00002702-\U000027B0"
                "\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE
            )
            emojis = emoji_pattern.findall(text)
            if len(emojis) > max_emojis:
                # Remove excess emojis from the end
                for emoji in emojis[max_emojis:]:
                    text = text.replace(emoji, "", 1)
        
        return text.strip()
    
    def get_message_preview(
        self,
        message_type: str,
        options: Optional[dict] = None
    ) -> str:
        """Get a preview of a message without sending."""
        try:
            options = options or {}
            
            # Handle randomization
            if options.get("randomize") and options.get("seed") is not None:
                # Use the provided seed for consistent randomization
                seed = options["seed"]
                rng = SeededRandom(seed)
                
                # Get fallback templates and pick one randomly
                templates = config.get_fallback_templates(message_type)
                if templates:
                    template = rng.choice(templates)
                    closer = rng.choice(config.get_signature_closers() or ["— bubu"])
                    return template.format(
                        GF_NAME=config.settings.gf_name,
                        closer=closer
                    )
            
            # Default behavior
            closer = self._get_signature_closer(date.today())
            
            if options and options.get("use_fallback", False):
                return self._get_fallback_message(message_type, closer)
            
            # For preview, we'll use fallback templates
            # In a real implementation, you might want to generate AI previews
            return self._get_fallback_message(message_type, closer)
            
        except Exception as e:
            logger.error(
                "Error generating message preview",
                message_type=message_type,
                error=str(e)
            )
            return f"Error generating preview for {message_type} message"
    
    def get_fallback_templates(self, message_type: str) -> List[str]:
        """Get fallback templates for a message type."""
        try:
            return config.get_fallback_templates(message_type)
        except Exception as e:
            logger.error(
                "Error getting fallback templates",
                message_type=message_type,
                error=str(e)
            )
            return []


def create_message_composer() -> MessageComposer:
    """Create a message composer instance."""
    settings = config.settings
    
    llm = HuggingFaceLLM(
        api_key=settings.hf_api_key,
        model_id=settings.hf_model_id,
        timeout=config.get_hf_setting("timeout_seconds", 30),
        max_retries=config.get_hf_setting("max_retries", 3)
    )
    
    return MessageComposer(llm)
