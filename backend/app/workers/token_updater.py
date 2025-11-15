"""
Token Updater Worker
--------------------
Fetches token metadata for all seen mints from Helius API
and stores it in the Supabase 'tokens' table.

Requires:
  HELIUS_API_KEY
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
"""

import os
import asyncio
import aiohttp
import logging
from datetime import datetime
from supabase import create_client, Client
from typing import List, Dict, Any, Optional

# --- ENV -------------------------------------------------------------------

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BATCH_SIZE = int(os.getenv("TOKEN_BATCH_SIZE", "50"))
REFRESH_MINUTES = int(os.getenv("TOKEN_REFRESH_MINUTES", "60"))

# --- LOGGER ----------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("token_updater")

# --- SUPABASE --------------------------------------------------------------

def supa() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


async def fetch_all_mints(client: Client) -> List[str]:
    """Collect distinct mints from trades_ledger + source_trades."""
    seen = set()
    for tbl in ["trades_ledger", "source_trades"]:
        res = client.table(tbl).select("token_mint").neq("token_mint", None).execute().data or []
        seen.update(r["token_mint"] for r in res if r.get("token_mint"))
    existing = client.table("tokens").select("mint").execute().data or []
    existing_mints = {r["mint"] for r in existing}
    new_mints = list(seen - existing_mints)
    log.info(f"Found {len(new_mints)} new mints to refresh")
    return new_mints


async def fetch_metadata_from_helius(mints: List[str]) -> List[Dict[str, Any]]:
    """Call Helius token-metadata endpoint."""
    if not mints:
        return []
    url = f"https://api.helius.xyz/v0/token-metadata?api-key={HELIUS_API_KEY}"
    payload = {"mintAccounts": mints}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                log.warning(f"Helius metadata fetch failed ({resp.status})")
                return []
            return await resp.json()


async def upsert_tokens(client: Client, metadata: List[Dict[str, Any]]):
    """Write metadata into Supabase 'tokens' table."""
    now = datetime.utcnow().isoformat() + "Z"
    for entry in metadata:
        try:
            mint = entry.get("mint")
            meta = entry.get("onChainMetadata", {}).get("metadata", {}).get("data", {}) or {}
            off = entry.get("offChainMetadata", {}) or {}

            payload = {
                "mint": mint,
                "symbol": off.get("symbol") or meta.get("symbol"),
                "name": off.get("name") or meta.get("name"),
                "decimals": entry.get("decimals"),
                "logo_uri": off.get("image"),
                "updated_at": now,
            }
            client.table("tokens").upsert(payload, on_conflict="mint").execute()
            log.info(f"[TOK] {mint[:6]}… {payload['symbol']}")
        except Exception as e:
            log.warning(f"[WARN] upsert failed: {e}")


# --- MAIN LOOP -------------------------------------------------------------

async def run_once():
    client = supa()
    new_mints = await fetch_all_mints(client)
    if not new_mints:
        return

    # chunk by BATCH_SIZE
    for i in range(0, len(new_mints), BATCH_SIZE):
        chunk = new_mints[i : i + BATCH_SIZE]
        meta = await fetch_metadata_from_helius(chunk)
        if meta:
            await upsert_tokens(client, meta)
        await asyncio.sleep(2)


async def main():
    while True:
        try:
            await run_once()
        except Exception as e:
            log.warning(f"[ERROR] main loop failed: {e}")
        log.info(f"Sleeping {REFRESH_MINUTES} min")
        await asyncio.sleep(REFRESH_MINUTES * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Shutdown requested by user")
