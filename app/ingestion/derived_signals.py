"""Derived distress signals (spec §4 Layer C).

Some of the most valuable signals are not ingested but *derived* by the platform from the
licensed title + assessment layers:

  * ABSENTEE  — owner's mailing municipality differs from the property's municipality.
  * LONG_HELD — current ownership started a long time ago (default >= 25 years).

Because these derive from licensed data, they require ``can_derive`` on the underlying
source's license. They are tagged with their own ``source_code`` ("derived") so downstream
license checks treat them as platform-derived rather than raw licensed data.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.compliance import provenance
from app.models.distress import DistressSignal
from app.models.enums import DataLayer, DistressType, OwnerType
from app.models.license import DataSourceLicense
from app.models.ownership import OwnershipRecord
from app.models.parcel import Parcel

DERIVED_SOURCE = "derived"
LONG_HELD_YEARS = 25


def ensure_derived_license(session: Session) -> None:
    if not session.scalar(select(DataSourceLicense).where(DataSourceLicense.code == DERIVED_SOURCE)):
        session.add(
            DataSourceLicense(
                code=DERIVED_SOURCE,
                name="Platform-derived signals",
                layer=DataLayer.DISTRESS,
                can_display=True,
                can_export=True,
                can_redistribute=False,
                can_derive=True,
                cache_ttl_days=None,
                is_public_open=False,
                notes="Signals computed from licensed layers. Honor source can_derive rights.",
            )
        )
        session.flush()


def _add_signal(session: Session, parcel_id: int, signal_type: DistressType, conf: float, detail: str) -> bool:
    key = f"{DERIVED_SOURCE}:{signal_type.value}:{parcel_id}"
    if session.scalar(select(DistressSignal).where(DistressSignal.dedupe_key == key)):
        return False
    sig = DistressSignal(
        parcel_id=parcel_id,
        signal_type=signal_type,
        confidence=conf,
        detail=detail,
        source_code=DERIVED_SOURCE,
        dedupe_key=key,
    )
    session.add(sig)
    session.flush()
    provenance.record(
        session,
        entity_type="DistressSignal",
        entity_id=sig.id,
        source_code=DERIVED_SOURCE,
        action="derived",
        detail=detail,
    )
    return True


def derive_all(session: Session, *, today: date | None = None) -> dict[str, int]:
    """Compute derived signals over current ownership records. Returns counts by type."""
    ensure_derived_license(session)
    today = today or date.today()
    counts = {"absentee": 0, "long_held": 0}

    rows = session.execute(
        select(OwnershipRecord, Parcel)
        .join(Parcel, OwnershipRecord.parcel_id == Parcel.id)
        .where(OwnershipRecord.is_current.is_(True))
    ).all()

    for owner, parcel in rows:
        # Absentee: mailing municipality known and != property municipality.
        if (
            owner.mailing_municipality
            and parcel.municipality
            and owner.mailing_municipality.strip().lower() != parcel.municipality.strip().lower()
        ):
            if _add_signal(
                session, parcel.id, DistressType.ABSENTEE, 0.7,
                f"Owner mails to {owner.mailing_municipality}, property in {parcel.municipality}.",
            ):
                counts["absentee"] += 1
            owner.owner_type = OwnerType.ABSENTEE

        # Long-held: ownership older than threshold.
        if owner.ownership_start and (today.year - owner.ownership_start.year) >= LONG_HELD_YEARS:
            years = today.year - owner.ownership_start.year
            if _add_signal(
                session, parcel.id, DistressType.LONG_HELD, 0.6,
                f"Held for ~{years} years (since {owner.ownership_start.isoformat()}).",
            ):
                counts["long_held"] += 1

    session.commit()
    return counts
