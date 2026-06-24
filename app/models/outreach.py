"""Outreach — campaigns, messages, and the CASL consent record for a contact.

v1 ships **postal-only**. Email/SMS exist in the model but are gated by the CASL state
machine (``app/compliance/casl.py``) and the ``ALLOW_ELECTRONIC_OUTREACH`` flag. A message
on an electronic channel without express/implied consent is forced to ``BLOCKED``.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import ConsentState, OutreachChannel, OutreachStatus


class Contact(Base):
    """A person/entity we may reach out to, with per-channel CASL consent state.

    PIPEDA note: this is personal information. v1 only ever populates the postal address
    (from the registered mailing address in Layer A). Email/phone stay empty until a
    PIPEDA-licensed source + consent capture are reviewed by counsel (spec §4 Layer E).
    """

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcel_id: Mapped[int | None] = mapped_column(ForeignKey("parcels.id"), index=True)
    name: Mapped[str | None] = mapped_column(String(256))
    postal_address: Mapped[str | None] = mapped_column(String(256))
    email: Mapped[str | None] = mapped_column(String(256))   # empty in v1
    phone: Mapped[str | None] = mapped_column(String(64))    # empty in v1

    # CASL consent per electronic channel. Postal needs no consent.
    email_consent: Mapped[ConsentState] = mapped_column(default=ConsentState.NONE)
    sms_consent: Mapped[ConsentState] = mapped_column(default=ConsentState.NONE)
    consent_source: Mapped[str | None] = mapped_column(String(256))  # how consent was obtained
    consent_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    source_code: Mapped[str | None] = mapped_column(String(64), index=True)


class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    channel: Mapped[OutreachChannel] = mapped_column(default=OutreachChannel.POSTAL)
    template: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    messages: Mapped[list["OutreachMessage"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("outreach_campaigns.id"), index=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)

    channel: Mapped[OutreachChannel] = mapped_column(default=OutreachChannel.POSTAL)
    status: Mapped[OutreachStatus] = mapped_column(default=OutreachStatus.DRAFT, index=True)
    rendered_body: Mapped[str | None] = mapped_column(Text)
    block_reason: Mapped[str | None] = mapped_column(String(256))  # set when compliance blocks
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    campaign: Mapped["OutreachCampaign"] = relationship(back_populates="messages")
