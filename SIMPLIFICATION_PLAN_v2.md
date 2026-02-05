# DST 插件简化计划 v2.0

**目标**: 简化命令结构，添加默认房间功能，减少用户记忆负担

---

## 📊 当前菜单分析

### 现状统计
- **总命令数**: 27 个
- **命令层级**: 2-3 层
- **用户困惑点**:
  1. 命令太��（如 `/dst backup restore <房间ID> <文件名>`）
 2. 参数繁多（如 `--optimized`, `--dry-run`）
  3. 每次都要输入房间 ID（重复工作）

---

## 🎯 简化策略

### 策略 1: 添加默认房间功能 ⭐⭐⭐

**功能说明**：
- 设置默认房间后，所有命令可省略房间 ID
- 需要时仍可临时指定其他房间 ID
- 适合单服务器用户

**命令**：
```
/dst 默认房间 <房间ID>    # 设置默认房间
/dst 清除默认              # 清除默认房间设置
/dst 查看默认              # 查看当前默认房间
```

**效果**：
```
# 设置默认房间为 2
/dst 默认房间 2

# 之后可以省略房间 ID
/dst 列表              # → /dst list 2
/dst 玩家列表          # → /dst players 2
/dst 模组列表          # → /dst mod list 2

# 临时使用其他房间
/dst 模组列表 3      # 查看 3 号房间的模组
```

---

### 策略 2: 中文命令别名（高频功能）

**优先级**: 高频命令 → 中文
**保留**: 低级命令 → 英文

#### 房间管理（高频）
```
当前: /dst list
简化: /dst 房间列表 [页码]

当前: /dst info <房间ID>
简化: /dst 房间详情 <房间ID>
```

#### 玩家管理（高频）
```
当前: /dst players <房间ID>
简化: /dst 玩家列表 <房间ID>
别名: /dst 玩家查询 <房间ID>
```

#### 模组管理（高频）
```
当前: /dst mod search <关键词>
简化: /dst 模组搜索 <关键词>

当前: /dst mod list <房间ID>
简化: /dst 模组列表 <房间ID>

当前: /dst mod add <房间ID> <世界ID> <模组ID>
简化: /dst 添加模组 <房间ID> <世界ID> <模组ID>

当前: /dst mod remove <房间ID> <世界ID> <模组ID>
简化: /dst 移除模组 <房间ID> <世界ID> <模组ID>
```

#### 备份管理（中频）
```
当前: /dst backup list <房间ID>
简化: /dst 备份列表 <房间ID>

当前: /dst backup create <房间ID>
简化: /dst 创建备份 <房间ID>

当前: /dst backup restore <房间ID> <文件名>
简化: /st 恢复备份 <房间ID> <文件名>
```

---

### 策略 3: 简化参数

#### 移除 `--optimized` 参数
```
当前: /dst mod config save 2 1 --optimized
简化: /dst 模组配置 <房间ID> <世界ID>

# 如果需要原始配置
/dst 模组原始配置 <房间ID> <世界ID>
```

#### 合并 `--dry-run` 到命令逻辑
```
当前: /dst mod config apply 2 1 --dry-run
简化: /st 预览配置 <房间ID> <世界ID>
```

---

## 📋 完整简化后的菜单

### 基础命令（保留英文）
```
房间管理：
  /dst list [页码]           → /dst 房间列表 [页码]
  /dst info <房间ID>          → /dst 房间详情 <房间ID>
  /dst start <房间ID>         → /dst 启动房间 <房间ID> 🔒
  /dst stop <房间ID>          → /dst 关闭房间 <房间ID> 🔒
  /dst restart <房间ID>       → /dst 重启房间 <房间ID> 🔒

玩家管理：
  /dst players <房间ID>       → /dst 玩家列表 <房间ID>
  /dst kick <房间ID> <KU_ID>  → /dst 踢出玩家 <房间ID> <KU_ID> 🔒

模组管理：
  /dst mod search <关键词>   → /dst 模组搜索 <关键词>
  /dst mod list <房间ID>     → /dst 模组列表 <房间ID>
  /dst mod add <房间ID> <世界ID> <模组ID>  → /dst 添加模组 <房间ID> <世界ID> <模组ID> 🔒
  /dst mod remove <房间ID> <世界ID> <> <模组ID>  → /dst 移除模组 <房间ID> <世界ID> <> <模组ID> 🔒
  /dst mod check <房间ID>   → /dst 检测模组 <房间ID>

备份管理：
  /dst backup list <房间ID>   → /dst 备份列表 <房间ID>
  /dst backup create <房间ID>  → /dst 创建备份 <房间ID> 🔒
  /dst backup restore <房间ID> <文件名>  → /dst 恢复备份 <房间ID> <文件名> 🔒

存档管理：
  /dst archive upload <房间ID> <文件>  → /st 上传存档 <房间ID> <文件> 🔒
  /dst archive download <房间ID>  → /st 下载存档 <房间ID>
  /dst archive replace <房间ID> <文件>  → /st 替换存档 <房间ID> <文件> 🔒
  /dst archive validate <文件>

控制台：
  /dst console <房间ID> [世界ID] <命令>  → /st 控制台 <房间ID> [世界ID] <命令> 🔒
  /dst announce <房间ID> <消息>  → /st 公告 <房间ID> <消息> 🔒

AI 功能：
  /dst analyze <房间ID>      → /st 配置分析 <房间ID>
  /dst mod recommend <房间ID> [类型]  → /st 模组推荐 <房间ID> [类型]
  /dst mod parse <房间ID> <世界ID>   → /st 模组解析 <房间ID> <世界ID>
  /dst archive analyze <文件>   → /st 存档分析 <文件>
  /dst ask <问题>              → /st 智能问答 <问题>

🔒 标记的命令需要管理员权限
```

---

## 🎯 推荐方案：混合模式 + 默认房间

### 第一批：核心简化（今天完成）

#### 1. 添加默认房间功能
```python
# 新增命令
@on_command("dst 默认房间")
@on_command("dst 清除默认")
@on_command("dst 查看默认")
```

#### 2. 添加中文命令别名
```python
# 高频命令中文别名
aliases=["dst list", "dst 房间列表"]
aliases=["dst players", "dst 玩家列表"]
aliases=["dst mod search", "dst 模组搜索"]
aliases=["dst mod list", "dst 模组列表"]
```

#### 3. 简化参数
- `mod config save` 默认使用优化配置
- `mod config save --raw` 使用原始配置

---

## 📊 实施优先级

### P0 - 立即实施
1. ✅ 默认房间功能
2. ✅ 中文命令别名（高频命令）
3. ✅ 简化参数（移除 --optimized）

### P1 - 近期（本周）
1. 命令别名文档
2. 使用示例更新
3. 帮助文档更新

### P2 - 中期（下周）
1. 用户配置持久化
2. 跨房间操作支持
3. 命令历史记录

---

## 💡 使用场景示例

### 单服务器用户（主要目标用户）

```bash
# 初次使用
/dst 默认房间 2        # 设置默认房间
/dst 玩家列表           # → 查看在线玩家
/dst 模组列表           # → 查看已安装模组

# 日常使用
/dst 玩家列表           # → 查看在线玩家
/dst 添加模组 2 1 123456  # → 安装模组
/dst 创建备份           # → 创建备份（使用默认房间）
```

### 多服务器管理员

```bash
# 管理 2 号服务器
/dst 模组列表 3       # 查看 3 号房间
/dst 创建备份 3       # 创建 3 号房间备份

# 快速查看多个服务器
/dst 房间列表 1       # 查看 1 号房间
/dst 房间详情 2       # 查看 2 号房间详情
```

---

## 🚀 预期效果

| 指标 | 当前 | 简化后 |
|------|------|--------|
| 核心命令数 | 27 | 15 个中文别名 + 27 个英文 |
| 平均命令长度 | 3 层 | 2 层 |
| 参数记忆负担 | 高 | 低（默认房间） |
| 学习曲线 | 2 天 | 1 天 |

---

## 📝 实施步骤

1. **创建 `handlers/default_room.py`**
   - 默认房间设置/查询/清除
   - 用户配置存储（localstore 或数据库）

2. **更新现有 handlers**
   - 添加中文命令别名
   - 支持默认房间参数

3. **更新文档**
   - COMMANDS_COMPLETE.md
   - README.md
   - 使用示例

4. **测试验证**
   - 单元测试
   - 集成测试
   - 用户体验测试

---

**主人，这个方案怎么样？要不要我现在开始实施"默认房间"功能？😊**
