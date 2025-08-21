#!/usr/bin/env python3
"""
Setup Hugging Face API Key for Bubu Agent

This script helps you set up a valid Hugging Face API key and choose a working model.
"""

import os
import sys
from pathlib import Path

import httpx

def test_api_key(api_key: str) -> bool:
    """Test if a Hugging Face API key is valid."""
    try:
        response = httpx.get(
            "https://huggingface.co/api/whoami",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def test_model(api_key: str, model_id: str) -> bool:
    """Test if a model is accessible with the given API key."""
    try:
        response = httpx.post(
            f"https://api-inference.huggingface.co/models/{model_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"inputs": "Hello"},
            timeout=30
        )
        # 200 = success, 503 = model loading (still valid)
        return response.status_code in [200, 503]
    except:
        return False

def update_env_file(api_key: str, model_id: str):
    """Update the .env file with new API key and model."""
    env_path = Path(__file__).parent.parent / ".env"
    
    if not env_path.exists():
        print(f"❌ .env file not found at {env_path}")
        return False
    
    # Read current .env content
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update HF_API_KEY and HF_MODEL_ID
    updated_lines = []
    hf_api_key_updated = False
    hf_model_id_updated = False
    
    for line in lines:
        if line.startswith('HF_API_KEY='):
            updated_lines.append(f'HF_API_KEY={api_key}\n')
            hf_api_key_updated = True
        elif line.startswith('HF_MODEL_ID='):
            updated_lines.append(f'HF_MODEL_ID={model_id}\n')
            hf_model_id_updated = True
        else:
            updated_lines.append(line)
    
    # Add missing entries if not found
    if not hf_api_key_updated:
        updated_lines.append(f'HF_API_KEY={api_key}\n')
    if not hf_model_id_updated:
        updated_lines.append(f'HF_MODEL_ID={model_id}\n')
    
    # Write back to file
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"✅ Updated .env file with new API key and model")
    return True

def main():
    print("🚀 Hugging Face API Setup for Bubu Agent")
    print("=" * 50)
    
    # Recommended models (known to work well)
    recommended_models = [
        "openai/gpt-oss-20b",          # Best: Advanced conversational AI
        "openai/gpt-oss-120b",         # Premium: Larger model if you have resources
        "microsoft/DialoGPT-medium",   # Fallback: Older but reliable
        "microsoft/DialoGPT-small",    # Lightweight: For limited resources
        "gpt2-medium",                 # Basic: Simple text generation
        "facebook/blenderbot-400M-distill"  # Alternative: Facebook's model
    ]
    
    print("\n📋 STEP 1: Get a Hugging Face API Key")
    print("1. Go to https://huggingface.co/settings/tokens")
    print("2. Create a new token (read access is sufficient)")
    print("3. Copy the token (starts with 'hf_')")
    
    # Get API key from user
    while True:
        api_key = input("\nEnter your Hugging Face API key: ").strip()
        
        if not api_key:
            print("❌ Please enter an API key")
            continue
            
        if not api_key.startswith('hf_'):
            print("⚠️  API key should start with 'hf_'. Are you sure this is correct? (y/n)")
            confirm = input().strip().lower()
            if confirm not in ['y', 'yes']:
                continue
        
        print("🔍 Testing API key...")
        if test_api_key(api_key):
            print("✅ API key is valid!")
            break
        else:
            print("❌ API key is invalid. Please check and try again.")
    
    # Choose model
    print(f"\n📋 STEP 2: Choose a Model")
    print("Testing recommended models...")
    
    working_models = []
    for model in recommended_models:
        print(f"   Testing {model}...", end=" ")
        if test_model(api_key, model):
            print("✅")
            working_models.append(model)
        else:
            print("❌")
    
    if not working_models:
        print("❌ No recommended models are working. You may need to wait or try later.")
        print("   Using 'openai/gpt-oss-20b' as fallback (best available model)")
        chosen_model = "openai/gpt-oss-20b"
    else:
        print(f"\n✅ Found {len(working_models)} working models:")
        for i, model in enumerate(working_models, 1):
            print(f"   {i}. {model}")
        
        if len(working_models) == 1:
            chosen_model = working_models[0]
            print(f"✅ Using: {chosen_model}")
        else:
            while True:
                try:
                    choice = int(input(f"\nChoose a model (1-{len(working_models)}): "))
                    if 1 <= choice <= len(working_models):
                        chosen_model = working_models[choice - 1]
                        break
                    else:
                        print(f"❌ Please enter a number between 1 and {len(working_models)}")
                except ValueError:
                    print("❌ Please enter a valid number")
    
    # Update .env file
    print(f"\n📋 STEP 3: Update Configuration")
    if update_env_file(api_key, chosen_model):
        print("✅ Setup complete!")
        print(f"\n🎉 Your Bubu Agent is now configured with:")
        print(f"   API Key: {api_key[:8]}...{api_key[-4:]}")
        print(f"   Model: {chosen_model}")
        print(f"\n🚀 You can now use AI generation in the interactive sender!")
        print(f"   Run: python demo/interactive_sender.py")
    else:
        print("❌ Failed to update .env file")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
