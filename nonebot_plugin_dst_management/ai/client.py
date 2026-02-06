"""
AI 客户端与 Provider 实现

支持 OpenAI、Claude 与 Ollama 三种提供商。
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import Any, Optional, Sequence

import httpx
from loguru import logger

from .base import (
    AIAuthError,
    AIProvider,
    AIProviderError,
    AIResponseParseError,
    AITransientError,
    AITimeoutError,
    AIRateLimitError,
    ChatMessage,
    RetryPolicy,
    run_with_retry,
)
from .config import AIConfig


class OpenAIProvider(AIProvider):
    """OpenAI Provider"""

    name = "openai"

    def __init__(self, config: AIConfig, http_client: Optional[httpx.AsyncClient] = None) -> None:
        super().__init__(http_client=http_client)
        self.config = config

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        if not self.config.api_key:
            raise AIAuthError("missing api key")

        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend(messages)

        url = self.config.api_url or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": api_messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        data = await self._post_json(url, headers, payload, timeout=self.config.timeout)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIResponseParseError("OpenAI 响应解析失败") from exc

    async def stream_chat(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str = "",
        **kwargs: Any,
    ):
        if not self.config.api_key:
            raise AIAuthError("missing api key")

        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend(messages)

        url = self.config.api_url or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": api_messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True,
        }

        async for line in self._stream_lines(url, headers, payload, timeout=self.config.timeout):
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if not data:
                continue
            if data == "[DONE]":
                break
            try:
                payload = json.loads(data)
                delta = payload["choices"][0]["delta"]
                content = delta.get("content")
                if content:
                    yield content
            except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
                raise AIResponseParseError("OpenAI 流式响应解析失败") from exc


class ClaudeProvider(AIProvider):
    """Anthropic Claude Provider"""

    name = "claude"

    def __init__(self, config: AIConfig, http_client: Optional[httpx.AsyncClient] = None) -> None:
        super().__init__(http_client=http_client)
        self.config = config

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        if not self.config.api_key:
            raise AIAuthError("missing api key")

        url = self.config.api_url or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        content_messages = []
        for item in messages:
            if item["role"] not in ("user", "assistant"):
                continue
            content_messages.append(
                {
                    "role": item["role"],
                    "content": [{"type": "text", "text": item["content"]}],
                }
            )

        payload = {
            "model": kwargs.get("model", self.config.model),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "messages": content_messages,
        }
        if system_prompt:
            payload["system"] = system_prompt

        data = await self._post_json(url, headers, payload, timeout=self.config.timeout)
        try:
            return data["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIResponseParseError("Claude 响应解析失败") from exc

    async def stream_chat(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str = "",
        **kwargs: Any,
    ):
        if not self.config.api_key:
            raise AIAuthError("missing api key")

        url = self.config.api_url or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        content_messages = []
        for item in messages:
            if item["role"] not in ("user", "assistant"):
                continue
            content_messages.append(
                {
                    "role": item["role"],
                    "content": [{"type": "text", "text": item["content"]}],
                }
            )

        payload = {
            "model": kwargs.get("model", self.config.model),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "messages": content_messages,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        async for line in self._stream_lines(url, headers, payload, timeout=self.config.timeout):
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if not data:
                continue
            try:
                payload = json.loads(data)
                if payload.get("type") == "content_block_delta":
                    delta = payload.get("delta", {})
                    text = delta.get("text")
                    if text:
                        yield text
                elif payload.get("type") == "content_block_start":
                    content_block = payload.get("content_block", {})
                    text = content_block.get("text")
                    if text:
                        yield text
                elif payload.get("type") == "message_stop":
                    break
            except (TypeError, json.JSONDecodeError) as exc:
                raise AIResponseParseError("Claude 流式响应解析失败") from exc


class OllamaProvider(AIProvider):
    """Ollama 本地模型 Provider"""

    name = "ollama"

    def __init__(self, config: AIConfig, http_client: Optional[httpx.AsyncClient] = None) -> None:
        super().__init__(http_client=http_client)
        self.config = config

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        url = self.config.api_url or "http://localhost:11434/api/chat"

        api_messages = list(messages)
        if system_prompt and not any(msg["role"] == "system" for msg in api_messages):
            api_messages.insert(0, {"role": "system", "content": system_prompt})

        payload = {
            "model": kwargs.get("model", self.config.model),
            "stream": False,
            "messages": api_messages,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        data = await self._post_json(url, {}, payload, timeout=self.config.timeout)
        try:
            return data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise AIResponseParseError("Ollama 响应解析失败") from exc

    async def stream_chat(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str = "",
        **kwargs: Any,
    ):
        url = self.config.api_url or "http://localhost:11434/api/chat"

        api_messages = list(messages)
        if system_prompt and not any(msg["role"] == "system" for msg in api_messages):
            api_messages.insert(0, {"role": "system", "content": system_prompt})

        payload = {
            "model": kwargs.get("model", self.config.model),
            "stream": True,
            "messages": api_messages,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        async for line in self._stream_lines(url, {}, payload, timeout=self.config.timeout):
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AIResponseParseError("Ollama 流式响应解析失败") from exc
            message = chunk.get("message") or {}
            content = message.get("content")
            if content:
                yield content
            if chunk.get("done") is True:
                break


class MockProvider(AIProvider):
    """测试用 Mock Provider"""

    name = "mock"

    def __init__(
        self,
        config: AIConfig,
        response: str = "mock",
        error: Optional[Exception] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        super().__init__(http_client=http_client)
        self.config = config
        self.response = response
        self.error = error

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        if self.error:
            raise self.error
        return self.response

    async def stream_chat(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str = "",
        **kwargs: Any,
    ):
        if self.error:
            raise self.error
        if self.response:
            yield self.response


class AIClient:
    """统一 AI 客户端封装"""

    def __init__(
        self,
        config: AIConfig,
        provider: Optional[AIProvider] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.config = config
        self.provider = provider or self._create_provider(config, http_client=http_client)
        self.retry_policy = RetryPolicy(
            retries=config.retries,
            backoff=config.retry_backoff,
            max_backoff=config.retry_max_backoff,
        )
        self._cache: dict[str, tuple[float, str]] = {}
        self._cache_lock = threading.Lock()

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """发送聊天请求，并处理重试逻辑"""
        if not self.config.enabled:
            raise AIProviderError("AI 功能未启用")
        if not messages:
            raise ValueError("messages cannot be empty")

        cache_key = self._make_cache_key(messages, system_prompt, kwargs)
        cached = self._get_cached_response(cache_key)
        if cached is not None:
            logger.debug("AI 命中缓存：provider={provider}", provider=self.provider.name)
            return cached

        logger.debug(
            "AI 请求准备：provider={provider} messages={count} model={model}",
            provider=self.provider.name,
            count=len(messages),
            model=kwargs.get("model", self.config.model),
        )
        response = await run_with_retry(
            lambda: self.provider.chat(messages, system_prompt=system_prompt, **kwargs),
            policy=self.retry_policy,
            retry_on=(AITransientError, AITimeoutError, AIRateLimitError),
        )
        self._set_cached_response(cache_key, response)
        return response

    async def stream_chat(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str = "",
        **kwargs: Any,
    ):
        """发送聊天请求（流式返回），不支持时回退为普通请求"""
        if not self.config.enabled:
            raise AIProviderError("AI 功能未启用")
        if not messages:
            raise ValueError("messages cannot be empty")

        cache_key = self._make_cache_key(messages, system_prompt, kwargs)
        cached = self._get_cached_response(cache_key)
        if cached is not None:
            yield cached
            return

        logger.debug(
            "AI 流式请求准备：provider={provider} messages={count} model={model}",
            provider=self.provider.name,
            count=len(messages),
            model=kwargs.get("model", self.config.model),
        )

        response_parts: list[str] = []
        try:
            async for chunk in self.provider.stream_chat(messages, system_prompt=system_prompt, **kwargs):
                response_parts.append(chunk)
                yield chunk
        except NotImplementedError:
            response = await self.chat(messages, system_prompt=system_prompt, **kwargs)
            yield response
            return

        if response_parts:
            self._set_cached_response(cache_key, "".join(response_parts))

    async def close(self) -> None:
        """关闭底层 Provider"""
        await self.provider.close()

    def _create_provider(
        self,
        config: AIConfig,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> AIProvider:
        if config.provider == "openai":
            return OpenAIProvider(config, http_client=http_client)
        if config.provider == "claude":
            return ClaudeProvider(config, http_client=http_client)
        if config.provider == "ollama":
            return OllamaProvider(config, http_client=http_client)
        if config.provider == "mock":
            return MockProvider(config, http_client=http_client)
        raise AIProviderError(f"Unsupported AI provider: {config.provider}")

    def _make_cache_key(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str,
        kwargs: dict[str, Any],
    ) -> str:
        payload = {
            "provider": self.provider.name,
            "system_prompt": system_prompt,
            "messages": messages,
            "kwargs": kwargs,
            "model": kwargs.get("model", self.config.model),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }
        raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        ttl = self.config.cache_ttl
        if ttl <= 0:
            return None
        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if not cached:
                return None
            timestamp, value = cached
            if time.monotonic() - timestamp > ttl:
                self._cache.pop(cache_key, None)
                return None
            return value

    def _set_cached_response(self, cache_key: str, value: str) -> None:
        ttl = self.config.cache_ttl
        if ttl <= 0:
            return
        # 简易内存缓存，用于减少重复请求
        now = time.monotonic()
        with self._cache_lock:
            self._cache[cache_key] = (now, value)
            self._prune_cache_locked(now)

    def _prune_cache_locked(self, now: float) -> None:
        ttl = self.config.cache_ttl
        if ttl > 0:
            expired = [key for key, (ts, _) in self._cache.items() if now - ts > ttl]
            for key in expired:
                self._cache.pop(key, None)
        max_entries = self.config.cache_max_entries
        if max_entries > 0 and len(self._cache) > max_entries:
            excess = len(self._cache) - max_entries
            for key, _ in sorted(self._cache.items(), key=lambda item: item[1][0])[:excess]:
                self._cache.pop(key, None)
