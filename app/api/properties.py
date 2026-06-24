"""Search + property-detail endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.compliance.license_rules import LicenseAction, LicenseEnforcer
from app.db import get_session
from app.models.assessment import Assessment
from app.models.instrument import Instrument
from app.models.ownership import OwnershipRecord
from app.models.parcel import Parcel
from app.schemas import (
    CompOut,
    DistressOut,
    ParcelOut,
    PropertyDetailOut,
    SearchHitOut,
    SearchRequest,
)
from app.services import comps as comps_service
from app.services.search import SearchFilters, search_properties

router = APIRouter(prefix="/api", tags=["properties"])


@router.post("/search", response_model=list[SearchHitOut])
def search(req: SearchRequest, session: Session = Depends(get_session)):
    filters = SearchFilters(**req.model_dump())
    hits = search_properties(session, filters)
    return [
        SearchHitOut(
            parcel=ParcelOut.model_validate(h.parcel),
            distress_types=h.distress_types,
            assessed_value=h.assessed_value,
            owner_type=h.owner_type,
        )
        for h in hits
    ]


@router.get("/properties/{parcel_id}", response_model=PropertyDetailOut)
def property_detail(parcel_id: int, session: Session = Depends(get_session)):
    parcel = session.get(Parcel, parcel_id)
    if parcel is None:
        raise HTTPException(404, "Parcel not found")

    enforcer = LicenseEnforcer(session)

    assessment = session.scalar(
        select(Assessment).where(Assessment.parcel_id == parcel.id).order_by(Assessment.roll_year.desc())
    )
    owner = session.scalar(
        select(OwnershipRecord).where(
            OwnershipRecord.parcel_id == parcel.id, OwnershipRecord.is_current.is_(True)
        )
    )
    instruments = list(session.scalars(select(Instrument).where(Instrument.parcel_id == parcel.id)))
    signals = enforcer.filter_displayable(
        list(parcel.distress_signals)  # type: ignore[arg-type]
    )

    # Comp estimate (assessment + title sale-history; never MLS).
    est = comps_service.estimate_value(session, parcel)

    def _displayable(obj):
        return obj is not None and enforcer.is_allowed(
            getattr(obj, "source_code", None), LicenseAction.DISPLAY
        )

    return PropertyDetailOut(
        parcel=ParcelOut.model_validate(parcel),
        assessment=(
            {
                "assessed_value": assessment.assessed_value,
                "tax_amount": assessment.tax_amount,
                "year_built": assessment.year_built,
                "property_class": assessment.property_class,
                "roll_year": assessment.roll_year,
            }
            if _displayable(assessment)
            else None
        ),
        ownership=(
            {
                "owner_name": owner.owner_name,
                "owner_type": owner.owner_type.value,
                "mailing_address": owner.mailing_address,
                "ownership_start": owner.ownership_start.isoformat() if owner.ownership_start else None,
            }
            if _displayable(owner)
            else None
        ),
        instruments=[
            {
                "instrument_type": i.instrument_type,
                "registered_date": i.registered_date.isoformat() if i.registered_date else None,
                "amount": i.amount,
            }
            for i in instruments
            if _displayable(i)
        ],
        distress_signals=[
            DistressOut(
                signal_type=s.signal_type,
                confidence=s.confidence,
                detail=s.detail,
                source_code=s.source_code,
                published_date=s.published_date.isoformat() if s.published_date else None,
            )
            for s in signals
        ],
        comp=CompOut(
            estimated_value=est.estimated_value,
            low=est.low,
            high=est.high,
            method=est.method,
            comparable_count=est.comparable_count,
        ),
    )
