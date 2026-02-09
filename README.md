# nonebot-plugin-dst-management

nonebot-plugin-dst-management 是一个基于 NoneBot2 的 DST (Don't Starve Together) 服务器管理插件。插件通过 DMP (DST Management Platform) API v3 与服务器交互，提供房间生命周期、玩家、模组、备份/存档等常用管理能力，并可选集成 AI 辅助分析与推荐。

## 功能概览

- 房间管理：房间列表、详情查询、启动/停止/重启
- 玩家管理：在线玩家列表、踢出玩家
- 模组管理：模组搜索、已装模组查询、添加/移除、冲突检测
- 备份与存档：备份列表、创建/恢复；存档上传/下载/替换与结构校验
- 控制台：执行控制台命令、发送全服公告
- 可选能力：签到/奖励、AI 配置分析与模组推荐、中文命令别名与模糊纠错

## 环境要求

- Python >= 3.10
- NoneBot2 >= 2.3.0
- 适配器：OneBot v11、QQ 官方适配器
- 可用的 DMP API v3 服务与访问 Token

## 安装

通过 nb-cli 安装：

```bash
nb plugin install nonebot-plugin-dst-management
```

或使用 pip：

```bash
pip install nonebot-plugin-dst-management
```

可选依赖：

```bash
pip install nonebot-plugin-dst-management[ai]
pip install nonebot-plugin-dst-management[archive]
```

## 配置

插件会在启动时读取 NoneBot 配置与当前工作目录下的 `.env` (如存在)。常用环境变量如下：

```bash
# DMP API
DST_API_URL=http://localhost:8080
DST_API_TOKEN=your_dmp_token
DST_TIMEOUT=10

# 权限控制 (逗号分隔的数字 ID)
DST_ADMIN_USERS=123456789,987654321
DST_ADMIN_GROUPS=123456789

# 签到数据 (可选，默认 data/dst_sign.db)
DST_SIGN_DB_PATH=data/dst_sign.db
```

AI (可选)：

```bash
AI_ENABLED=false
AI_PROVIDER=openai
AI_API_KEY=
AI_API_URL=https://api.openai.com/v1
AI_MODEL=gpt-4
```

安全建议：请妥善保管 `DST_API_TOKEN` 与 AI Key，并将管理员范围限制在必要的用户/群。

## 使用示例

以下示例以默认命令前缀 `/` 为例 (具体以你的 NoneBot `command_start` 配置为准)：

```bash
/dst list
/dst info 2
/dst start 2
/dst players 2
/dst kick 2 KU_XXXX

/dst mod search 健康条
/dst mod list 2
/dst mod add 2 1 123456789
/dst backup create 2
/dst archive download 2
/dst console 2 c_announce("Hello")

# 查看完整帮助
/dst help
```

说明：

- 需要管理员权限的操作由 `DST_ADMIN_USERS` / `DST_ADMIN_GROUPS` 控制
- 插件提供部分中文别名与模糊纠错输入，便于在聊天环境中快速调用

## License

MIT

## Links

- Repository: https://github.com/uitok/nonebot-dst-management
- Issues: https://github.com/uitok/nonebot-dst-management/issues
