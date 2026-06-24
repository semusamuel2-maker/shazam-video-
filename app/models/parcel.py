"""Parcel / Property — the spatial anchor every other record hangs off of."""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Parcel(Base):
    """A parcel of land / property.

    Geometry is stored as a GeoJSON string for portability between SQLite and PostGIS.

    PostGIS production path: add a real spatial column and a GiST index, e.g.::

        from geoalchemy2 import Geometry
        geom = mapped_column(Geometry("POLYGON", srid=4326))

    then run spatial predicates (ST_DWithin, ST_Contains) in the database instead of the
    Python-side haversine used by the demo search service.
    """

    __tablename__ = "parcels"

    id: Mapped[int] = mapped_column(primary_key=True)

    # PID (BC) / PIN (ON) — the registry parcel identifier. Unique per province.
    parcel_id: Mapped[str] = mapped_column(String(64), index=True)
    province: Mapped[str] = mapped_column(String(2), index=True)
    municipality: Mapped[str | None] = mapped_column(String(128), index=True)

    address: Mapped[str | None] = mapped_column(String(256), index=True)
    legal_description: Mapped[str | None] = mapped_column(Text)

    # Centroid for cheap distance math without PostGIS. Geometry holds the full polygon.
    latitude: Mapped[float | None] = mapped_column(Float, index=True)
    longitude: Mapped[float | None] = mapped_column(Float, index=True)
    geometry_geojson: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assessments: Mapped[list["Assessment"]] = relationship(back_populates="parcel", cascade="all, delete-orphan")  # noqa: F821,E501
    ownership_records: Mapped[list["OwnershipRecord"]] = relationship(back_populates="parcel", cascade="all, delete-orphan")  # noqa: F821,E501
    instruments: Mapped[list["Instrument"]] = relationship(back_populates="parcel", cascade="all, delete-orphan")  # noqa: F821,E501
    distress_signals: Mapped[list["DistressSignal"]] = relationship(back_populates="parcel", cascade="all, delete-orphan")  # noqa: F821,E501

    @property
    def geometry(self) -> dict | None:
        return json.loads(self.geometry_geojson) if self.geometry_geojson else None
