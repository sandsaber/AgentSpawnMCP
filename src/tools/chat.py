from mcp.server.fastmcp import FastMCP
from ..config import get_active_provider


def register_chat_tools(mcp: FastMCP) -> None:
    from ..utils import load_history, save_history

    @mcp.tool()
    async def chat(
        prompt: str,
        model: str | None = None,
        session: str | None = None,
        system_prompt: str | None = None,
    ):
        """
        Text chat with optional persistent session history.
        """
        p = get_active_provider()

        from ..providers import OpenAICompatProvider
        client = OpenAICompatProvider(
            name=p.name,
            base_url=p.base_url,
            api_key=p.resolve_token(),
        )
        model = model or p.default_model_name()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if session:
            history = load_history(p.name, session)
            messages.extend(history)

        messages.append({"role": "user", "content": prompt})

        resp = client.chat(model=model, messages=messages)
        content = resp["choices"][0]["message"]["content"]

        if session:
            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": content})
            save_history(p.name, session, history)

        return content

    @mcp.tool()
    async def stateful_chat(
        prompt: str,
        model: str | None = None,
        response_id: str | None = None,
        system_prompt: str | None = None,
    ):
        """
        Stateful chat via response_id for continued conversations.
        Provider must support stateful capability.
        """
        p = get_active_provider()
        if not p.capabilities.stateful:
            return f"Provider `{p.name}` does not support stateful conversations."

        from ..providers import OpenAICompatProvider
        client = OpenAICompatProvider(name=p.name, base_url=p.base_url, api_key=p.resolve_token())
        model = model or p.default_model_name()

        messages = []
        if system_prompt and not response_id:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        resp = client.chat(
            model=model,
            messages=messages,
            store_messages=True,
            previous_response_id=response_id,
        )
        content = resp["choices"][0]["message"]["content"]
        rid = resp.get("id", "")
        return f"{content}\n\n**Response ID:** `{rid}`"

    @mcp.tool(annotations={"readOnlyHint": True})
    async def list_chat_sessions():
        """List all saved chat sessions for the active provider."""
        import json
        from pathlib import Path
        p = get_active_provider()
        Path("chats").mkdir(exist_ok=True)
        sessions = sorted(Path("chats").glob(f"{p.name}_*.json"))
        if not sessions:
            return "No chat sessions found."
        result = ["**Chat Sessions:**\n"]
        for s in sessions:
            history = json.loads(s.read_text(encoding="utf-8"))
            turns = len(history) // 2
            last = history[-1]["time"] if history else "empty"
            result.append(f"- `{s.stem}` — {turns} turn(s), last: {last}")
        return "\n".join(result)

    @mcp.tool(annotations={"readOnlyHint": True})
    async def get_chat_history(session: str = "default"):
        """Get full message history for a session."""
        p = get_active_provider()
        history = load_history(p.name, session)
        if not history:
            return f"No history found for session `{session}`."
        result = [f"**Chat History: `{session}`**\n"]
        for message in history:
            role = message["role"].capitalize()
            time = message.get("time", "")
            result.append(f"**[{time}] {role}:** {message['content']}\n")
        return "\n".join(result)

    @mcp.tool()
    async def clear_chat_history(session: str = "default"):
        """Delete the history file for a session."""
        from pathlib import Path
        p = get_active_provider()
        path = Path("chats") / f"{p.name}_{session}.json"
        if not path.exists():
            return f"No session `{session}` found."
        path.unlink()
        return f"Cleared history for session `{session}`."
