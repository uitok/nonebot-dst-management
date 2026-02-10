"""
Alconna 命令处理器入口

on_alconna 架构下，命令匹配器在各子模块（room, console, player）中直接注册。
此模块仅提供统一的 init() 入口来初始化 API 客户端。
"""

from __future__ import annotations

from typing import Optional

from ..client.api_client import DSTApiClient


# 全局状态
_api_client: Optional[DSTApiClient] = None


def init(api_client: DSTApiClient) -> None:
    """
    初始化 Alconna 命令处理器

    在 on_alconna 架构下，各命令模块导入时自动注册匹配器。
    此函数仅设置 API 客户端供各命令模块使用。

    Args:
        api_client: DST API 客户端实例
    """
    global _api_client
    _api_client = api_client

    from . import room, console, player
    room.init(api_client)
    console.init(api_client)
    player.init(api_client)


__all__ = [
    "init",
]
