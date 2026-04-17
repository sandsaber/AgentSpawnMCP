from mcp.server.fastmcp import FastMCP
import time
from ...providers import OpenAICompatProvider


def _create_agent_tool(
    provider_name: str,
    api_url: str,
    api_token: str,
    default_model: str,
    api_type: str = "openai",
):
    """
    Factory: creates an agent tool function for a specific provider.
    """
    async def agent_tool(
        task: str,
        model: str | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int = 120,
    ) -> dict:
        """
        Spawn agent on {provider_name.upper()} for task execution.

        Args:
            task: The task description for the agent to perform.
            model: Override the default model (optional).
            system_prompt: Custom system prompt to guide the agent (optional).
            temperature: Sampling temperature 0.0-2.0 (optional).
            max_tokens: Maximum tokens in response (optional).
            timeout: Request timeout in seconds (default: 120).

        Returns:
            dict with 'result' (agent response) and 'metadata' (provider, model, usage, latency).
        """
        client = OpenAICompatProvider(
            name=provider_name,
            base_url=api_url,
            api_key=api_token,
            api_type=api_type,
        )
        model = model or default_model

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": task})

        start = time.perf_counter()
        resp = client.chat(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        content = resp["choices"][0]["message"]["content"]
        usage = resp.get("usage", {})

        return {
            "result": content,
            "metadata": {
                "provider": provider_name,
                "model_used": model,
                "usage": usage,
                "latency_ms": latency_ms,
            }
        }

    agent_tool.__name__ = f"{provider_name}_agent"
    agent_tool.__doc__ = f"Spawn agent on {provider_name.upper()} for task execution."

    return agent_tool
