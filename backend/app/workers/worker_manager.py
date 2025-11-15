# backend/app/workers/worker_manager.py
import os
import sys
import argparse
import asyncio
import logging
from typing import Optional
from pathlib import Path

# ---- Robust dotenv loading: backend/.env, backend/.ENV, repo/.env, repo/.ENV ----
def _load_env_files():
    try:
        from dotenv import load_dotenv
    except Exception:
        return  # dotenv not installed; skip (we'll rely on real env)
    here = Path(__file__).resolve()
    backend_dir = here.parents[2]      # .../backend
    repo_root   = backend_dir.parent   # repo root
    for p in [
        backend_dir / ".env",
        backend_dir / ".ENV",
        repo_root / ".env",
        repo_root / ".ENV",
    ]:
        if p.exists():
            load_dotenv(p, override=False)

_load_env_files()

import asyncpg
from asyncpg import Pool
from app.core.config import settings

from .normalizer_copy import NormalizerCopy
from .normalizer_creator import NormalizerCreator
from .pairing_worker import PairingWorker
from .ladder_worker import LadderWorker
from .scoring_worker import ScoringWorker
from .creator_intel_worker import CreatorIntelWorker
from .alerts_worker import AlertsWorker

log = logging.getLogger("worker_manager")
logging.basicConfig(
    level=os.getenv("WORKER_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

def _flag(name: str, default: bool) -> bool:
    return bool(getattr(settings, name, default))

FEATURE_WORKER_PAIRING = _flag("FEATURE_WORKER_PAIRING", True)
FEATURE_WORKER_LADDER  = _flag("FEATURE_WORKER_LADDER",  True)
FEATURE_WORKER_SCORING = _flag("FEATURE_WORKER_SCORING", True)
FEATURE_WORKER_NORMALIZER_COPY    = _flag("FEATURE_WORKER_NORMALIZER_COPY", True)
FEATURE_WORKER_NORMALIZER_CREATOR = _flag("FEATURE_WORKER_NORMALIZER_CREATOR", True)
FEATURE_WORKER_CREATOR_INTEL      = _flag("FEATURE_WORKER_CREATOR_INTEL", True)
FEATURE_WORKER_ALERTS             = _flag("FEATURE_WORKER_ALERTS", True)

DEFAULT_INTERVAL_SEC = float(getattr(settings, "WORKER_LOOP_INTERVAL_SEC", 2.0))

def _resolve_dsn() -> Optional[str]:
    # Preferred → fallbacks → settings
    dsn = (
        os.getenv("SUPABASE_DB_URL")
        or os.getenv("DB_DSN")
        or os.getenv("DATABASE_URL")
        or getattr(settings, "SUPABASE_DB_URL", None)
        or getattr(settings, "DATABASE_URL", None)
    )
    if dsn:
        src = ("SUPABASE_DB_URL" if os.getenv("SUPABASE_DB_URL") else
               "DB_DSN" if os.getenv("DB_DSN") else
               "DATABASE_URL" if os.getenv("DATABASE_URL") else
               "settings")
        log.info("Worker DSN resolved via %s.", src)
    return dsn

async def run(
    db: Optional[Pool] = None, *,
    interval_sec: float = DEFAULT_INTERVAL_SEC,
    once: bool = False
) -> None:
    created_pool_here = False

    if db is None:
        # Prefer SUPABASE_DB_URL, then DB_DSN, then DATABASE_URL
        dsn = (
            os.getenv("SUPABASE_DB_URL")
            or os.getenv("DB_DSN")
            or getattr(settings, "DATABASE_URL", None)
        )
        if not dsn:
            raise RuntimeError("No SUPABASE_DB_URL / DB_DSN / DATABASE_URL provided for workers.")

        # ⬇️ IMPORTANT: disable statement cache to avoid DuplicatePreparedStatementError
        db = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=5,
            statement_cache_size=0,          # <— key line
        )
        created_pool_here = True
        log.info("Worker manager connected to database (pool created).")

    workers = []
    if FEATURE_WORKER_NORMALIZER_COPY:    workers.append(NormalizerCopy(db))
    if FEATURE_WORKER_NORMALIZER_CREATOR: workers.append(NormalizerCreator(db))
    if FEATURE_WORKER_PAIRING:            workers.append(PairingWorker(db))
    if FEATURE_WORKER_LADDER:             workers.append(LadderWorker(db))
    if FEATURE_WORKER_SCORING:            workers.append(ScoringWorker(db))
    if FEATURE_WORKER_CREATOR_INTEL:      workers.append(CreatorIntelWorker(db))
    if FEATURE_WORKER_ALERTS:             workers.append(AlertsWorker(db))

    names = ", ".join([w.__class__.__name__ for w in workers]) or "<none>"
    log.info("Worker manager started (interval=%.2fs, once=%s). Enabled workers: %s",
             interval_sec, once, names)

    try:
        while True:
            for w in workers:
                try:
                    await w.run_once()
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    log.warning("Worker %s raised: %r", w.__class__.__name__, e)
            if once:
                break
            await asyncio.sleep(interval_sec)
    finally:
        if created_pool_here and db is not None:
            await db.close()
            log.info("Worker manager pool closed.")

def _parse_args(argv=None):
    p = argparse.ArgumentParser(description="Oculus Worker Manager")
    p.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_SEC, help="Loop interval seconds (default: %(default)s)")
    p.add_argument("--once", action="store_true", help="Run a single pass and exit")
    return p.parse_args(argv)

if __name__ == "__main__":
    args = _parse_args(sys.argv[1:])
    try:
        asyncio.run(run(None, interval_sec=args.interval, once=args.once))
    except KeyboardInterrupt:
        pass
