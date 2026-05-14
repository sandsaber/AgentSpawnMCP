from src.config import get_active_provider
from src.config.loader import set_active_provider
from src.config.models import Capabilities, ModelConfig, ProviderConfig
from src.server import create_server


def test_create_server_can_use_inline_provider_without_loading_yaml(monkeypatch):
    import src.server as server_module

    def fail_load_config(*args, **kwargs):
        raise AssertionError("load_config should not be called for inline providers")

    monkeypatch.setattr(server_module, "load_config", fail_load_config)

    provider = ProviderConfig(
        name="local",
        base_url="http://localhost:11434/v1",
        token="token",
        default_model="llama3",
        default=True,
        capabilities=Capabilities(),
        models=[ModelConfig(name="llama3", type="chat")],
    )

    create_server(inline_provider=provider)

    active = get_active_provider()
    assert active.name == "local"
    assert active.base_url == "http://localhost:11434/v1"
    assert active.default_model_name() == "llama3"


def test_create_server_applies_model_override_after_loading_config(monkeypatch):
    import src.server as server_module

    provider = ProviderConfig(
        name="configured",
        base_url="https://api.example.test/v1",
        token="token",
        default_model="model-a",
        default=True,
        capabilities=Capabilities(),
        models=[ModelConfig(name="model-a", type="chat")],
    )

    def fake_load_config(*args, **kwargs):
        return set_active_provider(provider)

    monkeypatch.setattr(server_module, "load_config", fake_load_config)

    create_server(model_override="model-b")

    active = get_active_provider()
    assert active.name == "configured"
    assert active.default_model_name() == "model-b"
