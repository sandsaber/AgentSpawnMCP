from mcp.server.fastmcp import FastMCP
from ..config import get_active_provider


def register_agent_tools(mcp: FastMCP) -> None:
    from ..providers import OpenAICompatProvider
    from ..utils import load_history, save_history, encode_image_to_base64

    @mcp.tool()
    async def agent(
        prompt: str,
        model: str | None = None,
        session: str | None = None,
        file_ids: list[str] | None = None,
        image_urls: list[str] | None = None,
        image_paths: list[str] | None = None,
        use_web_search: bool = False,
        use_code_execution: bool = False,
        allowed_domains: list[str] | None = None,
        excluded_domains: list[str] | None = None,
        include_citations: bool = False,
        system_prompt: str | None = None,
        max_turns: int | None = None,
    ):
        """
        Unified agent combining files, images, web search, and code execution.
        """
        p = get_active_provider()
        client = OpenAICompatProvider(name=p.name, base_url=p.base_url, api_key=p.resolve_token())
        model = model or p.default_model_name()

        history = load_history(p.name, session) if session else []
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(history)

        tools = []
        if use_web_search:
            if not p.capabilities.search:
                raise ValueError(f"Provider `{p.name}` does not support web search.")
            tools.append({"type": "web_search", "web_search": {}})
        if use_code_execution:
            if not p.capabilities.code_exec:
                raise ValueError(f"Provider `{p.name}` does not support code execution.")
            tools.append({"type": "code_execution", "code_execution": {}})

        include_opts = []
        if include_citations:
            include_opts.append("citations")

        content_items = []
        if file_ids:
            for fid in file_ids:
                content_items.append({"type": "file", "file": {"file_id": fid}})
        if image_urls:
            for url in image_urls:
                content_items.append({"type": "image_url", "image_url": {"url": url}})
        if image_paths:
            for path in image_paths:
                ext = path.rsplit(".", 1)[-1].lower() if "." in path else "png"
                b64 = encode_image_to_base64(path)
                content_items.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/{ext};base64,{b64}"},
                })

        content_items.append({"type": "text", "text": prompt})
        messages.append({"role": "user", "content": content_items})

        chat_kwargs: dict = {"model": model, "messages": messages}
        if tools:
            chat_kwargs["tools"] = tools
        if include_opts:
            chat_kwargs["include"] = include_opts
        if max_turns:
            chat_kwargs["max_turns"] = max_turns

        resp = client.chat(**chat_kwargs)
        msg = resp["choices"][0]["message"]
        result = msg.get("content", "")

        if session:
            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": result})
            save_history(p.name, session, history)

        output_parts = [result]
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                if tc.get("type") == "web_search":
                    citations = tc["web_search"].get("citations", [])
                    if citations:
                        output_parts.append("\n\n**Sources:**")
                        for url in citations[:10]:
                            output_parts.append(f"- {url}")

        return "\n".join(output_parts)
