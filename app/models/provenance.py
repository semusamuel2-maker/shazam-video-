"""ProvenanceRecord — append-only audit trail (spec §6).

Logs which licensed/public source each ingested record came from and when, so compliance
is provable. Also used to enforce cache-TTL retention sweeps.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ProvenanceRecord(Base):
    __tablename__ = "provenance_records"

    id: Mapped[int] = mapped_column(primary_key=True)

    entity_type: Mapped[str] = mapped_column(String(64), index=True)   # "DistressSignal", ...
    entity_id: Mapped[int | None] = mapped_column(Integer, index=True)
    source_code: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(32))                    # ingested | derived | exported
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    detail: Mapped[str | None] = mapped_column(Text)
