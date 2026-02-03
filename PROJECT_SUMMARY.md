# NoneBot2 DST 管理插件 - 完整开发计划总结

## 📊 项目状态总览

**项目名称**：nonebot-plugin-dst-management
**当前状态**：🎯 规划阶段
**预计完成时间**：7-10 天
**优先级**：🔴 高

---

## 🎯 核心目标

开发一个功能完整的 NoneBot2 插件，用于通过 DMP API 管理 Don't Starve Together 服务器。

### 为什么选择 NoneBot2？

✅ **成熟的生态**：200+ 可复用插件
✅ **多平台支持**：QQ、Telegram、Discord
✅ **异步性能**：原生 async/await
✅ **快速开发**：依赖注入、事件驱动
✅ **易于维护**：模块化架构、完善的文档

---

## 📦 功能模块清单

### ✅ MVP（最小可行产品）- Phase 1

#### 1. 基础架构（优先级：🔴 最高）
- [x] 项目结构搭建
- [x] 配置模型实现
- [x] API 客户端封装
- [x] 权限系统基础
- [x] 消息格式化工具

**预计时间**：1-2 天

#### 2. 房间管理（优先级：🔴 最高）
- [ ] `/dst list [page]` - 查看房间列表
- [ ] `/dst info <room_id>` - 查看房间详情
- [ ] `/dst start <room_id>` - 启动房间 🔒
- [ ] `/dst stop <room_id>` - 关闭房间 🔒
- [ ] `/dst restart <room_id>` - 重启房间 🔒

**预计时间**：1 天

#### 3. 玩家管理（优先级：🟡 中）
- [ ] `/dst players <room_id>` - 查看在线玩家
- [ ] `/dst stats <room_id>` - 查看玩家统计
- [ ] `/dst kick <room_id> <ku_id>` - 踢出玩家 🔒

**预计时间**：0.5 天

#### 4. 备份管理（优先级：🟡 中）
- [ ] `/dst backup list <room_id>` - 查看备份列表
- [ ] `/dst backup create <room_id>` - 创建备份 🔒
- [ ] `/dst backup restore <room_id> <index>` - 恢复备份 🔒

**预计时间**：0.5 天

**Phase 1 总计**：3-4 天

---

### 🚀 增强功能 - Phase 2

#### 5. 模组管理（优先级：🟢 低）
- [ ] `/dst mod search <keyword>` - 搜索模组
- [ ] `/dst mod list <room_id>` - 查看已安装模组
- [ ] `/dst mod add <room_id> <world_id> <mod_id>` - 添加模组 🔒
- [ ] `/dst mod remove <room_id> <world_id> <mod_id>` - 删除模组 🔒
- [ ] `/dst mod enable/disable` - 启用/禁用模组 🔒
- [ ] `/dst mod config` - 修改模组配置 🔒
- [ ] `/dst mod check` - 检测模组冲突

**预计时间**：1.5 天

#### 6. 存档管理（优先级：🟢 低）
- [ ] `/dst archive upload <room_id> <file>` - 上传存档 🔒
- [ ] `/dst archive download <room_id>` - 下载存档
- [ ] `/dst archive replace <room_id> <file>` - 替换存档 🔒
- [ ] `/dst archive validate <file>` - 验证存档格式

**预计时间**：1.5 天

#### 7. 控制台命令（优先级：🟢 低）
- [ ] `/dst console <room_id> <world_id> <cmd>` - 执行命令 🔒
- [ ] `/dst announce <room_id> <message>` - 发送公告 🔒

**预计时间**：0.5 天

**Phase 2 总计**：3.5 天

---

### 🤖 高级功能 - Phase 3（可选）

#### 8. AI 辅助功能
- [ ] AI 存档结构分析和修复
- [ ] AI 模组智能配置
- [ ] AI 模组冲突检测
- [ ] AI 故障诊断

**预计时间**：1-2 天

#### 9. 监控告警
- [ ] 服务器状态监控
- [ ] 定时任务集成
- [ ] 异常告警通知
- [ ] 统计图表生成

**预计时间**：1 天

**Phase 3 总计**：2-3 天

---

## 📁 完整项目结构

```
nonebot-dst-management/
├── nonebot_plugin_dst_management/
│   ├── __init__.py                 # 插件入口 ✅
│   ├── config.py                   # 配置模型 ✅
│   │
│   ├── client/                     # API 客户端层
│   │   ├── __init__.py
│   │   ├── api_client.py           # DMP API 客户端 ✅
│   │   └── models.py               # 数据模型
│   │
│   ├── handlers/                   # 命令处理器层
│   │   ├── __init__.py
│   │   ├── room.py                 # 房间管理命令 ⏳
│   │   ├── player.py               # 玩家管理命令 ⏳
│   │   ├── archive.py              # 存档管理命令 ⏳
│   │   ├── mod.py                  # 模组管理命令 ⏳
│   │   ├── backup.py               # 备份管理命令 ⏳
│   │   └── console.py              # 控制台命令 ⏳
│   │
│   ├── services/                   # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── archive_service.py      # 存档处理服务 ⏳
│   │   ├── mod_service.py          # 模组管理服务 ⏳
│   │   └── ai_service.py           # AI 辅助服务 ⏳
│   │
│   ├── utils/                      # 工具函数层
│   │   ├── __init__.py
│   │   ├── permission.py           # 权限检查 ✅
│   │   ├── formatter.py            # 消息格式化 ✅
│   │   └── validator.py            # 数据验证 ⏳
│   │
│   └── models/                     # 数据模型层
│       ├── __init__.py
│       ├── room.py                 # 房间模型 ⏳
│       ├── player.py               # 玩家模型 ⏳
│       └── mod.py                  # 模组模型 ⏳
│
├── tests/                          # 测试
│   ├── __init__.py
│   ├── test_api_client.py          # API 客户端测试 ⏳
│   ├── test_handlers.py            # 处理器测试 ⏳
│   └── test_services.py            # 服务测试 ⏳
│
├── docs/                           # 文档
│   ├── INSTALL.md                  # 安装指南 ✅
│   ├── COMMANDS.md                 # 命令参考 ✅
│   ├── API.md                      # API 文档 ⏳
│   └── ARCHITECTURE.md             # 架构设计 ⏳
│
├── examples/                       # 示例
│   └── bot.py                      # 示例 Bot ⏳
│
├── pyproject.toml                  # 项目配置 ✅
├── README.md                       # 项目说明 ✅
├── DEVELOPMENT_PLAN.md             # 开发计划 ✅
├── PROJECT_SUMMARY.md              # 项目总结 ✅
└── LICENSE                         # 许可证 ⏳

图例：
✅ 已完成
⏳ 待开发
```

---

## 🔧 核心代码骨架

### 1. 插件入口 (`__init__.py`)

```python
from nonebot import get_driver
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="DST服务器管理",
    description="通过DMP API管理Don't Starve Together服务器",
    usage="/dst help",
)

from .config import Config, dst_config
from .client.api_client import DSTApiClient

# 初始化 API 客户端
api_client = DSTApiClient(
    base_url=dst_config.dst_api_url,
    token=dst_config.dst_api_token
)

# 加载命令处理器
from .handlers import room, player, backup, mod, archive, console

room.init(api_client)
player.init(api_client)
backup.init(api_client)
# ...
```

### 2. 配置模型 (`config.py`)

```python
from pydantic import BaseModel, Field
from typing import List

class DSTConfig(BaseModel):
    dst_api_url: str = "http://localhost:8080"
    dst_api_token: str = ""
    dst_timeout: int = 10
    dst_admin_users: List[int] = Field(default_factory=list)
    dst_enable_ai: bool = False

class Config(BaseModel):
    dst: DSTConfig = Field(default_factory=DSTConfig)

driver = get_driver()
dst_config = Config().dst
```

### 3. API 客户端 (`client/api_client.py`)

```python
import httpx
from typing import Dict, Any, List

class DSTApiClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=f"{base_url}/v3",
            headers={"X-DMP-TOKEN": token}
        )

    async def get_room_list(self, page: int = 1) -> Dict[str, Any]:
        """获取房间列表"""
        response = await self.client.get("/room/list", params={"page": page})
        return response.json()

    # ... 更多 API 方法
```

### 4. 命令处理器示例 (`handlers/room.py`)

```python
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg

def init(api_client):
    room_list = on_command("dst list")

    @room_list.handle()
    async def handle(event: MessageEvent, args: Message = CommandArg()):
        result = await api_client.get_room_list()
        # 处理结果...
        await room_list.finish(message)
```

---

## 📅 详细开发时间表

### Week 1: MVP 开发

#### Day 1-2: 基础架构
- [ ] 创建项目结构
- [ ] 实现 `config.py`
- [ ] 实现 `api_client.py`（核心 API 方法）
- [ ] 实现 `permission.py` 和 `formatter.py`
- [ ] 编写基础测试

**验收标准**：
- 能够连接 DMP API
- 能够获取房间列表
- 权限检查正常工作

#### Day 3: 房间管理
- [ ] 实现 `handlers/room.py`
- [ ] 实现 5 个房间管理命令
- [ ] 消息格式化优化
- [ ] 错误处理完善

**验收标准**：
- 所有房间命令可用
- 消息格式清晰友好
- 错误提示完善

#### Day 4: 玩家和备份管理
- [ ] 实现 `handlers/player.py`
- [ ] 实现 `handlers/backup.py`
- [ ] 集成测试

**验收标准**：
- 能够查看玩家
- 能够管理备份

### Week 2: 增强功能

#### Day 5-6: 模组管理
- [ ] 实现 `handlers/mod.py`
- [ ] 实现 `services/mod_service.py`
- [ ] Steam Workshop 搜索集成

**验收标准**：
- 能够搜索和添加模组
- 能够配置模组

#### Day 7: 存档管理
- [ ] 实现 `handlers/archive.py`
- [ ] 实现 `services/archive_service.py`
- [ ] ZIP 文件处理

**验收标准**：
- 能够上传/下载存档
- 能够验证存档格式

#### Day 8: 控制台和其他
- [ ] 实现 `handlers/console.py`
- [ ] 完善所有命令
- [ ] 全文测试

#### Day 9-10: 测试和文档
- [ ] 完整的单元测试
- [ ] 集成测试
- [ ] 文档完善
- [ ] 发布准备

---

## 🎯 里程碑和验收标准

### Milestone 1: MVP 可用 (Day 4)
**验收标准**：
- ✅ 能够查看房间列表和详情
- ✅ 能够启动/关闭房间
- ✅ 能够查看在线玩家
- ✅ 能够创建和恢复备份
- ✅ 基本权限控制正常

### Milestone 2: 功能完整 (Day 8)
**验收标准**：
- ✅ 所有基础功能可用
- ✅ 模组管理功能完整
- ✅ 存档管理功能完整
- ✅ 测试覆盖率 > 80%

### Milestone 3: 生产就绪 (Day 10)
**验收标准**：
- ✅ 完整的文档
- ✅ 所有测试通过
- ✅ 性能优化完成
- ✅ 发布到 PyPI

---

## 🔗 可集成的 NoneBot 插件

### 必选集成
1. **nonebot-plugin-localstore**
   - 用途：用户偏好存储
   - 安装：`pip install nonebot-plugin-localstore`

2. **nonebot-plugin-apscheduler**
   - 用途：定时任务（自动备份等）
   - 安装：`pip install nonebot-plugin-apscheduler`

### 可选集成
3. **nonebot-plugin-status**
   - 用途：服务器状态监控
   - 安装：`pip install nonebot-plugin-status`

4. **nonebot-plugin-htmlrender**
   - 用途：生成统计图表
   - 安装：`pip install nonebot-plugin-htmlrender`

5. **nonebot-plugin-permission**
   - 用途：高级权限管理
   - 安装：`pip install nonebot-plugin-permission`

---

## 📊 技术栈总结

### 核心依赖
```
nonebot2[fastapi] >= 2.3.0      # NoneBot2 框架
nonebot-adapter-onebot >= 2.3.0  # OneBot 适配器
httpx >= 0.24.0                  # HTTP 客户端
pydantic >= 2.0.0                # 数据验证
loguru >= 0.7.0                  # 日志
```

### 开发依赖
```
pytest >= 7.4.0                  # 测试框架
pytest-asyncio >= 0.21.0         # 异步测试
black >= 23.0.0                  # 代码格式化
isort >= 5.12.0                  # import 排序
flake8 >= 6.0.0                  # 代码检查
```

### 可选依赖
```
openai >= 1.0.0                  # AI 支持
zipfile36 >= 0.1.3               # ZIP 处理
nonebot-plugin-localstore        # 数据存储
nonebot-plugin-apscheduler       # 定时任务
```

---

## 🔐 安全考虑

### 1. Token 安全
```python
# ✅ 好的做法：使用环境变量
DST_API_TOKEN=os.getenv("DST_API_TOKEN")

# ❌ 不好的做法：硬编码在代码中
DST_API_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 2. 权限验证
```python
# 所有管理员命令都要检查权限
if not await check_admin(event):
    await command.finish("❌ 只有管理员才能执行此操作")
```

### 3. 输入验证
```python
# 验证用户输入
room_id = args.extract_plain_text().strip()
if not room_id.isdigit():
    await command.finish("❌ 请提供有效的房间ID")
```

### 4. 频率限制
```python
# 防止命令滥用
from nonebot.plugin import PluginMetadata
__plugin_meta__.usage = "使用 /dst help 查看帮助"

# 实现简单的频率限制
```

---

## 📈 性能优化建议

### 1. 异步处理
```python
# ✅ 使用异步 API
async def get_room_list(self):
    return await self.client.get("/room/list")

# ❌ 避免同步阻塞
def get_room_list(self):
    return requests.get("/room/list")  # 阻塞事件循环
```

### 2. 缓存策略
```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
async def get_cached_room_list(room_id: int):
    """缓存房间列表 5 分钟"""
    # 实现...
```

### 3. 批量操作
```python
# 批量添加模组
async def batch_add_mods(room_id, mod_ids):
    tasks = [add_mod(room_id, mod_id) for mod_id in mod_ids]
    return await asyncio.gather(*tasks)
```

---

## 🧪 测试策略

### 单元测试
```python
# tests/test_api_client.py
import pytest
from nonebot_plugin_dst_management.client.api_client import DSTApiClient

@pytest.mark.asyncio
async def test_get_room_list():
    client = DSTApiClient("http://test", "test_token")
    result = await client.get_room_list()
    assert result["success"] is True
```

### 集成测试
```python
# tests/test_handlers.py
import pytest
from nonebot.adapters.onebot.v11 import Bot, MessageEvent

@pytest.mark.asyncio
async def test_room_list_command(bot: Bot):
    event = make_fake_message_event("/dst list")
    await handle_room_list(event)
    # 验证输出...
```

---

## 📝 文档清单

### 用户文档 ✅
- [x] README.md - 项目介绍
- [x] INSTALL.md - 安装指南
- [x] COMMANDS.md - 命令参考

### 开发文档 ⏳
- [ ] API.md - API 文档
- [ ] ARCHITECTURE.md - 架构设计
- [ ] CONTRIBUTING.md - 贡献指南
- [ ] CHANGELOG.md - 更新日志

---

## 🚀 发布计划

### v0.1.0 - Alpha (Day 4)
- MVP 功能
- 基础命令可用
- 内部测试

### v0.2.0 - Beta (Day 8)
- 所有核心功能
- 模组和存档管理
- 公开测试

### v1.0.0 - Release (Day 10)
- 生产就绪
- 完整文档
- PyPI 发布

---

## 📞 联系和支持

- **开发者**：小安 (Xiao An)
- **QQ 群**：744834037
- **GitHub**：https://github.com/your-repo/nonebot-dst-management
- **问题反馈**：https://github.com/your-repo/nonebot-dst-management/issues

---

## 🎓 学习资源

### NoneBot2 相关
- [NoneBot2 官方文档](https://nonebot.dev/docs/)
- [NoneBot2 插件开发指南](https://nonebot.dev/docs/creating-plugin)
- [NoneBot 插件商店](https://nonebot.dev/store/plugins)

### Python 异步编程
- [asyncio 官方文档](https://docs.python.org/3/library/asyncio.html)
- [Real Python: Async IO](https://realpython.com/async-io-python/)

### DST 相关
- [DMP API 文档](https://docs.miraclesses.top)
- [DST 官方论坛](https://forums.kleientertainment.com/)

---

## ✅ 检查清单

### 开发前
- [x] 阅读文档
- [x] 设计架构
- [x] 制定计划
- [ ] 搭建开发环境
- [ ] 准备测试服务器

### 开发中
- [ ] 编写代码
- [ ] 单元测试
- [ ] 代码审查
- [ ] 文档更新

### 发布前
- [ ] 完整测试
- [ ] 性能优化
- [ ] 安全检查
- [ ] 文档完善
- [ ] 发布准备

---

**最后更新**：2026-02-03
**维护者**：小安 (Xiao An)
**状态**：🎯 准备开始开发

---

## 🎉 下一步行动

1. ✅ 确认开发计划
2. ⏳ 创建项目骨架
3. ⏳ 实现 API 客户端
4. ⏳ 实现第一个命令
5. ⏳ 测试和迭代

**准备好了吗？让我们开始吧！** 🚀
