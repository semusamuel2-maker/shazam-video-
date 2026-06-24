"""Provenance service: record where every piece of data came from (spec §6 audit trail)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.provenance import ProvenanceRecord


def record(
    session: Session,
    *,
    entity_type: str,
    entity_id: int | None,
    source_code: str,
    action: str,
    detail: str | None = None,
) -> ProvenanceRecord:
    """Append an immutable provenance entry. Caller is responsible for committing."""
    rec = ProvenanceRecord(
        entity_type=entity_type,
        entity_id=entity_id,
        source_code=source_code,
        action=action,
        detail=detail,
    )
    session.add(rec)
    return rec
