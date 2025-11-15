# backend/app/services/execution_score.py
from __future__ import annotations
from typing import Any, Dict, Optional

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def norm_t(target: float, maxv: float, x: Optional[float]) -> Optional[float]:
    if x is None: return None
    xx = clamp(x, 0.0, maxv)
    if xx <= target: return 100.0
    return 100.0 * (maxv - xx) / (maxv - target)

def norm_pct(target_pct: float, max_pct: float, x_pct: Optional[float]) -> Optional[float]:
    if x_pct is None: return None
    xx = clamp(x_pct, 0.0, max_pct)
    if xx <= target_pct: return 100.0
    return 100.0 * (max_pct - xx) / (max_pct - target_pct)

def norm_inv_to_baseline(x: Optional[float], p50: Optional[float]) -> Optional[float]:
    if x is None or p50 is None or p50 <= 0: return None
    if x <= p50: return 100.0
    ratio = x / p50
    raw = 100.0 * (1.0 / (ratio ** 1.25))
    return clamp(raw, 0.0, 100.0)

def combine(weights_and_scores: Dict[str, float]) -> Optional[float]:
    # input: {"w:score": score, ...} but we’ll pass {"timing":score,...} and separate weights
    raise NotImplementedError  # not used; we’ll inline for clarity

def compute_subscores(inputs: Dict[str, Any], baselines: Dict[str, Any]) -> Dict[str, Optional[float]]:
    # Timing
    s_event = None
    if inputs.get("delta_slots_event") is not None or inputs.get("delta_ms_event") is not None:
        a = norm_t(2, 12, inputs.get("delta_slots_event"))
        b = norm_t(400, 3000, inputs.get("delta_ms_event"))
        parts = [p for p in (a, b) if p is not None]
        if parts:
            s_event = (0.6*(a or 0) + 0.4*(b or 0)) if (a is not None and b is not None) else sum(parts)/len(parts)

    s_landed = None
    if inputs.get("delta_slots_landed") is not None or inputs.get("delta_ms_landed") is not None:
        a = norm_t(2, 15, inputs.get("delta_slots_landed"))
        b = norm_t(800, 5000, inputs.get("delta_ms_landed"))
        parts = [p for p in (a, b) if p is not None]
        if parts:
            s_landed = (0.6*(a or 0) + 0.4*(b or 0)) if (a is not None and b is not None) else sum(parts)/len(parts)

    timing = None
    if s_event is not None and s_landed is not None:
        timing = 0.7*s_event + 0.3*s_landed
    elif s_event is not None:
        timing = s_event
    elif s_landed is not None:
        timing = s_landed

    # Financial
    price_drift_pct = inputs.get("price_drift_pct")
    s_price = norm_pct(0.005, 0.05, price_drift_pct)
    s_size  = (inputs.get("size_similarity") * 100.0) if inputs.get("size_similarity") is not None else None
    s_route = (inputs.get("route_similarity")* 100.0) if inputs.get("route_similarity") is not None else None

    # optional ROI delta (if provided)
    s_roi = None
    if inputs.get("copy_roi_pct") is not None and inputs.get("source_roi_pct") is not None:
        roi_pen = max(0.0, (inputs["source_roi_pct"] - inputs["copy_roi_pct"]))  # penalize if copy underperforms
        s_roi = clamp(100.0 - roi_pen*5.0, 0.0, 100.0)

    fin_parts = []
    fin_weights = []
    for val, w in ((s_price, 0.6), (s_size, 0.15), (s_route, 0.15), (s_roi, 0.10)):
        if val is not None:
            fin_parts.append((val, w))
            fin_weights.append(w)
    financial = None
    if fin_parts:
        wsum = sum(w for _, w in fin_parts)
        financial = sum(val*w for val, w in fin_parts) / (wsum or 1.0)

    # Cost
    s_tip = norm_inv_to_baseline(inputs.get("tip_per_cu"), baselines.get("tip_per_cu_p50"))
    s_cu_price = norm_inv_to_baseline(inputs.get("cu_price_micro_lamports"), baselines.get("cu_price_p50"))
    cost = None
    cost_parts = [p for p in (s_tip, s_cu_price) if p is not None]
    if cost_parts:
        cost = sum(cost_parts)/len(cost_parts)

    # Congestion
    s_land_again = norm_t(2, 15, inputs.get("delta_slots_landed"))
    cong_factor = None
    if baselines.get("delta_slots_landed_p95") is not None:
        cong_factor = clamp(baselines["delta_slots_landed_p95"]/6.0, 0.5, 2.0)
    congestion = None
    if s_land_again is not None and cong_factor is not None:
        congestion = clamp(s_land_again * cong_factor, 0.0, 100.0)

        # small penalty if overpaying when not congested
        if inputs.get("tip_per_cu") and baselines.get("tip_per_cu_p50"):
            if cong_factor < 0.8 and inputs["tip_per_cu"] > 3.0 * baselines["tip_per_cu_p50"]:
                congestion = clamp(congestion - 15.0, 0.0, 100.0)

    return {
        "timing": timing,
        "financial": financial,
        "cost": cost,
        "congestion": congestion
    }

def finalize_score(sub: Dict[str, Optional[float]]) -> Dict[str, Any]:
    weights = {"timing":0.40,"financial":0.35,"cost":0.15,"congestion":0.10}
    total_w = 0.0
    acc = 0.0
    missing = []
    for k, w in weights.items():
        v = sub.get(k)
        if v is None:
            missing.append(k)
            continue
        acc += v*w
        total_w += w
    score = None
    if total_w > 0:
        score = round(clamp(acc/total_w, 0.0, 100.0), 2)
    status = "READY" if (len(missing)==0 and score is not None) else ("PARTIAL" if score is not None else "FAILED")
    return {"score": score, "status": status, "missing": missing}
