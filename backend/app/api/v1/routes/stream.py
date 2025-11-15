# backend/app/api/v1/routes/stream.py
import uuid
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.services.bus import bus

router = APIRouter(prefix="/v1/stream", tags=["stream"])

def _client_id() -> str:
    return f"cli_{uuid.uuid4().hex}"

@router.get("")  # final URL: /v1/stream
async def sse_stream(request: Request):
    """
    Server-Sent Events endpoint.
    - Content-Type: text/event-stream
    - Auto heartbeats
    - Client auto-reconnect friendly
    """
    client_id = _client_id()
    gen = bus.sse_stream(client_id, heartbeat_seconds=settings.SSE_HEARTBEAT_SECONDS)

    async def event_generator():
        try:
            async for chunk in gen:
                if await request.is_disconnected():
                    break
                yield chunk
        finally:
            # sse_stream() handles unsubscribe in its own finally
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
