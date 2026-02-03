# NoneBot2 DST 管理插件 - 详细开发计划

## 📅 开发时间表（7天冲刺）

### Day 1: 项��初始化和基础框架

**目标**: 搭建项目结构，实现 API 客户端

**任务清单**:
- [x] 创建项目目录结构
- [x] 编写 `pyproject.toml` 配置
- [x] 实现 `config.py` 配置模型
- [x] 实现 `api_client.py` API 客户端
- [x] 编写基础测试用例
- [x] 设置开发环境

**预期产出**:
- 可运行的插件框架
- 能够连接 DMP API 并获取数据
- 基础测试通过

**代码示例**:

```python
# nonebot_plugin_dst_management/client/api_client.py
import httpx
from typing import Optional, Dict, Any, List
from loguru import logger

class DSTApiClient:
    def __init__(self, base_url: str, token: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.client = httpx.AsyncClient(
            base_url=f"{self.base_url}/v3",
            headers={"X-DMP-TOKEN": token},
            timeout=timeout
        )

    async def get_room_list(self, page: int = 1, page_size: int = 10):
        response = await self.client.get("/room/list", params={
            "page": page,
            "pageSize": page_size
        })
        return response.json()
```

---

### Day 2: 房间管理功能

**目标**: 实现房间查询和管理命令

**任务清单**:
- [x] 实现 `/dst list` 命令
- [x] 实现 `/dst info` 命令
- [x] 实现 `/dst start` 命令（管理员）
- [x] 实现 `/dst stop` 命令（管理员）
- [x] 实现 `/dst restart` 命令（管理员）
- [x] 实现权限检查
- [x] 实现消息格式化

**代码示例**:

```python
# nonebot_plugin_dst_management/handlers/room.py
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg

dst_list = on_command("dst list", priority=10, block=True)

@dst_list.handle()
async def handle_room_list(event: MessageEvent, args: Message = CommandArg()):
    page_str = args.extract_plain_text().strip()
    page = int(page_str) if page_str.isdigit() else 1

    result = await api_client.get_room_list(page=page, page_size=10)

    if result.get("code") != 200:
        await dst_list.finish(f"❌ 获取失败：{result.get('message')}")

    data = result.get("data", {})
    rooms = data.get("rows", [])

    message = format_room_list(rooms, page, data.get("totalCount", 0))
    await dst_list.finish(message)

def format_room_list(rooms, page, total):
    lines = ["🏕️ DST 房间列表", f"第 {page} 页"]
    for room in rooms:
        status = "🟢" if room.get("status") else "🔴"
        lines.append(f"{status} {room.get('gameName')} (ID: {room.get('id')})")
    return "\n".join(lines)
```

---

### Day 3: 玩家和备份管理

**目标**: 实现玩家查询和备份功能

**任务清单**:
- [x] 实现 `/dst players` 命令
- [x] 实现 `/dst stats` 命令
- [x] 实现 `/dst kick` 命令（管理员）
- [x] 实现 `/dst backup list` 命令
- [x] 实现 `/dst backup create` 命令（管理员）
- [x] 实现 `/dst backup restore` 命令（管理员）

**代码示例**:

```python
# nonebot_plugin_dst_management/handlers/player.py
dst_players = on_command("dst players", priority=10, block=True)

@dst_players.handle()
async def handle_players(event: MessageEvent, args: Message = CommandArg()):
    room_id_str = args.extract_plain_text().strip()
    if not room_id_str.isdigit():
        await dst_players.finish("❌ 请提供房间ID：/dst players <房间ID>")

    room_id = int(room_id_str)
    result = await api_client.get_online_players(room_id)

    if result.get("code") != 200:
        await dst_players.finish(f"❌ 获取失败：{result.get('message')}")

    players = result.get("data", [])
    message = format_players(players)
    await dst_players.finish(message)

def format_players(players):
    if not players:
        return "🈳 当前没有玩家在线"

    lines = ["👥 在线玩家", ""]
    for idx, player in enumerate(players, 1):
        nickname = player.get("nickname") or player.get("uid")
        prefab = player.get("prefab", "未知")
        lines.append(f"{idx}. {nickname} ({prefab})")

    return "\n".join(lines)
```

---

### Day 4: 模组管理基础功能

**目标**: 实现模组查询和管理

**任务清单**:
- [x] 实现 `/dst mod search` 命令
- [x] 实现 `/dst mod list` 命令
- [x] 实现 `/dst mod add` 命令（管理员）
- [x] 实现 `/dst mod remove` 命令（管理员）
- [x] 实现模组配置解析

**代码示例**:

```python
# nonebot_plugin_dst_management/handlers/mod.py
dst_mod_search = on_command("dst mod search", priority=10, block=True)

@dst_mod_search.handle()
async def handle_mod_search(event: MessageEvent, args: Message = CommandArg()):
    keyword = args.extract_plain_text().strip()
    if not keyword:
        await dst_mod_search.finish("❌ 请提供搜索关键词：/dst mod search <关键词>")

    result = await api_client.search_mod("text", keyword)

    if result.get("code") != 200:
        await dst_mod_search.finish(f"❌ 搜索失败：{result.get('message')}")

    mods = result.get("data", [])
    message = format_mod_search_results(mods, keyword)
    await dst_mod_search.finish(message)

def format_mod_search_results(mods, keyword):
    if not mods:
        return f"🈳 未找到包含 \"{keyword}\" 的模组"

    lines = [f"🧩 模组搜索结果：{keyword}", ""]
    for idx, mod in enumerate(mods[:10], 1):
        lines.append(f"{idx}. {mod.get('name')}")
        lines.append(f"   ID: {mod.get('id')}")
        lines.append(f"   作者: {mod.get('author', '未知')}")

    return "\n".join(lines)
```

---

### Day 5: 存档管理功能

**目标**: 实现存档上传和下载

**任务清单**:
- [x] 实现存档解析服务
- [x] 实现 `/dst archive upload` 命令
- [x] 实现 `/dst archive download` 命令
- [x] 实现 `/dst archive replace` 命令
- [x] 集成 AI 辅助功能（可选）

**代码示例**:

```python
# nonebot_plugin_dst_management/services/archive_service.py
import zipfile
import io
from typing import Dict, Any

class ArchiveService:
    def __init__(self, api_client):
        self.client = api_client

    async def upload_archive(self, room_id: int, archive_data: bytes):
        """上传存档"""
        # 解析 ZIP 文件
        try:
            with zipfile.ZipFile(io.BytesIO(archive_data)) as zip_file:
                structure = await self._parse_archive(zip_file)
        except Exception as e:
            return {"success": False, "error": f"存档解析失败：{str(e)}"}

        # 验证结构
        validation = await self._validate_structure(structure)
        if not validation["valid"]:
            return {"success": False, "error": f"存档验证失败：{validation['errors']}"}

        # 更新房间配置
        result = await self.client.update_room(
            room_id=room_id,
            room_data={},
            world_data_list=structure["worlds"],
            room_setting_data={}
        )

        return result

    async def _parse_archive(self, zip_file: zipfile.ZipFile) -> Dict[str, Any]:
        """解析存档结构"""
        structure = {
            "worlds": [],
            "mods": None,
            "cluster": None
        }

        for file in zip_file.filelist:
            if file.filename.endswith("leveldataoverride.lua"):
                world_name = "Master" if "Master" in file.filename else "Caves"
                content = zip_file.read(file).decode('utf-8')
                structure["worlds"].append({
                    "worldName": world_name,
                    "levelData": content
                })

            elif file.filename.endswith("modoverrides.lua"):
                structure["mods"] = zip_file.read(file).decode('utf-8')

            elif file.filename.endswith("cluster.ini"):
                structure["cluster"] = zip_file.read(file).decode('utf-8')

        return structure

    async def _validate_structure(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """验证存档结构"""
        errors = []

        if not structure["worlds"]:
            errors.append("缺少世界配置文件")

        if len(structure["worlds"]) < 1:
            errors.append("至少需要一个世界配置")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
```

---

### Day 6: 控制台命令和监控

**目标**: 实现控制台命令和系统监控

**任务清单**:
- [x] 实现 `/dst console` 命令
- [x] 实现 `/dst announce` 命令
- [x] 实现系统监控功能
- [x] 集成 apscheduler 定时任务
- [x] 实现异常告警

**代码示例**:

```python
# nonebot_plugin_dst_management/handlers/console.py
dst_console = on_command("dst console", priority=10, block=True)

@dst_console.handle()
async def handle_console(event: MessageEvent, args: Message = CommandArg()):
    if not await check_admin(event):
        await dst_console.finish("❌ 只有管理员才能执行此操作")

    parts = args.extract_plain_text().strip().split()
    if len(parts) < 2:
        await dst_console.finish("❌ 用法：/dst console <房间ID> <命令>")

    room_id = int(parts[0])
    command = " ".join(parts[1:])

    result = await api_client.execute_console_command(
        room_id=room_id,
        world_id=None,
        command=command
    )

    if result.get("code") == 200:
        await dst_console.finish(f"✅ 命令执行成功")
    else:
        await dst_console.finish(f"❌ 执行失败：{result.get('message')}")

# 定时任务示例
from nonebot_plugin_apscheduler import scheduler

@scheduler.scheduled_job("interval", minutes=30)
async def check_server_health():
    """每30分钟检查服务器健康状态"""
    result = await api_client.get_platform_overview()
    # 检查逻辑
    pass
```

---

### Day 7: 测试、优化和文档

**目标**: 完善测试、优化性能、编写文档

**任务清单**:
- [x] 编写单元测试
- [x] 编写集成测试
- [x] 性能优化
- [x] 编写用户文档
- [x] 编写 API 文档
- [x] 准备发布

**测试示例**:

```python
# tests/test_api_client.py
import pytest
from nonebot_plugin_dst_management.client.api_client import DSTApiClient

@pytest.mark.asyncio
async def test_get_room_list():
    client = DSTApiClient(
        base_url="http://test.com",
        token="test_token"
    )

    # Mock HTTP 响应
    # ...

    result = await client.get_room_list(page=1, page_size=10)
    assert result["success"] is True
    assert "data" in result
```

---

## 📊 依赖关系图

```
nonebot-plugin-dst-management
├── nonebot2 (核心框架)
│   ├── nonebot-adapter-onebot (QQ 适配器)
│   └── nonebot-plugin-localstore (数据存储)
├── httpx (HTTP 客户端)
├── pydantic (数据验证)
└── loguru (日志记录)

可选依赖:
├── openai (AI 功能)
├── nonebot-plugin-apscheduler (定时任务)
├── nonebot-plugin-status (状态监控)
└── nonebot-plugin-htmlrender (图表渲染)
```

---

## 🎯 MVP 功能范围

### 必须包含（v0.1.0）
- ✅ 房间列表和详情查看
- ✅ 房间启动/停止
- ✅ 在线玩家查看
- ✅ 基础备份管理
- ✅ 权限控制
- ✅ 错误处理

### 可选包含（v0.2.0）
- ⏳ 存档上传/下载
- ⏳ 模组管理增强
- ⏳ AI 辅助配置
- ⏳ 定时任务
- ⏳ 监控告警

---

## 📈 成功指标

### 功能完整性
- [ ] 所有 MVP 功能可用
- [ ] 命令响应时间 < 2秒
- [ ] 错误处理完善
- [ ] 权限控制有效

### 代码质量
- [ ] 测试覆盖率 > 80%
- [ ] 类型注解完整
- [ ] 文档字符串完整
- [ ] 代码规范检查通过

### 用户体验
- [ ] 命令提示清晰
- [ ] 错误信息友好
- [ ] 帮助文档完整
- [ ] 安装配置简单

---

## 🔧 开发工具推荐

### IDE
- PyCharm Professional
- VS Code + Python 扩展

### 代码质量工具
```bash
# 格式化
pip install black isort

# 代码检查
pip install flake8 mypy

# 测试
pip install pytest pytest-asyncio pytest-cov
```

### 调试工具
```bash
# 日志
pip install loguru

# 性能分析
pip install py-spy
```

---

## 📝 发布检查清单

- [ ] 所有测试通过
- [ ] 文档完整
- [ ] CHANGELOG 更新
- [ ] 版本号更新
- [ ] 标签创建
- [ ] 发布到 PyPI
- [ ] 发布到 NoneBot 插件商店

---

**文档版本**: 1.0.0
**创建时间**: 2026-02-03
**预计完成**: 7天
**维护者**: 小安 (Xiao An)
