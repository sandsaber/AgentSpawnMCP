# Changelog

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
