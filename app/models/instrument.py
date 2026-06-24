"""Instrument — Layer A. Registered instruments: mortgages, liens, transfers, CPLs."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.id"), index=True)

    instrument_type: Mapped[str | None] = mapped_column(String(64), index=True)  # mortgage, lien, transfer, cpl
    registration_number: Mapped[str | None] = mapped_column(String(128))
    registered_date: Mapped[date | None] = mapped_column(Date)
    amount: Mapped[float | None] = mapped_column(Float)
    party_from: Mapped[str | None] = mapped_column(String(256))
    party_to: Mapped[str | None] = mapped_column(String(256))
    source_code: Mapped[str | None] = mapped_column(String(64), index=True)

    parcel: Mapped["Parcel"] = relationship(back_populates="instruments")  # noqa: F821
