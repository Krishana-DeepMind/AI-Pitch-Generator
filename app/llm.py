"""LLM wrapper with retry-with-backoff and provider fallback.

Wraps all LLM calls so that:
1. Groq is tried first (with tenacity retry + exponential backoff).
2. On repeated failures (rate limits, timeouts), falls back to OpenRouter.
3. All calls return structured text; JSON parsing is handled by the caller.
"""

import json
import logging
import httpx
from typing import Optional, List, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception_type,
    before_sleep_log,
)
from app.config import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when all LLM providers fail."""
    pass


class LLMClient:
    """Unified LLM client with retry and fallback logic."""

    def __init__(self):
        self._groq_client = None
        self._httpx_client = None

    @property
    def groq_client(self):
        if self._groq_client is None:
            from groq import Groq
            self._groq_client = Groq(api_key=settings.groq_api_key)
        return self._groq_client

    @property
    def httpx_client(self):
        if self._httpx_client is None:
            self._httpx_client = httpx.Client(timeout=60.0)
        return self._httpx_client

    def _call_groq(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 800,
        response_format: Optional[Dict] = None,
    ) -> str:
        """Call Groq API with retry logic."""
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if "gpt-oss" in model:
            kwargs["extra_body"] = {"reasoning_effort": "low"}
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = self.groq_client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Groq API call failed: {e}")
            raise

    def _call_openrouter(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> str:
        """Fallback: call OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://marsh-pitch-generator.onrender.com",
            "X-Title": "Marsh Pitch Generator",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = self.httpx_client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(4),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _call_with_retry(self, provider: str, **kwargs) -> str:
        """Retry wrapper around a single provider call."""
        if provider == "groq":
            return self._call_groq(**kwargs)
        else:
            return self._call_openrouter(**kwargs)

    def generate(
        self,
        messages: List[Dict[str, str]],
        model_tier: str = "generation",  # "generation" or "structured"
        temperature: float = 0.7,
        max_tokens: int = 800,
        response_format: Optional[Dict] = None,
    ) -> str:
        """Generate text with automatic retry and fallback.
        
        Args:
            messages: Chat messages in OpenAI format.
            model_tier: "generation" for creative tasks (70B), "structured" for extraction (8B).
            temperature: Sampling temperature.
            max_tokens: Max tokens to generate.
            response_format: Optional JSON mode format spec.
            
        Returns:
            Generated text content.
            
        Raises:
            LLMError: If all providers fail after retries.
        """
        groq_model = (
            settings.groq_generation_model
            if model_tier == "generation"
            else settings.groq_structured_model
        )

        # Try Groq first
        if settings.groq_api_key:
            try:
                return self._call_with_retry(
                    provider="groq",
                    messages=messages,
                    model=groq_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
            except Exception as e:
                logger.warning(f"Groq exhausted after retries: {e}. Falling back to OpenRouter.")

        # Fallback to OpenRouter
        if settings.openrouter_api_key:
            try:
                return self._call_with_retry(
                    provider="openrouter",
                    messages=messages,
                    model=settings.openrouter_fallback_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                logger.error(f"OpenRouter also failed: {e}")
                raise LLMError(f"All LLM providers failed. Last error: {e}")

        raise LLMError("No LLM API keys configured. Set GROQ_API_KEY or OPENROUTER_API_KEY.")

    def generate_json(
        self,
        messages: List[Dict[str, str]],
        model_tier: str = "structured",
        temperature: float = 0.3,
        max_tokens: int = 800,
    ) -> Dict[str, Any]:
        """Generate and parse JSON response.
        
        Attempts JSON mode first, falls back to prompt-based JSON extraction.
        """
        response_format = {"type": "json_object"}

        raw = self.generate(
            messages=messages,
            model_tier=model_tier,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

        # Clean and parse
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
            raise LLMError(f"Failed to parse JSON from LLM response: {raw[:200]}")


# Singleton instance
llm_client = LLMClient()
