"""
默认房间功能测试
"""

import pytest

from nonebot_plugin_dst_management.handlers import default_room


class TestGetStorageKey:
    """测试存储 key 生成"""

    def test_session_id_format(self):
        """测试会话 ID 格式"""
        # OneBot v11 session_id 格式: group_user_id
        key = default_room.get_storage_key("123456_789")
        assert key == "dst_default_room:123456_789"


class TestDefaultRoom:
    """默认房间功能测试"""

    def test_set_and_get_default_room(self):
        """测试设���和获取默认房间"""
        storage = {}
        session_id = "test_group_test_user"

        # 未设置时返回 None
        assert default_room.get_default_room(storage, session_id) is None

        # 设置默认房间
        default_room.set_default_room(storage, session_id, 2)
        assert default_room.get_default_room(storage, session_id) == 2

        # 更新默认房间
        default_room.set_default_room(storage, session_id, 5)
        assert default_room.get_default_room(storage, session_id) == 5

    def test_clear_default_room(self):
        """测试清除默认房间"""
        storage = {}
        session_id = "test_group_test_user"

        # 设置默认房间
        default_room.set_default_room(storage, session_id, 3)
        assert default_room.get_default_room(storage, session_id) == 3

        # 清除默认房间
        default_room.clear_default_room(storage, session_id)
        assert default_room.get_default_room(storage, session_id) is None

    def test_resolve_room_id_with_arg(self):
        """测试解析房间 ID（提供参数）"""
        storage = {}
        session_id = "test_group_test_user"

        # 设置默认房间
        default_room.set_default_room(storage, session_id, 2)

        # 提供参数时，使用参数值
        assert default_room.resolve_room_id(storage, session_id, "5") == 5
        assert default_room.resolve_room_id(storage, session_id, "10") == 10

    def test_resolve_room_id_without_arg(self):
        """测试解析房间 ID（使用默认）"""
        storage = {}
        session_id = "test_group_test_user"

        # 未设置默认房间
        assert default_room.resolve_room_id(storage, session_id, None) is None

        # 设置默认房间
        default_room.set_default_room(storage, session_id, 3)

        # 不提供参数时，使用默认房间
        assert default_room.resolve_room_id(storage, session_id, None) == 3

    def test_resolve_room_id_invalid_arg(self):
        """测试解析房间 ID（无效参数）"""
        storage = {}
        session_id = "test_group_test_user"

        # 设置默认房间
        default_room.set_default_room(storage, session_id, 2)

        # 无效参数
        assert default_room.resolve_room_id(storage, session_id, "abc") is None
        assert default_room.resolve_room_id(storage, session_id, "") is None

    def test_resolve_room_id_non_positive(self):
        """测试解析房间 ID（非正数）"""
        storage = {}
        session_id = "test_group_test_user"

        # 非正数应返回 None
        assert default_room.resolve_room_id(storage, session_id, "0") is None
        assert default_room.resolve_room_id(storage, session_id, "-1") is None
        # 正数应该正常返回
        assert default_room.resolve_room_id(storage, session_id, "999") == 999

    def test_multiple_sessions(self):
        """测试多会话隔离"""
        storage = {}

        # 会话 A（用户在群 1）
        session_a = "group1_user123"
        default_room.set_default_room(storage, session_a, 1)

        # 会话 B（同一用户在群 2）
        session_b = "group2_user123"
        default_room.set_default_room(storage, session_b, 2)

        # 验证隔离
        assert default_room.get_default_room(storage, session_a) == 1
        assert default_room.get_default_room(storage, session_b) == 2

        # 会话 A 清除不影响会话 B
        default_room.clear_default_room(storage, session_a)
        assert default_room.get_default_room(storage, session_a) is None
        assert default_room.get_default_room(storage, session_b) == 2

    def test_different_users_same_group(self):
        """测试同一群的不同用户"""
        storage = {}

        # 用户 A
        session_a = "group1_userA"
        default_room.set_default_room(storage, session_a, 1)

        # 用户 B
        session_b = "group1_userB"
        default_room.set_default_room(storage, session_b, 2)

        # 验证隔离
        assert default_room.get_default_room(storage, session_a) == 1
        assert default_room.get_default_room(storage, session_b) == 2


class TestResolveRoomIdIntegration:
    """解析房间 ID 集成测试"""

    def test_resolve_priority(self):
        """测试参数优先级高于默认房间"""
        storage = {}
        session_id = "test_group_test_user"

        # 设置默认房间为 2
        default_room.set_default_room(storage, session_id, 2)

        # 提供参数时，优先使用参数
        assert default_room.resolve_room_id(storage, session_id, "5") == 5

        # 不提供参数时，使用默认房间
        assert default_room.resolve_room_id(storage, session_id, None) == 2

    def test_resolve_with_no_default(self):
        """测试无默认房间时的行为"""
        storage = {}
        session_id = "test_group_test_user"

        # 未设置默认房间，提供参数
        assert default_room.resolve_room_id(storage, session_id, "3") == 3

        # 未设置默认房间，不提供参数
        assert default_room.resolve_room_id(storage, session_id, None) is None
