from pydantic import BaseModel, Field
from typing import Literal


# Known provider definitions: base_url, default_model, capabilities
BUILTIN_PROVIDERS: dict[str, dict] = {
    "grok": {
        "base_url": "https://api.x.ai/v1",
        "default_model": "grok-4-1-fast-reasoning",
        "capabilities": dict(vision=True, files=True, search=True, code_exec=True, stateful=True, agent=True),
        "models": [
            {"name": "grok-4-1-fast-reasoning", "type": "chat"},
            {"name": "grok-4-1-fast-reasoning-vision", "type": "vision"},
            {"name": "grok-imagine-image", "type": "image_gen"},
            {"name": "grok-imagine-video", "type": "video_gen"},
        ],
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "capabilities": dict(vision=True, files=True, search=False, code_exec=False, stateful=False, agent=False),
        "models": [
            {"name": "gpt-4o", "type": "chat"},
            {"name": "gpt-4o-mini", "type": "chat"},
            {"name": "gpt-4-turbo", "type": "vision"},
            {"name": "dall-e-3", "type": "image_gen"},
        ],
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3-70b-8192",
        "capabilities": dict(vision=False, files=False, search=False, code_exec=False, stateful=False, agent=False),
        "models": [
            {"name": "llama-3-70b-8192", "type": "chat"},
            {"name": "llama-3.3-70b-versatile", "type": "chat"},
            {"name": "mixtral-8x7b-32768", "type": "chat"},
        ],
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3",
        "capabilities": dict(vision=False, files=False, search=False, code_exec=False, stateful=False, agent=False),
        "models": [
            {"name": "llama3", "type": "chat"},
        ],
    },
    "lm-studio": {
        "base_url": "http://localhost:1234/v1",
        "default_model": "llama3",
        "capabilities": dict(vision=False, files=False, search=False, code_exec=False, stateful=False, agent=False),
        "models": [
            {"name": "llama3", "type": "chat"},
        ],
    },
    "jan": {
        "base_url": "http://localhost:1337/v1",
        "default_model": "llama3",
        "capabilities": dict(vision=False, files=False, search=False, code_exec=False, stateful=False, agent=False),
        "models": [
            {"name": "llama3", "type": "chat"},
        ],
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "default_model": "meta-llama/Llama-3-70b-chat",
        "capabilities": dict(vision=False, files=False, search=False, code_exec=False, stateful=False, agent=False),
        "models": [
            {"name": "meta-llama/Llama-3-70b-chat", "type": "chat"},
            {"name": "mistralai/Mixtral-8x22B", "type": "chat"},
        ],
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "mistral-large-latest",
        "capabilities": dict(vision=False, files=True, search=False, code_exec=False, stateful=False, agent=False),
        "models": [
            {"name": "mistral-large-latest", "type": "chat"},
            {"name": "mistral-small-latest", "type": "chat"},
        ],
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "capabilities": dict(vision=False, files=False, search=False, code_exec=False, stateful=False, agent=False),
        "models": [
            {"name": "deepseek-chat", "type": "chat"},
            {"name": "deepseek-coder", "type": "chat"},
        ],
    },
    "zai": {
        "base_url": "https://api.z.ai/api/paas/v4",
        "default_model": "glm-5.1",
        "capabilities": dict(vision=False, files=False, search=False, code_exec=False, stateful=False, agent=True),
        "models": [
            {"name": "glm-5.1", "type": "chat"},
            {"name": "glm-5", "type": "chat"},
            {"name": "glm-5-turbo", "type": "chat"},
            {"name": "glm-4.7", "type": "chat"},
            {"name": "glm-4.6", "type": "chat"},
            {"name": "glm-4.5", "type": "chat"},
            {"name": "glm-image", "type": "image_gen"},
            {"name": "cogview-4-250304", "type": "image_gen"},
        ],
    },
}

# Env var name → provider name mapping
PROVIDER_TOKEN_ENV: dict[str, str] = {
    "XAI_TOKEN": "grok",
    "OPENAI_TOKEN": "openai",
    "GROQ_TOKEN": "groq",
    "TOGETHER_TOKEN": "together",
    "MISTRAL_TOKEN": "mistral",
    "DEEPSEEK_TOKEN": "deepseek",
    "ZAI_TOKEN": "zai",
}

PROVIDER_DEFAULT_MODEL_ENV: dict[str, str] = {
    "OLLAMA_MODEL": "ollama",
    "LMSTUDIO_MODEL": "lm-studio",
    "JAN_MODEL": "jan",
}


class Capabilities(BaseModel):
    vision: bool = False
    files: bool = False
    search: bool = False
    code_exec: bool = False
    stateful: bool = False
    agent: bool = False


class ModelConfig(BaseModel):
    name: str
    type: Literal["chat", "vision", "image_gen", "video_gen", "embeddings"] = "chat"


class ProviderConfig(BaseModel):
    name: str
    base_url: str = ""
    token: str = ""
    token_env: str = ""
    default_model: str = ""
    default: bool = False
    capabilities: Capabilities = Field(default_factory=Capabilities)
    models: list[ModelConfig] = Field(default_factory=list)

    def resolve_token(self) -> str:
        if self.token:
            return self.token
        if self.token_env:
            import os
            return os.getenv(self.token_env, "")
        return ""

    def api_url(self) -> str:
        return self.base_url.rstrip("/")

    def default_model_name(self) -> str:
        if self.default_model:
            return self.default_model
        for m in self.models:
            if m.type == "chat":
                return m.name
        return self.models[0].name if self.models else "unknown"

    def is_available(self) -> bool:
        return bool(self.resolve_token())


def discover_providers() -> list[ProviderConfig]:
    """
    Auto-discover providers from environment variables.
    If XAI_TOKEN is set → grok provider is available.
    If OPENAI_TOKEN is set → openai provider is available.
    And so on.
    """
    import os
    found: list[ProviderConfig] = []

    # 1) Built-in providers via env token vars
    for env_var, provider_name in PROVIDER_TOKEN_ENV.items():
        if os.getenv(env_var):
            spec = BUILTIN_PROVIDERS[provider_name]
            found.append(ProviderConfig(
                name=provider_name,
                base_url=spec["base_url"],
                token_env=env_var,
                default_model=spec["default_model"],
                capabilities=Capabilities(**spec["capabilities"]),
                models=[ModelConfig(**m) for m in spec["models"]],
            ))

    # 2) Local providers via URL detection
    # Ollama
    if os.getenv("OLLAMA_HOST") or _check_url("http://localhost:11434/v1/models"):
        spec = BUILTIN_PROVIDERS["ollama"]
        model_override = os.getenv("OLLAMA_MODEL")
        found.append(ProviderConfig(
            name="ollama",
            base_url="http://localhost:11434/v1",
            default_model=model_override or spec["default_model"],
            capabilities=Capabilities(**spec["capabilities"]),
            models=[ModelConfig(name=m, type="chat") for m in (os.getenv("OLLAMA_MODELS", "llama3").split(","))]
            if os.getenv("OLLAMA_MODELS") else [ModelConfig(**spec["models"][0])],
        ))

    # LM Studio
    if _check_url("http://localhost:1234/v1/models"):
        spec = BUILTIN_PROVIDERS["lm-studio"]
        found.append(ProviderConfig(
            name="lm-studio",
            base_url="http://localhost:1234/v1",
            default_model=os.getenv("LMSTUDIO_MODEL") or spec["default_model"],
            capabilities=Capabilities(**spec["capabilities"]),
            models=[ModelConfig(**m) for m in spec["models"]],
        ))

    # Jan
    if _check_url("http://localhost:1337/v1/models"):
        spec = BUILTIN_PROVIDERS["jan"]
        found.append(ProviderConfig(
            name="jan",
            base_url="http://localhost:1337/v1",
            default_model=os.getenv("JAN_MODEL") or spec["default_model"],
            capabilities=Capabilities(**spec["capabilities"]),
            models=[ModelConfig(**m) for m in spec["models"]],
        ))

    return found


def _check_url(url: str) -> bool:
    try:
        import httpx
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(url)
            return resp.status_code < 500
    except Exception:
        return False


class ConfigModel(BaseModel):
    providers: list[ProviderConfig] = Field(default_factory=list)

    def get_default_provider(self) -> ProviderConfig | None:
        for p in self.providers:
            if p.default:
                return p
        return self.providers[0] if self.providers else None

    def available_providers(self) -> list[ProviderConfig]:
        """Return only providers that have a valid token."""
        return [p for p in self.providers if p.is_available()]
