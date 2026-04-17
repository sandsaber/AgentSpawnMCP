# AgentSpawnMCP — Developer Guide

Universal MCP server for any OpenAI-compatible LLM provider. Built on [FastMCP](https://github.com/modelcontextprotocol/python-sdk), pure `httpx` HTTP — no provider SDKs.

## Two Modes

### 1. AgentSpawnMCP — Spawn Agents (Recommended)

Spawn agents on any provider. No git clone needed — runs directly with `uvx`.

```bash
uvx agent-spawn-mcp spawn --name minimax --url https://api.minimax.io/anthropic/v1 --token TOKEN --model MiniMax-M2.7 --api-type anthropic
```

### 2. AgentSpawnMCP — Full Server

Full-featured MCP server with all tools. Requires git clone.

```bash
git clone https://github.com/sandsaber/AgentSpawnMCP
cd AgentSpawnMCP
uv sync
uv run python main.py main --provider grok
```

## Code Organization

```
src/
  __init__.py
  server.py             — create_server() for full server
  utils.py             — history helpers
  config/
    models.py          — Pydantic models + BUILTIN_PROVIDERS
    loader.py           — load_config()
  providers/
    openai_compat.py    — OpenAICompatProvider (HTTP)
  tools/
    chat.py, vision.py, files.py, search.py, agent.py
  agent_spawn/          — Spawn agents module
    server.py           — create_agent_spawn_server()
    tools/
      base.py           — _create_agent_tool() factory
      registry.py       — register_tools()
configs/
  default.yaml         — Optional config for full server
main.py               — CLI entry point
```

## Full Server: Provider Discovery

Three sources (priority order):
1. Env vars (`XAI_TOKEN`, `OPENAI_TOKEN`, etc.) — auto-discover
2. Local URL probe — Ollama (11434), LM Studio (1234), Jan (1337)
3. YAML config (`configs/default.yaml`)

### BUILTIN_PROVIDERS

Keys: `grok`, `openai`, `groq`, `ollama`, `lm-studio`, `jan`, `together`, `mistral`, `deepseek`

## Full Server: Adding a Provider

1. Add entry to `BUILTIN_PROVIDERS` in `src/config/models.py`
2. Add `PROVIDER_TOKEN_ENV` mapping if needed
3. Restart — no YAML change needed

## Full Server: Adding a Tool

1. Add to `src/tools/`
2. Pattern: `p = get_active_provider()` → capability check → `OpenAICompatProvider(...)` → call
3. `mcp.tool()`
4. Add to `register_all_tools()` in `src/tools/__init__.py`

## AgentSpawnMCP: Adding a Provider

No code changes needed. Just run with new `--name`, `--url`, `--token`.

## AgentSpawnMCP: CLI Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--name`, `-n` | Yes | Provider name (tool: `{name}_agent`) |
| `--url`, `-u` | Yes | API base URL |
| `--token`, `-t` | Yes | API token |
| `--model`, `-m` | No | Default model |
| `--api-type` | No | `openai` (default) or `anthropic` |

## AgentSpawnMCP: Tool Interface

```python
{provider}_agent(
    task: str,
    model: str | None = None,
    system_prompt: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: int = 120,
) -> dict
```

Returns:
```python
{
    "result": "...",
    "metadata": {
        "provider": "name",
        "model_used": "model",
        "usage": {"prompt_tokens": N, "completion_tokens": N},
        "latency_ms": N
    }
}
```

## OpenAICompatProvider API

```python
client.chat(model, messages, tools=None, temperature=None, max_tokens=None, ...) -> dict
client.generate_image(model, prompt, image_path=None, image_url=None, n=1, ...) -> dict
client.upload_file(file_path) -> dict
client.list_files(limit=100) -> dict
client.get_file_content(file_id, max_bytes=500_000) -> bytes
client.delete_file(file_id) -> dict
```

## Notable Gotchas

1. **`token` vs `token_env`** — `token` is direct value, `token_env` is env var name. Use `resolve_token()`.
2. **`chats/` directory** — auto-created for session history. Working dir must be writable.
3. **Vision supports only jpg/jpeg/png**.
4. **`store_messages` default is `False`**.
5. **Local URL probing** — 3s timeout per port, can slow startup.
6. **`resolve_token()` returns empty string** if no token set.
