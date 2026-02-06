# nonebot-plugin-dst-management Markdown 模板与 UI 系统说明文档

本系统（Phase A）实现了平台感知的动态渲染，针对官方 QQ 机器人提供了精美的 Markdown 支持。

## 1. 核心渲染机制
- **渲染器**：`helpers/formatters.py` 中的 `render_auto` 函数。
- **工作流**：
    1. 检测 Bot 适配器（QQ vs OneBot）。
    2. 获取用户 UI 偏好（Markdown 或 Text）。
    3. 如果是官方 QQ 且偏好为 Markdown，使用 Markdown 模板。
    4. 否则回退到带 Emoji 的精美文本模式。

---

## 2. 现有 Markdown 模板列表

### 🏠 帮助菜单 (Help Menu)
- **位置**：`help_templates.py` -> `HELP_MARKDOWN_QQ`
- **参数**：无
- **结构**：分级标题 (##) + 列表 (-) + 引用块 (>)。

### 📋 房间列表 (Room List)
- **模板函数**：`format_room_list_markdown`
- **参数**：
    - `rooms`: `List[Dict]` (房间数据列表)
    - `page`: `int` (当前页码)
    - `total_pages`: `int` (总页数)
    - `total`: `int` (房间总数)
- **展示内容**：一级标题显示标题，二级标题显示房间名，列表显示状态、模式和 ID。

### 🔎 房间详情 (Room Detail)
- **模板函数**：`format_room_detail_markdown`
- **参数**：
    - `room`: `Dict` (基础信息)
    - `worlds`: `List[Dict]` (世界列表)
    - `players`: `List[Dict]` (在线玩家)
- **展示内容**：包含基本信息、世界状态、在线玩家、模组统计等多个二级板块。

### 👥 在线玩家 (Player List)
- **模板函数**：`format_players_markdown`
- **参数**：
    - `room_name`: `str` (房间名称)
    - `players`: `List[Dict]` (玩家列表)
- **展示内容**：列表展示玩家昵称、KU_ID 和所选角色。

### 💾 备份列表 (Backup List)
- **模板函数**：`format_backups_markdown`
- **参数**：
    - `room_name`: `str` (房间名称)
    - `backups`: `List[Dict]` (备份数据列表)
- **展示内容**：二级标题显示备份文件名，列表显示文件大小和创建时间。

### 📊 通用表格 (Table)
- **模板函数**：`format_table_markdown`
- **参数**：
    - `headers`: `List[str]` (表头)
    - `rows`: `List[List[Any]]` (行数据)
- **实现方式**：将文本表格包裹在 Markdown 的 ```text``` 代码块中。

---

## 3. 正在开发的模板 (Phase B / C)

### 🔍 存档扫描结果 (Discovery Scan)
- **用途**：展示 `dst room scan` 发现的存档。
- **参数**：
    - `clusters`: `List[ClusterInfo]` (扫描到的存档对象)
- **设计预期**：使用 Markdown 列表展示路径和健康状态。

### 🧠 AI 诊断报告 (AI Report)
- **用途**：展示 AI 对存档或模组的分析。
- **参数**：
    - `analysis_text`: `str` (AI 生成的原始 Markdown)
- **设计预期**：直接原样渲染 Markdown。
