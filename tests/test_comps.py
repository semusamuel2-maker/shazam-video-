"""Comp estimation from assessment + title sale-history (no MLS)."""
from __future__ import annotations

from datetime import date

from app.models.assessment import Assessment
from app.models.instrument import Instrument
from app.models.parcel import Parcel
from app.providers.deferred import DeferredLayerError, mls_comps
from app.services.comps import estimate_value


def _parcel(session, pin, lat, lon, assessed, sale=None):
    p = Parcel(parcel_id=pin, province="ON", municipality="X", latitude=lat, longitude=lon)
    session.add(p)
    session.flush()
    session.add(Assessment(parcel_id=p.id, roll_year=2025, assessed_value=assessed, source_code="demo_assessment"))
    if sale:
        session.add(Instrument(parcel_id=p.id, instrument_type="transfer", amount=sale,
                               registered_date=date(2020, 1, 1), source_code="demo_title"))
    session.commit()
    return p


def test_assessment_ratio_method_with_enough_comps(session):
    # Three nearby comps all sold at ~1.2x assessed.
    _parcel(session, "C1", 44.30, -78.32, 100000, sale=120000)
    _parcel(session, "C2", 44.301, -78.321, 200000, sale=240000)
    _parcel(session, "C3", 44.302, -78.322, 150000, sale=180000)
    subject = _parcel(session, "S", 44.3005, -78.3205, 250000)

    est = estimate_value(session, subject)
    assert est.method == "assessment_ratio"
    assert est.comparable_count >= 3
    assert abs(est.estimated_value - 300000) < 1  # 250k * 1.2


def test_fallback_when_insufficient_comps(session):
    subject = _parcel(session, "S", 44.30, -78.32, 250000)
    est = estimate_value(session, subject)
    assert est.method == "assessed_value_fallback"
    assert est.estimated_value == 250000
    assert est.low < est.estimated_value < est.high


def test_mls_layer_is_deferred_and_fails_loudly():
    try:
        mls_comps()
        assert False, "expected DeferredLayerError"
    except DeferredLayerError:
        pass
