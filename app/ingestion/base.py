"""Base class for ingestion sources.

Each source declares the :class:`DataSourceLicense` it operates under and yields normalized
records. The runner upserts parcels, attaches signals idempotently (via ``dedupe_key``), and
writes a provenance entry per record. A source must NEVER ingest from a licensed/commercial
system that forbids it — only open-government data and public notices belong here.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.compliance import provenance
from app.models.distress import DistressSignal
from app.models.enums import DistressType
from app.models.license import DataSourceLicense
from app.models.parcel import Parcel


@dataclass
class RawSignal:
    """A normalized distress signal emitted by a source, plus enough to locate the parcel."""

    province: str
    signal_type: DistressType
    confidence: float
    dedupe_key: str
    detail: str | None = None
    published_date: date | None = None
    # Parcel locators — at least one of parcel_id/address should be present.
    parcel_id: str | None = None
    address: str | None = None
    municipality: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    extra: dict = field(default_factory=dict)


class IngestionSource:
    #: Stable code matching a DataSourceLicense.code row.
    source_code: str = ""

    def license_seed(self) -> DataSourceLicense | None:
        """Optional: the license row this source should create on first run."""
        return None

    def fetch(self) -> Iterable[RawSignal]:
        """Yield normalized signals. Override in subclasses."""
        raise NotImplementedError


def _ensure_license(session: Session, source: IngestionSource) -> None:
    seed = source.license_seed()
    if seed is None:
        return
    exists = session.scalar(select(DataSourceLicense).where(DataSourceLicense.code == seed.code))
    if not exists:
        session.add(seed)
        session.flush()


def _upsert_parcel(session: Session, raw: RawSignal) -> Parcel:
    parcel = None
    if raw.parcel_id:
        parcel = session.scalar(
            select(Parcel).where(Parcel.parcel_id == raw.parcel_id, Parcel.province == raw.province)
        )
    if parcel is None and raw.address:
        parcel = session.scalar(
            select(Parcel).where(Parcel.address == raw.address, Parcel.province == raw.province)
        )
    if parcel is None:
        parcel = Parcel(
            parcel_id=raw.parcel_id or f"UNKNOWN-{raw.dedupe_key}",
            province=raw.province,
            municipality=raw.municipality,
            address=raw.address,
            latitude=raw.latitude,
            longitude=raw.longitude,
        )
        session.add(parcel)
        session.flush()
    return parcel


def run_source(session: Session, source: IngestionSource) -> int:
    """Ingest one source. Returns the number of new signals added. Idempotent."""
    _ensure_license(session, source)
    added = 0
    for raw in source.fetch():
        existing = session.scalar(
            select(DistressSignal).where(DistressSignal.dedupe_key == raw.dedupe_key)
        )
        if existing:
            continue
        parcel = _upsert_parcel(session, raw)
        signal = DistressSignal(
            parcel_id=parcel.id,
            signal_type=raw.signal_type,
            confidence=raw.confidence,
            detail=raw.detail,
            source_code=source.source_code,
            published_date=raw.published_date,
            dedupe_key=raw.dedupe_key,
        )
        session.add(signal)
        session.flush()
        provenance.record(
            session,
            entity_type="DistressSignal",
            entity_id=signal.id,
            source_code=source.source_code,
            action="ingested",
            detail=raw.dedupe_key,
        )
        added += 1
    session.commit()
    return added
