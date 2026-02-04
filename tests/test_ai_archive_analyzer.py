import pytest

from nonebot_plugin_dst_management.ai import archive_analyzer
from nonebot_plugin_dst_management.ai.archive_analyzer import ArchiveAnalyzer
from nonebot_plugin_dst_management.ai.base import AIError
from zipfile import ZipFile
import io


class DummyAIClient:
    async def chat(self, *args, **kwargs):
        raise AssertionError("chat should not be called for oversized archives")


@pytest.mark.asyncio
async def test_analyze_archive_rejects_large(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(archive_analyzer, "MAX_ARCHIVE_SIZE", 10)
    analyzer = ArchiveAnalyzer(DummyAIClient())

    result = await analyzer.analyze_archive(b"0" * 11)
    assert "存档文件过大" in result


class EmptyResponseAIClient:
    async def chat(self, *args, **kwargs):
        return ""


class ErrorAIClient:
    async def chat(self, *args, **kwargs):
        raise AIError("boom")


def _build_zip(files):
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_analyze_archive_fallback_report() -> None:
    archive_data = _build_zip({"cluster.ini": "data", "world/modoverrides.lua": "return {}"})
    analyzer = ArchiveAnalyzer(EmptyResponseAIClient())

    report = await analyzer.analyze_archive(archive_data)
    assert "存档分析报告" in report
    assert "文件数量" in report


@pytest.mark.asyncio
async def test_analyze_archive_ai_error() -> None:
    archive_data = _build_zip({"cluster.ini": "data"})
    analyzer = ArchiveAnalyzer(ErrorAIClient())

    report = await analyzer.analyze_archive(archive_data)
    assert "AI 分析失败" in report


def test_extract_files_invalid_zip() -> None:
    analyzer = ArchiveAnalyzer(EmptyResponseAIClient())

    with pytest.raises(RuntimeError):
        analyzer._extract_files(b"not a zip")
