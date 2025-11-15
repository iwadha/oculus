# app/services/db_stream.py
import os
import asyncio
import logging
from typing import Optional, List, Dict, Any

from supabase import create_client, Client
from ..core.config import settings

from .bus import bus
from .kpi_cache import record as record_kpi

# -------- Env & defaults --------
# Use environment variables directly (same pattern as sql.py, ladder.py)
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_ANON_KEY"]


TABLE_COPY = os.getenv("OCULUS_TABLE_TRADES", "oculus_trades_view")
PK_COPY = os.getenv("OCULUS_COPY_PK_COL", "id")

POLL_MS = int(os.getenv("OCULUS_DB_POLL_MS", getattr(settings, "DB_POLL_MS", 500)))
MAX_PER_TICK = int(os.getenv("OCULUS_DB_POLL_MAX_PER_TICK", "250"))

CURSOR_ENABLED = os.getenv("OCULUS_DB_CURSOR_ENABLED", "true").lower() == "true"
CURSOR_TABLE = os.getenv("OCULUS_DB_CURSOR_TABLE", "oculus_cursor")
CURSOR_STORAGE = os.getenv("OCULUS_DB_CURSOR_STORAGE", "supabase")  # supabase | memory
STREAM_KEY = os.getenv("OCULUS_DB_CURSOR_STREAM_KEY", "trades_view")

LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
log = logging.getLogger("db_stream")


def _sb() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL / SUPABASE_*_KEY not set")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


async def _read_cursor_supabase(sb: Client, stream_key: str) -> int:
    try:
        res = sb.table(CURSOR_TABLE).select("last_seen_id").eq("stream_key", stream_key).limit(1).execute()
        rows = res.data or []
        return int(rows[0]["last_seen_id"]) if rows else 0
    except Exception as e:
        log.warning("cursor read failed; defaulting to 0: %r", e)
        return 0


async def _write_cursor_supabase(sb: Client, stream_key: str, new_id: int) -> None:
    try:
        payload = {"stream_key": stream_key, "last_seen_id": int(new_id)}
        # upsert; never move backwards
        sb.table(CURSOR_TABLE).upsert(payload, on_conflict="stream_key").execute()
    except Exception as e:
        log.error("cursor write failed (stream_key=%s new_id=%s): %r", stream_key, new_id, e)


async def _read_cursor(sb: Client) -> int:
    if not CURSOR_ENABLED:
        return 0
    if CURSOR_STORAGE == "supabase":
        return await _read_cursor_supabase(sb, STREAM_KEY)
    # memory fallback (mostly for tests)
    return 0


async def _write_cursor(sb: Client, last_id: int) -> None:
    if not CURSOR_ENABLED:
        return
    if CURSOR_STORAGE == "supabase":
        await _write_cursor_supabase(sb, STREAM_KEY, last_id)


def _coerce_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _map_row(r: Dict[str, Any]) -> Dict[str, Any]:
    # Map DB row → canonical SSE event
    wallet = r.get("wallet_label") or r.get("wallet") or "Unknown"
    action = (r.get("action") or r.get("side") or "BUY")
    action = action.upper() if isinstance(action, str) else "BUY"
    token = r.get("mint") or r.get("token_mint") or "NA"
    ts = r.get("ts_iso") or r.get("ts") or r.get("created_at")

    score = _coerce_int(r.get("execution_score"), 75)
    copy_slot = _coerce_int(r.get("copy_slot") or r.get("slot"), 0)
    source_slot = _coerce_int(r.get("source_slot") or r.get("slot_source"), 0)
    creator = r.get("creator") or "Unknown"

    return {
        "type": "trade",
        "wallet": wallet,
        "action": action,
        "token": token,
        "creator": creator,
        "ts": ts,
        "execution_score": score,
        "source_slot": source_slot,
        "copy_slot": copy_slot,
    }


async def run_db_stream(stop_evt: asyncio.Event) -> None:
    """
    Poll new rows from OCULUS_TABLE_TRADES (view), emit to SSE bus, update KPI cache.
    Adds:
      - Cursor-based replay via Supabase table (oculus_cursor)
      - Burst limiting via OCULUS_DB_POLL_MAX_PER_TICK
    """
    sb = _sb()
    since_id: int = await _read_cursor(sb)  # 0 if disabled / not set
    log.info(
        "db_stream start: table=%s pk=%s poll_ms=%s max_per_tick=%s since_id=%s cursor_enabled=%s",
        TABLE_COPY, PK_COPY, POLL_MS, MAX_PER_TICK, since_id, CURSOR_ENABLED,
    )

    try:
        while not stop_evt.is_set():
            try:
                # ✅ Wrap blocking Supabase .execute() inside a thread
                rows: List[Dict[str, Any]] = await asyncio.to_thread(
                    lambda: (
                        sb.table(TABLE_COPY)
                        .select("*")
                        .gt(PK_COPY, since_id)
                        .order(PK_COPY, desc=False)
                        .limit(MAX_PER_TICK)
                        .execute()
                        .data
                        or []
                    )
                )

                if not rows:
                    log.debug("idle: no new rows > %s; sleep=%sms", since_id, POLL_MS)
                    await asyncio.sleep(POLL_MS / 1000.0)
                    continue

                # Map & emit
                for r in rows:
                    evt = _map_row(r)
                    await bus.publish(evt)
                    record_kpi(evt)

                max_id = _coerce_int(rows[-1].get(PK_COPY), since_id)
                burst_capped = len(rows) == MAX_PER_TICK

                # ✅ Wrap cursor write in to_thread as well
                await asyncio.to_thread(lambda: asyncio.run(_write_cursor(sb, max_id)))
                since_id = max(since_id, max_id)

                log.info(
                    "poll: fetched=%d burst_capped=%s advanced_cursor=%s sleep=%sms",
                    len(rows), burst_capped, since_id, POLL_MS,
                )

            except Exception as e:
                log.exception("[DB_STREAM] tick error: %r", e)

            await asyncio.sleep(POLL_MS / 1000.0)

    finally:
        # Best-effort flush; since_id already held the max we emitted.
        try:
            await _write_cursor(sb, since_id)
            log.info("db_stream stop: cursor flushed since_id=%s", since_id)
        except Exception as e:
            log.warning("cursor flush failed on shutdown: %r", e)
