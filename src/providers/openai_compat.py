import os
import json
import base64
from pathlib import Path
from typing import Any, Optional
import httpx
from .base import BaseProvider


class OpenAICompatProvider(BaseProvider):
    """OpenAI-compatible HTTP provider using chat completions API."""

    def __init__(self, name: str, base_url: str, api_key: str, default_model: str = "", api_type: str = "openai"):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.default_model = default_model
        self.api_type = api_type

    def _headers(self) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.api_type == "anthropic":
            headers["anthropic-version"] = "2023-06-01"
        return headers

    def _post(self, path: str, data: dict) -> httpx.Response:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, json=data, headers=self._headers())
            resp.raise_for_status()
            return resp

    def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        with httpx.Client(timeout=120.0) as client:
            resp = client.get(url, params=params, headers=self._headers())
            resp.raise_for_status()
            return resp

    def _delete(self, path: str) -> httpx.Response:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        with httpx.Client(timeout=120.0) as client:
            resp = client.delete(url, headers=self._headers())
            resp.raise_for_status()
            return resp

    def chat(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
        include: list[str] | None = None,
        max_turns: int | None = None,
        store_messages: bool = False,
        previous_response_id: str | None = None,
        stream: bool = False,
        max_tokens: int = 4096,
        **kwargs,
    ) -> dict:
        if self.api_type == "anthropic":
            return self._anthropic_chat(model, messages, max_tokens, **kwargs)
        return self._openai_chat(model, messages, tools, tool_choice, stream, store_messages, previous_response_id, max_turns, include, **kwargs)

    def _openai_chat(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
        stream: bool = False,
        store_messages: bool = False,
        previous_response_id: str | None = None,
        max_turns: int | None = None,
        include: list[str] | None = None,
        **kwargs,
    ) -> dict:
        data: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if store_messages:
            data["store_messages"] = True
        if previous_response_id:
            data["previous_response_id"] = previous_response_id
        if tools:
            data["tools"] = tools
        if tool_choice:
            data["tool_choice"] = tool_choice
        if include:
            data["include"] = include
        if max_turns:
            data["max_turns"] = max_turns
        data.update({k: v for k, v in kwargs.items() if v is not None})

        resp = self._post("v1/chat/completions", data)
        return resp.json()

    def _anthropic_chat(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int = 4096,
        system_prompt: str | None = None,
        temperature: float | None = None,
        **kwargs,
    ) -> dict:
        anthropic_messages = []
        system = system_prompt or ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            if role == "system":
                system = content[0]["text"] if content else ""
            else:
                anthropic_messages.append({"role": role, "content": content})

        data: dict[str, Any] = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
        }
        if system:
            data["system"] = system
        if temperature is not None:
            data["temperature"] = temperature
        data.update({k: v for k, v in kwargs.items() if v is not None})

        if "/v1" in self.base_url or "/anthropic" in self.base_url:
            resp = self._post("messages", data)
        else:
            resp = self._post("v1/messages", data)
        result = resp.json()

        content = result.get("content", [])
        text = ""
        for block in content:
            if block.get("type") == "text":
                text += block.get("text", "")

        return {
            "choices": [{"message": {"role": "assistant", "content": text}}],
            "model": result.get("model", model),
            "usage": {
                "prompt_tokens": result.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": result.get("usage", {}).get("output_tokens", 0),
            },
        }

    def list_models(self) -> dict:
        resp = self._get("v1/models")
        return resp.json()

    def generate_image(
        self,
        model: str,
        prompt: str,
        image_path: str | None = None,
        image_url: str | None = None,
        n: int = 1,
        aspect_ratio: str | None = None,
        **kwargs,
    ) -> dict:
        data: dict[str, Any] = {"model": model, "prompt": prompt, "n": n}
        if image_path:
            ext = Path(image_path).suffix.lower().replace(".", "")
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            data["image_url"] = f"data:image/{ext};base64,{b64}"
        elif image_url:
            data["image_url"] = image_url
        if aspect_ratio:
            data["aspect_ratio"] = aspect_ratio
        data.update({k: v for k, v in kwargs.items() if v is not None})

        resp = self._post("v1/images/generations", data)
        return resp.json()

    def upload_file(self, file_path: str) -> dict:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with httpx.Client(timeout=120.0) as client:
            with file_path.open("rb") as f:
                files = {"file": (file_path.name, f)}
                data = {}
                resp = client.post(
                    f"{self.base_url.rstrip('/')}/v1/files",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
            resp.raise_for_status()
            return resp.json()

    def list_files(self, limit: int = 100, order: str = "desc", sort_by: str = "created_at") -> dict:
        resp = self._get("v1/files", {"limit": limit, "order": order, "sort_by": sort_by})
        return resp.json()

    def get_file_content(self, file_id: str, max_bytes: int = 500_000) -> bytes:
        url = f"{self.base_url.rstrip('/')}/v1/files/{file_id}/content"
        with httpx.Client(timeout=120.0) as client:
            resp = client.get(url, headers=self._headers())
            resp.raise_for_status()
            content = resp.content
            if len(content) > max_bytes:
                content = content[:max_bytes]
            return content

    def delete_file(self, file_id: str) -> dict:
        resp = self._delete(f"v1/files/{file_id}")
        return resp.json()

    def chat_with_files(self, model: str, messages: list[dict], file_ids: list[str], **kwargs) -> dict:
        """Chat using assistant file attachments."""
        file_msgs = [{"type": "file", "file": {"file_id": fid}} for fid in file_ids]
        enriched_messages = []
        for msg in messages:
            if msg.get("role") == "user" and not any(
                item.get("type") == "file" for item in (msg.get("content") if isinstance(msg.get("content"), list) else [])
            ):
                enriched = msg.copy()
                if isinstance(enriched.get("content"), str):
                    enriched["content"] = [{"type": "text", "text": enriched["content"]}] + file_msgs
                else:
                    enriched["content"] = file_msgs
                enriched_messages.append(enriched)
            else:
                enriched_messages.append(msg)

        return self.chat(model=model, messages=enriched_messages, **kwargs)
