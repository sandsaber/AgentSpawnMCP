import asyncio

from src.config.models import Capabilities, ModelConfig, ProviderConfig
from src.tools import info as info_module


class DummyMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, *args, **kwargs):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def test_list_providers_tool_uses_configured_providers(monkeypatch):
    provider = ProviderConfig(
        name="test-provider",
        base_url="https://api.example.test/v1",
        token="token",
        default_model="model-a",
        default=True,
        capabilities=Capabilities(vision=True, files=True),
        models=[ModelConfig(name="model-a", type="chat")],
    )
    monkeypatch.setattr(info_module, "get_configured_providers", lambda: [provider])

    mcp = DummyMCP()
    info_module.register_info_tools(mcp)

    result = asyncio.run(mcp.tools["list_providers"]())

    assert "test-provider (default)" in result
    assert "https://api.example.test/v1" in result
    assert "model-a" in result
    assert "vision, files" in result
