"""DistressSignal — Layer C. The v1 value driver.

Signals are either *ingested* from public notices (tax sales) or *derived* by the platform
from licensed layers (absentee, long-held). ``confidence`` reflects how certain we are.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import DistressType


class DistressSignal(Base):
    __tablename__ = "distress_signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.id"), index=True)

    signal_type: Mapped[DistressType] = mapped_column(index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)  # 0..1
    detail: Mapped[str | None] = mapped_column(Text)

    # Provenance: which source produced this, when it was published/detected.
    source_code: Mapped[str | None] = mapped_column(String(64), index=True)
    published_date: Mapped[date | None] = mapped_column(Date)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Idempotency key so re-ingesting the same public notice doesn't duplicate signals.
    dedupe_key: Mapped[str | None] = mapped_column(String(256), unique=True, index=True)

    parcel: Mapped["Parcel"] = relationship(back_populates="distress_signals")  # noqa: F821
