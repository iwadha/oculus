# app/jobs/creator_intel_worker.py
import time
from supabase import create_client
from ..core.config import settings
from ..services.creator_intel import recompute_creator

def _sb():
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_ANON_KEY
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL / SUPABASE_ANON_KEY")
    return create_client(url, key)

def pop_queue_batch(limit=50):
    return (_sb().table("jobs_creator_intel_queue")
              .select("*").order("queued_at", desc=False).limit(limit)
              .execute().data) or []

def delete_row(row):
    (_sb().table("jobs_creator_intel_queue")
        .delete()
        .eq("creator_pubkey", row["creator_pubkey"])
        .eq("queued_at", row["queued_at"])
        .execute())

def enqueue_all_active_creators():
    creators = (_sb().table("creators")
                  .select("source_wallet_pubkey")
                  .eq("is_active", True).execute().data) or []
    payload = [{"creator_pubkey": c["source_wallet_pubkey"], "reason": "daily"} for c in creators]
    if payload:
        _sb().table("jobs_creator_intel_queue").insert(payload).execute()

def run_loop(sleep_sec=5):
    while True:
        batch = pop_queue_batch()
        if not batch:
            time.sleep(sleep_sec)
            continue
        for row in batch:
            cp = row["creator_pubkey"]
            try:
                recompute_creator(cp)
            except Exception as e:
                # TODO: log error to failed jobs table if desired
                pass
            finally:
                delete_row(row)

if __name__ == "__main__":
    run_loop()
