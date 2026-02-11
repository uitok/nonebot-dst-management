"""
模组管理命令 (on_alconna)

提供模组相关命令：mod search, mod list, mod add, mod remove, mod check, mod config save
支持房间上下文（resolve_room_id / remember_room）。
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

from arclet.alconna import Alconna, Args, CommandMeta, Option
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..client.api_client import DSTApiClient
from ..ai.client import AIClient
from ..ai.mod_parser import ModConfigParser
from ..utils.permission import ADMIN_PERMISSION, USER_PERMISSION, check_group
from ..helpers.formatters import (
    format_error,
    format_success,
    format_info,
    format_warning,
)
from ..helpers.room_context import RoomSource, remember_room, resolve_room_id
from ..services.monitors.sign_monitor import get_sign_monitor


# ========== 全局状态 ==========

_api_client: Optional[DSTApiClient] = None
_ai_client: Optional[AIClient] = None
_parser: Optional[ModConfigParser] = None


def get_api_client() -> DSTApiClient:
    if _api_client is None:
        raise RuntimeError("API 客户端未初始化，请先调用 init() 函数")
    return _api_client


# ========== 纯逻辑辅助函数 ==========


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
        return Message(f'🈳 未找到包含 "{keyword}" 的模组')

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


# ========== Alconna 命令定义 ==========

mod_search_command = Alconna(
    "dst mod search",
    Args["keyword", str],
    meta=CommandMeta(
        description="搜索模组",
        usage="/dst mod search <关键词>",
        example="/dst mod search 地图",
    ),
)

mod_list_command = Alconna(
    "dst mod list",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="查看已安装模组",
        usage="/dst mod list [房间ID]",
        example="/dst mod list 1",
    ),
)

mod_add_command = Alconna(
    "dst mod add",
    Args["room_id", str]["world_id", str]["mod_id", str],
    meta=CommandMeta(
        description="添加模组",
        usage="/dst mod add <房间ID> <世界ID> <模组ID>",
        example="/dst mod add 1 1 workshop-123456",
    ),
)

mod_remove_command = Alconna(
    "dst mod remove",
    Args["room_id", str]["world_id", str]["mod_id", str],
    meta=CommandMeta(
        description="移除模组",
        usage="/dst mod remove <房间ID> <世界ID> <模组ID>",
        example="/dst mod remove 1 1 workshop-123456",
    ),
)

mod_check_command = Alconna(
    "dst mod check",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="检测模组冲突",
        usage="/dst mod check [房间ID]",
        example="/dst mod check 1",
    ),
)

mod_config_save_command = Alconna(
    "dst mod config save",
    Args["room_id", str]["world_id", str],
    meta=CommandMeta(
        description="保存优化模组配置",
        usage="/dst mod config save <房间ID> <世界ID>",
        example="/dst mod config save 1 1",
    ),
)

# ========== on_alconna 匹配器 ==========

mod_search_matcher = on_alconna(
    mod_search_command, permission=USER_PERMISSION, priority=10, block=True
)
mod_list_matcher = on_alconna(
    mod_list_command, permission=USER_PERMISSION, priority=10, block=True
)
mod_add_matcher = on_alconna(
    mod_add_command, permission=ADMIN_PERMISSION, priority=10, block=True
)
mod_remove_matcher = on_alconna(
    mod_remove_command, permission=ADMIN_PERMISSION, priority=10, block=True
)
mod_check_matcher = on_alconna(
    mod_check_command, permission=USER_PERMISSION, priority=10, block=True
)
mod_config_save_matcher = on_alconna(
    mod_config_save_command, permission=ADMIN_PERMISSION, priority=10, block=True
)


# ========== 命令处理函数 ==========


@mod_search_matcher.handle()
async def handle_mod_search(
    event: Event,
    keyword: Match[str] = AlconnaMatch("keyword"),
) -> None:
    """搜索模组"""
    if not await check_group(event):
        await mod_search_matcher.finish(format_error("当前群组未授权使用此功能"))
        return

    client = get_api_client()
    kw = keyword.result if keyword.available else ""
    if not kw:
        await mod_search_matcher.finish(format_error("请提供搜索关键词：/dst mod search <关键词>"))
        return

    if not hasattr(client, "search_mod"):
        await mod_search_matcher.finish(format_error("当前 API 客户端未实现模组搜索"))
        return

    await mod_search_matcher.send(format_info(f"正在搜索模组：{kw}..."))
    result = await client.search_mod("text", kw)

    if not result.get("success"):
        await mod_search_matcher.finish(format_error(f"搜索失败：{result.get('error')}"))
        return

    mods = result.get("data") or []
    await mod_search_matcher.finish(_format_mod_search_results(mods, kw))


@mod_list_matcher.handle()
async def handle_mod_list(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """查看已安装模组"""
    if not await check_group(event):
        await mod_list_matcher.finish(format_error("当前群组未授权使用此功能"))
        return

    client = get_api_client()
    room_arg = room_id.result if room_id.available else None

    resolved = await resolve_room_id(event, room_arg)
    if resolved is None:
        if room_arg:
            await mod_list_matcher.finish(format_error("请提供有效的房间ID：/dst mod list <房间ID>"))
        else:
            await mod_list_matcher.finish(
                format_error("请提供房间ID：/dst mod list <房间ID>\n或先使用一次带房间ID的命令以锁定房间")
            )
        return

    rid = int(resolved.room_id)
    if resolved.source == RoomSource.LAST:
        await mod_list_matcher.send(format_info(f"未指定房间ID，使用上次操作的房间 {rid}..."))
    elif resolved.source == RoomSource.DEFAULT:
        await mod_list_matcher.send(format_info(f"未指定房间ID，使用默认房间 {rid}..."))

    room_result = await client.get_room_info(rid)
    if not room_result.get("success"):
        await mod_list_matcher.finish(format_error(f"获取房间信息失败：{room_result.get('error')}"))
        return

    # 触发签到奖励检查
    monitor = get_sign_monitor()
    if monitor:
        try:
            await monitor.check_room_pending_rewards(rid)
        except Exception:
            pass

    mod_data = room_result.get("data", {}).get("modData", "")
    enabled, disabled = _parse_mod_data(mod_data)
    await remember_room(event, rid)
    await mod_list_matcher.finish(_format_mod_list(rid, enabled, disabled))


@mod_add_matcher.handle()
async def handle_mod_add(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
    world_id: Match[str] = AlconnaMatch("world_id"),
    mod_id: Match[str] = AlconnaMatch("mod_id"),
) -> None:
    """添加模组"""
    client = get_api_client()

    room_id_str = room_id.result if room_id.available else ""
    world_id_str = world_id.result if world_id.available else ""
    mod_id_str = mod_id.result if mod_id.available else ""

    if not room_id_str.isdigit() or not world_id_str.isdigit():
        await mod_add_matcher.finish(format_error("请提供有效的房间ID和世界ID"))
        return

    rid = int(room_id_str)
    wid = int(world_id_str)
    _, normalized_mod_id = _normalize_mod_id(mod_id_str)

    required_methods = ["download_mod", "get_mod_setting_struct", "update_mod_setting", "enable_mod"]
    missing = [name for name in required_methods if not hasattr(client, name)]
    if missing:
        await mod_add_matcher.finish(format_error(f"当前 API 客户端未实现模组操作：{', '.join(missing)}"))
        return

    await mod_add_matcher.send(format_info(f"正在下载模组 {normalized_mod_id}..."))
    result = await client.download_mod(normalized_mod_id)
    if not result.get("success"):
        await mod_add_matcher.finish(format_error(f"下载失败：{result.get('error')}"))
        return

    await mod_add_matcher.send(format_info("正在获取模组默认配置..."))
    setting_result = await client.get_mod_setting_struct(normalized_mod_id)
    if not setting_result.get("success"):
        await mod_add_matcher.finish(format_error(f"获取配置失败：{setting_result.get('error')}"))
        return

    await mod_add_matcher.send(format_info("正在应用默认配置..."))
    update_result = await client.update_mod_setting(
        rid, wid, normalized_mod_id, setting_result.get("data")
    )
    if not update_result.get("success"):
        await mod_add_matcher.finish(format_error(f"配置失败：{update_result.get('error')}"))
        return

    await mod_add_matcher.send(format_info("正在启用模组..."))
    enable_result = await client.enable_mod(rid, wid, normalized_mod_id)
    if not enable_result.get("success"):
        await mod_add_matcher.finish(format_error(f"启用失败：{enable_result.get('error')}"))
        return

    await mod_add_matcher.finish(format_success("模组添加成功，房间重启后生效"))


@mod_remove_matcher.handle()
async def handle_mod_remove(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
    world_id: Match[str] = AlconnaMatch("world_id"),
    mod_id: Match[str] = AlconnaMatch("mod_id"),
) -> None:
    """移除模组"""
    client = get_api_client()

    room_id_str = room_id.result if room_id.available else ""
    world_id_str = world_id.result if world_id.available else ""
    mod_id_str = mod_id.result if mod_id.available else ""

    if not room_id_str.isdigit() or not world_id_str.isdigit():
        await mod_remove_matcher.finish(format_error("请提供有效的房间ID和世界ID"))
        return

    rid = int(room_id_str)
    wid = int(world_id_str)
    _, normalized_mod_id = _normalize_mod_id(mod_id_str)

    if not hasattr(client, "disable_mod"):
        await mod_remove_matcher.finish(format_error("当前 API 客户端未实现模组移除"))
        return

    await mod_remove_matcher.send(format_info(f"正在移除模组 {normalized_mod_id}..."))
    result = await client.disable_mod(rid, wid, normalized_mod_id)

    if result.get("success"):
        await mod_remove_matcher.finish(format_success("模组移除成功，房间重启后生效"))
    else:
        await mod_remove_matcher.finish(format_error(f"移除失败：{result.get('error')}"))


@mod_check_matcher.handle()
async def handle_mod_check(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """检测模组冲突"""
    if not await check_group(event):
        await mod_check_matcher.finish(format_error("当前群组未授权使用此功能"))
        return

    client = get_api_client()
    room_arg = room_id.result if room_id.available else None

    resolved = await resolve_room_id(event, room_arg)
    if resolved is None:
        if room_arg:
            await mod_check_matcher.finish(format_error("请提供有效的房间ID：/dst mod check <房间ID>"))
        else:
            await mod_check_matcher.finish(
                format_error("请提供房间ID：/dst mod check <房间ID>\n或先使用一次带房间ID的命令以锁定房间")
            )
        return

    rid = int(resolved.room_id)
    if resolved.source == RoomSource.LAST:
        await mod_check_matcher.send(format_info(f"未指定房间ID，使用上次操作的房间 {rid}..."))
    elif resolved.source == RoomSource.DEFAULT:
        await mod_check_matcher.send(format_info(f"未指定房间ID，使用默认房间 {rid}..."))

    room_result = await client.get_room_info(rid)
    if not room_result.get("success"):
        await mod_check_matcher.finish(format_error(f"获取房间信息失败：{room_result.get('error')}"))
        return

    mod_data = room_result.get("data", {}).get("modData", "")
    enabled, disabled = _parse_mod_data(mod_data)
    all_mods = enabled + disabled

    if not all_mods:
        await mod_check_matcher.finish(format_info("当前房间未安装任何模组"))
        return

    counts: Dict[str, int] = {}
    for mid in re.findall(r"workshop-\d+", mod_data):
        counts[mid] = counts.get(mid, 0) + 1

    duplicates = [mid for mid, count in counts.items() if count > 1]

    lines = ["🔍 模组分析报告", ""]
    lines.append(f"已启用：{len(enabled)} 个 | 已禁用：{len(disabled)} 个")

    if duplicates:
        lines.append("")
        lines.append(format_warning(f"发现 {len(duplicates)} 个重复条目").extract_plain_text())
        for mid in duplicates:
            lines.append(f"- {mid} (出现 {counts.get(mid)} 次)")
    else:
        lines.append("")
        lines.append("✅ 未发现重复模组条目")

    lines.append("")
    lines.append("💡 如需生效，请重启房间")
    await remember_room(event, rid)
    await mod_check_matcher.finish(Message("\n".join(lines)))


@mod_config_save_matcher.handle()
async def handle_mod_config_save(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
    world_id: Match[str] = AlconnaMatch("world_id"),
) -> None:
    """保存优化模组配置"""
    if not await check_group(event):
        await mod_config_save_matcher.finish(format_error("当前群组未授权使用此功能"))
        return

    client = get_api_client()

    room_id_str = room_id.result if room_id.available else ""
    world_id_str = world_id.result if world_id.available else ""

    if not room_id_str.isdigit():
        await mod_config_save_matcher.finish(format_error("请提供有效的房间ID"))
        return

    if _parser is None:
        await mod_config_save_matcher.finish(format_error("AI 模组解析器未初始化"))
        return

    rid = int(room_id_str)
    await mod_config_save_matcher.send(format_info("正在生成优化配置..."))

    optimized = _parser.get_cached_optimized(rid, world_id_str)
    if not optimized:
        try:
            result = await _parser.parse_mod_config(rid, world_id_str)
            optimized = result.get("optimized_config")
        except Exception as exc:
            await mod_config_save_matcher.finish(format_error(f"生成优化配置失败：{exc}"))
            return

    if not optimized:
        await mod_config_save_matcher.finish(format_error("未生成优化配置内容"))
        return

    save_handler = None
    for name in ("save_mod_config", "update_modoverrides", "update_mod_config", "save_modoverrides"):
        if hasattr(client, name):
            save_handler = getattr(client, name)
            break

    if save_handler is None:
        await mod_config_save_matcher.finish(format_error("当前 API 客户端未实现配置保存"))
        return

    await mod_config_save_matcher.send(format_info("正在保存优化配置..."))
    result = await save_handler(rid, world_id_str, optimized)
    if result.get("success"):
        await mod_config_save_matcher.finish(format_success("配置保存成功，重启后生效"))
    else:
        await mod_config_save_matcher.finish(format_error(f"保存失败：{result.get('error')}"))


def init(api_client: DSTApiClient, ai_client: Optional[AIClient] = None) -> None:
    """初始化模组管理命令"""
    global _api_client, _ai_client, _parser
    _api_client = api_client
    _ai_client = ai_client
    _parser = ModConfigParser(api_client, ai_client) if ai_client else None


__all__ = [
    "mod_search_command",
    "mod_list_command",
    "mod_add_command",
    "mod_remove_command",
    "mod_check_command",
    "mod_config_save_command",
    "mod_search_matcher",
    "mod_list_matcher",
    "mod_add_matcher",
    "mod_remove_matcher",
    "mod_check_matcher",
    "mod_config_save_matcher",
    "handle_mod_search",
    "handle_mod_list",
    "handle_mod_add",
    "handle_mod_remove",
    "handle_mod_check",
    "handle_mod_config_save",
    "init",
]
