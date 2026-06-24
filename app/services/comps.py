"""Basic comp / value estimate — NO MLS (spec §5.3, §4 Layer D deferred).

v1 estimates value from two licensed-but-non-MLS inputs:

  1. Assessment value of the subject, scaled by the local assessment-to-sale ratio observed
     from nearby title sale-history (transfer instruments with amounts).
  2. A fallback to the subject's own assessed value when too few comparables exist.

This is intentionally simple and transparent; it is a research aid, not an appraisal. When
MLS sold data is later licensed, add an MLS-backed method and prefer it.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.comp import Comp
from app.models.instrument import Instrument
from app.models.parcel import Parcel

DEFAULT_RADIUS_KM = 2.0
MIN_COMPARABLES = 3


@dataclass
class CompEstimate:
    estimated_value: float | None
    low: float | None
    high: float | None
    method: str
    comparable_count: int
    supporting: list[int]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _latest_assessed(session: Session, parcel_id: int) -> float | None:
    a = session.scalar(
        select(Assessment)
        .where(Assessment.parcel_id == parcel_id)
        .order_by(Assessment.roll_year.desc())
    )
    return a.assessed_value if a else None


def estimate_value(session: Session, parcel: Parcel, radius_km: float = DEFAULT_RADIUS_KM) -> CompEstimate:
    subject_assessed = _latest_assessed(session, parcel.id)

    ratios: list[float] = []
    supporting: list[int] = []
    if parcel.latitude is not None and parcel.longitude is not None:
        others = session.scalars(
            select(Parcel).where(Parcel.id != parcel.id, Parcel.province == parcel.province)
        )
        for other in others:
            if other.latitude is None or other.longitude is None:
                continue
            if _haversine_km(parcel.latitude, parcel.longitude, other.latitude, other.longitude) > radius_km:
                continue
            sale = session.scalar(
                select(Instrument)
                .where(Instrument.parcel_id == other.id, Instrument.instrument_type == "transfer")
                .where(Instrument.amount.is_not(None))
                .order_by(Instrument.registered_date.desc())
            )
            assessed = _latest_assessed(session, other.id)
            if sale and sale.amount and assessed:
                ratios.append(sale.amount / assessed)
                supporting.append(other.id)

    if subject_assessed and len(ratios) >= MIN_COMPARABLES:
        ratios.sort()
        median_ratio = ratios[len(ratios) // 2]
        est = subject_assessed * median_ratio
        spread = est * 0.1
        return CompEstimate(
            estimated_value=round(est, 2),
            low=round(est - spread, 2),
            high=round(est + spread, 2),
            method="assessment_ratio",
            comparable_count=len(ratios),
            supporting=supporting,
        )

    # Fallback: not enough comparables — return assessed value with a wider band.
    if subject_assessed:
        return CompEstimate(
            estimated_value=round(subject_assessed, 2),
            low=round(subject_assessed * 0.85, 2),
            high=round(subject_assessed * 1.15, 2),
            method="assessed_value_fallback",
            comparable_count=len(ratios),
            supporting=supporting,
        )

    return CompEstimate(None, None, None, "insufficient_data", len(ratios), supporting)


def save_comp(session: Session, parcel: Parcel, est: CompEstimate) -> Comp:
    comp = Comp(
        parcel_id=parcel.id,
        estimated_value=est.estimated_value,
        low=est.low,
        high=est.high,
        method=est.method,
        comparable_count=est.comparable_count,
        supporting=json.dumps(est.supporting),
    )
    session.add(comp)
    session.commit()
    return comp
