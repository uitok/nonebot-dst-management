# 🤖 AI 功能完整开发计划

**项目**: nonebot-plugin-dst-management
**创建时间**: 2026-02-03 14:25 UTC
**优先级**: 🔴 高
**开发者**: Codex AI
**监督者**: 小安 (Xiao An)

---

## 🎯 总体目标

为 DST 管理插件添加 **5 个 AI 功能**，提升用户体验和管理效率。

---

## 📋 AI 功能清单

### 1. 🔍 AI 配置分析 (优先级：🔴 最高)

#### 命��
```
/dst analyze <房间ID>
```

#### 功能特性
- ✅ 分析服务器完整配置
- ✅ 检测潜在问题（配置冲突、性能瓶颈、安全风险）
- ✅ 提供优化建议（3-5条）
- ✅ 预测服务器性能（CPU、内存、延迟）
- ✅ 生成详细分析报告（Markdown 格式）
- ✅ 给出总体评分（1-10分）

#### 返回格式示例
```
🔍 DST 服务器分析报告

📊 基本信息：
  房间ID: 2
  房间名: "我的生存服务器"
  模式: 生存
  玩家限制: 10人
  季节: 秋季 (第5天)

🧩 模组统计：
  已安装: 15个
  类型分布: 功能(8) 装饰(4) 平衡(3)
  冲突检测: ⚠️ 发现2个潜在冲突
    • "健康显示" 与 "血量显示" 功能重复
    • "地图全开" 可能影响性能

⚡ 性能预测：
  CPU使用: 中等 (~30-40%)
  内存使用: 中等 (~2-3GB)
  延迟: 良好 (<100ms)
  稳定性: 7.5/10

💡 优化建议：
  1. 🔧 减少 worldgen_size 从 "default" 改为 "small"
     → 可提升世界生成速度 20-30%

  2. 🔧 启用 autosaver_interval=300
     → 每5分钟自动保存，防止进度丢失

  3. 🗑️ 移除重复模组 "血量显示"
     → 减少冲突，提升稳定性

  4. ⚡ 调整 tick_rate 从 15 改为 30
     → 提升服务器响应速度

  5. 👥 增加 max_players 从 10 改为 12
     → 提升多人游戏稳定性

📈 总评分: 7.5/10 (良好)
🎯 改进空间: 中等
```

#### 技术要求
```python
# 需要创建的文件：
ai/__init__.py
ai/base.py              # AI 基类
ai/config.py            # AI 配置模型
ai/analyzer.py          # 配置分析器
handlers/ai_analyze.py  # 命令处理器

# 核心功能：
class AIAnalyzer:
    async def analyze_server(self, room_id: int) -> str:
        """分析服务器配置，返回 Markdown 报告"""

    def _build_prompt(self, room_info, mods, stats) -> str:
        """构建 AI 分析提示词"""

    async def _call_ai(self, prompt: str) -> str:
        """调用 AI API（支持 OpenAI/Claude/Ollama）"""

    def _parse_response(self, response: str) -> str:
        """解析 AI 返回结果"""
```

---

### 2. 🧩 AI 模组推荐 (优先级：🔴 最高)

#### 命令
```
/dst mod recommend <房间ID> [类型]
```

**类型可选**: `装饰` | `功能` | `平衡` | `综合`

#### 功能特性
- ✅ 分析当前模组配置
- ✅ 推荐兼容的优质模组（Top 5）
- ✅ 检测模组冲突
- ✅ 提供模组评分和推荐理由
- ✅ 生成一键安装命令
- ✅ 支持按类型筛选

#### 返回格式示例
```
🧩 模组推荐报告

📊 当前配置：
  已安装: 15个模组
  类型分布: 功能(8) 装饰(4) 平衡(3)
  空闲槽位: 充足

🎯 推荐模组（5个）：

1. ⭐ [健康显示] Health Info (9.2/10)
   📝 模组ID: 1234567890
   💡 理由: 显示玩家详细信息（血量、饥饿、精神），
            与当前配置完美兼容，必备工具
   🔗 下载: 50万+
   📦 安装: /dst mod add 2 Master 1234567890

2. ⭐ [地图共享] Global Positions (8.8/10)
   📝 模组ID: 3456789012
   💡 理由: 多人协作必备，实时显示玩家位置，
            无冲突，稳定性高
   🔗 下载: 80万+
   📦 安装: /dst mod add 2 Master 3456789012

3. ⭐ [背包扩展] Extra Equip Slots (8.5/10)
   📝 模组ID: 5678901234
   💡 理由: 提升背包容量（+8个装备槽），
            平衡性良好，不影响游戏难度
   🔗 下载: 30万+
   📦 安装: /dst mod add 2 Master 5678901234

4. ⭐ [自动保存] Auto Save (8.3/10)
   📝 模组ID: 7890123456
   💡 理由: 防止进度丢失，定时自动保存，
            服务器稳定性提升
   🔗 下载: 40万+
   📦 安装: /dst mod add 2 Master 7890123456

5. ⭐ [生物群组] Biome Icons (8.0/10)
   📝 模组ID: 9012345678
   💡 理由: 增强探索体验，显示生物群组图标，
            轻量级，性能影响小
   🔗 下载: 20万+
   📦 安装: /dst mod add 2 Master 9012345678

⚠️ 冲突检测: 无
✅ 所有推荐模组均兼容

💡 提示: 回复序号(1-5)可快速安装对应模组
```

#### 技术要求
```python
# 需要创建的文件：
ai/recommender.py        # 模组推荐器
handlers/ai_mod.py       # 命令处理器

# 核心功能：
class AIModRecommender:
    async def recommend_mods(
        self,
        room_id: int,
        mod_type: str = None
    ) -> str:
        """推荐模组，返回 Markdown 报告"""

    def _build_prompt(self, current_mods, available_mods, mod_type) -> str:
        """构建推荐提示词"""

    def _filter_by_type(self, mods, mod_type) -> list:
        """按类型筛选模组"""

    def _check_conflicts(self, recommended, current) -> list:
        """检测模组冲突"""
```

---

### 3. 📝 AI 模组配置解析 (优先级：🔴 最高) 🆕

#### 命令
```
/dst mod parse <房间ID>
/dst mod parse <房间ID> <世界ID>
```

#### 功能特性
- ✅ 解析 `modoverrides.lua` 配置文件
- ✅ 检测配置语法错误
- ✅ 分析模组选项设置
- ✅ 检测配置冲突
- ✅ 提供修复建议
- ✅ 生成标准配置模板
- ✅ 支持配置验证和优化

#### 返回格式示例
```
📝 模组配置解析报告

📄 文件信息：
  房间ID: 2
  世界ID: Master (主世界)
  配置文件: modoverrides.lua
  文件大小: 2.3 KB
  最后修改: 2026-02-03 10:30

🔍 语法检测：
  ✅ Lua 语法正确
  ✅ 括号匹配正确
  ✅ 引号使用正确
  ✅ 逗号分隔正确

📊 配置统计：
  已配置模组: 12个
  未配置模组: 3个
  自定义选项: 8个
  默认选项: 4个

🧩 模组配置详情：

1. [健康显示] Health Info (1234567890)
   ✅ 配置正常
   📋 选项: show_health = true, show_hunger = true
   💡 建议: 可启用 show_sanity = true

2. [地图全开] Global Map (3456789012)
   ⚠️ 性能警告
   📋 选项: reveal_all = true
   💡 建议: 改为 reveal_map_only = true
            → 可提升性能 15-20%

3. ⚠️ [未知模组] Unknown Mod (9999999999)
   ❌ 配置错误
   🔴 问题: 模组ID无效或未安装
   💡 修复: /dst mod remove 2 Master 9999999999

4. [背包扩展] Extra Slots (5678901234)
   ✅ 配置正常
   📋 选项: slot_count = 8
   💡 建议: 可增加到 slot_count = 12

⚠️ 发现问题（3个）：

1. 🔴 高危: 模组 9999999999 未安装
   → 修复命令: /dst mod remove 2 Master 9999999999

2. 🟡 中危: 地图全开可能影响性能
   → 修复建议: 启用 reveal_map_only 选项

3. 🟢 低危: 3个模组使用默认配置
   → 优化建议: 根据需求自定义配置

🔧 自动修复：
  /dst mod fix 2 Master

  将执行：
  • 移除无效模组ID
  • 优化性能相关配置
  • 应用推荐设置

📋 标准配置模板：
  运行 /dst mod template 2 Master
  生成标准 modoverrides.lua
```

#### 技术要求
```python
# 需要创建的文件：
ai/mod_parser.py         # 模组配置解析器
handlers/ai_mod_parse.py # 命令处理器

# 核心功能：
class AIModParser:
    async def parse_mod_config(
        self,
        room_id: int,
        world_id: str = None
    ) -> str:
        """解析模组配置，返回 Markdown 报告"""

    async def fix_mod_config(
        self,
        room_id: int,
        world_id: str
    ) -> str:
        """自动修复配置问题"""

    def _parse_lua(self, lua_content: str) -> dict:
        """解析 Lua 配置文件"""

    def _validate_syntax(self, lua_content: str) -> list:
        """验证 Lua 语法"""

    def _detect_issues(self, config, installed_mods) -> list:
        """检测配置问题"""

    def _generate_template(self, mods) -> str:
        """生成标准配置模板"""
```

---

### 4. 📦 AI 存档分析 (优先级：🟡 中)

#### 命令
```
/dst archive analyze <文件>
```

#### 功能特性
- ✅ 解析 ZIP 存档结构
- ✅ 检测 Lua 配置语法错误
- ✅ 分析世界生成设置
- ✅ 评估存档质量和完整性
- ✅ 提供修复和优化建议
- ✅ 预测兼容性问题

#### 返回格式示例
```
📦 存档分析报告

📄 文件信息：
  文件名: MyServer.zip
  文件大小: 15.6 MB
  上传时间: 2026-02-03 14:00

🔍 结构检测：
  ✅ ZIP 格式正确
  ✅ 包含 Master 世界
  ✅ 包含 Caves 世界
  ✅ cluster.ini 完整
  ✅ modoverrides.lua 存在

📊 存档统计：
  世界数量: 2个 (Master + Caves)
  总文件数: 156个
  存档天数: 45天
  季节: 冬季 (第10天)

⚠️ 发现问题（2个）：

1. 🟡 Master 世界配置问题
   📄 文件: Master/leveldataoverride.lua
   🔴 问题: worldgen_size 设置为 "huge"
   💡 影响: 世界生成时间过长（预计10-15分钟）
   🔧 建议: 改为 "medium" 或 "small"

2. 🟢 模组配置缺失
   📄 文件: Caves/modoverrides.lua
   🔴 问题: 文件为空或不存在
   💡 影响: 地下世界模组无法加载
   🔧 修复: 从 Master 复制配置

📈 质量评估：
  完整性: 8.5/10
  配置质量: 7.0/10
  兼容性: 9.0/10
  总评分: 8.2/10

💡 优化建议：
  1. 调整 worldgen_size 提升性能
  2. 补充 Caves 模组配置
  3. 启用自动保存功能

🚀 可以安全上传
```

#### 技术要求
```python
# 需要创建的文件：
ai/archive_analyzer.py   # 存档分析器
handlers/ai_archive.py   # 命令处理器

# 核心功能：
class AIArchiveAnalyzer:
    async def analyze_archive(self, archive_data: bytes) -> str:
        """分析存档，返回 Markdown 报告"""

    def _parse_zip(self, archive_data: bytes) -> dict:
        """解析 ZIP 存档"""

    def _validate_lua(self, lua_content: str) -> list:
        """验证 Lua 配置"""

    def _evaluate_quality(self, structure) -> dict:
        """评估存档质量"""
```

---

### 5. 💬 AI 智能问答 (优先级：🟡 中)

#### 命令
```
/dst ask <问题>
```

#### 功能特性
- ✅ 回答插件使用问题
- ✅ 解答 DST 游戏问题
- ✅ 提供配置帮助
- ✅ 故障排查建议
- ✅ 支持多轮对话
- ✅ 上下文理解

#### 返回格式示例
```
💬 智能助手

📝 问题: 如何设置服务器自动保存？

🤖 回答：

在 DST 服务器中设置自动保存，有以下几种方法：

方法1: 使用控制台命令（推荐）
  /dst console 2 "c_setAUTOSAVER(true)"
  /dst console 2 "c_setautosaveinterval(300)"

  → 每5分钟自动保存一次

方法2: 修改 cluster.ini 配置
  [MISC]
  CONSOLE_ENABLED = true
  AUTOSAVER_ENABLED = true
  AUTOSAVER_INTERVAL = 300

方法3: 使用本插件命令
  /dst console 2 "c_setAUTOSAVER(true)"

💡 提示:
  • 间隔单位是秒，300 = 5分钟
  • 建议设置 300-600 秒
  • 自动保存会轻微影响性��

📚 相关命令:
  /dst analyze 2 - 查看完整配置分析
  /dst console 2 <命令> - 执行其他命令

还有其他问题吗？😊
```

#### 技术要求
```python
# 需要创建的文件：
ai/qa.py                # 智能问答
handlers/ai_ask.py      # 命令处理器

# 核心功能：
class AIQA:
    async def ask_question(self, question: str, context: dict = None) -> str:
        """回答问题，返回 Markdown 格式"""

    def _build_context(self, question: str) -> str:
        """构建知识库上下文"""

    def _search_docs(self, question: str) -> list:
        """搜索项目文档"""
```

---

## 🛠️ 技术架构

### AI 服务配置

#### 配置文件
```python
# ai/config.py
from pydantic import BaseModel

class AIConfig(BaseModel):
    """AI 配置"""
    enabled: bool = False
    provider: str = "openai"  # openai | claude | ollama
    api_key: str = ""
    api_url: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30

# .env
AI_ENABLED=true
AI_PROVIDER=openai
AI_API_KEY=sk-xxxxxx
AI_MODEL=gpt-4o-mini
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000
```

### AI 客户端封装

```python
# ai/base.py
from abc import ABC, abstractmethod
from typing import Optional

class AIClient(ABC):
    """AI 客户端基类"""

    @abstractmethod
    async def chat(self, prompt: str, **kwargs) -> str:
        """调用 AI 聊天接口"""
        pass

class OpenAIClient(AIClient):
    """OpenAI 客户端"""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def chat(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2000)
        )
        return response.choices[0].message.content

class ClaudeClient(AIClient):
    """Claude 客户端"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet"):
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def chat(self, prompt: str, **kwargs) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2000),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

class OllamaClient(AIClient):
    """Ollama 本地模型客户端"""

    def __init__(self, model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434"):
        import httpx
        self.client = httpx.AsyncClient(base_url=base_url)
        self.model = model

    async def chat(self, prompt: str, **kwargs) -> str:
        response = await self.client.post("/api/generate", json={
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })
        return response.json()["response"]
```

### 缓存机制

```python
# ai/cache.py
from functools import lru_cache
from typing import Optional
import hashlib
import json

class AICache:
    """AI 响应缓存"""

    def __init__(self, ttl: int = 86400):
        self.ttl = ttl
        self.cache = {}

    def get_key(self, prompt: str) -> str:
        """生成缓存键"""
        return hashlib.md5(prompt.encode()).hexdigest()

    async def get(self, prompt: str) -> Optional[str]:
        """获取缓存"""
        key = self.get_key(prompt)
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
        return None

    async def set(self, prompt: str, response: str):
        """设置缓存"""
        key = self.get_key(prompt)
        self.cache[key] = (response, time.time())
```

---

## 📊 开发计划（分阶段）

### Phase 1: 基础框架（2小时）🔴

**任务清单**:
- [ ] 创建 `ai/` 目录结构
- [ ] 实现 `ai/__init__.py`
- [ ] 实现 `ai/config.py` - AI 配置模型
- [ ] 实现 `ai/base.py` - AI 客户端基类
- [ ] 实现 `ai/cache.py` - 缓存机制
- [ ] 更新 `config.py` 添加 AI 配置
- [ ] 更新 `.env.example` 添加 AI 环境变量

**验收标准**:
- ✅ AI 基类可以正常初始化
- ✅ 支持 OpenAI/Claude/Ollama 三种客户端
- ✅ 配置可以通过环境变量加载

---

### Phase 2: AI 配置分析（3小时）🔴

**任务清单**:
- [ ] 实现 `ai/analyzer.py`
  - [ ] `analyze_server()` - 主分析方法
  - [ ] `_build_prompt()` - 构建 Prompt
  - [ ] `_call_ai()` - 调用 AI
  - [ ] `_parse_response()` - 解析响应
- [ ] 实现 `handlers/ai_analyze.py`
  - [ ] 命令注册
  - [ ] 参数解析
  - [ ] 权限检查
  - [ ] 错误处理
- [ ] 编写测试 `tests/test_ai_analyzer.py`
- [ ] 编写使用文档

**验收标准**:
- ✅ `/dst analyze <房间ID>` 命令可用
- ✅ 生成完整的 Markdown 报告
- ✅ 包含评分和建议
- ✅ 响应时间 < 10秒

---

### Phase 3: AI 模组推荐（3小时）🔴

**任务清单**:
- [ ] 实现 `ai/recommender.py`
  - [ ] `recommend_mods()` - 主推荐方法
  - [ ] `_build_prompt()` - 构建 Prompt
  - [ ] `_filter_by_type()` - 类型筛选
  - [ ] `_check_conflicts()` - 冲突检测
- [ ] 实现 `handlers/ai_mod.py`
  - [ ] 命令注册
  - [ ] 类型筛选支持
  - [ ] 一键安装功能
- [ ] 编写测试 `tests/test_ai_recommender.py`
- [ ] 编写使用文档

**验收标准**:
- ✅ `/dst mod recommend <房间ID>` 命令可用
- ✅ 推荐结果准确（兼容性高）
- ✅ 支持类型筛选
- ✅ 提供一键安装命令

---

### Phase 4: AI 模组配置解析（3小时）🔴 🆕

**任务清单**:
- [ ] 实现 `ai/mod_parser.py`
  - [ ] `parse_mod_config()` - 主解析方法
  - [ ] `_parse_lua()` - 解析 Lua 配置
  - [ ] `_validate_syntax()` - 语法验证
  - [ ] `_detect_issues()` - 问题检测
  - [ ] `fix_mod_config()` - 自动修复
  - [ ] `_generate_template()` - 生成模板
- [ ] 实现 `handlers/ai_mod_parse.py`
  - [ ] 命令注册
  - [ ] 世界ID参数支持
  - [ ] 自动修复命令
  - [ ] 模板生成命令
- [ ] 编写测试 `tests/test_ai_mod_parser.py`
- [ ] 编写使用文档

**验收标准**:
- ✅ `/dst mod parse <房间ID>` 命令可用
- ✅ 准确检测 Lua 语法错误
- ✅ 提供有效的修复建议
- ✅ 支持自动修复功能
- ✅ 生成标准配置模板

---

### Phase 5: AI 存档分析（2小时）🟡

**任务清单**:
- [ ] 实现 `ai/archive_analyzer.py`
  - [ ] `analyze_archive()` - 主分析方法
  - [ ] `_parse_zip()` - 解析 ZIP
  - [ ] `_validate_lua()` - 验证 Lua
  - [ ] `_evaluate_quality()` - 质量评估
- [ ] 实现 `handlers/ai_archive.py`
- [ ] 编写测试
- [ ] 编写使用文档

**验收标准**:
- ✅ `/dst archive analyze <文件>` 命令可用
- ✅ 准确解析存档结构
- ✅ 检测配置问题
- ✅ 提供优化建议

---

### Phase 6: AI 智能问答（2小时）🟡

**任务清单**:
- [ ] 实现 `ai/qa.py`
  - [ ] `ask_question()` - 主问答方法
  - [ ] `_build_context()` - 构建上下文
  - [ ] `_search_docs()` - 搜索文档
- [ ] 实现 `handlers/ai_ask.py`
- [ ] 构建知识库（项目文档 + DST 知识）
- [ ] 编写测试
- [ ] 编写使用文档

**验收标准**:
- ✅ `/dst ask <问题>` 命令可用
- ✅ 回答准确率高（>80%）
- ✅ 支持多轮对话

---

### Phase 7: 测试和文档（3小时）🟡

**任务清单**:
- [ ] 补全所有 AI 功能的单元测试
- [ ] 编写集成测试
- [ ] 测试覆盖率 > 80%
- [ ] 编写用户文档 `docs/AI_GUIDE.md`
- [ ] 编写 API 文档 `docs/AI_API.md`
- [ ] 更新 README.md 添加 AI 功能说明
- [ ] 更新 CHANGELOG.md

---

## 📋 给 Codex 的开发指令

### 任务分配

#### 第一个任务：基础框架 + 配置分析
```
你好 Codex，请帮我开发 DST 管理插件的 AI 功能。

第一部分：基础框架
1. 创建 ai/ 目录
2. 实现 ai/config.py - AI 配置模型（使用 Pydantic）
3. 实现 ai/base.py - AI 客户端基类
   - 支持 OpenAI (gpt-4o-mini)
   - 支持 Claude (claude-3-5-sonnet)
   - 支持 Ollama (qwen2.5:7b)
4. 实现 ai/cache.py - 缓存机制（LRU，24小时TTL）

第二部分：AI 配置分析
1. 实现 ai/analyzer.py
   - analyze_server(room_id) 方法
   - 分析房间信息、模组、玩家统计
   - 生成详细的 Markdown 报告
   - 包含：基本信息、问题检测、优化建议、性能预测、总评分
2. 实现 handlers/ai_analyze.py
   - /dst analyze <房间ID> 命令
   - 权限检查（所有用户可用）
   - 错误处理完善

要求：
- 使用异步编程
- 完整的类型注解
- 详细的错误处理
- AI 响应时间 < 10秒
- 缓存常见查询（24小时）

请创建完整的、可运行的代码，包含所有必要的导入和配置。
```

#### 第二个任务：模组推荐
```
第二个任务：AI 模组推荐

1. 实现 ai/recommender.py
   - recommend_mods(room_id, mod_type) 方法
   - 分析当前模组配置
   - 从热门模组池推荐 Top 5
   - 检测模组冲突
   - 提供评分和推荐理由
   - 生成一键安装命令

2. 实现 handlers/ai_mod.py
   - /dst mod recommend <房间ID> [类型] 命令
   - 支持类型筛选：装饰、功能、平衡、综合
   - 格式化输出 Markdown 报告

要求：
- 推荐结果准确（兼容性高）
- 评分合理（7-10分）
- 推荐理由具体（1-2句话）
- 检测已知冲突
```

#### 第三个任务：模组配置解析 🆕
```
第三个任务：AI 模组配置解析

1. 实现 ai/mod_parser.py
   - parse_mod_config(room_id, world_id) 方法
   - 解析 modoverrides.lua 配置
   - 验证 Lua 语法
   - 检测配置问题（语法错误、无效模组ID、性能问题）
   - 提供修复建议
   - 支持自动修复
   - 生成标准配置模板

2. 实现 handlers/ai_mod_parse.py
   - /dst mod parse <房间ID> [世界ID] 命令
   - /dst mod fix <房间ID> <世界ID> 命令
   - /dst mod template <房间ID> <世界ID> 命令

要求：
- 准确解析 Lua 配置
- 检测常见配置错误
- 提供有效的修复方案
- 生成的模板可直接使用
```

---

## 🎯 成功指标

- [ ] 所有 AI 命令可用（5个功能，10个命令）
- [ ] AI 响应准确率 > 85%
- [ ] AI 响应时间 < 10秒
- [ ] 用户满意度 > 4.0/5.0
- [ ] 错误率 < 5%
- [ ] 测试覆盖率 > 80%

---

## 📝 总结

主人，这是**完整的 AI 功能开发计划**，包含：

### ✅ 5 个 AI 功能
1. 🔍 AI 配置分析 - `/dst analyze`
2. 🧩 AI 模组推荐 - `/dst mod recommend`
3. 📝 AI 模组配置解析 - `/dst mod parse` 🆕
4. 📦 AI 存档分析 - `/dst archive analyze`
5. 💬 AI 智能问答 - `/dst ask`

### ✅ 完整技术架构
- AI 客户端封装（OpenAI/Claude/Ollama）
- 缓存机制（LRU，24小时TTL）
- 错误处理
- 异步编程

### ✅ 分阶段开发计划
- Phase 1: 基础框架（2小时）
- Phase 2: 配置分析（3小时）
- Phase 3: 模组推荐（3小时）
- Phase 4: 模组配置解析（3小时）🆕
- Phase 5: 存档分析（2小时）
- Phase 6: 智能问答（2小时）
- Phase 7: 测试文档（3小时）

**总预计时间**: 18 小时

**需要我现在就把这个计划交给 Codex 开始开发吗？** 😊

或者你想先看看某个部分的更详细设计？