# backend/app/core/config.py
# Clean, corrected, safe version of Settings

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Central application configuration.
    Reads from environment variables automatically.
    All defaults are safe for development.
    """

    # ------------------------------------------------------------------
    # General App / FastAPI Settings
    # ------------------------------------------------------------------
    API_V1_PREFIX: str = "/v1"
    BACKEND_CORS_ORIGINS: list[str] = Field(default=["*"], env="BACKEND_CORS_ORIGINS")

    # ------------------------------------------------------------------
    # Stream Source
    # ------------------------------------------------------------------
    # mock | db
    STREAM_SOURCE: str = Field(default="db", env="OCULUS_STREAM_SOURCE")

    # If STREAM_SOURCE=mock is used:
    MOCK_EVENTS_ENABLED: bool = Field(default=False, env="MOCK_EVENTS_ENABLED")
    MOCK_EVENTS_HZ: float = Field(default=1.0, env="MOCK_EVENTS_HZ")

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # ------------------------------------------------------------------
    # Pairing Settings
    # ------------------------------------------------------------------
    PAIR_WINDOW_MS: int = Field(
        default=90000,
        env="PAIR_WINDOW_MS",
        description="Max time window (ms) to consider source trades for pairing.",
    )

    PAIRING_BATCH_SIZE: int = Field(default=200, env="PAIRING_BATCH_SIZE")
    PAIRING_INTERVAL_MS: int = Field(default=5000, env="PAIRING_INTERVAL_MS")

    FEATURE_WORKER_PAIRING: bool = Field(default=True, env="FEATURE_WORKER_PAIRING")

    # ------------------------------------------------------------------
    # Ladder Worker
    # ------------------------------------------------------------------
    LADDER_BACKFILL_BATCH: int = Field(default=200, env="LADDER_BACKFILL_BATCH")
    LADDER_INTERVAL_MS: int = Field(default=8000, env="LADDER_INTERVAL_MS")

    FEATURE_WORKER_LADDER: bool = Field(default=True, env="FEATURE_WORKER_LADDER")

    # ------------------------------------------------------------------
    # Scoring Worker
    # ------------------------------------------------------------------
    SCORING_BATCH_SIZE: int = Field(default=200, env="SCORING_BATCH_SIZE")
    SCORING_INTERVAL_MS: int = Field(default=5000, env="SCORING_INTERVAL_MS")

    FEATURE_WORKER_SCORING: bool = Field(default=True, env="FEATURE_WORKER_SCORING")

    # ------------------------------------------------------------------
    # Alerts Worker
    # ------------------------------------------------------------------
    EXEC_SCORE_ALERT_THRESHOLD: int = Field(
        default=60, env="EXEC_SCORE_ALERT_THRESHOLD"
    )
    ALERTS_BATCH_SIZE: int = Field(default=200, env="ALERTS_BATCH_SIZE")
    ALERTS_INTERVAL_MS: int = Field(default=8000, env="ALERTS_INTERVAL_MS")

    FEATURE_WORKER_ALERTS: bool = Field(default=True, env="FEATURE_WORKER_ALERTS")

    # ------------------------------------------------------------------
    # Token Updater Worker
    # ------------------------------------------------------------------
    FEATURE_WORKER_TOKEN_UPDATER: bool = Field(
        default=True, env="FEATURE_WORKER_TOKEN_UPDATER"
    )

    # ------------------------------------------------------------------
    # Creator Intel Worker
    # ------------------------------------------------------------------
    FEATURE_WORKER_CREATOR_INTEL: bool = Field(
        default=True, env="FEATURE_WORKER_CREATOR_INTEL"
    )

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        case_sensitive = True
        env_file = ".env"


# Instantiate the global settings
settings = Settings()
