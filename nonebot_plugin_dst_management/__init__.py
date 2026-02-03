"""
NoneBot2 DST 服务器管理插件

通过 DMP API 管理 Don't Starve Together 服务器。
"""

from nonebot import get_driver
from nonebot.plugin import PluginMetadata

from .config import get_dst_config
from .client.api_client import DSTApiClient

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="DST服务器管理",
    description="通过DMP API管理Don't Starve Together服务器，支持房间管理、玩家管理、备份管理等功能。",
    usage="""
房间管理：
    /dst list [页码]         - 查看房间列表
    /dst info <房间ID>        - 查看房间详情
    /dst start <房间ID>       - 启动房间 🔒
    /dst stop <房间ID>        - 关闭房间 🔒
    /dst restart <房间ID>     - 重启房间 🔒

玩家管理：
    /dst players <房间ID>     - 查看在线玩家
    /dst kick <房间ID> <KU_ID> - 踢出玩家 🔒

备份管理：
    /dst backup list <房间ID>       - 查看备份列表
    /dst backup create <房间ID>     - 创建备份 🔒

🔒 标记的命令需要管理员权限

更多命令和详细用法请查看：https://github.com/your-repo/nonebot-dst-management
    """,
    type="application",
    homepage="https://github.com/your-repo/nonebot-dst-management",
    config=None,
    supported_adapters={"~onebot.v11"},
)

# 获取驱动实例
driver = get_driver()

# 全局 API 客户端实例
api_client: DSTApiClient = None


@driver.on_startup
async def init_api_client():
    """
    插件启动时初始化 API 客户端
    """
    global api_client
    
    config = get_dst_config()
    
    # 初始化 API 客户端
    api_client = DSTApiClient(
        base_url=config.dst_api_url,
        token=config.dst_api_token,
        timeout=config.dst_timeout
    )
    
    # 测试连接
    try:
        result = await api_client.get_platform_overview()
        if result["success"]:
            driver.logger.info("DST 管理插件已连接到 DMP API")
        else:
            driver.logger.warning(f"DMP API 连接失败：{result.get('error')}")
    except Exception as e:
        driver.logger.error(f"DMP API 初始化失败：{e}")


@driver.on_shutdown
async def close_api_client():
    """
    插件关闭时清理资源
    """
    global api_client
    
    if api_client:
        await api_client.close()
        driver.logger.info("DST 管理插件已关闭 API 客户端")


# 加载命令处理器
from .handlers import room, player, backup

# 初始化所有命令处理器
def init_handlers():
    """
    初始化所有命令处理器
    """
    if api_client is None:
        driver.logger.error("API 客户端未初始化，无法加载命令处理器")
        return
    
    room.init(api_client)
    player.init(api_client)
    backup.init(api_client)
    
    driver.logger.info("DST 管理插件命令处理器已加载")


# 注册初始化钩子
driver.on_startup(init_handlers)

# 导出
__all__ = [
    "__plugin_meta__",
    "api_client",
    "get_dst_config"
]
