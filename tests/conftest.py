"""
pytest 配置文件

为测试环境提供 NoneBot mock 和其他 fixtures
"""

import sys
from unittest.mock import MagicMock, Mock
from pathlib import Path

import pytest


# 在插件导入之前 mock NoneBot 模块
def setup_nonebot_mock():
    """设置 NoneBot Mock"""
    # 创建 mock 模块
    mock_nonebot = MagicMock()
    mock_plugin = MagicMock()
    mock_adapters = MagicMock()
    mock_adapter_onebot = MagicMock()
    mock_adapter_onebot_v11 = MagicMock()
    mock_params = MagicMock()
    mock_permission = MagicMock()
    mock_rule = MagicMock()

    # 设置 SUPERUSER 常量
    SUPERUSER = Mock()
    mock_permission.SUPERUSER = SUPERUSER
    mock_permission.Permission = Mock
    mock_rule.Rule = Mock

    # 设置 get_driver 函数
    mock_driver = MagicMock()
    mock_driver.config = MagicMock()
    # NoneBot 的生命周期装饰器在插件导入时会被直接当作 decorator 使用。
    # 测试中让它们成为“透传装饰器”，避免把被装饰函数替换成 MagicMock，
    # 这样可以在单元测试里直接调用这些函数并提升覆盖率。
    mock_driver.on_startup = lambda func: func
    mock_driver.on_shutdown = lambda func: func
    mock_nonebot.get_driver = MagicMock(return_value=mock_driver)

    # 提供一个可用的 on_command 实现，避免 @cmd.handle() 装饰器把 handler 函数替换成 MagicMock。
    class DummyCommand:
        def __init__(self):
            self.handlers = []

        def handle(self):
            def decorator(func):
                self.handlers.append(func)
                return func

            return decorator

        async def send(self, message):  # pragma: no cover
            return None

        async def finish(self, message):  # pragma: no cover
            return None

    def on_command(*args, **kwargs):  # pragma: no cover
        return DummyCommand()

    mock_nonebot.on_command = on_command

    # 注册所有 mock 模块
    sys.modules["nonebot"] = mock_nonebot
    sys.modules["nonebot.plugin"] = mock_plugin
    sys.modules["nonebot.adapters"] = mock_adapters
    sys.modules["nonebot.adapters.onebot"] = mock_adapter_onebot
    sys.modules["nonebot.adapters.onebot.v11"] = mock_adapter_onebot_v11
    sys.modules["nonebot.params"] = mock_params
    sys.modules["nonebot.permission"] = mock_permission
    sys.modules["nonebot.rule"] = mock_rule

    # Mock Message 类为简单可用对象
    class DummyMessage:
        __name__ = "Message"

        def __init__(self, text: str = "") -> None:
            self._text = str(text)

        def extract_plain_text(self) -> str:
            return self._text

        def __str__(self) -> str:
            return self._text

    mock_adapter_onebot_v11.Message = DummyMessage

    return mock_nonebot


# 在导入前设置 mock
setup_nonebot_mock()


@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录"""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def temp_dir(tmp_path_factory):
    """临时目录 fixture"""
    return tmp_path_factory.mktemp("test_data")
