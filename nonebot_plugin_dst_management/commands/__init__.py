"""
Alconna 命令模块

提供基于 Alconna 的命令定义和权限管理。

第一阶段迁移：
- 房间管理命令 (list, info, start, stop, restart)
- 控制台命令 (console, announce)
- 玩家管理命令 (players, kick)
"""

from .base import (
    DSTCommand,
    DSTPermissionChecker,
    PermissionChecker,
    PermissionLevel,
    ADMIN_PERMISSION,
    SUPER_PERMISSION,
    USER_PERMISSION,
    make_permission_rule,
    require_admin,
    require_group,
)
from .registry import (
    CommandRegistry,
    get_registry,
    register_alconna_command,
    create_command_matcher,
)
from .room import (
    room_list_command,
    room_info_command,
    room_start_command,
    room_stop_command,
    room_restart_command,
    handle_room_list,
    handle_room_info,
    handle_room_start,
    handle_room_stop,
    handle_room_restart,
)
from .console import (
    console_command,
    announce_command,
    handle_console,
    handle_announce,
)
from .player import (
    players_command,
    kick_command,
    handle_players,
    handle_kick,
)

__all__ = [
    # Base
    "DSTCommand",
    "DSTPermissionChecker",
    "PermissionChecker",
    "PermissionLevel",
    "ADMIN_PERMISSION",
    "SUPER_PERMISSION",
    "USER_PERMISSION",
    "make_permission_rule",
    "require_admin",
    "require_group",
    # Registry
    "CommandRegistry",
    "get_registry",
    "register_alconna_command",
    "create_command_matcher",
    # Room commands
    "room_list_command",
    "room_info_command",
    "room_start_command",
    "room_stop_command",
    "room_restart_command",
    "handle_room_list",
    "handle_room_info",
    "handle_room_start",
    "handle_room_stop",
    "handle_room_restart",
    # Console commands
    "console_command",
    "announce_command",
    "handle_console",
    "handle_announce",
    # Player commands
    "players_command",
    "kick_command",
    "handle_players",
    "handle_kick",
]
