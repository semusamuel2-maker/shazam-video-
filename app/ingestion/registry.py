"""Registry of available ingestion sources, keyed by province.

The scheduled job / CLI iterates the active province's sources. Add new public/open sources
here; licensed feeds are wired through ``app/providers`` instead, not here.
"""
from __future__ import annotations

from app.ingestion.base import IngestionSource
from app.ingestion.sources.ontario_tax_sales import OntarioTaxSalesSource

SOURCES_BY_PROVINCE: dict[str, list[type[IngestionSource]]] = {
    "ON": [OntarioTaxSalesSource],
    # "BC": [BcTaxSaleSource, ...],  # add when expanding
}


def sources_for(province: str) -> list[IngestionSource]:
    return [cls() for cls in SOURCES_BY_PROVINCE.get(province, [])]
