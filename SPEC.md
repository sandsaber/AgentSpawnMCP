# SPEC.md — AgentSpawnMCP

## 1. Concept & Vision

**AgentSpawnMCP** — universal MCP server that combines any LLM providers (OpenAI-compatible APIs) into a single interface. One server, arbitrary number of providers/models, each with its own API key — all tools available through a unified MCP protocol without code changes.

Reuses the idea and structure of Grok-MCP, but instead of hard binding to xAI — universal adapter via HTTP REST calls to OpenAI-compatible endpoints.

Feel: minimalist, pragmatic, "configure — and it works".

## 2. Design Language

- **Aesthetic**: utilitarian CLI style — clean, no decoration, focus on functionality
- **Palette**: N/A (CLI-only, no UI)
- **Typography**: N/A
- **Icons**: N/A
- **Animations**: N/A

## 3. Layout & Structure

```
AgentSpawnMCP/
├── src/
│   ├── __init__.py
│   ├── server.py          # Main FastMCP server
│   ├── utils.py          # load_history, save_history, encode_image_to_base64
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py        # Abstract BaseProvider
│   │   └── openai_compat.py  # OpenAI-compatible HTTP provider
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── chat.py        # Chat/completion tools
│   │   ├── vision.py      # Image analysis
│   │   ├── files.py       # File management
│   │   ├── search.py      # Web search
│   │   └── agent.py       # Unified agent tool
│   ├── config/
│   │   ├── __init__.py
│   │   └── loader.py      # YAML config loader + env override
│   └── agent_spawn/        # Agent spawning module
│       ├── __init__.py
│       ├── server.py
│       └── tools/
├── configs/
│   └── default.yaml        # Example configuration
├── pyproject.toml
└── README.md
```

## 4. Features & Interactions

### 4.1 Multi-Provider Config

Each configuration is a provider with a set of models. Config in YAML:

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

### 4.2 Provider Selection Per Tool

Each MCP tool accepts optional `provider` parameter. If not specified — uses provider with `default: true` (or first in list).

### 4.3 Core Tools (per provider)

| Tool | Description |
|------|-------------|
| `list_providers` | List of all configured providers and their models |
| `list_models` | Models for a specific provider |
| `chat` | Text chat with history sessions |
| `chat_with_vision` | Image analysis |
| `stateful_chat` | Continue conversation via response_id |
| `upload_file` | File upload |
| `list_files` | List files |
| `get_file_content` | File content |
| `delete_file` | Delete file |
| `chat_with_files` | Chat with documents |
| `web_search` | Web search (if provider supports tools) |
| `code_executor` | Code execution (if provider supports) |

### 4.4 Provider Capabilities

Not all providers support all features. Each provider declares capabilities:

```yaml
capabilities:
  vision: true
  files: true        # /v1/files endpoint
  search: true        # web_search tool
  code_exec: true    # code_execution tool
  stateful: true     # conversation persistence
  agent: true        # unified agent tool
```

### 4.5 Session History

JSON files in `chats/{provider}_{session}.json`. Timestamp format: `"%d.%m.%Y %H:%M:%S"`.

### 4.6 Error Handling

- Missing API key → clear message with instructions
- Provider not found → list available providers
- Model not found → list models for provider
- Capability not supported → informative error
- Network error → propagate as-is

## 5. Component Inventory

### 5.1 `ProviderConfig`
```python
name: str
base_url: str
token: str          # resolved from env var
token_env: str
default_model: str
models: List[ModelConfig]
capabilities: Capabilities
```

### 5.2 `ModelConfig`
```python
name: str
type: Literal["chat", "vision", "embeddings"]
```

### 5.3 `Capabilities`
```python
vision: bool
files: bool
search: bool
code_exec: bool
stateful: bool
agent: bool
```

### 5.4 HTTP Client (per request)
```python
httpx.Client(timeout=120.0)
```
Headers:
```
Authorization: Bearer {api_key}
Content-Type: application/json
```

## 6. Technical Approach

### Stack
- **Runtime**: Python 3.11+
- **Package manager**: UV (Astral)
- **HTTP**: `httpx` (sync, stateless per request)
- **MCP Framework**: `mcp[cli]>=1.13.1`
- **Config**: YAML via `pyyaml` + dotenv override
- **Serialization**: `pydantic>=2.9` for validated config models

### API Pattern (OpenAI-Compatible)
All requests are REST HTTP to `{base_url}/{path}`:

```
POST /v1/chat/completions       → chat, vision, agent
GET  /v1/models                → list_models
POST /v1/images/generations    → generate_image
POST /v1/files                 → upload_file
GET  /v1/files                 → list_files
GET  /v1/files/{id}/content    → get_file_content
DELETE /v1/files/{id}          → delete_file
POST /v1/chat/completions      → web_search / code_executor (via tools param)
```

### No SDK Dependencies
Unlike Grok-MCP, there are **no SDKs** — only raw HTTP. This ensures compatibility with any OpenAI-compatible provider.

### Config Loading Order
1. Load `configs/default.yaml`
2. Override via environment variables matching pattern `PROVIDER_{NAME}_TOKEN`, `PROVIDER_{NAME}_BASE_URL`
3. Validate with Pydantic

### Tool Naming Convention
Tools are NOT prefixed with provider name. Provider selection is through `provider` parameter. This allows transparent switching between providers without changing calls.

## 7. AgentSpawnMCP (Spawn Mode)

Separate mode for spawning agents on configured providers.

### CLI Arguments
| Argument | Required | Description |
|----------|----------|-------------|
| `--name` | Yes | Provider name (tool name: `{name}_agent`) |
| `--url` | Yes | API base URL |
| `--token` | Yes | API token |
| `--model` | No | Default model name |
| `--api-type` | No | `openai` (default) or `anthropic` |

### Return Format
```python
{
    "result": "...",  # Agent response text
    "metadata": {
        "provider": "provider_name",
        "model_used": "model-name",
        "usage": {"prompt_tokens": N, "completion_tokens": N},
        "latency_ms": N
    }
}
```
