# nonebot-plugin-dst-management 优化计划 - Phase A (UI) 开发计划 (v2.2)

## 目标
重构帮助菜单与反馈系统，通过 **Emoji 视觉引导** 和 **动态切换的展示模式**（官方 QQ 默认 Markdown，OneBot 强制文本），提供极具灵活性的交互体验。

## 详细任务清单

### 1. 动态展示逻辑 (Dynamic Rendering Logic)
- **平台感知与偏好**：
    - **OneBot (v11)**：强制使用 `text` 模式。用户尝试切换 `markdown` 时，提示“当前平台不支持 Markdown，已锁定为文本模式 ⚠️”。
    - **官方 QQ (qq)**：默认使用 `markdown` 模式。支持用户通过命令切换为 `text` 模式。
- **渲染器分流**：在 `helpers/formatters.py` 中实现根据 `(bot_type, user_pref)` 返回对应内容。

### 2. UI 偏好管理 (UI Preference Management)
- **新增配置指令**：`dst config ui <text|markdown>`。
    - 逻辑：保存用户的 UI 展示偏好。
    - 在 OneBot 下，拦截并提示不支持。
- **状态存储**：将 UI 偏好持久化（可存储在现有数据库或配置中）。

### 3. 视觉增强 (Visuals)
- **Emoji 文本版**：使用 🏠, 👥, 📦, ⚙️ 等 Emoji 进行分级。
- **Markdown 版**：利用标题、粗体、列表实现结构化布局。
- **状态图标统一**：🟢/🔴/⚠️ 等状态全局一致。

## 实施步骤
1. **重构 `helpers/formatters.py`**：支持 `render(template_name, mode='text', **kwargs)`。
2. **实现适配器与偏好检测逻辑**。
3. **新增 `dst config ui` 命令及错误拦截**。
4. **更新所有 Handler 以支持动态渲染内容**。
