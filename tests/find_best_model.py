#!/usr/bin/env python3
"""Find and test the best romantic text generation models for limited RAM systems."""

import asyncio
import sys
import time
import os
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Direct imports to avoid circular dependency
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Get GF_NAME from environment
from dotenv import load_dotenv
load_dotenv(project_root / ".env")
GF_NAME = os.getenv("GF_NAME", "Preeti Bubu")

# Models to test - carefully selected for romantic text generation and RAM constraints
MODELS_TO_TEST = [
    {
        "id": "microsoft/DialoGPT-small",
        "description": "Smaller DialoGPT - uses less RAM",
        "expected_ram": "~1GB",
        "type": "conversational"
    },
    {
        "id": "gpt2",
        "description": "Base GPT-2 - general text generation",
        "expected_ram": "~1.5GB",
        "type": "generative"
    },
    {
        "id": "distilgpt2",
        "description": "Distilled GPT-2 - smaller and faster",
        "expected_ram": "~500MB",
        "type": "generative"
    },
    {
        "id": "EleutherAI/gpt-neo-125M",
        "description": "GPT-Neo 125M - small but capable",
        "expected_ram": "~500MB",
        "type": "generative"
    },
    {
        "id": "bigscience/bloom-560m",
        "description": "BLOOM 560M - multilingual, good for creative text",
        "expected_ram": "~2GB",
        "type": "generative"
    },
    {
        "id": "facebook/opt-125m",
        "description": "OPT 125M - Facebook's small language model",
        "expected_ram": "~500MB",
        "type": "generative"
    },
    {
        "id": "google/flan-t5-small",
        "description": "FLAN-T5 Small - instruction-following model",
        "expected_ram": "~500MB",
        "type": "instruction"
    }
]

# Test prompts for romantic message generation
TEST_PROMPTS = [
    {
        "name": "Simple romantic",
        "system": "",
        "user": f"Write a romantic good morning message for {GF_NAME}: ",
    },
    {
        "name": "Detailed instruction",
        "system": "You are writing romantic messages.",
        "user": f"Create a sweet and loving good morning message for {GF_NAME}. Include warmth and affection.",
    },
    {
        "name": "Creative prompt",
        "system": "",
        "user": f"Good morning {GF_NAME}! Today I want to tell you that",
    }
]

async def test_model(model_id: str, model_info: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single model with various prompts."""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {model_id}")
    print(f"📝 Description: {model_info['description']}")
    print(f"💾 Expected RAM: {model_info['expected_ram']}")
    print(f"🎯 Type: {model_info['type']}")
    print("-" * 40)
    
    results = {
        "model_id": model_id,
        "info": model_info,
        "load_success": False,
        "load_time": 0,
        "generations": [],
        "quality_score": 0,
        "recommendation": ""
    }
    
    try:
        # Try to load the model
        start_time = time.time()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float32,  # Use float32 for CPU
            device_map="cpu",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        load_time = time.time() - start_time
        results["load_success"] = True
        results["load_time"] = load_time
        print(f"✅ Model loaded in {load_time:.2f} seconds")
        
        # Test with different prompts
        for prompt_idx, prompt in enumerate(TEST_PROMPTS, 1):
            print(f"\n📋 Test {prompt_idx}: {prompt['name']}")
            
            try:
                # Adjust parameters based on model type
                if model_info['type'] == 'conversational':
                    max_tokens = 50
                    temperature = 0.8
                elif model_info['type'] == 'instruction':
                    max_tokens = 80
                    temperature = 0.7
                else:  # generative
                    max_tokens = 60
                    temperature = 0.9
                
                # Prepare input
                if prompt["system"]:
                    full_prompt = f"{prompt['system']}\n{prompt['user']}"
                else:
                    full_prompt = prompt["user"]
                
                # Tokenize input
                inputs = tokenizer.encode(full_prompt, return_tensors="pt")
                
                # Generate
                with torch.no_grad():
                    outputs = model.generate(
                        inputs,
                        max_new_tokens=max_tokens,
                        temperature=temperature,
                        top_p=0.9,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
                
                # Decode output
                result = tokenizer.decode(outputs[0], skip_special_tokens=True)
                # Remove the input prompt from output
                result = result.replace(full_prompt, "").strip()
                
                if result and result.strip():
                    # Clean up the result
                    result = result.strip()
                    # Remove the input prompt if it's repeated in the output
                    if prompt["user"] in result:
                        result = result.replace(prompt["user"], "").strip()
                    
                    print(f"   Generated: {result[:150]}...")
                    print(f"   Length: {len(result)} chars")
                    
                    # Score the quality (basic heuristic)
                    quality = 0
                    if len(result) > 20:
                        quality += 2
                    if any(word in result.lower() for word in ['love', 'beautiful', 'sweet', 'amazing', 'wonderful']):
                        quality += 3
                    if GF_NAME.lower() in result.lower():
                        quality += 2
                    if any(word in result.lower() for word in ['morning', 'day', 'sunshine', 'smile']):
                        quality += 1
                    
                    results["generations"].append({
                        "prompt": prompt["name"],
                        "output": result,
                        "quality": quality
                    })
                    results["quality_score"] += quality
                else:
                    print(f"   ❌ No output generated")
                    results["generations"].append({
                        "prompt": prompt["name"],
                        "output": None,
                        "quality": 0
                    })
                    
            except Exception as e:
                print(f"   ❌ Generation error: {str(e)[:100]}")
                results["generations"].append({
                    "prompt": prompt["name"],
                    "output": None,
                    "quality": 0,
                    "error": str(e)
                })
        
        # Calculate average quality
        if results["generations"]:
            results["quality_score"] = results["quality_score"] / len(results["generations"])
        
        # Make recommendation
        if results["quality_score"] >= 5:
            results["recommendation"] = "🌟 Excellent for romantic messages"
        elif results["quality_score"] >= 3:
            results["recommendation"] = "✅ Good for romantic messages"
        elif results["quality_score"] >= 1:
            results["recommendation"] = "⚠️ Basic, needs prompt engineering"
        else:
            results["recommendation"] = "❌ Not suitable for romantic messages"
            
    except Exception as e:
        print(f"❌ Failed to load model: {str(e)[:200]}")
        results["error"] = str(e)
        results["recommendation"] = "❌ Cannot load on this system"
    
    return results

async def main():
    """Test all models and provide recommendations."""
    print("🔍 Finding the Best Romantic Text Generation Model")
    print("=" * 60)
    print(f"System: Limited RAM (~1GB available)")
    print(f"Goal: Generate romantic messages for {GF_NAME}")
    
    all_results = []
    
    for model_info in MODELS_TO_TEST:
        results = await test_model(model_info["id"], model_info)
        all_results.append(results)
        
        # Small delay between models to avoid memory issues
        await asyncio.sleep(2)
    
    # Summary and recommendations
    print("\n" + "="*60)
    print("📊 SUMMARY & RECOMMENDATIONS")
    print("="*60)
    
    # Sort by quality score
    successful_models = [r for r in all_results if r["load_success"]]
    successful_models.sort(key=lambda x: x["quality_score"], reverse=True)
    
    if successful_models:
        print("\n✅ Models that worked (sorted by quality):")
        for idx, result in enumerate(successful_models, 1):
            print(f"\n{idx}. {result['model_id']}")
            print(f"   Quality Score: {result['quality_score']:.2f}/8")
            print(f"   Load Time: {result['load_time']:.2f}s")
            print(f"   {result['recommendation']}")
            
            # Show best generation
            best_gen = max(result['generations'], key=lambda x: x.get('quality', 0))
            if best_gen and best_gen.get('output'):
                print(f"   Best output: \"{best_gen['output'][:100]}...\"")
        
        # Final recommendation
        if successful_models:
            best_model = successful_models[0]
            print("\n" + "="*60)
            print("🏆 RECOMMENDED MODEL FOR YOUR SYSTEM:")
            print(f"   {best_model['model_id']}")
            print(f"   Reason: {best_model['recommendation']}")
            print("\n💡 To use this model, update your .env file:")
            print(f"   HF_MODEL_ID={best_model['model_id']}")
    else:
        print("\n❌ No models could be loaded successfully on this system.")
        print("   Consider using cloud-based API or upgrading hardware.")

if __name__ == "__main__":
    asyncio.run(main())
