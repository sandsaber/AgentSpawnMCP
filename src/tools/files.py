from mcp.server.fastmcp import FastMCP
from ..config import get_active_provider


def register_file_tools(mcp: FastMCP) -> None:
    from ..providers import OpenAICompatProvider
    from ..utils import load_history, save_history

    def _client():
        p = get_active_provider()
        if not p.capabilities.files:
            raise ValueError(f"Provider `{p.name}` does not support file operations.")
        return OpenAICompatProvider(name=p.name, base_url=p.base_url, api_key=p.resolve_token())

    @mcp.tool()
    async def upload_file(file_path: str):
        """Upload a file to the provider's file storage."""
        client = _client()
        resp = client.upload_file(file_path)
        data = resp
        return (
            f"**File uploaded successfully**\n"
            f"- **File ID:** `{data.get('id', '')}`\n"
            f"- **Filename:** {data.get('filename', file_path)}\n"
            f"- **Size:** {data.get('size', 0)} bytes"
        )

    @mcp.tool(annotations={"readOnlyHint": True})
    async def list_files(
        limit: int = 100,
        order: str = "desc",
        sort_by: str = "created_at",
    ):
        """List uploaded files with sorting."""
        client = _client()
        resp = client.list_files(limit=limit, order=order, sort_by=sort_by)
        files = resp.get("data", [])
        if not files:
            return "No files found."
        result = ["**Files:**\n"]
        for f in files:
            result.append(
                f"- `{f.get('id', '')}` — {f.get('filename', '?')} ({f.get('size', 0)} bytes)"
            )
        return "\n".join(result)

    @mcp.tool(annotations={"readOnlyHint": True})
    async def get_file_content(file_id: str = "", max_bytes: int = 500_000):
        """Download and return file content by ID. Truncates large files."""
        client = _client()
        content = client.get_file_content(file_id, max_bytes=max_bytes)
        text = content.decode("utf-8", errors="replace")
        truncated = len(content) >= max_bytes
        note = f"\n\n*[Truncated: showing {len(content):,} bytes]*" if truncated else ""
        return text + note

    @mcp.tool()
    async def delete_file(file_id: str = ""):
        """Delete a file by ID."""
        client = _client()
        resp = client.delete_file(file_id)
        return f"Deleted file `{resp.get('id', file_id)}`"

    @mcp.tool()
    async def chat_with_files(
        prompt: str,
        file_ids: list[str],
        model: str | None = None,
        session: str | None = None,
        system_prompt: str | None = None,
    ):
        """Chat with uploaded documents using file attachments."""
        p = get_active_provider()
        if not p.capabilities.files:
            return f"Provider `{p.name}` does not support file operations."

        client = OpenAICompatProvider(name=p.name, base_url=p.base_url, api_key=p.resolve_token())
        model = model or p.default_model_name()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if session:
            history = load_history(p.name, session)
            messages.extend(history)

        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
            + [{"type": "file", "file": {"file_id": fid}} for fid in file_ids],
        })

        resp = client.chat(model=model, messages=messages)
        result = resp["choices"][0]["message"]["content"]

        if session:
            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": result})
            save_history(p.name, session, history)

        return result
