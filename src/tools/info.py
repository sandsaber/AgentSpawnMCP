from mcp.server.fastmcp import FastMCP
from ..config import get_active_provider, list_providers


def register_info_tools(mcp: FastMCP) -> None:
    """Register informational tools: list_providers, list_models."""

    @mcp.tool(annotations={"readOnlyHint": True})
    async def list_providers():
        """List all configured providers and their models."""
        all_providers = list_providers()
        result = ["**Configured Providers:**\n"]
        for p in all_providers:
            default_marker = " (default)" if p.default else ""
            caps = p.capabilities
            cap_lines = []
            if caps.vision:
                cap_lines.append("vision")
            if caps.files:
                cap_lines.append("files")
            if caps.search:
                cap_lines.append("search")
            if caps.code_exec:
                cap_lines.append("code_exec")
            if caps.stateful:
                cap_lines.append("stateful")
            caps_str = ", ".join(cap_lines) if cap_lines else "none"
            models_str = ", ".join(m.name for m in p.models)
            result.append(f"### {p.name}{default_marker}")
            result.append(f"- **Base URL:** {p.base_url}")
            result.append(f"- **Default model:** {p.default_model_name()}")
            result.append(f"- **Models:** {models_str}")
            result.append(f"- **Capabilities:** {caps_str}\n")
        return "\n".join(result)

    @mcp.tool(annotations={"readOnlyHint": True})
    async def list_models():
        """List available models for the active provider."""
        from ..config import get_active_provider

        p = get_active_provider()
        result = [f"**Models for `{p.name}`:**\n"]
        for m in p.models:
            result.append(f"- **{m.name}** — type: {m.type}")
        return "\n".join(result)
