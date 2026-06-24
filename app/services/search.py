"""Property search with the spec §9 filters.

Filtering is done in SQL where possible; the spatial radius filter uses a Python-side
haversine so the scaffold works on SQLite. In production with PostGIS, replace the radius
step with ``ST_DWithin`` against an indexed geometry column for performance.

Results are passed through license enforcement so only display-permitted records surface.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.compliance.license_rules import LicenseAction, LicenseEnforcer
from app.models.assessment import Assessment
from app.models.distress import DistressSignal
from app.models.enums import DistressType, OwnerType
from app.models.ownership import OwnershipRecord
from app.models.parcel import Parcel
from app.services.comps import _haversine_km


@dataclass
class SearchFilters:
    province: str | None = None
    municipality: str | None = None
    distress_types: list[DistressType] | None = None
    owner_type: OwnerType | None = None
    min_value: float | None = None
    max_value: float | None = None
    property_class: str | None = None
    min_years_held: int | None = None
    # Spatial radius
    center_lat: float | None = None
    center_lon: float | None = None
    radius_km: float | None = None
    limit: int = 100


@dataclass
class SearchHit:
    parcel: Parcel
    distress_types: list[str]
    assessed_value: float | None
    owner_type: str | None


def search_properties(session: Session, f: SearchFilters) -> list[SearchHit]:
    stmt = select(Parcel)
    if f.province:
        stmt = stmt.where(Parcel.province == f.province)
    if f.municipality:
        stmt = stmt.where(Parcel.municipality == f.municipality)

    candidates = list(session.scalars(stmt))
    enforcer = LicenseEnforcer(session)
    hits: list[SearchHit] = []

    for parcel in candidates:
        # Spatial radius filter (Python-side; swap for PostGIS ST_DWithin in prod).
        if f.center_lat is not None and f.center_lon is not None and f.radius_km is not None:
            if parcel.latitude is None or parcel.longitude is None:
                continue
            if _haversine_km(f.center_lat, f.center_lon, parcel.latitude, parcel.longitude) > f.radius_km:
                continue

        # Only surface distress signals whose source permits display.
        signals = [
            s for s in session.scalars(
                select(DistressSignal).where(DistressSignal.parcel_id == parcel.id)
            )
            if enforcer.is_allowed(s.source_code, LicenseAction.DISPLAY)
        ]
        types = {s.signal_type for s in signals}

        if f.distress_types and not types.intersection(set(f.distress_types)):
            continue

        owner = session.scalar(
            select(OwnershipRecord)
            .where(OwnershipRecord.parcel_id == parcel.id, OwnershipRecord.is_current.is_(True))
        )
        if f.owner_type and (owner is None or owner.owner_type != f.owner_type):
            continue
        if f.min_years_held is not None:
            if owner is None or owner.ownership_start is None:
                continue
            from datetime import date
            if date.today().year - owner.ownership_start.year < f.min_years_held:
                continue

        assessment = session.scalar(
            select(Assessment)
            .where(Assessment.parcel_id == parcel.id)
            .order_by(Assessment.roll_year.desc())
        )
        value = assessment.assessed_value if assessment else None
        if f.min_value is not None and (value is None or value < f.min_value):
            continue
        if f.max_value is not None and (value is None or value > f.max_value):
            continue
        if f.property_class and (assessment is None or assessment.property_class != f.property_class):
            continue

        hits.append(
            SearchHit(
                parcel=parcel,
                distress_types=sorted(t.value for t in types),
                assessed_value=value,
                owner_type=owner.owner_type.value if owner else None,
            )
        )
        if len(hits) >= f.limit:
            break

    return hits
