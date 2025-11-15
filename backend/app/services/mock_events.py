import asyncio, random, time
from .bus import bus
from .kpi_cache import record as record_kpi

TOKENS = ["MINT123", "MINTABC", "MINTXYZ", "MINT777"]
WALLETS = ["Athena", "Zeus", "Ares", "Apollo", "Hera", "Hermes"]
CREATORS = ["Cr8r111", "Cr8r222", "Cr8r333", "Cr8r444"]

def _sample_trade() -> dict:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Simulate source vs copy slot — allow occasional "ahead" case
    source_slot = random.randint(10_000_000, 10_010_000)
    # copy can be 1 ahead up to 20 behind
    copy_slot = source_slot + random.randint(-1, 20)

    return {
        "type": "trade",
        "wallet": random.choice(WALLETS),
        "action": random.choice(["BUY", "SELL"]),
        "token": random.choice(TOKENS),
        "creator": random.choice(CREATORS),
        "ts": now,
        "execution_score": random.randint(55, 98),

        # NEW: slots to compute latency
        "source_slot": source_slot,
        "copy_slot": copy_slot,
    }

async def run_mock_event_loop(hz: float, stop_event: asyncio.Event):
    delay = 1.0 / max(hz, 0.1)
    while not stop_event.is_set():
        # ✅ generate one trade and reuse for both bus + KPI
        trade = _sample_trade()
        await bus.publish(trade)
        record_kpi(trade)
        await asyncio.sleep(delay)
