# app/core/config.py
from __future__ import annotations

import json
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


def _csv_to_list(val: str | None) -> List[str]:
    if not val:
        return []
    return [x.strip() for x in val.split(",") if x.strip()]


class Settings(BaseSettings):
    # -----------------------
    # App / Runtime
    # -----------------------
    ENV: str = Field("dev", alias="ENV")  # dev|staging|prod
    LOG_LEVEL: str = Field("info", alias="LOG_LEVEL")

    # SSE / Streaming
    SSE_HEARTBEAT_SECONDS: int = Field(10, alias="OCULUS_SSE_HEARTBEAT_SECONDS")
    STREAM_SOURCE: str = Field("mock", alias="OCULUS_STREAM_SOURCE")  # "mock" | "db"
    DB_POLL_MS: int = Field(500, alias="OCULUS_DB_POLL_MS")

    # CORS (JSON or CSV)
    CORS_ALLOW_ORIGINS_JSON: Optional[str] = Field(None, alias="CORS_ALLOW_ORIGINS_JSON")
    CORS_ALLOW_ORIGINS_CSV: Optional[str] = Field(None, alias="CORS_ALLOW_ORIGINS")
    CORS_ALLOW_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Supabase (used when STREAM_SOURCE=db)
    SUPABASE_URL: str = Field("", alias="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field("", alias="SUPABASE_ANON_KEY")

    # Tables / columns
    TABLE_TRADES: str = Field("trades_ledger", alias="OCULUS_TABLE_TRADES")
    TRADES_PK_COL: str = Field("id", alias="OCULUS_COPY_PK_COL")

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def _merge_cors(cls, v, info):
        # priority: JSON env → CSV env → default
        data = info.data or {}
        raw_json = data.get("CORS_ALLOW_ORIGINS_JSON")
        raw_csv = data.get("CORS_ALLOW_ORIGINS_CSV")
        if raw_json:
            try:
                parsed = json.loads(raw_json)
                if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                    return parsed
            except Exception:
                pass
        if raw_csv:
            parsed = _csv_to_list(raw_csv)
            if parsed:
                return parsed
        return v

    @property
    def is_db_stream(self) -> bool:
        return self.STREAM_SOURCE.lower() == "db"


settings = Settings()
