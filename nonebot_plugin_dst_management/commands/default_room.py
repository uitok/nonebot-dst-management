"""
默认房间命令 (on_alconna 版本)

使用 nonebot-plugin-alconna 的 on_alconna 匹配器。
"""

from __future__ import annotations

from typing import Any, Optional

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..client.api_client import DSTApiClient
from ..database import clear_user_default_room, get_user_default_room, set_user_default_room
from ..helpers.commands import parse_room_id
from ..helpers.formatters import format_error, format_info, format_success
from ..utils.permission import USER_PERMISSION


# 全局 API 客户端，由 init 函数设置
_api_client: Optional[DSTApiClient] = None


def get_api_client() -> Optional[DSTApiClient]:
    """获取 API 客户端"""
    return _api_client


def _extract_user_id(event: Any) -> Optional[str]:
    """从事件中提取用户 ID（兼容不同适配器）"""
    if event is None:
        return None
    get_user_id = getattr(event, "get_user_id", None)
    if callable(get_user_id):
        try:
            value = get_user_id()
            return str(value) if value else None
        except Exception:
            pass
    user_id = getattr(event, "user_id", None)
    return str(user_id) if user_id is not None else None


async def resolve_room_id(qq_id: str, room_id_arg: Optional[str]) -> Optional[int]:
    """
    解析房间 ID（支持默认房间）

    Args:
        qq_id: QQ 号
        room_id_arg: 房间 ID 参数

    Returns:
        Optional[int]: 房间 ID，解析失败返回 None
    """
    if room_id_arg is not None:
        return parse_room_id(room_id_arg)

    return await get_user_default_room(qq_id)


# ========== 命令定义 + on_alconna 匹配器 ==========

set_default_room_command = Alconna(
    "dst 默认房间",
    Args["room_id", str],
    meta=CommandMeta(
        description="设置默认房间",
        usage="/dst 默认房间 <房间ID>",
        example="/dst 默认房间 1",
    ),
)

clear_default_room_command = Alconna(
    "dst 清除默认",
    meta=CommandMeta(
        description="清除默认房间",
        usage="/dst 清除默认",
        example="/dst 清除默认",
    ),
)

show_default_room_command = Alconna(
    "dst 查看默认",
    meta=CommandMeta(
        description="查看默认房间",
        usage="/dst 查看默认",
        example="/dst 查看默���",
    ),
)

# ========== on_alconna 匹配器 ==========

set_default_room_matcher = on_alconna(set_default_room_command, permission=USER_PERMISSION, priority=5, block=True)
clear_default_room_matcher = on_alconna(clear_default_room_command, permission=USER_PERMISSION, priority=5, block=True)
show_default_room_matcher = on_alconna(show_default_room_command, permission=USER_PERMISSION, priority=5, block=True)


# ========== 命令处理函数 ==========

@set_default_room_matcher.handle()
async def handle_set_default_room(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """设置默认房间"""
    if not room_id.available:
        await set_default_room_matcher.finish(format_error("用法：/dst 默认房间 <房间ID>"))
        return

    room_id_val = parse_room_id(room_id.result)
    if room_id_val is None:
        await set_default_room_matcher.finish(format_error("房间 ID 必须是正整数"))
        return

    # 验证房间是否存在
    api_client = get_api_client()
    if api_client:
        try:
            room_info = await api_client.get_room_info(room_id_val)
        except Exception as e:
            await set_default_room_matcher.finish(format_error(f"验证房间失败: {e}"))
            return
        if not room_info or not room_info.get("success"):
            await set_default_room_matcher.finish(format_error(f"房间 {room_id_val} 不存在"))
            return

    qq_id = _extract_user_id(event) or ""
    await set_user_default_room(qq_id, room_id_val)

    await set_default_room_matcher.finish(format_success(f"已设置默认房间为 {room_id_val}"))


@clear_default_room_matcher.handle()
async def handle_clear_default_room(
    event: Event,
) -> None:
    """清除默认房间"""
    qq_id = _extract_user_id(event) or ""
    default_room = await get_user_default_room(qq_id)

    if default_room is None:
        await clear_default_room_matcher.finish(format_info("未设置默认房间"))
        return

    await clear_user_default_room(qq_id)
    await clear_default_room_matcher.finish(format_success(f"已清除默认房间（原房间：{default_room}）"))


@show_default_room_matcher.handle()
async def handle_show_default_room(
    event: Event,
) -> None:
    """查看默认房间"""
    qq_id = _extract_user_id(event) or ""
    default_room = await get_user_default_room(qq_id)

    if default_room is None:
        await show_default_room_matcher.finish(format_info("未设置默认房间\n使用 /dst 默认房间 <房间ID> 设置"))
        return

    await show_default_room_matcher.finish(format_info(f"当前默认房间：{default_room}"))


def init(api_client: DSTApiClient) -> None:
    """初始化默认房间命令"""
    global _api_client
    _api_client = api_client


__all__ = [
    "set_default_room_command",
    "clear_default_room_command",
    "show_default_room_command",
    "set_default_room_matcher",
    "clear_default_room_matcher",
    "show_default_room_matcher",
    "handle_set_default_room",
    "handle_clear_default_room",
    "handle_show_default_room",
    "init",
    "resolve_room_id",
]
