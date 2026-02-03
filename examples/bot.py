"""NoneBot2 示例 Bot - 集成 DST 管理插件"""
import nonebot
from nonebot.adapters.onebot.v11 import Adapter

# 初始化 NoneBot
nonebot.init()

# 获取 Driver
driver = get_driver()

# 配置
driver.config.host = "127.0.0.1"
driver.config.port = 8080

# 注册适配器
driver.register_adapter(Adapter)

# 加载 DST 管理插件
nonebot.load_plugin("nonebot_plugin_dst_management")

# 如果你想加载其他插件
# nonebot.load_plugin("nonebot_plugin_localstore")
# nonebot.load_plugin("nonebot_plugin_apscheduler")

if __name__ == "__main__":
    nonebot.run()
