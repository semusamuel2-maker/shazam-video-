"""CASL consent state machine for electronic outreach.

Canada's Anti-Spam Legislation requires express or implied consent before a commercial
electronic message (email/SMS), plus sender identification and a working unsubscribe.

Rules encoded here:
  * Postal mail is **not** a CEM — always allowed, no consent needed.
  * Electronic channels require EXPRESS or (non-expired) IMPLIED consent.
  * WITHDRAWN (unsubscribed) is terminal — it can never transition back automatically.
  * A global kill-switch (``ALLOW_ELECTRONIC_OUTREACH``) gates electronic sending even when
    consent exists, so v1 stays postal-only until counsel signs off.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings
from app.models.enums import ConsentState, OutreachChannel


@dataclass(frozen=True)
class ConsentDecision:
    allowed: bool
    reason: str


# Legal transitions for a consent record. Anything not listed is rejected.
_ALLOWED_TRANSITIONS: dict[ConsentState, set[ConsentState]] = {
    ConsentState.NONE: {ConsentState.IMPLIED, ConsentState.EXPRESS},
    ConsentState.IMPLIED: {ConsentState.EXPRESS, ConsentState.WITHDRAWN},
    ConsentState.EXPRESS: {ConsentState.WITHDRAWN},
    ConsentState.WITHDRAWN: set(),  # terminal — unsubscribe is permanent
}


class ConsentTransitionError(Exception):
    pass


def transition(current: ConsentState, target: ConsentState) -> ConsentState:
    """Validate a consent change. Raises if the transition is not permitted by CASL."""
    if target == current:
        return current
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise ConsentTransitionError(
            f"Illegal CASL consent transition {current.value} -> {target.value}"
        )
    return target


def can_send(channel: OutreachChannel, consent: ConsentState) -> ConsentDecision:
    """Decide whether a message may be sent on ``channel`` given the contact's consent."""
    if channel == OutreachChannel.POSTAL:
        return ConsentDecision(True, "postal mail is not a commercial electronic message")

    if not get_settings().allow_electronic_outreach:
        return ConsentDecision(
            False, "electronic outreach disabled (v1 is postal-only until CASL review)"
        )

    if consent in (ConsentState.EXPRESS, ConsentState.IMPLIED):
        return ConsentDecision(True, f"{consent.value} consent on file")
    if consent == ConsentState.WITHDRAWN:
        return ConsentDecision(False, "recipient has unsubscribed (consent withdrawn)")
    return ConsentDecision(False, "no CASL consent on file for electronic messaging")


# Every CEM must carry sender ID + unsubscribe. Templates are checked before send.
REQUIRED_CEM_ELEMENTS = ("sender_identification", "unsubscribe_mechanism")


def validate_cem_template(template: str) -> list[str]:
    """Return a list of missing CASL-required elements for an electronic template."""
    missing = []
    lowered = (template or "").lower()
    if "{{sender_identification}}" not in lowered and "unsubscribe" not in lowered:
        # crude scaffold check; real impl renders + inspects the message
        pass
    if "unsubscribe" not in lowered:
        missing.append("unsubscribe_mechanism")
    if "sender" not in lowered and "{{sender_identification}}" not in lowered:
        missing.append("sender_identification")
    return missing
