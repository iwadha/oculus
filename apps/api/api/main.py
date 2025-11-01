import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from dotenv import find_dotenv, load_dotenv
from supabase import create_client, Client

dotenv_path = find_dotenv(".env", raise_error_if_not_found=False)
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = FastAPI(title="Oculus API", version="0.0.2")

@app.get("/health")
def health():
    try:
        supabase.table("copy_wallets").select("id").limit(1).execute()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase error: {e}")

@app.get("/v1/wallets")
def list_wallets():
    try:
        res = supabase.table("copy_wallets") \
                      .select("id,label,status,created_at,updated_at") \
                      .order("label") \
                      .execute()
        return JSONResponse(res.data or [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase error: {e}")

@app.get("/v1/creators")
def list_creators():
    try:
        res = supabase.table("creators") \
                      .select("id,creator_pubkey,rank,score,created_at,updated_at") \
                      .order("score", desc=True) \
                      .execute()
        return JSONResponse(res.data or [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase error: {e}")
