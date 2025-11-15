# backend/app/api/v1/routes/rules.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from asyncpg import Pool, Record
from ..deps import get_db

router = APIRouter(prefix="/v1/rules", tags=["rules"])

def rec_to_dict(r: Record) -> dict:
    return dict(r) if r else {}

@router.get("")
async def list_rules(
    db: Pool = Depends(get_db),
    enabled: Optional[bool] = True,
) -> List[dict]:
    sql = "select * from public.rules"
    args = []
    if enabled is not None:
        sql += " where enabled = $1"
        args.append(enabled)
    async with db.acquire() as conn:
        rows = await conn.fetch(sql, *args)
    return [rec_to_dict(r) for r in rows]

@router.get("/{rule_id}")
async def get_rule(
    rule_id: str,
    db: Pool = Depends(get_db),
) -> dict:
    sql = "select * from public.rules where id = $1::uuid"
    async with db.acquire() as conn:
        row = await conn.fetchrow(sql, rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rec_to_dict(row)
