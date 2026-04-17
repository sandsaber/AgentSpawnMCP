from mcp.server.fastmcp import FastMCP
from .config import load_config
from .tools import register_all_tools


def create_server(
    name: str = "AgentSpawnMCP",
    config_path: str = "configs/default.yaml",
    active_provider: str | None = None,
) -> FastMCP:
    """
    Build and return a FastMCP server wired with all tools.

    Args:
        name: Server display name.
        config_path: Path to YAML config file.
        active_provider: Provider name to activate (from config). If None,
            uses the provider marked default:true, or the first one.

    Call .run(transport='stdio') on the returned instance to start.
    """
    mcp = FastMCP(name=name)
    config = load_config(config_path, active_provider=active_provider)
    register_all_tools(mcp)
    return mcp
