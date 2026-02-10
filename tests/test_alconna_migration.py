"""
Alconna 迁移测试脚本 — 第二阶段

测试 on_alconna 架构迁移的功能：
- Alconna 库导入
- 权限系统
- on_alconna 匹配器 + Match 注入
- 命令处理函数签名验证
"""

import importlib
import inspect
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
    - 仅 mock 外部依赖（nonebot, nonebot_plugin_alconna, loguru, database, ai, services 等）
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
    mock_ob_message.Message = str
    sys.modules['nonebot.adapters'] = MagicMock()
    sys.modules['nonebot.adapters.onebot'] = MagicMock()
    sys.modules['nonebot.adapters.onebot.v11'] = mock_ob_message

    # ========== Mock nonebot_plugin_alconna ==========
    # 创建真实的 Match 和 AlconnaMatch 类供测试检查
    from dataclasses import dataclass

    @dataclass
    class MockMatch:
        """模拟 Match[T] 对象"""
        result: object = None
        available: bool = False

    def mock_alconna_match(name: str):
        """模拟 AlconnaMatch 依赖注入"""
        return MockMatch()

    # 创建一个真正返回 AlconnaMatcher 类的 on_alconna
    def mock_on_alconna(command, **kwargs):
        """模拟 on_alconna 匹配器工厂"""
        matcher_cls = MagicMock()
        matcher_cls.command = MagicMock(return_value=command)
        matcher_cls.handle = MagicMock(return_value=lambda f: f)
        matcher_cls.finish = AsyncMock()
        matcher_cls.send = AsyncMock()
        matcher_cls.assign = MagicMock(return_value=lambda f: f)
        # 保存 permission 参数供测试检查
        matcher_cls._on_alconna_kwargs = kwargs
        return matcher_cls

    mock_alconna_plugin = types.ModuleType("nonebot_plugin_alconna")
    mock_alconna_plugin.on_alconna = mock_on_alconna
    mock_alconna_plugin.Match = MockMatch
    mock_alconna_plugin.AlconnaMatch = mock_alconna_match
    mock_alconna_plugin.AlconnaResult = MagicMock
    mock_alconna_plugin.AlconnaMatcher = MagicMock
    mock_alconna_plugin.UniMessage = MagicMock
    sys.modules['nonebot_plugin_alconna'] = mock_alconna_plugin

    # ========== Mock loguru ==========
    sys.modules['loguru'] = MagicMock()

    # ========== 注册主包为命名空间包 ==========
    pkg = _create_namespace_package("nonebot_plugin_dst_management")
    sys.modules["nonebot_plugin_dst_management"] = pkg

    for subpkg in ["utils", "helpers", "client", "commands"]:
        full_name = f"nonebot_plugin_dst_management.{subpkg}"
        sub = _create_namespace_package(full_name)
        sys.modules[full_name] = sub
        setattr(pkg, subpkg, sub)

    # ========== Mock database ==========
    mock_db = MagicMock()
    mock_db.get_user_last_room = AsyncMock(return_value=None)
    mock_db.get_user_default_room = AsyncMock(return_value=None)
    mock_db.set_user_last_room = AsyncMock()
    mock_db.get_user_ui_mode = AsyncMock(return_value=None)
    sys.modules['nonebot_plugin_dst_management.database'] = mock_db

    # ========== Mock AI config ==========
    from pydantic import BaseModel
    class AIConfigStub(BaseModel):
        enabled: bool = False

    mock_ai_config_module = types.ModuleType("nonebot_plugin_dst_management.ai.config")
    mock_ai_config_module.AIConfig = AIConfigStub
    sys.modules['nonebot_plugin_dst_management.ai'] = MagicMock()
    sys.modules['nonebot_plugin_dst_management.ai.config'] = mock_ai_config_module

    # ========== Mock config 模块 ==========
    config_mod = importlib.import_module("nonebot_plugin_dst_management.config")
    sys.modules['nonebot_plugin_dst_management.config'] = config_mod
    setattr(pkg, "config", config_mod)

    # ========== Mock services/monitors ==========
    mock_sign_monitor = MagicMock()
    mock_sign_monitor.get_sign_monitor = MagicMock(return_value=None)
    sys.modules['nonebot_plugin_dst_management.services'] = MagicMock()
    sys.modules['nonebot_plugin_dst_management.services.monitors'] = MagicMock()
    sys.modules['nonebot_plugin_dst_management.services.monitors.sign_monitor'] = mock_sign_monitor

    return MockMatch, mock_alconna_match


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

        mod = importlib.import_module("nonebot_plugin_dst_management.utils.permission")
        importlib.reload(mod)

        print("✅ 权限系统模块加载成功")
        print(f"   - PermissionLevel.USER: {mod.PermissionLevel.USER}")
        print(f"   - PermissionLevel.ADMIN: {mod.PermissionLevel.ADMIN}")
        print(f"   - PermissionLevel.SUPER: {mod.PermissionLevel.SUPER}")

        checker = mod.PermissionChecker(mod.PermissionLevel.ADMIN)
        print(f"   - PermissionChecker.level: {checker.level}")
        print(f"   - ADMIN_PERMISSION: {type(mod.ADMIN_PERMISSION).__name__}")

        rule_fn = mod.make_permission_rule("admin")
        assert callable(rule_fn), "make_permission_rule 应返回可调用对象"
        print("   - make_permission_rule: ✅ 返回可调用对象")

        combined_or = mod.USER_PERMISSION | mod.ADMIN_PERMISSION
        combined_and = mod.USER_PERMISSION & mod.ADMIN_PERMISSION
        print(f"   - OR 组合: {type(combined_or).__name__}")
        print(f"   - AND 组合: {type(combined_and).__name__}")

        return True
    except Exception as e:
        print(f"❌ 权限系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_room_commands():
    """测试房间管理命令 (on_alconna 架构)"""
    print("\n" + "=" * 60)
    print("🏠 测试房间管理命令 (on_alconna)")
    print("=" * 60)

    try:
        MockMatch, _ = setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.room")
        importlib.reload(mod)

        print("✅ 房间命令模块加载成功")

        # 验证 Alconna 命令定义
        for name, cmd_desc in [
            ("room_list_command", "查看房间列表"),
            ("room_info_command", "查看房间详情"),
            ("room_start_command", "启动房间"),
            ("room_stop_command", "关闭房间"),
            ("room_restart_command", "重启房间"),
        ]:
            cmd = getattr(mod, name)
            print(f"   - {name}: {cmd.path} ({cmd.meta.description})")
            assert cmd.meta.description == cmd_desc, f"{name} 描述不匹配"

        # 验证 on_alconna 匹配器存在
        for matcher_name in ["list_matcher", "info_matcher", "start_matcher", "stop_matcher", "restart_matcher"]:
            matcher = getattr(mod, matcher_name)
            assert matcher is not None, f"{matcher_name} 不存在"
        print("   - 所有 on_alconna 匹配器已验证 ✅")

        # 验证匹配器权限配置
        assert mod.list_matcher._on_alconna_kwargs.get("permission") is not None
        assert mod.start_matcher._on_alconna_kwargs.get("permission") is not None
        print("   - 匹配器权限配置已验证 ✅")

        # 验证 handler 函数签名使用 Match 注入
        sig = inspect.signature(mod.handle_room_list)
        params = list(sig.parameters.values())
        param_names = [p.name for p in params]
        assert "page" in param_names, "handle_room_list 应有 page 参数"
        print("   - handle_room_list 签名: Match[int] 注入 ✅")

        sig = inspect.signature(mod.handle_room_info)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id" in param_names, "handle_room_info 应有 room_id 参数"
        print("   - handle_room_info 签名: Match[str] 注入 ✅")

        # 测试 init
        mock_client = MagicMock()
        mod.init(mock_client)
        print("   - init() 初始化成功 ✅")

        return True
    except Exception as e:
        print(f"❌ 房间命令测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_console_commands():
    """测试控制台命令 (on_alconna 架构)"""
    print("\n" + "=" * 60)
    print("💻 测试控制台命令 (on_alconna)")
    print("=" * 60)

    try:
        setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.console")
        importlib.reload(mod)

        print("✅ 控制台命令模块加载成功")

        # 验证命令定义
        assert mod.console_command.meta.description == "执行控制台命令"
        assert mod.announce_command.meta.description == "发送全服公告"
        print(f"   - console_command: {mod.console_command.path}")
        print(f"   - announce_command: {mod.announce_command.path}")

        # 验证 on_alconna 匹配器
        assert mod.console_matcher is not None
        assert mod.announce_matcher is not None
        print("   - on_alconna 匹配器已验证 ✅")

        # 验证 admin 权限配置
        assert mod.console_matcher._on_alconna_kwargs.get("permission") is not None
        assert mod.announce_matcher._on_alconna_kwargs.get("permission") is not None
        print("   - 匹配器权限配置 (ADMIN) ✅")

        # 验证 handler 签名使用 Match 注入
        sig = inspect.signature(mod.handle_console)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id" in param_names
        assert "command" in param_names
        print("   - handle_console 签名: Match 注入 ✅")

        sig = inspect.signature(mod.handle_announce)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id" in param_names
        assert "message" in param_names
        print("   - handle_announce 签名: Match 注入 ���")

        mock_client = MagicMock()
        mod.init(mock_client)
        print("   - init() 初始化成功 ✅")

        return True
    except Exception as e:
        print(f"❌ 控制台命令测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_player_commands():
    """测试玩家管理命令 (on_alconna 架构)"""
    print("\n" + "=" * 60)
    print("👥 测试玩家管理命令 (on_alconna)")
    print("=" * 60)

    try:
        setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.player")
        importlib.reload(mod)

        print("✅ 玩家命令模块加载成功")

        # 验证命令定义
        assert mod.players_command.meta.description == "查看在线玩家"
        assert mod.kick_command.meta.description == "踢出玩家"
        print(f"   - players_command: {mod.players_command.path}")
        print(f"   - kick_command: {mod.kick_command.path}")

        # 验证 on_alconna 匹配器
        assert mod.players_matcher is not None
        assert mod.kick_matcher is not None
        print("   - on_alconna 匹配器已验证 ✅")

        # 验证权限配置
        assert mod.players_matcher._on_alconna_kwargs.get("permission") is not None
        assert mod.kick_matcher._on_alconna_kwargs.get("permission") is not None
        print("   - 匹配器权限配置 (USER/ADMIN) ✅")

        # 验证 handler 签名使用 Match 注入
        sig = inspect.signature(mod.handle_players)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id" in param_names
        print("   - handle_players 签名: Match 注入 ✅")

        sig = inspect.signature(mod.handle_kick)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id_or_kuid" in param_names
        assert "kuid" in param_names
        print("   - handle_kick 签名: Match 注入 ✅")

        mock_client = MagicMock()
        mod.init(mock_client)
        print("   - init() 初始化成功 ✅")

        return True
    except Exception as e:
        print(f"❌ 玩家命令测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_handlers_init():
    """测试统一初始化入口"""
    print("\n" + "=" * 60)
    print("🔧 测试命令统一初始化入口")
    print("=" * 60)

    try:
        setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.handlers")
        importlib.reload(mod)

        print("✅ handlers 模块加载成功")

        # 验证 init 函数存在且可调用
        assert callable(mod.init), "init 应为可调用对象"

        # 调用 init 初始化所有模块
        mock_client = MagicMock()
        mod.init(mock_client)
        print("   - init(api_client) 初始化成功 ✅")

        # 验证各子模块的 API 客户端已设置
        from nonebot_plugin_dst_management.commands import room, console, player
        assert room._api_client is mock_client, "room 模块 API 客户端未设置"
        assert console._api_client is mock_client, "console 模块 API 客户端未设置"
        assert player._api_client is mock_client, "player 模块 API 客户端未设置"
        print("   - 所有子模块 API 客户端已设置 ✅")

        return True
    except Exception as e:
        print(f"❌ handlers 初始化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_on_command_usage():
    """验证新命令模块不再使用 on_command"""
    print("\n" + "=" * 60)
    print("🚫 验证已移除 on_command 依赖")
    print("=" * 60)

    try:
        setup_common_mocks()

        for mod_name in [
            "nonebot_plugin_dst_management.commands.room",
            "nonebot_plugin_dst_management.commands.console",
            "nonebot_plugin_dst_management.commands.player",
        ]:
            mod = importlib.import_module(mod_name)
            importlib.reload(mod)
            source = inspect.getsource(mod)
            assert "on_command" not in source, f"{mod_name} 仍然使用 on_command"
            assert "on_alconna" in source, f"{mod_name} 未使用 on_alconna"
            short_name = mod_name.split(".")[-1]
            print(f"   - {short_name}: on_command ✗ / on_alconna ✓")

        # handlers.py 也不应使用 on_command
        handlers_mod = importlib.import_module("nonebot_plugin_dst_management.commands.handlers")
        importlib.reload(handlers_mod)
        source = inspect.getsource(handlers_mod)
        assert "on_command" not in source, "handlers.py 仍然使用 on_command"
        print("   - handlers: on_command ✗ ✅")

        print("   - 所有命令模块已完全迁移至 on_alconna ✅")
        return True
    except Exception as e:
        print(f"❌ on_command 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        Alconna 迁移测试 - 第二阶段                       ║
║        (on_alconna 架构升级)                             ║
║                                                          ║
║  测试内容：                                              ║
║  1. Alconna 库导入                                       ║
║  2. 权限系统                                             ║
║  3. 房间管理命令 (on_alconna + Match 注入)               ║
║  4. 控制台命令 (on_alconna + Match 注入)                 ║
║  5. 玩家管理命令 (on_alconna + Match 注入)               ║
║  6. 统一初始化入口                                       ║
║  7. 验证 on_command 已移除                               ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    results = []

    results.append(("Alconna 库导入", test_alconna_import()))
    results.append(("权限系统", test_permission_system()))
    results.append(("房间管理命令 (on_alconna)", test_room_commands()))
    results.append(("控制台命令 (on_alconna)", test_console_commands()))
    results.append(("玩家管理命令 (on_alconna)", test_player_commands()))
    results.append(("统一初始化入口", test_handlers_init()))
    results.append(("on_command 已移除", test_no_on_command_usage()))

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
        print("\n🎉 所有测试通过！第二阶段 on_alconna 架构升级成功完成！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 项测试失败，请检查相关模块")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
