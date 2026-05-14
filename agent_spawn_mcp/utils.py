import base64
import json
from datetime import datetime
from pathlib import Path


def load_history(provider: str, session: str) -> list:
    path = Path("chats") / f"{provider}_{session}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_history(provider: str, session: str, history: list) -> None:
    Path("chats").mkdir(exist_ok=True)
    now = datetime.now().isoformat(timespec="seconds")
    stamped: list = []
    for message in history:
        if isinstance(message, dict) and "time" not in message:
            stamped.append({**message, "time": now})
        else:
            stamped.append(message)
    (Path("chats") / f"{provider}_{session}.json").write_text(
        json.dumps(stamped, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def encode_image_to_base64(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def encode_video_to_base64(video_path: str) -> str:
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    with open(video_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def format_response(*parts: str) -> str:
    return "\n".join(p for p in parts if p)


def parse_iso_date(value: str | None, fmt: str = "%d-%m-%Y") -> str | None:
    if not value:
        return None
    return datetime.strptime(value, fmt).isoformat()
