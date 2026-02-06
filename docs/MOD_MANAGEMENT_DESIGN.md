# DST 模组管理命令

## 模组管理功能设计

### 1. 搜索模组
`cmd: /dst mod search <关键词>`
- 调用 `search_mod(type='text', keyword=keyword)`
- 显示前 5-10 个结果
- 显示模组 ID、名称、作者、订阅数

### 2. 查看已安装模组
`cmd: /dst mod list <room_id>`
- 调用 `get_room_info(room_id)`
- 解析 `modData` 字段
- 显示已启用和已禁用的模组

### 3. 添加模组
`cmd: /dst mod add <room_id> <world_id> <mod_id>`
- 检查模组是否存在
- 调用 `download_mod()` 下载模组
- 调用 `get_mod_setting_struct()` 获取配置
- 调用 `update_mod_setting()` 应用默认配置
- 调用 `enable_mod()` 启用模组

### 4. 移除模组
`cmd: /dst mod remove <room_id> <world_id> <mod_id>`
- 修改房间配置，移除模组引用
- 调用 `update_room()`

### 5. 模组配置
`cmd: /dst mod config <room_id> <world_id> <mod_id>`
- 显示当前配置
- 提供修改指引

---

## 代码实现计划

### handlers/mod.py

```python
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg
from ..client.api_client import DSTApiClient

# 搜索模组
mod_search = on_command("dst mod search")

@mod_search.handle()
async def handle_mod_search(event: MessageEvent, args: Message = CommandArg()):
    keyword = args.extract_plain_text().strip()
    if not keyword:
        await mod_search.finish("❌ 请提供搜索关键词")
        
    result = await api_client.search_mod("text", keyword)
    # ... 处理结果
```
