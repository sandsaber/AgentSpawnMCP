# AgentSpawnMCP

Universal MCP server for any OpenAI-compatible LLM. Supports OpenAI and Anthropic API formats, cloud providers (OpenAI, Grok, Claude, Minimax, DeepSeek) and local models (Ollama, LM Studio, Jan). Built on FastMCP with pure httpx. Zero-config via env vars; optional YAML config.

## Two Modes

### 1. AgentSpawnMCP — Spawn Agents (Recommended)

Spawn agents on any provider via CLI — one instance per provider. Configure tokens directly in your MCP client.

```bash
uvx agent-spawn-mcp spawn \
  --name minimax \
  --url https://api.minimax.io/anthropic/v1 \
  --token your-token \
  --model MiniMax-M2.7 \
  --api-type anthropic
```

### 2. UniOAPI-MCP — Full MCP Server

Full-featured MCP server with chat, vision, files, search, agent tools. Uses config/YAML.

```bash
uv run python main.py main --provider grok
uv run python main.py main --local --model llama3
```

---

## AgentSpawnMCP (Spawn Agents)

### Quick Start

```bash
# Install
uvx agent-spawn-mcp spawn --name minimax --url https://api.minimax.io --token TOKEN --model MiniMax-M2.7

# Or via pip
pip install agent-spawn-mcp
agent-spawn spawn --name minimax --url https://api.minimax.io --token TOKEN --model MiniMax-M2.7
```

### API Types

- `--api-type openai` (default) — OpenAI-compatible (`/v1/chat/completions`)
- `--api-type anthropic` — Anthropic API (`/v1/messages`)

### Claude Code / OpenCode Integration

```json
{
  "mcpServers": {
    "minimax-agent": {
      "command": "uvx",
      "args": ["agent-spawn-mcp", "spawn",
               "--name", "minimax",
               "--url", "https://api.minimax.io/anthropic/v1",
               "--token", "your-minimax-token",
               "--model", "MiniMax-M2.7",
               "--api-type", "anthropic"]
    },
    "claude-agent": {
      "command": "uvx",
      "args": ["agent-spawn-mcp", "spawn",
               "--name", "claude",
               "--url", "https://api.anthropic.com",
               "--token", "your-anthropic-token",
               "--model", "claude-sonnet-4-20250514",
               "--api-type", "anthropic"]
    }
  }
}
```

### Tools Exposed

- `{name}_agent(task, model?, system_prompt?, temperature?, max_tokens?, timeout?)`
- `agent_info()`

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

---

## UniOAPI-MCP (Full Server)

Full MCP server with all tools for the active provider.

### Quick Start

```bash
git clone https://github.com/sandsaber/AgentSpawnMCP
cd AgentSpawnMCP
uv sync
cp example.env .env
# Edit .env with your tokens

uv run python main.py main
```

### Auto-Discovery

Providers detected when env var is set:

| Env Var | Provider | Base URL |
|---------|----------|----------|
| `XAI_TOKEN` | Grok | https://api.x.ai/v1 |
| `OPENAI_TOKEN` | OpenAI | https://api.openai.com/v1 |
| `GROQ_TOKEN` | Groq | https://api.groq.com/openai/v1 |
| `DEEPSEEK_TOKEN` | DeepSeek | https://api.deepseek.com/v1 |

### Claude Desktop Integration

```json
{
  "mcpServers": {
    "grok-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/AgentSpawnMCP", "run", "python", "main.py", "main", "--provider", "grok"],
      "env": { "XAI_TOKEN": "xai-..." }
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `list_providers` | All discovered providers |
| `list_models` | Models for the active provider |
| `chat` | Text completion with session history |
| `stateful_chat` | Server-side conversation via `response_id` |
| `chat_with_vision` | Analyze images (jpg/jpeg/png) |
| `generate_image` | Create or edit images |
| `upload_file` / `list_files` / `get_file_content` / `delete_file` | File management |
| `chat_with_files` | Chat with uploaded documents |
| `web_search` | Agentic web search |
| `code_executor` | Execute code |
| `agent` | Unified agent |
| `list_chat_sessions` / `get_chat_history` / `clear_chat_history` | Session history |

---

## License

MIT — see [LICENSE](LICENSE)
