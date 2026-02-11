"""
Alconna 命令处理器入口

on_alconna 架构下，命令匹配器在各子模块中直接注册。
此模块仅提供统一的 init() 入口来初始化 API 客户端和 AI 客户端。
"""

from __future__ import annotations

from typing import Optional

from ..client.api_client import DSTApiClient
from ..ai.client import AIClient


# 全局状态
_api_client: Optional[DSTApiClient] = None
_ai_client: Optional[AIClient] = None


def init(api_client: DSTApiClient, ai_client: Optional[AIClient] = None) -> None:
    """
    初始化 Alconna 命令处理器

    在 on_alconna 架构下，各命令模块导入时自动注册匹配器。
    此函数仅设置 API 客户端和 AI 客户端供各命令模块使用。

    Args:
        api_client: DST API 客户端实例
        ai_client: AI 客户端实例（可选，用于 AI 命令）
    """
    global _api_client, _ai_client
    _api_client = api_client
    _ai_client = ai_client

    # 核心命令（仅需 api_client）
    from . import room, console, player, backup, help as help_cmd, config_ui, archive
    room.init(api_client)
    console.init(api_client)
    player.init(api_client)
    backup.init(api_client)
    archive.init(api_client)
    help_cmd.init()
    config_ui.init()

    # 需要 api_client（+ 可选 ai_client）的命令
    from . import mod
    mod.init(api_client, ai_client)

    # AI 命令（需要 api_client + ai_client）
    if ai_client is not None:
        from . import ai_analyze, ai_recommend, ai_mod_parse
        ai_analyze.init(api_client, ai_client)
        ai_recommend.init(api_client, ai_client)
        ai_mod_parse.init(api_client, ai_client)


__all__ = [
    "init",
]
