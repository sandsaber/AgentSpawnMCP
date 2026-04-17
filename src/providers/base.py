from abc import ABC, abstractmethod
from typing import Any, Optional
import httpx


class BaseProvider(ABC):
    name: str
    base_url: str
    api_key: str

    @abstractmethod
    def chat(self, model: str, messages: list[dict], **kwargs) -> httpx.Response:
        """Send a chat completion request."""
        ...

    @abstractmethod
    def list_models(self) -> httpx.Response:
        """List available models."""
        ...

    @abstractmethod
    def generate_image(self, model: str, prompt: str, **kwargs) -> httpx.Response:
        """Generate an image."""
        ...

    @abstractmethod
    def upload_file(self, file_path: str) -> httpx.Response:
        """Upload a file."""
        ...

    @abstractmethod
    def list_files(self, **kwargs) -> httpx.Response:
        """List uploaded files."""
        ...

    @abstractmethod
    def get_file_content(self, file_id: str, **kwargs) -> httpx.Response:
        """Get file content."""
        ...

    @abstractmethod
    def delete_file(self, file_id: str) -> httpx.Response:
        """Delete a file."""
        ...

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = kwargs.pop("headers", {})
        headers.setdefault("Authorization", f"Bearer {self.api_key}")
        headers.setdefault("Content-Type", "application/json")

        with httpx.Client(timeout=120.0) as client:
            response = client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response
