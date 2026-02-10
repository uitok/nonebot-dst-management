"""
NoneBot2 DST 服务器管理插件

通过 DMP API 管理 Don't Starve Together 服务器。
"""

from nonebot import get_driver
from nonebot.plugin import PluginMetadata

from .config import DSTConfig, Config, get_dst_config
from .client.api_client import DSTApiClient
from .ai.client import AIClient


def _register_smart_preprocessor() -> None:
    """Register fuzzy command normalizer (Phase B Smart).

    In unit tests, `nonebot` is commonly mocked and may not be a real package.
    In that case we skip registration silently.
    """

    try:
        from nonebot.message import event_preprocessor  # type: ignore
    except Exception:
        return

    from typing import Any

    from .helpers.fuzzy import normalize_command_text

    @event_preprocessor  # type: ignore[misc]
    async def _dst_smart_preprocessor(event: Any) -> None:
        raw = getattr(event, "raw_message", None)
        if not isinstance(raw, str):
            # Best-effort for adapters without raw_message.
            msg = getattr(event, "message", None)
            if msg is not None and hasattr(msg, "extract_plain_text"):
                try:
                    raw = str(msg.extract_plain_text())
                except Exception:
                    raw = None

        if not isinstance(raw, str) or not raw.strip():
            return

        normalized = normalize_command_text(raw)
        if not normalized or normalized == raw:
            return

        # Update raw_message
        if hasattr(event, "raw_message"):
            try:
                setattr(event, "raw_message", normalized)
            except Exception:
                pass

        # Update message for OneBot v11-style events (and other adapters where Message(text) works).
        msg_obj = getattr(event, "message", None)
        if msg_obj is None:
            return
        try:
            msg_cls = type(msg_obj)
            setattr(event, "message", msg_cls(normalized))
        except Exception:
            # Keep raw_message update only.
            return


_register_smart_preprocessor()

__version__ = "0.3.1"

__plugin_meta__ = PluginMetadata(
    name="DST服务器管理",
    description="通过DMP API管理Don't Starve Together服务器",
    usage="""
房间管理：
  /dst list [页码]           - 查看房间列表
  /dst info <房间ID>          - 查看房间详情
  /dst start <房间ID>         - 启动房间 🔒
  /dst stop <房间ID>          - 关闭房间 🔒
  /dst restart <房间ID>       - 重启房间 🔒

玩家管理：
  /dst players <房间ID>       - 查看在线玩家
  /dst kick <房间ID> <KU_ID>  - 踢出玩家 🔒

备份管理：
  /dst backup list <房间ID>   - 查看备份列表
  /dst backup create <房间ID> - 创建备份 🔒
  /dst backup restore <房间ID> <文件名> - 恢复备份 🔒

存档管理：
  /dst archive upload <房间ID> <文件URL或文件路径> - 上传存档 🔒
  /dst archive download <房间ID> - 下载存档
  /dst archive replace <房间ID> <文件URL或文件路径> - 替换存档 🔒
  /dst archive validate <文件路径> - 验证存档结构

模组管理：
  /dst mod search <关键词>       - 搜索模组
  /dst mod list <房间ID>         - 查看已安装模组
  /dst mod add <房间ID> <世界ID> <模组ID> - 添加模组 🔒
  /dst mod remove <房间ID> <世界ID> <模组ID> - 删除模组 🔒
  /dst mod check <房间ID>       - 检测模组冲突

默认房间：
  /dst 默认房间 <房间ID>        - 设置默认房间
  /dst 查看默认                 - 查看默认房间
  /dst 清除默认                 - 清除默认房间

AI 功能：
  /dst analyze <房间ID>         - AI 配置分析
  /dst mod recommend <房间ID> [类型] - AI 模组推荐
  /dst mod parse <房间ID> <世界ID> - AI 模组配置解析
  /dst mod config show <房间ID> <世界ID> - 查看模组诊断报告
  /dst mod config apply <房间ID> <世界ID> [--auto] [--dry-run] - 应用优化配置 🔒
  /dst mod config save <房间ID> <世界ID> --optimized - 保存优化配置 🔒
  /dst archive analyze <文件>    - AI 存档分析
  /dst ask <问题>                - AI 智能问答

控制台：
  /dst console <房间ID> [世界ID] <命令> - 执行控制台命令 🔒
  /dst announce <房间ID> <消息> - 发送全服公告 🔒

🔒 标记的命令需要管理员权限

提示：设置默认房间后，大部分命令可省略房间ID参数
使用 /dst help 查看完整帮助
""",
    type="application",
    homepage="https://github.com/your-repo/nonebot-dst-management",
    config=Config,
    supported_adapters={"nonebot.adapters.onebot.v11", "nonebot.adapters.qq"},
)

# 获取驱动
driver = get_driver()

# 全局 API 客户端
_api_client: DSTApiClient = None
_ai_client: AIClient = None


@driver.on_startup
async def init_client():
    """初始化 API 客户端"""
    global _api_client
    global _ai_client
    config = get_dst_config()

    # Ensure sqlite tables exist before any command touches the database.
    from .database import init_db

    await init_db()

    _api_client = DSTApiClient(
        base_url=config.dst_api_url,
        token=config.dst_api_token,
        timeout=config.dst_timeout
    )

    _ai_client = AIClient(config.get_ai_config())

    # ========== Alconna 命令 (on_alconna 架构) ==========
    # 已迁移至 commands/ 模块：room, console, player, help, config_ui,
    # backup, ai_analyze, ai_recommend, ai_mod_parse
    from .commands import handlers as alconna_handlers
    alconna_handlers.init(_api_client, _ai_client)

    # ========== 旧版命令处理器 (尚未迁移) ==========
    from .handlers import (
        mod,
        archive,
        ai_mod_apply,
        ai_archive,
        ai_qa,
        default_room,
        sign,
        auto_discovery,
    )

    # 初始化签到监视器（触发式，无后台任务）
    from .services.monitors import sign_monitor

    sign_monitor.init_sign_monitor(_api_client)

    # 旧版命令初始化
    mod.init(_api_client, _ai_client)
    archive.init(_api_client)
    ai_mod_apply.init(_api_client, _ai_client)
    ai_archive.init(_api_client)
    ai_qa.init(_api_client)
    default_room.init(_api_client, _ai_client)
    sign.init(_api_client)
    auto_discovery.init()


@driver.on_shutdown
async def close_client():
    """关闭 API 客户端"""
    global _api_client
    global _ai_client
    if _api_client:
        await _api_client.close()
    if _ai_client:
        await _ai_client.close()


def get_api_client() -> DSTApiClient:
    """
    获取 API 客户端实例

    Returns:
        DSTApiClient: API 客户端实例
    """
    return _api_client


from .services.monitors import sign_monitor  # noqa: F401

__all__ = [
    "__version__",
    "__plugin_meta__",
    "DSTConfig",
    "Config",
    "get_dst_config",
    "get_api_client",
]
