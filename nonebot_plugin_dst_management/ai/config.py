"""
AI 配置模型

统一管理 AI 功能开关、提供商参数与重试策略。
"""

from __future__ import annotations

from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AIConfig(BaseModel):
    """AI 功能配置"""

    model_config = ConfigDict(validate_assignment=True)

    enabled: bool = False
    provider: Literal["openai", "claude", "ollama", "mock"] = "openai"
    api_key: str = ""
    api_url: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    cache_ttl: int = 86400
    retries: int = 3
    retry_backoff: float = 0.5
    retry_max_backoff: float = 4.0

    @field_validator("provider")
    @classmethod
    def _normalize_provider(cls, value: str) -> str:
        return value.lower().strip()

    @field_validator("temperature")
    @classmethod
    def _validate_temperature(cls, value: float) -> float:
        if not 0 <= value <= 2:
            raise ValueError("temperature must be between 0 and 2")
        return value

    @field_validator("max_tokens")
    @classmethod
    def _validate_max_tokens(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_tokens must be positive")
        return value

    @field_validator("timeout")
    @classmethod
    def _validate_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("timeout must be positive")
        return value

    @field_validator("api_url")
    @classmethod
    def _validate_api_url(cls, value: str) -> str:
        if not value:
            return value
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("api_url must be a valid URL")
        return value

    @field_validator("retries")
    @classmethod
    def _validate_retries(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("retries must be positive")
        return value

    @field_validator("retry_backoff", "retry_max_backoff")
    @classmethod
    def _validate_backoff(cls, value: float) -> float:
        if value < 0:
            raise ValueError("backoff must be non-negative")
        return value

    @field_validator("cache_ttl")
    @classmethod
    def _validate_cache_ttl(cls, value: int) -> int:
        if value < 0:
            raise ValueError("cache_ttl must be non-negative")
        return value
