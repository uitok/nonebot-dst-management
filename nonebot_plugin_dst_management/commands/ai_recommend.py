"""
AI 模组推荐命令 (on_alconna)

提供 /dst mod recommend <房间ID> [类型] 命令。
"""

from __future__ import annotations

from typing import Optional

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..ai.recommender import ModRecommender
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

recommend_command = Alconna(
    "dst mod recommend",
    Args["room_id", str, None]["mod_type", str, None],
    meta=CommandMeta(
        description="AI模组推荐",
        usage="/dst mod recommend <房间ID> [类型]",
        example="/dst mod recommend 1 战斗",
    ),
)

recommend_matcher = on_alconna(recommend_command, permission=USER_PERMISSION, priority=10, block=True)


# ========== 命令处理 ==========

@recommend_matcher.handle()
async def handle_recommend(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
    mod_type: Match[str] = AlconnaMatch("mod_type"),
) -> None:
    """处理 AI 模组推荐命令"""
    if not await check_group(event):
        await recommend_matcher.finish(format_error("当前群组未授权使用此功能"))
        return

    client = get_api_client()
    ai = get_ai_client()

    room_id_str = room_id.result if room_id.available else None
    if not room_id_str or not room_id_str.isdigit():
        await recommend_matcher.finish(format_error("用法：/dst mod recommend <房间ID> [类型]"))
        return

    rid = int(room_id_str)
    type_val = mod_type.result if mod_type.available else None

    await recommend_matcher.send(format_info(f"正在生成房间 {rid} 的模组推荐..."))

    recommender = ModRecommender(client, ai)
    try:
        result = await recommender.recommend_mods(rid, type_val)
    except AIError as exc:
        await recommend_matcher.finish(format_error(format_ai_error(exc)))
        return
    except Exception as exc:
        await recommend_matcher.finish(format_error(f"推荐失败：{exc}"))
        return

    report = result.get("report", "")
    await recommend_matcher.finish(report)


def init(api_client: DSTApiClient, ai_client: AIClient) -> None:
    """初始化 AI 模组推荐命令"""
    global _api_client, _ai_client
    _api_client = api_client
    _ai_client = ai_client


__all__ = [
    "recommend_command",
    "recommend_matcher",
    "handle_recommend",
    "init",
]
