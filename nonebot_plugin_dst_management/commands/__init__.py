"""
Alconna 命令模块 (on_alconna 架构)

基于 nonebot-plugin-alconna 的 on_alconna 匹配器，
命令在各子模块导入时自动注册到 NoneBot。

第二阶段迁移：
- 房间管理命令 (list, info, start, stop, restart)
- 控制台命令 (console, announce)
- 玩家管理命令 (players, kick)
"""

from .base import (
    PermissionChecker,
    PermissionLevel,
    ADMIN_PERMISSION,
    SUPER_PERMISSION,
    USER_PERMISSION,
    make_permission_rule,
)
from .registry import (
    CommandRegistry,
    get_registry,
)
from .room import (
    room_list_command,
    room_info_command,
    room_start_command,
    room_stop_command,
    room_restart_command,
    list_matcher,
    info_matcher,
    start_matcher,
    stop_matcher,
    restart_matcher,
    handle_room_list,
    handle_room_info,
    handle_room_start,
    handle_room_stop,
    handle_room_restart,
)
from .console import (
    console_command,
    announce_command,
    console_matcher,
    announce_matcher,
    handle_console,
    handle_announce,
)
from .player import (
    players_command,
    kick_command,
    players_matcher,
    kick_matcher,
    handle_players,
    handle_kick,
)

__all__ = [
    # Base
    "PermissionChecker",
    "PermissionLevel",
    "ADMIN_PERMISSION",
    "SUPER_PERMISSION",
    "USER_PERMISSION",
    "make_permission_rule",
    # Registry
    "CommandRegistry",
    "get_registry",
    # Room commands
    "room_list_command",
    "room_info_command",
    "room_start_command",
    "room_stop_command",
    "room_restart_command",
    "list_matcher",
    "info_matcher",
    "start_matcher",
    "stop_matcher",
    "restart_matcher",
    "handle_room_list",
    "handle_room_info",
    "handle_room_start",
    "handle_room_stop",
    "handle_room_restart",
    # Console commands
    "console_command",
    "announce_command",
    "console_matcher",
    "announce_matcher",
    "handle_console",
    "handle_announce",
    # Player commands
    "players_command",
    "kick_command",
    "players_matcher",
    "kick_matcher",
    "handle_players",
    "handle_kick",
]
