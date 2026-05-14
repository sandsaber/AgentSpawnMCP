import os
import sys
from typing import Literal
import typer
from dotenv import load_dotenv

app = typer.Typer(help="AgentSpawnMCP — Universal OpenAI-compatible MCP server")

load_dotenv("example.env")


@app.callback()
def common(
    ctx: typer.Context,
    provider: str | None = typer.Option(
        None, "--provider", "-p",
        help="Provider name from config file. Required unless --local is used.",
    ),
    config: str | None = typer.Option(
        None, "--config", "-c",
        help="Path to YAML config file (default: configs/default.yaml).",
    ),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["provider"] = provider
    ctx.obj["config"] = config


@app.command()
def main(
    ctx: typer.Context,
    url: str | None = typer.Option(
        None, "--url", "-u",
        help="API base URL (e.g. http://localhost:11434/v1). Overrides --provider.",
    ),
    token: str | None = typer.Option(
        None, "--token", "-t",
        help="API token. Overrides --provider. Can also set via OPENAI_TOKEN env var.",
    ),
    model: str | None = typer.Option(
        None, "--model", "-m",
        help="Model name (e.g. llama3, gpt-4o). Overrides provider default.",
    ),
    local: bool = typer.Option(
        False, "--local", "-l",
        help="Shortcut for --url http://localhost:11434/v1 --model llama3.",
    ),
) -> None:
    """
    Start the AgentSpawnMCP server.

    Two modes:

      1) From config (recommended for persistent setup):
           uv run python main.py main --provider grok
           uv run python main.py main --provider openai

      2) Ad-hoc (for local models, quick tests, one-off runs):
           uv run python main.py main --url http://localhost:11434/v1 --model llama3
           uv run python main.py main --local                       # uses localhost:11434 + llama3
           uv run python main.py main --local --token ollama-token  # with token auth
           uv run python main.py main --url http://my-llm:8000/v1 --model chatgpt-4o-latest

    Run multiple instances for multiple providers simultaneously.
    """
    from src.config import get_active_provider
    from src.config.models import ProviderConfig, Capabilities, ModelConfig

    provider_name = ctx.obj.get("provider")
    cfg_path = ctx.obj.get("config") or "configs/default.yaml"
    inline_provider: ProviderConfig | None = None

    if local and url is None:
        url = "http://localhost:11434/v1"
    if local and model is None:
        model = "llama3"

    if url:
        token_val = token or os.getenv("OPENAI_TOKEN", "")
        if not token_val:
            token_val = os.getenv("LOCAL_TOKEN", "")

        inline_provider = ProviderConfig(
            name="local",
            base_url=url,
            token=token_val,
            default_model=model or "llama3",
            default=True,
            capabilities=Capabilities(
                vision=False,
                files=False,
                search=False,
                code_exec=False,
                stateful=False,
                agent=False,
            ),
            models=[ModelConfig(name=model or "llama3", type="chat")],
        )

    from src.server import create_server

    try:
        mcp = create_server(
            config_path=cfg_path,
            active_provider=provider_name,
            inline_provider=inline_provider,
            model_override=model if inline_provider is None else None,
        )
    except Exception as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)

    active = get_active_provider()
    if inline_provider is not None:
        print(
            f"Starting AgentSpawnMCP (local mode, url={active.base_url}, model={active.default_model_name()})",
            file=sys.stderr,
        )
    else:
        print(
            f"Starting AgentSpawnMCP (provider={active.name}, base_url={active.base_url})",
            file=sys.stderr,
        )

    mcp.run(transport="stdio")


@app.command()
def spawn(
    name: str = typer.Option(
        ..., "--name", "-n",
        help="Provider name (used in tool name: {name}_agent).",
    ),
    url: str = typer.Option(
        ..., "--url", "-u",
        help="API base URL (e.g. https://api.minimax.chat/v1).",
    ),
    token: str = typer.Option(
        ..., "--token", "-t",
        help="API token.",
    ),
    model: str | None = typer.Option(
        None, "--model", "-m",
        help="Default model name (optional).",
    ),
    api_type: Literal["openai", "anthropic"] = typer.Option(
        "openai", "--api-type",
        help="API type: 'openai' or 'anthropic' (default: openai).",
    ),
):
    """
    Start AgentSpawnMCP server for spawning agents on a configured provider.

    Example:

      uv run python main.py spawn \\
        --name minimax \\
        --url https://api.minimax.io \\
        --token your-minimax-token \\
        --model MiniMax-M2.7

      # For Anthropic-compatible API:
      uv run python main.py spawn \\
        --name claude \\
        --url https://api.anthropic.com \\
        --token your-anthropic-token \\
        --model claude-sonnet-4-20250514 \\
        --api-type anthropic

    Each instance exposes a single {name}_agent tool for task execution.
    """
    from src.agent_spawn import create_agent_spawn_server

    print(
        f"Starting AgentSpawnMCP (name={name}, url={url}, api_type={api_type}, model={model or 'default'})",
        file=sys.stderr,
    )

    mcp = create_agent_spawn_server(
        provider_name=name,
        api_url=url,
        api_token=token,
        default_model=model or "",
        api_type=api_type,
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    app()
