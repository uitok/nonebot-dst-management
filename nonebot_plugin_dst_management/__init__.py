"""
NoneBot2 DST 服务器管理插件

通过 DMP API 管理 Don't Starve Together 服务器。
"""

from nonebot import get_driver
from nonebot.plugin import PluginMetadata

from .config import DSTConfig, Config, get_dst_config
from .client.api_client import DSTApiClient

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

模组管理：
  /dst mod search <关键词>       - 搜索模组
  /dst mod list <房间ID>         - 查看已安装模组
  /dst mod add <房间ID> <世界ID> <模组ID> - 添加模组 🔒
  /dst mod remove <房间ID> <世界ID> <模组ID> - 删除模组 🔒
  /dst mod check <房间ID>       - 检测模组冲突

控制台：
  /dst console <房间ID> [世界ID] <命令> - 执行控制台命令 🔒
  /dst announce <房间ID> <消息> - 发送全服公告 🔒

🔒 标记的命令需要管理员权限

使用 /dst help 查看完整帮助
""",
    type="application",
    homepage="https://github.com/your-repo/nonebot-dst-management",
    config=Config,
    supported_adapters={"nonebot.adapters.onebot.v11"},
)

# 获取驱动
driver = get_driver()

# 全局 API 客户端
_api_client: DSTApiClient = None


@driver.on_startup
async def init_client():
    """初始化 API 客户端"""
    global _api_client
    config = get_dst_config()
    
    _api_client = DSTApiClient(
        base_url=config.dst_api_url,
        token=config.dst_api_token,
        timeout=config.dst_timeout
    )
    
    # 加载命令处理器
    from .handlers import room, player, backup, mod, console, archive
    
    room.init(_api_client)
    player.init(_api_client)
    backup.init(_api_client)
    mod.init(_api_client)
    console.init(_api_client)
    archive.init(_api_client)


@driver.on_shutdown
async def close_client():
    """关闭 API 客户端"""
    global _api_client
    if _api_client:
        await _api_client.close()


def get_api_client() -> DSTApiClient:
    """
    获取 API 客户端实例
    
    Returns:
        DSTApiClient: API 客户端实例
    """
    return _api_client


__all__ = [
    "__plugin_meta__",
    "DSTConfig",
    "Config",
    "get_dst_config",
    "get_api_client",
]
