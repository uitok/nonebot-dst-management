# 快速开始指南

## 🚀 5 分钟快速上手

### 前置要求

- Python 3.10+
- NoneBot2 已安装
- DMP API 服务器可用

### 步骤 1: 安装插件

```bash
# 进入你的 NoneBot 项目目录
cd your-nonebot-project

# 安装插件
pip install nonebot-plugin-dst-management

# 或者使用 nb-cli
nb plugin install nonebot-plugin-dst-management
```

### 步骤 2: 配置环境变量

在项目根目录的 `.env` 文件中添加：

```bash
# DMP API 配置
DST_API_URL=http://285k.mc5173.cn:35555
DST_API_TOKEN=your_jwt_token_here
DST_TIMEOUT=10

# 管理员配置（可选）
DST_ADMIN_USERS=["6830441855"]

# 启用 AI（可选）
DST_ENABLE_AI=false
```

### 步骤 3: 加载插件

在 `bot.py` 或主入口文件中：

```python
import nonebot
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)

# 加载 DST 管理插件
nonebot.load_plugin("nonebot_plugin_dst_management")

if __name__ == "__main__":
    nonebot.run()
```

### 步骤 4: 运行 Bot

```bash
nb run
# 或
python bot.py
```

### 步骤 5: 测试命令

在 QQ 中发送：

```
/dst list
```

如果一切正常，你会看到房间列表！

---

## 📚 常用命令速查

### 房间管理
```
/dst list              # 查看所有房间
/dst info 2            # 查看房间 2 的详情
/dst start 2           # 启动房间 2
/dst stop 2            # 关闭房间 2
```

### 玩家管理
```
/dst players 2         # 查看房间 2 的在线玩家
/dst kick 2 KU_xxx     # 踢出玩家
```

### 备份管理
```
/dst backup list 2     # 查看房间 2 的备份
/dst backup create 2   # 为房间 2 创建备份
```

### 模组管理
```
/dst mod search 健康条 # 搜索健康条模组
/dst mod list 2        # 查看房间 2 的模组
```

---

## 🔧 本地开发

### 克隆项目

```bash
git clone https://github.com/your-repo/nonebot-dst-management.git
cd nonebot-dst-management
```

### 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black nonebot_plugin_dst_management/
isort nonebot_plugin_dst_management/
```

---

## 🐛 常见问题

### Q1: 提示 "连接 API 失败"

**A:** 检查以下几点：
1. DMP API 服务器是否运行中
2. `DST_API_URL` 是否正确
3. `DST_API_TOKEN` 是否有效

### Q2: 提示 "权限不足"

**A:** 将你的 QQ 号添加到管理员列表：
```bash
DST_ADMIN_USERS=["6830441855"]
```

### Q3: 命令没有响应

**A:** 检查：
1. 插件是否正确加载
2. 命令前缀是否正确（默认是 `/dst`）
3. 查看日志输出

### Q4: 如何获取 Token？

**A:** 登录 DMP 平台后，Token 会显示在用户信息或设置中。

---

## 📖 下一步

- 📖 阅读 [完整命令参考](COMMANDS.md)
- 📖 阅读 [API 文档](docs/API.md)
- 📖 查看 [架构设计](docs/ARCHITECTURE.md)
- 💬 加入 QQ 群：744834037

---

## 🆘 获取帮助

如果遇到问题：

1. 查看 [常见问题](#常见问题)
2. 搜索 [GitHub Issues](https://github.com/your-repo/nonebot-dst-management/issues)
3. 加入 QQ 群询问
4. 提交新的 Issue

---

**需要帮助？** 联系 admin@example.com | QQ 群：744834037
