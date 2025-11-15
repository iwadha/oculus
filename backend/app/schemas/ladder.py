from typing import List, Literal, Optional
from pydantic import BaseModel


Badge = Literal[
    "Missing Source Event",
    "Execution Alone",
    "Early Execution",
    "On-Time",
    "Late Execution",
    "Contested Block",
    "Overpaid Tip",
    "Tip Slightly High",
    "Under-tipped",
]


class CopyTx(BaseModel):
    tx_signature: Optional[str]
    tip_lamports: Optional[int]
    cu_used: Optional[int]
    priority_fee_lamports: Optional[int]
    cu_price_micro_lamports: Optional[float]
    status: Optional[str]


class SourceTx(BaseModel):
    creator_pubkey: Optional[str]
    event_slot: Optional[int]
    landed_slot: Optional[int]
    tip_lamports: Optional[int]
    cu_used: Optional[int]
    cu_price_micro_lamports: Optional[float]


class SlotAgg(BaseModel):
    slot: int
    relative: int
    copies: int
    sources: int
    tip_avg: Optional[float] = None
    cu_price_avg: Optional[float] = None


class Crowding(BaseModel):
    ahead: int
    at_event: int
    behind: int
    total: int
    copies_per_slot: List[SlotAgg]


class FeePercentiles(BaseModel):
    p50: Optional[float] = None
    p66: Optional[float] = None
    p90: Optional[float] = None


class NeighborFeeStats(BaseModel):
    n: int
    tip_lamports: FeePercentiles
    cu_price_micro_lamports: FeePercentiles


class HistBin(BaseModel):
    bin_min: Optional[float] = None
    bin_max: Optional[float] = None
    count: int


class NeighborDistributions(BaseModel):
    tip_lamports_hist: List[HistBin]
    cu_price_micro_lamports_hist: List[HistBin]


class NeighborExample(BaseModel):
    copy_wallet_label: Optional[str] = None
    tx_signature: Optional[str] = None
    tip_lamports: Optional[int] = None
    cu_used: Optional[int] = None
    cu_price_micro_lamports: Optional[float] = None


class NeighborSampleGroup(BaseModel):
    slot: int
    relative: int
    copies: int
    examples: List[NeighborExample]


class NeighborSamples(BaseModel):
    top_ahead: List[NeighborSampleGroup]
    top_behind: List[NeighborSampleGroup]


class Efficiency(BaseModel):
    tip_grade: Optional[str] = None
    cu_price_grade: Optional[str] = None
    notes: List[str] = []


class LadderResponse(BaseModel):
    pair_id: int
    token_mint: Optional[str]
    side: Optional[str]
    window: int
    event_slot: Optional[int]
    landed_slot: Optional[int]
    delta_slots: Optional[int]

    copy_tx: CopyTx
    source_tx: SourceTx

    crowding: Crowding
    neighbor_fee_stats: NeighborFeeStats
    neighbor_distributions: NeighborDistributions
    neighbor_samples: NeighborSamples

    efficiency: Efficiency
    badges: List[Badge]
    confidence: Optional[str]
