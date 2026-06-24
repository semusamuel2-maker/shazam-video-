"""Layer C ingestion: idempotency, provenance, license seeding, derived signals."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.ingestion.base import run_source
from app.ingestion.derived_signals import derive_all
from app.ingestion.sources.ontario_tax_sales import OntarioTaxSalesSource
from app.models.distress import DistressSignal
from app.models.enums import DistressType, OwnerType
from app.models.license import DataSourceLicense
from app.models.ownership import OwnershipRecord
from app.models.parcel import Parcel
from app.models.provenance import ProvenanceRecord


def test_tax_sale_ingestion_creates_signals_and_is_idempotent(session):
    src = OntarioTaxSalesSource()
    added = run_source(session, src)
    assert added == 4  # matches the sample fixture

    # Re-running ingests nothing new (dedupe_key).
    assert run_source(session, src) == 0

    signals = list(session.scalars(select(DistressSignal)))
    assert len(signals) == 4
    assert all(s.signal_type == DistressType.TAX_SALE for s in signals)


def test_ingestion_seeds_license_and_provenance(session):
    run_source(session, OntarioTaxSalesSource())
    lic = session.scalar(select(DataSourceLicense).where(DataSourceLicense.code == "on_tax_sales"))
    assert lic is not None and lic.is_public_open is True and lic.can_display is True

    prov = list(session.scalars(select(ProvenanceRecord).where(ProvenanceRecord.action == "ingested")))
    assert len(prov) == 4


def test_derived_absentee_and_long_held(session):
    parcel = Parcel(parcel_id="P1", province="ON", municipality="Peterborough")
    session.add(parcel)
    session.flush()
    session.add(OwnershipRecord(
        parcel_id=parcel.id, owner_name="Jane Doe", mailing_municipality="Toronto",
        owner_type=OwnerType.UNKNOWN, ownership_start=date(1990, 1, 1),
        source_code="demo_title", is_current=True,
    ))
    session.commit()

    counts = derive_all(session, today=date(2026, 1, 1))
    assert counts["absentee"] == 1
    assert counts["long_held"] == 1

    types = {s.signal_type for s in session.scalars(select(DistressSignal))}
    assert DistressType.ABSENTEE in types
    assert DistressType.LONG_HELD in types

    # Idempotent.
    counts2 = derive_all(session, today=date(2026, 1, 1))
    assert counts2 == {"absentee": 0, "long_held": 0}
