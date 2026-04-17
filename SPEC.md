# SPEC.md — AgentSpawnMCP

## 1. Concept & Vision

**AgentSpawnMCP** — универсальный MCP-сервер, который объединяет любые LLM-провайдеры (OpenAI-совместимые API) в единый интерфейс. Один сервер, произвольное число провайдеров/моделей, каждый со своим API-ключом — и все инструменты доступны через единый MCP-протокол без изменения кода.

Переиспользует идею и структуру Grok-MCP, но вместо жёсткой привязки к xAI — универсальный адаптер через HTTP REST вызовы к OpenAI-совместимым эндпоинтам.

Ощущение: минималистичный, прагматичный, "настраиваешь — и работает".

## 2. Design Language

- **Aesthetic**: утилитарный CLI-стиль — чистый, без украшательств, фокус на функциональность
- **Палитра**: N/A (CLI-only, нет UI)
- **Типографика**: N/A
- **Иконки**: N/A
- **Анимации**: N/A

## 3. Layout & Structure

```
uniOAPI-MCP/
├── src/
│   ├── __init__.py
│   ├── server.py          # Главный FastMCP-сервер
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py        # Базовый абстрактный провайдер
│   │   └── openai_compat.py  # OpenAI-совместимый HTTP провайдер
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── chat.py        # Chat/completion tools
│   │   ├── vision.py      # Image analysis
│   │   ├── files.py       # File management
│   │   ├── search.py      # Web search (провайдерозависимо)
│   │   └── agent.py       # Agentic unified tool
│   ├── config/
│   │   ├── __init__.py
│   │   └── loader.py      # YAML config loader + env override
│   └── utils.py
├── configs/
│   └── default.yaml        # Пример конфигурации
├── tests/
│   └── ...
├── pyproject.toml
└── README.md
```

## 4. Features & Interactions

### 4.1 Multi-Provider Config

Каждая конфигурация — провайдер с набором моделей. Конфиг в YAML:

```yaml
providers:
  - name: "grok"
    api_key_env: "XAI_API_KEY"      # Имя env var (не значение)
    base_url: "https://api.x.ai/v1"  # OpenAI-совместимый endpoint
    default_model: "grok-4-1-fast-reasoning"
    models:
      - name: "grok-4-1-fast-reasoning"
        type: "chat"
      - name: "grok-4-1-fast-reasoning-vision"
        type: "vision"

  - name: "openai"
    api_key_env: "OPENAI_API_KEY"
    base_url: "https://api.openai.com/v1"
    default_model: "gpt-4o"
    models:
      - name: "gpt-4o"
        type: "chat"
      - name: "gpt-4o-mini"
        type: "chat"
      - name: "gpt-4-turbo"
        type: "vision"
```

### 4.2 Provider Selection Per Tool

Каждый MCP-инструмент принимает опциональный параметр `provider` (название). Если не указан — используется провайдер с пометкой `default: true` (или первый в списке).

```python
@mcp.tool()
async def chat(prompt: str, provider: Optional[str] = None, model: Optional[str] = None, ...):
    cfg = config.get_provider(provider)
    client = cfg.get_client()
    ...
```

### 4.3 Core Tools (per provider)

| Tool | Описание |
|------|----------|
| `list_providers` | Список всех настроенных провайдеров и их моделей |
| `list_models` | Модели конкретного провайдера (delegate к `/models`) |
| `chat` | Текстовый чат с history-сессиями |
| `chat_with_vision` | Анализ изображений |
| `stateful_chat` | Продолжениеconversation по response_id (если провайдер поддерживает) |
| `upload_file` | Загрузка файла |
| `list_files` | Список файлов |
| `get_file_content` | Содержимое файла |
| `delete_file` | Удаление файла |
| `chat_with_files` | Чат с документами |
| `web_search` | Веб-поиск (если провайдер поддерживает tools) |
| `code_executor` | Выполнение кода (если провайдер поддерживает) |

### 4.4 Provider Capabilities

Не все провайдеры поддерживают все функции. Каждый провайдер декларирует capabilities:

```yaml
capabilities:
  vision: true
  files: true        # /v1/files endpoint
  search: true        # web_search tool
  code_exec: true    # code_execution tool
  stateful: true     # conversation persistence
  agent: true        # unified agent tool
```

Если capability нет — tool возвращает informative error.

### 4.5 Session History

Аналогично Grok-MCP: JSON-файлы в `chats/{provider}_{session}.json`. Формат тот же.

### 4.6 Error Handling

- Missing API key → чёткое сообщение с инструкцией
- Provider not found → list available providers
- Model not found → list models for provider
- Capability not supported → informative error
- Network error → propagate as-is

## 5. Component Inventory

### 5.1 `ProviderConfig`
```python
name: str
api_key: str          # resolved from env var
base_url: str
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
- **Serialization**: `pydantic>=2.9` для validated config models

### API Pattern (OpenAI-Compatible)
Все запросы — REST HTTP к `{base_url}/{path}`:

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
В отличие от Grok-MCP, здесь **нет SDK** — только голый HTTP. Это обеспечивает совместимость с любым OpenAI-совместимым провайдером.

### Config Loading Order
1. Load `configs/default.yaml`
2. Override via environment variables matching pattern `PROVIDER_{NAME}_API_KEY`, `PROVIDER_{NAME}_BASE_URL`
3. Validate with Pydantic

### Tool Naming Convention
Инструменты НЕ префиксируются именем провайдера. Выбор провайдера — через параметр `provider`. Это позволяет прозрачно переключаться между провайдерами без смены вызовов.
