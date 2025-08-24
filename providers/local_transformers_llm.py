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
    
    # Detect Apple Silicon and use MPS if available
    import torch
    device = None
    if torch.backends.mps.is_available():
        device = "mps"
        logger.info("Detected Apple Silicon - using MPS acceleration")
    elif torch.cuda.is_available():
        device = "cuda"
        logger.info("CUDA GPU detected")
    else:
        device = "cpu"
        logger.info("Using CPU")
    
    # Optimized loading for different model types
    if "mistral" in model_id.lower() or "mixtral" in model_id.lower():
        logger.info("Detected Mistral/Mixtral model, using optimized loading")
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        
        # Use appropriate dtype for device
        if device == "mps":
            # MPS works best with float16
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                device_map=device,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype="auto",
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
    elif "phi" in model_id.lower():
        logger.info("Detected Phi model, using optimized loading for M3")
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        
        # Add padding token if not present (required for Phi)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        if device == "mps":
            # Use 4-bit quantization for MPS to reduce memory usage
            try:
                from transformers import BitsAndBytesConfig
                logger.info("Loading Phi-2 with 4-bit quantization for M3")
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    quantization_config=quantization_config,
                    device_map="auto",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
            except ImportError:
                logger.info("BitsAndBytes not available, using float16 with memory optimization")
                # Load with aggressive memory optimization for M3
                model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                    offload_folder="offload",
                    offload_state_dict=True,
                )
                model = model.to(device)
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype="auto",
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
    else:
        # Default loading for other models (including DialoGPT)
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        
        if device == "mps":
            # For MPS, use float16 for better performance
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
            model = model.to(device)
        else:
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype="auto",
                device_map="auto" if device != "cpu" else None,
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
            
            # Format messages based on model type
            if "phi" in self.model_id.lower():
                # Phi models work better with a specific format
                if system_prompt:
                    # Combine system and user prompts for Phi-2
                    combined_prompt = f"Instruct: {system_prompt}\n\nInput: {user_prompt}\n\nOutput:"
                    messages = [{"role": "user", "content": combined_prompt}]
                else:
                    messages.append({"role": "user", "content": user_prompt})
            else:
                # For all other models (Mistral, DialoGPT, etc.)
                if system_prompt:
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
                
                # Optimized generation parameters
                generation_kwargs = {
                    "max_new_tokens": max_new_tokens,
                    "do_sample": do_sample,
                    "top_p": top_p,
                    "temperature": temperature,
                    "pad_token_id": tokenizer.eos_token_id if tokenizer.eos_token_id else tokenizer.pad_token_id,
                    "repetition_penalty": 1.1,  # Avoid repetitive text
                }
                
                # Model-specific adjustments
                if "dialogpt" in self.model_id.lower():
                    # DialoGPT benefits from slightly different parameters
                    generation_kwargs["repetition_penalty"] = 1.2
                    generation_kwargs["top_k"] = 50
                
                generated = model.generate(**inputs, **generation_kwargs)
                output_ids = generated[0][len(inputs.input_ids[0]):]
                return tokenizer.decode(output_ids, skip_special_tokens=True)

            output_text: str = await asyncio.to_thread(_generate_sync)
            
            # Clean up the output based on model type
            if "mistral" in self.model_id.lower() or "mixtral" in self.model_id.lower():
                # Clean Mistral output
                output_text = self._clean_instruct_output(output_text)
            elif "phi" in self.model_id.lower():
                # Clean Phi output
                output_text = self._clean_instruct_output(output_text)
            elif "dialogpt" in self.model_id.lower():
                # Clean DialoGPT output for better romantic messages
                output_text = self._clean_dialogpt_output(output_text)
            elif "bloom" in self.model_id.lower():
                # Clean and truncate BLOOM output
                output_text = self._clean_bloom_output(output_text)
            
            return output_text.strip()
        except Exception as e:
            logger.error("Local LLM generation failed", error=str(e), model=self.model_id)
            return None
    
    def _clean_instruct_output(self, text: str) -> str:
        """Clean instruction-tuned model output."""
        # Remove any instruction artifacts
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip lines that look like instructions or system messages
            if any(marker in line.lower() for marker in ['<|', '|>', '[INST]', '[/INST]', '<<SYS>>', '<</SYS>>']):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _clean_dialogpt_output(self, text: str) -> str:
        """Clean DialoGPT output for romantic messages."""
        import re
        
        # Remove any response artifacts
        text = re.sub(r'<\|endoftext\|>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Ensure the message is complete
        if text and text[-1] not in '.!?':
            # Find the last complete sentence
            last_punct = max(
                text.rfind('.'),
                text.rfind('!'),
                text.rfind('?')
            )
            if last_punct > len(text) * 0.7:
                text = text[:last_punct + 1]
            else:
                text += '.'
        
        return text
    
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


