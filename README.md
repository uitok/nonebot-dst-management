# NoneBot2 DST 服务器管理插件

## 🎯 项目概述

一个强大的 NoneBot2 插件，用于管理 Don't Starve Together (DST) 饥荒联机版服务器。

### ✨ 核心特性

- 🏕️ **房间管理** - 创建、启动、停止、重启服务器
- 👥 **玩家管理** - 查看在线玩家、踢人、白名单管理
- 📦 **存档管理** - 上传、下载、替换存档（AI辅助格式验证）
- 🧩 **模组管理** - 搜索、安装、配置模组（AI智能配置）
- 💾 **备份管理** - 创建、恢复、删除备份
- 🔧 **控制台命令** - 执行游戏内命令、发送公告
- 📊 **监控告警** - 系统监控、玩家统计、异常告警

### 🚀 为什么选择 NoneBot2？

| 特性 | NoneBot2 | OneBot (原生) |
|------|----------|---------------|
| **插件生态** | ✅ 200+ 插件可复用 | ❌ 需自己开发 |
| **多平台支持** | ✅ QQ、Telegram、Discord 等 | ❌ 仅 QQ |
| **异步性能** | ✅ 原生 async/await | ⚠️ 回调/事件 |
| **权限管理** | ✅ 可集成权限插件 | ❌ 需自己实现 |
| **定时任务** | ✅ 可集成调度器插件 | ❌ 需自己实现 |
| **数据存储** | ✅ 可集成数据库插件 | ❌ 需自己实现 |
| **AI 集成** | ✅ 丰富的 AI 插件 | ❌ 需自己实现 |

### 📦 可复用的 NoneBot2 插件

1. **nonebot-plugin-localstore** - 数据持久化
2. **nonebot-plugin-apscheduler** - 定时任务
3. **nonebot-plugin-status** - 状态监控
4. **nonebot-plugin-permission** - 权限管理
5. **nonebot-plugin-htmlrender** - 图表渲染
6. **nonebot-plugin-gocqhttp** - Go-CQHTTP 协议支持

---

## 📋 快速开始

### 安装

```bash
# 使用 nb-cli 安装（推荐）
nb plugin install nonebot-plugin-dst-management

# 或使用 pip 安装
pip install nonebot-plugin-dst-management
```

### 配置

在 NoneBot 项目的 `.env` 文件中添加：

```bash
# DMP API 配置
DST_API_URL=http://285k.mc5173.cn:35555
DST_API_TOKEN=your_jwt_token_here
DST_TIMEOUT=10

# 管理员配置
DST_ADMIN_USERS=["6830441855"]
DST_ADMIN_GROUPS=[]

# AI 配置（可选）
DST_ENABLE_AI=true
DST_AI_PROVIDER=openai
DST_AI_API_KEY=your_openai_key
DST_AI_MODEL=gpt-4
```

### 使用示例

```python
import nonebot
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)

# 加载插件
nonebot.load_plugin("nonebot_plugin_dst_management")

if __name__ == "__main__":
    nonebot.run()
```

### 命令示例

```bash
# 房间管理
/dst list                    # 查看房间列表
/dst info 2                  # 查看房间详情
/dst start 2                 # 启动房间
/dst stop 2                  # 关闭房间

# 玩家管理
/dst players 2               # 查看在线玩家
/dst kick 2 KU_BQAUz1rk      # 踢出玩家

# 模组管理
/dst mod search 健康条       # 搜索模组
/dst mod add 2 1 1185229307  # 添加模组

# 备份管理
/dst backup list 2           # 查看备份
/dst backup create 2         # 创建备份

# 更多命令...
```

---

## 📁 项目结构

```
nonebot-dst-management/
├── nonebot_plugin_dst_management/
│   ├── __init__.py                 # 插件入口
│   ├── config.py                   # 配置模型
│   ├── client/
│   │   ├── __init__.py
│   │   ├── api_client.py           # DMP API 客户端
│   │   └── models.py               # 数据模型
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── room.py                 # 房间管理
│   │   ├── player.py               # 玩家管理
│   │   ├── archive.py              # 存档管理
│   │   ├── mod.py                  # 模组管理
│   │   ├── backup.py               # 备份管理
│   │   └── console.py              # 控制台命令
│   ├── services/
│   │   ├── __init__.py
│   │   ├── archive_service.py      # 存档处理服务
│   │   ├── mod_service.py          # 模组管理服务
│   │   └── ai_service.py           # AI 辅助服务
│   └── utils/
│       ├── __init__.py
│       ├── permission.py           # 权限检查
│       ├── formatter.py            # 消息格式化
│       └── validator.py            # 数据验证
├── tests/
│   ├── test_api_client.py
│   ├── test_handlers.py
│   └── test_services.py
├── docs/
│   ├── INSTALL.md
│   ├── COMMANDS.md
│   └── API.md
├── examples/
│   └── bot.py
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## 🔧 核心功能详解

### 1. 房间管理

**命令列表：**
- `/dst list [页码]` - 查看房间列表
- `/dst info <房间ID>` - 查看房间详情
- `/dst start <房间ID>` - 启动房间 🔒
- `/dst stop <房间ID>` - 关闭房间 🔒
- `/dst restart <房间ID>` - 重启房间 🔒
- `/dst create` - 创建新房间 🔒

**功能说明：**
- 支持分页显示（每页10个房间）
- 显示房间状态、模式、在线玩家数
- 显示世界列表和端口信息
- 管理员操作需要权限验证

### 2. 玩家管理

**命令列表：**
- `/dst players <房间ID>` - 查看在线玩家
- `/dst stats <房间ID>` - 查看玩家统计
- `/dst kick <房间ID> <KU_ID>` - 踢出玩家 🔒
- `/dst whitelist add <房间ID> <KU_ID>` - 添加白名单 🔒
- `/dst blacklist add <房间ID> <KU_ID>` - 添加黑名单 🔒

**功能说明：**
- 显示玩家角色、存活时间、在线时长
- 支持批量操作
- 操作日志记录

### 3. 存档管理

**命令列表：**
- `/dst archive upload <房间ID> <文件>` - 上传存档 🔒
- `/dst archive download <房间ID>` - 下载存档
- `/dst archive replace <房间ID> <文件>` - 替换存档 🔒
- `/dst archive validate <文件>` - 验证存档格式

**功能说明：**
- 支持 ZIP 格式存档
- AI 辅助存档结构分析和修复
- 自动备份当前存档
- 支持多世界配置

**AI 辅助功能：**
```python
# 自动识别存档结构
- Master/Caves 世界配置
- modoverrides.lua 模组配置
- cluster.ini 房间配置
- cluster_token.txt 令牌文件

# 自动修复问题
- 缺失文件补全
- 语法错误修复
- 配置冲突解决
```

### 4. 模组管理

**命令列表：**
- `/dst mod search <关键词>` - 搜索模组
- `/dst mod list <房间ID>` - 查看已安装模组
- `/dst mod add <房间ID> <世界ID> <模组ID>` - 添加模组 🔒
- `/dst mod remove <房间ID> <世界ID> <模组ID>` - 删除模组 🔒
- `/dst mod enable <房间ID> <世界ID> <模组ID>` - 启用模组 🔒
- `/dst mod disable <房间ID> <世界ID> <模组ID>` - 禁用模组 🔒
- `/dst mod config <房间ID> <世界ID> <模组ID>` - 修改配置 🔒
- `/dst mod check <房间ID>` - 检测模组冲突

**功能说明：**
- 从 Steam Workshop 搜索模组
- AI 智能配置模组参数
- 自动检测模组冲突
- 批量启用/禁用
- 推荐配置加载顺序

**AI 智能配置：**
```python
# 自动分析模组功能
- 游戏机制修改类
- UI 增强类
- 新增物品类
- 平衡性调整类

# 推荐配置
- 根据模组类型设置合理默认值
- 检测配置冲突
- 优化性能参数
```

### 5. 备份管理

**命令列表：**
- `/dst backup list <房间ID>` - 查看备份列表
- `/dst backup create <房间ID>` - 创建备份 🔒
- `/dst backup restore <房间ID> <序号>` - 恢复备份 🔒
- `/dst backup delete <房间ID> <序号>` - 删除备份 🔒

**功能说明：**
- 显示备份大小和创建时间
- 支持定时自动备份（需 apscheduler 插件）
- 恢复前二次确认
- 自动清理过期备份

### 6. 控制台命令

**命令列表：**
- `/dst console <房间ID> <世界ID> <命令>` - 执行控制台命令 🔒
- `/dst announce <房间ID> <消息>` - 发送全服公告 🔒
- `/dst rollback <房间ID> <天数>` - 回滚存档 🔒
- `/dst regenerate <房间ID> <世界ID>` - 重新生成世界 🔒

**功能说明：**
- 支持所有 DST 控制台命令
- 命令历史记录
- 危险操作二次确认

### 7. 监控告警

**功能说明：**
- 实时监控服务器状态
- 玩家数量统计
- CPU/内存使用率
- 自动异常告警

**集成插件：**
- `nonebot-plugin-status` - 状态监控
- `nonebot-plugin-apscheduler` - 定时检查

---

## 🎨 消息格式示例

### 房间列表

```
🏕️ DST 房间列表
第 1/2 页 | 共 15 个房间

1. 勋棱神话
   状态：🟢 运行中
   模式：无尽
   ID：2

2. 测试服务器
   状态：🔴 已停止
   模式：生存
   ID：3

💡 使用 /dst info <房间ID> 查看详情
💡 使用 /dst list 2 查看下一页
```

### 房间详情

```
🏕️ 勋棱神话

📋 基本信息
- 房间ID：2
- 状态：🟢 运行中
- 模式：无尽
- 玩家限制：6人
- 密码：已设置
- PVP：关闭
- 描述：有问题＋裙744834037

🌍 世界列表
- Master：🟢 在线 (端口 37777)
- Caves：🟢 在线 (端口 36666)

👥 在线玩家 (1人)
- 󰀍八雪󰀍 (white_bone)

🧩 已安装模组：21个
```

### 在线玩家

```
👥 在线玩家 (勋棱神话)

1. 󰀍八雪󰀍 (KU_BQAUz1rk)
   - KU_ID: KU_BQAUz1rk
   - 角色: 白骨
   - 存活: 15天
   - 在线: 2小时30分

共 1/6 名玩家在线
```

---

## 🔐 权限系统

### 权限级别

1. **普通用户**
   - 查看房间列表
   - 查看房间详情
   - 查看在线玩家
   - 查看备份列表

2. **管理员**
   - 所有普通用户权限
   - 启动/关闭房间
   - 踢出玩家
   - 管理备份
   - 管理模组
   - 执行控制台命令

3. **超级管理员**
   - 所有管理员权限
   - 创建/删除房间
   - 系统配置
   - 用户权限管理

### 权限配置

```python
# .env
DST_ADMIN_USERS=["6830441855"]           # 管理员 QQ 号列表
DST_ADMIN_GROUPS=[744834037]              # 允许的群组列表
SUPERUSERS=["6830441855"]                 # 超级用户（NoneBot 内置）
```

---

## 🤖 AI 辅助功能（可选）

### AI 功能清单

1. **存档智能分析**
   - 自动识别存档文件结构
   - 修复缺失的配置文件
   - 验证 Lua 语法

2. **模组��能配置**
   - 分析模组功能和类型
   - 推荐最佳配置参数
   - 检测模组冲突

3. **故障诊断**
   - 分析服务器日志
   - 识别常见问题
   - 提供解决方案

4. **性能优化**
   - 分析配置性能影响
   - 推荐优化方案
   - 资源使用预测

### AI 提供商支持

- ✅ OpenAI (GPT-4/GPT-3.5)
- ✅ Claude (Anthropic)
- ✅ 本地模型 (Ollama)
- ✅ 阿里云通义千问
- ✅ 百度文心一言

### AI 配置示例

```bash
# .env
DST_ENABLE_AI=true
DST_AI_PROVIDER=openai
DST_AI_API_KEY=sk-xxx
DST_AI_MODEL=gpt-4
DST_AI_BASE_URL=https://api.openai.com/v1
```

---

## 📊 高级功能集成

### 1. 定时任务（集成 apscheduler）

```python
# 自动备份
from nonebot.plugin import PluginMetadata
require("nonebot_plugin_apscheduler")

scheduler = require("nonebot_plugin_apscheduler").scheduler

@scheduler.scheduled_job("cron", hour=2, minute=0)
async def auto_backup():
    """每天凌晨2点自动备份所有房间"""
    # 实现自动备份逻辑
    pass

@scheduler.scheduled_job("interval", minutes=30)
async def check_server_status():
    """每30分钟检查服务器状态"""
    # 实现状态检查逻辑
    pass
```

### 2. 数据持久化（集成 localstore）

```python
from nonebot_plugin_localstore import store

# 保存用户偏好
await store.set("dst_preferences", user_id, {
    "default_room": 2,
    "notify_on_join": True
})

# 读取用户偏好
prefs = await store.get("dst_preferences", user_id)
```

### 3. 状态监控（集成 status）

```python
from nonebot_plugin_status import status

# 监控服务器状态
@status.track("dst_server_2")
async def track_server_status():
    """追踪房间2的状态"""
    result = await api_client.get_room_info(2)
    return {
        "status": "online" if result["data"]["status"] else "offline",
        "players": len(result["data"]["players"])
    }
```

### 4. 图表渲染（集成 htmlrender）

```python
from nonebot_plugin_htmlrender import template_to_pic

# 生成玩家统计图表
async def generate_player_chart(room_id: int):
    """生成玩家在线时长图表"""
    stats = await api_client.get_online_time_stats(room_id)

    template = """
    <html>
      <body>
        <canvas id="chart"></canvas>
        <script>
          // 使用 Chart.js 生成图表
        </script>
      </body>
    </html>
    """

    img = await template_to_pic(
        template=template,
        data={"stats": stats}
    )

    return MessageSegment.image(img)
```

---

## 🧪 开发和测试

### 本地开发

```bash
# 克隆项目
git clone https://github.com/your-repo/nonebot-dst-management.git
cd nonebot-dst-management

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black nonebot_plugin_dst_management/
isort nonebot_plugin_dst_management/

# 代码检查
flake8 nonebot_plugin_dst_management/
```

### 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_api_client.py

# 生成覆盖率报告
pytest --cov=nonebot_plugin_dst_management --cov-report=html
```

### 调试

```bash
# 启用调试模式
export LOG_LEVEL=DEBUG
nb run

# 或者在代码中
import loguru
logger = loguru.logger
logger.debug("Debug message")
```

---

## 📚 文档

- [安装指南](docs/INSTALL.md)
- [命令参考](docs/COMMANDS.md)
- [API 文档](docs/API.md)
- [架构设计](docs/ARCHITECTURE.md)
- [贡献指南](docs/CONTRIBUTING.md)

---

## 🤝 贡献

欢迎贡献代码！请查看 [CONTRIBUTING.md](docs/CONTRIBUTING.md) 了解详情。

### 贡献方式

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📝 更新日志

### v0.1.0 (2026-02-03)

**新增功能**
- ✅ 房间管理（列表、详情、开关）
- ✅ 玩家管理（查看、踢人）
- ✅ 基础权限系统
- ✅ API 客户端封装

**已知问题**
- 暂不支持存档上传
- AI 功能待完善

**计划中**
- ⏳ 存档管理
- ⏳ 模组管理增强
- ⏳ 监控告警

---

## 🔗 相关链接

- [NoneBot2 文档](https://nonebot.dev/docs/)
- [NoneBot 插件商店](https://nonebot.dev/store/plugins)
- [DMP API 文档](https://docs.miraclesses.top)
- [DST 官方论坛](https://forums.kleientertainment.com/)

---

## 📄 许可证

MIT License

Copyright (c) 2026 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

**作者**: 小安 (Xiao An)
**邮箱**: admin@example.com
**QQ群**: 744834037
**GitHub**: https://github.com/your-repo

💖 如果这个项目对你有帮助，请给个 Star！
