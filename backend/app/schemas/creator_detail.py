from pydantic import BaseModel
from typing import List, Optional, Tuple

class CreatorProfile(BaseModel):
    creator_pubkey: str
    alias: str
    copyability_tier: Optional[str] = None
    risk_score: Optional[float] = None
    creator_rank: Optional[float] = None
    last_activity: Optional[str] = None

    trades_copied_24h: int = 0
    trades_copied_7d: int = 0
    avg_execution_score_7d: float = 0.0
    delta_slots_7d: float = 0.0
    roi_me_7d: float = 0.0

    trades_copied_30d: int = 0
    avg_execution_score_30d: float = 0.0
    delta_slots_30d: float = 0.0
    roi_me_30d: float = 0.0

    badges: List[str] = []

class ActivityRow(BaseModel):
    pair_id: str
    token_symbol: Optional[str]
    token_mint: str
    side: str
    source_event_ts: Optional[str]
    source_landed_ts: Optional[str]
    copy_ts: Optional[str]
    delta_slots_event: Optional[int]
    delta_ms_event: Optional[int]
    delta_slots_landed: Optional[int]
    delta_ms_landed: Optional[int]
    price_drift_pct: Optional[float]
    execution_score: Optional[float]
    confidence: Optional[float]
    status: Optional[str]
    copy_roi_pct: Optional[float]
    source_tx_sig: Optional[str]
    copy_tx_sig: Optional[str]
    paired_at: Optional[str]

class ActivityPage(BaseModel):
    page: int
    page_size: int
    total_estimate: Optional[int] = None
    rows: List[ActivityRow]

class ChartSeries(BaseModel):
    window: str
    roi_for_me: List[Tuple[str, float]]
    execution_score: List[Tuple[str, float]]
    delta_slots: List[Tuple[str, float]]
    crowding: List[Tuple[str, float]]
