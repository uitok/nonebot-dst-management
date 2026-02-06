import json

import httpx
import pytest

from nonebot_plugin_dst_management.ai.base import (
    AIAuthError,
    AIProviderError,
    AIResponseParseError,
)
from nonebot_plugin_dst_management.ai.client import (
    AIClient,
    ClaudeProvider,
    MockProvider,
    OllamaProvider,
    OpenAIProvider,
)
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
    await ai_client.close()


@pytest.mark.asyncio
async def test_ai_client_cache_eviction() -> None:
    config = AIConfig(enabled=True, provider="mock", cache_ttl=60, cache_max_entries=1)
    provider = MockProvider(config, response="cached")
    ai_client = AIClient(config, provider=provider)

    await ai_client.chat([{"role": "user", "content": "hello"}])
    await ai_client.chat([{"role": "user", "content": "world"}])

    assert len(ai_client._cache) == 1
    await ai_client.close()


@pytest.mark.asyncio
async def test_openai_stream_chat_and_cache() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["stream"] is True
        assert payload["messages"][0]["role"] == "system"
        content = "\n".join(
            [
                "event: ignored",
                "data: " + json.dumps({"choices": [{"delta": {"content": "hi"}}]}),
                "data: " + json.dumps({"choices": [{"delta": {"content": "!"}}]}),
                "data: [DONE]",
                "",
            ]
        )
        return httpx.Response(200, content=content.encode("utf-8"))

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)

    config = AIConfig(enabled=True, api_key="key")
    provider = OpenAIProvider(config, http_client=http_client)
    ai_client = AIClient(config, provider=provider)

    parts: list[str] = []
    async for chunk in ai_client.stream_chat([{"role": "user", "content": "hello"}], system_prompt="sys"):
        parts.append(chunk)
    assert parts == ["hi", "!"]

    cached: list[str] = []
    async for chunk in ai_client.stream_chat([{"role": "user", "content": "hello"}], system_prompt="sys"):
        cached.append(chunk)
    assert cached == ["hi!"]

    await http_client.aclose()


@pytest.mark.asyncio
async def test_openai_stream_chat_parse_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        content = "\n".join(["data: {bad json}", ""])
        return httpx.Response(200, content=content.encode("utf-8"))

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)

    config = AIConfig(enabled=True, api_key="key")
    provider = OpenAIProvider(config, http_client=http_client)

    with pytest.raises(AIResponseParseError):
        async for _ in provider.stream_chat([{"role": "user", "content": "hello"}]):
            pass

    await http_client.aclose()


@pytest.mark.asyncio
async def test_claude_chat_and_stream_chat() -> None:
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        calls.append(payload)
        if payload.get("stream") is True:
            content = "\n".join(
                [
                    "data: " + json.dumps({"type": "content_block_start", "content_block": {"text": "hi"}}),
                    "data: " + json.dumps({"type": "content_block_delta", "delta": {"text": " there"}}),
                    "data: " + json.dumps({"type": "message_stop"}),
                    "",
                ]
            )
            return httpx.Response(200, content=content.encode("utf-8"))
        return httpx.Response(200, json={"content": [{"text": "ok"}]})

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)

    config = AIConfig(enabled=True, provider="claude", api_key="key")
    provider = ClaudeProvider(config, http_client=http_client)

    result = await provider.chat(
        [
            {"role": "system", "content": "ignored by provider"},
            {"role": "user", "content": "hello"},
        ],
        system_prompt="sys",
    )
    assert result == "ok"
    assert calls[0]["system"] == "sys"
    assert all(m["role"] in ("user", "assistant") for m in calls[0]["messages"])

    streamed: list[str] = []
    async for chunk in provider.stream_chat([{"role": "user", "content": "hello"}], system_prompt="sys"):
        streamed.append(chunk)
    assert streamed == ["hi", " there"]

    await http_client.aclose()


@pytest.mark.asyncio
async def test_ollama_chat_and_stream_chat() -> None:
    requests: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requests.append(payload)
        if payload.get("stream") is True:
            content = "\n".join(
                [
                    json.dumps({"message": {"content": "hi"}, "done": False}),
                    json.dumps({"message": {"content": "!"}, "done": True}),
                    "",
                ]
            )
            return httpx.Response(200, content=content.encode("utf-8"))
        return httpx.Response(200, json={"message": {"content": "ok"}})

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)

    config = AIConfig(enabled=True, provider="ollama")
    provider = OllamaProvider(config, http_client=http_client)

    result = await provider.chat([{"role": "user", "content": "hello"}], system_prompt="sys")
    assert result == "ok"
    assert requests[0]["messages"][0]["role"] == "system"

    streamed: list[str] = []
    async for chunk in provider.stream_chat([{"role": "user", "content": "hello"}], system_prompt="sys"):
        streamed.append(chunk)
    assert streamed == ["hi", "!"]

    await http_client.aclose()


@pytest.mark.asyncio
async def test_ai_client_disabled_and_empty_messages() -> None:
    config = AIConfig(enabled=False, provider="mock")
    ai_client = AIClient(config, provider=MockProvider(config, response="x"))

    with pytest.raises(AIProviderError):
        await ai_client.chat([{"role": "user", "content": "hello"}])

    await ai_client.close()

    config2 = AIConfig(enabled=True, provider="mock")
    ai_client2 = AIClient(config2, provider=MockProvider(config2, response="x"))
    with pytest.raises(ValueError):
        await ai_client2.chat([])
    await ai_client2.close()


@pytest.mark.asyncio
async def test_ai_client_stream_fallback_to_chat() -> None:
    class NoStreamProvider(MockProvider):
        async def stream_chat(self, messages, system_prompt: str = "", **kwargs):  # type: ignore[override]
            # Make this an async generator so `async for` works and the
            # NotImplementedError is raised during iteration (and can be caught).
            raise NotImplementedError
            if False:  # pragma: no cover
                yield ""  # type: ignore[misc]

    config = AIConfig(enabled=True, provider="mock")
    provider = NoStreamProvider(config, response="fallback")
    ai_client = AIClient(config, provider=provider)

    parts: list[str] = []
    async for chunk in ai_client.stream_chat([{"role": "user", "content": "hello"}]):
        parts.append(chunk)

    assert parts == ["fallback"]
    await ai_client.close()


@pytest.mark.asyncio
async def test_openai_provider_missing_api_key() -> None:
    config = AIConfig(enabled=True, api_key="")
    provider = OpenAIProvider(config)

    with pytest.raises(AIAuthError):
        await provider.chat([{"role": "user", "content": "hello"}])
    await provider.close()


@pytest.mark.asyncio
async def test_ai_client_cache_expired(monkeypatch: pytest.MonkeyPatch) -> None:
    config = AIConfig(enabled=True, provider="mock", cache_ttl=1)
    provider = MockProvider(config, response="x")
    ai_client = AIClient(config, provider=provider)

    key = ai_client._make_cache_key([{"role": "user", "content": "hello"}], "", {})
    ai_client._cache[key] = (0.0, "cached")

    import nonebot_plugin_dst_management.ai.client as ai_client_module

    monkeypatch.setattr(ai_client_module.time, "monotonic", lambda: 2.0)
    assert ai_client._get_cached_response(key) is None
    assert key not in ai_client._cache
    await ai_client.close()
