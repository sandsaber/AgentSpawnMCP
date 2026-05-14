# Changelog

## 2.0.0 - 2026-05-14

### Breaking

- Renamed the installed package from `src` to `agent_spawn_mcp`. The
  `agent-spawn-mcp` CLI script and `uvx agent-spawn-mcp` invocations are
  unchanged. Code that imported `from src.*` against this package must
  update to `from agent_spawn_mcp.*`.

### Fixed

- `load_dotenv("example.env")` no longer overrides real `.env` files. Both
  the CLI entry point and the config loader now call `load_dotenv()` so the
  user's `.env` (created via `cp example.env .env`) is actually loaded.
- `list_chat_sessions` no longer raises `KeyError` on histories that were
  written before timestamps were recorded; missing `time` falls back to
  `"?"`. New entries written by `save_history` always include a
  `time` field.
- Removed the `__import__("base64")` hack in `agent_spawn_mcp.utils`; the
  module imports `base64` once at the top level.

### Changed

- `OpenAICompatProvider` now keeps one `httpx.Client` per instance and the
  spawn-agent factory reuses a single provider across calls, so HTTP
  connections are pooled instead of opened and closed per request.
  Per-call `timeout` is applied at request level.
- `web_search` (full server) and the `agent` tool now forward
  `allowed_domains` / `excluded_domains` into the underlying `web_search`
  tool payload. Both raise on mutually exclusive arguments.
- `BaseProvider` abstract return types now reflect the actual
  implementation (`dict` / `bytes`) instead of misleading
  `httpx.Response`. The unused default `_request` helper has been removed.
- Added the `Programming Language :: Python :: 3.13` trove classifier.

## 1.1.3 - 2026-05-14

### Changed

- Refreshed the lockfile to the latest compatible dependency versions.
- Updated GitHub Actions to use locked dependency installs for tests and to
  check the lockfile before publishing.
- Added `--token-env` for spawn-agent MCP servers so persistent client configs
  can reference token environment variables.
- Added README instructions for registering AgentSpawnMCP in Codex CLI.
- Added a README hero image.

## 1.1.2 - 2026-05-14

### Fixed

- Fixed spawn-agent response extraction for providers that return text content
  blocks instead of a plain string.
- Fixed full-server `--url` and `--local` startup so inline providers are not
  overwritten by a second YAML config load.
- Fixed full-server `--model` override so it is applied after the active
  provider is loaded.
- Fixed the `list_providers` MCP tool by avoiding a helper/function name
  collision.

### Changed

- Added early validation for empty spawn-agent tasks, missing models, invalid
  timeouts, invalid `max_tokens`, and unsupported API types.
- Restricted the CLI `--api-type` option to `openai` or `anthropic`.
- Expanded `AGENTS.md` into a more complete developer guide with provider
  loading rules, tool patterns, validation expectations, and release-relevant
  gotchas.

### Tests

- Added coverage for spawn-agent metadata, text-block normalization, input
  validation, inline providers, model overrides, `list_providers`, and API type
  validation.
