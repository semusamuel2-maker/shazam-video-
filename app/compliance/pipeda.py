"""PIPEDA helpers: data minimization, purpose limitation, access/deletion.

PIPEDA governs how we collect and handle personal information. v1's posture is to hold the
*minimum* personal data needed for postal outreach (name + registered mailing address) and
nothing more. These helpers make that posture explicit and enforceable.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.outreach import Contact

# Fields on Contact that constitute personal information under PIPEDA.
PERSONAL_FIELDS = ("name", "postal_address", "email", "phone")

# Fields v1 is permitted to populate. Email/phone require Layer E licensing + consent.
V1_ALLOWED_PERSONAL_FIELDS = ("name", "postal_address")


def minimize_contact_payload(payload: dict) -> dict:
    """Strip personal fields v1 is not allowed to store (data minimization)."""
    disallowed = set(PERSONAL_FIELDS) - set(V1_ALLOWED_PERSONAL_FIELDS)
    return {k: v for k, v in payload.items() if k not in disallowed}


def export_subject_data(session: Session, *, email: str | None = None, name: str | None = None) -> list[dict]:
    """PIPEDA access request: return all personal data held about a data subject."""
    stmt = select(Contact)
    if email:
        stmt = stmt.where(Contact.email == email)
    elif name:
        stmt = stmt.where(Contact.name == name)
    else:
        return []
    return [
        {f: getattr(c, f) for f in PERSONAL_FIELDS} | {"id": c.id, "source": c.source_code}
        for c in session.scalars(stmt)
    ]


def delete_subject_data(session: Session, *, email: str | None = None, name: str | None = None) -> int:
    """PIPEDA deletion request: remove personal data for a subject. Returns rows affected."""
    stmt = select(Contact)
    if email:
        stmt = stmt.where(Contact.email == email)
    elif name:
        stmt = stmt.where(Contact.name == name)
    else:
        return 0
    contacts = list(session.scalars(stmt))
    for c in contacts:
        session.delete(c)
    session.commit()
    return len(contacts)
