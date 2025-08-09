"""Refactored message composition and text generation for Bubu Agent."""

from __future__ import annotations

import asyncio
import functools
import json
from datetime import date
from typing import Any, Dict, List, Optional

from .config_facade import ConfigFacadeImpl
from .storage import Storage
from .storage_protocol import StorageProtocolImpl
from .types import (
    ConfigFacade, EMOJI_PATTERN, GenerationResult, LLMProtocol, LLMResult,
    MessageResult, MessageStatus, MessageType, NullStorage, StorageProtocol,
    SongRecommendation
)
from .utils import SeededRandom, get_date_seed, get_logger

# Import song recommender
try:
    from recommenders.hf_bollywood import create_recommender
    SONG_RECOMMENDER_AVAILABLE = True
except ImportError:
    SONG_RECOMMENDER_AVAILABLE = False
    logger = get_logger(__name__)
    logger.warning("Song recommender not available. Song recommendations will be disabled.")

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
        
        # Initialize song recommender if available
        self.song_recommender = None
        if SONG_RECOMMENDER_AVAILABLE:
            self._init_song_recommender()
    
    def _init_song_recommender(self) -> None:
        """Initialize the song recommender."""
        try:
            song_enabled = self.config.get_song_recommendation_setting("song_reco_enabled", False)
            if not song_enabled:
                logger.info("Song recommendations disabled in config")
                return
            
            catalog_path = self.config.get_song_recommendation_setting("song_catalog_path", "data/bollywood_songs.csv")
            embeddings_path = self.config.get_song_recommendation_setting("song_embeddings_path")
            faiss_index_path = self.config.get_song_recommendation_setting("song_faiss_index_path")
            embed_model = self.config.get_song_recommendation_setting("hf_embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
            cross_model = self.config.get_song_recommendation_setting("hf_cross_encoder", "cross-encoder/ms-marco-MiniLM-L-6-v2")
            
            self.song_recommender = create_recommender(
                catalog_path=catalog_path,
                embeddings_path=embeddings_path,
                faiss_index_path=faiss_index_path,
                embed_model=embed_model,
                cross_model=cross_model
            )
            
            if self.song_recommender:
                logger.info("Song recommender initialized successfully")
            else:
                logger.warning("Failed to initialize song recommender")
                
        except Exception as e:
            logger.error(f"Failed to initialize song recommender: {e}")
            self.song_recommender = None
    
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
                
                # Add song recommendation if available
                final_text = await self._add_song_recommendation(validated_text, message_type, date_obj)
                
                return MessageResult(
                    text=final_text,
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
            
            # Add song recommendation if available
            final_message = await self._add_song_recommendation(message, message_type, date_obj)
            
            return MessageResult(
                text=final_message,
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
            
            # Add song recommendation if available
            final_message = await self._add_song_recommendation(message, message_type, date_obj)
            
            return MessageResult(
                text=final_message,
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
    
    async def pick_song(
        self,
        message_type: MessageType,
        day_ctx: Dict[str, Any]
    ) -> Optional[SongRecommendation]:
        """Pick a song recommendation for the message type."""
        if not self.song_recommender:
            return None
        
        try:
            # Get recent song IDs to avoid repeats
            cache_days = self.config.get_song_recommendation_setting("song_cache_days", 30)
            recent_ids = self.storage.get_recent_song_ids(cache_days)
            logger.info(f"Recent IDs retrieved: {type(recent_ids)}, value: {recent_ids}")
            
            # Generate intent using LLM
            intent = await self._generate_song_intent(message_type)
            if not intent:
                return None
            
            # Build query text
            query_text = self._build_song_query(message_type, intent)
            
            # Get preferences
            preferences = self._get_song_preferences()
            
            # Get recommendation
            logger.info(f"Calling recommend_song with recent_ids: {type(recent_ids)}, value: {recent_ids}")
            song_dict = self.song_recommender.recommend_song(
                query_text=query_text,
                preferences=preferences,
                recent_ids=recent_ids
            )
            
            if song_dict:
                return SongRecommendation(
                    song_id=song_dict["song_id"],
                    title=song_dict["title"],
                    url=song_dict["url"]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to pick song: {e}")
            return None
    
    async def _generate_song_intent(self, message_type: MessageType) -> Optional[Dict[str, Any]]:
        """Generate song intent using LLM."""
        try:
            system_prompt = """You are a music concierge for Bollywood romance songs.

Message type: {message_type}
Vibe mapping:
- morning → soft, warm, motivational romance
- flirty → playful, upbeat, teasing
- night → calm, cozy, dreamy

Preferred languages: {language_prefs}
Region: {region}

Avoid explicit/breakup/sad themes.

Return JSON only:
{{ "keywords": [...], "allow_classic": true|false, "language_priority": [...], "disallow": [...] }}"""

            language_prefs = self.config.get_song_recommendation_setting("song_language_prefs", ["Hindi"])
            region = self.config.get_song_recommendation_setting("song_region_code", "IN")
            
            system_prompt = system_prompt.format(
                message_type=message_type.value,
                language_prefs=language_prefs,
                region=region
            )
            
            user_prompt = f"Generate song intent for {message_type.value} message"
            
            response = await self.llm.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_new_tokens=100,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
            
            if response:
                # Try to parse JSON from response
                try:
                    # Extract JSON from response (handle markdown code blocks)
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = response[json_start:json_end]
                        return json.loads(json_str)
                except (json.JSONDecodeError, ValueError):
                    logger.warning(f"Failed to parse song intent JSON: {response}")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate song intent: {e}")
            return None
    
    def _build_song_query(self, message_type: MessageType, intent: Dict[str, Any]) -> str:
        """Build query text for song search."""
        vibe_map = {
            MessageType.MORNING: "soft warm motivational romance",
            MessageType.FLIRTY: "playful upbeat teasing romantic",
            MessageType.NIGHT: "calm cozy dreamy romantic"
        }
        
        vibe = vibe_map.get(message_type, "romantic")
        keywords = intent.get("keywords", [])
        
        query_parts = [vibe] + keywords
        return " ".join(query_parts)
    
    def _get_song_preferences(self) -> Dict[str, Any]:
        """Get song preferences from config."""
        return {
            "language_priority": self.config.get_song_recommendation_setting("song_language_prefs", ["Hindi"]),
            "blacklist": self.config.get_song_recommendation_setting("song_blacklist_terms", []),
            "max_age_days": self.config.get_song_recommendation_setting("song_max_age_days", 36500)
        }
    
    def _format_song_line(self, message_type: MessageType, title: str, url: str) -> str:
        """Format song recommendation line."""
        templates = self.config.get_song_recommendation_setting("song_insertion_templates", {})
        template = templates.get(message_type.value, "This song made me think of us: {title} — {url}")
        
        return template.format(title=title.strip(), url=url)
    
    def _add_song_to_message(self, message: str, song: SongRecommendation, message_type: MessageType) -> str:
        """Add song recommendation to message."""
        song_line = self._format_song_line(message_type, song.title, song.url)
        
        # Check if adding song would exceed max length
        max_length = self.config.get_general_setting("max_message_length", 700)
        if len(message + "\n\n" + song_line) <= max_length:
            return message + "\n\n" + song_line
        else:
            # Trim main message to make room for song
            available_space = max_length - len(song_line) - 2  # 2 for newlines
            if available_space > 50:  # Ensure we have reasonable space
                return message[:available_space] + "...\n\n" + song_line
            else:
                # If not enough space, just return original message
                return message
    
    async def _add_song_recommendation(self, message: str, message_type: MessageType, date_obj: date) -> str:
        """Add song recommendation to message if available."""
        try:
            # Check if song recommendations are enabled
            song_enabled = self.config.get_song_recommendation_setting("song_reco_enabled", False)
            if not song_enabled or not self.song_recommender:
                return message
            
            # Pick a song
            day_ctx = {"date": date_obj.isoformat()}
            song = await self.pick_song(message_type, day_ctx)
            
            if song:
                # Add song to message
                final_message = self._add_song_to_message(message, song, message_type)
                
                # Record the song recommendation
                self.storage.record_song_recommendation(
                    date_obj=date_obj,
                    slot=message_type.value,
                    song_id=song.song_id,
                    song_title=song.title
                )
                
                logger.info(
                    "Added song recommendation to message",
                    song_id=song.song_id,
                    song_title=song.title,
                    message_type=message_type.value
                )
                
                return final_message
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to add song recommendation: {e}")
            return message


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
