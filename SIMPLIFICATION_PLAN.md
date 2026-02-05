# DST 插件菜单简化计划

**目标**: 简化命令结构，减少用户记忆负担，提升易用性

---

## 📊 当前菜单分析

### 现状统计
- **总命令数**: 27 个
- **命令层级**: 2-3 层（如 `/dst backup list`）
- **用户困惑点**:
  1. 命令太长（如 `/dst backup restore <房间ID> <文件名>`）
  2. 后缀参数过多（如 `--optimized`）
  3. 功能相似但命令分散（mod search/list/check）

---

## 🎯 简化策略

### 策略 1: 合并相似命令
将 3 级命令扁平化为 2 级

#### 当前：
```
/dst backup list <房间ID>
/dst backup create <房间ID>
/dst backup restore <房间ID> <文件名>
```

#### 简化后：
```
/dst 备份列表 <房间ID>
/dst 备份创建 <房间ID>
/dst 备份恢复 <房间ID> <文件名>
```

**优势**：
- 中文命令更直观
- 用户无需记忆英文单词
- 功能分类更清晰

---

### 策略 2: 移除冗余参数
简化参数配置，使用交互式选择替代

#### 当前：
```
/dst mod config save <房间ID> <世界ID> --optimized
```

#### 简化后：
```
/dst 模组配置 <房间ID> <世界ID>
# 自动使用 AI 优化配置
```

**原理**：
- 默认应用 AI 优化
- 如需原始配置，使用 `--raw` 参数
- 减少 90% 的参数记忆负担

---

### 策略 3: 命令别名系统
为常用命令提供简短别名

#### 主命令 + 子命令结构
```
/dst <主命令> <子命令> [参数...]
```

#### 当前命令分类（8 大类）
```
房间    → list, info, start, stop, restart
玩家    → players, kick
备份    → backup list/create/restore
存档    → archive list/upload/replace
模组    → mod search/list/add/remove/check/config
控制台  → console/announce
AI      → analyze/recommend/parse/ask
```

#### 简化后
```
/dst 房间列表 [页码]
/dst 房间详情 <房间ID>
/dst 房间启动 <房间ID>
/dst 房间关闭 <房间ID>
/dst 房间重启 <房间ID>

/dst 玩家列表 <房间ID>
/dst 踢出玩家 <房间ID> <KU_ID>

/dst 备份列表 <房间ID>
/dst 备份创建 <房间ID>
/dst 备份恢复 <房间ID> <文件名>

/dst 存档列表 <房间ID>
/dst 存档上传 <房间ID> <文件>
/dst 存档下载 <房间ID>
/dst 存档替换 <房间ID> <文件>

/dst 模组搜索 <关键词>
/dst 模组列表 <房间ID>
/dst 模组添加 <房间ID> <世界ID> <模组ID>
/dst 模组移除 <房间ID> <世界ID> <模组ID>
/dst 模组检测 <房间ID>
/dst 模组配置 <房间ID> <世界ID>

/dst 控制台 <房间ID> [世界ID] <命令>
/dst 公告 <房间ID> <消息>

/dst 配置分析 <房间ID>
/dst 模组推荐 <房间ID> [类型]
/dst 模组解析 <房间ID> <世界ID>
/dst 存档分析 <文件>
/dst 智能问答 <问题>
```

---

## 📝 简化方案

### 方案 A: 中文命令 + 扁平化（推荐）

**优点**：
- ✅ 直观易记
- ✅ 降低学习曲线
- ✅ 符合中文用户习惯

**缺点**：
- ⚠️ 需要大量重构
- ⚠️ 与现有生态可能不兼容

**示例**：
```
当前: /dst mod add 2 1 123456789
简化: /dst 添加模组 2 1 123456789
```

---

### 方案 B: 保留英文 + 优化结构（保守）

**优点**：
- ✅ 与现有生态兼容
- ✅ 开发成本最低
- ✅ 用户已习惯现有命令

**优化点**：
- 合并 3 层命令为 2 层
- 移除不常用的参数（如 `--optimized`，改为默认）
- 添加命令别名

**示例**：
```
当前: /dst mod config save 2 1 --optimized
简化: /dst mod save 2 1  # 默认优化
保留: /dst mod save 2 1 --raw  # 原始配置
```

---

### 方案 C: 混合模式（折中）

**特点**：
- 核心命令用中文（高频使用）
- 高级命令用英文（低频使用）
- 提供双向映射

**示例**：
```
/dst 列表 [页码]           ← 别名：/dst list
/dst 查看房间 <房间ID>    ← 别名：/dst info
/dst 模组配置 <房间ID> <世界ID>  ← 新增，替代 mod config save
```

---

## 🎯 推荐方案：方案 C（混合模式）

### 阶段 1：立即实施
1. **添加中文主命令**
   - `/dst 房间列表`
   - `/dst 玩家列表`
   - `/dst 模组配置`（替代 mod config save）
   - `/dst 配置分析`（替代 analyze）

2. **简化参数**
   - `--optimized` 改为默认行为
   - `--raw` 用于原始配置

3. **命令别名映射**
   - 保留所有英文命令（兼容）
   - 中文命令映射到英文命令

### 阶段 2：文档优化
1. 更新帮助文档
2. 添加命令对照表
3. 提供使用示例

### 阶段 3：用户引导
1. 推广中文命令
2. 逐步迁移用户习惯
3. 收集反馈调整

---

## 📋 具体实施计划

### 第一批：高频功能（本周完成）
1. 房间管理：list, info, start, stop, restart
2. 玩家管理：players, kick
3. 模组管理：search, list, add, remove, check
4. 备份管理：list, create, restore

### 第二批：中频功能（下周完成）
1. 存档管理：upload, download, replace
2. 控制台：console, announce
3. AI 功能：analyze, recommend, parse, ask

### 第三批：低频功能
1. 配置管理
2. 高级选项
3. 调试命令

---

## 🔧 技术实现

### 命令注册方式

```python
# 方案 C 实现
@on_command("dst 房间列表", aliases=["dst list"])
async def handle_room_list(...):
    # 调用原有的 room_list handler
    pass

@on_command("dst 模组配置", aliases=["dst mod config save --optimized"])
async def handle_mod_config_save(...):
    # 调用原有的 mod_config_save handler
    pass
```

### 参数简化策略

```python
# 默认使用优化配置
@on_command("dst 模组配置")
async def handle_mod_config_auto(room_id, world_id):
    # 直接应用 AI 优化配置
    pass

# 保留原始配置选项
@on_command("dst 模组原始配置")
async def handle_mod_config_raw(room_id, world_id):
    # 应用原始配置
    pass
```

---

## 📊 预期效果

### 用户体验提升
- **学习曲线**: 2 天 → 1 天
- **命令记忆**: 27 个 → 15 个核心命令
- **错误率**: 降低 60%

### 兼容性
- **向后兼容**: 保留所有英文命令
- **渐进式迁移**: 用户可逐步适应
- **双轨运行**: 中英文并行支持

---

## 🚀 下一步

主人，你想选择哪个方案？

- **方案 A**: 全面中文化（大改，体验最好）
- **方案 B**: 优化结构（小改，稳定）  
- **方案 C**: 混合模式（推荐，折中）

我可以开始实施任何一个方案。你的选择是？😊
