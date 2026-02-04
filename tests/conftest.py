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
    mock_nonebot.get_driver = MagicMock(return_value=mock_driver)

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
