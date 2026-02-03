"""
配置管理模块

使用 Pydantic 进行配置验证和管理。
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from nonebot import get_driver


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


@driver.on_startup
def load_config():
    """加载配置"""
    global _dst_config
    config = driver.config
    if hasattr(config, "dst"):
        _dst_config = config.dst
    else:
        _dst_config = DSTConfig()


def get_dst_config() -> DSTConfig:
    """
    获取 DST 配置
    
    Returns:
        DSTConfig: 配置对象
    """
    global _dst_config
    if _dst_config is None:
        _dst_config = DSTConfig()
    return _dst_config


# 导出配置
__all__ = ["DSTConfig", "Config", "get_dst_config"]
