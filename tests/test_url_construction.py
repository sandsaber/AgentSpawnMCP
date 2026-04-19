import pytest
from src.providers.openai_compat import OpenAICompatProvider


@pytest.mark.parametrize(
    "base_url, path, expected",
    [
        # OpenAI-style: base has /v1 at the end → client must NOT double it.
        (
            "https://api.openai.com/v1",
            "v1/chat/completions",
            "https://api.openai.com/v1/chat/completions",
        ),
        (
            "https://api.x.ai/v1",
            "v1/chat/completions",
            "https://api.x.ai/v1/chat/completions",
        ),
        # OpenRouter: /api/v1 — same rule.
        (
            "https://openrouter.ai/api/v1",
            "v1/chat/completions",
            "https://openrouter.ai/api/v1/chat/completions",
        ),
        # z.ai coding: /paas/v4 — version is v4, not v1. Must strip our v1/ prefix.
        (
            "https://api.z.ai/api/coding/paas/v4",
            "v1/chat/completions",
            "https://api.z.ai/api/coding/paas/v4/chat/completions",
        ),
        (
            "https://api.z.ai/api/paas/v4",
            "v1/chat/completions",
            "https://api.z.ai/api/paas/v4/chat/completions",
        ),
        # Base without any version segment → keep the v1/ prefix.
        (
            "https://api.minimax.io",
            "v1/chat/completions",
            "https://api.minimax.io/v1/chat/completions",
        ),
        # Anthropic-compat cases
        (
            "https://api.anthropic.com",
            "v1/messages",
            "https://api.anthropic.com/v1/messages",
        ),
        # z.ai anthropic: base is /api/anthropic (no version). Must prepend v1/.
        # This is the regression test for the inverted heuristic in 1.0.5.
        (
            "https://api.z.ai/api/anthropic",
            "v1/messages",
            "https://api.z.ai/api/anthropic/v1/messages",
        ),
        # Minimax anthropic: /anthropic/v1 — keep as is.
        (
            "https://api.minimax.io/anthropic/v1",
            "v1/messages",
            "https://api.minimax.io/anthropic/v1/messages",
        ),
        # Trailing slash on base must not create double slashes.
        (
            "https://api.openai.com/v1/",
            "v1/chat/completions",
            "https://api.openai.com/v1/chat/completions",
        ),
        # Leading slash on path must not break anything.
        (
            "https://api.openai.com/v1",
            "/v1/chat/completions",
            "https://api.openai.com/v1/chat/completions",
        ),
        # Files endpoint on a versioned base must also get stripped.
        (
            "https://api.z.ai/api/paas/v4",
            "v1/files",
            "https://api.z.ai/api/paas/v4/files",
        ),
    ],
)
def test_url_construction(base_url, path, expected):
    p = OpenAICompatProvider(name="t", base_url=base_url, api_key="k")
    assert p._url(path) == expected
