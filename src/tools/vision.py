from mcp.server.fastmcp import FastMCP
from ..config import get_active_provider


def register_vision_tools(mcp: FastMCP) -> None:
    from ..utils import load_history, save_history, encode_image_to_base64

    @mcp.tool()
    async def chat_with_vision(
        prompt: str,
        model: str | None = None,
        session: str | None = None,
        image_paths: list[str] | None = None,
        image_urls: list[str] | None = None,
        detail: str = "auto",
    ):
        """
        Analyze images with text. Local images are base64-encoded.
        Supported formats: jpg, jpeg, png.
        Provider must support vision capability.
        """
        p = get_active_provider()
        if not p.capabilities.vision:
            raise ValueError(f"Provider `{p.name}` does not support vision.")

        from ..providers import OpenAICompatProvider
        client = OpenAICompatProvider(name=p.name, base_url=p.base_url, api_key=p.resolve_token())
        model = model or p.default_model_name()

        history = load_history(p.name, session) if session else []

        content = []
        if image_paths:
            for path in image_paths:
                ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
                if ext not in ("jpg", "jpeg", "png"):
                    raise ValueError(f"Unsupported image type: {ext}")
                b64 = encode_image_to_base64(path)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/{ext};base64,{b64}", "detail": detail},
                })
        if image_urls:
            for url in image_urls:
                content.append({"type": "image_url", "image_url": {"url": url, "detail": detail}})
        content.append({"type": "text", "text": prompt})

        messages = list(history)
        messages.append({"role": "user", "content": content})

        resp = client.chat(model=model, messages=messages)
        result = resp["choices"][0]["message"]["content"]

        if session:
            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": result})
            save_history(p.name, session, history)

        return result

    @mcp.tool()
    async def generate_image(
        prompt: str,
        model: str | None = None,
        image_path: str | None = None,
        image_url: str | None = None,
        n: int = 1,
        aspect_ratio: str | None = None,
    ):
        """Generate an image from text (optionally edit an existing one)."""
        p = get_active_provider()
        from ..providers import OpenAICompatProvider
        client = OpenAICompatProvider(name=p.name, base_url=p.base_url, api_key=p.resolve_token())
        model = model or next((m.name for m in p.models if m.type == "image_gen"), "gpt-image-1")

        resp = client.generate_image(
            model=model,
            prompt=prompt,
            image_path=image_path,
            image_url=image_url,
            n=n,
            aspect_ratio=aspect_ratio,
        )

        images = resp.get("data", [])
        result = ["## Generated Image(s)"]
        for i, img in enumerate(images, 1):
            result.append(f"\n**Image {i}:** {img.get('url', img.get('b64_json', '(no url)'))}")
        return "\n".join(result)
