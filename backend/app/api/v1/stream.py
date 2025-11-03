import uuid
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from .. import __init__ as _
from ...core.config import settings
from ...services.bus import bus
import asyncio

router = APIRouter(prefix="/v1", tags=["stream"])

def _client_id() -> str:
    return f"cli_{uuid.uuid4().hex}"

@router.get("/stream")
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
        # Stream until client disconnects
        try:
            async for chunk in gen:
                # If client disconnected, break
                if await request.is_disconnected():
                    break
                yield chunk
        finally:
            # sse_stream() handles unsubscribe in its finally
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
