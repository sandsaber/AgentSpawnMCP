from mcp.server.fastmcp import FastMCP
from .tools import register_tools


def create_agent_spawn_server(
    name: str = "AgentSpawnMCP",
    provider_name: str = "agent",
    api_url: str = "",
    api_token: str = "",
    default_model: str = "",
    api_type: str = "openai",
) -> FastMCP:
    """
    Build and return a FastMCP server wired with agent tools.

    Args:
        name: Server display name.
        provider_name: Provider identifier (used in tool name: {provider_name}_agent).
        api_url: API base URL.
        api_token: API token.
        default_model: Default model name.
        api_type: API type — 'openai' or 'anthropic' (default: 'openai').

    Call .run(transport='stdio') on the returned instance to start.
    """
    mcp = FastMCP(name=name)
    register_tools(
        mcp,
        provider_name=provider_name,
        api_url=api_url,
        api_token=api_token,
        default_model=default_model,
        api_type=api_type,
    )
    return mcp
