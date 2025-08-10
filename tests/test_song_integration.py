#!/usr/bin/env python3
"""Test script to verify song recommendation integration."""

import asyncio
import logging
from datetime import date
from utils.types import MessageType
from utils.compose_refactored import create_message_composer_refactored
from utils.storage import Storage
from recommenders.hf_bollywood import create_recommender

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockLLM:
    """Mock LLM for testing."""
    
    async def generate_text(self, system_prompt, user_prompt, **kwargs):
        """Mock text generation."""
        if "song intent" in user_prompt.lower():
            return '{"keywords": ["romantic", "soft", "duet"], "allow_classic": true, "language_priority": ["Hindi"], "disallow": ["explicit"]}'
        else:
            return "Good morning! This is a test message with love and warmth. — your bubu gourav"


async def test_song_integration():
    """Test the song recommendation integration."""
    print("🎵 Testing Song Recommendation Integration")
    print("=" * 50)
    
    # Create storage
    storage = Storage()
    
    # Create mock LLM
    llm = MockLLM()
    
    # Create message composer
    composer = create_message_composer_refactored(llm, storage)
    
    print(f"✅ Message composer created")
    print(f"🎵 Song recommender available: {composer.song_recommender is not None}")
    
    if composer.song_recommender:
        print(f"📊 Song catalog size: {len(composer.song_recommender.df)}")
        print(f"🔢 Embeddings shape: {composer.song_recommender.emb.shape if composer.song_recommender.emb is not None else 'None'}")
    
    # Test message composition for each type
    message_types = [MessageType.MORNING, MessageType.FLIRTY, MessageType.NIGHT]
    
    # Use tomorrow's date to avoid "already sent" status
    test_date = date(2025, 8, 10)
    
    # Test song recommendation directly
    print("\n🎵 Testing song recommendation directly:")
    print("-" * 30)
    
    # Get recent song IDs
    recent_ids = storage.get_recent_song_ids(30)
    print(f"Recent song IDs: {recent_ids}")
    
    # Test pick_song method
    day_ctx = {"date": test_date.isoformat()}
    song = await composer.pick_song(MessageType.MORNING, day_ctx)
    if song:
        print(f"✅ Song picked: {song.title}")
    else:
        print("❌ No song picked")
    
    for msg_type in message_types:
        print(f"\n📝 Testing {msg_type.value.upper()} message:")
        print("-" * 30)
        
        # Compose message
        result = await composer.compose_message(msg_type, test_date)
        
        print(f"Status: {result.status.value}")
        print(f"Message: {result.text}")
        
        # Check if song was added
        if "This song made me think of us:" in result.text or "Thinking of you… and this song:" in result.text or "Before you sleep, this one for us:" in result.text:
            print("✅ Song recommendation found in message!")
        else:
            print("❌ No song recommendation found")
    
    print("\n🎉 Integration test completed!")


if __name__ == "__main__":
    asyncio.run(test_song_integration())
