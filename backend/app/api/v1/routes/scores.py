# backend/app/api/v1/routes/scores.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from supabase import create_client
from app.core.config import settings

router = APIRouter(prefix="/v1/scores", tags=["scores"])


def get_sb():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


@router.get("/pairs/{copy_trade_id}")
def get_pair_score(copy_trade_id: int):
    sb = get_sb()
    res = sb.table("trade_pairs").select(
        "copy_trade_id, source_trade_id, execution_score, exec_status, "
        "exec_version, exec_ready_at, exec_latency_ms, exec_subscores, "
        "exec_inputs, exec_missing"
    ).eq("copy_trade_id", copy_trade_id).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="pair not found")
    return res.data[0]


@router.get("/timeseries")
def timeseries():
    sb = get_sb()
    res = sb.table("v_execution_score_timeseries").select("*").order("bucket_minute", ascending=True).execute()
    return res.data or []


@router.get("/leaderboard/creator")
def leaderboard_creator(period: str = Query("7d", pattern="^(1d|7d|30d)$")):
    sb = get_sb()
    col = {"1d": "avg_score_1d", "7d": "avg_score_7d", "30d": "avg_score_30d"}[period]
    res = sb.table("v_execution_score_by_creator").select(
        f"creator_pubkey,{col},trade_count_7d"
    ).order(col, desc=True).limit(50).execute()
    return res.data or []


@router.get("/leaderboard/token")
def leaderboard_token(period: str = Query("7d", pattern="^(1d|7d|30d)$")):
    sb = get_sb()
    col = {"1d": "avg_score_1d", "7d": "avg_score_7d", "30d": "avg_score_30d"}[period]
    res = sb.table("v_execution_score_by_token").select(
        f"token_mint,{col},trade_count_7d"
    ).order(col, desc=True).limit(50).execute()
    return res.data or []
