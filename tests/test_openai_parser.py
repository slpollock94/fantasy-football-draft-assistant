import types
import sys

# Provide a minimal openai stub if the real package is unavailable
sys.modules.setdefault("openai", types.SimpleNamespace(OpenAI=None))

from ff_draft_assistant import openai_parser

class DummyResponse:
    def __init__(self, content):
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=content))]

class DummyClient:
    def __init__(self):
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(
                create=lambda **kwargs: DummyResponse('[{"player":"A","position":"QB"}]')
            )
        )

def test_parse_table_with_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(openai_parser, "openai", types.SimpleNamespace(OpenAI=lambda api_key: DummyClient()))
    result = openai_parser.parse_table_with_openai("text", ["player", "position"])
    assert result == [{"player": "A", "position": "QB"}]
