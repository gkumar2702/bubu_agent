"""Adaptive configuration system that selects optimal models based on system resources."""

import logging
from typing import Dict, Any

try:
    import psutil
    import torch
    SYSTEM_CHECK_AVAILABLE = True
except ImportError:
    SYSTEM_CHECK_AVAILABLE = False

from utils.utils import get_logger

logger = get_logger(__name__)


def get_system_info() -> Dict[str, Any]:
    """Get system resource information."""
    info = {
        "ram_gb": 8,  # Default assumption
        "available_ram_gb": 4,  # Default assumption
        "has_gpu": False,
        "gpu_memory_gb": 0,
        "cpu_cores": 4  # Default assumption
    }
    
    if not SYSTEM_CHECK_AVAILABLE:
        logger.warning("System check dependencies not available, using defaults")
        return info
    
    try:
        # Memory info
        memory = psutil.virtual_memory()
        info["ram_gb"] = memory.total / (1024**3)
        info["available_ram_gb"] = memory.available / (1024**3)
        
        # CPU info
        info["cpu_cores"] = psutil.cpu_count()
        
        # GPU info
        if torch.cuda.is_available():
            info["has_gpu"] = True
            gpu_props = torch.cuda.get_device_properties(0)
            info["gpu_memory_gb"] = gpu_props.total_memory / (1024**3)
        
        logger.info(
            "System resources detected",
            ram_gb=f"{info['ram_gb']:.1f}",
            available_ram_gb=f"{info['available_ram_gb']:.1f}",
            has_gpu=info["has_gpu"],
            gpu_memory_gb=f"{info['gpu_memory_gb']:.1f}",
            cpu_cores=info["cpu_cores"]
        )
        
    except Exception as e:
        logger.warning(f"Failed to detect system resources: {e}")
    
    return info


def get_optimal_model_config(target_model: str = None) -> Dict[str, Any]:
    """Get optimal model configuration based on system resources."""
    system_info = get_system_info()
    
    # Model recommendations based on resources
    model_tiers = {
        "high_end": {
            "model": "openai/gpt-oss-20b",
            "description": "Best quality, requires 16GB+ RAM and preferably GPU",
            "min_ram_gb": 16,
            "min_available_ram_gb": 12,
            "preferred_gpu": True
        },
        "premium": {
            "model": "openai/gpt-oss-120b",
            "description": "Highest quality, requires 32GB+ RAM and GPU",
            "min_ram_gb": 32,
            "min_available_ram_gb": 24,
            "preferred_gpu": True
        },
        "medium": {
            "model": "microsoft/DialoGPT-medium",
            "description": "Good balance, works on 4GB+ available RAM",
            "min_ram_gb": 6,
            "min_available_ram_gb": 3,
            "preferred_gpu": False
        },
        "lightweight": {
            "model": "microsoft/DialoGPT-small",
            "description": "Lightweight, works on 2GB+ available RAM",
            "min_ram_gb": 4,
            "min_available_ram_gb": 2,
            "preferred_gpu": False
        },
        "minimal": {
            "model": "gpt2",
            "description": "Basic functionality, minimal resources",
            "min_ram_gb": 2,
            "min_available_ram_gb": 1,
            "preferred_gpu": False
        }
    }
    
    # If target model is specified, check if system can handle it
    if target_model:
        for tier_name, tier_config in model_tiers.items():
            if tier_config["model"] == target_model:
                can_handle = (
                    system_info["available_ram_gb"] >= tier_config["min_available_ram_gb"] and
                    system_info["ram_gb"] >= tier_config["min_ram_gb"]
                )
                
                if can_handle:
                    logger.info(f"System can handle target model: {target_model}")
                    return {
                        "model_id": target_model,
                        "tier": tier_name,
                        "description": tier_config["description"],
                        "system_compatible": True
                    }
                else:
                    logger.warning(f"System cannot handle target model: {target_model}")
                    break
    
    # Auto-select best model for system
    for tier_name, tier_config in model_tiers.items():
        can_handle = (
            system_info["available_ram_gb"] >= tier_config["min_available_ram_gb"] and
            system_info["ram_gb"] >= tier_config["min_ram_gb"]
        )
        
        # Bonus points for GPU if preferred
        if tier_config["preferred_gpu"] and not system_info["has_gpu"]:
            can_handle = False
        
        if can_handle:
            logger.info(
                f"Selected optimal model tier: {tier_name}",
                model=tier_config["model"],
                description=tier_config["description"]
            )
            return {
                "model_id": tier_config["model"],
                "tier": tier_name,
                "description": tier_config["description"],
                "system_compatible": True,
                "auto_selected": target_model != tier_config["model"]
            }
    
    # Fallback to minimal if nothing else works
    logger.warning("System resources very limited, using minimal model")
    return {
        "model_id": "gpt2",
        "tier": "minimal",
        "description": "Basic functionality, minimal resources",
        "system_compatible": True,
        "auto_selected": True
    }


def get_generation_config(model_tier: str) -> Dict[str, Any]:
    """Get optimal generation parameters based on model tier."""
    configs = {
        "high_end": {
            "max_new_tokens": 150,
            "temperature": 0.8,
            "top_p": 0.9,
            "do_sample": True
        },
        "premium": {
            "max_new_tokens": 200,
            "temperature": 0.8,
            "top_p": 0.9,
            "do_sample": True
        },
        "medium": {
            "max_new_tokens": 100,
            "temperature": 0.7,
            "top_p": 0.85,
            "do_sample": True
        },
        "lightweight": {
            "max_new_tokens": 80,
            "temperature": 0.7,
            "top_p": 0.8,
            "do_sample": True
        },
        "minimal": {
            "max_new_tokens": 50,
            "temperature": 0.6,
            "top_p": 0.8,
            "do_sample": True
        }
    }
    
    return configs.get(model_tier, configs["medium"])


def print_system_recommendations():
    """Print system resource analysis and model recommendations."""
    system_info = get_system_info()
    optimal_config = get_optimal_model_config()
    
    print("🔧 System Analysis & Model Recommendations")
    print("=" * 50)
    
    print(f"💾 RAM: {system_info['available_ram_gb']:.1f}GB available / {system_info['ram_gb']:.1f}GB total")
    print(f"🎮 GPU: {'Available' if system_info['has_gpu'] else 'Not available'}")
    if system_info['has_gpu']:
        print(f"   GPU Memory: {system_info['gpu_memory_gb']:.1f}GB")
    print(f"🖥️  CPU Cores: {system_info['cpu_cores']}")
    
    print(f"\n✅ Recommended Model: {optimal_config['model_id']}")
    print(f"📊 Tier: {optimal_config['tier']}")
    print(f"📝 Description: {optimal_config['description']}")
    
    if optimal_config.get('auto_selected'):
        print("⚠️  Model auto-selected based on system resources")
    
    gen_config = get_generation_config(optimal_config['tier'])
    print(f"\n🎛️  Recommended Generation Settings:")
    for key, value in gen_config.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    print_system_recommendations()
