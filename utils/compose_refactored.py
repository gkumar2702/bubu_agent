"""Refactored message composition and text generation for Bubu Agent."""

from __future__ import annotations

import asyncio
import functools
from datetime import date
from typing import Any, Dict, List, Optional

from .config_facade import ConfigFacadeImpl
from .storage import Storage
from .storage_protocol import StorageProtocolImpl
from .types import (
    ConfigFacade, EMOJI_PATTERN, GenerationResult, LLMProtocol, LLMResult,
    MessageResult, MessageStatus, MessageType, NullStorage, StorageProtocol
)
from .utils import SeededRandom, get_date_seed, get_logger

logger = get_logger(__name__)


class MessageComposer:
    """Handles message composition and text generation with proper typing and error handling."""
    
    def __init__(
        self,
        llm: LLMProtocol,
        config: ConfigFacade,
        storage: StorageProtocol = NullStorage()
    ):
        """Initialize the message composer.
        
        Args:
            llm: LLM protocol implementation for text generation
            config: Configuration facade for accessing settings
            storage: Storage protocol for idempotency checks
        """
        self.llm = llm
        self.config = config
        self.storage = storage
    
    async def compose_message(
        self,
        message_type: MessageType,
        date_obj: date,
        force_fallback: bool = False
    ) -> MessageResult:
        """Compose a message for the given type and date.
        
        Args:
            message_type: Type of message to compose
            date_obj: Date for the message
            force_fallback: Force use of fallback templates
            
        Returns:
            MessageResult containing the composed message and status
        """
        try:
            # Check if message already sent
            if self.storage.is_message_sent(date_obj, message_type):
                logger.info(
                    "Message already sent for this date and slot",
                    date=date_obj.isoformat(),
                    slot=message_type.value
                )
                return MessageResult(
                    text="",
                    status=MessageStatus.ALREADY_SENT,
                    details={"date": date_obj.isoformat(), "message_type": message_type.value}
                )
            
            # Get signature closer
            closer = self._get_signature_closer(date_obj)
            
            if force_fallback:
                message = self._get_fallback_message(message_type, closer, date_obj)
                return MessageResult(
                    text=message,
                    status=MessageStatus.FALLBACK,
                    details={"reason": "forced_fallback"}
                )
            
            # Try AI generation first
            generation_result = await self._generate_ai_message(message_type, closer, date_obj)
            
            if generation_result.reason == LLMResult.OK and generation_result.text:
                # Validate and clean the message
                validated_text = self._validate_and_trim(
                    generation_result.text,
                    self.config.get_general_setting("max_message_length", 700),
                    self.config.get_general_setting("max_emojis", 5)
                )
                
                return MessageResult(
                    text=validated_text,
                    status=MessageStatus.AI_GENERATED,
                    details=generation_result.details
                )
            else:
                logger.warning(
                    "AI generation failed, using fallback",
                    reason=generation_result.reason.value,
                    message_type=message_type.value,
                    details=generation_result.details
                )
            
            # Fallback to template
            message = self._get_fallback_message(message_type, closer, date_obj)
            return MessageResult(
                text=message,
                status=MessageStatus.FALLBACK,
                details={"reason": "ai_generation_failed"}
            )
            
        except Exception as e:
            logger.exception(
                "Error composing message",
                message_type=message_type.value,
                date=date_obj.isoformat()
            )
            # Emergency fallback
            closer = self._get_signature_closer(date_obj)
            message = self._get_fallback_message(message_type, closer, date_obj)
            return MessageResult(
                text=message,
                status=MessageStatus.ERROR_FALLBACK,
                details={"error": str(e)}
            )
    
    async def _generate_ai_message(
        self,
        message_type: MessageType,
        closer: str,
        date_obj: date
    ) -> GenerationResult:
        """Generate message using AI with proper error handling.
        
        Args:
            message_type: Type of message to generate
            closer: Signature closer to append
            date_obj: Date for the message
            
        Returns:
            GenerationResult containing the generated text and status
        """
        try:
            # Get prompt templates
            system_prompt = self.config.get_prompt_template(message_type, "system")
            user_prompt = self.config.get_prompt_template(message_type, "user")
            
            if not system_prompt or not user_prompt:
                return GenerationResult(
                    text=None,
                    reason=LLMResult.MISSING_PROMPTS,
                    details={"message_type": message_type.value}
                )
            
            # Get Bollywood quote and cheesy line for inspiration
            bollywood_quote = self._get_bollywood_quote(date_obj)
            cheesy_line = self._get_cheesy_line(date_obj)
            
            # Replace placeholders safely
            replacements = {
                "GF_NAME": self.config.gf_name,
                "DAILY_FLIRTY_TONE": self.config.daily_flirty_tone,
                "closer": closer
            }
            
            try:
                system_prompt = system_prompt.format_map(replacements)
                user_prompt = user_prompt.format_map(replacements)
            except KeyError as e:
                return GenerationResult(
                    text=None,
                    reason=LLMResult.MISSING_PROMPTS,
                    details={"missing_key": str(e)}
                )
            
            # Add Bollywood and cheesy inspiration to prompts
            if bollywood_quote:
                system_prompt += f"\n\nBollywood inspiration: '{bollywood_quote}'"
                user_prompt += f"\n\nFeel free to use the romantic style of this Bollywood quote as inspiration."
            
            if cheesy_line:
                system_prompt += f"\n\nCheesy line example: '{cheesy_line}'"
                user_prompt += f"\n\nYou can include cheesy romantic elements like this example for fun."
            
            # Get generation parameters
            max_tokens = self.config.get_hf_setting("max_new_tokens", 150)
            temperature = self.config.get_hf_setting("temperature", 0.8)
            top_p = self.config.get_hf_setting("top_p", 0.9)
            do_sample = self.config.get_hf_setting("do_sample", True)
            timeout = self.config.get_hf_setting("timeout_seconds", 30)
            
            # Generate text with timeout
            try:
                generated_text = await asyncio.wait_for(
                    self.llm.generate_text(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        max_new_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        do_sample=do_sample
                    ),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                return GenerationResult(
                    text=None,
                    reason=LLMResult.TIMEOUT,
                    details={"timeout_seconds": timeout}
                )
            
            if not generated_text:
                return GenerationResult(
                    text=None,
                    reason=LLMResult.EMPTY,
                    details={"message_type": message_type.value}
                )
            
            # Clean and format the message
            message = self._clean_generated_text(generated_text, closer)
            
            return GenerationResult(
                text=message,
                reason=LLMResult.OK,
                details={"message_type": message_type.value}
            )
            
        except Exception as e:
            logger.exception(
                "Error generating AI message",
                message_type=message_type.value
            )
            return GenerationResult(
                text=None,
                reason=LLMResult.EXCEPTION,
                details={"error": str(e)}
            )
    
    def _get_fallback_message(
        self,
        message_type: MessageType,
        closer: str,
        date_obj: date
    ) -> str:
        """Get a fallback message from templates.
        
        Args:
            message_type: Type of message
            closer: Signature closer
            date_obj: Date for deterministic selection
            
        Returns:
            Formatted fallback message
        """
        templates = self.config.get_fallback_templates(message_type)
        
        if not templates:
            # Emergency fallback
            return f"Hello {self.config.gf_name}! {closer}"
        
        # Use seeded random for consistent selection per day
        rng = self._rng(date_obj)
        template = rng.choice(templates)
        
        try:
            message = template.format(
                GF_NAME=self.config.gf_name,
                closer=closer
            )
        except KeyError:
            # Fallback if template has missing keys
            message = f"Hello {self.config.gf_name}! {closer}"
        
        # Occasionally add Bollywood quote or cheesy line (20% chance)
        if rng.random() < 0.2:
            bollywood_quote = self._get_bollywood_quote(date_obj)
            cheesy_line = self._get_cheesy_line(date_obj)
            
            if bollywood_quote and rng.random() < 0.5:
                # Add Bollywood quote before the closer
                message = message.replace(closer, f" 💕 '{bollywood_quote}' {closer}")
            elif cheesy_line:
                # Add cheesy line before the closer
                message = message.replace(closer, f" {cheesy_line} {closer}")
        
        return message
    
    def _get_signature_closer(self, date_obj: date) -> str:
        """Get a signature closer for the date.
        
        Args:
            date_obj: Date for deterministic selection
            
        Returns:
            Selected signature closer
        """
        closers = self.config.get_signature_closers()
        
        if not closers:
            return "— bubu"
        
        # Use seeded random for consistent selection per day
        rng = self._rng(date_obj)
        return rng.choice(closers)
    
    def _get_bollywood_quote(self, date_obj: date) -> Optional[str]:
        """Get a random Bollywood quote for inspiration.
        
        Args:
            date_obj: Date for deterministic selection
            
        Returns:
            Selected Bollywood quote or None
        """
        quotes = self.config.get_bollywood_quotes()
        
        if not quotes:
            return None
        
        # Use seeded random for consistent selection per day
        rng = self._rng(date_obj)
        return rng.choice(quotes)
    
    def _get_cheesy_line(self, date_obj: date) -> Optional[str]:
        """Get a random cheesy line for fun.
        
        Args:
            date_obj: Date for deterministic selection
            
        Returns:
            Selected cheesy line or None
        """
        lines = self.config.get_cheesy_lines()
        
        if not lines:
            return None
        
        # Use seeded random for consistent selection per day
        rng = self._rng(date_obj)
        return rng.choice(lines)
    
    def _clean_generated_text(self, text: str, closer: str) -> str:
        """Clean and format generated text.
        
        Args:
            text: Raw generated text
            closer: Signature closer to append
            
        Returns:
            Cleaned and formatted text
        """
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove the closer if it's already in the text
        if closer in text:
            text = text.replace(closer, "").strip()
        
        # Add the closer
        text = f"{text} {closer}"
        
        return text.strip()
    
    def _validate_and_trim(
        self,
        text: str,
        max_length: int,
        max_emojis: int
    ) -> str:
        """Validate and trim text to meet length and emoji constraints.
        
        Args:
            text: Text to validate and trim
            max_length: Maximum allowed length
            max_emojis: Maximum allowed emojis
            
        Returns:
            Validated and trimmed text
        """
        # Normalize whitespace
        text = " ".join(text.split())
        
        # Check emoji count and reduce if necessary
        emoji_count = len(EMOJI_PATTERN.findall(text))
        if emoji_count > max_emojis:
            emojis = EMOJI_PATTERN.findall(text)
            if len(emojis) > max_emojis:
                # Remove excess emojis from the end
                for emoji in emojis[max_emojis:]:
                    text = text.replace(emoji, "", 1)
        
        # Trim to max length if necessary
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + "..."
        
        return text.strip()
    
    def _rng(self, date_obj: date) -> SeededRandom:
        """Get seeded random number generator for the date.
        
        Args:
            date_obj: Date for seed generation
            
        Returns:
            Seeded random number generator
        """
        seed = get_date_seed(date_obj)
        return SeededRandom(seed)
    
    @functools.lru_cache(maxsize=128)
    def _get_cached_prompt_template(
        self,
        message_type: MessageType,
        template_type: str
    ) -> str:
        """Get cached prompt template.
        
        Args:
            message_type: Type of message
            template_type: Type of template (system/user)
            
        Returns:
            Cached prompt template
        """
        return self.config.get_prompt_template(message_type, template_type)
    
    def get_message_preview(
        self,
        message_type: MessageType,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get a preview of a message without sending.
        
        Args:
            message_type: Type of message to preview
            options: Optional configuration for preview
            
        Returns:
            Preview message text
        """
        try:
            options = options or {}
            
            # Handle randomization
            if options.get("randomize") and options.get("seed") is not None:
                # Use the provided seed for consistent randomization
                seed = options["seed"]
                rng = SeededRandom(seed)
                
                # Get fallback templates and pick one randomly
                templates = self.config.get_fallback_templates(message_type)
                if templates:
                    template = rng.choice(templates)
                    closer = rng.choice(self.config.get_signature_closers() or ["— bubu"])
                    try:
                        return template.format(
                            GF_NAME=self.config.gf_name,
                            closer=closer
                        )
                    except KeyError:
                        return f"Hello {self.config.gf_name}! {closer}"
            
            # Default behavior
            closer = self._get_signature_closer(date.today())
            
            if options and options.get("use_fallback", False):
                return self._get_fallback_message(message_type, closer, date.today())
            
            # For preview, we'll use fallback templates
            return self._get_fallback_message(message_type, closer, date.today())
            
        except Exception as e:
            logger.exception(
                "Error generating message preview",
                message_type=message_type.value
            )
            return f"Error generating preview for {message_type.value} message"
    
    def get_fallback_templates(self, message_type: MessageType) -> List[str]:
        """Get fallback templates for a message type.
        
        Args:
            message_type: Type of message
            
        Returns:
            List of fallback templates
        """
        try:
            return self.config.get_fallback_templates(message_type)
        except Exception as e:
            logger.exception(
                "Error getting fallback templates",
                message_type=message_type.value
            )
            return []


def create_message_composer_refactored(
    llm: LLMProtocol,
    storage: Optional[Storage] = None
) -> MessageComposer:
    """Create a refactored message composer instance.
    
    Args:
        llm: LLM protocol implementation
        storage: Optional storage instance for idempotency checks
        
    Returns:
        Configured MessageComposer instance
    """
    config_facade = ConfigFacadeImpl()
    storage_protocol = StorageProtocolImpl(storage) if storage else NullStorage()
    
    return MessageComposer(
        llm=llm,
        config=config_facade,
        storage=storage_protocol
    )
