import os
from pathlib import Path
from zipfile import ZipFile

import pytest

from nonebot_plugin_dst_management.config import DSTConfig
from nonebot_plugin_dst_management.services import archive_service
from nonebot_plugin_dst_management.services.archive_service import ArchiveService


@pytest.mark.asyncio
async def test_prepare_archive_local_file(tmp_path):
    test_file = tmp_path / "sample.zip"
    test_file.write_text("content", encoding="utf-8")

    service = ArchiveService(work_dir=str(tmp_path))
    result = await service.prepare_archive(str(test_file))

    assert result["success"] is True
    assert result["path"] == str(test_file)
    assert result["cleanup"] is False


@pytest.mark.asyncio
async def test_prepare_archive_url(tmp_path):
    service = ArchiveService(work_dir=str(tmp_path))

    async def fake_download(url: str, dest: Path) -> None:
        dest.write_bytes(b"zip")

    service.download_file = fake_download  # type: ignore[assignment]

    result = await service.prepare_archive("https://example.com/archive")

    assert result["success"] is True
    assert result["cleanup"] is True
    assert result["path"].endswith("archive.zip")
    assert os.path.isfile(result["path"])


def test_validate_archive_success(tmp_path):
    archive_path = tmp_path / "cluster.zip"

    with ZipFile(archive_path, "w") as zf:
        zf.writestr("cluster.ini", "game_mode=survival\ncluster_name=Test Room\n")
        zf.writestr("cluster_token.txt", "token")
        zf.writestr("Master/server.ini", "server")
        zf.writestr("Caves/server.ini", "server")
        zf.writestr("Master/modoverrides.lua", "return { ['workshop-12345']={enabled=true}, ['workshop-67890']={enabled=false} }")

    service = ArchiveService(work_dir=str(tmp_path))
    result = service.validate_archive(str(archive_path))

    assert result["success"] is True
    info = result["info"]
    assert info is not None
    assert info.cluster_name == "Test Room"
    assert info.game_mode == "survival"
    assert set(info.worlds) == {"Master", "Caves"}
    assert info.mod_count == 2
    assert info.warnings == []


def test_validate_archive_missing_files(tmp_path):
    archive_path = tmp_path / "bad.zip"

    with ZipFile(archive_path, "w") as zf:
        zf.writestr("Master/server.ini", "server")

    service = ArchiveService(work_dir=str(tmp_path))
    result = service.validate_archive(str(archive_path))

    assert result["success"] is False
    errors = result["errors"]
    assert "缺少 cluster.ini" in errors
    assert "缺少 cluster_token.txt" in errors


def test_analyze_with_ai_flag(monkeypatch, tmp_path):
    monkeypatch.setattr(
        archive_service,
        "get_dst_config",
        lambda: DSTConfig(dst_enable_ai=True),
    )
    service = ArchiveService(work_dir=str(tmp_path))
    info = archive_service.ArchiveInfo(worlds=[], mod_count=0, game_mode=None, cluster_name=None, warnings=[])
    assert service.analyze_with_ai(info) == "AI 功能已启用，但当前未配置分析器"

    monkeypatch.setattr(
        archive_service,
        "get_dst_config",
        lambda: DSTConfig(dst_enable_ai=False),
    )
    service = ArchiveService(work_dir=str(tmp_path))
    assert service.analyze_with_ai(info) is None
