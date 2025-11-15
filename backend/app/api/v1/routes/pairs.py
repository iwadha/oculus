# app/api/v1/routes/pairs.py
from fastapi import APIRouter, Query
from typing import Optional

from app.core.config import settings
from app.services.pairing_service import force_pair, rebuild_pairs

# ✅ Router handles the version segment
router = APIRouter(prefix="/v1", tags=["pairs"])

@router.post("/trades/{trade_id}/pair")
def pair_trade(trade_id: int):
    if not settings.FEATURE_MODULE3:
        return {"ok": False, "error": "Module 3 disabled"}
    res = force_pair(trade_id)
    return {"ok": True, **res}

@router.post("/pairs/rebuild")
def rebuild(
    limit: int = Query(200, ge=1, le=5000),
    since: Optional[str] = Query(None, description="ISO timestamp lower bound"),
    until: Optional[str] = Query(None, description="ISO timestamp upper bound"),
):
    if not settings.FEATURE_MODULE3:
        return {"ok": False, "error": "Module 3 disabled"}
    res = rebuild_pairs(limit, since, until)
    return {"ok": True, **res}
