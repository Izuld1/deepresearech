# utils.py
import json


def sse_event(event_type: str, payload: dict) -> str:
    """
    将事件格式化为 SSE 标准文本
    """
    data = {
        "type": event_type,
        "payload": payload,
    }
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
