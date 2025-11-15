# backend/app/api/v1/routes/creator_intel.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from supabase import create_client
from app.core.config import settings
from app.services.creator_intel import recompute_creator

# Align with the rest of the API and avoid double segments
router = APIRouter(prefix="/v1/creators", tags=["creator_intel"])

# --- Lazy Supabase client setup ---
def _sb():
    """
    Lazily create a Supabase client using settings.
    Avoids failing at import time when env is not loaded yet.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_ANON_KEY
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL / SUPABASE_ANON_KEY in environment.")
    return create_client(url, key)

_sb_cached_client = None

def sb() -> any:
    """Return a cached Supabase client, creating it if needed."""
    global _sb_cached_client
    if _sb_cached_client is None:
        _sb_cached_client = _sb()
    return _sb_cached_client


# --- API Routes ---

@router.get("/{pubkey}/intel")
def get_creator_intel(pubkey: str):  # ✅ Fix 1: use str, not string
    res = (
        sb()
        .table("creators")
        .select("*")
        .eq("source_wallet_pubkey", pubkey)
        .single()
        .execute()
        .data
    )
    if not res:
        raise HTTPException(status_code=404, detail="Creator not found")

    return {
        "creator": pubkey,
        "trend": res.get("trend"),
        "risk_score": res.get("risk_score"),
        "copyability": res.get("copyability"),
        "badges": res.get("badges") or [],
        "signal_confidence": res.get("signal_confidence"),
        "metrics": res.get("intel_metrics") or {},
        "updated_at": res.get("intel_updated_at"),
    }


@router.post("/{pubkey}/intel/recompute")
def api_recompute_creator(pubkey: str):
    # NOTE: If this writes through Supabase, it likely needs the service-role key.
    return recompute_creator(pubkey)


@router.get("/leaderboard")
def creator_leaderboard(
    sort: str = Query("risk_score"),
    limit: int = Query(100, ge=1, le=500),
):
    data = (
        sb()
        .table("creators")
        .select(
            "source_wallet_pubkey,label,risk_score,trend,copyability,badges,signal_confidence"
        )
        .order(sort, desc=False)
        .limit(limit)
        .execute()
        .data
        or []
    )
    return {"items": data}


@router.get("/{pubkey}/badges")
def creator_badges(pubkey: str):
    hist = (
        sb()
        .table("creator_badges_history")
        .select("*")
        .eq("creator_pubkey", pubkey)
        .order("awarded_at", desc=True)
        .limit(200)
        .execute()
        .data
        or []
    )
    return {"creator": pubkey, "history": hist}


@router.get("/{pubkey}/timeline")
def creator_intel_timeline(pubkey: str, days: int = Query(30, ge=1, le=365)):
    from datetime import date, timedelta

    since = (date.today() - timedelta(days=days)).isoformat()
    rows = (
        sb()
        .table("creator_intel_daily")
        .select("*")
        .eq("creator_pubkey", pubkey)
        .gte("day", since)
        .order("day", desc=False)
        .execute()
        .data
        or []
    )
    return {"creator": pubkey, "daily": rows}
