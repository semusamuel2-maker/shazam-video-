"""Layer B — Assessment provider interface (MPAC / BC Assessment + municipal open data).

MIXED posture: the authoritative datasets (MPAC, BC Assessment) are LICENSED; some
municipalities publish assessment/parcel attributes under open licences. Only the open
municipal path may be implemented without a commercial license — and only where that
municipality's open-data licence permits it (spec §4 Layer B).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.config import get_settings


@dataclass
class AssessmentResult:
    assessed_value: float | None = None
    tax_amount: float | None = None
    lot_size_sqft: float | None = None
    building_size_sqft: float | None = None
    year_built: int | None = None
    bedrooms: int | None = None
    bathrooms: float | None = None
    property_class: str | None = None
    roll_year: int | None = None
    source_code: str | None = None


class AssessmentProvider(Protocol):
    def lookup(self, parcel_id: str, province: str) -> AssessmentResult | None: ...


class StubAssessmentProvider:
    """v1 default. Returns nothing — no licensed assessment data is available."""

    def lookup(self, parcel_id: str, province: str) -> AssessmentResult | None:  # noqa: ARG002
        return None


# --- Real adapters once licensed / where open licence permits. ---
#
# class MunicipalOpenDataProvider:
#     """Ingest a municipality's OPEN assessment/parcel attributes. source_code per city."""
#
# class MpacProvider / BcAssessmentProvider:  # LICENSED — needs agreement.


def get_assessment_provider() -> AssessmentProvider:
    provider = get_settings().assessment_provider
    if provider == "stub":
        return StubAssessmentProvider()
    raise NotImplementedError(
        f"Assessment provider '{provider}' is not implemented. Add a licensed (or "
        "open-data) adapter before enabling it (see app/providers/assessment.py)."
    )
