"""
签到系统数据库模型与 CRUD。
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

from .connection import execute, execute_returning_id, execute_script, fetch_all, fetch_one


SIGN_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS sign_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qq_id TEXT NOT NULL,
    ku_id TEXT NOT NULL,
    room_id INTEGER NOT NULL,
    player_name TEXT,
    bind_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sign_time DATE,
    sign_count INTEGER DEFAULT 0,
    continuous_days INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    total_points INTEGER DEFAULT 0,
    UNIQUE(qq_id, room_id)
);
"""

SIGN_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS sign_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qq_id TEXT NOT NULL,
    room_id INTEGER NOT NULL,
    sign_date DATE NOT NULL,
    reward_level INTEGER NOT NULL,
    reward_items TEXT,
    status INTEGER DEFAULT 1,
    sign_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(qq_id, room_id, sign_date)
);
"""

SIGN_REWARDS_TABLE = """
CREATE TABLE IF NOT EXISTS sign_rewards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level INTEGER NOT NULL UNIQUE,
    continuous_days INTEGER NOT NULL,
    reward_items TEXT NOT NULL,
    bonus_points INTEGER DEFAULT 0,
    description TEXT
);
"""

USER_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS user_settings (
    qq_id TEXT PRIMARY KEY,
    default_room_id INTEGER,
    last_room_id INTEGER,
    ui_mode TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

@dataclass
class SignUser:
    id: int
    qq_id: str
    ku_id: str
    room_id: int
    player_name: Optional[str]
    bind_time: Optional[datetime]
    last_sign_time: Optional[date]
    sign_count: int
    continuous_days: int
    level: int
    total_points: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "SignUser":
        return cls(
            id=row["id"],
            qq_id=row["qq_id"],
            ku_id=row["ku_id"],
            room_id=row["room_id"],
            player_name=row["player_name"],
            bind_time=_parse_datetime(row["bind_time"]),
            last_sign_time=_parse_date(row["last_sign_time"]),
            sign_count=row["sign_count"],
            continuous_days=row["continuous_days"],
            level=row["level"],
            total_points=row["total_points"],
        )


@dataclass
class SignRecord:
    id: int
    qq_id: str
    room_id: int
    sign_date: date
    reward_level: int
    reward_items: Optional[list[dict[str, Any]]]
    sign_time: Optional[datetime]
    status: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "SignRecord":
        return cls(
            id=row["id"],
            qq_id=row["qq_id"],
            room_id=row["room_id"],
            sign_date=_parse_date(row["sign_date"]) or date.min,
            reward_level=row["reward_level"],
            reward_items=_load_json(row["reward_items"]),
            sign_time=_parse_datetime(row["sign_time"]),
            status=row["status"] if "status" in row.keys() else 1,
        )


@dataclass
class PendingSignRecord:
    id: int
    qq_id: str
    ku_id: str
    room_id: int
    sign_date: date
    reward_level: int
    reward_items: Optional[list[dict[str, Any]]]
    sign_time: Optional[datetime]
    status: int

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "PendingSignRecord":
        return cls(
            id=row["id"],
            qq_id=row["qq_id"],
            ku_id=row["ku_id"],
            room_id=row["room_id"],
            sign_date=_parse_date(row["sign_date"]) or date.min,
            reward_level=row["reward_level"],
            reward_items=_load_json(row["reward_items"]),
            sign_time=_parse_datetime(row["sign_time"]),
            status=row["status"] if "status" in row.keys() else 0,
        )


@dataclass
class SignReward:
    id: int
    level: int
    continuous_days: int
    reward_items: list[dict[str, Any]]
    bonus_points: int
    description: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "SignReward":
        return cls(
            id=row["id"],
            level=row["level"],
            continuous_days=row["continuous_days"],
            reward_items=_load_json(row["reward_items"]) or [],
            bonus_points=row["bonus_points"],
            description=row["description"],
        )


def _parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _dump_json(value: Optional[object]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _load_json(value: Optional[str]) -> Optional[list[dict[str, Any]]]:
    if not value:
        return None
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return None
    if isinstance(data, list):
        return data
    return None


async def init_db() -> None:
    """初始化数据库表。"""
    await execute_script(
        "\n".join(
            [
                SIGN_USERS_TABLE,
                SIGN_RECORDS_TABLE,
                SIGN_REWARDS_TABLE,
                USER_SETTINGS_TABLE,
            ]
        )
    )
    await _ensure_sign_records_status()
    await _ensure_user_settings_last_room_id()
    await _ensure_user_settings_ui_mode()


async def _ensure_sign_records_status() -> None:
    rows = await fetch_all("PRAGMA table_info(sign_records)")
    columns = {row["name"] for row in rows}
    if "status" not in columns:
        await execute("ALTER TABLE sign_records ADD COLUMN status INTEGER DEFAULT 1")
    await execute("UPDATE sign_records SET status = 1 WHERE status IS NULL")


async def _ensure_user_settings_ui_mode() -> None:
    rows = await fetch_all("PRAGMA table_info(user_settings)")
    columns = {row["name"] for row in rows}
    if "ui_mode" not in columns:
        await execute("ALTER TABLE user_settings ADD COLUMN ui_mode TEXT")

async def _ensure_user_settings_last_room_id() -> None:
    rows = await fetch_all("PRAGMA table_info(user_settings)")
    columns = {row["name"] for row in rows}
    if "last_room_id" not in columns:
        await execute("ALTER TABLE user_settings ADD COLUMN last_room_id INTEGER")




async def create_user_binding(
    qq_id: str,
    ku_id: str,
    room_id: int,
    player_name: Optional[str] = None,
) -> Optional[int]:
    """创建用户绑定。"""
    try:
        return await execute_returning_id(
            """
            INSERT INTO sign_users (qq_id, ku_id, room_id, player_name)
            VALUES (?, ?, ?, ?)
            """,
            (qq_id, ku_id, room_id, player_name),
        )
    except sqlite3.IntegrityError:
        return None


async def get_user_binding(qq_id: str, room_id: int) -> Optional[SignUser]:
    """根据 QQ 与房间获取绑定信息。"""
    row = await fetch_one(
        """
        SELECT * FROM sign_users
        WHERE qq_id = ? AND room_id = ?
        """,
        (qq_id, room_id),
    )
    return SignUser.from_row(row) if row else None


async def get_user_binding_by_ku(ku_id: str, room_id: int) -> Optional[SignUser]:
    """根据 KU_ID 获取绑定信息。"""
    row = await fetch_one(
        """
        SELECT * FROM sign_users
        WHERE ku_id = ? AND room_id = ?
        """,
        (ku_id, room_id),
    )
    return SignUser.from_row(row) if row else None


async def update_user_sign_stats(
    qq_id: str,
    room_id: int,
    last_sign_time: Optional[date],
    sign_count: int,
    continuous_days: int,
    level: int,
    total_points: int,
) -> int:
    """更新用户签到信息。"""
    return await execute(
        """
        UPDATE sign_users
        SET last_sign_time = ?,
            sign_count = ?,
            continuous_days = ?,
            level = ?,
            total_points = ?
        WHERE qq_id = ? AND room_id = ?
        """,
        (
            last_sign_time.isoformat() if last_sign_time else None,
            sign_count,
            continuous_days,
            level,
            total_points,
            qq_id,
            room_id,
        ),
    )


async def delete_user_binding(qq_id: str, room_id: int) -> int:
    """删除用户绑定。"""
    return await execute(
        """
        DELETE FROM sign_users
        WHERE qq_id = ? AND room_id = ?
        """,
        (qq_id, room_id),
    )


async def create_sign_record(
    qq_id: str,
    room_id: int,
    sign_date: date,
    reward_level: int,
    reward_items: Optional[object] = None,
    status: int = 1,
) -> Optional[int]:
    """创建签到记录。"""
    try:
        return await execute_returning_id(
            """
            INSERT INTO sign_records (qq_id, room_id, sign_date, reward_level, reward_items, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                qq_id,
                room_id,
                sign_date.isoformat(),
                reward_level,
                _dump_json(reward_items),
                status,
            ),
        )
    except sqlite3.IntegrityError:
        return None


async def get_sign_record(
    qq_id: str,
    sign_date: date,
    room_id: Optional[int] = None,
) -> Optional[SignRecord]:
    """获取签到记录。"""
    if room_id is None:
        row = await fetch_one(
            """
            SELECT * FROM sign_records
            WHERE qq_id = ? AND sign_date = ?
            """,
            (qq_id, sign_date.isoformat()),
        )
    else:
        row = await fetch_one(
            """
            SELECT * FROM sign_records
            WHERE qq_id = ? AND sign_date = ? AND room_id = ?
            """,
            (qq_id, sign_date.isoformat(), room_id),
        )
    return SignRecord.from_row(row) if row else None


async def list_sign_records(qq_id: str, room_id: int) -> list[SignRecord]:
    """列出用户签到记录。"""
    rows = await fetch_all(
        """
        SELECT * FROM sign_records
        WHERE qq_id = ? AND room_id = ?
        ORDER BY sign_date DESC
        """,
        (qq_id, room_id),
    )
    return [SignRecord.from_row(row) for row in rows]


async def list_pending_sign_records() -> list[PendingSignRecord]:
    """列出待发放奖励的签到记录。"""
    rows = await fetch_all(
        """
        SELECT r.*, u.ku_id
        FROM sign_records AS r
        JOIN sign_users AS u
            ON u.qq_id = r.qq_id AND u.room_id = r.room_id
        WHERE r.status = 0
        ORDER BY r.sign_time ASC
        """
    )
    return [PendingSignRecord.from_row(row) for row in rows]


async def update_sign_record_status(record_id: int, status: int) -> int:
    """更新签到记录发放状态。"""
    return await execute(
        """
        UPDATE sign_records
        SET status = ?
        WHERE id = ?
        """,
        (status, record_id),
    )


async def delete_sign_record(qq_id: str, sign_date: date, room_id: Optional[int] = None) -> int:
    """删除签到记录。"""
    if room_id is None:
        return await execute(
            """
            DELETE FROM sign_records
            WHERE qq_id = ? AND sign_date = ?
            """,
            (qq_id, sign_date.isoformat()),
        )
    return await execute(
        """
        DELETE FROM sign_records
        WHERE qq_id = ? AND sign_date = ? AND room_id = ?
        """,
        (qq_id, sign_date.isoformat(), room_id),
    )


async def create_sign_reward(
    level: int,
    continuous_days: int,
    reward_items: object,
    bonus_points: int = 0,
    description: Optional[str] = None,
) -> Optional[int]:
    """创建奖励配置。"""
    try:
        return await execute_returning_id(
            """
            INSERT INTO sign_rewards (level, continuous_days, reward_items, bonus_points, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (level, continuous_days, _dump_json(reward_items), bonus_points, description),
        )
    except sqlite3.IntegrityError:
        return None


async def list_sign_rewards() -> list[SignReward]:
    """列出奖励配置。"""
    rows = await fetch_all("SELECT * FROM sign_rewards ORDER BY level ASC")
    return [SignReward.from_row(row) for row in rows]


async def get_sign_reward(level: int) -> Optional[SignReward]:
    """获取奖励配置。"""
    row = await fetch_one(
        """
        SELECT * FROM sign_rewards
        WHERE level = ?
        """,
        (level,),
    )
    return SignReward.from_row(row) if row else None


async def update_sign_reward(
    level: int,
    continuous_days: int,
    reward_items: object,
    bonus_points: int = 0,
    description: Optional[str] = None,
) -> int:
    """更新奖励配置。"""
    return await execute(
        """
        UPDATE sign_rewards
        SET continuous_days = ?,
            reward_items = ?,
            bonus_points = ?,
            description = ?
        WHERE level = ?
        """,
        (continuous_days, _dump_json(reward_items), bonus_points, description, level),
    )


async def delete_sign_reward(level: int) -> int:
    """删除奖励配置。"""
    return await execute(
        """
        DELETE FROM sign_rewards
        WHERE level = ?
        """,
        (level,),
    )


async def set_user_default_room(qq_id: str, room_id: int) -> int:
    """设置用户默认房间（存在则更新）。"""
    return await execute(
        """
        INSERT INTO user_settings (qq_id, default_room_id, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(qq_id)
        DO UPDATE SET default_room_id = excluded.default_room_id,
                      updated_at = CURRENT_TIMESTAMP
        """,
        (qq_id, room_id),
    )


async def get_user_default_room(qq_id: str) -> Optional[int]:
    """获取用户默认房间。"""
    row = await fetch_one(
        """
        SELECT default_room_id
        FROM user_settings
        WHERE qq_id = ?
        """,
        (qq_id,),
    )
    if not row:
        return None
    return row["default_room_id"]


async def clear_user_default_room(qq_id: str) -> int:
    """清除用户默认房间。"""
    return await execute(
        """
        UPDATE user_settings
        SET default_room_id = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE qq_id = ?
        """,
        (qq_id,),
    )


async def set_user_ui_mode(qq_id: str, ui_mode: str) -> int:
    """设置用户 UI 展示模式（存在则更新）。"""
    if ui_mode not in {"text", "markdown"}:
        raise ValueError(f"Invalid ui_mode: {ui_mode}")
    return await execute(
        """
        INSERT INTO user_settings (qq_id, ui_mode, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(qq_id)
        DO UPDATE SET ui_mode = excluded.ui_mode,
                      updated_at = CURRENT_TIMESTAMP
        """,
        (qq_id, ui_mode),
    )


async def get_user_ui_mode(qq_id: str) -> Optional[str]:
    """获取用户 UI 展示模式。"""
    row = await fetch_one(
        """
        SELECT ui_mode
        FROM user_settings
        WHERE qq_id = ?
        """,
        (qq_id,),
    )
    if not row:
        return None
    value = row["ui_mode"]
    if not value:
        return None
    return str(value)


async def clear_user_ui_mode(qq_id: str) -> int:
    """清除用户 UI 展示模式。"""
    return await execute(
        """
        UPDATE user_settings
        SET ui_mode = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE qq_id = ?
        """,
        (qq_id,),
    )


async def set_user_last_room(qq_id: str, room_id: int) -> int:
    """设置用户/群组最近操作房间（存在则更新）。"""
    return await execute(
        """
        INSERT INTO user_settings (qq_id, last_room_id, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(qq_id)
        DO UPDATE SET last_room_id = excluded.last_room_id,
                      updated_at = CURRENT_TIMESTAMP
        """,
        (qq_id, room_id),
    )


async def get_user_last_room(qq_id: str) -> Optional[int]:
    """获取用户/群组最近操作房间。"""
    row = await fetch_one(
        """
        SELECT last_room_id
        FROM user_settings
        WHERE qq_id = ?
        """,
        (qq_id,),
    )
    if not row:
        return None
    return row["last_room_id"]


async def clear_user_last_room(qq_id: str) -> int:
    """清除用户/群组最近操作房间。"""
    return await execute(
        """
        UPDATE user_settings
        SET last_room_id = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE qq_id = ?
        """,
        (qq_id,),
    )


__all__ = [
    "SignUser",
    "SignRecord",
    "PendingSignRecord",
    "SignReward",
    "init_db",
    "create_user_binding",
    "get_user_binding",
    "get_user_binding_by_ku",
    "update_user_sign_stats",
    "delete_user_binding",
    "create_sign_record",
    "get_sign_record",
    "list_sign_records",
    "list_pending_sign_records",
    "delete_sign_record",
    "update_sign_record_status",
    "create_sign_reward",
    "list_sign_rewards",
    "get_sign_reward",
    "update_sign_reward",
    "delete_sign_reward",
    "set_user_default_room",
    "get_user_default_room",
    "clear_user_default_room",
    "set_user_ui_mode",
    "get_user_ui_mode",
    "clear_user_ui_mode",
]
