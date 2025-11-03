# app/api/v1/kpis.py
from fastapi import APIRouter
from ...services.kpi_cache import current_kpis

router = APIRouter(prefix="/v1", tags=["kpis"])

@router.get("/kpis")
async def get_kpis():
    return current_kpis()
