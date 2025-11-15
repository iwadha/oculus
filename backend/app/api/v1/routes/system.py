"""
System Status Endpoint
----------------------
Reports live health and runtime information for Oculus backend.
"""

import os
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Request
from asyncpg import Pool

from app.core.config import settings

router = APIRouter(prefix="/v1/system", tags=["system"])

# Cache state for recent updates (optional)
_last_updates: Dict[str, str] = {}
_started_at = datetime.utcnow().isoformat() + "Z"


def update_heartbeat(worker_name: str) -> None:
    """Optional: workers can call this to record last activity."""
    _last_updates[worker_name] = datetime.utcnow().isoformat() + "Z"


async def _check_db(request: Request) -> bool:
    """Lightweight DB connectivity check."""
    try:
        db: Pool = request.app.state.db  # type: ignore[attr-defined]
        async with db.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception:
        return False


@router.get("/status")
async def system_status(request: Request) -> Dict[str, Any]:
    """
    Detailed system status:
      - env, version
      - stream source (mock | db)
      - DB connectivity
      - worker feature flags
      - last worker heartbeats (if populated)
    """
    db_ok = await _check_db(request)

    worker_flags = {
        "helius_ingest": os.getenv("ENABLE_HELIUS_INGEST", "false").lower() == "true",
        "token_updater": os.getenv("ENABLE_TOKEN_UPDATER", "false").lower() == "true",
        "scoring_worker": os.getenv("ENABLE_SCORING_WORKER", "false").lower() == "true",
        "alerts_worker": os.getenv("ENABLE_ALERTS_WORKER", "false").lower() == "true",
    }

    return {
        "status": "ok" if db_ok else "degraded",
        "env": getattr(settings, "ENV", "dev"),
        "version": getattr(settings, "APP_VERSION", "0.3"),
        "stream_source": getattr(settings, "STREAM_SOURCE", "mock"),
        "database": "connected" if db_ok else "error",
        "workers": worker_flags,
        "last_updates": _last_updates,
        "started_at": _started_at,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/health")
async def system_health(request: Request) -> Dict[str, Any]:
    """
    Lightweight health check for /v1/system/health.
    Returns a minimal subset of system_status.
    """
    status = await system_status(request)
    return {
        "status": status["status"],
        "database": status["database"],
        "env": status["env"],
        "timestamp": status["timestamp"],
    }
