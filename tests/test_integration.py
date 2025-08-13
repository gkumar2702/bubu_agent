#!/usr/bin/env python3
"""
Test script to verify Bollywood quotes, cheesy lines, and song recommendations integration.
"""

import asyncio
import sys
import os
from datetime import date

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.compose_refactored import create_message_composer_refactored
from utils.types import MessageType
from providers.huggingface_llm import HuggingFaceLLM
from utils.config import config

async def test_integration():
    """Test the integration of all features."""
    print("🧪 Testing Bubu Agent Integration")
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
        
        # Test Bollywood quotes
        print("\n🎬 Testing Bollywood quotes...")
        today = date.today()
        bollywood_quote = composer._get_bollywood_quote(today)
        if bollywood_quote:
            print(f"✅ Bollywood quote: {bollywood_quote}")
        else:
            print("❌ No Bollywood quote found")
        
        # Test cheesy lines
        print("\n💕 Testing cheesy lines...")
        cheesy_line = composer._get_cheesy_line(today)
        if cheesy_line:
            print(f"✅ Cheesy line: {cheesy_line}")
        else:
            print("❌ No cheesy line found")
        
        # Test song recommender
        print("\n🎵 Testing song recommender...")
        if composer.song_recommender:
            print("✅ Song recommender initialized")
            
            # Test song recommendation
            try:
                song = composer._pick_song_sync(MessageType.MORNING, {"date": today.isoformat()})
                if song:
                    print(f"✅ Song recommendation: {song.title}")
                    print(f"   URL: {song.url}")
                else:
                    print("❌ No song recommendation generated")
            except Exception as e:
                print(f"❌ Error getting song recommendation: {e}")
        else:
            print("❌ Song recommender not initialized")
        
        # Test AI message generation
        print("\n🤖 Testing AI message generation...")
        try:
            result = await composer.compose_message(MessageType.MORNING, today, force_fallback=False)
            if result.status.value == "ai_generated":
                print("✅ AI message generated successfully")
                print(f"   Message: {result.text[:100]}...")
                print(f"   Length: {len(result.text)} chars")
                print(f"   Status: {result.status.value}")
            else:
                print(f"⚠️ AI generation failed, using fallback: {result.status.value}")
                print(f"   Message: {result.text[:100]}...")
        except Exception as e:
            print(f"❌ Error generating AI message: {e}")
        
        # Test fallback message
        print("\n📋 Testing fallback message...")
        try:
            fallback_message = composer._get_fallback_message(MessageType.MORNING, "— bubu", today)
            if fallback_message:
                print("✅ Fallback message generated")
                print(f"   Message: {fallback_message[:100]}...")
                print(f"   Length: {len(fallback_message)} chars")
            else:
                print("❌ No fallback message generated")
        except Exception as e:
            print(f"❌ Error generating fallback message: {e}")
        
        print("\n🎉 Integration test completed!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_integration())
