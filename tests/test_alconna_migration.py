"""
Alconna 迁移测试脚本 — 第三阶段 A

测试 on_alconna 架构迁移的功能：
- Alconna 库导入
- 权限系统
- on_alconna 匹配器 + Match 注入
- 命令处理函数签名验证
- 第三阶段 A 新增模块：help, config_ui, ai_analyze, ai_recommend, ai_mod_parse, backup
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
    mock_nonebot.get_bot = MagicMock(return_value=MagicMock())

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
    from dataclasses import dataclass

    @dataclass
    class MockMatch:
        """模拟 Match[T] 对象"""
        result: object = None
        available: bool = False

    def mock_alconna_match(name: str):
        """模拟 AlconnaMatch 依赖注入"""
        return MockMatch()

    def mock_on_alconna(command, **kwargs):
        """模拟 on_alconna 匹配器工厂"""
        matcher_cls = MagicMock()
        matcher_cls.command = MagicMock(return_value=command)
        matcher_cls.handle = MagicMock(return_value=lambda f: f)
        matcher_cls.finish = AsyncMock()
        matcher_cls.send = AsyncMock()
        matcher_cls.assign = MagicMock(return_value=lambda f: f)
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
    mock_db.set_user_ui_mode = AsyncMock()
    mock_db.init_db = AsyncMock()
    sys.modules['nonebot_plugin_dst_management.database'] = mock_db

    # ========== Mock AI ==========
    from pydantic import BaseModel
    class AIConfigStub(BaseModel):
        enabled: bool = False

    mock_ai_config_module = types.ModuleType("nonebot_plugin_dst_management.ai.config")
    mock_ai_config_module.AIConfig = AIConfigStub

    mock_ai = MagicMock()
    sys.modules['nonebot_plugin_dst_management.ai'] = mock_ai
    sys.modules['nonebot_plugin_dst_management.ai.config'] = mock_ai_config_module

    # Mock AI submodules used by new command files
    mock_ai_client_module = MagicMock()
    mock_ai_client_module.AIClient = MagicMock
    sys.modules['nonebot_plugin_dst_management.ai.client'] = mock_ai_client_module

    sys.modules['nonebot_plugin_dst_management.ai.analyzer'] = MagicMock()
    sys.modules['nonebot_plugin_dst_management.ai.recommender'] = MagicMock()
    sys.modules['nonebot_plugin_dst_management.ai.mod_parser'] = MagicMock()
    sys.modules['nonebot_plugin_dst_management.ai.base'] = MagicMock()

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

        for matcher_name in ["list_matcher", "info_matcher", "start_matcher", "stop_matcher", "restart_matcher"]:
            matcher = getattr(mod, matcher_name)
            assert matcher is not None, f"{matcher_name} 不存在"
        print("   - 所有 on_alconna 匹配器已验证 ✅")

        assert mod.list_matcher._on_alconna_kwargs.get("permission") is not None
        assert mod.start_matcher._on_alconna_kwargs.get("permission") is not None
        print("   - 匹配器权限配置已验证 ✅")

        sig = inspect.signature(mod.handle_room_list)
        param_names = [p.name for p in sig.parameters.values()]
        assert "page" in param_names, "handle_room_list 应有 page 参数"
        print("   - handle_room_list 签名: Match[int] 注入 ✅")

        sig = inspect.signature(mod.handle_room_info)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id" in param_names, "handle_room_info 应有 room_id 参数"
        print("   - handle_room_info 签名: Match[str] 注入 ✅")

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

        assert mod.console_command.meta.description == "执行控制台命令"
        assert mod.announce_command.meta.description == "发送全服公告"
        print(f"   - console_command: {mod.console_command.path}")
        print(f"   - announce_command: {mod.announce_command.path}")

        assert mod.console_matcher is not None
        assert mod.announce_matcher is not None
        print("   - on_alconna 匹配器已验证 ✅")

        assert mod.console_matcher._on_alconna_kwargs.get("permission") is not None
        assert mod.announce_matcher._on_alconna_kwargs.get("permission") is not None
        print("   - 匹配器权限配置 (ADMIN) ✅")

        sig = inspect.signature(mod.handle_console)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id" in param_names
        assert "command" in param_names
        print("   - handle_console 签名: Match 注入 ✅")

        sig = inspect.signature(mod.handle_announce)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id" in param_names
        assert "message" in param_names
        print("   - handle_announce 签名: Match 注入 ✅")

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

        assert mod.players_command.meta.description == "查看在线玩家"
        assert mod.kick_command.meta.description == "踢出玩家"
        print(f"   - players_command: {mod.players_command.path}")
        print(f"   - kick_command: {mod.kick_command.path}")

        assert mod.players_matcher is not None
        assert mod.kick_matcher is not None
        print("   - on_alconna 匹配器已验证 ✅")

        assert mod.players_matcher._on_alconna_kwargs.get("permission") is not None
        assert mod.kick_matcher._on_alconna_kwargs.get("permission") is not None
        print("   - 匹配器权限配置 (USER/ADMIN) ✅")

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


def test_help_command():
    """测试帮助命令 (on_alconna 架构)"""
    print("\n" + "=" * 60)
    print("📖 测试帮助命令 (on_alconna)")
    print("=" * 60)

    try:
        setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.help")
        importlib.reload(mod)

        print("✅ 帮助命令模块加载成功")

        assert mod.help_command.meta.description == "查看帮助"
        print(f"   - help_command: {mod.help_command.path} ({mod.help_command.meta.description})")

        assert mod.help_matcher is not None
        print("   - on_alconna 匹配器已验证 ✅")

        assert mod.help_matcher._on_alconna_kwargs.get("permission") is not None
        print("   - 匹配器权限配置 (USER) ✅")

        sig = inspect.signature(mod.handle_help)
        param_names = [p.name for p in sig.parameters.values()]
        assert "category" in param_names, "handle_help 应有 category 参数"
        print("   - handle_help 签名: Match[str] 注入 ✅")

        mod.init()
        print("   - init() 初始化成功 ✅")

        return True
    except Exception as e:
        print(f"❌ 帮助命令测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_ui_command():
    """测试 UI 配置命令 (on_alconna 架构)"""
    print("\n" + "=" * 60)
    print("⚙️ 测试 UI 配置命令 (on_alconna)")
    print("=" * 60)

    try:
        setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.config_ui")
        importlib.reload(mod)

        print("✅ UI 配置命令模块加载成功")

        assert mod.config_ui_command.meta.description == "设置UI展示模式"
        print(f"   - config_ui_command: {mod.config_ui_command.path} ({mod.config_ui_command.meta.description})")

        assert mod.config_ui_matcher is not None
        print("   - on_alconna 匹配器已验证 ✅")

        assert mod.config_ui_matcher._on_alconna_kwargs.get("permission") is not None
        print("   - 匹配器权限配置 (USER) ✅")

        sig = inspect.signature(mod.handle_config_ui)
        param_names = [p.name for p in sig.parameters.values()]
        assert "mode" in param_names, "handle_config_ui 应有 mode 参数"
        print("   - handle_config_ui 签名: Match[str] 注入 ✅")

        mod.init()
        print("   - init() 初始化成功 ✅")

        return True
    except Exception as e:
        print(f"❌ UI 配置命令测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_analyze_command():
    """测试 AI 配置分析命令 (on_alconna 架构)"""
    print("\n" + "=" * 60)
    print("🤖 测试 AI 配置分析命令 (on_alconna)")
    print("=" * 60)

    try:
        setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.ai_analyze")
        importlib.reload(mod)

        print("✅ AI 分析命令模块加载成功")

        assert mod.analyze_command.meta.description == "AI配置分析"
        print(f"   - analyze_command: {mod.analyze_command.path} ({mod.analyze_command.meta.description})")

        assert mod.analyze_matcher is not None
        print("   - on_alconna 匹配器已验证 ✅")

        assert mod.analyze_matcher._on_alconna_kwargs.get("permission") is not None
        print("   - 匹配器权限配置 (USER) ✅")

        sig = inspect.signature(mod.handle_analyze)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id" in param_names, "handle_analyze 应有 room_id 参数"
        print("   - handle_analyze 签名: Match[str] 注入 ✅")

        mock_api = MagicMock()
        mock_ai = MagicMock()
        mod.init(mock_api, mock_ai)
        assert mod._api_client is mock_api
        assert mod._ai_client is mock_ai
        print("   - init(api_client, ai_client) 初始化成功 ✅")

        return True
    except Exception as e:
        print(f"❌ AI 分析命令测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_recommend_command():
    """测试 AI 模组推荐命令 (on_alconna 架构)"""
    print("\n" + "=" * 60)
    print("🧩 测试 AI 模组推荐命令 (on_alconna)")
    print("=" * 60)

    try:
        setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.ai_recommend")
        importlib.reload(mod)

        print("✅ AI 推荐命令模块加载成功")

        assert mod.recommend_command.meta.description == "AI模组推荐"
        print(f"   - recommend_command: {mod.recommend_command.path} ({mod.recommend_command.meta.description})")

        assert mod.recommend_matcher is not None
        print("   - on_alconna 匹配器已验证 ✅")

        sig = inspect.signature(mod.handle_recommend)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id" in param_names
        assert "mod_type" in param_names
        print("   - handle_recommend 签名: Match[str] 注入 ✅")

        mock_api = MagicMock()
        mock_ai = MagicMock()
        mod.init(mock_api, mock_ai)
        assert mod._api_client is mock_api
        assert mod._ai_client is mock_ai
        print("   - init(api_client, ai_client) 初始化成功 ✅")

        return True
    except Exception as e:
        print(f"❌ AI 推荐命令测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_mod_parse_command():
    """测试 AI 模组配置解析命令 (on_alconna 架构)"""
    print("\n" + "=" * 60)
    print("🔍 测试 AI 模组配置解析命令 (on_alconna)")
    print("=" * 60)

    try:
        setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.ai_mod_parse")
        importlib.reload(mod)

        print("✅ AI 解析命令模块加载成功")

        assert mod.mod_parse_command.meta.description == "AI模组配置解析"
        print(f"   - mod_parse_command: {mod.mod_parse_command.path} ({mod.mod_parse_command.meta.description})")

        assert mod.mod_parse_matcher is not None
        print("   - on_alconna 匹配器已验证 ✅")

        sig = inspect.signature(mod.handle_mod_parse)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id" in param_names
        assert "world_id" in param_names
        print("   - handle_mod_parse 签名: Match[str] 注入 ✅")

        mock_api = MagicMock()
        mock_ai = MagicMock()
        mod.init(mock_api, mock_ai)
        assert mod._api_client is mock_api
        assert mod._ai_client is mock_ai
        print("   - init(api_client, ai_client) 初始化成功 ✅")

        return True
    except Exception as e:
        print(f"❌ AI 解析命令测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backup_commands():
    """测试备份管理命令 (on_alconna 架构)"""
    print("\n" + "=" * 60)
    print("💾 测试备份管理命令 (on_alconna)")
    print("=" * 60)

    try:
        setup_common_mocks()

        mod = importlib.import_module("nonebot_plugin_dst_management.commands.backup")
        importlib.reload(mod)

        print("✅ 备份命令模块加载成功")

        for name, cmd_desc in [
            ("backup_list_command", "查看备份列表"),
            ("backup_create_command", "创建备份"),
            ("backup_restore_command", "恢复备份"),
        ]:
            cmd = getattr(mod, name)
            print(f"   - {name}: {cmd.path} ({cmd.meta.description})")
            assert cmd.meta.description == cmd_desc, f"{name} 描述不匹配"

        for matcher_name in ["backup_list_matcher", "backup_create_matcher", "backup_restore_matcher"]:
            matcher = getattr(mod, matcher_name)
            assert matcher is not None, f"{matcher_name} 不存在"
        print("   - 所有 on_alconna 匹配器已验证 ✅")

        # 验证权限配置
        assert mod.backup_list_matcher._on_alconna_kwargs.get("permission") is not None
        assert mod.backup_create_matcher._on_alconna_kwargs.get("permission") is not None
        assert mod.backup_restore_matcher._on_alconna_kwargs.get("permission") is not None
        print("   - 匹配器权限配置 (USER/ADMIN) ✅")

        # 验证 handler 签名
        sig = inspect.signature(mod.handle_backup_list)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id" in param_names
        print("   - handle_backup_list 签名: Match[str] 注入 ✅")

        sig = inspect.signature(mod.handle_backup_create)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id" in param_names
        print("   - handle_backup_create 签名: Match[str] 注入 ✅")

        sig = inspect.signature(mod.handle_backup_restore)
        param_names = [p.name for p in sig.parameters.values()]
        assert "room_id_or_file" in param_names
        assert "filename" in param_names
        print("   - handle_backup_restore 签名: Match[str] 注入 ✅")

        mock_client = MagicMock()
        mod.init(mock_client)
        assert mod._api_client is mock_client
        print("   - init(api_client) 初始化成功 ✅")

        return True
    except Exception as e:
        print(f"❌ 备份命令测试失败: {e}")
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

        assert callable(mod.init), "init 应为可调用对象"

        mock_client = MagicMock()
        mock_ai_client = MagicMock()
        mod.init(mock_client, mock_ai_client)
        print("   - init(api_client, ai_client) 初始化成功 ✅")

        # 验证核心子模块的 API 客户端已设置
        from nonebot_plugin_dst_management.commands import room, console, player, backup
        assert room._api_client is mock_client, "room 模块 API 客户端未设置"
        assert console._api_client is mock_client, "console 模块 API 客户端未设置"
        assert player._api_client is mock_client, "player 模块 API 客户端未设置"
        assert backup._api_client is mock_client, "backup 模块 API 客户端未设置"
        print("   - 核心子模块 API 客户端已设置 ✅")

        # 验证 AI 子模块客户端已设置
        from nonebot_plugin_dst_management.commands import ai_analyze, ai_recommend, ai_mod_parse
        assert ai_analyze._api_client is mock_client
        assert ai_analyze._ai_client is mock_ai_client
        assert ai_recommend._api_client is mock_client
        assert ai_recommend._ai_client is mock_ai_client
        assert ai_mod_parse._api_client is mock_client
        assert ai_mod_parse._ai_client is mock_ai_client
        print("   - AI 子模块客户端已设置 ✅")

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

        all_modules = [
            "nonebot_plugin_dst_management.commands.room",
            "nonebot_plugin_dst_management.commands.console",
            "nonebot_plugin_dst_management.commands.player",
            "nonebot_plugin_dst_management.commands.help",
            "nonebot_plugin_dst_management.commands.config_ui",
            "nonebot_plugin_dst_management.commands.ai_analyze",
            "nonebot_plugin_dst_management.commands.ai_recommend",
            "nonebot_plugin_dst_management.commands.ai_mod_parse",
            "nonebot_plugin_dst_management.commands.backup",
        ]

        for mod_name in all_modules:
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


def test_old_handlers_removed():
    """验证已迁移的旧 handler 文件已删除"""
    print("\n" + "=" * 60)
    print("🗑️ 验证已删除旧 handler 文件")
    print("=" * 60)

    try:
        handlers_dir = project_root / "nonebot_plugin_dst_management" / "handlers"
        removed_files = [
            "room.py",
            "console.py",
            "player.py",
            "player_enhanced.py",
            "help.py",
            "config_ui.py",
            "ai_analyze.py",
            "ai_recommend.py",
            "ai_mod_parse.py",
            "backup.py",
        ]

        for fname in removed_files:
            fpath = handlers_dir / fname
            assert not fpath.exists(), f"旧文件未删除: handlers/{fname}"
            print(f"   - handlers/{fname}: 已删除 ✅")

        # 验证仍存在的旧 handler 文件
        remaining_files = [
            "mod.py",
            "archive.py",
            "ai_mod_apply.py",
            "ai_archive.py",
            "ai_qa.py",
            "sign.py",
            "default_room.py",
            "auto_discovery.py",
        ]

        for fname in remaining_files:
            fpath = handlers_dir / fname
            assert fpath.exists(), f"不应删除的文件丢失: handlers/{fname}"
        print(f"   - 保留 {len(remaining_files)} 个待迁移 handler 文件 ✅")

        return True
    except Exception as e:
        print(f"❌ 旧 handler 文件检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        Alconna 迁移测试 - 第三阶段 A                    ║
║        (on_alconna 架构 + 6 模块迁移)                   ║
║                                                          ║
║  测试内容：                                              ║
║  1.  Alconna 库导入                                      ║
║  2.  权限系统                                            ║
║  3.  房间管理命令                                        ║
║  4.  控制台命令                                          ║
║  5.  玩家管理命令                                        ║
║  6.  帮助命令 [NEW]                                      ║
║  7.  UI 配置命令 [NEW]                                   ║
║  8.  AI 配置分析命令 [NEW]                               ║
║  9.  AI 模组推荐命令 [NEW]                               ║
║  10. AI 模组配置解析命令 [NEW]                           ║
║  11. 备份管理命令 [NEW]                                  ║
║  12. 统一初始化入口 (含 AI)                              ║
║  13. 验证 on_command 已移除                              ║
║  14. 验证旧 handler 文件已删除 [NEW]                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    results = []

    results.append(("Alconna 库导入", test_alconna_import()))
    results.append(("权限系统", test_permission_system()))
    results.append(("房间管理命令 (on_alconna)", test_room_commands()))
    results.append(("控制台命令 (on_alconna)", test_console_commands()))
    results.append(("玩家管理命令 (on_alconna)", test_player_commands()))
    results.append(("帮助命令 (on_alconna)", test_help_command()))
    results.append(("UI 配置命令 (on_alconna)", test_config_ui_command()))
    results.append(("AI 配置分析命令", test_ai_analyze_command()))
    results.append(("AI 模组推荐命令", test_ai_recommend_command()))
    results.append(("AI 模组解析命令", test_ai_mod_parse_command()))
    results.append(("备份管理命令 (on_alconna)", test_backup_commands()))
    results.append(("统一初始化入口", test_handlers_init()))
    results.append(("on_command 已移除", test_no_on_command_usage()))
    results.append(("旧 handler 文件已删除", test_old_handlers_removed()))

    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")

    print(f"\n总计: {passed}/{total} 项测试���过")

    if passed == total:
        print("\n🎉 所有测试通过！第三阶段 A 迁移成功完成！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 项测试失败，请检查相关模块")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
