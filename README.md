# AgentSpawnMCP

Universal MCP server for any OpenAI-compatible LLM. Supports OpenAI and Anthropic API formats, cloud providers (OpenAI, Grok, Claude, Minimax, DeepSeek) and local models (Ollama, LM Studio, Jan). Built on FastMCP with pure httpx.

## Quick Start — Spawn Agents

```bash
# No install needed — run directly with uvx
uvx agent-spawn-mcp spawn \
  --name minimax \
  --url https://api.minimax.io/anthropic/v1 \
  --token your-token \
  --model MiniMax-M2.7 \
  --api-type anthropic
```

Or install globally:

```bash
pip install agent-spawn-mcp
agent-spawn-mcp spawn --name minimax --url https://api.minimax.io --token TOKEN --model MiniMax-M2.7
```

## API Types

- `--api-type openai` (default) — OpenAI-compatible (`/v1/chat/completions`)
- `--api-type anthropic` — Anthropic API (`/v1/messages`)

## Claude Code / OpenCode Integration

Add to your `.mcp.json`:

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

## Tools Exposed

- `{name}_agent(task, model?, system_prompt?, temperature?, max_tokens?, timeout?)` — Spawn agent
- `agent_info()` — Get provider info

## Return Format

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

## UniOAPI-MCP — Full Server

Full MCP server with all tools (chat, vision, files, search, agent). Requires git clone.

```bash
git clone https://github.com/sandsaber/AgentSpawnMCP
cd AgentSpawnMCP
uv sync
cp example.env .env
# Edit .env with your tokens

uv run python main.py main --provider grok
```

### Auto-Discovery

Providers auto-detected when env var is set:

| Env Var | Provider |
|---------|----------|
| `XAI_TOKEN` | Grok |
| `OPENAI_TOKEN` | OpenAI |
| `GROQ_TOKEN` | Groq |
| `DEEPSEEK_TOKEN` | DeepSeek |

### Available Tools (Full Server)

| Tool | Description |
|------|-------------|
| `list_providers` | All discovered providers |
| `list_models` | Models for the active provider |
| `chat` | Text completion with session history |
| `stateful_chat` | Server-side conversation |
| `chat_with_vision` | Analyze images (jpg/jpeg/png) |
| `generate_image` | Create or edit images |
| `upload_file` / `list_files` / `get_file_content` / `delete_file` | File management |
| `chat_with_files` | Chat with documents |
| `web_search` | Agentic web search |
| `code_executor` | Execute code |
| `agent` | Unified agent |
| `list_chat_sessions` / `get_chat_history` / `clear_chat_history` | Session history |

---

## License

MIT — see [LICENSE](LICENSE)
