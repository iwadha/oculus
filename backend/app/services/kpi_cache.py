# app/services/kpi_cache.py
from collections import deque
from time import time
from typing import Deque, Dict, Any

MAX_BUF = 1000
_T: Deque[Dict[str, Any]] = deque(maxlen=MAX_BUF)

def record(evt: Dict[str, Any]) -> None:
    e = dict(evt)
    e["_t"] = time()
    _T.appendleft(e)

def current_kpis() -> Dict[str, Any]:
    if not _T:
        return {
            "active_creators": 0,
            "buy_pct": 0.0,
            "avg_blocks": 0.0,
            "avg_score": 0.0,
            "tps": 0.0,
            "window": 0,
        }
    total = len(_T)
    creators = {e.get("creator", "") for e in _T}
    buys = sum(1 for e in _T if e.get("action") == "BUY")
    deltas = [(e.get("copy_slot", 0) - e.get("source_slot", 0)) for e in _T]
    avg_blocks = sum(deltas) / total
    avg_score = sum(int(e.get("execution_score", 0)) for e in _T) / total

    now = time()
    recent = sum(1 for e in _T if now - e["_t"] <= 15.0)
    tps = recent / 15.0

    return {
        "active_creators": len(creators),
        "buy_pct": (buys / total) * 100.0,
        "avg_blocks": avg_blocks,
        "avg_score": avg_score,
        "tps": tps,
        "window": total,
    }
