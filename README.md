# nonebot-dst-management

一个实用的 DST 饥荒联机版服务器管理插件

基于 NoneBot2 和 DMP API 实现，帮你在 QQ/TG 上管理服务器。

## 能做什么

- 房间管理 - 启动、停止、重启服务器
- 玩家管理 - 踢人、禁言、管理白名单
- 模组管理 - 搜索、安装、配置模组
- 备份管理 - 创建、恢复、管理存档备份
- AI 助手 - 配置分析、模组推荐、智能问答
- 中文命令 - 支持中文命令，更方便
- 默认房间 - 设置常用房间，省得每次都输 ID

## 快速开始

### 安装

```bash
nb plugin install nonebot-plugin-dst-management
```

或

```bash
pip install nonebot-plugin-dst-management
```

### 配置

在 `.env` 文件中添加：

```bash
DST_API_URL=http://your-dmp-api-url
DST_API_TOKEN=your_jwt_token
DST_ADMIN_USERS=["your_qq_number"]
```

### 基本用法

```bash
/dst list              # 查看房间
/dst info 2            # 查看详情
/dst start 2           # 启动服务器
/dst players 2         # 查看玩家
/dst kick 2 KU_xxx     # 踢人
/dst mod search 健康条 # 搜索模组
```

## 中文命令

高频命令都支持中文，用起来更顺手：

```bash
/dst 房间列表          # 查看房间
/dst 玩家列表 2        # 查看玩家
/dst 模组搜索 健康条   # 搜索模组
/dst 添加模组 2 1 123456789  # 安装模组
```

## 默认房间

主要管理一个房间的话，设为默认更省事：

```bash
/dst 默认房间 2
```

之后大部分命令不用输房间 ID：

```bash
/dst 玩家列表          # 自动用房间 2
/dst 模组列表          # 自动用房间 2
/dst 创建备份          # 自动用房间 2
```

## 完整命令

### 房间管理

| 命令 | 说明 |
|------|------|
| `/dst list [页码]` | 查看房间列表 |
| `/dst info <房间ID>` | 查看房间详情 |
| `/dst start <房间ID>` | 启动房间 |
| `/dst stop <房间ID>` | 停止房间 |
| `/dst restart <房间ID>` | 重启房间 |

中文别名：`房间列表`、`房间详情`

### 玩家管理

| 命令 | 说明 |
|------|------|
| `/dst players <房间ID>` | 查看在线玩家 |
| `/dst kick <房间ID> <KU_ID>` | 踢出玩家 |

中文别名：`玩家列表`、`踢出玩家`

### 模组管理

| 命令 | 说明 |
|------|------|
| `/dst mod search <关键词>` | 搜索模组 |
| `/dst mod list <房间ID>` | 查看已安装模组 |
| `/dst mod add <房间ID> <世界ID> <模组ID>` | 添加模组 |
| `/dst mod remove <房间ID> <世界ID> <模组ID>` | 删除模组 |
| `/dst mod check <房间ID>` | 检测模组冲突 |

中文别名：`模组搜索`、`模组列表`、`添加模组`、`移除模组`、`检测模组`

### 备份管理

| 命令 | 说明 |
|------|------|
| `/dst backup list <房间ID>` | 查看备份列表 |
| `/dst backup create <房间ID>` | 创建备份 |
| `/dst backup restore <房间ID> <文件名>` | 恢复备份 |

中文别名：`备份列表`、`创建备份`、`恢复备份`

### 默认房间

| 命令 | 说明 |
|------|------|
| `/dst 默认房间 <房间ID>` | 设置默认房间 |
| `/dst 查看默认` | 查看默认房间 |
| `/dst 清除默认` | 清除默认房间设置 |

### AI 功能

| 命令 | 说明 |
|------|------|
| `/dst analyze <房间ID>` | AI 配置分析 |
| `/dst mod recommend <房间ID> [类型]` | AI 模组推荐 |
| `/dst mod parse <房间ID> <世界ID>` | AI 模组配置解析 |
| `/dst archive analyze <文件>` | AI 存档分析 |
| `/dst ask <问题>` | AI 智能问答 |

AI 功能可选，需要配置 API Key 才能用。

## 环境要求

- Python 3.10+
- NoneBot2 2.3.0+
- DMP API 服务器

## 常见问题

**Q: 怎么获取 DMP API Token？**

A: 登录 DMP 管理后台，在设置里找 API Token。

**Q: AI 功能怎么用？**

A: AI 功能是可选的。要使用的话在 `.env` 中配置：

```bash
AI_ENABLED=true
AI_PROVIDER=openai
AI_API_KEY=your_openai_key
AI_MODEL=gpt-4
```

**Q: 默认房间重启后还在吗？**

A: 目前是内存存储，重启需要重新设置。

**Q: 中文命令和英文命令有区别吗？**

A: 没区别，功能完全一致。

## 更新日志

### v0.3.1 (2026-02-05)

- 新增默认房间功能
- 新增 24 个中文命令别名
- AI 诊断模式增强
- 测试覆盖率提升至 70%+

### v0.3.0 (2026-02-04)

- 新增 AI 智能命令
- Lua 解析安全修复
- 推荐结果验证

## 许可证

MIT License

## 链接

- GitHub: https://github.com/uitok/nonebot-dst-management
- 问题反馈: https://github.com/uitok/nonebot-dst-management/issues
