# app/schemas/creators.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CreatorRow(BaseModel):
    creator_pubkey: str
    alias: str
    copyability_tier: Optional[str] = None
    risk_score: Optional[float] = None
    creator_rank: Optional[float] = None
    last_activity: Optional[datetime] = None

    trades_copied_24h: int = 0
    trades_copied_7d: int = 0
    avg_execution_score_7d: float = 0.0
    delta_slots_7d: float = 0.0
    roi_me_7d: float = 0.0

    trades_copied_30d: int = 0
    avg_execution_score_30d: float = 0.0
    delta_slots_30d: float = 0.0
    roi_me_30d: float = 0.0

    fail_rate_7d: Optional[float] = 0.0
    skip_rate_7d: Optional[float] = 0.0

class CatalogResponse(BaseModel):
    items: List[CreatorRow] = Field(default_factory=list)
    page: int
    page_size: int
    total: int
