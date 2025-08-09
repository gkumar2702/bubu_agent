"""Hugging Face Inference API client for text generation."""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import httpx
from utils import get_logger, scrub_secrets_from_logs

logger = get_logger(__name__)


class HuggingFaceLLM:
    """Client for Hugging Face Inference API."""
    
    def __init__(
        self,
        api_key: str,
        model_id: str,
        base_url: str = "https://api-inference.huggingface.co",
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.model_id = model_id
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int = 150,
        temperature: float = 0.8,
        top_p: float = 0.9,
        do_sample: bool = True
    ) -> Optional[str]:
        """
        Generate text using Hugging Face Inference API.
        
        Args:
            system_prompt: System instruction
            user_prompt: User message
            max_new_tokens: Maximum new tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            do_sample: Whether to use sampling
            
        Returns:
            Generated text or None if failed
        """
        payload = {
            "inputs": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "do_sample": do_sample,
                "return_full_text": False
            }
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    "Generating text with Hugging Face",
                    model=self.model_id,
                    attempt=attempt + 1,
                    max_tokens=max_new_tokens
                )
                
                response = await self.client.post(
                    f"{self.base_url}/models/{self.model_id}",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_text = self._extract_generated_text(result)
                    
                    if generated_text:
                        logger.info(
                            "Text generation successful",
                            model=self.model_id,
                            text_length=len(generated_text)
                        )
                        return generated_text
                    else:
                        logger.warning(
                            "No text generated from response",
                            model=self.model_id,
                            response=scrub_secrets_from_logs(result)
                        )
                
                elif response.status_code == 503:
                    # Model is loading, wait and retry
                    wait_time = (attempt + 1) * 2
                    logger.info(
                        "Model is loading, waiting before retry",
                        model=self.model_id,
                        wait_time=wait_time,
                        attempt=attempt + 1
                    )
                    await asyncio.sleep(wait_time)
                    continue
                
                else:
                    logger.error(
                        "Hugging Face API error",
                        model=self.model_id,
                        status_code=response.status_code,
                        response_text=response.text[:200]
                    )
                    
            except httpx.TimeoutException:
                logger.error(
                    "Hugging Face API timeout",
                    model=self.model_id,
                    attempt=attempt + 1,
                    timeout=self.timeout
                )
                
            except Exception as e:
                logger.error(
                    "Hugging Face API exception",
                    model=self.model_id,
                    attempt=attempt + 1,
                    error=str(e)
                )
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        logger.error(
            "Text generation failed after all retries",
            model=self.model_id,
            max_retries=self.max_retries
        )
        return None
    
    def _extract_generated_text(self, response: Any) -> Optional[str]:
        """Extract generated text from Hugging Face API response."""
        try:
            if isinstance(response, list) and len(response) > 0:
                # Standard response format
                return response[0].get("generated_text", "")
            
            elif isinstance(response, dict):
                # Alternative response format
                if "generated_text" in response:
                    return response["generated_text"]
                elif "text" in response:
                    return response["text"]
                elif "choices" in response:
                    choices = response["choices"]
                    if choices and len(choices) > 0:
                        return choices[0].get("text", "")
            
            return None
            
        except Exception as e:
            logger.error(
                "Failed to extract generated text",
                response_type=type(response).__name__,
                error=str(e)
            )
            return None
    
    async def is_available(self) -> bool:
        """Check if the Hugging Face API is available."""
        try:
            response = await self.client.get(f"{self.base_url}/models/{self.model_id}")
            return response.status_code == 200
        except Exception as e:
            logger.error(
                "Failed to check Hugging Face API availability",
                model=self.model_id,
                error=str(e)
            )
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def __repr__(self):
        return f"HuggingFaceLLM(model={self.model_id})"
