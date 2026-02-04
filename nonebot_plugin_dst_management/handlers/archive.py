"""
存档管理命令处理器

处理存档相关命令：archive upload, download, replace, validate
"""

from __future__ import annotations

from typing import Optional

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message
from nonebot.params import CommandArg

from ..client.api_client import DSTApiClient
from ..services.archive_service import ArchiveService, ArchiveInfo
from ..utils.permission import check_admin, check_group
from ..utils.formatter import (
    format_error,
    format_success,
    format_info,
    format_warning,
)


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


def init(api_client: DSTApiClient):
    """
    初始化存档管理命令

    Args:
        api_client: DMP API 客户端实例
    """

    service = ArchiveService()

    # ========== 上传存档 ==========
    archive_upload = on_command("dst archive upload", priority=10, block=True)

    @archive_upload.handle()
    async def handle_archive_upload(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await archive_upload.finish(format_error("当前群组未授权使用此功能"))
            return
        if not await check_admin(bot, event):
            await archive_upload.finish(format_error("只有管理员才能执行此操作"))
            return

        parsed = _extract_room_and_source(args.extract_plain_text())
        if not parsed:
            await archive_upload.finish(format_error("用法：/dst archive upload <房间ID> <文件URL或文件路径>"))
            return

        room_id, source = parsed

        await archive_upload.send(format_info("正在准备存档文件..."))
        prepared = await service.prepare_archive(source)
        if not prepared.get("success"):
            await archive_upload.finish(format_error(prepared.get("error", "文件处理失败")))
            return

        archive_path = prepared["path"]
        cleanup = prepared.get("cleanup", False)

        try:
            await archive_upload.send(format_info("正在解析存档结构..."))
            validation = service.validate_archive(archive_path)
            if not validation.get("success"):
                errors = validation.get("errors") or ["存档结构验证失败"]
                await archive_upload.finish(format_error("；".join(errors)))
                return

            info = validation.get("info")
            if info:
                await archive_upload.send(_format_archive_info(info))

            ai_summary = service.analyze_with_ai(info) if info else None
            if ai_summary:
                await archive_upload.send(format_info(ai_summary))

            await archive_upload.send(format_info("正在备份当前存档..."))
            backup_result = await api_client.create_backup(room_id)
            if not backup_result.get("success"):
                await archive_upload.finish(format_error(f"备份失败：{backup_result.get('error')}"))
                return

            if not hasattr(api_client, "upload_archive"):
                await archive_upload.finish(format_error("当前 API 客户端未实现存档上传"))
                return

            await archive_upload.send(format_info("正在上传存档..."))
            result = await api_client.upload_archive(room_id, archive_path)
            if result.get("success"):
                await archive_upload.finish(format_success("存档上传成功"))
            else:
                await archive_upload.finish(format_error(f"存档上传失败：{result.get('error')}"))

        finally:
            if cleanup:
                service.cleanup_file(archive_path)

    # ========== 下载存档 ==========
    archive_download = on_command("dst archive download", priority=10, block=True)

    @archive_download.handle()
    async def handle_archive_download(event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await archive_download.finish(format_error("当前群组未授权使用此功能"))
            return

        room_id_str = args.extract_plain_text().strip()
        if not room_id_str.isdigit():
            await archive_download.finish(format_error("请提供有效的房间ID：/dst archive download <房间ID>"))
            return

        room_id = int(room_id_str)

        if not hasattr(api_client, "download_archive"):
            await archive_download.finish(format_error("当前 API 客户端未实现存档下载"))
            return

        await archive_download.send(format_info("正在打包存档..."))
        result = await api_client.download_archive(room_id)
        if not result.get("success"):
            await archive_download.finish(format_error(f"存档打包失败：{result.get('error')}"))
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
            temp_path = service.work_dir / (filename or f"archive_{room_id}.zip")
            try:
                with open(temp_path, "wb") as f:
                    f.write(content)
                lines.append("")
                lines.append(f"已保存到服务端：{temp_path}")
            except Exception:
                lines.append("\n⚠️ 存档已生成，但保存到本地失败")
        else:
            lines.append("\n⚠️ 未获取到下载链接，请联系管理员")

        await archive_download.finish(Message("\n".join(lines)))

    # ========== 替换存档 ==========
    archive_replace = on_command("dst archive replace", priority=10, block=True)

    @archive_replace.handle()
    async def handle_archive_replace(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await archive_replace.finish(format_error("当前群组未授权使用此功能"))
            return
        if not await check_admin(bot, event):
            await archive_replace.finish(format_error("只有管理员才能执行此操作"))
            return

        parsed = _extract_room_and_source(args.extract_plain_text())
        if not parsed:
            await archive_replace.finish(format_error("用法：/dst archive replace <房间ID> <文件URL或文件路径>"))
            return

        room_id, source = parsed

        await archive_replace.send(format_info("正在准备存档文件..."))
        prepared = await service.prepare_archive(source)
        if not prepared.get("success"):
            await archive_replace.finish(format_error(prepared.get("error", "文件处理失败")))
            return

        archive_path = prepared["path"]
        cleanup = prepared.get("cleanup", False)

        try:
            await archive_replace.send(format_info("正在解析存档结构..."))
            validation = service.validate_archive(archive_path)
            if not validation.get("success"):
                errors = validation.get("errors") or ["存档结构验证失败"]
                await archive_replace.finish(format_error("；".join(errors)))
                return

            info = validation.get("info")
            if info:
                await archive_replace.send(_format_archive_info(info))

            await archive_replace.send(format_info("正在备份当前存档..."))
            backup_result = await api_client.create_backup(room_id)
            if not backup_result.get("success"):
                await archive_replace.finish(format_error(f"备份失败：{backup_result.get('error')}"))
                return

            if not hasattr(api_client, "replace_archive"):
                await archive_replace.finish(format_error("当前 API 客户端未实现存档替换"))
                return

            await archive_replace.send(format_info("正在替换存档..."))
            result = await api_client.replace_archive(room_id, archive_path)
            if result.get("success"):
                await archive_replace.finish(format_success("存档替换成功"))
            else:
                await archive_replace.finish(format_error(f"存档替换失败：{result.get('error')}"))

        finally:
            if cleanup:
                service.cleanup_file(archive_path)

    # ========== 验证存档 ==========
    archive_validate = on_command("dst archive validate", priority=10, block=True)

    @archive_validate.handle()
    async def handle_archive_validate(event: MessageEvent, args: Message = CommandArg()):
        if not await check_group(event):
            await archive_validate.finish(format_error("当前群组未授权使用此功能"))
            return

        source = args.extract_plain_text().strip()
        if not source:
            await archive_validate.finish(format_error("用法：/dst archive validate <文件URL或文件路径>"))
            return

        await archive_validate.send(format_info("正在准备存档文件..."))
        prepared = await service.prepare_archive(source)
        if not prepared.get("success"):
            await archive_validate.finish(format_error(prepared.get("error", "文件处理失败")))
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
                await archive_validate.finish(format_error(message))
                return

            info = validation.get("info")
            if info:
                await archive_validate.finish(_format_archive_info(info))
                return

            await archive_validate.finish(format_warning("存档解析完成，但未获取到结构信息"))

        finally:
            if cleanup:
                service.cleanup_file(archive_path)
