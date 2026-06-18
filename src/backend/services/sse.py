import json
from typing import Any


def sse_event(event: str, data: Any) -> str:
    """Encode an SSE event with JSON data."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
