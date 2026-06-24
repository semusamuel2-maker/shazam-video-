"""OwnershipRecord — Layer A. Registered owner of record + mailing address."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import OwnerType


class OwnershipRecord(Base):
    __tablename__ = "ownership_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.id"), index=True)

    owner_name: Mapped[str | None] = mapped_column(String(256))
    # Registered mailing address — the lawful postal-outreach target in v1.
    mailing_address: Mapped[str | None] = mapped_column(String(256))
    mailing_municipality: Mapped[str | None] = mapped_column(String(128))

    owner_type: Mapped[OwnerType] = mapped_column(default=OwnerType.UNKNOWN, index=True)
    ownership_start: Mapped[date | None] = mapped_column(Date)
    source_instrument: Mapped[str | None] = mapped_column(String(128))
    source_code: Mapped[str | None] = mapped_column(String(64), index=True)
    is_current: Mapped[bool] = mapped_column(default=True, index=True)

    parcel: Mapped["Parcel"] = relationship(back_populates="ownership_records")  # noqa: F821
