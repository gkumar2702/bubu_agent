#!/usr/bin/env python3
"""Demo script for Bollywood song recommendation system."""

import asyncio
import logging
from datetime import date
from unittest.mock import Mock

from utils.types import MessageType, SongRecommendation
from recommenders.hf_bollywood import BollywoodSongRecommender
import pandas as pd
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_demo_catalog():
    """Create a demo song catalog."""
    return pd.DataFrame({
        'song_id': ['B001', 'B002', 'B003', 'B004', 'B005'],
        'title': ['Tum Hi Ho', 'Pehla Nasha', 'Tere Sang Yaara', 'Kal Ho Naa Ho', 'Tum Mile'],
        'artist': ['Arijit Singh', 'Udit Narayan', 'Rahat Fateh Ali Khan', 'Shankar Mahadevan', 'Atif Aslam'],
        'year': [2013, 1992, 2016, 2003, 2009],
        'language': ['Hindi', 'Hindi', 'Hindi', 'Hindi', 'Hindi'],
        'moods': ['romantic', 'romantic', 'romantic', 'romantic', 'romantic'],
        'themes': ['longing', 'first_love', 'devotion', 'melancholy', 'reunion'],
        'url': [
            'https://www.youtube.com/watch?v=foE1mO2yM04',
            'https://www.youtube.com/watch?v=foE1mO2yM04',
            'https://www.youtube.com/watch?v=foE1mO2yM04',
            'https://www.youtube.com/watch?v=foE1mO2yM04',
            'https://www.youtube.com/watch?v=foE1mO2yM04'
        ],
        'duration_sec': [280, 320, 310, 350, 290],
        'views': [150000000, 45000000, 85000000, 120000000, 95000000],
        'is_explicit': [False, False, False, False, False]
    })


def create_demo_embeddings(catalog_size=5):
    """Create demo embeddings."""
    return np.random.rand(catalog_size, 384).astype('float32')


class MockLLM:
    """Mock LLM for testing."""
    
    async def generate_text(self, system_prompt, user_prompt, **kwargs):
        """Mock text generation."""
        return '{"keywords": ["romantic", "soft", "duet"], "allow_classic": true, "language_priority": ["Hindi"], "disallow": ["explicit"]}'


async def demo_song_recommendation():
    """Demo the song recommendation system."""
    print("🎵 Bollywood Song Recommendation Demo")
    print("=" * 50)
    
    # Create demo data
    catalog = create_demo_catalog()
    embeddings = create_demo_embeddings(len(catalog))
    
    print(f"📊 Created demo catalog with {len(catalog)} songs")
    print(f"🔢 Generated embeddings with shape {embeddings.shape}")
    
    # Create recommender
    recommender = BollywoodSongRecommender(
        catalog_df=catalog,
        emb_matrix=embeddings
    )
    
    if not hasattr(recommender, 'st') or recommender.st is None:
        print("⚠️  Sentence transformers not available. Using fallback mode.")
        print("   Install with: pip install sentence-transformers")
        print("\n📋 Demo would show:")
        print("   - Morning: 'This song made me think of us: Tum Hi Ho — https://youtube.com/...'")
        print("   - Flirty: 'Thinking of you… and this song: Pehla Nasha — https://youtube.com/...'")
        print("   - Night: 'Before you sleep, this one for us: Tere Sang Yaara — https://youtube.com/...'")
        return
    
    print("🤖 Initialized song recommender")
    
    # Test different message types
    message_types = [MessageType.MORNING, MessageType.FLIRTY, MessageType.NIGHT]
    
    for msg_type in message_types:
        print(f"\n📝 Testing {msg_type.value.upper()} message type:")
        print("-" * 30)
        
        # Mock preferences
        preferences = {
            "language_priority": ["Hindi"],
            "blacklist": ["explicit"],
            "max_age_days": 36500
        }
        
        # Mock recent song IDs
        recent_ids = set()
        
        # Test query
        query_text = f"romantic {msg_type.value} bollywood song"
        print(f"🔍 Query: '{query_text}'")
        
        # Get recommendation
        song_dict = recommender.recommend_song(
            query_text=query_text,
            preferences=preferences,
            recent_ids=recent_ids
        )
        
        if song_dict:
            song = SongRecommendation(
                song_id=song_dict["song_id"],
                title=song_dict["title"],
                url=song_dict["url"]
            )
            
            print(f"✅ Recommended: {song.title}")
            print(f"🎤 Artist: {catalog[catalog['song_id'] == song.song_id]['artist'].iloc[0]}")
            print(f"📅 Year: {catalog[catalog['song_id'] == song.song_id]['year'].iloc[0]}")
            print(f"🎵 URL: {song.url}")
            
            # Show how it would appear in a message
            templates = {
                "morning": "This song made me think of us: {title} — {url}",
                "flirty": "Thinking of you… and this song: {title} — {url}",
                "night": "Before you sleep, this one for us: {title} — {url}"
            }
            
            template = templates.get(msg_type.value, "This song made me think of us: {title} — {url}")
            song_line = template.format(title=song.title, url=song.url)
            
            print(f"💌 Message addition: {song_line}")
        else:
            print("❌ No song recommended")
    
    print("\n🎉 Demo completed!")
    print("\nTo use this in Bubu Agent:")
    print("1. Install dependencies: pip install sentence-transformers pandas numpy faiss-cpu")
    print("2. Generate embeddings: python scripts/generate_embeddings.py")
    print("3. Enable in config.yaml: song_reco_enabled: true")
    print("4. Restart Bubu Agent")


if __name__ == "__main__":
    asyncio.run(demo_song_recommendation())
