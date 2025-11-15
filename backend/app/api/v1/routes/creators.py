# app/api/v1/routes/creators.py
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional, List
from asyncpg import Pool

from app.schemas.creators import CatalogResponse, CreatorRow
from app.services.creators_catalog import fetch_catalog
from app.schemas.creator_detail import CreatorProfile, ActivityPage
from app.services.creator_detail import fetch_profile, fetch_activity, fetch_charts
from app.api.v1.deps import get_db  # same pattern as your other routes

router = APIRouter(prefix="/v1/creators", tags=["creators"])

@router.get("/catalog", response_model=CatalogResponse)
async def get_catalog(
    query: Optional[str] = None,
    tier: Optional[str] = None,
    risk_max: Optional[float] = None,
    roi_min: Optional[float] = None,
    active_within: Optional[str] = Query(default="30d"),
    badges: Optional[List[str]] = Query(default=None),
    sort: str = "last_activity",
    order: str = "desc",
    page: int = 1,
    page_size: int = 50,
    pool: Pool = Depends(get_db),
):
    rows, total = await fetch_catalog(
        pool=pool,
        query=query, tier=tier, risk_max=risk_max, roi_min=roi_min,
        active_within=active_within, badges=badges,
        sort=sort, order=order, page=page, page_size=page_size,
    )
    items = [CreatorRow(**dict(r)) for r in rows]
    return CatalogResponse(items=items, page=page, page_size=page_size, total=total)

@router.get("/{creator_id}/profile", response_model=CreatorProfile)
async def creator_profile(creator_id: str, pool: Pool = Depends(get_db)):
    data = await fetch_profile(pool, creator_id)
    if not data:
        raise HTTPException(status_code=404, detail="Creator not found")
    return data

@router.get("/{creator_id}/activity", response_model=ActivityPage)
async def creator_activity(
    creator_id: str,
    since: Optional[str] = None,
    until: Optional[str] = None,
    side: Optional[str] = None,
    min_score: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    pool: Pool = Depends(get_db),
):
    rows, total = await fetch_activity(
        pool, creator_id, since=since, until=until, side=side,
        min_score=min_score, status=status, page=page, page_size=page_size
    )
    return {"page": page, "page_size": page_size, "total_estimate": total, "rows": rows}

@router.get("/{creator_id}/charts")
async def creator_charts(
    creator_id: str,
    window: str = Query("7d", regex="^(7d|30d)$"),
    pool: Pool = Depends(get_db),
):
    return await fetch_charts(pool, creator_id, window)

