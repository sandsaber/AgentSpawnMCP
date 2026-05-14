from mcp.server.fastmcp import FastMCP
from .config import ProviderConfig, get_active_provider, load_config, set_active_provider
from .tools import register_all_tools


def create_server(
    name: str = "AgentSpawnMCP",
    config_path: str = "configs/default.yaml",
    active_provider: str | None = None,
    inline_provider: ProviderConfig | None = None,
    model_override: str | None = None,
) -> FastMCP:
    """
    Build and return a FastMCP server wired with all tools.

    Args:
        name: Server display name.
        config_path: Path to YAML config file.
        active_provider: Provider name to activate (from config). If None,
            uses the provider marked default:true, or the first one.
        inline_provider: Ad-hoc provider to use instead of loading YAML config.
        model_override: Optional model override for the active provider.

    Call .run(transport='stdio') on the returned instance to start.
    """
    mcp = FastMCP(name=name)
    if inline_provider is not None:
        set_active_provider(inline_provider)
    else:
        load_config(config_path, active_provider=active_provider)
        if model_override:
            get_active_provider().default_model = model_override
    register_all_tools(mcp)
    return mcp
