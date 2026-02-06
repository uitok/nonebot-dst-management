"""
Room context helper (Phase B Smart).

This module implements "session locking" / context awareness for room-scoped commands:
- Remember the last successfully operated room per user and per group.
- When a command omits the room id, fall back to last room, then default room.

Persistence: stored in the sqlite `user_settings.last_room_id` column.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from loguru import logger

from .commands import parse_room_id
from ..database import get_user_default_room, get_user_last_room, set_user_last_room


class RoomSource(str, Enum):
    """Where the room id came from."""

    ARG = "arg"
    LAST = "last"
    DEFAULT = "default"


@dataclass(frozen=True)
class RoomResolution:
    room_id: int
    source: RoomSource
    # For LAST source, indicates which context key matched ("group:..." or user_id).
    context_key: Optional[str] = None


def _extract_user_id(event: Any) -> Optional[str]:
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


def _extract_group_id(event: Any) -> Optional[str]:
    if event is None:
        return None
    if (group_id := getattr(event, "group_id", None)) is not None:
        return str(group_id)
    if (group_openid := getattr(event, "group_openid", None)) is not None:
        return str(group_openid)
    if (guild_id := getattr(event, "guild_id", None)) is not None and (
        channel_id := getattr(event, "channel_id", None)
    ) is not None:
        return f"{guild_id}:{channel_id}"
    return None


def _iter_context_keys(event: Any) -> list[str]:
    # Priority: group -> user
    keys: list[str] = []
    group_id = _extract_group_id(event)
    if group_id:
        keys.append(f"group:{group_id}")
    user_id = _extract_user_id(event)
    if user_id:
        keys.append(user_id)
    return keys


async def resolve_room_id(event: Any, room_id_arg: Optional[str]) -> Optional[RoomResolution]:
    """Resolve room id with context awareness.

    Resolution priority:
    1) Explicit room id argument (must be a valid positive integer)
    2) Last operated room (group context first, then user context)
    3) Default room (per user)

    Returns None when:
    - room_id_arg is provided but invalid
    - room_id_arg omitted and there is no stored context/default room
    """

    if room_id_arg is not None and str(room_id_arg).strip():
        room_id = parse_room_id(str(room_id_arg))
        if room_id is None:
            return None
        return RoomResolution(room_id=room_id, source=RoomSource.ARG)

    for key in _iter_context_keys(event):
        try:
            last = await get_user_last_room(key)
        except Exception as exc:
            logger.warning(f"读取 last_room_id 失败({key}): {exc}")
            continue
        if last is not None:
            return RoomResolution(room_id=int(last), source=RoomSource.LAST, context_key=key)

    user_id = _extract_user_id(event)
    if user_id:
        try:
            default_room = await get_user_default_room(user_id)
        except Exception as exc:
            logger.warning(f"读取 default_room_id 失败({user_id}): {exc}")
            default_room = None
        if default_room is not None:
            return RoomResolution(room_id=int(default_room), source=RoomSource.DEFAULT)

    return None


async def remember_room(event: Any, room_id: int) -> None:
    """Persist last operated room for group/user context (best-effort)."""

    if room_id <= 0:
        return
    keys = _iter_context_keys(event)
    if not keys:
        return

    for key in keys:
        try:
            await set_user_last_room(key, int(room_id))
        except Exception as exc:
            logger.warning(f"写入 last_room_id 失败({key}): {exc}")


__all__ = ["RoomResolution", "RoomSource", "resolve_room_id", "remember_room"]

