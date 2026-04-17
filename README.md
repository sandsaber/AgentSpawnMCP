# AgentSpawnMCP

Universal MCP server for any OpenAI-compatible LLM. Supports OpenAI and Anthropic API formats, cloud providers (OpenAI, Grok, Claude, Minimax, DeepSeek) and local models (Ollama, LM Studio, Jan). Spawn agents on any provider via CLI — one instance per provider. Built on FastMCP with pure httpx. Zero-config via env vars; optional YAML config.

```
┌──────────────────────────────────────────────────────────────┐
│                       AgentSpawnMCP                           │
│                                                              │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│   │  Grok    │  │  OpenAI │  │  Groq    │  │  Ollama  │    │
│   │  cloud  │  │  cloud  │  │  cloud  │  │   local  │    │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│        └───────────────┼───────────────┼───────────────┘      │
│                        ▼                                     │
│               ┌─────────────────┐                           │
│               │   FastMCP Server │                           │
│               └─────────────────┘                           │
└──────────────────────────────────────────────────────────────┘
```

## Features

- **Zero-config for common providers** — if `XAI_TOKEN` is set, Grok just works
- **Auto-discovery** — detects local models (Ollama, LM Studio, Jan) by probing localhost
- **Cloud + Local** — any OpenAI-compatible API
- **Process-level isolation** — one provider per process; run multiple instances simultaneously
- **Ad-hoc mode** — no config file needed: `--url` + `--model` + `--token`
- **Pure `httpx`** — no SDK lock-in

## Prerequisites

- Python 3.11+
- [Astral UV](https://docs.astral.sh/uv/getting-started/installation/)

## Quick Start

```bash
git clone <repo>
cd AgentSpawnMCP
uv venv && source .venv/bin/activate
uv sync
cp example.env .env
# Edit .env — add your token
```

Then run:

```bash
uv run python main.py main
```

Server auto-detects available providers from env vars. First one with a valid token becomes active.

## Running

### Auto mode (no flags needed)

If env vars are set, server picks the first available provider:

```bash
XAI_TOKEN=xai-... uv run python main.py main
OPENAI_TOKEN=sk-... uv run python main.py main
```

### Explicit provider selection

```bash
uv run python main.py main --provider grok
uv run python main.py main --provider openai
uv run python main.py main --provider groq
```

### Ad-hoc / Local models

```bash
# Ollama (default: localhost:11434/v1 + llama3)
uv run python main.py main --local

# Ollama with specific model
uv run python main.py main --local --model mixtral

# Any local server
uv run python main.py main --url http://localhost:8000/v1 --model llama3

# With token auth
uv run python main.py main --local --token my-token
```

### Override model

```bash
uv run python main.py main --provider grok --model grok-4-1-fast-reasoning
```

## Provider Auto-Discovery

Providers are detected automatically when their env var is set:

| Env Var | Provider | Base URL | Capabilities |
|---------|----------|----------|---------------|
| `XAI_TOKEN` | Grok | https://api.x.ai/v1 | vision, files, search, code_exec, stateful, agent |
| `OPENAI_TOKEN` | OpenAI | https://api.openai.com/v1 | vision, files |
| `GROQ_TOKEN` | Groq | https://api.groq.com/openai/v1 | chat only |
| `TOGETHER_TOKEN` | Together AI | https://api.together.xyz/v1 | chat only |
| `MISTRAL_TOKEN` | Mistral | https://api.mistral.ai/v1 | files |
| `DEEPSEEK_TOKEN` | DeepSeek | https://api.deepseek.com/v1 | chat only |
| `OLLAMA_HOST` / running | Ollama | http://localhost:11434/v1 | chat only |
| LM Studio running | LM Studio | http://localhost:1234/v1 | chat only |
| Jan running | Jan | http://localhost:1337/v1 | chat only |

Set one or more tokens in `.env`:

```
XAI_TOKEN=xai-...
OPENAI_TOKEN=sk-...
GROQ_TOKEN=gsk_...
```

First token in the file becomes the default provider. Use `--provider` to pick a specific one.

## Persistent Configuration

For fine-grained control, edit `configs/default.yaml`:

```yaml
providers:
  - name: "grok"
    token_env: "XAI_TOKEN"
    default: true
    default_model: "grok-4-1-fast-reasoning"
    capabilities:
      vision: true
      files: true
      search: true
      code_exec: true
      stateful: true
      agent: true
    models:
      - name: "grok-4-1-fast-reasoning"
        type: "chat"
      - name: "grok-4-1-fast-reasoning-vision"
        type: "vision"
      - name: "grok-imagine-image"
        type: "image_gen"
```

Any `base_url`, `token`, `default_model`, or `models` not specified are filled from built-in provider specs.

## Claude Desktop Integration

```json
{
  "mcpServers": {
    "grok-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/AgentSpawnMCP", "run", "python", "main.py", "main", "--provider", "grok"],
      "env": { "XAI_TOKEN": "xai-..." }
    },
    "ollama-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/AgentSpawnMCP", "run", "python", "main.py", "main", "--local", "--model", "llama3"],
      "env": {}
    },
    "groq-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/AgentSpawnMCP", "run", "python", "main.py", "main", "--provider", "groq"],
      "env": { "GROQ_TOKEN": "gsk_..." }
    }
  }
}
```

## Claude Code

```bash
claude mcp add grok-mcp -e XAI_TOKEN=xai-... -- uv run --directory /path/to/AgentSpawnMCP python main.py main --provider grok
claude mcp add ollama-mcp -- uv run --directory /path/to/AgentSpawnMCP python main.py main --local --model llama3
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_providers` | All discovered providers (config mode only) |
| `list_models` | Models for the active provider |
| `chat` | Text completion with optional session history |
| `stateful_chat` | Server-side conversation via `response_id` |
| `chat_with_vision` | Analyze images (jpg/jpeg/png) |
| `generate_image` | Create or edit images from text |
| `upload_file` / `list_files` / `get_file_content` / `delete_file` | File management |
| `chat_with_files` | Chat with uploaded documents |
| `web_search` | Agentic web search |
| `code_executor` | Execute code |
| `agent` | Unified agent |
| `list_chat_sessions` / `get_chat_history` / `clear_chat_history` | Session history |

## AgentSpawnMCP — Spawn Agents on Any Provider

AgentSpawnMCP lets Claude Code and OpenCode spawn agents on any OpenAI-compatible LLM provider. One MCP instance = one provider. Configure tokens and endpoints directly in your MCP client config — no server-side config needed.

### What It Does

Claude Code / OpenCode can use this to delegate tasks to other LLMs (Minimax, GLM, ChatGPT, etc.) for specialized or parallel work. Each spawned agent runs a single task and returns the result with metadata.

### Quick Example

```bash
uv run python main.py spawn \
  --name minimax \
  --url https://api.minimax.io \
  --token your-minimax-token \
  --model MiniMax-M2.7
```

### API Types

- `--api-type openai` (default) — OpenAI-compatible API (`/v1/chat/completions`)
- `--api-type anthropic` — Anthropic API (`/v1/messages`)

### URL Handling

For Anthropic API, if your provider uses a base path like `/anthropic/v1`, include it in the URL:

```bash
# Anthropic-compatible endpoint with custom path
uv run python main.py spawn \
  --name minimax \
  --url https://api.minimax.io/anthropic/v1 \
  --token your-token \
  --model MiniMax-M2.7 \
  --api-type anthropic
```

### Claude Code / OpenCode Integration

Add to your `.mcp.json`:

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

Claude Code / OpenCode will see `minimax_agent(task, model?, system_prompt?, ...)` and `claude_agent(task, model?, system_prompt?, ...)` as available tools.

### Tools Exposed

- `{name}_agent(task, model?, system_prompt?, temperature?, max_tokens?, timeout?)` — Spawn agent for task execution
- `agent_info()` — Get current provider info

### Return Format

```python
{
    "result": "...",  # Agent response text
    "metadata": {
        "provider": "minimax",
        "model_used": "MiniMax-M2.7",
        "usage": {"prompt_tokens": 100, "completion_tokens": 500},
        "latency_ms": 2340
    }
}
```

### Architecture

```
main.py (typer CLI)
  ├─ load_config() → discover providers from env vars or YAML
  └─ create_server(active_provider)
        └─ register_all_tools()
              └─ get_active_provider() → OpenAICompatProvider → httpx

Provider selection:
  --provider flag       → from config
  --url / --local flag  → inline ProviderConfig (no YAML needed)
  env var present       → auto-discovered from BUILTIN_PROVIDERS
```

## License

MIT — see [LICENSE](LICENSE)
