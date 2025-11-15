import os
import time
import random
from typing import Any, Dict, Optional, List
import httpx

# Environment configuration
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "")
HELIUS_REST_BASE = os.getenv("HELIUS_REST_BASE", "")
HELIUS_RPC_URL = os.getenv("HELIUS_RPC_URL", "")
DEFAULT_TIMEOUT = 20.0


class HeliusClient:
    """
    Minimal, retrying Helius REST client:
      - by signature
      - by address (creator) window
      - blocks/slot neighborhood

    This version prefers HELIUS_REST_BASE (https://api.helius.xyz) for /v0/* endpoints
    and falls back to HELIUS_RPC_URL if HELIUS_REST_BASE is not configured.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        rpc_url: Optional[str] = None,
    ):
        # API key: explicit arg > env
        self.api_key = api_key or HELIUS_API_KEY

        # Base URL:
        #   1) explicit rpc_url param (if provided)
        #   2) HELIUS_REST_BASE env (preferred for /v0 paths)
        #   3) HELIUS_RPC_URL env (fallback)
        base = rpc_url or HELIUS_REST_BASE or HELIUS_RPC_URL

        # Strip any query string and trailing slash to avoid //v0/...
        base = base.split("?", 1)[0].rstrip("/")
        self.base_url = base

        self._client = httpx.Client(timeout=DEFAULT_TIMEOUT)

    def _sleep_backoff(self, attempt: int):
        """
        Simple exponential backoff with jitter.
        """
        time.sleep(min(2 ** attempt + random.random(), 8.0))

    def tx_by_signature(self, signature: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a single transaction by signature via Helius v0/transactions.

        Returns:
            - dict for the transaction (if found)
            - None on failure or not found
        """
        url = f"{self.base_url}/v0/transactions/?tx={signature}&api-key={self.api_key}"

        for attempt in range(4):
            try:
                r = self._client.get(url)
                if r.status_code == 200:
                    data = r.json()
                    # Helius may return a list or a single dict
                    if isinstance(data, list) and data:
                        return data[0]
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
            self._sleep_backoff(attempt)

        return None

    def address_txs_window(
        self,
        address: str,
        limit: int = 25,
        before_slot: Optional[int] = None,
        after_slot: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
            """
            Fetch a batch of transactions for a given address.

            NOTE:
                Helius's /v0/addresses/{address}/transactions endpoint does NOT accept
                raw slot numbers as `before` / `after` like we're currently trying.
                That is why calls like `before=50&after=0` are returning HTTP 400.

            SHORT-TERM STRATEGY:
                - Ignore before_slot / after_slot in the REST query for now.
                - Just request the latest `limit` transactions for the address.
                - Let the caller (_pick_best_tx) decide which tx is best based on
                slot / timestamp once we have the JSON.

            This keeps the design multi-wallet and gets us working, and we can later
            upgrade this to the correct Helius-style pagination (signatures, etc.)
            once you're ready.
            """
            # For now, we intentionally ignore before_slot/after_slot in the query.
            qs = f"limit={limit}"
            url = f"{self.base_url}/v0/addresses/{address}/transactions?{qs}&api-key={self.api_key}"

            for attempt in range(4):
                try:
                    r = self._client.get(url)
                    if r.status_code == 200:
                        data = r.json()
                        # Helius typically returns a list here
                        if isinstance(data, list):
                            return data
                        # If it's a dict for some reason, wrap it
                        if isinstance(data, dict):
                            return [data]
                        return []
                    else:
                        # Log non-200s for debugging
                        print(
                            f"[HELIUS] address_txs_window HTTP {r.status_code} "
                            f"for address={address} url={url}"
                                )
                except Exception as e:
                    print(f"[HELIUS] address_txs_window error on attempt {attempt}: {e}")
                self._sleep_backoff(attempt)

            return []


    def block_by_slot(self, slot: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a block by slot using /v0/blocks/{slot}.

        Returns:
            - dict with block data on success
            - None on failure
        """
        url = f"{self.base_url}/v0/blocks/{slot}?api-key={self.api_key}"

        for attempt in range(4):
            try:
                r = self._client.get(url)
                if r.status_code == 200:
                    return r.json()
            except Exception:
                pass
            self._sleep_backoff(attempt)

        return None
