#!/usr/bin/env python3
"""Lightweight test for LLM functionality with automatic fallback to compatible models."""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.llm_factory import create_llm
from utils.config import config
from providers.local_transformers_llm import LocalTransformersLLM

async def test_lightweight_llm():
    """Test LLM with automatic fallback to compatible models."""
    print("🧪 Testing Lightweight LLM with Fallback Support")
    print("=" * 55)
    
    try:
        # Test with different models in order of preference
        test_models = [
            "openai/gpt-oss-20b",      # Primary choice (if GPU available)
            "microsoft/DialoGPT-medium", # Fallback 1 (CPU friendly)
            "microsoft/DialoGPT-small",  # Fallback 2 (very lightweight)
            "gpt2"                       # Last resort (basic)
        ]
        
        successful_model = None
        
        for model_id in test_models:
            print(f"\n🔄 Testing model: {model_id}")
            try:
                # Create LLM instance directly
                llm = LocalTransformersLLM(model_id=model_id)
                print(f"✅ Model loaded: {model_id}")
                
                # Test simple generation
                print("⏳ Testing message generation...")
                result = await llm.generate_text(
                    system_prompt="You are a loving partner creating a short romantic message.",
                    user_prompt="Create a brief good morning message for Preeti.",
                    max_new_tokens=50,  # Keep it short for faster testing
                    temperature=0.8,
                    top_p=0.9,
                    do_sample=True
                )
                
                if result and result.strip():
                    print("✅ Message generated successfully!")
                    print(f"📝 Generated message: {result}")
                    print(f"📊 Message length: {len(result)} characters")
                    successful_model = model_id
                    break
                else:
                    print("❌ No message generated")
                    
            except Exception as e:
                print(f"❌ Model failed: {str(e)[:100]}...")
                continue
        
        if successful_model:
            print(f"\n🎉 Success! Working model: {successful_model}")
            print("\n💡 To use this model permanently, update your configuration:")
            print(f"   HF_MODEL_ID={successful_model}")
        else:
            print("\n❌ No models worked. Check your system resources and dependencies.")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_system_resources():
    """Check system resources and provide recommendations."""
    print("\n🔧 System Resource Check")
    print("=" * 30)
    
    try:
        import torch
        import psutil
        
        # Check available RAM
        memory = psutil.virtual_memory()
        print(f"💾 Available RAM: {memory.available / (1024**3):.1f} GB / {memory.total / (1024**3):.1f} GB")
        
        # Check GPU availability
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            print(f"🎮 GPU available: {gpu_count} device(s)")
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                print(f"   GPU {i}: {gpu_name} ({gpu_memory:.1f} GB)")
        else:
            print("🎮 GPU: Not available (CPU-only mode)")
        
        # Recommendations
        print("\n📋 Recommendations:")
        if memory.available / (1024**3) >= 16:
            print("✅ Sufficient RAM for GPT-OSS-20B")
        elif memory.available / (1024**3) >= 8:
            print("⚠️  Limited RAM - DialoGPT-medium recommended")
        else:
            print("❌ Low RAM - DialoGPT-small or GPT-2 recommended")
            
    except ImportError:
        print("❌ Cannot check system resources (missing dependencies)")

if __name__ == "__main__":
    asyncio.run(test_system_resources())
    asyncio.run(test_lightweight_llm())
