"""Assessment — Layer B. Assessed value + physical characteristics for a roll year."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcel_id: Mapped[int] = mapped_column(ForeignKey("parcels.id"), index=True)

    roll_year: Mapped[int | None] = mapped_column(Integer, index=True)
    assessed_value: Mapped[float | None] = mapped_column(Float)
    tax_amount: Mapped[float | None] = mapped_column(Float)

    lot_size_sqft: Mapped[float | None] = mapped_column(Float)
    building_size_sqft: Mapped[float | None] = mapped_column(Float)
    year_built: Mapped[int | None] = mapped_column(Integer)
    bedrooms: Mapped[int | None] = mapped_column(Integer)
    bathrooms: Mapped[float | None] = mapped_column(Float)
    property_class: Mapped[str | None] = mapped_column(String(64), index=True)

    # Which licensed/open source this row came from (FK into data_source_licenses.code).
    source_code: Mapped[str | None] = mapped_column(String(64), index=True)

    parcel: Mapped["Parcel"] = relationship(back_populates="assessments")  # noqa: F821
