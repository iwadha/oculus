# app/main.py (only the CORS + startup bits shown for clarity)
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .api.v1.stream import router as stream_router
from .api.v1.kpis import router as kpis_router

from .services.mock_events import run_mock_event_loop
try:
    from .services.db_stream import run_db_stream
except Exception:
    run_db_stream = None

app = FastAPI(title="Oculus API", version="0.2")

# --- CORS (now driven by typed settings) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream_router)
app.include_router(kpis_router)

@app.get("/")
def root():
    return {"ok": True, "service": "Oculus API", "endpoints": ["/healthz", "/v1/stream", "/v1/kpis"]}

@app.get("/healthz")
def healthz():
    return {"status": "ok", "env": settings.ENV, "import_error": None}

_stop_evt: asyncio.Event | None = None
_task: asyncio.Task | None = None

@app.on_event("startup")
async def on_startup():
    global _stop_evt, _task
    loop = asyncio.get_event_loop()
    _stop_evt = asyncio.Event()

    if settings.is_db_stream:
        if run_db_stream is None:
            raise RuntimeError("DB stream selected but supabase client not available. `pip install supabase`")
        _task = loop.create_task(run_db_stream(_stop_evt))
        print("[STARTUP] DB stream started")
    else:
        _task = loop.create_task(run_mock_event_loop(hz=1.0, stop_event=_stop_evt))
        print("[STARTUP] Mock stream started")

@app.on_event("shutdown")
async def on_shutdown():
    global _stop_evt, _task
    if _stop_evt is not None:
        _stop_evt.set()
    if _task is not None:
        try:
            await asyncio.wait_for(_task, timeout=3.0)
        except Exception:
            _task.cancel()
