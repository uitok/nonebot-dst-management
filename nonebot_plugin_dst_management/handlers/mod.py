"""
模组管理命令处理器

处理模组相关的命令：search, list, add, remove, check
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Tuple, Optional

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg

from ..client.api_client import DSTApiClient
from ..ai.client import AIClient
from ..ai.mod_parser import ModConfigParser
from ..services.monitors.sign_monitor import get_sign_monitor
from ..utils.permission import check_admin, check_group
from ..helpers.formatters import (
    format_error,
    format_success,
    format_info,
    format_warning,
)


def _normalize_mod_id(mod_id: str) -> Tuple[str, str]:
    """标准化模组 ID，返回 (纯数字, workshop-前缀)"""
    mod_id = mod_id.strip()
    if mod_id.startswith("workshop-"):
        numeric = mod_id.split("-", 1)[1]
    else:
        numeric = mod_id
    return numeric, f"workshop-{numeric}"


def _parse_mod_data(mod_data: str) -> Tuple[List[str], List[str]]:
    """解析 modData 内容，返回 (enabled, disabled) 模组列表。"""
    enabled: List[str] = []
    disabled: List[str] = []

    if not mod_data:
        return enabled, disabled

    seen = set()

    def add_mod(mod_id: str, is_enabled: bool) -> None:
        if mod_id in seen:
            return
        seen.add(mod_id)
        if is_enabled:
            enabled.append(mod_id)
        else:
            disabled.append(mod_id)

    # 1) 尝试解析 JSON
    try:
        data = json.loads(mod_data)
        if isinstance(data, dict):
            for key, value in data.items():
                if not isinstance(key, str) or not key.startswith("workshop-"):
                    continue
                is_enabled = True
                if isinstance(value, dict) and "enabled" in value:
                    is_enabled = bool(value.get("enabled"))
                add_mod(key, is_enabled)
        elif isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                mod_id = item.get("id") or item.get("mod_id") or item.get("modId")
                if not mod_id:
                    continue
                mod_id = str(mod_id)
                if not mod_id.startswith("workshop-"):
                    mod_id = f"workshop-{mod_id}"
                is_enabled = bool(item.get("enabled", True))
                add_mod(mod_id, is_enabled)
    except Exception:
        pass

    # 2) 尝试解析 Lua 风格 modoverrides
    lua_pattern = re.compile(
        r'\["(workshop-\d+)"\]\s*=\s*\{[^}]*?enabled\s*=\s*(true|false)',
        re.IGNORECASE | re.DOTALL,
    )
    for match in lua_pattern.finditer(mod_data):
        mod_id = match.group(1)
        is_enabled = match.group(2).lower() == "true"
        add_mod(mod_id, is_enabled)

    # 3) 兜底：仅提取 workshop- 前缀 ID
    if not enabled and not disabled:
        for mod_id in re.findall(r"workshop-\d+", mod_data):
            add_mod(mod_id, True)

    return enabled, disabled


def _format_mod_search_results(mods: List[Dict], keyword: str) -> Message:
    if not mods:
        return Message(f"🈳 未找到包含 \"{keyword}\" 的模组")

    lines = [f"🧩 模组搜索结果：{keyword}", ""]
    for idx, mod in enumerate(mods[:10], 1):
        name = mod.get("name") or mod.get("title") or "未知模组"
        mod_id = mod.get("id") or mod.get("modId") or mod.get("mod_id") or "未知"
        author = mod.get("author") or mod.get("creator") or "未知"
        subs = mod.get("subscriptions") or mod.get("subscribers") or mod.get("subs")
        lines.append(f"{idx}. {name}")
        lines.append(f"   ID: {mod_id}")
        lines.append(f"   作者: {author}")
        if subs is not None:
            lines.append(f"   订阅: {subs}")
        lines.append("")

    lines.append("💡 使用 /dst mod add <房间ID> <世界ID> <模组ID> 添加模组")
    return Message("\n".join(lines))


def _format_mod_list(room_id: int, enabled: List[str], disabled: List[str]) -> Message:
    lines = [f"🧩 已安装模组 (房间 {room_id})", ""]

    if not enabled and not disabled:
        lines.append("🈳 暂无模组")
        return Message("\n".join(lines))

    if enabled:
        lines.append(f"✅ 已启用 ({len(enabled)} 个)")
        for idx, mod_id in enumerate(enabled, 1):
            lines.append(f"{idx}. {mod_id}")
        lines.append("")

    if disabled:
        lines.append(f"⛔ 已禁用 ({len(disabled)} 个)")
        for idx, mod_id in enumerate(disabled, 1):
            lines.append(f"{idx}. {mod_id}")

    return Message("\n".join(lines))


def init(api_client: DSTApiClient, ai_client: Optional[AIClient] = None):
    """
    初始化模组管理命令
    
    Args:
        api_client: DMP API 客户端实例
        ai_client: AI 客户端实例（可选）
    """

    parser = ModConfigParser(api_client, ai_client) if ai_client else None

    # ========== 搜索模组 ==========
    mod_search = on_command(
        "dst mod search",
        aliases={"dst 模组搜索", "dst 搜索模组", "dst 找模组"},
        priority=10,
        block=True
    )

    @mod_search.handle()
    async def handle_mod_search(event: MessageEvent, args: Message = CommandArg()):
        # 检查群组权限
        if not await check_group(event):
            await mod_search.finish(format_error("当前群组未授权使用此功能"))
            return

        keyword = args.extract_plain_text().strip()
        if not keyword:
            await mod_search.finish(format_error("请提供搜索关键词：/dst mod search <关键词>"))
            return

        if not hasattr(api_client, "search_mod"):
            await mod_search.finish(format_error("当前 API 客户端未实现模组搜索"))
            return

        await mod_search.send(format_info(f"正在搜索模组：{keyword}..."))
        result = await api_client.search_mod("text", keyword)

        if not result.get("success"):
            await mod_search.finish(format_error(f"搜索失败：{result.get('error')}"))
            return

        mods = result.get("data") or []
        message = _format_mod_search_results(mods, keyword)
        await mod_search.finish(message)

    # ========== 查看已安装模组 ==========
    mod_list = on_command(
        "dst mod list",
        aliases={"dst 模组列表", "dst 已安装模组", "dst 已装模组"},
        priority=10,
        block=True
    )

    @mod_list.handle()
    async def handle_mod_list(event: MessageEvent, args: Message = CommandArg()):
        # 检查群组权限
        if not await check_group(event):
            await mod_list.finish(format_error("当前群组未授权使用此功能"))
            return

        room_id_str = args.extract_plain_text().strip()
        if not room_id_str.isdigit():
            await mod_list.finish(format_error("请提供有效的房间ID：/dst mod list <房间ID>"))
            return

        room_id = int(room_id_str)
        room_result = await api_client.get_room_info(room_id)
        if not room_result.get("success"):
            await mod_list.finish(format_error(f"获取房间信息失败：{room_result.get('error')}"))
            return

        # ✨ 触发签到奖励检查
        monitor = get_sign_monitor()
        if monitor:
            try:
                await monitor.check_room_pending_rewards(room_id)
            except Exception:
                pass

        mod_data = room_result.get("data", {}).get("modData", "")
        enabled, disabled = _parse_mod_data(mod_data)
        await mod_list.finish(_format_mod_list(room_id, enabled, disabled))

    # ========== 添加模组 ==========
    mod_add = on_command(
        "dst mod add",
        aliases={"dst 添加模组", "dst 安装模组", "dst 装模组"},
        priority=10,
        block=True
    )

    @mod_add.handle()
    async def handle_mod_add(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        # 检查管理员权限
        if not await check_admin(bot, event):
            await mod_add.finish(format_error("只有管理员才能执行此操作"))
            return

        arg_parts = args.extract_plain_text().strip().split()
        if len(arg_parts) < 3:
            await mod_add.finish(format_error("用法：/dst mod add <房间ID> <世界ID> <模组ID>"))
            return

        room_id_str, world_id_str, mod_id_str = arg_parts[:3]
        if not room_id_str.isdigit() or not world_id_str.isdigit():
            await mod_add.finish(format_error("请提供有效的房间ID和世界ID"))
            return

        room_id = int(room_id_str)
        world_id = int(world_id_str)
        _, mod_id = _normalize_mod_id(mod_id_str)

        # 必要能力检查
        required_methods = ["download_mod", "get_mod_setting_struct", "update_mod_setting", "enable_mod"]
        missing = [name for name in required_methods if not hasattr(api_client, name)]
        if missing:
            await mod_add.finish(format_error(f"当前 API 客户端未实现模组操作：{', '.join(missing)}"))
            return

        await mod_add.send(format_info(f"正在下载模组 {mod_id}..."))
        result = await api_client.download_mod(mod_id)
        if not result.get("success"):
            await mod_add.finish(format_error(f"下载失败：{result.get('error')}"))
            return

        await mod_add.send(format_info("正在获取模组默认配置..."))
        setting_result = await api_client.get_mod_setting_struct(mod_id)
        if not setting_result.get("success"):
            await mod_add.finish(format_error(f"获取配置失败：{setting_result.get('error')}"))
            return

        await mod_add.send(format_info("正在应用默认配置..."))
        update_result = await api_client.update_mod_setting(
            room_id,
            world_id,
            mod_id,
            setting_result.get("data")
        )
        if not update_result.get("success"):
            await mod_add.finish(format_error(f"配置失败：{update_result.get('error')}"))
            return

        await mod_add.send(format_info("正在启用模组..."))
        enable_result = await api_client.enable_mod(room_id, world_id, mod_id)
        if not enable_result.get("success"):
            await mod_add.finish(format_error(f"启用失败：{enable_result.get('error')}"))
            return

        await mod_add.finish(format_success("模组添加成功，房间重启后生效"))

    # ========== 删除模组 ==========
    mod_remove = on_command(
        "dst mod remove",
        aliases={"dst 移除模组", "dst 删除模组", "dst 卸载模组"},
        priority=10,
        block=True
    )

    @mod_remove.handle()
    async def handle_mod_remove(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        # 检查管理员权限
        if not await check_admin(bot, event):
            await mod_remove.finish(format_error("只有管理员才能执行此操作"))
            return

        arg_parts = args.extract_plain_text().strip().split()
        if len(arg_parts) < 3:
            await mod_remove.finish(format_error("用法：/dst mod remove <房间ID> <世界ID> <模组ID>"))
            return

        room_id_str, world_id_str, mod_id_str = arg_parts[:3]
        if not room_id_str.isdigit() or not world_id_str.isdigit():
            await mod_remove.finish(format_error("请提供有效的房间ID和世界ID"))
            return

        room_id = int(room_id_str)
        world_id = int(world_id_str)
        _, mod_id = _normalize_mod_id(mod_id_str)

        if not hasattr(api_client, "disable_mod"):
            await mod_remove.finish(format_error("当前 API 客户端未实现模组移除"))
            return

        await mod_remove.send(format_info(f"正在移除模组 {mod_id}..."))
        result = await api_client.disable_mod(room_id, world_id, mod_id)

        if result.get("success"):
            await mod_remove.finish(format_success("模组移除成功，房间重启后生效"))
        else:
            await mod_remove.finish(format_error(f"移除失败：{result.get('error')}"))

    # ========== 检测模组冲突 ==========
    mod_check = on_command(
        "dst mod check",
        aliases={"dst 检测模组", "dst 模组检测", "dst 冲突检测"},
        priority=10,
        block=True
    )

    @mod_check.handle()
    async def handle_mod_check(event: MessageEvent, args: Message = CommandArg()):
        # 检查群组权限
        if not await check_group(event):
            await mod_check.finish(format_error("当前群组未授权使用此功能"))
            return

        room_id_str = args.extract_plain_text().strip()
        if not room_id_str.isdigit():
            await mod_check.finish(format_error("请提供有效的房间ID：/dst mod check <房间ID>"))
            return

        room_id = int(room_id_str)
        room_result = await api_client.get_room_info(room_id)
        if not room_result.get("success"):
            await mod_check.finish(format_error(f"获取房间信息失败：{room_result.get('error')}"))
            return

        mod_data = room_result.get("data", {}).get("modData", "")
        enabled, disabled = _parse_mod_data(mod_data)
        all_mods = enabled + disabled

        if not all_mods:
            await mod_check.finish(format_info("当前房间未安装任何模组"))
            return

        counts: Dict[str, int] = {}
        for mod_id in re.findall(r"workshop-\d+", mod_data):
            counts[mod_id] = counts.get(mod_id, 0) + 1

        duplicates = [mod_id for mod_id, count in counts.items() if count > 1]

        lines = ["🔍 模组分析报告", ""]
        lines.append(f"已启用：{len(enabled)} 个 | 已禁用：{len(disabled)} 个")

        if duplicates:
            lines.append("")
            lines.append(format_warning(f"发现 {len(duplicates)} 个重复条目").extract_plain_text())
            for mod_id in duplicates:
                lines.append(f"- {mod_id} (出现 {counts.get(mod_id)} 次)")
        else:
            lines.append("")
            lines.append("✅ 未发现重复模组条目")

        lines.append("")
        lines.append("💡 如需生效，请重启房间")
        await mod_check.finish(Message("\n".join(lines)))

    # ========== 保存模组配置 ==========
    mod_config_save = on_command("dst mod config save", priority=10, block=True)

    @mod_config_save.handle()
    async def handle_mod_config_save(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await mod_config_save.finish(format_error("当前群组未授权使用此功能"))
            return
        if not await check_admin(bot, event):
            await mod_config_save.finish(format_error("只有管理员才能执行此操作"))
            return

        raw = args.extract_plain_text().strip()
        if not raw:
            await mod_config_save.finish(
                format_error("用法：/dst mod config save <房间ID> <世界ID> --optimized")
            )
            return

        parts = raw.split()
        if len(parts) < 3:
            await mod_config_save.finish(
                format_error("用法：/dst mod config save <房间ID> <世界ID> --optimized")
            )
            return

        room_id_str, world_id, flag = parts[0], parts[1], parts[2]
        if not room_id_str.isdigit():
            await mod_config_save.finish(format_error("请提供有效的房间ID"))
            return
        if flag != "--optimized":
            await mod_config_save.finish(format_error("当前仅支持 --optimized 参数"))
            return

        if parser is None:
            await mod_config_save.finish(format_error("AI 模组解析器未初始化"))
            return

        room_id = int(room_id_str)
        await mod_config_save.send(format_info("正在生成优化配置..."))

        optimized = parser.get_cached_optimized(room_id, world_id)
        if not optimized:
            try:
                result = await parser.parse_mod_config(room_id, world_id)
                optimized = result.get("optimized_config")
            except Exception as exc:
                await mod_config_save.finish(format_error(f"生成优化配置失败：{exc}"))
                return

        if not optimized:
            await mod_config_save.finish(format_error("未生成优化配置内容"))
            return

        save_handler = None
        for name in ("save_mod_config", "update_modoverrides", "update_mod_config", "save_modoverrides"):
            if hasattr(api_client, name):
                save_handler = getattr(api_client, name)
                break

        if save_handler is None:
            await mod_config_save.finish(format_error("当前 API 客户端未实现配置保存"))
            return

        await mod_config_save.send(format_info("正在保存优化配置..."))
        result = await save_handler(room_id, world_id, optimized)
        if result.get("success"):
            await mod_config_save.finish(format_success("配置保存成功，重启后生效"))
        else:
            await mod_config_save.finish(format_error(f"保存失败：{result.get('error')}"))
