"""
Compatibility wrapper.

Phase A introduces `nonebot_plugin_dst_management.helpers.formatters` as the single
source of truth for emoji/UI strings. Keep `utils.formatter` to avoid breaking
imports in existing code/tests.
"""

from __future__ import annotations

from ..helpers.formatters import (  # noqa: F401
    format_room_list,
    format_room_detail,
    format_players,
    format_player_list,
    format_backups,
    format_backup_list,
    format_error,
    format_success,
    format_info,
    format_warning,
    format_loading,
    format_table,
)


__all__ = [
    "format_room_list",
    "format_room_detail",
    "format_players",
    "format_player_list",
    "format_backups",
    "format_backup_list",
    "format_error",
    "format_success",
    "format_info",
    "format_warning",
    "format_loading",
    "format_table",
]
