"""
AI 基础抽象与通用工具

提供统一的错误类型、重试策略与 Provider 基类。
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Literal, Optional, Sequence, Tuple, TypeVar, TypedDict

import httpx
from loguru import logger


ChatRole = Literal["system", "user", "assistant"]


class ChatMessage(TypedDict):
    """聊天消息结构"""

    role: ChatRole
    content: str


class AIError(Exception):
    """AI 调用相关的基础错误"""


class AIAuthError(AIError):
    """认证失败错误"""


class AIRateLimitError(AIError):
    """触发限流错误"""


class AITimeoutError(AIError):
    """调用超时错误"""


class AITransientError(AIError):
    """临时网络错误，可重试"""


class AIResponseParseError(AIError):
    """响应解析错误，不可重试"""


class AIProviderError(AIError):
    """AI 提供商返回错误"""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class RetryPolicy:
    """重试策略"""

    retries: int = 3
    backoff: float = 0.5
    max_backoff: float = 4.0


T = TypeVar("T")


Headers = TypedDict(
    "Headers",
    {
        "Authorization": str,
        "Content-Type": str,
        "x-api-key": str,
        "anthropic-version": str,
    },
    total=False,
)


def _mask_secret(value: str) -> str:
    if not value:
        return value
    if len(value) <= 8:
        return "***"
    return f"{value[:3]}***{value[-2:]}"


def _mask_headers(headers: dict[str, str]) -> dict[str, str]:
    masked: dict[str, str] = {}
    for key, raw_value in headers.items():
        value = raw_value
        if key.lower() in {"authorization", "x-api-key"}:
            if value.lower().startswith("bearer "):
                token = value[7:]
                value = f"Bearer {_mask_secret(token)}"
            else:
                value = _mask_secret(value)
        masked[key] = value
    return masked


async def run_with_retry(
    func: Callable[[], Awaitable[T]],
    policy: RetryPolicy,
    retry_on: Tuple[type[Exception], ...],
) -> T:
    """统一的重试执行器"""

    last_error: Optional[Exception] = None
    for attempt in range(1, policy.retries + 1):
        try:
            return await func()
        except retry_on as exc:
            last_error = exc
            if attempt >= policy.retries:
                break
            delay = min(policy.max_backoff, policy.backoff * (2 ** (attempt - 1)))
            # 加入随机抖动，避免多个客户端同时重试导致惊群效应
            delay = delay * (0.8 + random.random() * 0.4)
            logger.warning("AI 调用失败，{attempt}/{total} 次重试，{delay:.2f}s 后重试：{err}",
                           attempt=attempt,
                           total=policy.retries,
                           delay=delay,
                           err=exc)
            await asyncio.sleep(delay)
        except Exception:
            raise
    if last_error is not None:
        raise last_error
    raise AIError("AI 调用失败")


class AIProvider:
    """AI Provider 基类"""

    name: str = "base"

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None) -> None:
        self._owns_client = http_client is None
        self.http_client = http_client or httpx.AsyncClient()

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str = "",
        **kwargs: Any,
    ) -> str:
        """发送聊天请求"""
        raise NotImplementedError

    async def stream_chat(
        self,
        messages: Sequence[ChatMessage],
        system_prompt: str = "",
        **kwargs: Any,
    ):
        """发送聊天请求（流式返回）"""
        raise NotImplementedError

    async def close(self) -> None:
        """关闭 Provider 持有的 HTTP 客户端"""
        if self._owns_client:
            await self.http_client.aclose()

    async def _post_json(
        self,
        url: str,
        headers: Headers,
        payload: dict[str, Any],
        timeout: Optional[int] = None,
    ) -> dict[str, Any]:
        """统一 HTTP POST JSON 请求，并转换错误类型"""

        try:
            logger.debug(
                "AI 请求发送：provider={provider} url={url} headers={headers} payload_keys={keys} timeout={timeout}",
                provider=self.name,
                url=url,
                headers=_mask_headers(headers),
                keys=sorted(payload.keys()),
                timeout=timeout,
            )
            response = await self.http_client.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            logger.debug(
                "AI 响应成功：provider={provider} status={status} keys={keys}",
                provider=self.name,
                status=response.status_code,
                keys=sorted(data.keys()) if isinstance(data, dict) else type(data).__name__,
            )
            return data
        except httpx.TimeoutException as exc:
            logger.warning("AI 请求超时：provider={provider} url={url}", provider=self.name, url=url)
            raise AITimeoutError("AI 请求超时") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            message = exc.response.text
            logger.warning(
                "AI 响应错误：provider={provider} status={status} body={body}",
                provider=self.name,
                status=status,
                body=message[:500],
            )
            if status in (401, 403):
                raise AIAuthError("AI 认证失败，请检查 API Key") from exc
            if status == 429:
                raise AIRateLimitError("AI 调用过于频繁，请稍后重试") from exc
            if status in (408, 504):
                raise AITimeoutError("AI 请求超时") from exc
            if 500 <= status <= 599:
                raise AITransientError("AI 服务暂时不可用，请稍后重试") from exc
            raise AIProviderError(f"AI 服务错误: {message}", status_code=status) from exc
        except httpx.RequestError as exc:
            logger.warning("AI 网络错误：provider={provider} url={url} err={err}", provider=self.name, url=url, err=exc)
            raise AITransientError("AI 网络错误") from exc
        except ValueError as exc:
            logger.warning("AI 响应解析失败：provider={provider} url={url} err={err}", provider=self.name, url=url, err=exc)
            raise AIResponseParseError("AI 响应格式错误") from exc

    async def _stream_lines(
        self,
        url: str,
        headers: Headers,
        payload: dict[str, Any],
        timeout: Optional[int] = None,
    ):
        try:
            logger.debug(
                "AI 流式请求发送：provider={provider} url={url} headers={headers} payload_keys={keys} timeout={timeout}",
                provider=self.name,
                url=url,
                headers=_mask_headers(headers),
                keys=sorted(payload.keys()),
                timeout=timeout,
            )
            async with self.http_client.stream(
                "POST",
                url,
                headers=headers,
                json=payload,
                timeout=timeout,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield line
        except httpx.TimeoutException as exc:
            logger.warning("AI 流式请求超时：provider={provider} url={url}", provider=self.name, url=url)
            raise AITimeoutError("AI 请求超时") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            message = exc.response.text
            logger.warning(
                "AI 流式响应错误：provider={provider} status={status} body={body}",
                provider=self.name,
                status=status,
                body=message[:500],
            )
            if status in (401, 403):
                raise AIAuthError("AI 认证失败，请检查 API Key") from exc
            if status == 429:
                raise AIRateLimitError("AI 调用过于频繁，请稍后重试") from exc
            if status in (408, 504):
                raise AITimeoutError("AI 请求超时") from exc
            if 500 <= status <= 599:
                raise AITransientError("AI 服务暂时不可用，请稍后重试") from exc
            raise AIProviderError(f"AI 服务错误: {message}", status_code=status) from exc
        except httpx.RequestError as exc:
            logger.warning("AI 流式网络错误：provider={provider} url={url} err={err}", provider=self.name, url=url, err=exc)
            raise AITransientError("AI 网络错误") from exc


def format_ai_error(error: Exception) -> str:
    """将错误转换为统一的用户提示"""

    if isinstance(error, AIAuthError):
        return "⚠️ AI API 认证失败，请检查配置"
    if isinstance(error, AIRateLimitError):
        return "⚠️ AI 调用过于频繁，请稍后再试"
    if isinstance(error, AITimeoutError):
        return "⚠️ AI 响应超时，请重试"
    if isinstance(error, AITransientError):
        return "⚠️ AI 网络错误，请稍后再试"
    if isinstance(error, AIResponseParseError):
        return "⚠️ AI 响应格式错误"
    if isinstance(error, AIProviderError):
        return "⚠️ AI 服务暂时不可用"
    if isinstance(error, AIError):
        return "⚠️ AI 调用失败"
    return "⚠️ 未知错误"
