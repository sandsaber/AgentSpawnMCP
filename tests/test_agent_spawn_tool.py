import asyncio

import pytest

from src.agent_spawn.tools.base import _create_agent_tool
from src.providers.openai_compat import OpenAICompatProvider


def test_agent_tool_uses_default_model_and_returns_metadata(monkeypatch):
    calls = {}

    def fake_chat(self, model, messages, temperature=None, max_tokens=None, timeout=None):
        calls.update(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        return {
            "choices": [{"message": {"role": "assistant", "content": "done"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 4},
        }

    monkeypatch.setattr(OpenAICompatProvider, "chat", fake_chat)

    tool = _create_agent_tool(
        provider_name="glm",
        api_url="https://api.example.test/v1",
        api_token="token",
        default_model="glm-5",
    )
    result = asyncio.run(
        tool(
            task="Review this",
            system_prompt="Be concise",
            temperature=0.2,
            max_tokens=64,
            timeout=30,
        )
    )

    assert result["result"] == "done"
    assert result["metadata"]["provider"] == "glm"
    assert result["metadata"]["model_used"] == "glm-5"
    assert result["metadata"]["usage"] == {"prompt_tokens": 3, "completion_tokens": 4}
    assert isinstance(result["metadata"]["latency_ms"], int)
    assert calls["model"] == "glm-5"
    assert calls["temperature"] == 0.2
    assert calls["max_tokens"] == 64
    assert calls["timeout"] == 30.0
    assert calls["messages"] == [
        {"role": "system", "content": "Be concise"},
        {"role": "user", "content": "Review this"},
    ]


def test_agent_tool_normalizes_text_blocks(monkeypatch):
    def fake_chat(self, **kwargs):
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": "hello"},
                            {"type": "text", "text": " world"},
                        ],
                    }
                }
            ],
            "usage": {},
        }

    monkeypatch.setattr(OpenAICompatProvider, "chat", fake_chat)

    tool = _create_agent_tool(
        provider_name="provider",
        api_url="https://api.example.test/v1",
        api_token="token",
        default_model="model-a",
    )

    result = asyncio.run(tool(task="say hi"))

    assert result["result"] == "hello world"


def test_agent_tool_requires_model():
    tool = _create_agent_tool(
        provider_name="provider",
        api_url="https://api.example.test/v1",
        api_token="token",
        default_model="",
    )

    with pytest.raises(ValueError, match="No model provided"):
        asyncio.run(tool(task="run"))


def test_agent_tool_validates_timeout():
    tool = _create_agent_tool(
        provider_name="provider",
        api_url="https://api.example.test/v1",
        api_token="token",
        default_model="model-a",
    )

    with pytest.raises(ValueError, match="timeout must be greater than zero"):
        asyncio.run(tool(task="run", timeout=0))
