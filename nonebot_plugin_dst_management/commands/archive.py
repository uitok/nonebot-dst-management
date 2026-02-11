"""
存档管理命令 (on_alconna)

提供存档相关命令：archive upload, archive download, archive replace, archive validate
支持房间上下文（resolve_room_id / remember_room）。
"""

from __future__ import annotations

from typing import Optional

from arclet.alconna import Alconna, Args, CommandMeta
from nonebot.adapters.onebot.v11 import Message
from nonebot.internal.adapter import Event

from nonebot_plugin_alconna import Match, AlconnaMatch, on_alconna

from ..client.api_client import DSTApiClient
from ..utils.permission import ADMIN_PERMISSION, USER_PERMISSION, check_group
from ..helpers.formatters import (
    format_error,
    format_success,
    format_info,
    format_warning,
)
from ..helpers.room_context import RoomSource, remember_room, resolve_room_id
from ..services.archive_service import ArchiveService, ArchiveInfo


# ========== 全局状态 ==========

_api_client: Optional[DSTApiClient] = None
_archive_service: Optional[ArchiveService] = None


def get_api_client() -> DSTApiClient:
    if _api_client is None:
        raise RuntimeError("API 客户端未初始化，请先调用 init() 函数")
    return _api_client


def get_service() -> ArchiveService:
    if _archive_service is None:
        raise RuntimeError("存档服务未初始化，请先调用 init() 函数")
    return _archive_service


# ========== 纯逻辑辅助函数 ==========


def _format_archive_info(info: ArchiveInfo) -> Message:
    lines = ["📦 存档解析结果", ""]
    if info.cluster_name:
        lines.append(f"房间名称：{info.cluster_name}")
    if info.game_mode:
        lines.append(f"游戏模式：{info.game_mode}")
    if info.worlds:
        lines.append(f"世界数量：{len(info.worlds)} ({' + '.join(info.worlds)})")
    lines.append(f"模组数量：{info.mod_count}")
    if info.warnings:
        lines.append("")
        lines.append("⚠️ 注意事项：")
        for item in info.warnings:
            lines.append(f"- {item}")
    return Message("\n".join(lines))


def _extract_room_and_source(raw: str) -> Optional[tuple[int, str]]:
    raw = raw.strip()
    if not raw:
        return None
    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        return None
    room_id_str, source = parts
    if not room_id_str.isdigit():
        return None
    return int(room_id_str), source.strip()


# ========== Alconna 命令定义 ==========

archive_upload_command = Alconna(
    "dst archive upload",
    Args["room_id_or_source", str, None]["source", str, None],
    meta=CommandMeta(
        description="上传存档",
        usage="/dst archive upload <房间ID> <文件URL或路径>\n或：/dst archive upload <文件URL或路径>",
        example="/dst archive upload 1 https://example.com/save.zip",
    ),
)

archive_download_command = Alconna(
    "dst archive download",
    Args["room_id", str, None],
    meta=CommandMeta(
        description="下载存档",
        usage="/dst archive download [房间ID]",
        example="/dst archive download 1",
    ),
)

archive_replace_command = Alconna(
    "dst archive replace",
    Args["room_id_or_source", str, None]["source", str, None],
    meta=CommandMeta(
        description="替换存档",
        usage="/dst archive replace <房间ID> <文件URL或路径>\n或：/dst archive replace <文件URL或路径>",
        example="/dst archive replace 1 https://example.com/save.zip",
    ),
)

archive_validate_command = Alconna(
    "dst archive validate",
    Args["source", str],
    meta=CommandMeta(
        description="验证存档",
        usage="/dst archive validate <文件URL或路径>",
        example="/dst archive validate https://example.com/save.zip",
    ),
)

# ========== on_alconna 匹配器 ==========

archive_upload_matcher = on_alconna(
    archive_upload_command, permission=ADMIN_PERMISSION, priority=10, block=True
)
archive_download_matcher = on_alconna(
    archive_download_command, permission=USER_PERMISSION, priority=10, block=True
)
archive_replace_matcher = on_alconna(
    archive_replace_command, permission=ADMIN_PERMISSION, priority=10, block=True
)
archive_validate_matcher = on_alconna(
    archive_validate_command, permission=USER_PERMISSION, priority=10, block=True
)


# ========== 命令处理函数 ==========


async def _resolve_upload_args(
    event: Event,
    first_arg: Optional[str],
    second_arg: Optional[str],
) -> Optional[tuple[int, str, Optional[object]]]:
    """解析上传/替换命令的 room_id 和 source 参数。

    返回 (room_id, source, resolved) 或 None 表示参数不足。
    """
    if not first_arg:
        return None

    # 拼接原始文本尝试解析
    raw = first_arg if second_arg is None else f"{first_arg} {second_arg}"
    parsed = _extract_room_and_source(raw)
    resolved = None

    if parsed:
        room_id, source = parsed
    else:
        resolved = await resolve_room_id(event, None)
        if resolved is None:
            return None
        room_id = int(resolved.room_id)
        source = raw.strip()

    return room_id, source, resolved


@archive_upload_matcher.handle()
async def handle_archive_upload(
    event: Event,
    room_id_or_source: Match[str] = AlconnaMatch("room_id_or_source"),
    source: Match[str] = AlconnaMatch("source"),
) -> None:
    """上传存档"""
    if not await check_group(event):
        await archive_upload_matcher.finish(format_error("当前群组未授权使用此功能"))
        return

    client = get_api_client()
    service = get_service()

    first_arg = room_id_or_source.result if room_id_or_source.available else None
    second_arg = source.result if source.available else None

    result = await _resolve_upload_args(event, first_arg, second_arg)
    if result is None:
        await archive_upload_matcher.finish(
            format_error("用法：/dst archive upload <房间ID> <文件URL或路径>\n或：/dst archive upload <文件URL或路径>")
        )
        return

    room_id, file_source, resolved = result

    if resolved and hasattr(resolved, "source"):
        if resolved.source == RoomSource.LAST:
            await archive_upload_matcher.send(format_info(f"未指定房间ID，使用上次操作的房间 {room_id}..."))
        elif resolved.source == RoomSource.DEFAULT:
            await archive_upload_matcher.send(format_info(f"未指定房间ID，使用默认房间 {room_id}..."))

    await archive_upload_matcher.send(format_info("正在准备存档文件..."))
    prepared = await service.prepare_archive(file_source)
    if not prepared.get("success"):
        await archive_upload_matcher.finish(format_error(prepared.get("error", "文件处理失败")))
        return

    archive_path = prepared["path"]
    cleanup = prepared.get("cleanup", False)

    try:
        await archive_upload_matcher.send(format_info("正在解析存档结构..."))
        validation = service.validate_archive(archive_path)
        if not validation.get("success"):
            errors = validation.get("errors") or ["存档结构验证失败"]
            await archive_upload_matcher.finish(format_error("；".join(errors)))
            return

        info = validation.get("info")
        if info:
            await archive_upload_matcher.send(_format_archive_info(info))

        ai_summary = service.analyze_with_ai(info) if info else None
        if ai_summary:
            await archive_upload_matcher.send(format_info(ai_summary))

        await archive_upload_matcher.send(format_info("正在备份当前存档..."))
        backup_result = await client.create_backup(room_id)
        if not backup_result.get("success"):
            await archive_upload_matcher.finish(format_error(f"备份失败：{backup_result.get('error')}"))
            return

        if not hasattr(client, "upload_archive"):
            await archive_upload_matcher.finish(format_error("当前 API 客户端未实现存档上传"))
            return

        await archive_upload_matcher.send(format_info("正在上传存档..."))
        upload_result = await client.upload_archive(room_id, archive_path)
        if upload_result.get("success"):
            await remember_room(event, room_id)
            await archive_upload_matcher.finish(format_success("存档上传成功"))
        else:
            await archive_upload_matcher.finish(format_error(f"存档上传失败：{upload_result.get('error')}"))

    finally:
        if cleanup:
            service.cleanup_file(archive_path)


@archive_download_matcher.handle()
async def handle_archive_download(
    event: Event,
    room_id: Match[str] = AlconnaMatch("room_id"),
) -> None:
    """下载存档"""
    if not await check_group(event):
        await archive_download_matcher.finish(format_error("当前群组未授权使用此功能"))
        return

    client = get_api_client()
    service = get_service()
    room_arg = room_id.result if room_id.available else None

    resolved = await resolve_room_id(event, room_arg)
    if resolved is None:
        if room_arg:
            await archive_download_matcher.finish(
                format_error("请提供有效的房间ID：/dst archive download <房间ID>")
            )
        else:
            await archive_download_matcher.finish(
                format_error("请提供房间ID：/dst archive download <房间ID>\n或先使用一次带房间ID的命令以锁定房间")
            )
        return

    rid = int(resolved.room_id)
    if resolved.source == RoomSource.LAST:
        await archive_download_matcher.send(format_info(f"未指定房间ID，使用上次操作的房间 {rid}..."))
    elif resolved.source == RoomSource.DEFAULT:
        await archive_download_matcher.send(format_info(f"未指定房间ID，使用默认房间 {rid}..."))

    if not hasattr(client, "download_archive"):
        await archive_download_matcher.finish(format_error("当前 API 客户端未实现存档下载"))
        return

    await archive_download_matcher.send(format_info("正在打包存档..."))
    result = await client.download_archive(rid)
    if not result.get("success"):
        await archive_download_matcher.finish(format_error(f"存档打包失败：{result.get('error')}"))
        return

    data = result.get("data") or {}
    url = data.get("url") or data.get("downloadUrl") or data.get("download_url")
    filename = data.get("filename")
    size = data.get("size")
    content = data.get("content")

    lines = ["✅ 存档已生成"]
    if filename:
        lines.append(f"- 文件名：{filename}")
    if size:
        lines.append(f"- 大小：{size}")
    if url:
        lines.append("")
        lines.append(url)
    elif content:
        temp_path = service.work_dir / (filename or f"archive_{rid}.zip")
        try:
            with open(temp_path, "wb") as f:
                f.write(content)
            lines.append("")
            lines.append(f"已保存到服务端：{temp_path}")
        except Exception:
            lines.append("\n⚠️ 存档已生成，但保存到本地失败")
    else:
        lines.append("\n⚠️ 未获取到下载链接，请联系管理员")

    await remember_room(event, rid)
    await archive_download_matcher.finish(Message("\n".join(lines)))


@archive_replace_matcher.handle()
async def handle_archive_replace(
    event: Event,
    room_id_or_source: Match[str] = AlconnaMatch("room_id_or_source"),
    source: Match[str] = AlconnaMatch("source"),
) -> None:
    """替换存档"""
    if not await check_group(event):
        await archive_replace_matcher.finish(format_error("当前群组未授权使用此功能"))
        return

    client = get_api_client()
    service = get_service()

    first_arg = room_id_or_source.result if room_id_or_source.available else None
    second_arg = source.result if source.available else None

    result = await _resolve_upload_args(event, first_arg, second_arg)
    if result is None:
        await archive_replace_matcher.finish(
            format_error("用法：/dst archive replace <房间ID> <文件URL或路径>\n或：/dst archive replace <文件URL或路径>")
        )
        return

    room_id, file_source, resolved = result

    if resolved and hasattr(resolved, "source"):
        if resolved.source == RoomSource.LAST:
            await archive_replace_matcher.send(format_info(f"未指定房间ID，使用上次操作的房间 {room_id}..."))
        elif resolved.source == RoomSource.DEFAULT:
            await archive_replace_matcher.send(format_info(f"未指定房间ID，使用默认房间 {room_id}..."))

    await archive_replace_matcher.send(format_info("正在准备存档文件..."))
    prepared = await service.prepare_archive(file_source)
    if not prepared.get("success"):
        await archive_replace_matcher.finish(format_error(prepared.get("error", "文件处理失败")))
        return

    archive_path = prepared["path"]
    cleanup = prepared.get("cleanup", False)

    try:
        await archive_replace_matcher.send(format_info("正在解析存档结构..."))
        validation = service.validate_archive(archive_path)
        if not validation.get("success"):
            errors = validation.get("errors") or ["存档结构验证失败"]
            await archive_replace_matcher.finish(format_error("；".join(errors)))
            return

        info = validation.get("info")
        if info:
            await archive_replace_matcher.send(_format_archive_info(info))

        await archive_replace_matcher.send(format_info("正在备份当前存档..."))
        backup_result = await client.create_backup(room_id)
        if not backup_result.get("success"):
            await archive_replace_matcher.finish(format_error(f"备份失败：{backup_result.get('error')}"))
            return

        if not hasattr(client, "replace_archive"):
            await archive_replace_matcher.finish(format_error("当前 API 客户端未实现存档替换"))
            return

        await archive_replace_matcher.send(format_info("正在替换存档..."))
        replace_result = await client.replace_archive(room_id, archive_path)
        if replace_result.get("success"):
            await remember_room(event, room_id)
            await archive_replace_matcher.finish(format_success("存档替换成功"))
        else:
            await archive_replace_matcher.finish(format_error(f"存档替换失败：{replace_result.get('error')}"))

    finally:
        if cleanup:
            service.cleanup_file(archive_path)


@archive_validate_matcher.handle()
async def handle_archive_validate(
    event: Event,
    source: Match[str] = AlconnaMatch("source"),
) -> None:
    """验证存档"""
    if not await check_group(event):
        await archive_validate_matcher.finish(format_error("当前群组未授权使用此功能"))
        return

    service = get_service()
    file_source = source.result if source.available else ""

    if not file_source:
        await archive_validate_matcher.finish(format_error("用法：/dst archive validate <文件URL或路径>"))
        return

    await archive_validate_matcher.send(format_info("正在准备存档文件..."))
    prepared = await service.prepare_archive(file_source)
    if not prepared.get("success"):
        await archive_validate_matcher.finish(format_error(prepared.get("error", "文件处理失败")))
        return

    archive_path = prepared["path"]
    cleanup = prepared.get("cleanup", False)

    try:
        validation = service.validate_archive(archive_path)
        if not validation.get("success"):
            errors = validation.get("errors") or ["存档结构验证失败"]
            warnings = validation.get("warnings") or []
            message = "；".join(errors)
            if warnings:
                message = f"{message}（警告：{'；'.join(warnings)}）"
            await archive_validate_matcher.finish(format_error(message))
            return

        info = validation.get("info")
        if info:
            await archive_validate_matcher.finish(_format_archive_info(info))
            return

        await archive_validate_matcher.finish(format_warning("存档解析完成，但未获取到结构信息"))

    finally:
        if cleanup:
            service.cleanup_file(archive_path)


def init(api_client: DSTApiClient) -> None:
    """初始化存档管理命令"""
    global _api_client, _archive_service
    _api_client = api_client
    _archive_service = ArchiveService()


__all__ = [
    "archive_upload_command",
    "archive_download_command",
    "archive_replace_command",
    "archive_validate_command",
    "archive_upload_matcher",
    "archive_download_matcher",
    "archive_replace_matcher",
    "archive_validate_matcher",
    "handle_archive_upload",
    "handle_archive_download",
    "handle_archive_replace",
    "handle_archive_validate",
    "init",
]
