# app/services/pairing_store.py
from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime
from ..core.config import settings
from ..db.sql import (
    fetch_copy_trade,
    fetch_source_trade,
    nearest_source_for_copy,
    upsert_trade_pair,
)

def _ms_delta(copy_ts: Optional[str], source_ts: Optional[str]) -> Optional[int]:
    if not copy_ts or not source_ts:
        return None
    try:
        c = datetime.fromisoformat(copy_ts.replace("Z", "+00:00"))
        s = datetime.fromisoformat(source_ts.replace("Z", "+00:00"))
        return int((c - s).total_seconds() * 1000)
    except Exception:
        return None

def _slots_delta(copy_slot: Optional[int], source_slot: Optional[int]) -> Optional[int]:
    if copy_slot is None or source_slot is None:
        return None
    try:
        return int(copy_slot - source_slot)
    except Exception:
        return None

def _copy_effective_price(invested_sol: Optional[float], received_qty: Optional[float]) -> Optional[float]:
    try:
        if invested_sol is None or received_qty in (None, 0):
            return None
        return float(invested_sol) / float(received_qty)
    except Exception:
        return None

def _price_drift(copy_price: Optional[float], source_price: Optional[float]) -> Optional[float]:
    if copy_price is None or source_price in (None, 0):
        return None
    try:
        return ((copy_price - source_price) / source_price) * 100.0
    except Exception:
        return None

def _confidence_from_deltas(delta_ms: Optional[int], delta_slots: Optional[int]) -> str:
    # v1 thresholds
    if delta_slots is not None and abs(delta_slots) <= 20:
        return "HIGH"
    if delta_ms is not None and abs(delta_ms) <= 1200:
        return "HIGH"
    if (delta_slots is not None and abs(delta_slots) <= 60) or (delta_ms is not None and abs(delta_ms) <= 5000):
        return "MED"
    return "LOW"

def pair_one(copy_trade_id: int) -> Dict[str, Any]:
    """
    Pair one copy trade to its nearest source and upsert into trade_pairs.
    Returns a small result for logs.
    """
    copy = fetch_copy_trade(copy_trade_id)
    if not copy:
        return {"paired": False, "reason": "COPY_NOT_FOUND", "copy_trade_id": copy_trade_id}

    # Find nearest source (via RPC; if not registered, this returns None)
    win_s = settings.PAIR_WINDOW_MS // 1000
    source_id = nearest_source_for_copy(copy_trade_id, win_s)
    if not source_id:
        # nothing we can do right now
        payload = {
            "copy_trade_id": copy_trade_id,
            # keep token_mint/side on the row so later uniqueness/guards can work
            "token_mint": copy.get("token_mint"),
            "side": (copy.get("side") or "").upper(),
            "paired_at": datetime.utcnow().isoformat() + "Z",
        }
        ok, err = upsert_trade_pair(payload)
        return {"paired": False, "reason": "NO_SOURCE", "error": err, "copy_trade_id": copy_trade_id}

    source = fetch_source_trade(source_id)
    if not source:
        return {"paired": False, "reason": "SOURCE_NOT_FOUND", "copy_trade_id": copy_trade_id, "source_id": source_id}

    # Compute deltas
    delta_ms_event = _ms_delta(copy.get("timestamp"), source.get("event_ts"))
    delta_slots_event = _slots_delta(copy.get("tx_slot"), source.get("event_slot"))

    # Prices
    copy_price = _copy_effective_price(copy.get("invested_sol"), copy.get("received_qty"))
    source_price = source.get("price")
    drift_pct = _price_drift(copy_price, source_price)

    # Confidence (v1)
    conf = _confidence_from_deltas(delta_ms_event, delta_slots_event)

    # Upsert
    payload = {
        "copy_trade_id": copy_trade_id,
        "source_trade_id": source_id,
        "token_mint": copy.get("token_mint"),
        "side": (copy.get("side") or "").upper(),
        "delta_ms_event": delta_ms_event,
        "delta_slots_event": delta_slots_event,
        "price_drift": drift_pct,
        "confidence": conf,
        "paired_at": datetime.utcnow().isoformat() + "Z",
        # keep diagnostics flexible (v2 can add detail)
        "diagnostics": None,
    }
    ok, err = upsert_trade_pair(payload)
    return {
        "paired": bool(ok),
        "copy_trade_id": copy_trade_id,
        "source_id": source_id,
        "error": err,
        "confidence": conf,
        "delta_ms_event": delta_ms_event,
        "delta_slots_event": delta_slots_event,
        "price_drift_pct": drift_pct,
    }

def rebuild(limit: int = 500, since_iso: Optional[str] = None, until_iso: Optional[str] = None) -> Dict[str, Any]:
    """
    Pair recent copy trades in bulk (idempotent upsert).
    """
    from ..db.sql import select_recent_copy_ids
    ids = select_recent_copy_ids(limit=limit, since_iso=since_iso, until_iso=until_iso)
    paired, awaiting, errors = 0, 0, 0
    results = []
    for tid in ids:
        res = pair_one(tid)
        results.append(res)
        if res.get("paired"):
            paired += 1
        elif res.get("reason") in ("NO_SOURCE",):
            awaiting += 1
        if res.get("error"):
            errors += 1
    return {"scanned": len(ids), "paired": paired, "awaiting": awaiting, "errors": errors}
