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
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})

            def _generate_sync() -> str:
                text = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
                inputs = tokenizer([text], return_tensors="pt").to(model.device)
                generated = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=do_sample,
                    top_p=top_p,
                    temperature=temperature,
                )
                output_ids = generated[0][len(inputs.input_ids[0]):]
                return tokenizer.decode(output_ids, skip_special_tokens=True)

            output_text: str = await asyncio.to_thread(_generate_sync)
            return output_text.strip()
        except Exception as e:
            logger.error("Local LLM generation failed", error=str(e))
            return None


