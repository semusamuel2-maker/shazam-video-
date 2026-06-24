"""License-rule enforcement: the moat must fail closed and honor per-source rights."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.compliance.license_rules import LicenseAction, LicenseEnforcer, LicenseViolation
from app.models.enums import DataLayer
from app.models.license import DataSourceLicense


def _add(session, **kw):
    lic = DataSourceLicense(layer=DataLayer.DISTRESS, **kw)
    session.add(lic)
    session.commit()
    return lic


def test_unknown_source_is_denied(session):
    enf = LicenseEnforcer(session)
    assert enf.is_allowed("does_not_exist", LicenseAction.DISPLAY) is False
    with pytest.raises(LicenseViolation):
        enf.require("does_not_exist", LicenseAction.DISPLAY)


def test_missing_source_code_is_denied(session):
    enf = LicenseEnforcer(session)
    assert enf.is_allowed(None, LicenseAction.EXPORT) is False


def test_per_action_rights_respected(session):
    _add(session, code="src1", name="s", can_display=True, can_export=False)
    enf = LicenseEnforcer(session)
    assert enf.is_allowed("src1", LicenseAction.DISPLAY) is True
    assert enf.is_allowed("src1", LicenseAction.EXPORT) is False
    enf.require("src1", LicenseAction.DISPLAY)  # no raise
    with pytest.raises(LicenseViolation):
        enf.require("src1", LicenseAction.EXPORT)


def test_filter_displayable_drops_unlicensed_rows(session):
    _add(session, code="ok", name="s", can_display=True)
    _add(session, code="no", name="s", can_display=False)

    class Row:
        def __init__(self, code):
            self.source_code = code

    enf = LicenseEnforcer(session)
    rows = [Row("ok"), Row("no"), Row("unknown")]
    assert [r.source_code for r in enf.filter_displayable(rows)] == ["ok"]


def test_cache_ttl(session):
    _add(session, code="ttl", name="s", can_display=True, cache_ttl_days=30)
    _add(session, code="open", name="s", can_display=True, cache_ttl_days=None)
    enf = LicenseEnforcer(session)
    fresh = datetime.now(timezone.utc) - timedelta(days=5)
    stale = datetime.now(timezone.utc) - timedelta(days=40)
    assert enf.is_within_cache_ttl("ttl", fresh) is True
    assert enf.is_within_cache_ttl("ttl", stale) is False
    assert enf.is_within_cache_ttl("open", stale) is True  # no limit
