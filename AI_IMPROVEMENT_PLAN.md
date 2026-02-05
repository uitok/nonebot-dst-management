# AI 解析功能增强计划

## 目标

将 AI 模组/存档解析功能从"自动优化"改为"诊断 + 建议 + 用户确认"模式。

---

## 当前问题

### 现有流程
```
用户 → /dst mod parse <房间ID> <世界ID>
  ↓
AI 分析配置
  ↓
返回：优化后的完整配置 + 警告
  ↓
用户需要手动复制配置到服务器
```

### 用户需求
```
用户 → /dst mod parse <房间ID> <世界ID>
  ↓
AI 分析配置
  ↓
返回：
  1. 当前配置有什么问题
  2. 建议如何调整（分条列出）
  3. 为什么这样调整
  ↓
用户：/dst mod config apply <房间ID> <世界ID> --auto
  ↓
应用 AI 建议的配置
```

---

## 增强方案

### 1. 诊断报告格式

#### 当前格式
```
📄 模组配置解析报告

🔍 解析结果：
- 状态：✅ 有效
- 已配置模组：21 个
- 总配置项：156 个

📋 优化后的配置：
```lua
return {
  ["workshop-1185229307"] = {
    enabled = true,
    configuration_options = {
      ...
    },
  },
  ...
}
```
```

#### 增强后格式
```
📄 模组配置诊断报告

🔍 配置概览：
- 状态：⚠️ 有 3 个问题需要关注
- 已配置模组：21 个
- 总配置项：156 个

❌ 发现的问题：

1. 【健康显示栏模组】配置缺失
   - 模组ID：workshop-1185229307
   - 问题：缺少关键配置项 "show_max"（显示最大血量）
   - 影响：游戏内可能无法正确显示血量上限
   - 💡 建议：添加配置 `show_max = true`

2. 【自动存档模组】间隔时间过短
   - 模组ID：workshop-375850593
   - 问题："autosave_interval" 设置为 30 秒
   - 影响：频繁存档可能导致服务器卡顿
   - 💡 建议：调整配置 `autosave_interval = 300`（5分钟）

3. 【更多槽位模组】与服务器配置冲突
   - 模组ID：workshop-378160973
   - 问题：max_players 设置为 20，但服务器限制 6 人
   - 影响：玩家可能无法正常加入
   - 💡 建议：调整配置 `max_players = 6`

✅ 优化建议摘要：

1. 【必须修复】
   - 添加缺失配置项（2 处）
   - 调整冲突配置（1 处）

2. 【建议优化】
   - 调整自动存档间隔
   - 优化性能相关配置

3. 【可选增强】
   - 启用调试日志（排查问题时使用）

---

📋 查看完整优化后的配置：
/dst mod config show <房间ID> <世界ID>

🚀 应用 AI 建议的配置：
/dst mod config apply <房间ID> <世界ID> --auto

💡 使用 --dry-run 预览将要应用的更改：
/dst mod config apply <房间ID> <世界ID> --dry-run
```

---

## 新增命令

### 1. `/dst mod config show <房间ID> <世界ID>`
显示完整的优化后配置（当前功能）

### 2. `/dst mod config apply <房间ID> <世界ID> [--auto] [--dry-run]`
应用 AI 建议的配置

**参数：**
- `--auto`：自动应用所有建议
- `--dry-run`：只预览，不实际修改

**交互式确认流程（无 --auto）：**
```
用户：/dst mod config apply 2 1

Bot：检测到 3 处需要调整的配置：

1. [workshop-1185229307] 健康显示栏
   添加：show_max = true

2. [workshop-375850593] 自动存档
   调整：autosave_interval = 30 → 300

3. [workshop-378160973] 更多槽位
   调整：max_players = 20 → 6

是否应用这些更改？
回复 "是" 确认，"否" 取消，"跳过 1" 跳过第 1 项

用户：跳过 1

Bot：已跳过第 1 项。剩余 2 项：
1. [workshop-375850593] 自动存档
   调整：autosave_interval = 30 → 300

2. [workshop-378160973] 更多槽位
   调整：max_players = 20 → 6

是否应用这 2 项更改？
回复 "是" 确认，"否" 取消

用户：是

Bot：✅ 配置已更新！
- 修改了 2 个模组配置
- 跳过了 1 项建议
```

---

## AI Prompt 改进

### 当前 Prompt
```
你是 DST 模组配置专家，请分析以下 modoverrides.lua 配置并输出优化报告。

要求：
1. 输出 JSON，包含 status, warnings, suggestions, optimized_config。
2. status 为 valid/warn/error。
3. warnings 为数组，每项包含 mod_id, issue, suggestion。
4. optimized_config 为完整 Lua 配置文本。
```

### 增强后 Prompt
```
你是 DST 模组配置诊断专家，请分析以下 modoverrides.lua 配置并给出详细的诊断报告。

输入数据包含：
- room_id: 房间ID
- world_id: 世界ID
- mods: 模组列表（含配置）
- raw: 原始配置内容

输出 JSON 格式：
{
  "status": "valid" | "warn" | "error",
  "summary": {
    "mod_count": 模组总数,
    "issue_count": 问题数量,
    "critical_count": 严重问题数,
    "suggestion_count": 建议数量
  },
  "issues": [
    {
      "level": "critical" | "warning" | "info",
      "mod_id": "workshop-xxxxx",
      "mod_name": "模组名称",
      "issue_type": "missing" | "conflict" | "invalid" | "performance",
      "title": "问题标题（简短）",
      "description": "问题详细描述",
      "impact": "影响说明",
      "current_value": "当前值",
      "suggested_value": "建议值",
      "reason": "为什么建议这样改",
      "config_path": "configuration_options.xxx"
    }
  ],
  "optimized_config": "完整的 Lua 配置文本"
}

问题级别说明：
- critical: 必须修复（导致模组无法工作或严重bug）
- warning: 建议修复（影响体验或性能）
- info: 可选优化（锦上添花）

问题类型说明：
- missing: 缺失关键配置项
- conflict: 与其他模组或服务器设置冲突
- invalid: 配置值无效或超出范围
- performance: 性能优化建议
```

---

## 数据结构变更

### 当前返回
```python
{
    "report": str,  # Markdown 报告
    "optimized_config": str,  # Lua 配置
    "cached": bool
}
```

### 增强后返回
```python
{
    "status": "valid" | "warn" | "error",
    "summary": {
        "mod_count": int,
        "issue_count": int,
        "critical_count": int,
        "suggestion_count": int
    },
    "issues": List[Dict],  # 详见 AI Prompt
    "optimized_config": str,
    "report": str,  # 人类可读的 Markdown 报告
    "cached": bool
}
```

---

## 实现步骤

### Phase 1: AI Prompt 增强
1. 修改 `ModConfigParser._build_prompt()`
2. 修改 `ModConfigParser._build_ai_report()` 解析新的 JSON 格式
3. 测试 AI 返回的 issues 数据

### Phase 2: 报告渲染
1. 修改 `ModConfigParser._render_report()`
2. 按级别分组显示问题（critical/warning/info）
3. 添加交互式提示（如何应用配置）

### Phase 3: 新增命令
1. 实现 `/dst mod config show` 命令
2. 实现 `/dst mod config apply` 命令（支持 --auto 和 --dry-run）
3. 实现交互式确认流程

### Phase 4: 存档分析增强
1. 同样改进 `ArchiveAnalyzer`
2. 增加存档结构问题的诊断
3. 提供修复建议

---

## 存档分析增强示例

### 当前
```
📦 存档分析报告

文件数量：42
Lua 文件：12 个
识别到的世界：Master, Caves
已安装模组：21 个
```

### 增强
```
📦 存档诊断报告

🔍 存档结构：
- 文件总数：42
- 世界数量：2（Master + Caves）
- 已安装模组：21 个

❌ 发现的问题：

1. 【存档结构】Caves 世界缺少 leveldataoverride.lua
   - 路径：Caves/leveldataoverride.lua
   - 影响：洞穴世界可能无法正常加载
   - 💡 建议：从默认模板复制或使用 AI 生成

2. 【配置文件】server.ini 缺少最大玩家数设置
   - 路径：Master/server.ini
   - 影响：使用默认值，可能与模组设置冲突
   - 💡 建议：添加配置 `max_players = 6`

3. 【存档元数据】missing 对象数量异常
   - 路径：metadata/metadata.lua
   - 问题：检测到 missing 对象超过 100 个
   - 影响：可能存在已移除的物品引用
   - 💡 建议：使用世界重置工具清理

✅ 优化建议：

1. 【必须修复】补充缺失的配置文件
2. 【建议优化】清理无效的存档引用
3. 【可选】调整世界生成参数

---

📋 查看详细修复步骤：
/dst archive fix <房间ID> --list

🚀 自动修复可修复的问题：
/dst archive fix <房间ID> --auto
```

---

## 用户体验流程对比

### 当前流程
```
用户：/dst mod parse 2 1
  ↓
Bot：[完整报告 + 优化配置]
  ↓
用户：[手动复制配置到服务器] 😓
```

### 增强后流程
```
用户：/dst mod parse 2 1
  ↓
Bot：[问题清单 + 建议清单]
  ↓
用户：/dst mod config apply 2 1 --auto
  ↓
Bot：[应用成功] ✅
```

---

## 技术细节

### 1. AI 响应缓存
```python
# 缓存 AI 分析结果（1小时 TTL）
# 用户可以在诊断后立即应用，无需重新分析
cache_key = f"mod_parse:{room_id}:{world_id}"
```

### 2. 配置应用策略
```python
# 策略 1: 完全替换（覆盖整个文件）
await api_client.update_mod_config(room_id, world_id, config)

# 策略 2: 增量更新（只修改特定项）
for issue in issues:
    await api_client.update_mod_option(
        room_id, world_id,
        issue['mod_id'],
        issue['config_path'],
        issue['suggested_value']
    )
```

### 3. 交互式确认状态管理
```python
# 使用会话状态跟踪用户选择
session_id = f"mod_config_apply:{room_id}:{world_id}:{user_id}"
state = {
    "issues": [...],
    "applied": [],
    "skipped": [],
    "pending": [...]
}
```

---

## 预期效果

1. **用户更清楚问题所在**：不只是看到优化后的配置，还能知道为什么需要改
2. **降低应用门槛**：不需要手动复制粘贴，一行命令即可应用
3. **提高可控性**：用户可以选择性应用建议，不必全盘接受
4. **减少错误**：AI 分析后用户确认，避免误操作

---

## 下一步

是否开始实施这个增强计划？

我可以：
1. 先实现模组配置诊断功能
2. 然后实现存档诊断功能
3. 最后添加交互式应用命令

或者你想先看看具体的代码实现？
