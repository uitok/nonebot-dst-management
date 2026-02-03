# 🤖 AI 功能完整开发计划

**项目**: nonebot-plugin-dst-management
**创建时间**: 2026-02-03 14:35 UTC
**优先级**: 🔴 最高
**开发者**: Codex AI
**监督者**: 小安 (Xiao An)

---

## 🎯 总体目标

为 DST 管理插件添加 **5 个 AI 功能**，提升用户体验和管理效率。

---

## 📋 功能清单

### 1. AI 配置分析 🔴
**命令**: `/dst analyze <房间ID>`

**功能**:
- 分析服务器整体配置
- 检测潜在问题和冲突
- 提供优化建议
- 预测性能（CPU/内存/延迟）
- 生成评分报告（1-10分）

**输出示例**:
```
🔍 DST 服务器分析报告

📊 基本信息：
  房间ID: 2
  房间名: "我的生存服务器"
  模式: 生存
  玩家限制: 10人

🧩 模组统计：
  已安装: 15个
  冲突检测: 2个潜在冲突
  建议: 移除或更新过时模组

⚡ 性能预测：
  CPU使用: 中等 (~30-40%)
  内存使用: 中等 (~2-3GB)
  延迟: 良好 (<100ms)

💡 优化建议：
  1. 减少 worldgen_size 可提升生成速度
  2. 增加 max_players 可提升稳定性
  3. 建议启用 autosaver_interval=300

📈 总评分: 7.5/10 (良好)
```

---

### 2. AI 模组推荐 🔴
**命令**: `/dst mod recommend <房间ID> [类型]`

**功能**:
- 分析当前模组配置
- 推荐兼容的优质模组（Top 5）
- 检测模组冲突
- 提供评分和推荐理由
- 生成一键安装命令

**输出示例**:
```
🧩 模组推荐报告

📊 当前配置：
  已安装: 15个模组
  类型分布: 功能(8) 装饰(4) 平衡(3)

🎯 推荐模组（5个）：

1. [健康显示] Health Info
   📝 模组ID: 1234567890
   ⭐ 评分: 9.2/10
   💡 理由: 显示玩家详细信息，与当前配置完美兼容
   📦 安装: /dst mod add 2 Master 1234567890

2. [地图共享] Global Positions
   📝 模组ID: 3456789012
   ⭐ 评分: 8.8/10
   💡 理由: 多人协作必备，无冲突
   📦 安装: /dst mod add 2 Master 3456789012

⚠️ 冲突检测: 无
✅ 所有推荐模组均兼容
```

---

### 3. AI 模组配置解析 🔴🆕
**命令**: `/dst mod parse <房间ID> <世界ID>`

**功能**:
- 解析 `modoverrides.lua` 配置文件
- 检查配置语法错误
- 分析每个模组的配置选项
- 检测配置冲突和无效选项
- 提供配置优化建议
- 生成标准化的配置文件

**输出示例**:
```
📄 模组配置解析报告

🔍 解析结果：
  房间ID: 2
  世界ID: Master (主世界)
  配置文件: modoverrides.lua
  状态: ✅ 有效

📊 配置统计：
  已配置模组: 15个
  总配置项: 47个
  警告: 2个
  错误: 0个

⚠️ 配置警告：

1. [健康栏] Health Info
   📍 选项: configuration_options.health_percent
   ⚠️ 问题: 值超出推荐范围 (150 → 推荐 100)
   💡 建议: 降低到 100 以保持游戏平衡

2. [额外装备] Extra Equip Slots
   📍 选项: configuration_options.equip_slots
   ⚠️ 问题: 可能导致客户端性能下降
   💡 建议: 减少 slots 数量或提示玩家

🔧 配置优化建议：
  1. 将 health_percent 从 150 改为 100
  2. 为所有模组添加明确的配置注释
  3. 使用标准化的配置格式

📋 生成的优化配置：
  [点击查看完整配置文件]

💾 保存命令：
  /dst mod config save 2 Master --optimized
```

**技术细节**:
```python
# ai/mod_config_parser.py
class ModConfigParser:
    """模组配置解析器"""

    async def parse_mod_config(
        self,
        room_id: int,
        world_id: str
    ) -> Dict[str, Any]:
        """解析模组配置"""
        # 1. 获取 modoverrides.lua 内容
        config_content = await self._fetch_modoverrides(room_id, world_id)

        # 2. Lua 语法解析
        parsed = await self._parse_lua(config_content)

        # 3. 构建分析 Prompt
        prompt = self._build_parse_prompt(parsed)

        # 4. AI 分析
        analysis = await self._call_ai(prompt)

        return self._format_analysis(analysis)

    def _build_parse_prompt(self, parsed_config) -> str:
        """构建解析提示词"""
        return f"""
你是 DST 模组配置专家，分析以下 modoverrides.lua 配置：

配置内容：
```lua
{parsed_config}
```

请分析：
1. Lua 语法是否正确
2. 每个模组的配置选项是否有效
3. 检测配置冲突和无效值
4. 提供优化建议（3-5条）
5. 生成优化后的配置文件

输出格式：
- 总体状态（有效/警告/错误）
- 配置统计（模组数、配置项数）
- 警告列表（配置名、问题描述、建议）
- 优化建议（3-5条）
- 优化后的完整配置文件（Lua代码块）

使用 Markdown 格式。
"""
```

---

### 4. AI 存档分析 🟡
**命令**: `/dst archive analyze <文件>`

**功能**:
- 解析存档 ZIP 结构
- 检测 Lua 配置错误
- 分析世界生成设置
- 评估存档质量
- 提供修复建议

**输出示例**:
```
📦 存档分析报告

🔍 解析结果：
  文件名: my_world.zip
  大小: 15.3 MB
  结构: ✅ 有效

📊 存档统计：
  世界数量: 2个 (Master + Caves)
  配置文件: 6个
  模组配置: 已配置
  总评分: 8.5/10

✅ 有效性检查：
  ✓ Master/leveldataoverride.lua - 有效
  ✓ Caves/leveldataoverride.lua - 有效
  ✓ modoverrides.lua - 有效
  ✓ cluster.ini - 有效

⚠️ 潜在问题：
  1. cluster.ini 中 max_players 过高（建议10 → 8）
  2. 缺少 server.ini 配置文件

💡 优化建议：
  1. 降低玩家限制提升稳定性
  2. 添加 server.ini 自定义配置
  3. 启用自动保存（autosaver_interval）

🔧 修复方案：
  [点击查看修复后的配置]
```

---

### 5. AI 智能问答 🟡
**命令**: `/dst ask <问题>`

**功能**:
- 回答插件使用问题
- 解答 DST 游戏问题
- 提供配置帮助
- 故障排查建议

**输出示例**:
```
❓ 问题：如何提升服务器性能？

🤖 AI 回答：

根据你的服务器配置分析，以下是提升性能的建议：

1. **降低世界生成大小**
   - 将 worldgen_size 从 "default" 改为 "small"
   - 可减少 30-40% 的内存使用

2. **优化模组配置**
   - 移除或禁用性能敏感的模组：
     * [Global Positions] - 可改用轻量替代
     * [Health Info] - 降低更新频率

3. **调整服务器参数**
   ```ini
   [NETWORK]
   max_players = 8  # 从 10 降低到 8
   tick_rate = 15   # 从 30 降低到 15

   [MISC]
   console_enabled = true
   autosaver_interval = 300  # 5分钟自动保存
   ```

4. **定期维护**
   - 使用 `/dst backup create` 定期备份
   - 使用 `/dst archive download` 清理旧存档

预期效果：CPU 使用降低 20%，内存使用降低 30%
```

---

## 🛠️ 技术架构

### 文件结构
```
nonebot_plugin_dst_management/
├── ai/                           🆕 AI 模块
│   ├── __init__.py
│   ├── base.py                   # AI 基类
│   ├── config.py                 # AI 配置模型
│   ├── client.py                 # AI 客户端封装
│   ├── analyzer.py               # 配置分析器
│   ├── recommender.py            # 模组推荐器
│   ├── mod_parser.py             # 模组配置解析器 🆕
│   ├── archive_analyzer.py       # 存档分析器
│   └── qa.py                     # 智能问答
├── handlers/
│   ├── ai_analyze.py             # /dst analyze 命令
│   ├── ai_recommend.py           # /dst mod recommend 命令
│   ├── ai_mod_parse.py           # /dst mod parse 命令 🆕
│   ├── ai_archive.py             # /dst archive analyze 命令
│   └── ai_qa.py                  # /dst ask 命令
└── config.py                     # 全局配置（需扩展 AI 配置）
```

### 配置扩展

#### `config.py` 扩展
```python
from pydantic import BaseModel

class AIConfig(BaseModel):
    """AI 功能配置"""
    enabled: bool = False
    provider: str = "openai"  # openai | claude | ollama
    api_key: str = ""
    api_url: str = ""  # for ollama
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    cache_ttl: int = 86400  # 24小时缓存

class Config(BaseModel):
    # ... 现有配置 ...

    # 新增 AI 配置
    ai: AIConfig = AIConfig()
```

#### `.env` 配置
```bash
# AI 功能开关
AI_ENABLED=true

# AI 服务提供商（openai | claude | ollama）
AI_PROVIDER=openai

# OpenAI 配置
AI_API_KEY=sk-xxxxxxxxxxxxx
AI_MODEL=gpt-4o-mini
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000

# Claude 配置（如果使用）
# AI_PROVIDER=claude
# AI_API_KEY=sk-ant-xxxxxxxxxxxxx
# AI_MODEL=claude-3-5-sonnet-20241022

# Ollama 配置（如果使用本地模型）
# AI_PROVIDER=ollama
# AI_API_URL=http://localhost:11434
# AI_MODEL=qwen2.5:7b
```

---

## 📊 开发任务清单

### Phase 1: AI 基础框架（2小时）

#### 任务 1.1: 创建 AI 模块结构
```python
# 创建以下文件：
ai/__init__.py
ai/base.py          # AI 基类
ai/config.py        # AI 配置模型
ai/client.py        # AI 客户端封装（支持 OpenAI/Claude/Ollama）
```

**代码要求**:
- `AIProvider` 基类，定义统一接口
- `OpenAIProvider`, `ClaudeProvider`, `OllamaProvider` 实现
- 异步调用支持
- 统一错误处理
- 自动重试机制（最多3次）

#### 任务 1.2: 扩展全局配置
```python
# 修改文件：
config.py           # 添加 AIConfig 模型
```

**代码要求**:
- 使用 Pydantic 验证配置
- 环境变量加载
- 配置默认值

#### 任务 1.3: 编写基础测试
```python
# 创建文件：
tests/test_ai_base.py
tests/test_ai_client.py
```

**测试要求**:
- Mock AI API 调用
- 测试错误处理
- 测试重试机制

---

### Phase 2: AI 配置分析（3小时）

#### 任务 2.1: 实现分析器
```python
# 创建文件：
ai/analyzer.py      # 服务器配置分析器
```

**功能要求**:
1. `analyze_server(room_id)` 方法
2. 获取房间信息、模组列表、玩家统计
3. 构建 Prompt 模板
4. 解析 AI 响应
5. 生成 Markdown 报告
6. 结果缓存（24小时）

**Prompt 模板要求**:
- 明确的角色定位（DST 服务器专家）
- 清晰的输出格式要求
- 包含评分标准（1-10分）
- 要求提供 3-5 条优化建议

#### 任务 2.2: 实现命令处理器
```python
# 创建文件：
handlers/ai_analyze.py
```

**功能要求**:
1. `/dst analyze <房间ID>` 命令
2. 权限检查（所有用户可用）
3. 参数验证
4. 调用分析器
5. 格式化输出
6. 错误处理

#### 任务 2.3: 测试
```python
# 创建文件：
tests/test_ai_analyzer.py
tests/test_handlers_ai_analyze.py
```

**测试要求**:
- Mock AI API 响应
- 测试报告生成
- 测试缓存功能

---

### Phase 3: AI 模组推荐（3小时）

#### 任务 3.1: 实现推荐器
```python
# 创建文件：
ai/recommender.py   # 模组推荐器
```

**功能要求**:
1. `recommend_mods(room_id, mod_type)` 方法
2. 获取当前模组列表
3. 获取热门模组池（Top 50）
4. 过滤已安装和冲突模组
5. 构建 Prompt 模板
6. 解析 AI 推荐（Top 5）
7. 生成 Markdown 报告
8. 结果缓存（24小时）

**推荐算法要求**:
- 兼容性检查（基于模组标签和类型）
- 评分计算（综合考虑热度、兼容性、功能性）
- 冲突检测（已知冲突列表）
- 按优先级排序

#### 任务 3.2: 实现命令处理器
```python
# 创建文件：
handlers/ai_recommend.py
```

**功能要求**:
1. `/dst mod recommend <房间ID> [类型]` 命令
2. 支持类型筛选（功能/装饰/平衡）
3. 参数验证
4. 调用推荐器
5. 格式化输出（包含一键安装命令）
6. 错误处理

#### 任务 3.3: 测试
```python
# 创建文件：
tests/test_ai_recommender.py
```

**测试要求**:
- Mock AI API 响应
- 测试推荐逻辑
- 测试类型筛选

---

### Phase 4: AI 模组配置解析（4小时）🆕

#### 任务 4.1: 实现解析器
```python
# 创建文件：
ai/mod_parser.py    # 模组配置解析器
```

**功能要求**:
1. `parse_mod_config(room_id, world_id)` 方法
2. 获取 `modoverrides.lua` 内容
3. Lua 语法解析（使用 `lupa` 或正则表达式）
4. 构建详细的 Prompt 模板
5. AI 分析配置：
   - 语法检查
   - 配置选项验证
   - 冲突检测
   - 优化建议
6. 生成优化后的配置文件
7. 生成详细的 Markdown 报告
8. 结果缓存（1小时）

**Lua 解析要求**:
- 识别 `ReturnConfig` 结构
- 提取每个模组的 `configuration_options`
- 检测 Lua 语法错误
- 验证配置选项名称和值类型

**Prompt 模板要求**:
- 包含完整的 Lua 配置内容
- 要求逐个模组分析
- 检测常见配置错误（值超范围、类型错误）
- 提供具体的修复建议
- 生成优化后的完整配置

#### 任务 4.2: 实现命令处理器
```python
# 创建文件：
handlers/ai_mod_parse.py
```

**功能要求**:
1. `/dst mod parse <房间ID> <世界ID>` 命令
2. 支持的世界ID: Master, Caves, Forest, etc.
3. 参数验证
4. 调用解析器
5. 格式化输出（包含配置统计和警告）
6. 支持保存优化后的配置
7. 错误处理

#### 任务 4.3: 实现配置保存功能
```python
# 扩展文件：
handlers/mod.py     # 添加配置保存方法
```

**功能要求**:
1. `/dst mod config save <房间ID> <世界ID> --optimized` 命令
2. 应用 AI 优化后的配置
3. 创建备份
4. 重启服务器
5. 确认提示

#### 任务 4.4: 测试
```python
# 创建文件：
tests/test_ai_mod_parser.py
```

**测试要求**:
- 提供真实的 modoverrides.lua 示例
- Mock AI API 响应
- 测试 Lua 解析
- 测试配置验证
- 测试优化配置生成

---

### Phase 5: AI 存档分析（2小时）

#### 任务 5.1: 实现存档分析器
```python
# 创建文件：
ai/archive_analyzer.py
```

**功能要求**:
1. `analyze_archive(archive_data)` 方法
2. 解析 ZIP 文件结构
3. 提取所有 `.lua` 和 `.ini` 配置文件
4. 构建分析 Prompt
5. AI 分析存档质量
6. 生成报告

#### 任务 5.2: 实现命令处理器
```python
# 创建文件：
handlers/ai_archive.py
```

**功能要求**:
1. `/dst archive analyze <文件>` 命令
2. 支持文件上传或 URL
3. 调用分析器
4. 格式化输出

---

### Phase 6: AI 智能问答（2小时）

#### 任务 6.1: 实现问答系统
```python
# 创建文件：
ai/qa.py            # 智能问答
```

**功能要求**:
1. `ask(question, context)` 方法
2. 构建知识库上下文（项目文档 + DST 知识）
3. 构建问答 Prompt
4. AI 生成回答
5. 引用来源

#### 任务 6.2: 实现命令处理器
```python
# 创建文件：
handlers/ai_qa.py
```

**功能要求**:
1. `/dst ask <问题>` 命令
2. 支持多轮对话（可选）
3. 格式化输出

---

### Phase 7: 集成测试和优化（2小时）

#### 任务 7.1: 集成测试
```python
# 创建文件：
tests/test_ai_integration.py
```

**测试要求**:
- 端到端测试所有 AI 功能
- 测试真实 AI API 调用
- 性能测试（响应时间 < 5秒）

#### 任务 7.2: 文档更新
```markdown
# 更新文件：
README.md                      # 添加 AI 功能说明
docs/AI_FEATURES.md            # AI 功能详细文档
COMMANDS_COMPLETE.md           # 添加 AI 命令
```

#### 任务 7.3: 性能优化
- 实现响应缓存
- 优化 Prompt 长度
- 添加流式响应（可选）

---

## 🎯 成功标准

### 功能完整性
- [ ] 所有 5 个 AI 功能实现
- [ ] 所有命令正常工作
- [ ] 支持 3 种 AI 提供商（OpenAI/Claude/Ollama）
- [ ] 完善的错误处理

### 代码质量
- [ ] 测试覆盖率 > 80%
- [ ] 所有测试通过
- [ ] 代码符合规范（black/isort/mypy）
- [ ] 完整的类型注解

### 性能要求
- [ ] AI 响应时间 < 5秒（90% 请求）
- [ ] 缓存命中率 > 50%
- [ ] 错误率 < 5%

### 文档完整
- [ ] README 更新
- [ ] AI 功能文档完整
- [ ] 命令参考更新
- [ ] 配置说明清晰

---

## 📋 开发建议

### Prompt 工程最佳实践

1. **明确的角色定位**
   ```
   "你是 DST 服务器配置专家，拥有丰富的服务器管理经验。"
   ```

2. **清晰的输出格式**
   ```
   "请使用以下 Markdown 格式输出：
   ## 总体状态
   ## 详细分析
   ## 优化建议
   "
   ```

3. **具体的评分标准**
   ```
   "请从以下维度评分（1-10分）：
   - 配置合理性
   - 性能表现
   - 稳定性
   - 用户体验
   "
   ```

4. **上下文信息**
   ```
   "当前服务器配置：
   - 房间名：xxx
   - 模组数：15个
   - 玩家限制：10人
   "
   ```

### 错误处理

```python
# 统一的错误处理装饰器
def handle_ai_errors(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except RateLimitError:
            return "⚠️ AI 调用过于频繁，请稍后再试"
        except AuthenticationError:
            return "⚠️ AI API 配置错误，请检查 API Key"
        except TimeoutError:
            return "⚠️ AI 响应超时，请重试"
        except Exception as e:
            logger.error(f"AI 调用失败: {e}")
            return "⚠️ AI 服务暂时不可用"
    return wrapper
```

### 缓存策略

```python
from functools import lru_cache
from datetime import datetime, timedelta

# 使用 LRU 缓存
@lru_cache(maxsize=100)
async def get_cached_analysis(room_id: int) -> str:
    """获取缓存的分析结果"""
    cache_key = f"ai_analysis_{room_id}_{datetime.now().date()}"
    # ... 缓存逻辑
```

---

## 🚀 交付清单

### 代码文件
- [ ] `ai/` 目录（8个文件）
- [ ] `handlers/ai_*.py`（5个文件）
- [ ] `config.py` 扩展
- [ ] `tests/test_ai_*.py`（7个文件）

### 文档文件
- [ ] `docs/AI_FEATURES.md`
- [ ] `README.md` 更新
- [ ] `COMMANDS_COMPLETE.md` 更新
- [ ] `.env.example` 更新

### 测试报告
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 性能测试报告

---

**计划版本**: 2.0.0 (完整版)
**创建者**: 小安 (Xiao An)
**开发者**: Codex AI
**预计完成**: 2-3天（14-18小时）
**优先级**: 🔴 最高
**状态**: 🟡 准备就绪，等待分配给 Codex

---

## 📞 联系方式

**监督者**: 小安 (Xiao An)
**开发者**: Codex AI
**项目**: nonebot-plugin-dst-management

**下一步**: 将此计划提交给 Codex，开始开发！🚀
