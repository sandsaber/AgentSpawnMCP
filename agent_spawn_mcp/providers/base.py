from abc import ABC, abstractmethod


class BaseProvider(ABC):
    name: str
    base_url: str
    api_key: str

    @abstractmethod
    def chat(self, model: str, messages: list[dict], **kwargs) -> dict:
        """Send a chat completion request and return the parsed JSON body."""
        ...

    @abstractmethod
    def list_models(self) -> dict:
        """List available models."""
        ...

    @abstractmethod
    def generate_image(self, model: str, prompt: str, **kwargs) -> dict:
        """Generate an image."""
        ...

    @abstractmethod
    def upload_file(self, file_path: str) -> dict:
        """Upload a file."""
        ...

    @abstractmethod
    def list_files(self, **kwargs) -> dict:
        """List uploaded files."""
        ...

    @abstractmethod
    def get_file_content(self, file_id: str, **kwargs) -> bytes:
        """Get raw file content bytes."""
        ...

    @abstractmethod
    def delete_file(self, file_id: str) -> dict:
        """Delete a file."""
        ...
