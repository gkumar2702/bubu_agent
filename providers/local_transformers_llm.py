"""Local Transformers-based LLM provider implementing LLMProtocol.

Loads a chat-capable model via transformers and generates text locally,
avoiding external Inference API calls. Intended as a drop-in for testing
or offline usage when HF Inference is unavailable.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from transformers import AutoModelForCausalLM, AutoTokenizer

from utils.types import LLMProtocol
from utils.utils import get_logger


logger = get_logger(__name__)


_CACHED_MODEL = None
_CACHED_TOKENIZER = None
_CACHED_MODEL_ID = None


def _ensure_model_loaded(model_id: str):
    global _CACHED_MODEL, _CACHED_TOKENIZER, _CACHED_MODEL_ID
    if _CACHED_MODEL is not None and _CACHED_MODEL_ID == model_id:
        return _CACHED_MODEL, _CACHED_TOKENIZER

    logger.info("Loading local transformers model", model_id=model_id)
    
    # Optimized loading for GPT-OSS models
    if "gpt-oss" in model_id.lower():
        logger.info("Detected GPT-OSS model, using optimized loading parameters")
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        
        # Try GPU first, fallback to CPU if needed
        try:
            logger.info("Attempting GPU loading for GPT-OSS model")
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype="auto",  # Uses BF16 automatically for GPT-OSS
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                attn_implementation="flash_attention_2" if _has_flash_attention() else None,
            )
        except Exception as gpu_error:
            logger.warning(f"GPU loading failed, trying CPU: {gpu_error}")
            try:
                # Fallback to CPU with different settings
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    torch_dtype="float32",  # Use float32 for CPU
                    device_map="cpu",       # Force CPU
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
                logger.info("Successfully loaded GPT-OSS model on CPU")
            except Exception as cpu_error:
                logger.error(f"Both GPU and CPU loading failed: {cpu_error}")
                # Try with minimal settings as last resort
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    trust_remote_code=True,
                )
                logger.info("Loaded GPT-OSS model with minimal settings")
    else:
        # Default loading for other models
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype="auto",
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
    
    _CACHED_MODEL = model
    _CACHED_TOKENIZER = tokenizer
    _CACHED_MODEL_ID = model_id
    return model, tokenizer


def _has_flash_attention() -> bool:
    """Check if flash attention is available."""
    try:
        import flash_attn
        return True
    except ImportError:
        return False


class LocalTransformersLLM(LLMProtocol):
    """Local LLM using transformers generate API."""

    def __init__(self, model_id: str):
        self.model_id = model_id
        # Lazy-load on first call to avoid blocking startup

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        do_sample: bool,
    ) -> Optional[str]:
        try:
            model, tokenizer = await asyncio.to_thread(_ensure_model_loaded, self.model_id)

            messages = []
            
            # Optimize system prompt for GPT-OSS models
            if "gpt-oss" in self.model_id.lower() and system_prompt:
                # Add reasoning level for GPT-OSS models (medium for balanced speed and detail)
                enhanced_system_prompt = f"{system_prompt}\n\nReasoning: medium"
                messages.append({"role": "system", "content": enhanced_system_prompt})
            elif system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                
            messages.append({"role": "user", "content": user_prompt})

            def _generate_sync() -> str:
                # Check if model supports chat templates
                if hasattr(tokenizer, 'chat_template') and tokenizer.chat_template:
                    # Use the harmony response format for GPT-OSS models
                    text = tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=True,
                    )
                else:
                    # For models without chat templates (like BLOOM), concatenate directly
                    if system_prompt:
                        text = f"{system_prompt}\n\n{user_prompt}"
                    else:
                        text = user_prompt
                
                inputs = tokenizer([text], return_tensors="pt").to(model.device)
                
                # Optimized generation parameters for GPT-OSS
                generation_kwargs = {
                    "max_new_tokens": max_new_tokens,
                    "do_sample": do_sample,
                    "top_p": top_p,
                    "temperature": temperature,
                    "pad_token_id": tokenizer.eos_token_id,
                }
                
                # Add repetition penalty for better quality
                if "gpt-oss" in self.model_id.lower():
                    generation_kwargs["repetition_penalty"] = 1.1
                
                generated = model.generate(**inputs, **generation_kwargs)
                output_ids = generated[0][len(inputs.input_ids[0]):]
                return tokenizer.decode(output_ids, skip_special_tokens=True)

            output_text: str = await asyncio.to_thread(_generate_sync)
            
            # Clean up the output for GPT-OSS models
            if "gpt-oss" in self.model_id.lower():
                # Remove any reasoning traces that shouldn't be shown to end users
                output_text = self._clean_gpt_oss_output(output_text)
            
            return output_text.strip()
        except Exception as e:
            logger.error("Local LLM generation failed", error=str(e), model=self.model_id)
            return None
    
    def _clean_gpt_oss_output(self, text: str) -> str:
        """Clean GPT-OSS output by removing internal reasoning traces."""
        # Remove common reasoning artifacts that shouldn't be shown to users
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip lines that look like internal reasoning
            if any(marker in line.lower() for marker in ['<thinking>', '</thinking>', 'reasoning:', 'let me think']):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()


