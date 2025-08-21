#!/usr/bin/env python3
"""Test script for GPT-OSS-20B model integration."""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.llm_factory import create_llm
from utils.config import config

async def test_gpt_oss():
    """Test GPT-OSS model integration."""
    print("🧪 Testing GPT-OSS-20B Model Integration")
    print("=" * 50)
    
    try:
        # Create LLM instance
        print(f"📝 Creating LLM with model: {config.settings.hf_model_id}")
        llm = create_llm()
        print(f"✅ LLM created: {type(llm).__name__}")
        
        # Test simple generation
        print("\n🎭 Testing romantic message generation...")
        system_prompt = "You are a loving partner creating a romantic good morning message. Be warm, sweet, and include emojis."
        user_prompt = "Create a good morning message for Preeti Bubu that's romantic and includes Bollywood-style expressions."
        
        print("⏳ Generating message (this may take a while for first run)...")
        result = await llm.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_new_tokens=150,
            temperature=0.8,
            top_p=0.9,
            do_sample=True
        )
        
        if result:
            print("✅ Message generated successfully!")
            print(f"📝 Generated message:")
            print(f"   {result}")
            print(f"📊 Message length: {len(result)} characters")
        else:
            print("❌ No message generated")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gpt_oss())
