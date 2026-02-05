# QQ群签到获取游戏内物资功能 - 开发计划

**功能名称**: QQ群签到系统
**目标**: 玩家在QQ群内签到，获得游戏内物品奖励
**技术栈**: NoneBot2 + DST控制台命令 + 数据库

---

## 📊 需求分析

### 核心功能
1. **签到系统**
   - 每日签到打卡
   - 连续签到奖励
   - 签到等级系统

2. **物品奖励**
   - 通过控制台命令给予物品
   - 可配置奖励列表
   - 不同等级不同奖励

3. **防作弊**
   - 绑定游戏内玩家ID（KU_ID）
   - 防止重复签到
   - IP/账号限制

---

## 🔍 技术调研

### DST控制台命令（给予物品）

根据搜索结果，DST支持以下控制台命令：

#### 1. 给予物品到玩家背包
```lua
c_give("prefab", amount)
```

**示例**：
```lua
c_give("goldnugget", 10)      -- 给予10个金块
c_give("meat", 5)             -- 给予5个肉
c_give("hammer", 1)           -- 给予1个锤子
c_give("nightmare_timepiece", 1)  -- 给予1个铥矿碎片
```

#### 2. 生成物品在玩家位置
```lua
c_spawn("prefab", amount)
```

#### 3. 给予指定玩家物品
```lua
-- 先选择玩家
c_select(AllPlayers[index])
-- 然后给予
c_give("prefab", amount)
```

#### 4. 通过玩家ID查找
```lua
for i, v in ipairs(AllPlayers) do
    if v.userid == "KU_xxx" then
        c_give("goldnugget", 10)
    end
end
```

### 常用物品prefab列表

| 物品名称 | prefab | 说明 |
|---------|--------|------|
| 金块 | goldnugget | 基础货币 |
| 草 | cutgrass | 基础材料 |
| 木头 | log | 基础材料 |
| 石头 | rocks | 基础材料 |
| 烤肉 | cookedmeat | 食物 |
| 猪皮 | pigskin | 材料 |
| 铰矿 | nightmare_timepiece | 高级材料 |
| 格罗姆粘液 | gears | 材料 |
| 蓝图 | blueprint | 图纸 |
|宝石 | redgem | 宝石 |

---

## 🏗️ 系统设计

### 架构图

```
QQ群用户
    ↓
NoneBot2 插件
    ↓
签到命令 (/dst sign)
    ↓
┌─────────────────────┐
│  数据层 (SQLite)     │
│  - 用户绑定信息      │
│  - 签到记录          │
│  - 奖励配置          │
└─────────────────────┘
    ↓
┌─────────────────────┐
│  逻辑层              │
│  - 签到验证          │
│  - 奖励计算          │
│  - 防作弊检查        │
└─────────────────────┘
    ↓
┌─────────────────────┐
│  DST控制台接口       │
│  - c_give命令        │
│  - 玩家查找          │
└─────────────────────┘
    ↓
游戏内玩家收到物品
```

### 数据库设计

#### 1. 用户绑定表 (sign_users)
```sql
CREATE TABLE sign_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qq_id TEXT NOT NULL,              -- QQ号
    ku_id TEXT NOT NULL,              -- DST玩家ID (KU_xxx)
    room_id INTEGER NOT NULL,         -- 绑定的房间ID
    player_name TEXT,                 -- 玩家昵称
    bind_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sign_time DATE,
    sign_count INTEGER DEFAULT 0,
    continuous_days INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    total_points INTEGER DEFAULT 0,
    UNIQUE(qq_id, room_id)
);
```

#### 2. 签到记录表 (sign_records)
```sql
CREATE TABLE sign_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qq_id TEXT NOT NULL,
    room_id INTEGER NOT NULL,
    sign_date DATE NOT NULL,
    reward_level INTEGER NOT NULL,
    reward_items TEXT,                 -- JSON格式：[{"prefab":"goldnugget","amount":10}]
    sign_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(qq_id, sign_date)
);
```

#### 3. 奖励配置表 (sign_rewards)
```sql
CREATE TABLE sign_rewards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level INTEGER NOT NULL UNIQUE,
    continuous_days INTEGER NOT NULL,
    reward_items TEXT NOT NULL,        -- JSON格式
    bonus_points INTEGER DEFAULT 0,
    description TEXT
);
```

---

## 📝 功能详细设计

### Phase 1: 基础签到功能

#### 1.1 绑定命令
```bash
/dst sign bind <KU_ID> [房间ID]
```

**功能**：
- 绑定QQ号与DST玩家ID
- 可选：指定房间（使用默认房间则省略）
- 每个QQ号在同一个房间只能绑定一次

**逻辑**：
1. 验证KU_ID格式（KU_开头的字符串）
2. 检查是否已绑定
3. 保存到数据库

#### 1.2 签到命令
```bash
/dst sign [房间ID]
```

**功能**：
- 每日签到打卡
- 获得物品奖励
- 记录签到天数

**逻辑**：
1. 检查用户是否绑定
2. 检查今天是否已签到
3. 计算连续天数和等级
4. 发送控制台命令给予物品
5. 保存签到记录

**控制台命令示例**：
```lua
-- 查找玩家
for i, v in ipairs(AllPlayers) do
    if v.userid == "KU_BQAUz1rk" then
        -- 给予奖励
        c_give("goldnugget", 10)
        c_give("cookedmeat", 5)
    end
end
```

### Phase 2: 奖励系统

#### 2.1 等级奖励
```lua
Level 1 (新用户): 金块x10, 烤肉x5
Level 2 (3天):     金块x20, 烤肉x10, 草x20
Level 3 (7天):     金块x30, 铰矿x2, 格罗姆粘液x1
Level 4 (14天):    金块x50, 铰矿x5, 宝石x1
Level 5 (30天):    金块x100, 铰矿x10, 宝石x2
```

#### 2.2 连续签到奖励
- 连续3天：额外金块x20
- 连续7天：额外铰矿x1
- 连续30天：额外宝石x1

#### 2.3 特殊奖励
- 首次签到：额外获得锤子x1
- 满月签到：额外获得蓝图x3

### Phase 3: 防作弊机制

#### 3.1 绑定验证
- 绑定时需要玩家在游戏中确认
- 通过发送私聊消息确认

#### 3.2 签到限制
- 每天只能签到一次
- 同一QQ号不能重复绑定同一房间
- 检测玩家是否在线（可选）

#### 3.3 异常检测
- 频繁切换绑定
- 短时间多次签到尝试
- IP地址异常变化

---

## 🔧 技术实现

### 文件结构
```
nonebot_plugin_dst_management/
├── handlers/
│   └── sign.py                    # 签到处理器
├── services/
│   ├── sign_service.py            # 签到业务逻辑
│   └── reward_service.py          # 奖励计算
├── database/
│   ├── __init__.py
│   ├── models.py                  # 数据库模型
│   └── connection.py              # 数据库连接
└── utils/
    └── console_helper.py          # 控制台命令辅助
```

### 核心代码示例

#### 1. 控制台命令生成
```python
def generate_give_command(ku_id: str, rewards: List[Dict]) -> str:
    """生成给予物品的控制台命令"""
    commands = []
    
    # 查找玩家并给予物品
    cmd = f'''
for i, v in ipairs(AllPlayers) do
    if v.userid == "{ku_id}" then
'''
    
    for reward in rewards:
        prefab = reward['prefab']
        amount = reward['amount']
        cmd += f'        c_give("{prefab}", {amount})\n'
    
    cmd += '    end\nend'
    
    return cmd
```

#### 2. 签到逻辑
```python
async def handle_sign(user_id: str, room_id: int):
    """处理签到"""
    # 1. 检查绑定
    user = get_bound_user(user_id, room_id)
    if not user:
        return "请先使用 /dst sign bind <KU_ID> 绑定账号"
    
    # 2. 检查今日签到
    today = date.today()
    if already_signed(user_id, today):
        return "今天已经签到过了哦~"
    
    # 3. 计算奖励
    continuous_days = calculate_continuous_days(user)
    reward = calculate_reward(continuous_days)
    
    # 4. 发送控制台命令
    console_cmd = generate_give_command(user['ku_id'], reward['items'])
    await api_client.execute_console_command(room_id, None, console_cmd)
    
    # 5. 保存记录
    save_sign_record(user_id, room_id, reward)
    
    # 6. 返回结果
    return f"签到成功！获得：{format_reward(reward)}"
```

### 3. 数据库操作
```python
def get_bound_user(qq_id: str, room_id: int) -> Optional[Dict]:
    """获取绑定的用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ku_id, player_name, continuous_days, level
        FROM sign_users
        WHERE qq_id = ? AND room_id = ?
    ''', (qq_id, room_id))
    
    return cursor.fetchone()
```

---

## 📋 奖励配置示例

### 基础奖励表
```python
SIGN_REWARDS = {
    1: {  # 新用户
        'continuous_days': 0,
        'items': [
            {'prefab': 'goldnugget', 'amount': 10},
            {'prefab': 'cookedmeat', 'amount': 5},
        ],
        'bonus_points': 10,
    },
    2: {  # 3天
        'continuous_days': 3,
        'items': [
            {'prefab': 'goldnugget', 'amount': 20},
            {'prefab': 'cookedmeat', 'amount': 10},
            {'prefab': 'cutgrass', 'amount': 20},
        ],
        'bonus_points': 20,
    },
    3: {  # 7天
        'continuous_days': 7,
        'items': [
            {'prefab': 'goldnugget', 'amount': 30},
            {'prefab': 'nightmare_timepiece', 'amount': 2},
            {'prefab': 'gears', 'amount': 1},
        ],
        'bonus_points': 50,
    },
    # ... 更多等级
}
```

---

## 🚀 开发步骤

### Phase 1: 数据库层（第1天）
1. 创建数据库表结构
2. 实现基础CRUD操作
3. 编写数据库测试

### Phase 2: 核心功能（第2-3天）
1. 实现绑定功能
2. 实现基础签到
3. 实现奖励计算

### Phase 3: 控制台集成（第4天）
1. 实现控制台命令生成
2. 集成DMP API
3. 测试物品给予

### Phase 4: 高级功能（第5-6天）
1. 实现连续签到奖励
2. 实现等级系统
3. 添加防作弊机制

### Phase 5: 测试与优化（第7天）
1. 编写完整测试
2. 性能优化
3. 文档编写

---

## ⚠️ 注意事项

### 1. 游戏平衡
- 奖励不能过于丰厚，避免破坏游戏平衡
- 高级材料奖励要谨慎
- 考虑服务器经济影响

### 2. 性能考虑
- 控制台命令执行需要时间
- 大量玩家同时签到可能卡顿
- 考虑队列机制

### 3. 安全性
- 防止SQL注入
- 验证KU_ID格式
- 限制绑定次数

### 4. 兼容性
- 确保与现有功能兼容
- 不影响正常游戏
- 可配置开关

---

## 📊 预期效果

### 用户体验
- 每日签到获得游戏资源
- 连续签到有额外奖励
- 提升群活跃度

### 技术指标
- 签到响应时间 < 3秒
- 物品给予成功率 > 95%
- 数据库查询 < 100ms

---

## 🔗 参考资料

- [DST控制台命令文档](https://dontstarve.fandom.com/wiki/Console/Don't_Star_Together_Commands)
- [NoneBot2文档](https://nonebot.cqp.moe/)
- [Python SQLite文档](https://docs.python.org/3/library/sqlite3.html)

---

**计划制定时间**: 2026-02-05
**计划制定人**: 小安 (Xiao An)
**预计开发周期**: 7天
**版本**: v0.4.0
