# app/services/creator_intel.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta, date
import math
from supabase import create_client
from ..core.config import settings

def _sb():
    """
    Lazily create a Supabase client using settings.
    Avoids failing at import time when env is not loaded yet.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_ANON_KEY
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL / SUPABASE_ANON_KEY in environment.")
    return create_client(url, key)

_sb_cached_client = None

def sb():
    """Return a cached Supabase client, creating it lazily."""
    global _sb_cached_client
    if _sb_cached_client is None:
        _sb_cached_client = _sb()
    return _sb_cached_client


# ---- thresholds (tune later) ----
LATE_ENTRY_MS = 1500
LATE_ENTRY_DRIFT_PCT = 2.0
CHASE_DRIFT_PCT = 3.0

# helpers
def _utcnow_iso() -> str:
    return datetime.utcnow().isoformat()

def _since(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).isoformat()

def _safe_avg(vals: List[float]) -> float:
    return sum(vals)/len(vals) if vals else 0.0

def _safe_std(vals: List[float]) -> float:
    if len(vals) < 2:
        return 0.0
    mu = _safe_avg(vals)
    var = sum((x-mu)**2 for x in vals)/(len(vals)-1)
    return math.sqrt(var)

def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def _exp(x: float) -> float:
    try:
        return math.e ** x
    except Exception:
        return 0.0

# ---- data fetch ----
def _fetch_pairs_plus(creator_pubkey: str, days: int) -> List[dict]:
    # joined with creator_pubkey
    q = (sb().table("v_trade_compare_plus")
           .select("*")
           .gte("source_ts", _since(days))
           .eq("creator_pubkey", creator_pubkey))
    return q.execute().data

def _fetch_source_core(creator_pubkey: str, days: int) -> List[dict]:
    q = (sb().table("v_creator_trade_core")
           .select("*")
           .gte("event_ts", _since(days))
           .eq("creator_pubkey", creator_pubkey))
    return q.execute().data

def _fetch_exec_avg_7d(creator_pubkey: str) -> float:
    # v_execution_score_by_creator includes avg_score_7d
    res = (sb().table("v_execution_score_by_creator")
             .select("avg_score_7d")
             .eq("creator_pubkey", creator_pubkey)
             .limit(1)).execute().data
    if res and res[0].get("avg_score_7d") is not None:
        return float(res[0]["avg_score_7d"])
    return 0.0

def _fetch_last_trade_ts(creator_pubkey: str) -> Optional[datetime]:
    res = (sb().table("source_trades")
             .select("event_ts")
             .eq("source_wallet_pubkey", creator_pubkey)
             .order("event_ts", desc=True)
             .limit(1)).execute().data
    if res and res[0].get("event_ts"):
        return datetime.fromisoformat(res[0]["event_ts"].replace("Z",""))
    return None

# ---- metrics computation ----
def compute_metrics_window(creator_pubkey: str, days: int) -> Dict:
    pairs = _fetch_pairs_plus(creator_pubkey, days)
    src   = _fetch_source_core(creator_pubkey, days)

    # 1) win_rate / roi stats (paired only)
    copy_rois = [float(p.get("copy_roi_pct", 0) or 0) for p in pairs if p.get("copy_roi_pct") is not None]
    win_rate = 0.0
    if copy_rois:
        wins = sum(1 for r in copy_rois if r > 0)
        win_rate = wins / len(copy_rois)

    avg_roi_pct = _safe_avg(copy_rois)
    roi_std_pct = _safe_std(copy_rois)

    # 2) late_entry_rate
    late_flags = []
    for p in pairs:
        dms = p.get("delta_ms_event")
        drift = p.get("price_drift")
        if dms is None and drift is None:
            continue
        is_late = False
        if dms is not None and isinstance(dms, (int, float)):
            if dms > LATE_ENTRY_MS:
                is_late = True
        if drift is not None:
            try:
                if float(drift) > LATE_ENTRY_DRIFT_PCT:
                    is_late = True
            except:
                pass
        late_flags.append(1.0 if is_late else 0.0)
    late_entry_rate = _safe_avg(late_flags) if late_flags else 0.0

    # 3) chase_rate (price_drift > CHASE_DRIFT_PCT and ROI ends negative)
    chase_flags = []
    for p in pairs:
        drift = p.get("price_drift")
        roi   = p.get("copy_roi_pct")
        try:
            if drift is not None and float(drift) > CHASE_DRIFT_PCT and roi is not None and float(roi) < 0:
                chase_flags.append(1.0)
            else:
                chase_flags.append(0.0)
        except:
            pass
    chase_rate = _safe_avg(chase_flags) if chase_flags else 0.0

    # 4) exec_score_avg (7d specific source)
    exec_score_avg = _fetch_exec_avg_7d(creator_pubkey)

    # 5) position size consistency (creator source_trades buys only)
    sizes = [float(s.get("size") or 0) for s in src if (s.get("side_text") or "").upper() == "BUY"]
    position_cv = 0.0
    if sizes:
        mu = _safe_avg(sizes)
        if mu > 0:
            position_cv = _safe_std(sizes) / mu

    # 6) avg_hold_hrs (creator: time from first BUY to last SELL per token in window)
    # group by token_mint; collect buy/sell timestamps
    by_token: Dict[str, Dict[str, List[datetime]]] = {}
    for s in src:
        tm = s.get("token_mint")
        side = (s.get("side_text") or "").upper()
        ets = s.get("event_ts")
        if not tm or not ets:
            continue
        d = by_token.setdefault(tm, {"BUY": [], "SELL": []})
        try:
            d[side].append(datetime.fromisoformat(ets.replace("Z","")))
        except:
            pass
    holds_hrs: List[float] = []
    sells_within_15m = 0
    sells_after_2h   = 0
    total_sell_cases = 0
    for tm, g in by_token.items():
        if g["BUY"] and g["SELL"]:
            first_buy = min(g["BUY"])
            last_sell = max(g["SELL"])
            dt = (last_sell - first_buy).total_seconds() / 3600.0
            if dt >= 0:
                holds_hrs.append(dt)
            # stats for badges
            for ss in g["SELL"]:
                delta_min = (ss - first_buy).total_seconds()/60.0
                total_sell_cases += 1
                if delta_min <= 15:
                    sells_within_15m += 1
                if delta_min >= 120:
                    sells_after_2h += 1
    avg_hold_hrs = _safe_avg(holds_hrs)

    # 7) crowd_pressure proxy:
    # normalize combination of: late_entry_rate, mean delta_ms_event (scaled), token trade density from your copies
    deltas = [float(p["delta_ms_event"]) for p in pairs if p.get("delta_ms_event") is not None]
    mean_delta_ms = _safe_avg(deltas)
    scaled_delta = _clip(mean_delta_ms / 3000.0, 0.0, 1.0)  # 3000ms ~ high
    # token density: max same-token copies in window / total pairs
    token_counts: Dict[str, int] = {}
    for p in pairs:
        tm = p.get("token_mint")
        if tm: token_counts[tm] = token_counts.get(tm, 0) + 1
    density = 0.0
    if pairs and token_counts:
        density = max(token_counts.values()) / len(pairs)
    crowd_pressure = _clip(0.5*late_entry_rate + 0.3*scaled_delta + 0.2*density, 0.0, 1.0)

    # 8) liquidity reaction penalty (proxy):
    # penalize if many buys have positive drift but negative ROI
    liq_flags = []
    for p in pairs:
        drift = p.get("price_drift")
        roi   = p.get("copy_roi_pct")
        try:
            if drift is not None and float(drift) > 0 and roi is not None and float(roi) < 0:
                liq_flags.append(1.0)
            else:
                liq_flags.append(0.0)
        except:
            pass
    liquidity_penalty = _safe_avg(liq_flags) if liq_flags else 0.0

    trade_count = len(pairs)

    # badge helper stats
    pct_sold_15m = (sells_within_15m / total_sell_cases) if total_sell_cases else 0.0
    pct_sold_after_2h = (sells_after_2h / total_sell_cases) if total_sell_cases else 0.0

    return {
        "win_rate": win_rate,
        "avg_roi_pct": avg_roi_pct,
        "roi_std_pct": roi_std_pct,
        "late_entry_rate": late_entry_rate,
        "chase_rate": chase_rate,
        "exec_score_avg": exec_score_avg,
        "position_cv": position_cv,
        "avg_hold_hrs": avg_hold_hrs,
        "crowd_pressure": crowd_pressure,
        "liquidity_penalty": liquidity_penalty,
        "trade_count": trade_count,
        "pct_sold_15m": pct_sold_15m,
        "pct_sold_after_2h": pct_sold_after_2h
    }

def compute_metrics_7d_with_fallback(creator_pubkey: str) -> Dict:
    m7 = compute_metrics_window(creator_pubkey, 7)
    if m7["trade_count"] >= 10:
        return m7
    m30 = compute_metrics_window(creator_pubkey, 30)
    # mark that it’s fallback by embedding a flag
    m30["_fallback_30d"] = True
    return m30

def risk_trend_tier_from_metrics(m7: Dict, m30_baseline: Optional[Dict] = None) -> Tuple[float, str, str]:
    # risk
    risk = 100.0 * (
        0.25 * m7["late_entry_rate"] +
        0.20 * m7["chase_rate"] +
        0.15 * _clip(abs(m7["roi_std_pct"]) / 25.0, 0.0, 1.0) +
        0.10 * m7["crowd_pressure"] +
        0.10 * max(0.0, (0.50 - m7["win_rate"]) * 2.0) +
        0.10 * m7["liquidity_penalty"] +
        0.10 * _clip(m7["position_cv"] / 1.0, 0.0, 1.0)
    )
    # trend (compare 7d to 30d)
    if not m30_baseline:
        m30_baseline = m7  # neutral if no baseline
    def _rel(a: float, b: float) -> float:
        if b == 0: return 0.0
        return (a - b) / abs(b)
    rel_roi = _rel(m7["avg_roi_pct"], m30_baseline.get("avg_roi_pct", 0.0001))
    rel_win = _rel(m7["win_rate"],   m30_baseline.get("win_rate", 0.0001))
    trend = "NEUTRAL"
    if rel_roi >= 0.20 and rel_win >= 0.20:
        trend = "BULLISH"
    elif rel_roi <= -0.20 and rel_win <= -0.20:
        trend = "BEARISH"

    # copyability tier
    tier = "D"
    exec_score = m7.get("exec_score_avg", 0.0)
    if m7["trade_count"] < 5:
        # cap at B
        if risk < 50 and exec_score >= 55: tier = "B"
        elif risk < 65: tier = "C"
        else: tier = "D"
    else:
        if risk < 25 and exec_score >= 75:
            tier = "S"
        elif risk < 35 and exec_score >= 65:
            tier = "A"
        elif risk < 50 and exec_score >= 55:
            tier = "B"
        elif risk < 65:
            tier = "C"
        else:
            tier = "D"

    return float(round(risk, 2)), trend, tier

def _days_since(dt: Optional[datetime]) -> float:
    if not dt: return 999.0
    return (datetime.utcnow() - dt).total_seconds() / 86400.0

def compute_signal_confidence(creator_pubkey: str, trade_count: int) -> float:
    last_ts = _fetch_last_trade_ts(creator_pubkey)
    recency = _exp(-_days_since(last_ts) / 7.0)
    volume  = min(1.0, trade_count / 20.0)
    return float(round(min(recency, volume), 2))

def compute_badges(m: Dict) -> List[str]:
    badges: List[str] = []
    # Smart Entries
    if m["late_entry_rate"] < 0.20 and m["avg_roi_pct"] > 0.0:
        badges.append("Smart Entries")
    # Bad Chaser
    if m["chase_rate"] > 0.35:
        badges.append("Bad Chaser")
    # Diamond Hands / Paper Hands
    if m["avg_hold_hrs"] > 6.0 and m["pct_sold_after_2h"] >= 0.60:
        badges.append("Diamond Hands")
    if m["avg_hold_hrs"] < 0.5 and m["pct_sold_15m"] >= 0.60:
        badges.append("Paper Hands")
    # Conviction Trader
    if m["position_cv"] > 0 and m["position_cv"] < 0.35 and m["win_rate"] >= 0.60:
        badges.append("Conviction Trader")
    # Exit Early (approx)
    if m["avg_hold_hrs"] < 0.5 and m["avg_roi_pct"] > 0:
        badges.append("Exit Early")
    return badges

def upsert_daily_and_creator(creator_pubkey: str, m: Dict, risk: float, trend: str, tier: str, conf: float):
    # daily rollup
    today = date.today().isoformat()
    sb().table("creator_intel_daily").upsert({
        "creator_pubkey": creator_pubkey,
        "day": today,
        "win_rate": m["win_rate"],
        "avg_roi_pct": m["avg_roi_pct"],
        "roi_std_pct": m["roi_std_pct"],
        "avg_hold_hrs": m["avg_hold_hrs"],
        "position_cv": m["position_cv"],
        "crowd_pressure": m["crowd_pressure"],
        "late_entry_rate": m["late_entry_rate"],
        "chase_rate": m["chase_rate"],
        "exec_score_avg": m["exec_score_avg"],
        "trade_count": m["trade_count"],
        "risk_score": risk,
        "trend": trend,
        "copyability": tier
    }, on_conflict="creator_pubkey,day").execute()

    # badges: compare with existing creator
    current = (sb().table("creators")
                 .select("badges")
                 .eq("source_wallet_pubkey", creator_pubkey)
                 .single().execute().data) or {}
    old = current.get("badges") or []
    new_badges = compute_badges(m)

    # write badge diff to history
    add = [b for b in new_badges if b not in old]
    for b in add:
        sb().table("creator_badges_history").insert({
            "creator_pubkey": creator_pubkey,
            "badge": b,
            "reason": "auto-rule"
        }).execute()

    sb().table("creators").update({
        "risk_score": risk,
        "trend": trend,
        "copyability": tier,
        "badges": new_badges,
        "signal_confidence": conf,
        "intel_updated_at": _utcnow_iso(),
        "intel_metrics": m
    }).eq("source_wallet_pubkey", creator_pubkey).execute()

def recompute_creator(creator_pubkey: str) -> Dict:
    m7 = compute_metrics_7d_with_fallback(creator_pubkey)
    # baselines for trend: if we used 30d fallback for the “7d”, recompute 30d again as baseline (it’s identical but ok)
    m30 = compute_metrics_window(creator_pubkey, 30)
    risk, trend, tier = risk_trend_tier_from_metrics(m7, m30_baseline=m30)
    conf = compute_signal_confidence(creator_pubkey, m7["trade_count"])
    upsert_daily_and_creator(creator_pubkey, m7, risk, trend, tier, conf)
    return {
        "creator": creator_pubkey,
        "trend": trend,
        "risk_score": risk,
        "copyability": tier,
        "badges": compute_badges(m7),
        "signal_confidence": conf,
        "metrics": m7,
        "updated_at": _utcnow_iso()
    }
