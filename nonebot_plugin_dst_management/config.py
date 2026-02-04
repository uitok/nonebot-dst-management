"""
配置管理模块

使用 Pydantic 进行配置验证和管理。
"""

import json
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from nonebot import get_driver

from .ai.config import AIConfig

class DSTConfig(BaseModel):
    """DST 管理配置"""
    
    # DMP API 配置
    dst_api_url: str = "http://localhost:8080"
    dst_api_token: str = ""
    dst_timeout: int = 10
    
    # 权限配置
    dst_admin_users: List[int] = Field(default_factory=list)
    dst_admin_groups: List[int] = Field(default_factory=list)
    
    # AI 功能配置（可选）
    dst_enable_ai: bool = False
    dst_ai_provider: str = "openai"
    dst_ai_api_key: str = ""
    dst_ai_model: str = "gpt-4"
    dst_ai_base_url: Optional[str] = None

    # 新版 AI 配置
    ai: AIConfig = Field(default_factory=AIConfig)

    def get_ai_config(self) -> AIConfig:
        """
        获取最终 AI 配置（兼容旧字段）。

        Returns:
            AIConfig: 合并后的 AI 配置
        """
        base = self.ai or AIConfig()
        # 仅当旧字段被显式设置时才覆盖，避免默认值覆盖新配置
        fields_set = getattr(self, "model_fields_set", set())
        updates = {}
        if "dst_enable_ai" in fields_set:
            updates["enabled"] = bool(self.dst_enable_ai)
        if "dst_ai_provider" in fields_set and self.dst_ai_provider:
            updates["provider"] = self.dst_ai_provider
        if "dst_ai_api_key" in fields_set and self.dst_ai_api_key:
            updates["api_key"] = self.dst_ai_api_key
        if "dst_ai_base_url" in fields_set and self.dst_ai_base_url:
            updates["api_url"] = self.dst_ai_base_url
        if "dst_ai_model" in fields_set and self.dst_ai_model:
            updates["model"] = self.dst_ai_model
        if updates:
            return base.model_copy(update=updates)
        return base

    # 功能开关
    dst_enable_room_management: bool = True
    dst_enable_player_management: bool = True
    dst_enable_backup_management: bool = True
    dst_enable_mod_management: bool = True
    dst_enable_console_commands: bool = True


class Config(BaseModel):
    """插件配置"""

    dst: DSTConfig = Field(default_factory=DSTConfig)


# 获取驱动并加载配置
driver = get_driver()

# 全局配置实例
_dst_config: Optional[DSTConfig] = None


def _load_dotenv(path: Optional[str] = None) -> None:
    """加载 .env 文件到环境变量（仅覆盖未设置的键）。"""
    env_path = Path(path or ".env")
    if not env_path.is_file():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            if raw.startswith("export "):
                raw = raw[7:].strip()
            if "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        return


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _parse_int_list(value: str) -> List[int]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    return [int(item) for item in items]


def _apply_env_overrides(config: DSTConfig) -> DSTConfig:
    updates: dict[str, object] = {}

    def env(key: str) -> Optional[str]:
        value = os.environ.get(key)
        if value is None or value == "":
            return None
        return value

    if (value := env("DST_API_URL")) is not None:
        updates["dst_api_url"] = value
    if (value := env("DST_API_TOKEN")) is not None:
        updates["dst_api_token"] = value
    if (value := env("DST_TIMEOUT")) is not None:
        updates["dst_timeout"] = int(value)
    if (value := env("DST_ADMIN_USERS")) is not None:
        updates["dst_admin_users"] = _parse_int_list(value)
    if (value := env("DST_ADMIN_GROUPS")) is not None:
        updates["dst_admin_groups"] = _parse_int_list(value)
    if (value := env("DST_ENABLE_AI")) is not None:
        updates["dst_enable_ai"] = _parse_bool(value)
    if (value := env("DST_AI_PROVIDER")) is not None:
        updates["dst_ai_provider"] = value
    if (value := env("DST_AI_API_KEY")) is not None:
        updates["dst_ai_api_key"] = value
    if (value := env("DST_AI_MODEL")) is not None:
        updates["dst_ai_model"] = value
    if (value := env("DST_AI_BASE_URL")) is not None:
        updates["dst_ai_base_url"] = value

    ai_updates: dict[str, object] = {}
    if (value := env("AI_ENABLED")) is not None:
        ai_updates["enabled"] = _parse_bool(value)
    if (value := env("AI_PROVIDER")) is not None:
        ai_updates["provider"] = value
    if (value := env("AI_API_KEY")) is not None:
        ai_updates["api_key"] = value
    if (value := env("AI_API_URL")) is not None:
        ai_updates["api_url"] = value
    if (value := env("AI_MODEL")) is not None:
        ai_updates["model"] = value
    if (value := env("AI_TEMPERATURE")) is not None:
        ai_updates["temperature"] = float(value)
    if (value := env("AI_MAX_TOKENS")) is not None:
        ai_updates["max_tokens"] = int(value)
    if (value := env("AI_TIMEOUT")) is not None:
        ai_updates["timeout"] = int(value)
    if (value := env("AI_CACHE_TTL")) is not None:
        ai_updates["cache_ttl"] = int(value)
    if (value := env("AI_CACHE_MAX_ENTRIES")) is not None:
        ai_updates["cache_max_entries"] = int(value)
    if (value := env("AI_RETRIES")) is not None:
        ai_updates["retries"] = int(value)
    if (value := env("AI_RETRY_BACKOFF")) is not None:
        ai_updates["retry_backoff"] = float(value)
    if (value := env("AI_RETRY_MAX_BACKOFF")) is not None:
        ai_updates["retry_max_backoff"] = float(value)
    if (value := env("AI_SESSION_MAX_ROUNDS")) is not None:
        ai_updates["session_max_rounds"] = int(value)
    if (value := env("AI_SESSION_TTL")) is not None:
        ai_updates["session_ttl"] = int(value)
    if (value := env("AI_PROMPT_ACTIVE")) is not None:
        ai_updates["prompt_active"] = value
    if (value := env("AI_PROMPT_TEMPLATE")) is not None:
        ai_updates["prompt_template"] = value
    if (value := env("AI_PROMPT_TEMPLATES")) is not None:
        try:
            ai_updates["prompt_templates"] = json.loads(value)
        except json.JSONDecodeError:
            pass
    if (value := env("AI_STREAM_CHUNK_SIZE")) is not None:
        ai_updates["stream_chunk_size"] = int(value)

    if ai_updates:
        updates["ai"] = config.ai.model_copy(update=ai_updates)

    if updates:
        return config.model_copy(update=updates)
    return config


@driver.on_startup
def load_config():
    """加载配置"""
    global _dst_config
    _load_dotenv()
    config = driver.config
    if hasattr(config, "dst"):
        raw = config.dst
        if isinstance(raw, DSTConfig):
            _dst_config = raw
        else:
            _dst_config = DSTConfig.model_validate(raw)
    else:
        _dst_config = DSTConfig()
    _dst_config = _apply_env_overrides(_dst_config)


def get_dst_config() -> DSTConfig:
    """
    获取 DST 配置
    
    Returns:
        DSTConfig: 配置对象
    """
    global _dst_config
    if _dst_config is None:
        _load_dotenv()
        _dst_config = _apply_env_overrides(DSTConfig())
    return _dst_config


# 导出配置
__all__ = ["AIConfig", "DSTConfig", "Config", "get_dst_config"]
