import os
import yaml
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from .models import (
    ConfigModel,
    ProviderConfig,
    Capabilities,
    ModelConfig,
    BUILTIN_PROVIDERS,
    discover_providers,
)


_config: Optional[ConfigModel] = None
_active_provider: Optional[ProviderConfig] = None


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _build_provider(name: str, spec: dict) -> ProviderConfig:
    """Build a ProviderConfig from a YAML spec, filling missing fields from BUILTIN_PROVIDERS."""
    builtin = BUILTIN_PROVIDERS.get(name, {})
    token = spec.get("token", "")
    token_env = spec.get("token_env", builtin.get("token_env", ""))

    resolved_token = token
    if not resolved_token and token_env:
        resolved_token = os.getenv(token_env, "")

    return ProviderConfig(
        name=name,
        base_url=spec.get("base_url", builtin.get("base_url", "")),
        token=token,
        token_env=token_env,
        default_model=spec.get("default_model", builtin.get("default_model", "")),
        default=spec.get("default", False),
        capabilities=Capabilities(**(spec.get("capabilities", {}) or builtin.get("capabilities", {}))),
        models=[ModelConfig(**m) for m in (spec.get("models") or builtin.get("models", []))],
    )


def load_config(
    config_path: str | Path = "configs/default.yaml",
    active_provider: str | None = None,
    discover: bool = True,
) -> ConfigModel:
    """
    Load configuration.

    Steps:
    1. Load YAML — if empty or only has `providers: []`, fall back to discovery mode
    2. For each provider in YAML, fill missing fields from BUILTIN_PROVIDERS
    3. Env overrides: PROVIDER_{NAME}_TOKEN, PROVIDER_{NAME}_BASE_URL, etc.
    4. If discover=True and no providers found, scan env vars for available providers
    """
    global _config, _active_provider
    load_dotenv("example.env")
    path = Path(config_path)
    data = _load_yaml(path)

    providers: list[ProviderConfig] = []

    yaml_providers = data.get("providers", [])
    if yaml_providers:
        for spec in yaml_providers:
            name = spec.get("name", "")
            if not name:
                continue
            p = _build_provider(name, spec)
            providers.append(p)
    elif discover:
        providers = discover_providers()

    if not providers:
        raise ValueError("No providers found. Set a token env var (XAI_TOKEN, OPENAI_TOKEN, etc.) or add providers to config YAML.")

    for p in providers:
        name_upper = p.name.upper().replace("-", "_").replace(" ", "_")
        if os.getenv(f"PROVIDER_{name_upper}_TOKEN"):
            p.token = os.getenv(f"PROVIDER_{name_upper}_TOKEN")
        if os.getenv(f"PROVIDER_{name_upper}_BASE_URL"):
            p.base_url = os.getenv(f"PROVIDER_{name_upper}_BASE_URL")
        if os.getenv(f"PROVIDER_{name_upper}_DEFAULT_MODEL"):
            p.default_model = os.getenv(f"PROVIDER_{name_upper}_DEFAULT_MODEL")

    _config = ConfigModel(providers=providers)

    if active_provider:
        for p in _config.providers:
            if p.name == active_provider:
                _active_provider = p
                break
        else:
            available = [p.name for p in _config.providers]
            raise ValueError(
                f"Provider '{active_provider}' not found. Available: {available}"
            )
    else:
        _active_provider = _config.get_default_provider()

    if _active_provider is None:
        raise ValueError("No providers configured.")

    token = _active_provider.resolve_token()
    if not token:
        env_hint = _active_provider.token_env or f"PROVIDER_{_active_provider.name.upper()}_TOKEN"
        raise ValueError(
            f"Token not found for provider '{_active_provider.name}'.\n"
            f"Set {env_hint} in example.env or as an env var."
        )

    return _config


def get_active_provider() -> ProviderConfig:
    if _active_provider is None:
        raise RuntimeError("Call load_config() before accessing the active provider.")
    return _active_provider


def list_providers() -> list[ProviderConfig]:
    if _config is None:
        raise RuntimeError("Call load_config() first.")
    return _config.providers
