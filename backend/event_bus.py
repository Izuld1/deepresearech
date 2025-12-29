# event_bus.py
import asyncio
from typing import AsyncGenerator


class EventBus:
    """
    简单的事件总线（基于 asyncio.Queue）
    - 后端各模块：emit()
    - SSE 层：stream()
    """

    def __init__(self):
        self.queue: asyncio.Queue[str] = asyncio.Queue()

    async def emit(self, event: str):
        """
        向事件队列中发送一条已经格式化好的 SSE 文本
        """
        await self.queue.put(event)

    async def stream(self) -> AsyncGenerator[str, None]:
        """
        SSE 消费端：不断从队列中取事件并 yield 给前端
        """
        while True:
            event = await self.queue.get()
            yield event


# 全局单例（当前 demo 阶段足够）
event_bus = EventBus()
