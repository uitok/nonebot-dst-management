import json

import httpx
import pytest

from nonebot_plugin_dst_management.ai.base import AIResponseParseError
from nonebot_plugin_dst_management.ai.client import AIClient, MockProvider, OpenAIProvider
from nonebot_plugin_dst_management.ai.config import AIConfig


@pytest.mark.asyncio
async def test_openai_provider_parses_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "gpt-4o-mini"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "hi"}}]},
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)

    config = AIConfig(enabled=True, api_key="key")
    provider = OpenAIProvider(config, http_client=http_client)
    ai_client = AIClient(config, provider=provider)

    result = await ai_client.chat([{"role": "user", "content": "hello"}])
    assert result == "hi"

    await http_client.aclose()


@pytest.mark.asyncio
async def test_openai_provider_parse_error_is_not_retried() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"unexpected": "format"})

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)

    config = AIConfig(enabled=True, api_key="key", retries=3, retry_backoff=0.0, retry_max_backoff=0.0)
    provider = OpenAIProvider(config, http_client=http_client)
    ai_client = AIClient(config, provider=provider)

    with pytest.raises(AIResponseParseError):
        await ai_client.chat([{"role": "user", "content": "hello"}])

    assert calls == 1
    await http_client.aclose()


@pytest.mark.asyncio
async def test_retry_on_5xx() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(500, json={"error": "server"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)

    config = AIConfig(enabled=True, api_key="key", retries=2, retry_backoff=0.0, retry_max_backoff=0.0)
    provider = OpenAIProvider(config, http_client=http_client)
    ai_client = AIClient(config, provider=provider)

    result = await ai_client.chat([{"role": "user", "content": "hello"}])
    assert result == "ok"
    assert calls == 2
    await http_client.aclose()


@pytest.mark.asyncio
async def test_ai_client_cache() -> None:
    calls = 0

    class CountingProvider(MockProvider):
        async def chat(self, messages, system_prompt: str = "", **kwargs):  # type: ignore[override]
            nonlocal calls
            calls += 1
            return await super().chat(messages, system_prompt=system_prompt, **kwargs)

    config = AIConfig(enabled=True, provider="mock", cache_ttl=60)
    provider = CountingProvider(config, response="cached")
    ai_client = AIClient(config, provider=provider)

    result1 = await ai_client.chat([{"role": "user", "content": "hello"}])
    result2 = await ai_client.chat([{"role": "user", "content": "hello"}])

    assert result1 == "cached"
    assert result2 == "cached"
    assert calls == 1
