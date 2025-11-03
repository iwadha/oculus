import asyncio
import json
import time
from typing import AsyncIterator, Dict, Optional

class EventBus:
    """
    A simple in-memory pub/sub bus using an asyncio.Queue per subscriber.
    Not for production fanout scale, but perfect for Module 2.1.
    """
    def __init__(self, buffer_limit: int = 1000):
        self._subscribers = {}  # subscriber_id -> Queue
        self._buffer_limit = buffer_limit
        self._lock = asyncio.Lock()

    async def subscribe(self, subscriber_id: str) -> asyncio.Queue:
        async with self._lock:
            q = asyncio.Queue(maxsize=self._buffer_limit)
            self._subscribers[subscriber_id] = q
            return q

    async def unsubscribe(self, subscriber_id: str):
        async with self._lock:
            self._subscribers.pop(subscriber_id, None)

    async def publish(self, payload: Dict):
        """Publish a dict; we JSON-encode at the edges."""
        msg = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        # Best-effort broadcast; drop-old if queue full
        for q in list(self._subscribers.values()):
            if q.full():
                # remove one oldest by getting without waiting
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            await q.put(msg)

    async def sse_stream(self, subscriber_id: str, heartbeat_seconds: int) -> AsyncIterator[str]:
        """
        Async generator that yields Server-Sent Events lines.
        Sends 'event: ping' heartbeat to keep connections alive.
        """
        queue = await self.subscribe(subscriber_id)
        last_ping = time.monotonic()

        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    pass

                now = time.monotonic()
                if now - last_ping >= heartbeat_seconds:
                    # Heartbeat (clients should ignore)
                    yield f"event: ping\ndata: {{\"ts\": {int(now)}}}\n\n"
                    last_ping = now
        finally:
            await self.unsubscribe(subscriber_id)

# Singleton bus for the app
bus = EventBus()
