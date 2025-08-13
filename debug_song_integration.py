#!/usr/bin/env python3
"""
Debug script to test song recommendation integration step by step.
"""

import sys
import os
from datetime import date

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.compose_refactored import create_message_composer_refactored
from utils.types import MessageType
from providers.huggingface_llm import HuggingFaceLLM
from utils.config import config

def debug_song_integration():
    """Debug the song recommendation integration step by step."""
    print("🔍 Debugging Song Recommendation Integration")
    print("=" * 50)
    
    try:
        # Create LLM instance
        print("📡 Creating HuggingFace LLM instance...")
        llm = HuggingFaceLLM(
            api_key=config.settings.hf_api_key,
            model_id=config.settings.hf_model_id
        )
        
        # Create message composer
        print("🎵 Creating message composer...")
        composer = create_message_composer_refactored(llm)
        
        # Test song recommender initialization
        print("\n🎵 Testing song recommender initialization...")
        if composer.song_recommender:
            print("✅ Song recommender initialized")
        else:
            print("❌ Song recommender not initialized")
            return
        
        # Test song recommendation
        print("\n🎵 Testing song recommendation...")
        try:
            song = composer._pick_song_sync(MessageType.MORNING, {"date": date.today().isoformat()})
            if song:
                print(f"✅ Song recommendation: {song.title}")
                print(f"   URL: {song.url}")
            else:
                print("❌ No song recommendation generated")
                return
        except Exception as e:
            print(f"❌ Error getting song recommendation: {e}")
            return
        
        # Test message preview with song recommendation
        print("\n📝 Testing message preview with song recommendation...")
        try:
            message = composer.get_message_preview(MessageType.MORNING)
            print(f"✅ Message preview generated")
            print(f"   Message: {message[:100]}...")
            print(f"   Length: {len(message)} chars")
            
            # Check if song is included
            if song.title in message:
                print("✅ Song recommendation included in message")
            else:
                print("❌ Song recommendation NOT included in message")
                print("   This suggests the integration is not working properly")
                
        except Exception as e:
            print(f"❌ Error generating message preview: {e}")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_song_integration()
