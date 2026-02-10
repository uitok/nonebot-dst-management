"""
AI 配置分析命令 (on_alconna)

提供 /dst analyze <房间ID> 命令。
"""

from __future__ import annotations

from typing import Optional

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..ai.analyzer import ServerConfigAnalyzer
from ..ai.base import AIError, format_ai_error
from ..ai.client import AIClient
from ..client.api_client import DSTApiClient
from ..utils.permission import USER_PERMISSION
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

analyze_command = Alconna(
    "dst analyze",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="AI配置分析",
        usage="/dst analyze <房间ID>",
        example="/dst analyze 1",
    ),
)

analyze_matcher = on_alconna(analyze_command, permission=USER_PERMISSION, priority=10, block=True)


# ========== 命令处理 ==========

@analyze_matcher.handle()
async def handle_analyze(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """处理 AI 配置分析命令"""
    client = get_api_client()
    ai = get_ai_client()

    room_id_str = room_id.result if room_id.available else None
    if not room_id_str or not room_id_str.isdigit():
        await analyze_matcher.finish(format_error("请提供有效的房间ID：/dst analyze <房间ID>"))
        return

    rid = int(room_id_str)
    await analyze_matcher.send(format_info(f"正在分析房间 {rid} 配置..."))

    analyzer = ServerConfigAnalyzer(client, ai)
    try:
        report = await analyzer.analyze_server(rid)
    except AIError as exc:
        await analyze_matcher.finish(format_error(format_ai_error(exc)))
        return
    except Exception as exc:
        await analyze_matcher.finish(format_error(f"分析失败：{exc}"))
        return

    await analyze_matcher.finish(report)


def init(api_client: DSTApiClient, ai_client: AIClient) -> None:
    """初始化 AI 配置分析命令"""
    global _api_client, _ai_client
    _api_client = api_client
    _ai_client = ai_client


__all__ = [
    "analyze_command",
    "analyze_matcher",
    "handle_analyze",
    "init",
]
