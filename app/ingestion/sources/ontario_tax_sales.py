"""Ontario municipal tax-sale notices — a genuinely public Layer C source.

Ontario municipalities are required to publicly advertise tax-sale properties. Those
notices are legitimately collectable. This adapter reads from a local fixture
(``data/sample/on_tax_sales.json``) so the scaffold runs offline; a production
implementation would fetch the same shape from the public notice listings (respecting
robots/ToU and rate limits) and map them into :class:`RawSignal`.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import date
from pathlib import Path

from app.ingestion.base import IngestionSource, RawSignal
from app.models.enums import DataLayer, DistressType
from app.models.license import DataSourceLicense

_DATA = Path(__file__).resolve().parents[3] / "data" / "sample" / "on_tax_sales.json"


class OntarioTaxSalesSource(IngestionSource):
    source_code = "on_tax_sales"

    def __init__(self, data_path: Path | None = None):
        self.data_path = data_path or _DATA

    def license_seed(self) -> DataSourceLicense:
        # Public notice => open posture: display/export/derive allowed, no cache limit.
        return DataSourceLicense(
            code=self.source_code,
            name="Ontario Municipal Tax Sale Notices (public)",
            layer=DataLayer.DISTRESS,
            province="ON",
            can_display=True,
            can_export=True,
            can_redistribute=False,  # be conservative on redistribution even for public data
            can_derive=True,
            cache_ttl_days=None,
            is_public_open=True,
            notes="Publicly advertised municipal tax sales. Verify each municipality's terms.",
        )

    def fetch(self) -> Iterable[RawSignal]:
        if not self.data_path.exists():
            return
        records = json.loads(self.data_path.read_text())
        for r in records:
            pub = r.get("advertised_date")
            yield RawSignal(
                province="ON",
                signal_type=DistressType.TAX_SALE,
                confidence=0.95,  # explicit public notice — high confidence
                dedupe_key=f"on_tax_sales:{r['municipality']}:{r['roll_or_pin']}:{pub}",
                detail=(
                    f"Tax sale advertised by {r['municipality']}. "
                    f"Minimum tender: ${r.get('minimum_tender', 'n/a')}."
                ),
                published_date=date.fromisoformat(pub) if pub else None,
                parcel_id=r.get("pin"),
                address=r.get("address"),
                municipality=r.get("municipality"),
                latitude=r.get("latitude"),
                longitude=r.get("longitude"),
                extra={"minimum_tender": r.get("minimum_tender")},
            )
