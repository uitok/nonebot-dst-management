# Alconna 命令系统迁移计划

## Context

nonebot-plugin-dst-management 项目当前使用 NoneBot2 的传统 `on_command` 系统，需要迁移到 `nonebot-plugin-alconna` 以获得更强大的命令解析能力、更好的类型安全和更简洁的代码结构。

**当前状态：**
- 使用 `on_command` + `aliases` 参数定义命令
- 5 个核心房间管理命令，24 个中文别名
- 自定义权限系统 (`check_admin`, `check_group`)
- 房间上下文系统 (`resolve_room_id`, `remember_room`)
- 模糊命令预处理器 (`normalize_command_text`)

---

## 实施方案

### Phase 1: 依赖安装

**文件:** `pyproject.toml`

在 `dependencies` 中添加：
```toml
"nonebot-plugin-alconna>=0.50.0",
```

安装命令：
```bash
pdm install
# 或
pip install nonebot-plugin-alconna
```

---

### Phase 2: 创建 Alconna 房间管理命令

**新文件:** `nonebot_plugin_dst_management/handlers/room_alconna.py`

使用 Alconna 的 `Subcommand` 结构组织命令：

```python
from arclet.alconna import Alconna, Args, Subcommand, CommandMeta
from nonebot_plugin_alconna import on_alconna, Match, AlconnaMatch

# 定义统一命令结构
dst_room_cmd = Alconna(
    "dst",
    Subcommand("list", Args["page?", int, 1]),
    Subcommand("info", Args["room_id?", int]),
    Subcommand("start", Args["room_id?", int]),
    Subcommand("stop", Args["room_id?", int]),
    Subcommand("restart", Args["room_id?", int]),
)

room_matcher = on_alconna(dst_room_cmd, priority=10, block=True)
```

---

### Phase 3: 实现 24 个中文别名

使用 Alconna 的 `shortcut()` 方法，在 `init()` 中注册所有别名：

| 子命令 | 中文别名 | 数量 |
|--------|----------|------|
| `dst list` | 房间列表, 列表, 查看房间, 查房间, 查房列表 | 5 |
| `dst info` | 房间详情, 详情, 房间信息, 查房, 查房间详情, 查详情 | 6 |
| `dst start` | 启动, 启动房间, 开房, 开启房间, 开服 | 5 |
| `dst stop` | 停止, 停止房间, 关闭, 关闭房间, 关房, 关服 | 6 |
| `dst restart` | 重启, 重启房间, 重开房间, 一键维护, 维护 | 5 |
| **合计** | | **27** |

```python
def init(api_client: DSTApiClient) -> None:
    # dst list 别名
    dst_room_cmd.shortcut("dst 房间列表", {"command": "dst list"})
    dst_room_cmd.shortcut("dst 列表", {"command": "dst list"})
    dst_room_cmd.shortcut("dst 查看房间", {"command": "dst list"})
    dst_room_cmd.shortcut("dst 查房间", {"command": "dst list"})
    dst_room_cmd.shortcut("dst 查房列表", {"command": "dst list"})

    # dst info 别名
    dst_room_cmd.shortcut("dst 房间详情", {"command": "dst info"})
    dst_room_cmd.shortcut("dst 详情", {"command": "dst info"})
    dst_room_cmd.shortcut("dst 房间信息", {"command": "dst info"})
    dst_room_cmd.shortcut("dst 查房", {"command": "dst info"})
    dst_room_cmd.shortcut("dst 查房间详情", {"command": "dst info"})
    dst_room_cmd.shortcut("dst 查详情", {"command": "dst info"})

    # dst start 别名
    dst_room_cmd.shortcut("dst 启动", {"command": "dst start"})
    dst_room_cmd.shortcut("dst 启动房间", {"command": "dst start"})
    dst_room_cmd.shortcut("dst 开房", {"command": "dst start"})
    dst_room_cmd.shortcut("dst 开启房间", {"command": "dst start"})
    dst_room_cmd.shortcut("dst 开服", {"command": "dst start"})

    # dst stop 别名
    dst_room_cmd.shortcut("dst 停止", {"command": "dst stop"})
    dst_room_cmd.shortcut("dst 停止房间", {"command": "dst stop"})
    dst_room_cmd.shortcut("dst 关闭", {"command": "dst stop"})
    dst_room_cmd.shortcut("dst 关闭房间", {"command": "dst stop"})
    dst_room_cmd.shortcut("dst 关房", {"command": "dst stop"})
    dst_room_cmd.shortcut("dst 关服", {"command": "dst stop"})

    # dst restart 别名
    dst_room_cmd.shortcut("dst 重启", {"command": "dst restart"})
    dst_room_cmd.shortcut("dst 重启房间", {"command": "dst restart"})
    dst_room_cmd.shortcut("dst 重开房间", {"command": "dst restart"})
    dst_room_cmd.shortcut("dst 一键维护", {"command": "dst restart"})
    dst_room_cmd.shortcut("dst 维护", {"command": "dst restart"})
```

---

### Phase 4: 集成权限控制

保持现有权限系统 (`utils/permission.py`)，在处理函数中直接调用：

```python
from ..utils.permission import check_admin, check_group

# 普通用户命令 — 仅检查群组权限
@room_matcher.assign("list")
async def handle_room_list(event: MessageEvent, ...):
    if not await check_group(event):
        await room_matcher.finish(format_error("当前群组未授权使用此功能"))
        return

# 管理员命令 — 同时检查管理员和群组权限
@room_matcher.assign("start")
async def handle_room_start(bot: Bot, event: MessageEvent, ...):
    if not await check_admin(bot, event):
        await room_matcher.finish(format_error("只有管理员才能执行此操作"))
        return
```

---

### Phase 5: 集成房间上下文系统

保持现有上下文系统 (`helpers/room_context.py`) 完全兼容：

```python
from ..helpers.room_context import RoomSource, remember_room, resolve_room_id

@room_matcher.assign("info")
async def handle_room_info(event: MessageEvent, room_id: Match[int] = AlconnaMatch("room_id")):
    room_arg = str(room_id.result) if room_id.available else None
    resolved = await resolve_room_id(event, room_arg)
    if resolved is None:
        await room_matcher.finish(format_error("请提供有效的房间ID"))
        return

    room_id_int = int(resolved.room_id)

    if resolved.source == RoomSource.LAST:
        await room_matcher.send(format_info(f"未指定房间ID，使用上次操作的房间 {room_id_int}..."))
    elif resolved.source == RoomSource.DEFAULT:
        await room_matcher.send(format_info(f"未指定房间ID，使用默认房间 {room_id_int}..."))

    # ... 业务逻辑 ...
    await remember_room(event, room_id_int)
```

---

### Phase 6: 更新插件初始化

**修改文件:** `__init__.py`

- 添加 `nonebot_plugin_alconna` 到 `require()`
- 将 `room.init(_api_client)` 替换为 `room_alconna.init(_api_client)`
- 保留旧 `room.py` 文件作为参考（不加载）

---

## 关键文件变更

| 文件 | 操作 |
|------|------|
| `pyproject.toml` | 添加 `nonebot-plugin-alconna` 依赖 |
| `handlers/room_alconna.py` | **新建** — Alconna 版本的房间命令处理器 |
| `__init__.py` | 修改 — 加载 Alconna 插件，切换到新处理器 |
| `utils/permission.py` | **不变** — 复用现有权限逻辑 |
| `helpers/room_context.py` | **不变** — 复用现有上下文逻辑 |
| `helpers/fuzzy.py` | **不变** — 预处理器继续正常工作 |

---

## 处理函数签名对照

### 迁移前 (on_command)
```python
room_list = on_command("dst list", aliases={...}, priority=10, block=True)

@room_list.handle()
async def handle_room_list(event: MessageEvent, args: Message = CommandArg()):
    page_str = args.extract_plain_text().strip()
    page = int(page_str) if page_str.isdigit() else 1
```

### 迁移后 (Alconna)
```python
@room_matcher.assign("list")
async def handle_room_list(event: MessageEvent, page: Match[int] = AlconnaMatch("page")):
    page_num = page.result if page.available else 1
```

---

## 验证步骤

1. **依赖安装**: `pdm install` 验证无错误
2. **命令解析测试**:
   - `/dst list` — 基本命令
   - `/dst list 2` — 带参数
   - `/dst 房间列表` — 中文别名
   - `/dst 开服` — 中文别名
   - `/dst 开服 1` — 中文别名 + 参数
3. **权限测试**: 验证管理员/普通用户权限正确区分
4. **上下文测试**: 验证默认房间和会话锁定功能
5. **fuzzy 兼容性测试**: 验证 "帮我开服" 等自然语言命令仍然工作

---

## 注意事项

1. **向后兼容**: 保留旧的 `room.py` 文件作为参考，不删除
2. **渐进式迁移**: 本次只迁移房间管理命令（5个），其他 handler 保持不变
3. **fuzzy 预处理器**: 保持原样，它在事件预处理层工作，与 Alconna 互不干扰
4. **权限逻辑**: 100% 复用现有的 `check_admin` 和 `check_group`
5. **shortcut 带参数**: 别名支持透传参数，如 `/dst 开服 1` 等效于 `/dst start 1`
