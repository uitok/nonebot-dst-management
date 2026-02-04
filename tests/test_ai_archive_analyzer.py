import pytest

from nonebot_plugin_dst_management.ai import archive_analyzer
from nonebot_plugin_dst_management.ai.archive_analyzer import ArchiveAnalyzer


class DummyAIClient:
    async def chat(self, *args, **kwargs):
        raise AssertionError("chat should not be called for oversized archives")


@pytest.mark.asyncio
async def test_analyze_archive_rejects_large(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(archive_analyzer, "MAX_ARCHIVE_SIZE", 10)
    analyzer = ArchiveAnalyzer(DummyAIClient())

    result = await analyzer.analyze_archive(b"0" * 11)
    assert "存档文件过大" in result
