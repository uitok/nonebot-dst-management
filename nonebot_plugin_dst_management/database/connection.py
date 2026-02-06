"""
数据库连接管理

提供 SQLite 连接与异步执行封装。
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, Tuple

DEFAULT_DB_PATH = "data/dst_sign.db"

_db_path_override: Optional[Path] = None



def set_db_path(path: str | Path) -> None:
    """设置数据库路径（用于测试或自定义配置）。"""
    global _db_path_override
    _db_path_override = Path(path)


def get_db_path() -> Path:
    """获取数据库路径（优先环境变量）。"""
    if (env_path := os.getenv("DST_SIGN_DB_PATH")):
        return Path(env_path)
    if _db_path_override is not None:
        return _db_path_override
    return Path(DEFAULT_DB_PATH)


def _open_connection() -> sqlite3.Connection:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _execute(query: str, params: Sequence[Any]) -> Tuple[int, int]:
    with closing(_open_connection()) as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.rowcount, cursor.lastrowid


def _execute_many(query: str, params: Iterable[Sequence[Any]]) -> int:
    with closing(_open_connection()) as conn:
        cursor = conn.executemany(query, params)
        conn.commit()
        return cursor.rowcount


def _execute_script(script: str) -> None:
    with closing(_open_connection()) as conn:
        conn.executescript(script)
        conn.commit()


def _fetch_one(query: str, params: Sequence[Any]) -> Optional[sqlite3.Row]:
    with closing(_open_connection()) as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchone()


def _fetch_all(query: str, params: Sequence[Any]) -> list[sqlite3.Row]:
    with closing(_open_connection()) as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


async def execute(query: str, params: Sequence[Any] = ()) -> int:
    """执行写入语句，返回受影响行数。"""
    rowcount, _ = _execute(query, params)
    return rowcount


async def execute_returning_id(query: str, params: Sequence[Any] = ()) -> int:
    """执行写入语句，返回自增主键。"""
    _, lastrowid = _execute(query, params)
    return lastrowid


async def execute_many(query: str, params: Iterable[Sequence[Any]]) -> int:
    """批量执行写入语句。"""
    return _execute_many(query, params)


async def execute_script(script: str) -> None:
    """执行多条 SQL 语句。"""
    _execute_script(script)


async def fetch_one(query: str, params: Sequence[Any] = ()) -> Optional[sqlite3.Row]:
    """查询单条记录。"""
    return _fetch_one(query, params)


async def fetch_all(query: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
    """查询多条记录。"""
    return _fetch_all(query, params)


__all__ = [
    "DEFAULT_DB_PATH",
    "set_db_path",
    "get_db_path",
    "execute",
    "execute_returning_id",
    "execute_many",
    "execute_script",
    "fetch_one",
    "fetch_all",
]
