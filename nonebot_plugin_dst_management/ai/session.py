"""
AI 会话与上下文管理

提供多轮对话历史管理与上下文窗口控制。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
import threading
from typing import Dict, List

from .base import ChatMessage


@dataclass
class ChatSession:
    """单个会话数据"""

    session_id: str
    messages: List[ChatMessage] = field(default_factory=list)
    last_active: float = field(default_factory=time.monotonic)

    def touch(self) -> None:
        self.last_active = time.monotonic()


class SessionManager:
    """会话管理器"""

    def __init__(self, max_rounds: int = 6, ttl_seconds: int = 3600) -> None:
        self.max_rounds = max_rounds
        self.ttl_seconds = ttl_seconds
        self._sessions: Dict[str, ChatSession] = {}
        self._lock = threading.RLock()

    def get_session(self, session_id: str) -> ChatSession:
        with self._lock:
            self._cleanup_expired()
            session = self._sessions.get(session_id)
            if session is None:
                session = ChatSession(session_id=session_id)
                self._sessions[session_id] = session
            elif self._is_expired(session):
                session = ChatSession(session_id=session_id)
                self._sessions[session_id] = session
            session.touch()
            return session

    def reset_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def list_history(self, session_id: str) -> List[ChatMessage]:
        with self._lock:
            self._cleanup_expired()
            session = self._sessions.get(session_id)
            if not session or self._is_expired(session):
                self._sessions.pop(session_id, None)
                return []
            session.touch()
            return list(session.messages)

    def append_turn(self, session_id: str, user_content: str, assistant_content: str) -> None:
        with self._lock:
            session = self.get_session(session_id)
            session.messages.append({"role": "user", "content": user_content})
            session.messages.append({"role": "assistant", "content": assistant_content})
            self._trim_session(session)

    def append_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            session = self.get_session(session_id)
            session.messages.append({"role": role, "content": content})
            self._trim_session(session)

    def _trim_session(self, session: ChatSession) -> None:
        if self.max_rounds <= 0:
            return
        max_messages = self.max_rounds * 2
        if len(session.messages) > max_messages:
            session.messages = session.messages[-max_messages:]

    def _is_expired(self, session: ChatSession) -> bool:
        if self.ttl_seconds <= 0:
            return False
        return time.monotonic() - session.last_active > self.ttl_seconds

    def _cleanup_expired(self) -> None:
        if self.ttl_seconds <= 0:
            return
        now = time.monotonic()
        expired: List[str] = []
        for key, session in self._sessions.items():
            if now - session.last_active > self.ttl_seconds:
                expired.append(key)
        for key in expired:
            self._sessions.pop(key, None)
