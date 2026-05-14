from typer.testing import CliRunner

from src.__main__ import app


runner = CliRunner()


def test_spawn_accepts_token_env(monkeypatch):
    import src.agent_spawn

    calls = {}

    class DummyServer:
        def run(self, transport):
            calls["transport"] = transport

    def fake_create_agent_spawn_server(**kwargs):
        calls.update(kwargs)
        return DummyServer()

    monkeypatch.setattr(src.agent_spawn, "create_agent_spawn_server", fake_create_agent_spawn_server)
    monkeypatch.setenv("MINIMAX_TOKEN", "secret-token")

    result = runner.invoke(
        app,
        [
            "spawn",
            "--name",
            "minimax",
            "--url",
            "https://api.minimax.io/anthropic/v1",
            "--token-env",
            "MINIMAX_TOKEN",
            "--model",
            "MiniMax-M2.7",
            "--api-type",
            "anthropic",
        ],
    )

    assert result.exit_code == 0
    assert calls["api_token"] == "secret-token"
    assert calls["provider_name"] == "minimax"
    assert calls["api_type"] == "anthropic"
    assert calls["transport"] == "stdio"


def test_spawn_requires_token_or_token_env():
    result = runner.invoke(
        app,
        [
            "spawn",
            "--name",
            "minimax",
            "--url",
            "https://api.minimax.io/anthropic/v1",
            "--token-env",
            "MISSING_TOKEN",
        ],
    )

    assert result.exit_code == 1
    assert "Token not found" in result.stderr
