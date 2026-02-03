# NoneBot2 DST 管理插件 - 命令参考

## 📋 命令总览

### 房间管理
- `/dst list [页码]` - 查看房间列表
- `/dst info <房间ID>` - 查看房间详情
- `/dst start <房间ID>` - 启动房间 🔒
- `/dst stop <房间ID>` - 关闭房间 🔒
- `/dst restart <房间ID>` - 重启房间 🔒
- `/dst create` - 创建新房间 🔒

### 玩家管理
- `/dst players <房间ID>` - 查看在线玩家
- `/dst stats <房间ID>` - 查看玩家统计
- `/dst kick <房间ID> <KU_ID>` - 踢出玩家 🔒
- `/dst whitelist add <房间ID> <KU_ID>` - 添加白名单 🔒
- `/dst whitelist remove <房间ID> <KU_ID>` - 移除白名单 🔒
- `/dst blacklist add <房间ID> <KU_ID>` - 添加黑名单 🔒
- `/dst blacklist remove <房间ID> <KU_ID>` - 移除黑名单 🔒

### 存档管理
- `/dst archive upload <房间ID> <文件>` - 上传存档 🔒
- `/dst archive download <房间ID>` - 下载存档
- `/dst archive replace <房间ID> <文件>` - 替换存档 🔒
- `/dst archive validate <文件>` - 验证存档格式

### 模组管理
- `/dst mod search <关键词>` - 搜索模组
- `/dst mod list <房间ID>` - 查看已安装模组
- `/dst mod info <模组ID>` - 查看模组详情
- `/dst mod add <房间ID> <世界ID> <模组ID>` - 添加模组 🔒
- `/dst mod remove <房间ID> <世界ID> <模组ID>` - 删除模组 🔒
- `/dst mod enable <房间ID> <世界ID> <模组ID>` - 启用模组 🔒
- `/dst mod disable <房间ID> <世界ID> <模组ID>` - 禁用模组 🔒
- `/dst mod config <房间ID> <世界ID> <模组ID>` - 修改配置 🔒
- `/dst mod check <房间ID>` - 检测模组冲突

### 备份管理
- `/dst backup list <房间ID>` - 查看备份列表
- `/dst backup create <房间ID>` - 创建备份 🔒
- `/dst backup restore <房间ID> <序号>` - 恢复备份 🔒
- `/dst backup delete <房间ID> <序号>` - 删除备份 🔒
- `/dst backup auto <房间ID> <cron表达式>` - 设置自动备份 🔒

### 控制台命令
- `/dst console <房间ID> <世界ID> <命令>` - 执行控制台命令 🔒
- `/dst announce <房间ID> <消息>` - 发送全服公告 🔒
- `/dst rollback <房间ID> <天数>` - 回滚存档 🔒
- `/dst regenerate <房间ID> <世界ID>` - 重新生成世界 🔒

### 监控和统计
- `/dst overview` - 查看平台概览
- `/dst metrics [分钟数]` - 查看系统指标
- `/dst status <房间ID>` - 查看房间状态

### 系统命令
- `/dst help` - 显示帮助信息
- `/dst version` - 显示插件版本
- `/dst config` - 查看当前配置

---

## 📖 命令详解

### 房间管理命令

#### `/dst list [页码]`

**描述**: 查看所有 DST 房间列表

**权限**: 所有用户

**参数**:
- `页码` (可选) - 页码，默认为 1

**示例**:
```
用户: /dst list
Bot: 🏕️ DST 房间列表
     第 1/2 页 | 共 15 个房间

     1. 勋棱神话
        状态：🟢 运行中
        模式：无尽
        ID：2

     2. 测试服务器
        状态：🔴 已停止
        模式：生存
        ID：3

     💡 使用 /dst info <房间ID> 查看详情
     💡 使用 /dst list 2 查看下一页
```

---

#### `/dst info <房间ID>`

**描述**: 查看房间详细信息

**权限**: 所有用户

**参数**:
- `房间ID` (必需) - 房间的数字 ID

**示例**:
```
用户: /dst info 2
Bot: 🏕️ 勋棱神话

     📋 基本信息
     - 房间ID：2
     - 状态：🟢 运行中
     - 模式：无尽
     - 玩家限制：6人
     - 密码：已设置
     - PVP：关闭
     - 描述：有问题＋裙744834037

     🌍 世界列表
     - Master：🟢 在线 (端口 37777)
     - Caves：🟢 在线 (端口 36666)

     👥 在线玩家 (1人)
     - 󰀍八雪󰀍 (white_bone)

     🧩 已安装模组：21个
```

---

#### `/dst start <房间ID>`

**描述**: 启动指定的房间（所有世界）

**权限**: 管理员

**参数**:
- `房间ID` (必需) - 要启动的房间 ID

**示例**:
```
用户: /dst start 2
Bot: ⏳ 正在启动房间 2...

     ✅ 房间 2 启动成功
```

---

### 玩家管理命令

#### `/dst players <房间ID>`

**描述**: 查看当前在线玩家

**权限**: 所有用户

**参数**:
- `房间ID` (必需) - 房间 ID

**示例**:
```
用户: /dst players 2
Bot: 👥 在线玩家 (勋棱神话)

     1. 󰀍八雪󰀍 (KU_BQAUz1rk)
        - KU_ID: KU_BQAUz1rk
        - 角色: 白骨
        - 存活: 15天
        - 在线: 2小时30分

     共 1/6 名玩家在线
```

---

#### `/dst kick <房间ID> <KU_ID>`

**描述**: 踢出指定玩家

**权限**: 管理员

**参数**:
- `房间ID` (必需) - 房间 ID
- `KU_ID` (必需) - 玩家的 KU_ID

**示例**:
```
用户: /dst kick 2 KU_BQAUz1rk
Bot: ⏳ 正在踢出玩家 KU_BQAUz1rk...

     ✅ 玩家已被踢出
```

---

### 存档管理命令

#### `/dst archive upload <房间ID> <文件>`

**描述**: 上传存档文件到指定房间

**权限**: 管理员

**参数**:
- `房间ID` (必需) - 房间 ID
- `文件` (必需) - 存档文件（ZIP 格式）或文件 URL

**功能**:
- 自动备份当前存档
- AI 辅助存档结构验证
- 自动识别 Master/Caves 世界
- 支持模组配置导入

**示例**:
```
用户: /dst archive upload 2 https://example.com/archive.zip
Bot: ⏳ 正在下载存档...

     ⏳ 正在解析存档结构...

     ⏳ 正在备份当前存档...

     ✅ 存档上传成功
     - 世界数量：2 (Master + Caves)
     - 模组数量：21
     - 游戏模式：无尽

     💡 使用 /dst start 2 启动房间
```

---

#### `/dst archive download <房间ID>`

**描述**: 下载房间存档

**权限**: 所有用户

**参数**:
- `房间ID` (必需) - 房间 ID

**功能**:
- 打包所有世界配置
- 包含模组配置
- 自动生成 ZIP 文件

**示例**:
```
用户: /dst archive download 2
Bot: 📦 正在打包存档...

     ✅ 存档已生成
     - 文件名：勋棱神话_20260203.zip
     - 大小：245.3 MB
     - 世界：Master + Caves
     - 模组：21个

     [下载链接]
```

---

### 模组管理命令

#### `/dst mod search <关键词>`

**描述**: 从 Steam Workshop 搜索模组

**权限**: 所有用户

**参数**:
- `关键词` (必需) - 搜索关键词

**示例**:
```
用户: /dst mod search 健康条
Bot: 🧩 模组搜索结果：健康条

     1. [Show Me] Health Info
        ID: 1185229307
        作者: Zarklord
        订阅：100,000+

     2. DST Health Info
        ID: 3625940357
        作者：Mroz4k
        订阅：50,000+

     💡 使用 /dst mod add <房间ID> <世界ID> <模组ID> 添加模组
```

---

#### `/dst mod add <房间ID> <世界ID> <模组ID>`

**描述**: 添加并启用模组

**权限**: 管理员

**参数**:
- `房间ID` (必需) - 房间 ID
- `世界ID` (必需) - 世界 ID（1=Master, 2=Caves）
- `模组ID` (必需) - Steam Workshop ID

**功能**:
- 自动下载模组
- AI 智能配置（可选）
- 自动启用模组
- 检测配置冲突

**示例**:
```
用户: /dst mod add 2 1 1185229307
Bot: ⏳ 正在搜索模组...

     ✅ 找到模组：[Show Me] Health Info

     ⏳ 正在下载模组...

     ⏳ 正在配置模组（AI 辅助）...

     ⏳ 正在启用模组...

     ✅ 模组添加成功！
     💡 房间需要重启才能生效，使用 /dst restart 2
```

---

#### `/dst mod check <房间ID>`

**描述**: 检测模组冲突和问题

**权限**: 所有用户

**参数**:
- `房间ID` (必需) - 房间 ID

**功能**:
- 检测功能冲突
- 检测兼容性问题
- 推荐加载顺序
- 性能影响评估

**示例**:
```
用户: /dst mod check 2
Bot: 🔍 模组分析报告

     ⚠️ 发现 2 个冲突：

     1. 健康显示冲突
        - [Show Me] Health Info
        - DST Health Info
        建议：只保留一个

     2. 性能警告
        - Too Many Items (可能影响性能)
        建议：关闭服务器时禁用

     ✅ 推荐加载顺序：
     1. 基础功能模组
     2. UI 增强模组
     3. 游戏机制模组
```

---

### 备份管理命令

#### `/dst backup create <房间ID>`

**描述**: 创建房间备份

**权限**: 管理员

**参数**:
- `房间ID` (必需) - 房间 ID

**示例**:
```
用户: /dst backup create 2
Bot: ⏳ 正在创建备份...

     ✅ 备份创建成功
     - 文件名：20260203_120000.zip
     - 大小：245.3 MB
     - 时间：2026-02-03 12:00:00
```

---

#### `/dst backup restore <房间ID> <序号>`

**描述**: 从备份恢复存档

**权限**: 管理员

**参数**:
- `房间ID` (必需) - 房间 ID
- `序号` (必需) - 备份序号（使用 /dst backup list 查看）

**示例**:
```
用户: /dst backup restore 2 1
Bot: ⚠️ 警告：恢复备份将覆盖当前存档

     确认恢复？回复 "确认" 继续，其他取消

用户: 确认
Bot: ⏳ 正在停止房间...

     ⏳ 正在恢复备份...

     ⏳ 正在启动房间...

     ✅ 备份恢复成功
```

---

### 控制台命令

#### `/dst console <房间ID> <世界ID> <命令>`

**描述**: 执行游戏控制台命令

**权限**: 管理员

**参数**:
- `房间ID` (必需) - 房间 ID
- `世界ID` (可选) - 世界 ID（不指定则所有世界）
- `命令` (必需) - 控制台命令

**常用命令**:
```
c_announce("消息")              # 发送公告
c_regenerateworld()             # 重新生成世界
c_reset()                       # 重置世界
c_despawn()                     # 删除所有生物
c_setseason("autumn")           # 设置季节
```

**示例**:
```
用户: /dst console 2 c_announce("服务器将在10分钟后重启")
Bot: ✅ 公告已发送

用户: /dst console 2 1 c_setseason("winter")
Bot: ✅ 命令执行成功
```

---

#### `/dst announce <房间ID> <消息>`

**描述**: 发送全服公告

**权限**: 管理员

**参数**:
- `房间ID` (必需) - 房间 ID
- `消息` (必需) - 公告内容

**示例**:
```
用户: /dst announce 2 欢迎来到勋棱神话！
Bot: ✅ 公告已发送到所有世界
```

---

### 监控命令

#### `/dst overview`

**描述**: 查看平台概览

**权限**: 所有用户

**示例**:
```
用户: /dst overview
Bot: 📊 DST 管理平台概览

     🏕️ 房间统计
     - 总房间数：15
     - 运行中：8
     - 已停止：7

     👥 玩家统计
     - 在线玩家：42
     - 最大同时在线：128

     💻 系统状态
     - CPU 使用率：35%
     - 内存使用：4.2GB / 16GB
     - 磁盘使用：125GB / 500GB
```

---

## 🔐 权限说明

### 权限级别

**普通用户**:
- 查看房间列表
- 查看房间详情
- 查看在线玩家
- 查看备份列表
- 搜索模组

**管理员**:
- 所有普通用户权限
- 启动/关闭房间
- 踢出玩家
- 管理备份
- 管理模组
- 执行控制台命令

**超级管理员**:
- 所有管理员权限
- 创建/删除房间
- 系统配置
- 用户权限管理

---

## 💡 使用技巧

### 1. 批量操作

```
# 批量添加多个模组
/dst mod add 2 1 1185229307
/dst mod add 2 1 3625940357
/dst mod add 2 1 1392778117

# 批量踢人
/dst kick 2 KU_123
/dst kick 2 KU_456
/dst kick 2 KU_789
```

### 2. 定时任务

```
# 设置每天凌晨2点自动备份
/dst backup auto 2 "0 2 * * *"

# 设置每6小时自动重启
/dst restart auto 2 "0 */6 * * *"
```

### 3. 监控告警

```
# 设置玩家数量告警
/dst monitor players 2 --max=10 --alert=true

# 设置内存使用告警
/dst monitor memory 2 --max=80 --alert=true
```

---

## ❓ 常见问题

### Q: 为什么命令没有响应？

A: 可能的原因：
1. 没有安装插件或加载失败
2. 权限不足（某些命令需要管理员）
3. 参数格式错误
4. API 连接失败

### Q: 如何获取房间 ID？

A: 使用 `/dst list` 查看所有房间及其 ID

### Q: 如何获取世界 ID？

A:
- Master 世界：通常是 1 或第一个世界的 ID
- Caves 世界：通常是 2 或第二个世界的 ID
- 使用 `/dst info <房间ID>` 查看详细世界列表

### Q: 模组安装后不生效？

A:
1. 检查模组是否已启用：`/dst mod list <房间ID>`
2. 尝试重启房间：`/dst restart <房间ID>`
3. 检查模组配置是否正确

### Q: 存档上传失败？

A:
1. 检查文件格式（必须是 ZIP）
2. 检查文件大小（不要超过限制）
3. 查看错误消息了解具体原因
4. 尝试使用 `/dst archive validate` 验证存档

---

## 📞 获取帮助

- 查看命令帮助：`/dst help`
- 查看插件版本：`/dst version`
- QQ群：744834037
- GitHub Issues：https://github.com/your-repo/issues

---

**文档版本**: 1.0.0
**最后更新**: 2026-02-03
**维护者**: 小安 (Xiao An)
