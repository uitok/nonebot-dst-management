# 单元测试示例

**文件**: tests/test_helpers_commands.py

```python
"""
测试 helpers/commands.py 中的辅助函数
"""

import pytest
from nonebot_plugin_dst_management.helpers.commands import (
    parse_room_id,
    parse_room_and_message,
    parse_console_command_args,
    escape_console_string,
)


class TestParseRoomId:
    """测试房间 ID 解析"""
    
    def test_valid_room_id(self):
        """测试有效的房间 ID"""
        assert parse_room_id("1") == 1
        assert parse_room_id("123") == 123
        assert parse_room_id("9999") == 9999
    
    def test_invalid_room_id(self):
        """测试无效的房间 ID"""
        assert parse_room_id("") is None
        assert parse_room_id("abc") is None
        assert parse_room_id("12.3") is None
        assert parse_room_id("0") is None
        assert parse_room_id("-1") is None
        assert parse_room_id(" 123 ") == 123  # 应该处理空格


class TestEscapeConsoleString:
    """测试字符串转义"""
    
    def test_escape_backslash(self):
        """测试反斜杠转义"""
        assert escape_console_string("test\\slash") == "test\\\\slash"
        assert escape_console_string("\\\\") == "\\\\\\\"
    
    def test_escape_quotes(self):
        """测试引号转义"""
        assert escape_console_string('hello "world"') == 'hello \\"world\\"'
        assert escape_console_string('"test"') == '\\"test\\"'
    
    def test_escape_mixed(self):
        """测试混合转义"""
        assert escape_console_string('test\\slash "quote"') == 'test\\\\slash \\"quote\\"'


class TestParseRoomAndMessage:
    """测试房间和消息解析"""
    
    def test_valid_input(self):
        """测试有效输入"""
        room_id, message, error = parse_room_and_message(
            "1 Hello World",
            "/dst announce <房间ID> <消息>"
        )
        assert room_id == 1
        assert message == "Hello World"
        assert error is None
    
    def test_empty_input(self):
        """测试空输入"""
        room_id, message, error = parse_room_and_message("", "")
        assert room_id is None
        assert message is None
        assert error is not None
    
    def test_missing_message(self):
        """测试缺少消息"""
        room_id, message, error = parse_room_and_message("1", "")
        assert room_id is None
        assert message is None
        assert error is not None
    
    def test_invalid_room_id(self):
        """测试无效房间 ID"""
        room_id, message, error = parse_room_and_message("abc Hello", "")
        assert room_id is None
        assert message is None
        assert error is not None


class TestParseConsoleCommandArgs:
    """测试控制台命令参数解析"""
    
    def test_command_without_world(self):
        """测试不带世界 ID 的命令"""
        room_id, world_id, command, error = parse_console_command_args(
            "1 c_announce('test')",
            "/dst console <房间ID> [世界ID] <命令>"
        )
        assert room_id == 1
        assert world_id is None
        assert command == "c_announce('test')"
        assert error is None
    
    def test_command_with_world(self):
        """测试带世界 ID 的命令"""
        room_id, world_id, command, error = parse_console_command_args(
            "1 2 c_announce('test')",
            "/dst console <房间ID> [世界ID] <命令>"
        )
        assert room_id == 1
        assert world_id == 2
        assert command == "c_announce('test')"
        assert error is None
    
    def test_multi_word_command(self):
        """测试多词命令"""
        room_id, world_id, command, error = parse_console_command_args(
            "1 c_announce('test') more text",
            "/dst console <房间ID> [世界ID] <命令>"
        )
        assert room_id == 1
        assert world_id is None
        assert command == "c_announce('test') more text"
        assert error is None
    
    def test_invalid_room_id(self):
        """测试无效房间 ID"""
        room_id, world_id, command, error = parse_console_command_args(
            "abc c_announce('test')",
            "/dst console <房间ID> [世界ID] <命令>"
        )
        assert room_id is None
        assert world_id is None
        assert command is None
        assert error is not None
    
    def test_invalid_world_id(self):
        """测试无效世界 ID"""
        room_id, world_id, command, error = parse_console_command_args(
            "1 abc c_announce('test')",
            "/dst console <房间ID> [世界ID] <命令>"
        )
        assert room_id == 1
        assert world_id is None
        assert command == "c_announce('test')"
        # 注意：这里会把 "abc" 当作命令的一部分
        assert error is None  # 或者应该返回错误？需要确认
    
    def test_missing_command(self):
        """测试缺少命令"""
        room_id, world_id, command, error = parse_console_command_args(
            "1",
            "/dst console <房间ID> [世界ID] <命令>"
        )
        # 当只有一个参数时，应该返回错误
        assert room_id == 1
        assert world_id is None
        assert command is None
        assert error is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## 运行测试

```bash
# 安装 pytest
pip install pytest pytest-asyncio

# 运行测试
pytest tests/test_helpers_commands.py -v

# 查看覆盖率
pytest tests/test_helpers_commands.py --cov=nonebot_plugin_dst_management.helpers --cov-report=html
```
