"""DataSourceLicense — per-source rules, enforced across the app.

This is the codified moat (spec §6). Every record carries a ``source_code`` that resolves
to one of these rows; the compliance layer consults the rules before displaying, exporting,
or redistributing data, and the cache TTL governs how long ingested data may be retained.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import DataLayer


class DataSourceLicense(Base):
    __tablename__ = "data_source_licenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # e.g. "on_tax_sales"
    name: Mapped[str] = mapped_column(String(256))
    layer: Mapped[DataLayer] = mapped_column(index=True)
    province: Mapped[str | None] = mapped_column(String(2), index=True)

    # Core enforceable rights. Defaults are conservative (deny) — open them per agreement.
    can_display: Mapped[bool] = mapped_column(Boolean, default=False)
    can_export: Mapped[bool] = mapped_column(Boolean, default=False)
    can_redistribute: Mapped[bool] = mapped_column(Boolean, default=False)
    can_derive: Mapped[bool] = mapped_column(Boolean, default=False)

    # How long ingested rows may be cached/retained, in days. None = no limit (open data).
    cache_ttl_days: Mapped[int | None] = mapped_column(Integer)

    is_public_open: Mapped[bool] = mapped_column(Boolean, default=False)  # open-gov / public notice
    license_terms_url: Mapped[str | None] = mapped_column(String(512))
    notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
