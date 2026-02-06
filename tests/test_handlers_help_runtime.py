import pytest

from nonebot_plugin_dst_management.handlers import help as help_handler


class FakeCommand:
    def __init__(self):
        self.handlers = []
        self.sent = []
        self.finished = []

    def handle(self):
        def decorator(func):
            self.handlers.append(func)
            return func

        return decorator

    async def send(self, message):
        self.sent.append(message)

    async def finish(self, message):
        self.finished.append(message)


def setup_fake_commands(monkeypatch, module):
    commands = []

    def fake_on_command(*args, **kwargs):
        cmd = FakeCommand()
        commands.append(cmd)
        return cmd

    monkeypatch.setattr(module, "on_command", fake_on_command)
    return commands


def _text(message) -> str:
    if hasattr(message, "extract_plain_text"):
        return message.extract_plain_text()
    return str(message)


@pytest.mark.asyncio
async def test_dst_help_branches_by_bot_type(monkeypatch):
    commands = setup_fake_commands(monkeypatch, help_handler)
    help_handler.init()

    assert commands
    assert commands[0].handlers

    OneBotBot = type("Bot", (), {"__module__": "nonebot.adapters.onebot.v11.bot"})
    bot_onebot = OneBotBot()

    await commands[0].handlers[0](bot_onebot, object())
    assert commands[0].finished
    onebot_text = _text(commands[0].finished[-1])
    assert "DST 管理帮助" in onebot_text
    assert "🏠 基础管理" in onebot_text

    QQBot = type("Bot", (), {"__module__": "nonebot.adapters.qq.bot"})
    bot_qq = QQBot()

    await commands[0].handlers[0](bot_qq, object())
    qq_text = _text(commands[0].finished[-1])
    assert "# DST 管理帮助" in qq_text
    assert "## 🏠 基础管理" in qq_text

