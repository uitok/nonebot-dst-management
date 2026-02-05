# 中文命令别名

为了提升用户体验，��件为高频命令提供了中文别名。详细对照表请查看 [COMMAND_ALIASES.md](COMMAND_ALIASES.md)。

## 快速参考

### 房间管理
```bash
/dst 房间列表          # 查看房间列表
/dst 房间详情 2        # 查看房间详情
```

### 玩家管理
```bash
/dst 玩家列表 2        # 查看在线玩家
/dst 踢出玩家 2 KU_xxx # 踢出玩家
```

### 模组管理
```bash
/dst 模组搜索 健康条   # 搜索模组
/dst 模组列表 2        # 查看已安装模组
/dst 添加模组 2 1 123456789  # 安装模组
/dst 移除模组 2 1 123456789  # 删除模组
/dst 检测模组 2        # 检测模组冲突
```

### 备份管理
```bash
/dst 备份列表 2        # 查看备份列表
/dst 创建备份 2        # 创建备份
/dst 恢复备份 2 backup_xxx.zip  # 恢复备份
```

### 默认房间
```bash
/dst 默认房间 2        # 设置默认房间
/dst 查看默认          # 查看默认房间
/dst 清除默认          # 清除默认房间设置
```

设置默认房间后，大部分命令可省略房间 ID 参数：

```bash
/dst 玩家列表          # 使用默认房间
/dst 模组列表          # 使用默认房间
/dst 创建备份          # 使用默认房间
```

---

# 使用示例

## 房间管理
```bash
/dst list                    # 查看房间列表
/dst info 2                  # 查看房间详情
/dst start 2                 # 启动房间
/dst stop 2                  # 关闭房间

# 中文命令
/dst 房间列表          # 同上
/dst 房间详情 2        # 同上
```

## 玩家管理
```bash
/dst players 2               # 查看在线玩家
/dst kick 2 KU_BQAUz1rk      # 踢出玩家

# 中文命令
/dst 玩家列表 2        # 同上
/dst 踢出玩家 2 KU_xxx # 同上
```

## 模组管理
```bash
/dst mod search 健康条       # 搜索模组
/dst mod add 2 1 1185229307  # 添加模组
/dst mod check 2             # 检测模组冲突

# 中文命令
/dst 模组搜索 健康条   # 同上
/dst 添加模组 2 1 1185229307  # 同上
/dst 检测模组 2        # 同上
```

## 备份管理
```bash
/dst backup list 2           # 查看备份
/dst backup create 2         # 创建备份

# 中文命令
/dst 备份列表 2        # 同上
/dst 创建备份 2        # 同上
```

## AI 功能
```bash
/dst analyze 2               # AI 配置分析
/dst mod recommend 2 生存     # AI 模组推荐
/dst mod parse 2 1           # AI 模组配置解析
/dst mod config save 2 1 --optimized  # 保存 AI 优化配置
/dst archive analyze /path/to/archive.zip # AI 存档分析
/dst ask 冬天基地怎么搭？     # AI 智能问答
/dst ask --stream 冬天基地怎么搭？  # AI 流式问答
/dst ask reset               # 清空 AI 会话上下文

# 中文命令
/dst 配置分析 2         # 同上
/dst 模组推荐 2 生存     # 同上
/dst 模组解析 2 1       # 同上
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
│   │   ├── console.py              # 控制台命令
│   │   ├── default_room.py         # 默认房间功能
│   │   └── ai_*.py                 # AI 功能
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
│   ├── test_default_room.py        # 默认房间测试
│   └── test_services.py
├── docs/
│   ├── INSTALL.md
│   ├── COMMANDS.md
│   ├── COMMAND_ALIASES.md          # 中文命令别名对照表
│   └── API.md
├── examples/
│   └── bot.py
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## 🧭 命令总览（v0.3.0）

### 房间管理（5个）
- `/dst list [页码]` - 查看房间列表
- `/dst info <房间ID>` - 查看房间详情
- `/dst start <房间ID>` - 启动房间 🔒
- `/dst stop <房间ID>` - 关闭房间 🔒
- `/dst restart <房间ID>` - 重启房间 🔒

**中文别名**：
- `/dst 房间列表` → list
- `/dst 房间详情` → info

### 玩家管理（2个）
- `/dst players <房间ID>` - 查看在线玩家
- `/dst kick <房间ID> <KU_ID>` - 踢出玩家 🔒

**中文别名**：
- `/dst 玩家列表` → players
- `/dst 踢出玩家` → kick

### 备份管理（3个）
- `/dst backup list <房间ID>` - 查看备份列表
- `/dst backup create <房间ID>` - 创建备份 🔒
- `/dst backup restore <房间ID> <文件名>` - 恢复备份 🔒

**中文别名**：
- `/dst 备份列表` → backup list
- `/dst 创建备份` → backup create
- `/dst 恢复备份` → backup restore

### 存档管理（4个）
- `/dst archive upload <房间ID> <文件URL或文件路径>` - 上传存档 🔒
- `/dst archive download <房间ID>` - 下载存档
- `/dst archive replace <房间ID> <文件URL或文件路径>` - 替换存档 🔒
- `/dst archive validate <文件路径>` - 验证存档结构

### 模组管理（6个）
- `/dst mod search <关键词>` - 搜索模组
- `/dst mod list <房间ID>` - 查看已安装模组
- `/dst mod add <房间ID> <世界ID> <模组ID>` - 添加模组 🔒
- `/dst mod remove <房间ID> <世界ID> <模组ID>` - 删除模组 🔒
- `/dst mod check <房间ID>` - 检测模组冲突

**中文别名**：
- `/dst 模组搜索` → mod search
- `/dst 模组列表` → mod list
- `/dst 添加模组` → mod add
- `/dst 移除模组` → mod remove
- `/dst 检测模组` → mod check

### 控制台命令（2个）
- `/dst console <房间ID> [世界ID] <命令>` - 执行控制台命令 🔒
- `/dst announce <房间ID> <消息>` - 发送全服公告 🔒

### AI 功能（5个）
- `/dst analyze <房间ID>` - AI 配置分析
- `/dst mod recommend <房间ID> [类型]` - AI 模组推荐
- `/dst mod parse <房间ID> <世界ID>` - AI 模组配置解析
- `/dst archive analyze <文件路径>` - AI 存档分析
- `/dst ask <问题>` - AI 智能问答

### 默认房间（3个）
- `/dst 默认房间 <房间ID>` - 设置默认房间
- `/dst 查看默认` - 查看默认房间
- `/dst 清除默认` - 清除默认房间设置

🔒 标记的命令需要管理员权限

**总计**：27 个命令 + 15 个中文别名

提示：设置默认房间后，大部分命令可省略房间ID参数

---

## 🔧 高级配置

### AI 配置
插件支持多种 AI 提供商：OpenAI、Claude、Ollama、Mock。

#### OpenAI 配置
```bash
AI_PROVIDER=openai
AI_API_KEY=sk-xxx
AI_API_URL=https://api.openai.com/v1
AI_MODEL=gpt-4
```

#### Claude 配置
```bash
AI_PROVIDER=claude
AI_API_KEY=sk-ant-xxx
AI_API_URL=https://api.anthropic.com/v1
AI_MODEL=claude-3-sonnet-20240229
```

#### Ollama 配置
```bash
AI_PROVIDER=ollama
AI_API_URL=http://localhost:11434
AI_MODEL=llama2:13b
```

#### Mock 配置（测试用）
```bash
AI_PROVIDER=mock
```

### 权限配置
```bash
# 管理员用户 ID（QQ 号）
DST_ADMIN_USERS=["123456789", "987654321"]

# 管理员群组 ID（QQ 群号）
DST_ADMIN_GROUPS=["987654321", "123456789"]
```

---

## 📝 开发

### 安装开发依赖
```bash
git clone https://github.com/your-repo/nonebot-dst-management.git
cd nonebot-dst-management
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 运行测试
```bash
pytest -v
pytest --cov=nonebot_plugin_dst_management
```

### 代码规范
项目遵循以下规范：
- PEP 8 代码风格
- Black 代码格式化
- isort 导入排序
- 类型提示（Type Hints）

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

MIT License

---

## 📞 联系方式

- **GitHub**: https://github.com/your-repo/nonebot-dst-management
- **Issues**: https://github.com/your-repo/nonebot-dst-management/issues
- **Discussions**: https://github.com/your-repo/nonebot-dst-management/discussions

---

## 🌟 Star History

如果这个项目对你有帮助，请给一个 Star ⭐️

---

**最后更新**: 2026-02-04
**版本**: v0.3.0
