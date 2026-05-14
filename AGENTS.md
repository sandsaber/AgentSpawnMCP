# AgentSpawnMCP - Developer Guide

AgentSpawnMCP is a universal MCP server for OpenAI-compatible and
Anthropic-compatible LLM HTTP APIs. It is built on FastMCP and plain `httpx`.
Do not add provider SDKs unless the project explicitly changes direction.

The core design goal is provider portability: new providers should usually be
configuration, CLI arguments, or small request-shape changes, not new client
stacks.

## Operating Modes

### 1. Spawn Agents MCP server (recommended integration path)

Runs from an installed package or directly through `uvx`. It exposes one
provider-specific agent tool plus `agent_info`.

```bash
uvx agent-spawn-mcp spawn \
  --name minimax \
  --url https://api.minimax.io/anthropic/v1 \
  --token TOKEN \
  --model MiniMax-M2.7 \
  --api-type anthropic
```

Use this mode for Claude Code, OpenCode, Codex MCP, and other MCP clients when
the user only needs to delegate tasks to a single external model/provider.

### 2. Full MCP server

Runs from a cloned checkout and registers the full tool set: chat, stateful
chat, vision, files, search, image generation, provider info, and agent tools.

```bash
git clone https://github.com/sandsaber/AgentSpawnMCP
cd AgentSpawnMCP
uv sync
uv run python main.py main --provider grok
```

Use this mode when the user needs the configured provider catalog and the
general-purpose MCP tools.

## Repository Map

```text
main.py                         # Thin CLI shim to src.__main__:app
src/__main__.py                 # Typer CLI: main and spawn commands
src/server.py                   # create_server() for the full server
src/utils.py                    # Local chat history helpers
src/config/models.py            # Pydantic config models and BUILTIN_PROVIDERS
src/config/loader.py            # load_config(), active provider globals
src/providers/base.py           # Base provider shape
src/providers/openai_compat.py  # HTTP client for OpenAI/Anthropic-style APIs
src/tools/                      # Full server MCP tool registration modules
src/agent_spawn/server.py       # create_agent_spawn_server()
src/agent_spawn/tools/base.py   # _create_agent_tool() factory
src/agent_spawn/tools/registry.py
configs/default.yaml            # Default full-server provider catalog
tests/                          # Request-shape and URL-construction tests
```

## Development Commands

```bash
uv sync
uv run pytest
uv run pytest tests/test_url_construction.py tests/test_request_shape.py
uv run python main.py --help
uv run python main.py spawn --help
uv run python main.py main --help
```

The current test suite uses mocked HTTP transport for provider request-shape
checks. Do not make live provider calls in tests unless a task explicitly asks
for an integration test.

## Provider Loading Rules

`src/config/loader.py` is the source of truth for the full server config flow.

1. `load_dotenv("example.env")` is called before config is resolved.
2. If the YAML config contains `providers`, those entries are used.
3. If the YAML config has no providers and discovery is enabled,
   `discover_providers()` scans known env vars and local URLs.
4. After providers are built, `PROVIDER_{NAME}_TOKEN`,
   `PROVIDER_{NAME}_BASE_URL`, and `PROVIDER_{NAME}_DEFAULT_MODEL` override
   matching provider fields.
5. The active provider is the requested `--provider`, otherwise the provider
   marked `default: true`, otherwise the first provider.

Do not describe provider discovery as a simple env/local/YAML priority chain:
YAML provider entries take precedence over discovery, while provider-specific
env overrides still apply after YAML loading.

## Built-In Providers

`BUILTIN_PROVIDERS` lives in `src/config/models.py`.

Current built-in keys:

```text
grok, openai, groq, ollama, lm-studio, jan, together, mistral, deepseek, zai
```

For full-server built-ins:

1. Add or update the provider entry in `BUILTIN_PROVIDERS`.
2. Add `PROVIDER_TOKEN_ENV` only when the provider can be discovered from a
   standard token env var.
3. Add `PROVIDER_DEFAULT_MODEL_ENV` only for local/provider-specific default
   model env overrides.
4. Update `configs/default.yaml` if the provider should appear in the default
   cloned configuration.
5. Update README examples when the provider changes user-facing setup.

For spawn mode, adding a provider normally requires no code change. Use a new
`--name`, `--url`, `--token`, and optional `--model`.

## API Type Rules

`--api-type openai` is the default and uses the OpenAI chat-completions request
shape.

`--api-type anthropic` uses Anthropic `/v1/messages`, adds the
`anthropic-version` header, extracts system messages, and normalizes the result
back into an OpenAI-like `choices[0].message.content` shape.

Keep these compatibility rules centralized in
`src/providers/openai_compat.py`. Tool modules should not reimplement provider
request formatting.

## URL Construction Contract

`OpenAICompatProvider._url()` intentionally strips a leading `v1/` path segment
when `base_url` already contains a version segment such as `/v1` or `/v4`.

Examples covered by tests:

```text
https://api.openai.com/v1 + v1/chat/completions
  -> https://api.openai.com/v1/chat/completions

https://api.z.ai/api/paas/v4 + v1/chat/completions
  -> https://api.z.ai/api/paas/v4/chat/completions

https://api.z.ai/api/anthropic + v1/messages
  -> https://api.z.ai/api/anthropic/v1/messages
```

Any change to URL joining must update and pass
`tests/test_url_construction.py`.

## Full Server Tool Pattern

Full-server tools live in `src/tools/` and are registered from
`src/tools/__init__.py`.

Use this pattern:

1. Define `register_<area>_tools(mcp: FastMCP) -> None`.
2. Inside each MCP tool, call `get_active_provider()`.
3. Check `p.capabilities.<feature>` before using optional provider features.
4. Instantiate `OpenAICompatProvider(name=p.name, base_url=p.base_url,
   api_key=p.resolve_token())`.
5. Use `model or p.default_model_name()`.
6. Register the module from `register_all_tools()`.

Avoid network calls at import time. Keep provider-specific branching in the
provider client or config model unless a tool is truly feature-specific.

MCP tool function names become public tool names. Avoid shadowing imported
helpers with the same Python name inside a registration function; alias helper
imports if needed.

## Spawn Tool Interface

Spawn mode exposes this provider-specific tool:

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

Return shape:

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

`src/agent_spawn/tools/base.py` should stay small: it builds messages, calls
`OpenAICompatProvider.chat()`, measures latency, and returns normalized output.

## OpenAICompatProvider Contract

Important behavior in `src/providers/openai_compat.py`:

- Use `httpx.Client`, not provider SDKs.
- Include response body text in raised `httpx.HTTPStatusError` messages.
- For OpenAI-style chat, omit `max_tokens` when the caller passes `None`.
- For Anthropic-style chat, default omitted `max_tokens` to `16384`.
- Only send `store_messages` when it is true.
- Normalize Anthropic usage into `prompt_tokens` and `completion_tokens`.
- `generate_image()` uses the OpenAI `/images/generations` shape only.
- File APIs use the OpenAI-style `/files` endpoints.

If a provider needs a materially different image, file, or agent API shape, do
not hide that behind misleading OpenAI-compatible names. Document the gap and
add a clearly scoped adapter.

## State and Generated Files

- Session history is stored under `chats/`; the directory is ignored by git.
- `resolve_token()` returns an empty string when neither `token` nor
  `token_env` resolves.
- `token` means the direct secret value; `token_env` means the env var name.
- Vision tools support local `jpg`, `jpeg`, and `png` files only.
- Local URL probing can take about three seconds per local port when discovery
  mode is used.

## Security Rules

- Never commit real API tokens.
- Avoid printing tokens or full auth headers.
- `--token` passed on the command line can be visible in process listings and
  crash logs; mention this in user-facing setup docs when relevant.
- Keep example configs as templates, not secret stores.

## Validation Expectations

Run `uv run pytest` after code changes unless the task is documentation-only
and the edited docs do not affect commands or behavior.

Run focused tests when touching these areas:

```bash
uv run pytest tests/test_url_construction.py
uv run pytest tests/test_request_shape.py
```

For CLI changes, also run:

```bash
uv run python main.py --help
uv run python main.py spawn --help
uv run python main.py main --help
```

For docs-only changes, at minimum check Markdown formatting by reading the
edited file and run `git diff --check`.

## Documentation Style

- Keep project docs and code comments in English.
- Prefer provider-agnostic wording: this project is not tied to one MCP client
  or model vendor.
- Distinguish the two modes clearly: spawn mode is the lightweight integration
  path; full server is the cloned, configurable tool server.
- When documenting compatibility claims, say what is verified by tests and
  what depends on provider behavior.
