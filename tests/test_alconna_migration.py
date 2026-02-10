"""
Alconna 迁移测试脚本

测试第一阶段 Alconna 迁移的功能：
- 命令定义
- 权限系统
- 命令处理函数
"""

import importlib
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def _purge_plugin_modules():
    """移除所有已缓存的插件模块，以便每次测试重新导入。"""
    to_remove = [
        key for key in sys.modules
        if key.startswith("nonebot_plugin_dst_management")
    ]
    for key in to_remove:
        del sys.modules[key]


def _create_namespace_package(name: str) -> types.ModuleType:
    """创建一个空的命名空间包模块，不会触发 __init__.py。"""
    mod = types.ModuleType(name)
    mod.__path__ = [
        str(project_root / name.replace(".", "/"))
    ]
    mod.__package__ = name
    return mod


def setup_common_mocks():
    """设置通用 mock 模块。

    策略：
    - 将 nonebot_plugin_dst_management 注册为命名空间包（不执行 __init__.py）
    - 仅 mock 外部依赖（nonebot, loguru, database, ai, services 等）
    - 让真正的子模块（utils, helpers, commands, client）正常加载
    """
    _purge_plugin_modules()

    # ========== Mock NoneBot 核心 ==========
    mock_nonebot = MagicMock()
    mock_driver = MagicMock()
    mock_nonebot.get_driver = MagicMock(return_value=mock_driver)

    mock_matcher = MagicMock()
    mock_matcher.handle = MagicMock(return_value=lambda f: f)
    mock_matcher.finish = AsyncMock()
    mock_nonebot.on_command = MagicMock(return_value=mock_matcher)

    sys.modules['nonebot'] = mock_nonebot

    # Mock NoneBot 子模块
    mock_permission = MagicMock()
    mock_superuser = AsyncMock(return_value=False)
    mock_permission.SUPERUSER = mock_superuser
    sys.modules['nonebot.permission'] = mock_permission

    sys.modules['nonebot.adapter'] = MagicMock()
    sys.modules['nonebot.internal'] = MagicMock()
    sys.modules['nonebot.internal.adapter'] = MagicMock()
    sys.modules['nonebot.internal.adapter.bot'] = MagicMock()
    sys.modules['nonebot.internal.adapter.event'] = MagicMock()
    sys.modules['nonebot.plugin'] = MagicMock()

    mock_rule_module = MagicMock()
    mock_rule_module.Rule = MagicMock()
    sys.modules['nonebot.rule'] = mock_rule_module

    # Mock OneBot adapter (used by formatters.py)
    mock_ob_message = MagicMock()
    mock_ob_message.Message = str  # Make Message act like str
    sys.modules['nonebot.adapters'] = MagicMock()
    sys.modules['nonebot.adapters.onebot'] = MagicMock()
    sys.modules['nonebot.adapters.onebot.v11'] = mock_ob_message

    # ========== Mock loguru ==========
    sys.modules['loguru'] = MagicMock()

    # ========== 注册主包为命名空间包 ==========
    pkg = _create_namespace_package("nonebot_plugin_dst_management")
    sys.modules["nonebot_plugin_dst_management"] = pkg

    # 注册真实子包的命名空间
    for subpkg in ["utils", "helpers", "client", "commands"]:
        full_name = f"nonebot_plugin_dst_management.{subpkg}"
        sub = _create_namespace_package(full_name)
        sys.modules[full_name] = sub
        setattr(pkg, subpkg, sub)

    # ========== Mock database 模块 ==========
    mock_db = MagicMock()
    mock_db.get_user_last_room = AsyncMock(return_value=None)
    mock_db.get_user_default_room = AsyncMock(return_value=None)
    mock_db.set_user_last_room = AsyncMock()
    mock_db.get_user_ui_mode = AsyncMock(return_value=None)
    sys.modules['nonebot_plugin_dst_management.database'] = mock_db

    # ========== Mock AI config ==========
    # 创建一个真正的 Pydantic AIConfig stub，避免 MagicMock 导致 schema 错误
    from pydantic import BaseModel
    class AIConfigStub(BaseModel):
        enabled: bool = False

    mock_ai_config_module = types.ModuleType("nonebot_plugin_dst_management.ai.config")
    mock_ai_config_module.AIConfig = AIConfigStub
    sys.modules['nonebot_plugin_dst_management.ai'] = MagicMock()
    sys.modules['nonebot_plugin_dst_management.ai.config'] = mock_ai_config_module

    # ========== Mock config 模块 ==========
    # 为 config.py 提供 get_dst_config（避免 __init__.py 触发 get_driver）
    config_mod = importlib.import_module("nonebot_plugin_dst_management.config")
    sys.modules['nonebot_plugin_dst_management.config'] = config_mod
    setattr(pkg, "config", config_mod)

    # ========== Mock services/monitors ==========
    mock_sign_monitor = MagicMock()
    mock_sign_monitor.get_sign_monitor = MagicMock(return_value=None)
    sys.modules['nonebot_plugin_dst_management.services'] = MagicMock()
    sys.modules['nonebot_plugin_dst_management.services.monitors'] = MagicMock()
    sys.modules['nonebot_plugin_dst_management.services.monitors.sign_monitor'] = mock_sign_monitor

    # ========== Create mock bot/event ==========
    mock_bot = MagicMock()
    mock_event = MagicMock()
    mock_event.get_user_id = MagicMock(return_value="12345")
    mock_event.group_id = 67890

    return mock_bot, mock_event


def test_alconna_import():
    """测试 Alconna 库导入"""
    print("=" * 60)
    print("📦 测试 Alconna 库导入")
    print("=" * 60)

    try:
        from arclet.alconna import Alconna, Args, CommandMeta, Option
        print("✅ Alconna 库导入成功")

        test_cmd = Alconna(
            "test",
            Args["arg1", str, None],
            meta=CommandMeta(description="测试命令")
        )
        print(f"   命令路径: {test_cmd.path}")
        print(f"   命令参数: {test_cmd.args}")

        return True
    except Exception as e:
        print(f"❌ Alconna 库导入失败: {e}")
        return False


def test_permission_system():
    """测试权限系统"""
    print("\n" + "=" * 60)
    print("🔒 测试权限系统")
    print("=" * 60)

    try:
        setup_common_mocks()

        # 强制重新加载权限模块
        mod = importlib.import_module("nonebot_plugin_dst_management.utils.permission")
        importlib.reload(mod)

        PermissionLevel = mod.PermissionLevel
        PermissionChecker = mod.PermissionChecker
        ADMIN_PERMISSION = mod.ADMIN_PERMISSION
        USER_PERMISSION = mod.USER_PERMISSION
        SUPER_PERMISSION = mod.SUPER_PERMISSION
        make_permission_rule = mod.make_permission_rule

        print("✅ 权限系统模块加载成功")
        print(f"   - PermissionLevel.USER: {PermissionLevel.USER}")
        print(f"   - PermissionLevel.ADMIN: {PermissionLevel.ADMIN}")
        print(f"   - PermissionLevel.SUPER: {PermissionLevel.SUPER}")

        checker = PermissionChecker(PermissionLevel.ADMIN)
        print(f"   - PermissionChecker.level: {checker.level}")

        print(f"   - ADMIN_PERMISSION: {type(ADMIN_PERMISSION).__name__}")
        print(f"   - USER_PERMISSION: {type(USER_PERMISSION).__name__}")
        print(f"   - SUPER_PERMISSION: {type(SUPER_PERMISSION).__name__}")

        rule_fn = make_permission_rule("admin")
        assert callable(rule_fn), "make_permission_rule 应返回可调用对象"
        print("   - make_permission_rule: ✅ 返回可调用对象")

        combined_or = USER_PERMISSION | ADMIN_PERMISSION
        combined_and = USER_PERMISSION & ADMIN_PERMISSION
        print(f"   - OR 组合: {type(combined_or).__name__}")
        print(f"   - AND 组合: {type(combined_and).__name__}")

        return True
    except Exception as e:
        print(f"❌ 权限系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_room_commands():
    """测试房间管理命令"""
    print("\n" + "=" * 60)
    print("🏠 测试房间管理命令")
    print("=" * 60)

    try:
        setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.room")
        importlib.reload(mod)

        print("✅ 房间命令模块加载成功")
        print(f"   - room_list_command: {mod.room_list_command.path}")
        print(f"   - room_info_command: {mod.room_info_command.path}")
        print(f"   - room_start_command: {mod.room_start_command.path}")
        print(f"   - room_stop_command: {mod.room_stop_command.path}")
        print(f"   - room_restart_command: {mod.room_restart_command.path}")

        print(f"   - room_list_command 描述: {mod.room_list_command.meta.description}")
        assert mod.room_list_command.meta.description == "查看房间列表"
        assert mod.room_start_command.meta.description == "启动房间"

        for name in [
            "handle_room_list", "handle_room_info",
            "handle_room_start", "handle_room_stop", "handle_room_restart",
        ]:
            assert callable(getattr(mod, name)), f"{name} 应为可调用对象"
        print("   - 所有 handler 函数已验证 ✅")

        mock_client = MagicMock()
        mod.init(mock_client)
        print("   - init() 初始化 API 客户端成功 ✅")

        return True
    except Exception as e:
        print(f"❌ 房间命令测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_console_commands():
    """测试控制台命令"""
    print("\n" + "=" * 60)
    print("💻 测试控制台命令")
    print("=" * 60)

    try:
        setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.console")
        importlib.reload(mod)

        print("✅ 控制台命令模块加载成功")
        print(f"   - console_command: {mod.console_command.path}")
        print(f"   - announce_command: {mod.announce_command.path}")
        print(f"   - console_command 描述: {mod.console_command.meta.description}")

        assert mod.console_command.meta.description == "执行控制台命令"
        assert mod.announce_command.meta.description == "发送全服公告"

        assert callable(mod.handle_console), "handle_console 应为可调用对象"
        assert callable(mod.handle_announce), "handle_announce 应为可调用对象"
        print("   - 所有 handler 函数已验证 ✅")

        mock_client = MagicMock()
        mod.init(mock_client)
        print("   - init() 初始化 API 客户端成功 ✅")

        return True
    except Exception as e:
        print(f"❌ 控制台命令测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_player_commands():
    """测试玩家管理命令"""
    print("\n" + "=" * 60)
    print("👥 测试玩家管理命令")
    print("=" * 60)

    try:
        setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.player")
        importlib.reload(mod)

        print("✅ 玩家命令模块加载成功")
        print(f"   - players_command: {mod.players_command.path}")
        print(f"   - kick_command: {mod.kick_command.path}")
        print(f"   - players_command 描述: {mod.players_command.meta.description}")

        assert mod.players_command.meta.description == "查看在线玩家"
        assert mod.kick_command.meta.description == "踢出玩家"

        assert callable(mod.handle_players), "handle_players 应为可调用对象"
        assert callable(mod.handle_kick), "handle_kick 应为可调用对象"
        print("   - 所有 handler 函数已验证 ✅")

        mock_client = MagicMock()
        mod.init(mock_client)
        print("   - init() 初始化 API 客户端成功 ✅")

        return True
    except Exception as e:
        print(f"❌ 玩家命令测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        Alconna 迁移测试 - 第一阶段                       ║
║                                                          ║
║  测试内容：                                              ║
║  - Alconna 库导入                                        ║
║  - 权限系统                                              ║
║  - 房间管理命令 (list, info, start, stop, restart)       ║
║  - 控制台命令 (console, announce)                        ║
║  - 玩家管理命令 (players, kick)                          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    results = []

    results.append(("Alconna 库导入", test_alconna_import()))
    results.append(("权限系统", test_permission_system()))
    results.append(("房间管理命令", test_room_commands()))
    results.append(("控制台命令", test_console_commands()))
    results.append(("玩家管理命令", test_player_commands()))

    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")

    print(f"\n总计: {passed}/{total} 项测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！第一阶段 Alconna 迁移成功完成！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 项测试失败，请检查相关模块")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
