"""CASL consent state machine + send gating."""
from __future__ import annotations

import pytest

from app.compliance.casl import (
    ConsentTransitionError,
    can_send,
    transition,
    validate_cem_template,
)
from app.models.enums import ConsentState, OutreachChannel


def test_postal_always_allowed_regardless_of_consent():
    assert can_send(OutreachChannel.POSTAL, ConsentState.NONE).allowed is True
    assert can_send(OutreachChannel.POSTAL, ConsentState.WITHDRAWN).allowed is True


def test_electronic_blocked_when_globally_disabled():
    # Default test env has ALLOW_ELECTRONIC_OUTREACH=false.
    assert can_send(OutreachChannel.EMAIL, ConsentState.EXPRESS).allowed is False


def test_legal_transitions():
    assert transition(ConsentState.NONE, ConsentState.EXPRESS) == ConsentState.EXPRESS
    assert transition(ConsentState.IMPLIED, ConsentState.WITHDRAWN) == ConsentState.WITHDRAWN
    assert transition(ConsentState.NONE, ConsentState.NONE) == ConsentState.NONE  # no-op ok


def test_withdrawn_is_terminal():
    with pytest.raises(ConsentTransitionError):
        transition(ConsentState.WITHDRAWN, ConsentState.EXPRESS)


def test_cannot_skip_back_from_express_to_none():
    with pytest.raises(ConsentTransitionError):
        transition(ConsentState.EXPRESS, ConsentState.NONE)


def test_cem_template_requires_unsubscribe_and_sender():
    missing = validate_cem_template("Hi there, buy my stuff")
    assert "unsubscribe_mechanism" in missing
    assert "sender_identification" in missing
    ok = validate_cem_template("From sender Acme. Reply STOP to unsubscribe.")
    assert ok == []
