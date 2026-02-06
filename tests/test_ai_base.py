import pytest

import nonebot_plugin_dst_management.ai.base as ai_base
from nonebot_plugin_dst_management.ai.base import (
    AIAuthError,
    AIError,
    AIProviderError,
    AIResponseParseError,
    AIRateLimitError,
    AITimeoutError,
    AITransientError,
    RetryPolicy,
    run_with_retry,
)


@pytest.mark.asyncio
async def test_run_with_retry_success() -> None:
    attempts = 0

    async def task() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise AITransientError("temporary")
        return "ok"

    policy = RetryPolicy(retries=3, backoff=0.01, max_backoff=0.02)
    result = await run_with_retry(task, policy, retry_on=(AITransientError,))

    assert result == "ok"
    assert attempts == 3


@pytest.mark.asyncio
async def test_run_with_retry_exhausted() -> None:
    attempts = 0

    async def task() -> str:
        nonlocal attempts
        attempts += 1
        raise AITransientError("temporary")

    policy = RetryPolicy(retries=2, backoff=0.0, max_backoff=0.0)

    with pytest.raises(AITransientError):
        await run_with_retry(task, policy, retry_on=(AITransientError,))

    assert attempts == 2


@pytest.mark.asyncio
async def test_run_with_retry_jitter(monkeypatch: pytest.MonkeyPatch) -> None:
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(ai_base.random, "random", lambda: 0.0)
    monkeypatch.setattr(ai_base.asyncio, "sleep", fake_sleep)

    attempts = 0

    async def task() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise AITransientError("temporary")
        return "ok"

    policy = RetryPolicy(retries=2, backoff=1.0, max_backoff=10.0)
    result = await run_with_retry(task, policy, retry_on=(AITransientError,))

    assert result == "ok"
    assert delays == [0.8]


def test_mask_helpers() -> None:
    assert ai_base._mask_secret("") == ""
    assert ai_base._mask_secret("short") == "***"
    assert ai_base._mask_secret("verylongsecret") == "ver***et"

    masked = ai_base._mask_headers(
        {
            "Authorization": "Bearer verylongsecret",
            "x-api-key": "verylongsecret",
            "Other": "value",
        }
    )
    assert masked["Authorization"] == "Bearer ver***et"
    assert masked["x-api-key"] == "ver***et"
    assert masked["Other"] == "value"


@pytest.mark.asyncio
async def test_provider_close_ownership() -> None:
    # Owns client -> close should close
    provider = ai_base.AIProvider()
    await provider.close()
    assert provider.http_client.is_closed is True

    # Does not own client -> close should not close the injected client
    import httpx

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})))
    provider2 = ai_base.AIProvider(http_client=http_client)
    await provider2.close()
    assert http_client.is_closed is False
    await http_client.aclose()


@pytest.mark.asyncio
async def test_post_json_error_mapping() -> None:
    import httpx

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="nope")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = ai_base.AIProvider(http_client=http_client)
    with pytest.raises(AIAuthError):
        await provider._post_json("https://example.com", {"Authorization": "Bearer x"}, {"a": 1})
    await http_client.aclose()

    def handler_429(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="rate")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler_429))
    provider = ai_base.AIProvider(http_client=http_client)
    with pytest.raises(AIRateLimitError):
        await provider._post_json("https://example.com", {}, {"a": 1})
    await http_client.aclose()

    def handler_504(request: httpx.Request) -> httpx.Response:
        return httpx.Response(504, text="timeout")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler_504))
    provider = ai_base.AIProvider(http_client=http_client)
    with pytest.raises(AITimeoutError):
        await provider._post_json("https://example.com", {}, {"a": 1})
    await http_client.aclose()

    def handler_500(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="server")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler_500))
    provider = ai_base.AIProvider(http_client=http_client)
    with pytest.raises(AITransientError):
        await provider._post_json("https://example.com", {}, {"a": 1})
    await http_client.aclose()

    def handler_400(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="bad")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler_400))
    provider = ai_base.AIProvider(http_client=http_client)
    with pytest.raises(AIProviderError) as exc:
        await provider._post_json("https://example.com", {}, {"a": 1})
    assert exc.value.status_code == 400
    await http_client.aclose()

    def handler_invalid_json(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler_invalid_json))
    provider = ai_base.AIProvider(http_client=http_client)
    with pytest.raises(AIResponseParseError):
        await provider._post_json("https://example.com", {}, {"a": 1})
    await http_client.aclose()

    def handler_timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler_timeout))
    provider = ai_base.AIProvider(http_client=http_client)
    with pytest.raises(AITimeoutError):
        await provider._post_json("https://example.com", {}, {"a": 1})
    await http_client.aclose()

    def handler_request_error(request: httpx.Request) -> httpx.Response:
        raise httpx.RequestError("boom", request=request)

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler_request_error))
    provider = ai_base.AIProvider(http_client=http_client)
    with pytest.raises(AITransientError):
        await provider._post_json("https://example.com", {}, {"a": 1})
    await http_client.aclose()


@pytest.mark.asyncio
async def test_stream_lines_success_and_errors() -> None:
    import httpx

    def ok(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"line1\n\nline2\n")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(ok))
    provider = ai_base.AIProvider(http_client=http_client)
    lines = []
    async for line in provider._stream_lines("https://example.com", {}, {"a": 1}):
        lines.append(line)
    assert lines == ["line1", "line2"]
    await http_client.aclose()

    def err401(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="nope")

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(err401))
    provider = ai_base.AIProvider(http_client=http_client)
    with pytest.raises(AIAuthError):
        async for _ in provider._stream_lines("https://example.com", {}, {"a": 1}):
            pass
    await http_client.aclose()

    def request_error(request: httpx.Request) -> httpx.Response:
        raise httpx.RequestError("boom", request=request)

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(request_error))
    provider = ai_base.AIProvider(http_client=http_client)
    with pytest.raises(AITransientError):
        async for _ in provider._stream_lines("https://example.com", {}, {"a": 1}):
            pass
    await http_client.aclose()


def test_format_ai_error() -> None:
    assert "认证失败" in ai_base.format_ai_error(AIAuthError("x"))
    assert "过于频繁" in ai_base.format_ai_error(AIRateLimitError("x"))
    assert "超时" in ai_base.format_ai_error(AITimeoutError("x"))
    assert "网络错误" in ai_base.format_ai_error(AITransientError("x"))
    assert "响应格式错误" in ai_base.format_ai_error(AIResponseParseError("x"))
    assert "服务暂时不可用" in ai_base.format_ai_error(AIProviderError("x"))
    assert "调用失败" in ai_base.format_ai_error(AIError("x"))
    assert "未知错误" in ai_base.format_ai_error(Exception("x"))
