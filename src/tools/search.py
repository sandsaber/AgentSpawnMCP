from mcp.server.fastmcp import FastMCP
from ..config import get_active_provider


def register_search_tools(mcp: FastMCP) -> None:
    from ..providers import OpenAICompatProvider

    @mcp.tool(annotations={"readOnlyHint": True})
    async def web_search(
        prompt: str,
        model: str | None = None,
        allowed_domains: list[str] | None = None,
        excluded_domains: list[str] | None = None,
        include_citations: bool = False,
        max_turns: int | None = None,
    ):
        """
        Web search via agentic tool. Provider must support search capability.
        """
        p = get_active_provider()
        if not p.capabilities.search:
            raise ValueError(f"Provider `{p.name}` does not support web search.")

        client = OpenAICompatProvider(name=p.name, base_url=p.base_url, api_key=p.resolve_token())
        model = model or p.default_model_name()

        if allowed_domains and excluded_domains:
            raise ValueError("Cannot specify both allowed_domains and excluded_domains")

        include_opts = ["citations"] if include_citations else None

        resp = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            tools=[{"type": "web_search", "web_search": {}}],
            include=include_opts,
            max_turns=max_turns,
        )

        msg = resp["choices"][0]["message"]
        content = msg.get("content", "")
        citations = []
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                if tc.get("type") == "web_search" and tc.get("web_search"):
                    citations.extend(tc["web_search"].get("citations", []))

        result = [content]
        if citations:
            result.append("\n\n**Sources:**")
            for url in citations[:10]:
                result.append(f"- {url}")
        return "\n".join(result)

    @mcp.tool()
    async def code_executor(
        prompt: str,
        model: str | None = None,
        max_turns: int | None = None,
    ):
        """
        Execute code for calculations and analysis.
        Provider must support code_exec capability.
        """
        p = get_active_provider()
        if not p.capabilities.code_exec:
            raise ValueError(f"Provider `{p.name}` does not support code execution.")

        client = OpenAICompatProvider(name=p.name, base_url=p.base_url, api_key=p.resolve_token())
        model = model or p.default_model_name()

        resp = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            tools=[{"type": "code_execution", "code_execution": {}}],
            include=["code_execution_call_output"],
            max_turns=max_turns,
        )

        msg = resp["choices"][0]["message"]
        content = msg.get("content", "")
        code_outputs = []
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                if tc.get("type") == "code_execution":
                    code_outputs.append(tc["code_execution"].get("output", ""))

        result = [content]
        if code_outputs:
            result.append("\n\n**Code Output(s):**")
            for out in code_outputs:
                result.append(f"```\n{out}\n```")
        return "\n".join(result)
