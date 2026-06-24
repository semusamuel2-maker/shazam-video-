"""Admin / compliance endpoints: ingestion triggers, license catalog, PIPEDA requests."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.compliance import pipeda
from app.config import get_settings
from app.db import get_session
from app.ingestion.base import run_source
from app.ingestion.derived_signals import derive_all
from app.ingestion.registry import sources_for
from app.models.license import DataSourceLicense

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/ingest")
def ingest(province: str | None = None, session: Session = Depends(get_session)):
    """Run all Layer C public sources for the (active) province, then derive signals."""
    province = province or get_settings().active_province
    results = {}
    for source in sources_for(province):
        results[source.source_code] = run_source(session, source)
    derived = derive_all(session)
    return {"province": province, "ingested": results, "derived": derived}


@router.get("/licenses")
def list_licenses(session: Session = Depends(get_session)):
    rows = session.scalars(select(DataSourceLicense))
    return [
        {
            "code": r.code,
            "name": r.name,
            "layer": r.layer.value,
            "province": r.province,
            "can_display": r.can_display,
            "can_export": r.can_export,
            "can_redistribute": r.can_redistribute,
            "can_derive": r.can_derive,
            "cache_ttl_days": r.cache_ttl_days,
            "is_public_open": r.is_public_open,
        }
        for r in rows
    ]


@router.get("/pipeda/access")
def pipeda_access(email: str | None = Query(None), name: str | None = Query(None), session: Session = Depends(get_session)):
    """PIPEDA access request — return personal data held about a subject."""
    return pipeda.export_subject_data(session, email=email, name=name)


@router.delete("/pipeda/data")
def pipeda_delete(email: str | None = Query(None), name: str | None = Query(None), session: Session = Depends(get_session)):
    """PIPEDA deletion request — erase personal data for a subject."""
    n = pipeda.delete_subject_data(session, email=email, name=name)
    return {"deleted": n}
