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
            
            # Clean up the output based on model type
            if "gpt-oss" in self.model_id.lower():
                # Remove any reasoning traces that shouldn't be shown to end users
                output_text = self._clean_gpt_oss_output(output_text)
            elif "bloom" in self.model_id.lower():
                # Clean and truncate BLOOM output for better romantic messages
                output_text = self._clean_bloom_output(output_text)
            
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
    
    def _clean_bloom_output(self, text: str, max_chars: int = 300) -> str:
        """Clean BLOOM output for meaningful multi-line romantic messages."""
        import re
        
        # Remove any quotes at the beginning
        text = text.lstrip('"\'')
        
        # Clean up the text first
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.replace('""', '')  # Remove empty quotes
        text = text.replace('" "', ' ')  # Remove quote spaces
        
        # Split into sentences to ensure we get at least 3 meaningful lines
        sentence_endings = re.compile(r'([.!?]+)')
        parts = sentence_endings.split(text)
        
        sentences = []
        current_length = 0
        min_sentences = 3  # Aim for at least 3 sentences
        
        i = 0
        while i < len(parts) - 1:
            # Combine sentence with its ending punctuation
            sentence = parts[i].strip()
            if i + 1 < len(parts):
                sentence += parts[i + 1]
            
            # Skip very short sentences (likely fragments)
            if len(sentence) < 10 and len(sentences) > 0:
                i += 2
                continue
            
            # Add the sentence if we haven't reached max length
            # OR if we need more sentences to reach minimum
            if current_length + len(sentence) <= max_chars or len(sentences) < min_sentences:
                sentences.append(sentence.strip())
                current_length += len(sentence) + 1
                
                # Stop if we have enough sentences and good length
                if len(sentences) >= min_sentences and current_length >= 150:
                    break
            else:
                # If we have minimum sentences, we can stop
                if len(sentences) >= min_sentences:
                    break
                # Otherwise, add a truncated version of this sentence
                remaining_chars = max_chars - current_length
                if remaining_chars > 20:
                    sentences.append(sentence[:remaining_chars-3].strip() + '...')
                break
            
            i += 2
        
        # If we don't have enough sentences, keep more of the original text
        if len(sentences) < min_sentences:
            # Try to split by commas or other natural breaks
            if len(sentences) == 1 and len(sentences[0]) > 50:
                # Split the long sentence into parts
                first_sentence = sentences[0]
                parts = first_sentence.split(', ')
                if len(parts) >= 2:
                    sentences = []
                    for j, part in enumerate(parts[:3]):  # Take up to 3 parts
                        if j == len(parts[:3]) - 1:
                            sentences.append(part.strip())
                        else:
                            sentences.append(part.strip() + ',')
        
        # Format as multi-line message
        if len(sentences) >= 3:
            # Format as 3 distinct lines for better readability
            result = sentences[0]
            if len(sentences) > 1:
                result += ' ' + sentences[1]
            if len(sentences) > 2:
                result += ' ' + ' '.join(sentences[2:])
        else:
            result = ' '.join(sentences)
        
        # Ensure proper ending
        if result and result[-1] not in '.!?':
            result += '.'
        
        # Final length check
        if len(result) > max_chars:
            # Find a good breaking point
            last_sentence_end = max(
                result.rfind('. ', 0, max_chars),
                result.rfind('! ', 0, max_chars),
                result.rfind('? ', 0, max_chars)
            )
            if last_sentence_end > max_chars * 0.6:
                result = result[:last_sentence_end + 1]
            else:
                result = result[:max_chars-3] + '...'
        
        return result.strip()


