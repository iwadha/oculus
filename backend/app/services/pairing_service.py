# app/services/pairing_service.py
import time
from asyncpg import Pool
from typing import Optional, Dict, Any
from ..core.config import settings
from ..db.sql import fetch_compare_row, call_nearest_source
from . import pairing_store  # now implemented

# simple in-memory cache (trade_id -> (ts_ms, payload or awaiting))
_CACHE: Dict[int, Dict[str, Any]] = {}

def _now_ms() -> int:
    return int(time.time() * 1000)

def _fresh(entry_ts: int) -> bool:
    return (_now_ms() - entry_ts) <= settings.COMPARE_CACHE_TTL_MS

def compare_for_trade(copy_trade_id: int) -> Dict[str, Any]:
    cached = _CACHE.get(copy_trade_id)
    if cached and _fresh(cached["ts"]):
        return cached["payload"]

    row = fetch_compare_row(copy_trade_id)
    if not row:
        # Do NOT call DB RPC here. Workers will pair asynchronously.
        payload = {"status": "AWAITING_MATCH", "message": "Awaiting worker pairing…", "confidence": "LOW"}
        CACHE[copy_trade_id] = {"ts": _now_ms(), "payload": payload}
        return payload


    copy_price = row.get("copy_price")
    source_price = row.get("source_price")
    roi_copy = row.get("copy_roi_pct")
    roi_source = None

    price_drift_pct = None
    if source_price and copy_price is not None:
        try:
            price_drift_pct = ((copy_price - source_price) / source_price) * 100.0
        except ZeroDivisionError:
            price_drift_pct = None

    roi_delta_pct = None
    if roi_copy is not None and roi_source is not None:
        roi_delta_pct = (roi_copy - roi_source)

    payload = {
        "pair_id": None,
        "side": row.get("side"),
        "token_mint": row.get("token_mint"),
        "copy": {
            "trade_id": row.get("copy_id"),
            "ts": row.get("copy_ts"),
            "slot": None,  # not exposed in view v1
            "price": copy_price,
            "roi_pct": roi_copy,
            "tip_lamports": row.get("tip_lamports"),
            "cu_used": row.get("cu_used"),
            "cu_price_micro_lamports": row.get("cu_price_micro_lamports"),
            "tx_route": row.get("route"),
        },
        "source": {
            "trade_id": row.get("source_id"),
            "ts": row.get("source_ts"),
            "slot": None,
            "price": source_price,
            "roi_pct": roi_source,
            "tip_lamports": row.get("tip_lamports"),
            "cu_used": row.get("cu_used"),
            "cu_price_micro_lamports": row.get("cu_price_micro_lamports"),
            "tx_route": row.get("route"),
        },
        "deltas": {
            "slots": row.get("delta_slots_event"),
            "ms": row.get("delta_ms_event"),
            "price_drift_pct": price_drift_pct,
            "roi_delta_pct": roi_delta_pct
        },
        "diagnostics": row.get("diagnostics") or {"cause": None, "detail": None},
        "confidence": (row.get("confidence") or "NONE"),
    }
    _CACHE[copy_trade_id] = {"ts": _now_ms(), "payload": payload}
    return payload

def force_pair(copy_trade_id: int) -> Dict[str, Any]:
    """
    Force a pairing attempt (upsert). Clears cache entry for this trade.
    """
    res = pairing_store.pair_one(copy_trade_id)
    _CACHE.pop(copy_trade_id, None)
    return res

def rebuild_pairs(limit: int, since_iso: Optional[str], until_iso: Optional[str]) -> Dict[str, Any]:
    res = pairing_store.rebuild(limit=limit, since_iso=since_iso, until_iso=until_iso)
    _CACHE.clear()
    return res

async def get_pair(db: Pool, copy_trade_id: int) -> Optional[Dict[str, Any]]:
    row = await db.fetchrow("select * from trade_pairs where copy_trade_id = $1", copy_trade_id)
    return dict(row) if row else None

async def enqueue_pairing(db: Pool, copy_trade_id: int) -> None:
    # If you keep a simple jobs table, insert here; otherwise no-op (workers poll unpaired).
    return