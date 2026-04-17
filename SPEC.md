# SPEC.md — AgentSpawnMCP

## 1. Concept & Vision

**AgentSpawnMCP** — universal MCP server combining any LLM providers (OpenAI-compatible APIs) into a single interface. One server, arbitrary number of providers/models, each with its own API key — all tools available through unified MCP protocol without code changes.

Feels: minimalist, pragmatic, "configure — and it works".

## 2. Design Language

- **Aesthetic**: utilitarian CLI style — clean, no decoration, focus on functionality
- **CLI-only** — no UI

## 3. Layout & Structure

```
AgentSpawnMCP/
├── src/
│   ├── __init__.py
│   ├── __main__.py       # Package entry point (uvx/pip)
│   ├── server.py         # create_server() for full server
│   ├── utils.py          # history helpers
│   ├── providers/
│   │   ├── openai_compat.py  # OpenAICompatProvider (HTTP)
│   ├── tools/
│   │   ├── chat.py, vision.py, files.py, search.py, agent.py
│   ├── config/
│   │   ├── models.py     # Pydantic models + BUILTIN_PROVIDERS
│   │   └── loader.py     # load_config()
│   └── agent_spawn/
│       ├── server.py     # create_agent_spawn_server()
│       └── tools/
│           ├── base.py   # _create_agent_tool() factory
│           └── registry.py
├── configs/
│   └── default.yaml
├── main.py               # CLI entry point for local development
└── pyproject.toml
```

## 4. Features

### AgentSpawnMCP (Spawn Agents Mode)

CLI-based agent spawning — one instance per provider. No git clone needed.

```bash
uvx agent-spawn-mcp spawn --name minimax --url ... --token ... --model ... --api-type anthropic
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--name` | Yes | Provider name (tool: `{name}_agent`) |
| `--url` | Yes | API base URL |
| `--token` | Yes | API token |
| `--model` | No | Default model |
| `--api-type` | No | `openai` (default) or `anthropic` |

### AgentSpawnMCP (Full Server Mode)

Full MCP server with all tools. Auto-discovers providers from env vars or YAML config.

## 5. Technical Stack

- **Runtime**: Python 3.11+
- **Package manager**: UV (Astral)
- **HTTP**: `httpx` (sync, stateless per request)
- **MCP Framework**: `mcp[cli]>=1.13.1`
- **Config**: YAML via `pyyaml` + dotenv
- **Validation**: `pydantic>=2.9`

### API Pattern

```
POST /v1/chat/completions       → chat, vision, agent
GET  /v1/models                → list_models
POST /v1/images/generations    → generate_image
POST /v1/files                 → upload_file
GET  /v1/files                 → list_files
GET  /v1/files/{id}/content    → get_file_content
DELETE /v1/files/{id}          → delete_file
```

### No SDK Dependencies

Only raw HTTP via `httpx` — ensures compatibility with any OpenAI-compatible provider.

## 6. Config Loading Order

1. Load `configs/default.yaml`
2. Env overrides: `PROVIDER_{NAME}_TOKEN`, `PROVIDER_{NAME}_BASE_URL`
3. Validate with Pydantic

## 7. Provider Capabilities

Each provider declares:

```yaml
capabilities:
  vision: true/false
  files: true/false
  search: true/false
  code_exec: true/false
  stateful: true/false
  agent: true/false
```

If capability not supported — tool returns informative error.