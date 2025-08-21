#!/usr/bin/env python3
"""Debug AI generation issues."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.llm_factory import create_llm
from utils.config import config

async def test_prompt_generation():
    """Test AI generation with the actual prompts used by the system."""
    print("🔍 Debugging AI Message Generation")
    print("=" * 50)
    
    # Create LLM
    llm = create_llm()
    print(f"✅ LLM created: {type(llm).__name__}")
    
    # Get the actual prompts from config
    system_prompt = config.get_prompt_template("morning", "system")
    user_prompt = config.get_prompt_template("morning", "user")
    
    print(f"\n📝 System Prompt:")
    print(f"   {system_prompt}")
    print(f"\n📝 User Prompt:")
    print(f"   {user_prompt}")
    
    if not system_prompt or not user_prompt:
        print("❌ Missing prompt templates!")
        return
    
    # Replace placeholders
    replacements = {
        "GF_NAME": config.settings.gf_name,
        "DAILY_FLIRTY_TONE": config.settings.daily_flirty_tone,
        "closer": "— missing you, bubu gourav"
    }
    
    for key, value in replacements.items():
        system_prompt = system_prompt.replace(f"{{{key}}}", value)
        user_prompt = user_prompt.replace(f"{{{key}}}", value)
    
    print(f"\n🔧 After Placeholder Replacement:")
    print(f"   System: {system_prompt[:100]}...")
    print(f"   User: {user_prompt[:100]}...")
    
    # Test different approaches
    test_cases = [
        {
            "name": "Full System + User Prompt",
            "system": system_prompt,
            "user": user_prompt,
            "max_tokens": 150
        },
        {
            "name": "Simple System Prompt",
            "system": "You are a loving boyfriend writing a romantic good morning message.",
            "user": f"Write a sweet good morning message for {config.settings.gf_name}.",
            "max_tokens": 100
        },
        {
            "name": "Direct Instruction",
            "system": "",
            "user": f"Good morning message for {config.settings.gf_name}: ",
            "max_tokens": 50
        },
        {
            "name": "DialoGPT Style",
            "system": "",
            "user": f"Write a romantic good morning text for {config.settings.gf_name}",
            "max_tokens": 80
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            result = await llm.generate_text(
                system_prompt=test_case["system"],
                user_prompt=test_case["user"],
                max_new_tokens=test_case["max_tokens"],
                temperature=0.8,
                top_p=0.9,
                do_sample=True
            )
            
            if result and result.strip():
                print(f"✅ Generated: {result}")
                print(f"📊 Length: {len(result)} chars")
            else:
                print("❌ No output generated")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_prompt_generation())
