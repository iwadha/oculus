# backend/app/api/v1/routes/alerts.py
import os
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from asyncpg import Pool, Record

from ..deps import get_db

# Router now has a proper prefix so main.py can include it without adding one.
router = APIRouter(prefix="/v1/alerts", tags=["alerts"])

# Simple service-role guard via header (keep creds only in backend calls)
SERVICE_ROLE_SECRET = os.getenv("SERVICE_ROLE_SECRET", "")

def require_service_role(x_service_key: Optional[str] = Header(default=None)):
    if not SERVICE_ROLE_SECRET:
        # If you haven't set it, allow local dev by default (or raise)
        return True
    if not x_service_key or x_service_key != SERVICE_ROLE_SECRET:
        raise HTTPException(status_code=403, detail="service_role required")
    return True

def rec_to_dict(r: Record) -> Dict[str, Any]:
    return dict(r) if r else {}

@router.get("")
async def list_alerts(
    db: Pool = Depends(get_db),
    # make resolved optional so "all" can be fetched when omitted
    resolved: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=300),
    severity: Optional[str] = Query(None, pattern="^(INFO|WARN|CRITICAL)$"),
    wallet_id: Optional[str] = Query(None),
    creator_pubkey: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """
    Returns a paginated list of alerts:
      { items: [...], page, page_size, total }
    """
    offset = (page - 1) * page_size

    where: List[str] = []
    args: List[Any] = []
    argn = 1

    if resolved is not None:
        where.append(f"resolved = ${argn}")
        args.append(resolved); argn += 1

    if severity:
        where.append(f"severity = ${argn}")
        args.append(severity); argn += 1

    if wallet_id:
        where.append(f"wallet_id = ${argn}::uuid")
        args.append(wallet_id); argn += 1

    if creator_pubkey:
        where.append(f"creator_pubkey = ${argn}")
        args.append(creator_pubkey); argn += 1

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    # We can parameterize LIMIT/OFFSET with asyncpg too
    lim_idx = argn
    off_idx = argn + 1

    async with db.acquire() as conn:
        # total count for pagination
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM public.alerts{where_sql}",
            *args
        )

        rows = await conn.fetch(
            f"""
            SELECT id, wallet_id, creator_pubkey, category, severity, reason,
                   resolution_action, resolved, resolved_at, rule_id, rule_version,
                   eval_snapshot, created_at
            FROM public.alerts
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ${lim_idx} OFFSET ${off_idx}
            """,
            *args, page_size, offset
        )

    return {
        "items": [rec_to_dict(r) for r in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    }

@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    db: Pool = Depends(get_db),
    _svc = Depends(require_service_role),
):
    sql = """
      UPDATE public.alerts
      SET resolved = true,
          resolved_at = now()
      WHERE id = $1::uuid
      RETURNING id
    """
    async with db.acquire() as conn:
        row = await conn.fetchrow(sql, alert_id)
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"ok": True, "id": row["id"]}
