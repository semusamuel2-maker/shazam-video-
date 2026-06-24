"""Seed the database for local demo.

What's real vs. synthetic:
  * REAL Layer C: ingests the public Ontario tax-sale notices from data/sample/.
  * SYNTHETIC: assessment, ownership, and transfer instruments are fabricated and tagged
    with the ``demo_*`` license codes (clearly marked SYNTHETIC) purely so comps, derived
    signals, owner-type filters, and the property page have something to render. This is NOT
    data from Teranet/LTSA/MPAC/BC Assessment — those require commercial licenses (see
    docs/LEGAL.md). Do not treat demo_* data as licensed.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.db import SessionLocal, init_db
from app.ingestion.base import run_source
from app.ingestion.derived_signals import derive_all
from app.ingestion.sources.ontario_tax_sales import OntarioTaxSalesSource
from app.models.assessment import Assessment
from app.models.enums import DataLayer, OutreachChannel, OwnerType
from app.models.instrument import Instrument
from app.models.license import DataSourceLicense
from app.models.outreach import Contact, OutreachCampaign
from app.models.ownership import OwnershipRecord
from app.models.parcel import Parcel
from app.models.property_list import PropertyList, PropertyListItem
from app.models.user import User


def _ensure_demo_licenses(session) -> None:
    demos = [
        DataSourceLicense(
            code="demo_assessment", name="SYNTHETIC demo assessment data", layer=DataLayer.ASSESSMENT,
            province="ON", can_display=True, can_export=True, can_derive=True, can_redistribute=False,
            is_public_open=False, notes="SYNTHETIC. Stand-in for licensed MPAC; not real data.",
        ),
        DataSourceLicense(
            code="demo_title", name="SYNTHETIC demo title data", layer=DataLayer.TITLE,
            province="ON", can_display=True, can_export=False, can_derive=True, can_redistribute=False,
            cache_ttl_days=30, is_public_open=False,
            notes="SYNTHETIC. Stand-in for licensed Teranet; export intentionally denied to "
                  "demonstrate per-source export enforcement.",
        ),
    ]
    for d in demos:
        if not session.scalar(select(DataSourceLicense).where(DataSourceLicense.code == d.code)):
            session.add(d)
    session.commit()


# Synthetic enrichment per ingested parcel: (assessed, tax, year_built, class, owner, mail_muni, owned_since, last_sale)
_ENRICH = {
    "ON-PIN-100001": (310000, 4200, 1962, "RT", "Doe, Jane", "Toronto", date(1995, 6, 1), (2018, 295000)),
    "ON-PIN-100002": (480000, 6100, 1978, "RT", "1234567 Ontario Inc.", "Peterborough", date(2009, 3, 12), (2016, 410000)),
    "ON-PIN-100003": (255000, 3300, 1955, "RT", "Smith, Robert", "Ottawa", date(1990, 1, 20), (2015, 240000)),
    "ON-PIN-100004": (615000, 8800, 1925, "RT", "Estate of A. Brown", "Hamilton", date(1998, 9, 5), (2019, 560000)),
}


def _enrich(session) -> None:
    for pin, (assessed, tax, yb, klass, owner, mail_muni, since, last_sale) in _ENRICH.items():
        parcel = session.scalar(select(Parcel).where(Parcel.parcel_id == pin))
        if parcel is None:
            continue
        if not session.scalar(select(Assessment).where(Assessment.parcel_id == parcel.id)):
            session.add(Assessment(
                parcel_id=parcel.id, roll_year=2025, assessed_value=assessed, tax_amount=tax,
                year_built=yb, property_class=klass, source_code="demo_assessment",
            ))
        if not session.scalar(select(OwnershipRecord).where(OwnershipRecord.parcel_id == parcel.id)):
            session.add(OwnershipRecord(
                parcel_id=parcel.id, owner_name=owner, mailing_municipality=mail_muni,
                mailing_address=f"PO Box, {mail_muni}, ON", owner_type=OwnerType.UNKNOWN,
                ownership_start=since, source_code="demo_title", is_current=True,
            ))
        sale_year, sale_amt = last_sale
        if not session.scalar(select(Instrument).where(Instrument.parcel_id == parcel.id, Instrument.instrument_type == "transfer")):
            session.add(Instrument(
                parcel_id=parcel.id, instrument_type="transfer", amount=sale_amt,
                registered_date=date(sale_year, 7, 1), source_code="demo_title",
            ))
    session.commit()


def _seed_outreach(session) -> None:
    if session.scalar(select(User)) is None:
        session.add(User(email="investor@example.com", display_name="Demo Investor"))
        session.commit()

    # One contact per parcel, postal address from the (synthetic) registered mailing address.
    for parcel in session.scalars(select(Parcel)):
        if session.scalar(select(Contact).where(Contact.parcel_id == parcel.id)):
            continue
        owner = session.scalar(select(OwnershipRecord).where(OwnershipRecord.parcel_id == parcel.id))
        if owner:
            session.add(Contact(
                parcel_id=parcel.id, name=owner.owner_name, postal_address=owner.mailing_address,
                source_code="demo_title",
            ))
    session.commit()

    if session.scalar(select(PropertyList)) is None:
        pl = PropertyList(name="Peterborough tax sales", owner_user_id=1)
        session.add(pl)
        session.flush()
        for parcel in session.scalars(select(Parcel).where(Parcel.municipality == "Peterborough")):
            session.add(PropertyListItem(list_id=pl.id, parcel_id=parcel.id))
        session.commit()

    if session.scalar(select(OutreachCampaign)) is None:
        session.add(OutreachCampaign(
            name="Postal — tax sale owners", channel=OutreachChannel.POSTAL, owner_user_id=1,
            template="Hello {{name}}, regarding your property at {{address}} ...",
        ))
        session.commit()


def main() -> None:
    init_db()
    session = SessionLocal()
    try:
        _ensure_demo_licenses(session)
        added = run_source(session, OntarioTaxSalesSource())
        _enrich(session)
        derived = derive_all(session)
        _seed_outreach(session)
        print(f"Ingested {added} public tax-sale signals; derived {derived}.")
        print("Seed complete. Run: uvicorn app.main:app --reload  ->  http://localhost:8000/")
    finally:
        session.close()


if __name__ == "__main__":
    main()
