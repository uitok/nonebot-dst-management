"""
默认房间命令处理器

处理用户默认房间设置：设置、清除、查看
"""

from __future__ import annotations

from typing import Optional

from loguru import logger
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg

from ..client.api_client import DSTApiClient
from ..database import clear_user_default_room, get_user_default_room, set_user_default_room
from ..helpers.commands import parse_room_id
from ..helpers.formatters import format_error, format_info, format_success
from ..utils.permission import check_group


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


# 全局 API 客户端（用于房间验证）
_api_client: Optional[DSTApiClient] = None


def get_api_client() -> Optional[DSTApiClient]:
    """获取 API 客户端"""
    return _api_client


# 命令注册
cmd_set = on_command(
    "dst 默认房间",
    aliases={"dst setroom", "dst 设置默认房间", "dst 设默认房间"},
    priority=5,
    block=True,
)
cmd_clear = on_command(
    "dst 清除默认",
    aliases={"dst unsetroom", "dst 清除默认房间", "dst 清默认", "dst 清空默认"},
    priority=5,
    block=True,
)
cmd_show = on_command(
    "dst 查看默认",
    aliases={"dst myroom", "dst 查看默认房间", "dst 我的房间"},
    priority=5,
    block=True,
)


@cmd_set.handle()
async def handle_set_default(
    bot: Bot,
    event: MessageEvent,
    args: Message = CommandArg(),
):
    """设置默认房间"""
    if not await check_group(event):
        await cmd_set.finish(format_error("权限不足"))
        return

    room_id_str = args.extract_plain_text().strip()

    if not room_id_str:
        await cmd_set.finish(format_error("用法：/dst 默认房间 <房间ID>"))
        return

    room_id = parse_room_id(room_id_str)
    if room_id is None:
        await cmd_set.finish(format_error("房间 ID 必须是正整数"))
        return

    # 验证房间是否存在
    api_client = get_api_client()
    if api_client:
        try:
            room_info = await api_client.get_room_info(room_id)
        except Exception as e:
            logger.error(f"验证房间失败: {e}")
            await cmd_set.finish(format_error(f"验证房间失败: {e}"))
            return
        if not room_info or not room_info.get("success"):
            await cmd_set.finish(format_error(f"房间 {room_id} 不存在"))
            return

    qq_id = str(event.user_id)
    await set_user_default_room(qq_id, room_id)

    logger.info(f"用户 {qq_id} 设置默认房间为 {room_id}")
    await cmd_set.finish(format_success(f"已设置默认房间为 {room_id}"))


@cmd_clear.handle()
async def handle_clear_default(
    bot: Bot,
    event: MessageEvent,
):
    """清除默认房间"""
    if not await check_group(event):
        await cmd_clear.finish(format_error("权限不足"))
        return

    qq_id = str(event.user_id)
    default_room = await get_user_default_room(qq_id)

    if default_room is None:
        await cmd_clear.finish(format_info("未设置默认房间"))
        return

    await clear_user_default_room(qq_id)

    logger.info(f"用户 {qq_id} 清除默认房间（原房间：{default_room}）")
    await cmd_clear.finish(format_success(f"已清除默认房间（原房间：{default_room}）"))


@cmd_show.handle()
async def handle_show_default(
    bot: Bot,
    event: MessageEvent,
):
    """查看默认房间"""
    if not await check_group(event):
        await cmd_show.finish(format_error("权限不足"))
        return

    qq_id = str(event.user_id)
    default_room = await get_user_default_room(qq_id)

    if default_room is None:
        await cmd_show.finish(format_info("未设置默认房间\n使用 /dst 默认房间 <房间ID> 设置"))
        return

    await cmd_show.finish(format_info(f"当前默认房间：{default_room}"))


def init(api_client: DSTApiClient, *_: object) -> None:
    """
    初始化 handler

    Args:
        api_client: DST API 客户端
    """
    global _api_client
    _api_client = api_client
    logger.info("默认房间 handler 已初始化")


__all__ = ["init", "resolve_room_id"]
