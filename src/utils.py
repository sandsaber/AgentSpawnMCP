import json
from pathlib import Path
from datetime import datetime


def load_history(provider: str, session: str) -> list:
    path = Path("chats") / f"{provider}_{session}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_history(provider: str, session: str, history: list) -> None:
    Path("chats").mkdir(exist_ok=True)
    (Path("chats") / f"{provider}_{session}.json").write_text(
        json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def encode_image_to_base64(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    with open(image_path, "rb") as f:
        return __import__("base64").b64encode(f.read()).decode("utf-8")


def encode_video_to_base64(video_path: str) -> str:
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    with open(video_path, "rb") as f:
        return __import__("base64").b64encode(f.read()).decode("utf-8")


def format_response(*parts: str) -> str:
    return "\n".join(p for p in parts if p)


def parse_iso_date(value: str | None, fmt: str = "%d-%m-%Y") -> str | None:
    if not value:
        return None
    from datetime import datetime
    return datetime.strptime(value, fmt).isoformat()
