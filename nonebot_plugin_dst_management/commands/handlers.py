"""
Alconna 命令处理器入口

将 Alconna 命令与 NoneBot 事件处理系统连接。
"""

from __future__ import annotations

from typing import Any, Optional

from nonebot import on_command
from nonebot.internal.adapter.bot import Bot
from nonebot.internal.adapter.event import Event
from nonebot.rule import Rule

from ..client.api_client import DSTApiClient
from ..utils.permission import check_permission
from . import (
    room_list_command,
    room_info_command,
    room_start_command,
    room_stop_command,
    room_restart_command,
    console_command,
    announce_command,
    players_command,
    kick_command,
    handle_room_list,
    handle_room_info,
    handle_room_start,
    handle_room_stop,
    handle_room_restart,
    handle_console,
    handle_announce,
    handle_players,
    handle_kick,
)


# 全局状态
_api_client: Optional[DSTApiClient] = None


def init(api_client: DSTApiClient) -> None:
    """
    初始化 Alconna 命令处理器

    Args:
        api_client: DST API 客户端实例
    """
    global _api_client
    _api_client = api_client

    # 初始化各命令模块
    from . import room, console, player
    room.init(api_client)
    console.init(api_client)
    player.init(api_client)

    # 注册命令处理器到 NoneBot
    _register_room_commands()
    _register_console_commands()
    _register_player_commands()


def _create_permission_rule(level: str):
    """创建权限规则函数"""
    async def rule(bot: Bot, event: Event) -> bool:
        return await check_permission(bot, event, level)
    return Rule(rule)


def _register_room_commands() -> None:
    """注册房间管理命令"""
    # 房间列表命令 (user 权限)
    list_cmd = on_command(
        "dst list",
        rule=_create_permission_rule("user"),
        priority=10,
        block=True,
    )

    @list_cmd.handle()
    async def _handle_list(bot: Bot, event: Event) -> None:
        result = await handle_room_list(bot, event)
        await list_cmd.finish(result)

    # 房间详情命令 (user 权限)
    info_cmd = on_command(
        "dst info",
        rule=_create_permission_rule("user"),
        priority=10,
        block=True,
    )

    @info_cmd.handle()
    async def _handle_info(bot: Bot, event: Event) -> None:
        result = await handle_room_info(bot, event)
        await info_cmd.finish(result)

    # 启动房间命令 (admin 权限)
    start_cmd = on_command(
        "dst start",
        rule=_create_permission_rule("admin"),
        priority=10,
        block=True,
    )

    @start_cmd.handle()
    async def _handle_start(bot: Bot, event: Event) -> None:
        result = await handle_room_start(bot, event)
        await start_cmd.finish(result)

    # 关闭房间命令 (admin 权限)
    stop_cmd = on_command(
        "dst stop",
        rule=_create_permission_rule("admin"),
        priority=10,
        block=True,
    )

    @stop_cmd.handle()
    async def _handle_stop(bot: Bot, event: Event) -> None:
        result = await handle_room_stop(bot, event)
        await stop_cmd.finish(result)

    # 重启房间命令 (admin 权限)
    restart_cmd = on_command(
        "dst restart",
        rule=_create_permission_rule("admin"),
        priority=10,
        block=True,
    )

    @restart_cmd.handle()
    async def _handle_restart(bot: Bot, event: Event) -> None:
        result = await handle_room_restart(bot, event)
        await restart_cmd.finish(result)


def _register_console_commands() -> None:
    """注册控制台命令"""
    # 控制台命令 (admin 权限)
    console_cmd = on_command(
        "dst console",
        rule=_create_permission_rule("admin"),
        priority=10,
        block=True,
    )

    @console_cmd.handle()
    async def _handle_console_cmd(bot: Bot, event: Event) -> None:
        result = await handle_console(bot, event)
        await console_cmd.finish(result)

    # 公告命令 (admin 权限)
    announce_cmd = on_command(
        "dst announce",
        rule=_create_permission_rule("admin"),
        priority=10,
        block=True,
    )

    @announce_cmd.handle()
    async def _handle_announce_cmd(bot: Bot, event: Event) -> None:
        result = await handle_announce(bot, event)
        await announce_cmd.finish(result)


def _register_player_commands() -> None:
    """注册玩家管理命令"""
    # 玩家列表命令 (user 权限)
    players_cmd = on_command(
        "dst players",
        rule=_create_permission_rule("user"),
        priority=10,
        block=True,
    )

    @players_cmd.handle()
    async def _handle_players_cmd(bot: Bot, event: Event) -> None:
        result = await handle_players(bot, event)
        await players_cmd.finish(result)

    # 踢出玩家命令 (admin 权限)
    kick_cmd = on_command(
        "dst kick",
        rule=_create_permission_rule("admin"),
        priority=10,
        block=True,
    )

    @kick_cmd.handle()
    async def _handle_kick_cmd(bot: Bot, event: Event) -> None:
        result = await handle_kick(bot, event)
        await kick_cmd.finish(result)


__all__ = [
    "init",
]
