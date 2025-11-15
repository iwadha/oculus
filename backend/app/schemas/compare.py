from pydantic import BaseModel, Field
from typing import Optional, Literal

Confidence = Literal["HIGH", "MED", "LOW", "NONE"]

class TradeSide(BaseModel):
    trade_id: Optional[str] = None
    ts: Optional[str] = None
    slot: Optional[int] = None
    price: Optional[float] = None
    roi_pct: Optional[float] = None
    tip_lamports: Optional[int] = None
    cu_used: Optional[int] = None
    cu_price_micro_lamports: Optional[int] = None
    tx_route: Optional[str] = None

class Deltas(BaseModel):
    slots: Optional[int] = None
    ms: Optional[int] = None
    price_drift_pct: Optional[float] = None
    roi_delta_pct: Optional[float] = None

class Diagnostics(BaseModel):
    cause: Optional[str] = None
    detail: Optional[str] = None

class ComparePayload(BaseModel):
    # Keep JSON the same, avoid name clash by using alias
    pair_id: Optional[str] = None
    side: Optional[str] = None
    token: Optional[str] = Field(None, alias="token_mint")

    copy_side: TradeSide = Field(alias="copy")
    source: TradeSide

    deltas: Deltas
    diagnostics: Diagnostics
    confidence: Confidence = "NONE"

    model_config = {
        # allow passing either field names or aliases
        "populate_by_name": True
    }

class AwaitingPayload(BaseModel):
    status: Literal["AWAITING_MATCH"] = "AWAITING_MATCH"
    message: str = "Awaiting match…"
    confidence: Confidence = "LOW"
