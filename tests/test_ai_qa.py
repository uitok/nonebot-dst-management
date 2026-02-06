from pathlib import Path

import pytest

from nonebot_plugin_dst_management.ai.base import AIError
from nonebot_plugin_dst_management.ai.config import AIConfig
from nonebot_plugin_dst_management.ai.qa import QASystem


class FakeAIClient:
    def __init__(self, response=None, error: Exception | None = None, config: AIConfig | None = None):
        self.response = response
        self.error = error
        self.calls = []
        self.config = config or AIConfig(enabled=True)

    async def chat(self, messages, system_prompt="", **kwargs):
        self.calls.append((messages, system_prompt))
        if self.error:
            raise self.error
        return self.response


def test_build_knowledge_base(tmp_path):
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    (tmp_path / "COMMANDS.md").write_text("commands", encoding="utf-8")
    (tmp_path / "AI_COMPLETE_PLAN.md").write_text("plan", encoding="utf-8")

    qa = QASystem(FakeAIClient(), docs_root=tmp_path)
    sources = qa._build_knowledge_base("extra")

    names = [source.name for source in sources]
    assert "README.md" in names
    assert "COMMANDS.md" in names
    assert "AI_COMPLETE_PLAN.md" in names
    assert "DST basics" in names
    assert "User context" in names


def test_build_prompt_contains_question():
    qa = QASystem(FakeAIClient(), docs_root=Path("."))
    prompt = qa._build_prompt("问题?", [], [], None)
    assert "问题" in prompt


@pytest.mark.asyncio
async def test_ask_success():
    client = FakeAIClient(response="OK")
    qa = QASystem(client, docs_root=Path("."))
    result = await qa.ask("test")
    assert result == "OK"
    assert client.calls


@pytest.mark.asyncio
async def test_ask_fallback_on_ai_error():
    client = FakeAIClient(error=AIError("fail"))
    qa = QASystem(client, docs_root=Path("."))
    result = await qa.ask("test")
    assert "当前无法获得 AI 答复" in result
    assert "AI 问答失败" in result


@pytest.mark.asyncio
async def test_ask_fallback_on_empty_response():
    client = FakeAIClient(response="   ")
    qa = QASystem(client, docs_root=Path("."))
    result = await qa.ask("test")
    assert "当前无法获得 AI 答复" in result


@pytest.mark.asyncio
async def test_session_history_in_prompt():
    class SeqClient(FakeAIClient):
        def __init__(self, responses):
            super().__init__(response=None)
            self.responses = list(responses)

        async def chat(self, messages, system_prompt="", **kwargs):
            self.calls.append((messages, system_prompt))
            return self.responses.pop(0)

    client = SeqClient(["A1", "A2"])
    qa = QASystem(client, docs_root=Path("."))

    await qa.ask("first", session_id="s1")
    await qa.ask("second", session_id="s1")

    last_prompt = client.calls[-1][0][0]["content"]
    assert "用户：first" in last_prompt
    assert "助手：A1" in last_prompt


def test_custom_prompt_template_used():
    cfg = AIConfig(enabled=True, prompt_template="Q:{question}")
    client = FakeAIClient(response="OK", config=cfg)
    qa = QASystem(client, docs_root=Path("."))
    prompt = qa._build_prompt("hello", [], [], None)
    assert prompt.strip() == "Q:hello"
