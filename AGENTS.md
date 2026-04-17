# AgentSpawnMCP

Universal MCP server for any OpenAI-compatible LLM provider. Built on [FastMCP](https://github.com/modelcontextprotocol/python-sdk), pure `httpx` HTTP — no provider SDKs.

## Architecture: Process = Provider

One process — one provider. `--provider` selects from discovered/configured providers. To run multiple providers simultaneously, start multiple processes.

```
XAI_TOKEN=xai-... uv run python main.py main --provider grok
GROQ_TOKEN=gsk-... uv run python main.py main --provider groq
uv run python main.py main --local --model llama3
```

## Project Overview

- **Type**: MCP server (Model Context Protocol)
- **Language**: Python 3.11+
- **Package manager**: UV (Astral)
- **Transport**: stdio only
- **Entry point**: `main.py` → `load_config()` → `create_server()` → `mcp.run(transport='stdio')`
- **Dependencies**: `mcp[cli]`, `httpx`, `pydantic`, `pyyaml`, `python-dotenv`, `typer`

## Essential Commands

```bash
uv sync                                    # Install
uv run python main.py main                 # Auto-detect provider
uv run python main.py main --provider grok
uv run python main.py main --local --model mixtral
mcp dev main.py -- main --provider grok
```

## Code Organization

```
src/
  __init__.py
  server.py             — create_server(config_path, active_provider)
  utils.py             — load_history, save_history, encode_image_to_base64
  config/
    models.py          — Pydantic models + BUILTIN_PROVIDERS dict + discover_providers()
    loader.py           — load_config(), get_active_provider(), list_providers()
    __init__.py         — re-exports
  providers/
    base.py            — Abstract BaseProvider
    openai_compat.py    — OpenAICompatProvider: all HTTP via httpx
  tools/
    __init__.py         — register_all_tools(mcp)
    info.py             — list_providers, list_models
    chat.py             — chat, stateful_chat, session tools
    vision.py           — chat_with_vision, generate_image
    files.py            — file CRUD, chat_with_files
    search.py           — web_search, code_executor
    agent.py            — agent (unified)
configs/
  default.yaml         — Optional; BUILTIN_PROVIDERS used when absent
main.py               — Typer CLI with --provider, --url, --local, --model, --token
```

## Provider Discovery

Three sources (in priority order):

### 1. Env vars → auto-discover
If `XAI_TOKEN`, `OPENAI_TOKEN`, `GROQ_TOKEN`, etc. are set in the environment, those providers are auto-added with their built-in specs.

### 2. Local URL probe → auto-detect
`discover_providers()` pings localhost ports (11434=Ollama, 1234=LM Studio, 1337=Jan) and auto-adds them if responding.

### 3. YAML config (`configs/default.yaml`)
For any custom or fine-grained configuration. Missing fields (base_url, default_model, capabilities, models) are filled from `BUILTIN_PROVIDERS`.

## BUILTIN_PROVIDERS

`src/config/models.py:BUILTIN_PROVIDERS` is the central registry. Keys: `grok`, `openai`, `groq`, `ollama`, `lm-studio`, `jan`, `together`, `mistral`, `deepseek`. Each entry has `base_url`, `default_model`, `capabilities`, `models`.

## Config Loading (`load_config`)

```python
load_config(
    config_path: str = "configs/default.yaml",
    active_provider: str | None = None,  # None → first available → first default:true
    discover: bool = True,               # If YAML empty, auto-discover from env
) -> ConfigModel
```

Flow:
1. Load YAML (or skip if file absent/empty)
2. For each provider: fill missing fields from `BUILTIN_PROVIDERS`
3. Env overrides: `PROVIDER_{NAME}_TOKEN`, `PROVIDER_{NAME}_BASE_URL`, `PROVIDER_{NAME}_DEFAULT_MODEL`
4. If no providers found and `discover=True`: call `discover_providers()`
5. Set global `_active_provider`
6. Validate token is present → error if missing

## ProviderConfig API

```python
p.name               # string identifier
p.base_url          # e.g. "https://api.x.ai/v1"
p.token             # direct value from YAML
p.token_env         # env var name to resolve
p.resolve_token()   # token (priority: token > os.getenv(token_env) > env override)
p.default_model     # explicit default
p.default_model_name()  # default_model → first chat model → first model
p.capabilities      # Capabilities(vision, files, ...)
p.models            # list[ModelConfig]
p.is_available()    # bool: has a resolved token
```

## `create_server()` Signature

```python
def create_server(
    name: str = "AgentSpawnMCP",
    config_path: str = "configs/default.yaml",
    active_provider: str | None = None,
) -> FastMCP
```

## Core Pattern: Every Tool

```python
def register_chat_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def chat(prompt: str, ...):
        p = get_active_provider()
        if not p.capabilities.{cap}:
            raise ValueError(f"Provider `{p.name}` does not support this.")
        client = OpenAICompatProvider(
            name=p.name,
            base_url=p.base_url,
            api_key=p.resolve_token(),
        )
        ...
```

**Never pass `p.token_env` directly to HTTP client — always use `p.resolve_token()`.**

## OpenAICompatProvider API

```python
client.chat(
    model, messages,
    tools: list[dict] | None = None,      # [{"type": "web_search", "web_search": {}}]
    include: list[str] | None = None,     # ["code_execution_call_output", "citations"]
    max_turns: int | None = None,
    store_messages: bool = False,
    previous_response_id: str | None = None,
) -> dict  # parsed JSON

client.generate_image(model, prompt, image_path, image_url, n, aspect_ratio) -> dict
client.upload_file(file_path) -> dict
client.list_files(limit, order, sort_by) -> dict
client.get_file_content(file_id, max_bytes) -> bytes
client.delete_file(file_id) -> dict
```

## Session History

`chats/{provider_name}_{session}.json`. Timestamp format: `"%d.%m.%Y %H:%M:%S"`.

## Notable Gotchas

1. **`token` vs `token_env`** — `token` is direct value (YAML), `token_env` is env var name. `resolve_token()` checks both.
2. **`chats/` directory** — auto-created by `save_history()`. Working dir must be writable.
3. **Vision supports only jpg/jpeg/png** — raises `ValueError` for others.
4. **`store_messages` default is `False`** — pass explicitly for server-side persistence.
5. **Local URL probing** (`_check_url`) — uses `httpx` with 3s timeout. Can add latency on startup if local servers are slow/absent.
6. **`list_providers` tool** — only works in config/discovery mode; not available in ad-hoc `--url` mode (no providers list to show).
7. **File upload** — multipart form-data, not JSON.
8. **No tests** — no test suite exists yet.
9. **`resolve_token()` returns empty string** if neither `token` nor `token_env` is set — caller must handle this.

## Adding a New Provider

1. Add entry to `BUILTIN_PROVIDERS` in `src/config/models.py`
2. Add `PROVIDER_TOKEN_ENV` mapping if it has a standard env var name
3. Restart — no YAML change needed

## Adding a Tool

1. Add to appropriate `src/tools/` file
2. Pattern: `p = get_active_provider()` → capability check → `OpenAICompatProvider(...)` → call → return string
3. `mcp.tool()` or `mcp.tool(annotations={"readOnlyHint": True})`
4. Add to `register_all_tools()` in `src/tools/__init__.py`

---

# AgentSpawnMCP

Agent spawning MCP server — allows spawning agents on configurable LLM providers. Each instance exposes a single `{provider}_agent` tool.

## Architecture: One Instance = One Provider

Each MCP instance is configured for one provider. To use multiple providers, start multiple instances with different configs.

## CLI

```bash
# OpenAI-compatible API (Minimax, OpenAI, etc.)
uv run python main.py spawn --name minimax --url https://api.minimax.io --token <token> --model MiniMax-M2.7

# Anthropic-compatible API with custom path
uv run python main.py spawn --name minimax --url https://api.minimax.io/anthropic/v1 --token <token> --model MiniMax-M2.7 --api-type anthropic

# Anthropic API
uv run python main.py spawn --name claude --url https://api.anthropic.com --token <token> --model claude-sonnet-4-20250514 --api-type anthropic
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--name`, `-n` | Yes | Provider name (used in tool name: `{name}_agent`) |
| `--url`, `-u` | Yes | API base URL |
| `--token`, `-t` | Yes | API token |
| `--model`, `-m` | No | Default model name |
| `--api-type` | No | API type: `openai` (default) or `anthropic` |

## Tools Exposed

- `{name}_agent` — Spawn agent for task execution
- `agent_info` — Get current provider info

## Agent Tool Interface

```python
{provider}_agent(
    task: str,                           # Task description
    model: str | None = None,           # Override default model
    system_prompt: str | None = None,    # Custom system prompt
    temperature: float | None = None,    # 0.0-2.0
    max_tokens: int | None = None,       # Response token limit
    timeout: int = 120,                  # Request timeout (seconds)
) -> dict:
    """
    Returns:
        {
            "result": "...",  # Agent response text
            "metadata": {
                "provider": "provider_name",
                "model_used": "model-name",
                "usage": {"prompt_tokens": N, "completion_tokens": N},
                "latency_ms": N
            }
        }
    """
```

## Claude Code / OpenCode Integration

Add to your MCP client config (`.mcp.json`):

```json
{
  "mcpServers": {
    "minimax-agent": {
      "command": "uv",
      "args": ["run", "python", "main.py", "spawn",
               "--name", "minimax",
               "--url", "https://api.minimax.io/anthropic/v1",
               "--token", "your-minimax-token",
               "--model", "MiniMax-M2.7",
               "--api-type", "anthropic"]
    },
    "claude-agent": {
      "command": "uv",
      "args": ["run", "python", "main.py", "spawn",
               "--name", "claude",
               "--url", "https://api.anthropic.com",
               "--token", "your-anthropic-token",
               "--model", "claude-sonnet-4-20250514",
               "--api-type", "anthropic"]
    }
  }
}
```

## Code Organization

```
src/agent_spawn/
  __init__.py
  server.py              — create_agent_spawn_server()
  tools/
    __init__.py
    base.py              — _create_agent_tool() factory
    registry.py          — register_tools()
```

## `create_agent_spawn_server()` Signature

```python
def create_agent_spawn_server(
    name: str = "AgentSpawnMCP",
    provider_name: str = "agent",
    api_url: str = "",
    api_token: str = "",
    default_model: str = "",
    api_type: str = "openai",
) -> FastMCP
```

## Adding a New Agent Provider

No code changes needed. Just add a new MCP server instance with `--name`, `--url`, `--token`, `--model`, and optionally `--api-type`.
