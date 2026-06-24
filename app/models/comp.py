"""Comp — derived value estimate. v1 runs off assessment + title sale-history, NOT MLS."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Comp(Base):
    __tablename__ = "comps"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.id"), index=True)

    estimated_value: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(64), default="assessment_ratio")
    comparable_count: Mapped[int] = mapped_column(Integer, default=0)
    # JSON list of supporting parcel ids / sale records (kept as text for portability).
    supporting: Mapped[str | None] = mapped_column(Text)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
