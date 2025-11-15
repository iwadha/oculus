# app/api/v1/routes/kpis.py
from fastapi import APIRouter
from app.services.kpi_cache import current_kpis

# ✅ Prefix handles /v1/kpis, don’t repeat it in path
router = APIRouter(prefix="/v1/kpis", tags=["kpis"])

@router.get("")  # or @router.get("/")
async def get_kpis():
    return current_kpis()
