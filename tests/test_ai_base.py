import pytest

import nonebot_plugin_dst_management.ai.base as ai_base
from nonebot_plugin_dst_management.ai.base import AITransientError, RetryPolicy, run_with_retry


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
