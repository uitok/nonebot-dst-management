"""
Alconna 命令模块 (on_alconna 架构)

基于 nonebot-plugin-alconna 的 on_alconna 匹配器，
命令在各子模块导入时自动注册到 NoneBot。

已迁移：
- 房间管理命令 (list, info, start, stop, restart)
- 控制台命令 (console, announce)
- 玩家管理命令 (players, kick)
- 帮助命令 (help)
- UI 配置命令 (config ui)
- AI 配置分析 (analyze)
- AI 模组推荐 (mod recommend)
- AI 模组解析 (mod parse)
- 备份管理命令 (backup list, create, restore)
- 模组管理命令 (mod search, list, add, remove, check, config save)
- 存档管理命令 (archive upload, download, replace, validate)
- 签到命令 (sign bind, sign unbind, sign)
- 默认房间命令 (默认房间, 清除默认, 查看默认)
- 自动发现命令 (room scan, room import)
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
from .help import (
    help_command,
    help_matcher,
    handle_help,
)
from .config_ui import (
    config_ui_command,
    config_ui_matcher,
    handle_config_ui,
)
from .ai_analyze import (
    analyze_command,
    analyze_matcher,
    handle_analyze,
)
from .ai_recommend import (
    recommend_command,
    recommend_matcher,
    handle_recommend,
)
from .ai_mod_parse import (
    mod_parse_command,
    mod_parse_matcher,
    handle_mod_parse,
)
from .backup import (
    backup_list_command,
    backup_create_command,
    backup_restore_command,
    backup_list_matcher,
    backup_create_matcher,
    backup_restore_matcher,
    handle_backup_list,
    handle_backup_create,
    handle_backup_restore,
)
from .mod import (
    mod_search_command,
    mod_list_command,
    mod_add_command,
    mod_remove_command,
    mod_check_command,
    mod_config_save_command,
    mod_search_matcher,
    mod_list_matcher,
    mod_add_matcher,
    mod_remove_matcher,
    mod_check_matcher,
    mod_config_save_matcher,
    handle_mod_search,
    handle_mod_list,
    handle_mod_add,
    handle_mod_remove,
    handle_mod_check,
    handle_mod_config_save,
)
from .archive import (
    archive_upload_command,
    archive_download_command,
    archive_replace_command,
    archive_validate_command,
    archive_upload_matcher,
    archive_download_matcher,
    archive_replace_matcher,
    archive_validate_matcher,
    handle_archive_upload,
    handle_archive_download,
    handle_archive_replace,
    handle_archive_validate,
)
from .sign import (
    sign_bind_command,
    sign_unbind_command,
    sign_command,
    sign_bind_matcher,
    sign_unbind_matcher,
    sign_matcher,
    handle_sign_bind,
    handle_sign_unbind,
    handle_sign,
)
from .default_room import (
    set_default_room_command,
    clear_default_room_command,
    show_default_room_command,
    set_default_room_matcher,
    clear_default_room_matcher,
    show_default_room_matcher,
    handle_set_default_room,
    handle_clear_default_room,
    handle_show_default_room,
)
from .auto_discovery import (
    scan_command,
    import_command,
    scan_matcher,
    import_matcher,
    handle_scan,
    handle_import,
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
    # Help command
    "help_command",
    "help_matcher",
    "handle_help",
    # Config UI command
    "config_ui_command",
    "config_ui_matcher",
    "handle_config_ui",
    # AI Analyze command
    "analyze_command",
    "analyze_matcher",
    "handle_analyze",
    # AI Recommend command
    "recommend_command",
    "recommend_matcher",
    "handle_recommend",
    # AI Mod Parse command
    "mod_parse_command",
    "mod_parse_matcher",
    "handle_mod_parse",
    # Backup commands
    "backup_list_command",
    "backup_create_command",
    "backup_restore_command",
    "backup_list_matcher",
    "backup_create_matcher",
    "backup_restore_matcher",
    "handle_backup_list",
    "handle_backup_create",
    "handle_backup_restore",
    # Mod commands
    "mod_search_command",
    "mod_list_command",
    "mod_add_command",
    "mod_remove_command",
    "mod_check_command",
    "mod_config_save_command",
    "mod_search_matcher",
    "mod_list_matcher",
    "mod_add_matcher",
    "mod_remove_matcher",
    "mod_check_matcher",
    "mod_config_save_matcher",
    "handle_mod_search",
    "handle_mod_list",
    "handle_mod_add",
    "handle_mod_remove",
    "handle_mod_check",
    "handle_mod_config_save",
    # Archive commands
    "archive_upload_command",
    "archive_download_command",
    "archive_replace_command",
    "archive_validate_command",
    "archive_upload_matcher",
    "archive_download_matcher",
    "archive_replace_matcher",
    "archive_validate_matcher",
    "handle_archive_upload",
    "handle_archive_download",
    "handle_archive_replace",
    "handle_archive_validate",
    # Sign commands
    "sign_bind_command",
    "sign_unbind_command",
    "sign_command",
    "sign_bind_matcher",
    "sign_unbind_matcher",
    "sign_matcher",
    "handle_sign_bind",
    "handle_sign_unbind",
    "handle_sign",
    # Default room commands
    "set_default_room_command",
    "clear_default_room_command",
    "show_default_room_command",
    "set_default_room_matcher",
    "clear_default_room_matcher",
    "show_default_room_matcher",
    "handle_set_default_room",
    "handle_clear_default_room",
    "handle_show_default_room",
    # Auto discovery commands
    "scan_command",
    "import_command",
    "scan_matcher",
    "import_matcher",
    "handle_scan",
    "handle_import",
]
