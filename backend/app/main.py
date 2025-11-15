# app/main.py
import os
import asyncio
import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from os import getenv

from pathlib import Path
try:
    from dotenv import load_dotenv
    ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"  # repo root/.env
    load_dotenv(dotenv_path=ROOT_ENV, override=False)
except Exception:
    pass


from .core.config import settings

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)  # look for .env in CWD; doesn't overwrite real env
except Exception:
    pass

# Routers (each already declares its own /v1/... prefix)
from .api.v1.routes.stream import router as stream_router
from .api.v1.routes.kpis import router as kpis_router
from .api.v1.routes.compare import router as compare_router
from .api.v1.routes.ladder import router as ladder_router
from .api.v1.routes.scores import router as scores_router
from .api.v1.routes.creator_intel import router as creator_intel_router
from .api.v1.routes.wallet_ops import router as wallet_ops_router
from .api.v1.routes.creators import router as creators_router
from .api.v1.routes.alerts import router as alerts_router
from .api.v1.routes.rules import router as rules_router
from .api.v1.routes.trades import router as trades_router
from .api.v1.routes.pairs import router as pairs_router  # prefix="/v1" inside file
from .api.v1.routes.system import router as system_router
from .api.v1.routes.metrics import router as metrics_router


# Optional stream drivers (mock or DB-backed)
from .services.mock_events import run_mock_event_loop
try:
    from .services.db_stream import run_db_stream
except Exception:
    run_db_stream = None  # type: ignore

app = FastAPI(title="Oculus API", version="0.3")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ALLOW_ORIGINS", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers (no extra prefixes here) ---
app.include_router(stream_router)
app.include_router(kpis_router)
app.include_router(compare_router)
app.include_router(ladder_router)
app.include_router(scores_router)
app.include_router(creator_intel_router)
app.include_router(wallet_ops_router)
app.include_router(creators_router)
app.include_router(alerts_router)
app.include_router(rules_router)
app.include_router(trades_router)
app.include_router(pairs_router)
app.include_router(system_router)
app.include_router(metrics_router)


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "Oculus API",
        "endpoints": [
            "/healthz",
            "/v1/stream",
            "/v1/kpis",
            "/v1/trades",
            "/v1/trades/{id}/compare",
            "/v1/trades/{id}/ladder",
            "/v1/trades/{id}/pair",
            "/v1/pairs/rebuild",
            "/v1/wallets/ops",
            "/v1/alerts",
            "/v1/rules",
            "/v1/creators/catalog",
        ],
    }

@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "env": getattr(settings, "ENV", "dev"),
        "db": bool(getattr(app.state, "db", None)),
    }

# --- Background stream task handles ---
_stop_evt: asyncio.Event | None = None
_task: asyncio.Task | None = None

@app.on_event("startup")
async def on_startup():
    """
    - Initialize asyncpg pool on app.state.db
    - Start either DB-backed stream or mock stream task
    """
    global _stop_evt, _task

    # 1) Create DB pool
    DSN = (
    getattr(settings, "DB_DSN", None)
    or getattr(settings, "DATABASE_URL", None)
    or getattr(settings, "SUPABASE_DB_URL", None)
    or getenv("DB_DSN")                 # explicit override
    or getenv("DATABASE_URL")           # common
    or getenv("SUPABASE_DB_URL")        # ✅ your .env key
    or getenv("POSTGRES_DSN")
    or getenv("PG_DSN")
    )

    if not DSN:
        raise RuntimeError(
            "No database DSN found. Set one of: DB_DSN (preferred), DATABASE_URL, "
            "POSTGRES_DSN, PG_DSN, or SUPABASE_DB_URL. "
            "Example: postgresql://user:pass@host:5432/dbname"
        )
    
    app.state.db = await asyncpg.create_pool(
    DSN,
    min_size=1,
    max_size=10,
    statement_cache_size=0,  # required when using pgBouncer in transaction/statement mode
)  # type: ignore[attr-defined]

  # type: ignore[attr-defined]
    print("[STARTUP] Postgres pool ready")

    # 2) Start stream task
    _stop_evt = asyncio.Event()
    loop = asyncio.get_event_loop()
    if getattr(settings, "STREAM_SOURCE", "mock") == "db":
        if run_db_stream is None:
            raise RuntimeError("DB stream selected but Supabase client is unavailable. `pip install supabase`")
        _task = loop.create_task(run_db_stream(_stop_evt))
        print("[STARTUP] DB stream started")
    else:
        _task = loop.create_task(run_mock_event_loop(hz=1.0, stop_event=_stop_evt))
        print("[STARTUP] Mock stream started")

@app.on_event("shutdown")
async def on_shutdown():
    """
    - Stop stream task
    - Close asyncpg pool
    """
    global _stop_evt, _task

    # Stop background task
    if _stop_evt is not None:
        _stop_evt.set()
    if _task is not None:
        try:
            await asyncio.wait_for(_task, timeout=3.0)
        except Exception:
            _task.cancel()

    # Close DB
    pool = getattr(app.state, "db", None)  # type: ignore[attr-defined]
    if pool is not None:
        try:
            await asyncio.wait_for(pool.close(), timeout=5.0)
            print("[SHUTDOWN] Postgres pool closed")
        except asyncio.TimeoutError:
            print("[SHUTDOWN] Pool close timed out; forcing terminate")
            await pool.terminate()
        except Exception:
            pass
