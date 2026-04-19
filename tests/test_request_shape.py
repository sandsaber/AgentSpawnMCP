"""Tests that verify request body + URL the client sends, via httpx MockTransport."""
import json
import httpx
import pytest
from src.providers.openai_compat import OpenAICompatProvider


class _Recorder:
    """Captures the request sent through httpx.MockTransport."""

    def __init__(self, response_body: dict, status: int = 200):
        self.response_body = response_body
        self.status = status
        self.last_request: httpx.Request | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.last_request = request
        return httpx.Response(self.status, json=self.response_body)


@pytest.fixture
def patch_httpx(monkeypatch):
    """Replace httpx.Client with a MockTransport-wrapped client that records calls."""
    recorders: list[_Recorder] = []

    def factory(response_body=None, status=200):
        rec = _Recorder(response_body or {}, status)
        recorders.append(rec)

        real_client_cls = httpx.Client

        def fake_client_init(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(rec)
            return real_client_cls(*args, **kwargs)

        monkeypatch.setattr(httpx, "Client", fake_client_init)
        return rec

    return factory


def test_openai_omits_max_tokens_when_none(patch_httpx):
    rec = patch_httpx(
        response_body={
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }
    )
    p = OpenAICompatProvider(name="t", base_url="https://api.openai.com/v1", api_key="k")
    p.chat(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])

    body = json.loads(rec.last_request.content)
    assert "max_tokens" not in body, "OpenAI request must not contain max_tokens when caller passes None"
    assert str(rec.last_request.url) == "https://api.openai.com/v1/chat/completions"


def test_openai_sends_max_tokens_when_set(patch_httpx):
    rec = patch_httpx(
        response_body={
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {},
        }
    )
    p = OpenAICompatProvider(name="t", base_url="https://api.openai.com/v1", api_key="k")
    p.chat(model="gpt-4o", messages=[{"role": "user", "content": "hi"}], max_tokens=512)

    body = json.loads(rec.last_request.content)
    assert body["max_tokens"] == 512


def test_anthropic_defaults_max_tokens_to_16384(patch_httpx):
    rec = patch_httpx(
        response_body={
            "content": [{"type": "text", "text": "ok"}],
            "model": "claude-x",
            "usage": {"input_tokens": 1, "output_tokens": 1},
        }
    )
    p = OpenAICompatProvider(
        name="t",
        base_url="https://api.anthropic.com",
        api_key="k",
        api_type="anthropic",
    )
    p.chat(model="claude-x", messages=[{"role": "user", "content": "hi"}])

    body = json.loads(rec.last_request.content)
    assert body["max_tokens"] == 16384
    assert str(rec.last_request.url) == "https://api.anthropic.com/v1/messages"
    assert rec.last_request.headers["anthropic-version"] == "2023-06-01"


def test_anthropic_respects_explicit_max_tokens(patch_httpx):
    rec = patch_httpx(
        response_body={
            "content": [{"type": "text", "text": "ok"}],
            "model": "claude-x",
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }
    )
    p = OpenAICompatProvider(
        name="t",
        base_url="https://api.z.ai/api/anthropic",
        api_key="k",
        api_type="anthropic",
    )
    p.chat(
        model="glm-4.7",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=1024,
    )

    body = json.loads(rec.last_request.content)
    assert body["max_tokens"] == 1024
    # Regression: z.ai anthropic used to get /anthropic/messages (no /v1) in 1.0.5.
    assert str(rec.last_request.url) == "https://api.z.ai/api/anthropic/v1/messages"


def test_http_error_includes_response_body(patch_httpx):
    rec = patch_httpx(
        response_body={"error": {"message": "invalid model 'glm-999'"}},
        status=400,
    )
    p = OpenAICompatProvider(name="t", base_url="https://api.z.ai/api/paas/v4", api_key="k")

    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        p.chat(model="glm-999", messages=[{"role": "user", "content": "hi"}])

    # The fix in 1.1.0 adds response body to the error — regression check.
    assert "invalid model 'glm-999'" in str(excinfo.value)
    assert "400" in str(excinfo.value)


def test_anthropic_system_message_extracted(patch_httpx):
    rec = patch_httpx(
        response_body={
            "content": [{"type": "text", "text": "ok"}],
            "model": "claude-x",
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }
    )
    p = OpenAICompatProvider(
        name="t", base_url="https://api.anthropic.com", api_key="k", api_type="anthropic"
    )
    p.chat(
        model="claude-x",
        messages=[
            {"role": "system", "content": "you are concise"},
            {"role": "user", "content": "hi"},
        ],
        max_tokens=100,
    )

    body = json.loads(rec.last_request.content)
    assert body["system"] == "you are concise"
    assert len(body["messages"]) == 1
    assert body["messages"][0]["role"] == "user"
