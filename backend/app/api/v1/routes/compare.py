from fastapi import APIRouter, HTTPException
from typing import Union

from app.services.pairing_service import compare_for_trade
from app.schemas.compare import ComparePayload, AwaitingPayload
from app.core.config import settings

router = APIRouter(prefix="/v1/trades", tags=["compare"])

@router.get("/{trade_id}/compare", response_model=Union[ComparePayload, AwaitingPayload])
def get_compare(trade_id: int):
    if not settings.FEATURE_MODULE3:
        raise HTTPException(status_code=404, detail="Module 3 disabled")
    payload = compare_for_trade(trade_id)
    return payload
