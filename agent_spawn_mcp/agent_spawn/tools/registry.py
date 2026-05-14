from mcp.server.fastmcp import FastMCP
from .base import _create_agent_tool


def register_tools(
    mcp: FastMCP,
    provider_name: str,
    api_url: str,
    api_token: str,
    default_model: str,
    api_type: str = "openai",
) -> None:
    """
    Register agent tools for a provider.

    Creates:
    - {provider_name}_agent tool for task execution
    - agent_info tool for current provider info
    """
    @mcp.tool()
    async def agent_info() -> str:
        """
        Get information about the current agent provider.
        """
        return (
            f"**Provider:** {provider_name}\n"
            f"**API URL:** {api_url}\n"
            f"**API Type:** {api_type}\n"
            f"**Default Model:** {default_model}"
        )

    agent_tool = _create_agent_tool(
        provider_name=provider_name,
        api_url=api_url,
        api_token=api_token,
        default_model=default_model,
        api_type=api_type,
    )
    mcp.tool()(agent_tool)
