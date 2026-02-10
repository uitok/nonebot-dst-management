"""
AI 模组配置解析命令 (on_alconna)

提供 /dst mod parse <房间ID> <世界ID> 命令。
"""

from __future__ import annotations

from typing import Optional

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..ai.mod_parser import ModConfigParser
from ..ai.base import AIError, format_ai_error
from ..ai.client import AIClient
from ..client.api_client import DSTApiClient
from ..utils.permission import USER_PERMISSION, check_group
from ..utils.formatter import format_error, format_info


# 全局客户端
_api_client: Optional[DSTApiClient] = None
_ai_client: Optional[AIClient] = None


def get_api_client() -> DSTApiClient:
    if _api_client is None:
        raise RuntimeError("API 客户端未初始化，请先调用 init() 函数")
    return _api_client


def get_ai_client() -> AIClient:
    if _ai_client is None:
        raise RuntimeError("AI 客户端未初始化，请先调用 init() 函数")
    return _ai_client


# ========== Alconna 命令定义 ==========

mod_parse_command = Alconna(
    "dst mod parse",
    Args["room_id", str, None]["world_id", str, None],
    meta=CommandMeta(
        description="AI模组配置解析",
        usage="/dst mod parse <房间ID> <世界ID>",
        example="/dst mod parse 1 Master",
    ),
)

mod_parse_matcher = on_alconna(mod_parse_command, permission=USER_PERMISSION, priority=10, block=True)


# ========== 命令处理 ==========

@mod_parse_matcher.handle()
async def handle_mod_parse(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
    world_id: Match[str] = AlconnaMatch("world_id"),
) -> None:
    """处理 AI 模组配置解析命令"""
    if not await check_group(event):
        await mod_parse_matcher.finish(format_error("当前群组未授权使用此功能"))
        return

    client = get_api_client()
    ai = get_ai_client()

    room_id_str = room_id.result if room_id.available else None
    world_id_str = world_id.result if world_id.available else None

    if not room_id_str or not room_id_str.isdigit():
        await mod_parse_matcher.finish(format_error("用法：/dst mod parse <房间ID> <世界ID>"))
        return

    if not world_id_str:
        await mod_parse_matcher.finish(format_error("用法：/dst mod parse <房间ID> <世界ID>"))
        return

    rid = int(room_id_str)
    await mod_parse_matcher.send(format_info(f"正在解析房间 {rid} - 世界 {world_id_str} 配置..."))

    parser = ModConfigParser(client, ai)
    try:
        result = await parser.parse_mod_config(rid, world_id_str)
    except AIError as exc:
        await mod_parse_matcher.finish(format_error(format_ai_error(exc)))
        return
    except Exception as exc:
        await mod_parse_matcher.finish(format_error(f"解析失败：{exc}"))
        return

    report = result.get("report", "")
    await mod_parse_matcher.finish(report)


def init(api_client: DSTApiClient, ai_client: AIClient) -> None:
    """初始化 AI 模组配置解析命令"""
    global _api_client, _ai_client
    _api_client = api_client
    _ai_client = ai_client


__all__ = [
    "mod_parse_command",
    "mod_parse_matcher",
    "handle_mod_parse",
    "init",
]
