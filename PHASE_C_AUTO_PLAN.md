# nonebot-plugin-dst-management 优化计划 - Phase C (Auto) 开发计划

## 目标
实现房间与存档的自动扫描功能，简化配置流程，降低新用户的上手门槛。

## 详细任务清单

### 1. 自动扫描引擎 (Discovery Engine)
- **路径探测**：在 `utils/path.py` (或新文件) 中实现递归扫描逻辑，自动识别包含 `cluster.ini` 和 `server.ini` 的目录。
- **元数据提取**：从 `cluster.ini` 中提取房间名（`cluster_name`），从 `cluster_token.txt` 中提取令牌（如果存在）。
- **存档识别**：自动识别 Master/Caves 架构。

### 2. 配置向导 (Setup Wizard)
- **交互式配置**：实现 `dst setup` 指令，通过序号选择扫描到的房间，自动将其加入配置文件。
- **重复检查**：防止将已有的房间重复添加。

### 3. 后端服务增强
- **ApiClient 增强**：确保 ApiClient 能动态适配新扫描到的房间路径。
- **默认配置生成**：如果没有配置文件，启动时尝试执行一次静默扫描并提醒用户。

### 4. UI 适配
- **扫描结果展示**：使用 Phase A 中建立的 `format_table` 展示扫描到的可用房间列表。

## 实施步骤
1. **实现目录遍历与 ini 解析逻辑**。
2. **开发 `dst setup` (或 `dst room scan`) 指令**。
3. **集成到现有的 `RoomManager` 逻辑中**。
4. **编写单元测试，模拟各种复杂的目录结构**。
