import time
from typing import Any
from ...providers import OpenAICompatProvider


def _content_to_text(content: Any) -> str:
    """Normalize provider content blocks into plain text for MCP clients."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if text is not None:
                    parts.append(str(text))
        if parts:
            return "".join(parts)
    return str(content)


def _extract_assistant_content(response: dict[str, Any]) -> str:
    if not isinstance(response, dict):
        raise ValueError("Provider response must be a JSON object.")

    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            if isinstance(message, dict) and "content" in message:
                return _content_to_text(message["content"])
            if "text" in first_choice:
                return _content_to_text(first_choice["text"])

    if "content" in response:
        return _content_to_text(response["content"])

    raise ValueError("Provider response did not include assistant content.")


def _create_agent_tool(
    provider_name: str,
    api_url: str,
    api_token: str,
    default_model: str,
    api_type: str = "openai",
):
    """
    Factory: creates an agent tool function for a specific provider.

    The provider client is created lazily on first invocation and reused
    across subsequent calls so the underlying httpx connection pool is
    shared. Per-call ``timeout`` is applied at request level.
    """
    client_holder: dict[str, OpenAICompatProvider] = {}

    def _get_client(timeout_seconds: float) -> OpenAICompatProvider:
        existing = client_holder.get("client")
        if existing is not None:
            return existing
        client = OpenAICompatProvider(
            name=provider_name,
            base_url=api_url,
            api_key=api_token,
            api_type=api_type,
            timeout=timeout_seconds,
        )
        client_holder["client"] = client
        return client

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
        if not task or not task.strip():
            raise ValueError("Agent task must not be empty.")

        selected_model = (model or default_model or "").strip()
        if not selected_model:
            raise ValueError("No model provided. Start the server with --model or pass model to the tool.")

        timeout_seconds = float(timeout)
        if timeout_seconds <= 0:
            raise ValueError("timeout must be greater than zero.")
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero when provided.")

        client = _get_client(timeout_seconds)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": task})

        start = time.perf_counter()
        resp = client.chat(
            model=selected_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout_seconds,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        content = _extract_assistant_content(resp)
        usage = resp.get("usage", {})
        if not isinstance(usage, dict):
            usage = {}

        return {
            "result": content,
            "metadata": {
                "provider": provider_name,
                "model_used": selected_model,
                "usage": usage,
                "latency_ms": latency_ms,
            }
        }

    agent_tool.__name__ = f"{provider_name}_agent"
    agent_tool.__doc__ = f"Spawn agent on {provider_name.upper()} for task execution."

    return agent_tool
