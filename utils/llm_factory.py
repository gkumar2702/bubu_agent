"""LLM Factory for creating the appropriate LLM instance based on configuration."""

from typing import Union

from providers.huggingface_llm import HuggingFaceLLM
from providers.local_transformers_llm import LocalTransformersLLM
from utils.config import config
from utils.utils import get_logger
from utils.types import LLMProtocol

logger = get_logger(__name__)


def create_llm() -> LLMProtocol:
    """Create the appropriate LLM instance based on configuration.
    
    Returns:
        LLM instance implementing LLMProtocol
    """
    api_key = config.settings.hf_api_key
    model_id = config.settings.hf_model_id
    
    # Always use local transformers for GPT-OSS models (they're designed for local use)
    if "gpt-oss" in model_id.lower():
        logger.info("Using local transformers for GPT-OSS model", model_id=model_id)
        return LocalTransformersLLM(model_id=model_id)
    
    # Use local transformers if API key is 'local' or invalid
    if api_key == "local" or api_key == "your_valid_hf_api_key_here":
        logger.info("Using local transformers LLM", model_id=model_id)
        return LocalTransformersLLM(model_id=model_id)
    
    # Try to use HuggingFace API
    logger.info("Using HuggingFace API LLM", model_id=model_id)
    return HuggingFaceLLM(
        api_key=api_key,
        model_id=model_id,
        timeout=config.get_hf_setting("timeout_seconds", 30),
        max_retries=config.get_hf_setting("max_retries", 3)
    )


def create_llm_with_fallback() -> LLMProtocol:
    """Create LLM with automatic fallback to local transformers if HF API fails.
    
    Returns:
        LLM instance implementing LLMProtocol
    """
    api_key = config.settings.hf_api_key
    model_id = config.settings.hf_model_id
    
    # If explicitly set to local, use local transformers
    if api_key == "local":
        logger.info("Using local transformers LLM (explicit)", model_id=model_id)
        return LocalTransformersLLM(model_id=model_id)
    
    # If API key looks invalid, use local transformers
    if api_key == "your_valid_hf_api_key_here" or not api_key.startswith("hf_"):
        logger.info("Using local transformers LLM (invalid API key)", model_id=model_id)
        return LocalTransformersLLM(model_id=model_id)
    
    # Try HuggingFace API first
    logger.info("Using HuggingFace API LLM", model_id=model_id)
    return HuggingFaceLLM(
        api_key=api_key,
        model_id=model_id,
        timeout=config.get_hf_setting("timeout_seconds", 30),
        max_retries=config.get_hf_setting("max_retries", 3)
    )
