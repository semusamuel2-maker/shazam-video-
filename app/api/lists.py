"""Saved target lists + CSV export (export respects per-source license rules)."""
from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.compliance.license_rules import LicenseAction, LicenseEnforcer
from app.db import get_session
from app.models.assessment import Assessment
from app.models.parcel import Parcel
from app.models.property_list import PropertyList, PropertyListItem
from app.schemas import ListCreate, ListItemCreate

router = APIRouter(prefix="/api/lists", tags=["lists"])


@router.post("")
def create_list(req: ListCreate, session: Session = Depends(get_session)):
    pl = PropertyList(name=req.name, owner_user_id=req.owner_user_id)
    session.add(pl)
    session.commit()
    return {"id": pl.id, "name": pl.name}


@router.post("/{list_id}/items")
def add_item(list_id: int, req: ListItemCreate, session: Session = Depends(get_session)):
    if session.get(PropertyList, list_id) is None:
        raise HTTPException(404, "List not found")
    if session.get(Parcel, req.parcel_id) is None:
        raise HTTPException(404, "Parcel not found")
    item = PropertyListItem(list_id=list_id, parcel_id=req.parcel_id, note=req.note)
    session.add(item)
    session.commit()
    return {"id": item.id}


@router.get("/{list_id}")
def get_list(list_id: int, session: Session = Depends(get_session)):
    pl = session.get(PropertyList, list_id)
    if pl is None:
        raise HTTPException(404, "List not found")
    return {
        "id": pl.id,
        "name": pl.name,
        "items": [{"parcel_id": i.parcel_id, "note": i.note} for i in pl.items],
    }


@router.get("/{list_id}/export.csv")
def export_csv(list_id: int, session: Session = Depends(get_session)):
    """Export a list as CSV. Assessment columns are blanked when the governing license
    does not permit export — enforcing per-source export rights at the boundary."""
    pl = session.get(PropertyList, list_id)
    if pl is None:
        raise HTTPException(404, "List not found")

    enforcer = LicenseEnforcer(session)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["parcel_id", "address", "municipality", "assessed_value", "note"])

    for item in pl.items:
        parcel = session.get(Parcel, item.parcel_id)
        if parcel is None:
            continue
        assessment = session.scalar(
            select(Assessment).where(Assessment.parcel_id == parcel.id).order_by(Assessment.roll_year.desc())
        )
        value = ""
        if assessment and enforcer.is_allowed(assessment.source_code, LicenseAction.EXPORT):
            value = assessment.assessed_value or ""
        writer.writerow([parcel.parcel_id, parcel.address or "", parcel.municipality or "", value, item.note or ""])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="list_{list_id}.csv"'},
    )
