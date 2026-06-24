"""Shared enums used across models, schemas, and compliance logic."""
from __future__ import annotations

import enum


class DataLayer(str, enum.Enum):
    """The data layers from spec §4. Drives license posture and what v1 may ingest."""

    TITLE = "A_title"               # licensed (Teranet / LTSA)
    ASSESSMENT = "B_assessment"     # mixed (MPAC / BC Assessment + municipal open data)
    DISTRESS = "C_distress"         # mostly public — v1 sweet spot
    MLS = "D_mls"                   # licensed — deferred
    CONTACT = "E_contact"           # privacy-sensitive — deferred


class DistressType(str, enum.Enum):
    TAX_SALE = "tax_sale"
    POWER_OF_SALE = "power_of_sale"
    FORECLOSURE = "foreclosure"
    PROBATE = "probate"
    LIEN = "lien"
    CPL = "certificate_of_pending_litigation"
    ABSENTEE = "absentee_owner"
    LONG_HELD = "long_held"
    VACANT = "vacant"


class OwnerType(str, enum.Enum):
    LOCAL = "local"        # mailing address in same municipality as property
    ABSENTEE = "absentee"  # mailing address elsewhere
    CORPORATE = "corporate"
    UNKNOWN = "unknown"


class OutreachChannel(str, enum.Enum):
    POSTAL = "postal"   # v1 default — no CASL consent required
    EMAIL = "email"     # gated by CASL — deferred
    SMS = "sms"         # gated by CASL — deferred


class ConsentState(str, enum.Enum):
    """CASL consent lifecycle for a contact on an electronic channel."""

    NONE = "none"                # no consent — electronic messaging prohibited
    IMPLIED = "implied"          # implied consent (e.g. existing business relationship)
    EXPRESS = "express"          # express opt-in captured
    WITHDRAWN = "withdrawn"      # unsubscribed — permanently blocked


class OutreachStatus(str, enum.Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    SENT = "sent"
    BLOCKED = "blocked"   # blocked by compliance (e.g. no CASL consent)
    FAILED = "failed"
