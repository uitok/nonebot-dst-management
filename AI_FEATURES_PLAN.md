# 🤖 AI 功能开发计划

**项目**: nonebot-plugin-dst-management
**创建时间**: 2026-02-03 14:00 UTC
**优先级**: 🔴 高

---

## 🎯 AI 功能目标

为 DST 管理插件添加智能辅助功能，提升用户体验和管��效率。

---

## 📋 功能列表

### 1. AI 配置分析 (优先级：🔴 高)

#### 功能描述
使用 AI 分析服务器配置，提供优化建议和性能预测。

#### 命令
```
/dst analyze <房间ID>
```

#### 功能特性
- ✅ 分析服务器配置（世界设置、模组、玩家限制）
- ✅ 检测潜在问题（配置冲突、性能瓶颈）
- ✅ 提供优化建议
- ✅ 预测服务器性能（CPU、内存使用）
- ✅ 生成详细分析报告

#### 返回格式
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

#### 技术实现
```python
# handlers/ai_analyzer.py
from openai import OpenAI
from typing import Dict, Any

class AIAnalyzer:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    async def analyze_server(self, room_id: int) -> Dict[str, Any]:
        """分析服务器配置"""
        # 1. 获取房间信息
        room_info = await api_client.get_room_info(room_id)

        # 2. 获取模组列表
        mods = await api_client.get_room_mods(room_id)

        # 3. 获取玩家统计
        stats = await api_client.get_room_stats(room_id)

        # 4. 构建 AI Prompt
        prompt = self._build_analysis_prompt(room_info, mods, stats)

        # 5. 调用 AI 分析
        response = await self._call_ai(prompt)

        return self._parse_response(response)

    def _build_analysis_prompt(self, room_info, mods, stats) -> str:
        """构建 AI 分析提示词"""
        return f"""
分析以�� DST 服务器配置，提供优化建议：

房间信息：
- 名称: {room_info.get('gameName')}
- 模式: {room_info.get('mode')}
- 玩家限制: {room_info.get('maxPlayers')}
- 季节配置: {room_info.get('seasonConfig')}

模组列表（{len(mods)}个）：
{self._format_mods(mods)}

统计信息：
- 平均在线人数: {stats.get('avgPlayers')}
- 峰值在线: {stats.get('peakPlayers')}
- 服务器运行时间: {stats.get('uptime')}小时

请提供：
1. 配置分析（优点/缺点）
2. 潜在问题检测
3. 优化建议（3-5条）
4. 性能预测（CPU/内存/延迟）
5. 总体评分（1-10分）

使用 Markdown 格式回复。
"""

    async def _call_ai(self, prompt: str) -> str:
        """调用 AI API"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是 DST 服务器配置专家"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI 分析失败：{str(e)}"
```

---

### 2. AI 模组推荐 (优先级：🔴 高)

#### 功能描述
根据服务器当前配置，智能推荐合适的模组。

#### 命令
```
/dst mod recommend <房间ID> [类型]
```

#### 功能特性
- ✅ 分析当前模组配置
- ✅ 推荐兼容的优质模组
- ✅ 检测模组冲突
- ✅ 提供模组评分和理由
- ✅ 支持按类型筛选（装饰/功能/平衡）

#### 返回格式
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

3. [背包扩展] Extra Equip Slots
   📝 模组ID: 5678901234
   ⭐ 评分: 8.5/10
   💡 理由: 提升背包容量，平衡性良好
   📦 安装: /dst mod add 2 Master 5678901234

4. [自动保存] Auto Save
   📝 模组ID: 7890123456
   ⭐ 评分: 8.3/10
   💡 理由: 防止进度丢失，稳定性高
   📦 安装: /dst mod add 2 Master 7890123456

5. [生物群组] Biome Icons
   📝 模组ID: 9012345678
   ⭐ 评分: 8.0/10
   💡 理由: 增强探索体验，轻量级
   📦 安装: /dst mod add 2 Master 9012345678

⚠️ 冲突检测: 无
✅ 所有推荐模组均兼容
```

#### 技术实现
```python
# handlers/ai_recommender.py
class AIModRecommender:
    def __init__(self, api_key: str, api_client: DSTApiClient):
        self.client = OpenAI(api_key=api_key)
        self.api_client = api_client

    async def recommend_mods(
        self,
        room_id: int,
        mod_type: str = None
    ) -> Dict[str, Any]:
        """推荐模组"""
        # 1. 获取当前模组
        current_mods = await self.api_client.get_room_mods(room_id)

        # 2. 获取热门模组列表
        popular_mods = await self.api_client.search_mod("downloads", "", limit=50)

        # 3. 过滤已安装模组
        available_mods = [
            m for m in popular_mods
            if m['id'] not in current_mods
        ]

        # 4. 构建 AI Prompt
        prompt = self._build_recommendation_prompt(
            current_mods,
            available_mods,
            mod_type
        )

        # 5. 调用 AI 推荐
        response = await self._call_ai(prompt)

        return self._parse_recommendations(response)

    def _build_recommendation_prompt(
        self,
        current_mods,
        available_mods,
        mod_type
    ) -> str:
        """构建推荐提示词"""
        type_filter = f"（类型：{mod_type}）" if mod_type else ""

        return f"""
根据以下 DST 服务器配置，推荐5个最合适的模组{type_filter}：

当前模组（{len(current_mods)}个）：
{self._format_mods_summary(current_mods)}

可用模组池（前50个热门模组）：
{self._format_available_mods(available_mods[:20])}

请推荐：
1. 功能性强、评价高的模组
2. 与当前配置完全兼容
3. 适合多人服务器
4. 无已知冲突
5. 按优先级排序

每个推荐包含：
- 模组名称和ID
- 评分（1-10）
- 推荐理由（1-2句话）
- 安装命令示例

使用 Markdown 格式回复。
"""
```

---

### 3. AI 存档分析 (优先级：🟡 中)

#### 功能描述
分析上传的存档文件，检测配置问题和优化空间。

#### 命令
```
/dst archive analyze <文件>
```

#### 功能特性
- ✅ 解析存档结构
- ✅ 检测 Lua 配置错误
- ✅ 分析世界生成设置
- ✅ 评估存档质量
- ✅ 提供修复建议

---

### 4. AI 智能问答 (优先级：🟡 中)

#### 功能描述
基于项目文档和 DST 知识，回答用户问题。

#### 命令
```
/dst ask <问题>
```

#### 功能特性
- ✅ 回答插件使用问题
- ✅ 解答 DST 游戏问题
- ✅ 提供配置帮助
- ✅ 故障排查建议

---

## 🛠️ 技术架构

### AI 服务选择

#### Option 1: OpenAI GPT-4（推荐）
```python
# 优点：
- 智能程度最高
- 理解能力最强
- 中文支持好

# 缺点：
- 需要付费 API
- 延迟较高（2-5秒）

# 适用场景：
- 配置分析
- 智能推荐
- 复杂问答
```

#### Option 2: Anthropic Claude
```python
# 优点：
- 安全性高
- 上下文长
- 性价比高

# 缺点：
- API 访问受限
- 中文支持一般
```

#### Option 3: 本地模型（Ollama）
```python
# 优点：
- 完全免费
- 数据隐私
- 低延迟

# 缺点：
- 需要高性能服务器
- 智能程度较低
- 配置复杂

# 推荐模型：
- llama3.1:8b
- qwen2.5:7b
```

### 配置方式

```python
# config.py
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
```

---

## 📊 开发计划

### Phase 1: 基础框架（2小时）
- [ ] 创建 `ai/` 目录
- [ ] 实现 `ai/base.py` - AI 基类
- [ ] 实现 `ai/config.py` - AI 配置
- [ ] 实现 `ai/client.py` - AI 客户端封装
- [ ] 编写基础测试

### Phase 2: 配置分析（3小时）
- [ ] 实现 `ai/analyzer.py`
- [ ] 实现 `/dst analyze` 命令
- [ ] 实现 Prompt 模板
- [ ] 测试和优化

### Phase 3: 模组推荐（3小时）
- [ ] 实现 `ai/recommender.py`
- [ ] 实现 `/dst mod recommend` 命令
- [ ] 实现推荐算法
- [ ] 测试和优化

### Phase 4: 存档分析（2小时）
- [ ] 实现 `ai/archive_analyzer.py`
- [ ] 实现 `/dst archive analyze` 命令
- [ ] 集成存档服务
- [ ] 测试和优化

### Phase 5: 智能问答（2小时）
- [ ] 实现 `ai/qa.py`
- [ ] 实现 `/dst ask` 命令
- [ ] 构建知识库
- [ ] 测试和优化

### Phase 6: 测试和文档（2小时）
- [ ] 编写单元测试
- [ ] 编写使用文档
- [ ] 性能优化
- [ ] 错误处理完善

**总预计时间**: 14-16 小时

---

## 💡 最佳实践

### Prompt 工程原则

1. **明确性**: 清晰描述任务要求
2. **上下文**: 提供足够的背景信息
3. **格式**: 指定输出格式（Markdown/JSON）
4. **约束**: 设置合理的字数限制
5. **温度**: 0.3-0.7（稳定性 vs 创造性）

### 错误处理

```python
async def safe_ai_call(prompt: str) -> Optional[str]:
    """安全的 AI 调用"""
    try:
        response = await ai_client.call(prompt)
        return response
    except RateLimitError:
        return "⚠️ AI 调用过于频繁，请稍后再试"
    except AuthenticationError:
        return "⚠️ AI API 配置错误"
    except TimeoutError:
        return "⚠️ AI 响应超时"
    except Exception as e:
        logger.error(f"AI 调用失败: {e}")
        return "⚠️ AI 服务暂时不可用"
```

### 缓存策略

```python
from functools import lru_cache
from nonebot_plugin_localstore import get_data_dir

# 缓存 AI 响应（24小时）
@lru_cache(maxsize=100)
async def get_cached_analysis(room_id: int) -> str:
    """获取缓存的分析结果"""
    # 生成缓存键
    cache_key = f"ai_analysis_{room_id}"

    # 尝试从本地存储读取
    cached = get_data_dir().cache.get(cache_key)
    if cached and not is_expired(cached):
        return cached.data

    # 调用 AI
    result = await analyze_server(room_id)

    # 保存缓存
    get_data_dir().cache.set(cache_key, result, ttl=86400)

    return result
```

---

## 📈 性能优化

1. **异步调用**: 使用 asyncio 并发处理
2. **结果缓存**: 缓存常见查询结果
3. **流式响应**: 实时显示 AI 思考过程
4. **降级策略**: AI 不可用时返回模板建议

---

## 🎯 成功指标

- [ ] AI 分析准确率 > 85%
- [ ] 响应时间 < 5秒
- [ ] 用户满意度 > 4.0/5.0
- [ ] 错误率 < 5%

---

**计划版本**: 1.0.0
**创建者**: 小安 (Xiao An)
**预计完成**: 2天
**优先级**: 🔴 高
