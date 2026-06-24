"""Application configuration.

Defaults are chosen so the scaffold runs with zero setup (SQLite, postal-only outreach,
stubbed licensed providers). Production overrides come from environment / `.env`.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Storage. SQLite by default so tests/demo need no Postgres. Use PostGIS in prod.
    database_url: str = "sqlite:///./prop.sqlite3"

    # Single-province launch (see spec §2.4). All data is scoped to this province in v1.
    active_province: str = "ON"

    # CASL guardrail. v1 is postal-only; electronic channels stay gated regardless.
    allow_electronic_outreach: bool = False

    # Licensed-layer providers. "stub" => no live data (v1 default).
    title_provider: str = "stub"
    assessment_provider: str = "stub"
    title_api_key: str = ""
    assessment_api_key: str = ""

    @property
    def is_postgis(self) -> bool:
        return self.database_url.startswith("postgresql")


@lru_cache
def get_settings() -> Settings:
    return Settings()
