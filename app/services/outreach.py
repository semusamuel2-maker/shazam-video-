"""Outreach generation. Postal-first, CASL-enforced for electronic channels.

Generating a campaign renders a message per contact and runs it through the CASL gate.
Postal messages are produced ready-to-mail. Electronic messages without consent are written
with status BLOCKED and a reason — they are never silently sent.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.compliance.casl import can_send
from app.models.enums import ConsentState, OutreachChannel, OutreachStatus
from app.models.outreach import Contact, OutreachCampaign, OutreachMessage


def _render(template: str, contact: Contact) -> str:
    return (template or "").replace("{{name}}", contact.name or "Property Owner").replace(
        "{{address}}", contact.postal_address or ""
    )


def _consent_for(contact: Contact, channel: OutreachChannel) -> ConsentState:
    if channel == OutreachChannel.EMAIL:
        return contact.email_consent
    if channel == OutreachChannel.SMS:
        return contact.sms_consent
    return ConsentState.NONE  # postal: consent not consulted


def generate_messages(session: Session, campaign: OutreachCampaign, contact_ids: list[int]) -> list[OutreachMessage]:
    """Create one message per contact for the campaign, enforcing CASL. Idempotent-ish:
    callers should not re-run for the same campaign+contacts without clearing first."""
    contacts = list(session.scalars(select(Contact).where(Contact.id.in_(contact_ids))))
    messages: list[OutreachMessage] = []

    for contact in contacts:
        decision = can_send(campaign.channel, _consent_for(contact, campaign.channel))
        msg = OutreachMessage(
            campaign_id=campaign.id,
            contact_id=contact.id,
            channel=campaign.channel,
            rendered_body=_render(campaign.template or "", contact),
        )
        if decision.allowed:
            msg.status = OutreachStatus.QUEUED
        else:
            msg.status = OutreachStatus.BLOCKED
            msg.block_reason = decision.reason
        session.add(msg)
        messages.append(msg)

    session.commit()
    return messages


def set_consent(session: Session, contact: Contact, channel: OutreachChannel, target: ConsentState, *, source: str) -> Contact:
    """Apply a validated CASL consent transition to a contact for an electronic channel."""
    from app.compliance.casl import transition

    if channel == OutreachChannel.EMAIL:
        contact.email_consent = transition(contact.email_consent, target)
    elif channel == OutreachChannel.SMS:
        contact.sms_consent = transition(contact.sms_consent, target)
    else:
        raise ValueError("Consent only applies to electronic channels (email/sms).")
    contact.consent_source = source
    contact.consent_updated_at = datetime.now(timezone.utc)
    session.commit()
    return contact
