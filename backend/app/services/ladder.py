from typing import Any, Dict, List, Tuple, Optional
from asyncpg import Connection, Pool
from supabase import create_client
import os

# Supabase client using environment variables (same as sql.py)
_SUPABASE_URL = os.environ["SUPABASE_URL"]
_SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_ANON_KEY"]

_sb = create_client(_SUPABASE_URL, _SUPABASE_KEY)


DEFAULT_WINDOW = 8
MIN_WINDOW = 2
MAX_WINDOW = 32

# Badge thresholds (tunable later)
BADGE_CONTESTED_THRESHOLD = 5      # total crowd
BADGE_LATE_THRESHOLD = 10          # delta_slots
# Grading thresholds are derived from percentiles we fetch


def fetch_ladder_snapshot(copy_trade_id: int) -> Optional[Dict[str, Any]]:
    res = (_sb.table("ladder_snapshots")
              .select("*")
              .eq("copy_trade_id", copy_trade_id)
              .limit(1)
              .execute())
    return (res.data or [None])[0]

def ladder_for_trade(copy_trade_id: int) -> Dict[str, Any]:
    snap = fetch_ladder_snapshot(copy_trade_id)
    if not snap:
        return {"status": "MISSING", "message": "No ladder snapshot", "copy_trade_id": copy_trade_id}

    return {
        "status": "OK",
        "copy_trade_id": copy_trade_id,
        # canonical, compact fields (populated by the ladder worker):
        "copy_slot": snap.get("copy_slot"),
        "source_slot": snap.get("source_slot"),
        "delta_slots_event": snap.get("delta_slots_event"),
        "delta_ms_event": snap.get("delta_ms_event"),
        "crowd_before_copy": snap.get("crowd_before_copy"),
        "crowd_before_source": snap.get("crowd_before_source"),
        "tip_lamports_pctl": snap.get("tip_lamports_pctl"),
        "cu_price_micro_lamports_pctl": snap.get("cu_price_micro_lamports_pctl"),
        "badges": snap.get("badges"),  # e.g., ["MEGA_CROWD","HIGH_TIP"]
        "diagnostics": snap.get("diagnostics"),
    }

def build_crowd(neighbors: List[Dict[str, Any]], event_slot: Optional[int]) -> Dict[str, int]:
    ahead = at_event = behind = 0
    for n in neighbors:
        rel = n["relative"]
        c = int(n["copies"])
        if rel < 0:
            ahead += c
        elif rel == 0:
            at_event += c
        else:
            behind += c
    return {"ahead": ahead, "at_event": at_event, "behind": behind, "total": ahead + at_event + behind}


def grade_efficiency(
    copy_tip: Optional[int],
    copy_cu_price: Optional[float],
    pct: Dict[str, Any],
) -> Tuple[Optional[str], Optional[str], List[str]]:
    notes: List[str] = []

    def grade(val: Optional[float], p50: Optional[float], p66: Optional[float], p90: Optional[float]) -> Optional[str]:
        if val is None or p50 is None:
            return None
        if p66 is None or p90 is None:
            # fall back to simple median split
            return "Underpay" if val < p50 else "Optimal"
        if val <= p66:
            return "Optimal" if val >= p50 else "Underpay"
        if val <= p90:
            return "Slight Overpay"
        return "Overpay"

    tip_grade = grade(
        float(copy_tip) if copy_tip is not None else None,
        pct.get("tip_p50"), pct.get("tip_p66"), pct.get("tip_p90"),
    )
    cu_grade = grade(
        copy_cu_price,
        pct.get("cu_p50"), pct.get("cu_p66"), pct.get("cu_p90"),
    )

    if copy_tip is not None and pct.get("tip_p66") is not None:
        if copy_tip > pct["tip_p90"]:
            notes.append("You paid ≥90th percentile tip vs window")
        elif copy_tip > pct["tip_p66"]:
            notes.append("You paid >66th percentile tip vs window")
        elif pct.get("tip_p50") is not None and copy_tip < pct["tip_p50"]:
            notes.append("You paid <median tip vs window")

    return tip_grade, cu_grade, notes


def derive_badges(
    event_slot: Optional[int],
    delta_slots: Optional[int],
    crowd_total: int,
    tip_grade: Optional[str],
) -> List[str]:
    b: List[str] = []
    if event_slot is None:
        b.append("Missing Source Event")
        return b
    if crowd_total == 0:
        b.append("Execution Alone")
    if delta_slots is not None:
        if delta_slots < 0:
            b.append("Early Execution")
        elif delta_slots == 0:
            b.append("On-Time")
        elif delta_slots >= BADGE_LATE_THRESHOLD:
            b.append("Late Execution")
    if crowd_total >= BADGE_CONTESTED_THRESHOLD:
        b.append("Contested Block")
    if tip_grade == "Overpay":
        b.append("Overpaid Tip")
    elif tip_grade == "Slight Overpay":
        b.append("Tip Slightly High")
    elif tip_grade == "Underpay" and (delta_slots or 0) > 0:
        b.append("Under-tipped")
    return b
